#!/usr/bin/env python3
"""Backtest 16,380 BTCUSD second-green entries with percentage SL/TP.

15 fixed SL percentages (including NONE) x 13 TP percentages x
2 entry logics x 42 volume/volatility filters. Conservative 1m OHLC.
Research only; do not mistake historical 1-BTC-equivalent point PnL
for capital or leverage-adjusted returns.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd

import research_supertrend_15m_line_touch as base
import research_supertrend_15m_filter_grid as filt
import research_supertrend_15m_profit_protection as protect
import research_supertrend_15m_second_green as green

OUT=Path("analysis/second_green_percentage_grid_20261122")
SL_PCT=(.10,.12,.15,.20,.25,.30,.40,.50,.75,1.,1.5,2.,3.,5.,None)
TP_PCT=(.10,.12,.15,.20,.30,.40,.50,.75,1.,1.5,2.,3.,5.)
FILL_SLIP=base.SLIP
FEE=base.FEE
KINDS=("after_line_touch","after_bullish_flip")
MONTHS=base.MONTHS
SHOW=[("vol_off","atr_off"),("vol_ge_1p0","atrpct_ge_0p20"),
      ("vol_ge_1p25","atrpct_ge_0p20"),
      ("vol_ge_1p5","atrpct_ge_0p20"),
      ("vol_ge_2p0","atrpct_ge_0p30"),
      ("vol_ge_2p0","atrpct_ge_0p40")]
# The full experiment grid is evaluated for BOTH entries and all filters;
# SHOW only controls tables in the research report.
assert len(SL_PCT)==15 and len(TP_PCT)==13
S=np.array([p if p is not None else np.inf for p in SL_PCT],float)
T=np.array(TP_PCT,float)
NS=len(S); NT=len(T)
ALL_FINITE_SL=np.isfinite(S)
RR_MASK=np.ones((NS,NT),bool)

def money_fmt(x):
    return f"{x:+,.2f}"

def market_ohlc_precompute(mid,j,end,high,low,opening,close):
    """Return arrays of exit price, exit index, cause, and OHLC collision.

    Entry is BUY at first minute OPEN (+5 pt effective slippage). All highs
    and lows from that entry minute are eligible; same-minute SL takes
    precedence over TP. The next 1m after ST close-stop is an alternate
    exit. If a hard stop gaps, exit at 1m open if below the SL. If an
    unprotected trade reaches data end, exit last minute close.
    """
    n=len(high)
    if j<0 or j>=n or end<=j:raise AssertionError((j,end,n))
    s=mid+FILL_SLIP
    tp_price=s*(1.+T/100.)
    sl_price=np.where(ALL_FINITE_SL,s*(1.-S/100.),-np.inf)
    chunk_high=high[j:end]
    chunk_low=low[j:end]
    assert len(chunk_high)>0
    maxhi=np.maximum.accumulate(chunk_high)
    minlo=np.minimum.accumulate(chunk_low)
    tp_ix0=np.searchsorted(maxhi,tp_price,side="left")
    sl_ix0=np.searchsorted(-minlo,-sl_price,side="left")
    # Index == number of active observed 1m candles means no hit.
    tp_ix=np.where(tp_ix0<len(maxhi),tp_ix0+j,n+1)
    sl_ix=np.where(sl_ix0<len(minlo),sl_ix0+j,n+1)
    # Use 2d matrix SL x TP for all 195 target choices at once.
    stopped=(sl_ix[:,None]<=tp_ix[None,:]) & (sl_ix[:,None]<=n)
    taken=(tp_ix[None,:]<sl_ix[:,None]) & (tp_ix[None,:]<=n)
    # Same 1m touches on SL and TP counted as stop, never as TP.
    ambiguous=(sl_ix[:,None]==tp_ix[None,:]) & (sl_ix[:,None]<=n)
    before_close=stopped|taken
    close_exit=(end<n)
    close_mid=(float(opening[end]) if close_exit else float(close[-1]))
    exitmid=np.full((NS,NT),close_mid,dtype=float)
    stop_at=np.minimum(sl_ix,n-1)
    # Stop gap gets the worse opening price; fill at SL otherwise.
    exitmid=np.where(stopped,np.minimum(opening[stop_at][:,None],
                          sl_price[:,None]),exitmid)
    exitmid=np.where(taken,tp_price[None,:],exitmid)
    reasons=np.where(stopped,1,np.where(taken,2,3 if close_exit else 4))
    exitidx=np.where(stopped,sl_ix[:,None],
             np.where(taken,tp_ix[None,:],
                   end if close_exit else n-1))
    return exitmid,exitidx,reasons,ambiguous

def test_synthetic():
    op=np.full(50,1000.,float);lo=op.copy();hi=op.copy();cl=op.copy()
    # BUY at 1005 assumed effective fill. +0.12% target => 1006.206
    # -0.12% hard stop => 1003.794; both in same entry minute.
    hi[0]=1010.;lo[0]=990.
    mid,idx,reason,amb=market_ohlc_precompute(1000.,0,20,hi,lo,op,cl)
    sidx=SL_PCT.index(.12);tidx=TP_PCT.index(.12)
    assert reason[sidx,tidx]==1 and idx[sidx,tidx]==0 and amb[sidx,tidx],(
        mid[sidx,tidx],reason[sidx,tidx])
    # With no SL, TP is eligible in entry 1m for market-open entry.
    assert reason[-1,tidx]==2 and idx[-1,tidx]==0
    # Close-stop at j=10 open if neither percent barrier touched.
    hi[0]=1000.;lo[0]=1000.
    mid,idx,reason,amb=market_ohlc_precompute(1000.,0,10,hi,lo,op,cl)
    assert reason[-1,TP_PCT.index(5.)]==3 and idx[-1,TP_PCT.index(5.)]==10
    # Spike on last minute (minute 10) is after the close-stop exit,
    # and must NOT be counted.
    hi[10]=2000.
    mid,idx,reason,amb=market_ohlc_precompute(1000.,0,10,hi,lo,op,cl)
    assert reason[-1,TP_PCT.index(5.)]==3
    # If lower gap below hard stop, stop exit at opening gap, not SL level.
    op[1]=970.;hi[1]=985.;lo[1]=960.
    mid,idx,reason,amb=market_ohlc_precompute(1000.,0,10,hi,lo,op,cl)
    assert reason[SL_PCT.index(.12),tidx]==1 and mid[SL_PCT.index(.12),tidx]==970.
    print("SYNTHETIC_PERCENT_STOP_FIRST_TESTS_PASS",flush=True)

def run_grid(entries,stopbars,minute,months_arr,filtername,atrname,mode):
    high=minute.high.to_numpy(float)
    low=minute.low.to_numpy(float)
    opening=minute.open.to_numpy(float)
    closing=minute.close.to_numpy(float)
    count=np.zeros((NS,NT),int)
    wins=np.zeros((NS,NT),int)
    tp_hits=np.zeros((NS,NT),int)
    sl_hits=np.zeros((NS,NT),int)
    close_exits=np.zeros((NS,NT),int)
    ambig=np.zeros((NS,NT),int)
    net_sum=np.zeros((NS,NT),float)
    gross_sum=np.zeros((NS,NT),float)
    fee_sum=np.zeros((NS,NT),float)
    equity=np.zeros((NS,NT),float)
    peak=np.zeros((NS,NT),float)
    drawdown=np.zeros((NS,NT),float)
    month_sum=np.zeros((len(MONTHS),NS,NT),float)
    month_trade=np.zeros((len(MONTHS),NS,NT),int)
    month_wins=np.zeros((len(MONTHS),NS,NT),int)
    mindex={m:i for i,m in enumerate(MONTHS)}
    n=len(high)
    for cycle,bar,j,mid,line in entries:
        month=str(months_arr[j])
        if month not in mindex:continue
        mi=mindex[month]
        sidx=np.searchsorted(stopbars,bar,side="left")
        sb=int(stopbars[sidx]) if sidx<len(stopbars) else -1
        end=min((sb+1)*15,n) if sb>=0 else n
        # Market fill at third bar open; assert no lookahead.
        assert abs(mid-opening[j])<1e-7
        emid,ex,reason,amb=market_ohlc_precompute(mid,j,end,
                                                   high,low,opening,closing)
        fill=mid+FILL_SLIP
        eff_exit=emid-FILL_SLIP
        fees=FEE*(fill+eff_exit)
        gross=emid-mid
        net=eff_exit-fill-fees
        # All active trades are fixed entry counts in this cohort.
        count+=1;wins+=(net>0)
        tp_hits+=(reason==2);sl_hits+=(reason==1)
        close_exits+=(reason==3);ambig+=amb.astype(int)
        net_sum+=net;gross_sum+=gross;fee_sum+=fees
        equity+=net
        peak=np.maximum(peak,equity)
        drawdown=np.maximum(drawdown,peak-equity)
        month_sum[mi]+=net
        month_trade[mi]+=1
        month_wins[mi]+=(net>0)

    rows=[];allmonths=[]
    def period_slice(s,t):
        pnl=month_sum[s:t].sum(axis=0)
        n=month_trade[s:t].sum(axis=0)
        w=month_wins[s:t].sum(axis=0)
        return pnl,n,w
    for si,stop in enumerate(SL_PCT):
        for ti,target in enumerate(TP_PCT):
            pnl=float(net_sum[si,ti])
            for period,s,t in [("all22",0,22),("2025",0,12),
                               ("2026_JanOct",12,22),
                               ("2026_JanJun",12,18),
                               ("2026_JulOct",18,22)]:
                p,ntr,nw=period_slice(s,t)
                tr=int(ntr[si,ti]);w=int(nw[si,ti])
                allmonths.append(dict(
                    entry_type=mode,vol_filter=filtername,atr_filter=atrname,
                    sl_pct=stop if stop is not None else "none",
                    tp_pct=target,period=period,
                    trades=tr,wins=w,win_rate_pct=round(100*w/tr,2)
                                        if tr else None,
                    net_pts=round(float(p[si,ti]),2),
                    net_pts_per_trade=round(float(p[si,ti])/tr,2) if tr else None,
                    positive_months=int(np.sum(month_sum[s:t,si,ti]>0)),
                    losing_months=int(np.sum(month_sum[s:t,si,ti]<0)),
                    flat_months=int(np.sum(month_sum[s:t,si,ti]==0))))
            tr=int(count[si,ti]);w=int(wins[si,ti])
            pmonth=month_sum[:,si,ti]
            rows.append(dict(
                entry_type=mode,vol_filter=filtername,atr_filter=atrname,
                sl_pct=stop if stop is not None else "none",tp_pct=target,
                trades=tr,wins=w,win_rate_pct=round(100*w/tr,2) if tr else None,
                tp_exits=int(tp_hits[si,ti]),sl_exits=int(sl_hits[si,ti]),
                close_stop_exits=int(close_exits[si,ti]),
                ambiguous_bar_exits=int(ambig[si,ti]),
                net_pts=round(pnl,2),net_pts_per_trade=round(pnl/tr,2) if tr else None,
                gross_pts=round(float(gross_sum[si,ti]),2),
                estimated_fees_pts=round(float(fee_sum[si,ti]),2),
                max_drawdown_pts=round(float(drawdown[si,ti]),2),
                profitable_months=int(np.sum(pmonth>0)),
                losing_months=int(np.sum(pmonth<0)),
                flat_months=int(np.sum(pmonth==0))))
    return rows,allmonths

def main():
    test_synthetic()
    OUT.mkdir(parents=True,exist_ok=True)
    minute,bar15,files=base.load()
    st,trend=base.supertrend(bar15)
    vol,atpct,atrel=filt.build_features(bar15)
    events,stopbars=filt.candidate_touch_events(
        minute,bar15,st,trend,vol,atpct,atrel)
    op=minute.open.to_numpy(float)
    months_arr=minute.index.tz_convert("Asia/Kolkata").strftime("%Y-%m").to_numpy()

    # Pre-compare the EXACT fixed point 300/1200 baseline from previously
    # verified 2-green study before new percentage study begins.
    vs0=filt.VOLUME["vol_ge_1p0"]
    a0=filt.VOLATILITY["atrpct_ge_0p20"]
    t0=protect.select_events(events,vs0,a0)
    touch0=green.after_touch_green(t0,bar15,trend,stopbars,op)
    flip0=green.after_flip_green(bar15,trend,vol,atpct,atrel,
                vs0,a0,stopbars,op)
    arrays=(minute.high.to_numpy(float),minute.low.to_numpy(float),
            op,minute.close.to_numpy(float),minute.index)
    for name,entry,expected_n,expected_net in (
       ("after_line_touch",touch0,108,4704.53),
       ("after_bullish_flip",flip0,197,-24654.29)):
        ref=green.market_replay(entry,stopbars,arrays,300,1200,"off",months_arr)
        subset=ref[ref.month_ist.isin(MONTHS)]
        assert len(subset)==expected_n,(name,len(subset))
        assert abs(subset.net_pts.sum()-expected_net)<.15,(
                     name,subset.net_pts.sum(),expected_net)
    print("PRIOR_FIXED_POINT_COHORT_PARITY_PASS",flush=True)
    allrows=[];allperiod=[]

    for vi,(vn,vs) in enumerate(filt.VOLUME.items()):
        for ai,(an,a) in enumerate(filt.VOLATILITY.items()):
            touch=protect.select_events(events,vs,a)
            green_touch=green.after_touch_green(touch,bar15,trend,stopbars,op)
            green_flip=green.after_flip_green(bar15,trend,vol,atpct,atrel,
                           vs,a,stopbars,op)
            for mode,entry in [
              ("after_line_touch",green_touch),
              ("after_bullish_flip",green_flip)]:
                rows,period=run_grid(entry,stopbars,minute,months_arr,
                                        vn,an,mode)
                allrows.extend(rows);allperiod.extend(period)
            print("GRID_DONE",vn,an,"touch_green",len(green_touch),
                  "flip_green",len(green_flip),"rows",len(allrows),flush=True)
    summary=pd.DataFrame(allrows)
    parts=pd.DataFrame(allperiod)
    assert len(summary)==42*2*NS*NT==16380,len(summary)
    assert len(parts)==len(summary)*5
    assert summary.groupby(["entry_type","vol_filter","atr_filter"]).trades.nunique().eq(1).all()
    # The volume >=1 ATR>=.20% cohort is exactly previously researched.
    match=summary[(summary.vol_filter=="vol_ge_1p0")&
                  (summary.atr_filter=="atrpct_ge_0p20")]
    assert match[match.entry_type=="after_line_touch"].trades.eq(108).all()
    assert match[match.entry_type=="after_bullish_flip"].trades.eq(197).all()

    summary.to_csv(OUT/"all_16380_percentage_grid.csv",index=False)
    parts.to_csv(OUT/"all_2025_2026_period_splits.csv.gz",
                 index=False,compression="gzip")
    default=summary[(summary.vol_filter=="vol_ge_1p0")&
                    (summary.atr_filter=="atrpct_ge_0p20")]
    unfiltered=summary[(summary.vol_filter=="vol_off")&
                       (summary.atr_filter=="atr_off")]
    default.to_csv(OUT/"default_filter_percent_grid.csv",index=False)
    unfiltered.to_csv(OUT/"no_filter_percent_grid.csv",index=False)

    # Pre-selected grid displays, only for robust cohort, both methods.
    selective=default[default.sl_pct.astype(str).isin([
        ".12","0.12","0.2","0.3","0.5","1.0","2.0","5.0","none"])&
                      default.tp_pct.isin([.12,.2,.3,.5,1.,2.,5.])]
    selective.to_csv(OUT/"key_percentage_combinations.csv",index=False)

    # Separate 2025 ranking as a descriptive sensitivity check. All source
    # periods were already explored, so 2026 is not a genuine blind OOS.
    p2025=parts[parts.period=="2025"][
      ["entry_type","vol_filter","atr_filter","sl_pct","tp_pct",
       "trades","net_pts","net_pts_per_trade"]].rename(columns={
        "trades":"trades_2025","net_pts":"net_pts_2025",
        "net_pts_per_trade":"avg_pts_2025"})
    joint=summary.merge(p2025,on=["entry_type","vol_filter","atr_filter",
                                  "sl_pct","tp_pct"])
    eligible=joint[(joint.trades>=60)&(joint.trades_2025>=30)]
    rank=eligible.sort_values(["avg_pts_2025","trades_2025"],
                              ascending=[False,False])
    rank.to_csv(OUT/"2025_reference_rank_min60trades.csv",index=False)

    total_positive=int((summary.net_pts>0).sum())
    robust=summary[summary.trades>=60]
    robust_positive=int((robust.net_pts>0).sum())
    quality=dict(
        run="BTCUSD 15m Supertrend second green percentage SL TP grid",
        all_configurations=int(len(summary)),
        entry_methods=list(KINDS),
        filter_combinations=42,
        sl_percentages=[v if v is not None else "none" for v in SL_PCT],
        tp_percentages=list(TP_PCT),
        source_1m_candles=len(minute),
        fifteen_min_bars=len(bar15),
        period="22 completed IST entry months Jan2025-Oct2026",
        same_filter_fixed_point_reference="previous 300-point SL/1200-point TP entry cohort 108 touch vs 197 flip PARITY PASS",
        total_net_positive_configs=total_positive,
        net_positive_configs_min60trades=robust_positive,
        model="third 15m candle open, buy fill mid+5 pt slip, TP & SL levels as percent of simulated fill, 1m high/low stop-first on simultaneous hit, 15m ST close-stop next 1m open",
        fee="0.05% taker each direction with 18% GST on fee",
        units="1 BTC-equivalent profit in BTCUSD price points, NOT leverage or account return",
        absent=["funding","bid/ask book","fill queue","dynamic spread","margin","liquidation"],
        note="Hindsight grid; years 2025 and 2026 already used for prior research. No untouched out-of-sample or forward validation.")
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2)+"\n")

    kcols=["entry_type","vol_filter","atr_filter","sl_pct","tp_pct",
           "trades","wins","win_rate_pct","tp_exits","sl_exits",
           "close_stop_exits","ambiguous_bar_exits","net_pts",
           "net_pts_per_trade","max_drawdown_pts",
           "profitable_months","flat_months"]
    top=robust.sort_values(["net_pts","profitable_months"],
                           ascending=[False,False])
    # Long-form percentage matrix for each method with same previously
    # highlighted filter. Top SL=5% may be data-end dominated; warn.
    def table(mode):
        a=default[default.entry_type==mode].copy()
        a["sl_pct"]=a.sl_pct.astype(str)
        piv=a.pivot(index="sl_pct",columns="tp_pct",values="net_pts_per_trade")
        piv=piv.reindex([str(x) for x in SL_PCT[:-1]]+["none"])
        return piv.to_markdown(floatfmt=".1f")
    base_profiles=[]
    for mode in KINDS:
        for sp,tp in [(.12,.12),(.12,.20),(.20,.20),(.20,.30),
                      (.30,.30),(.30,.50),(.50,1.),(1.,2.),
                      (2.,5.),(5.,5.),("none",5.)]:
            x=default[(default.entry_type==mode)&
                      (default.sl_pct.astype(str)==str(sp))&
                      (default.tp_pct==tp)]
            if len(x):base_profiles.extend(x.to_dict("records"))
    chosen=pd.DataFrame(base_profiles)
    # Report rank with 2025-only decision; 2026 is re-check but previously exposed.
    report=[
        "# BTCUSD 15m: percentage SL and TP grid to 5%",
        "",
        "**16,380 configurations** = 2 second-green 15m entry models ×",
        "42 volume/ATR regimes × 15 percent stops (including Supertrend-only)",
        "× 13 percent take-profit sizes.",
        "",
        "Stops and targets measured as % from simulated third-candle market BUY",
        "fill. Evaluated using 1m OHLC, conservative hard-stop-first if same",
        "1m also touches TP. Retain 15m Supertrend close-stop as secondary exit.",
        "Data: 22 IST months Jan2025–Oct2026, Delta India BTCUSD futures 1m.",
        "Taker fees 0.05% each side, GST 18%, 5 BTC pts slip on each side.",
        "All net amounts are hypothetical 1-BTC-equivalent BTC price points.",
        "",
        "## Prior 300 SL / 1200 TP cohorts: VERIFIED SAME ENTRY COUNTS",
        "- After touch: 108, previous net +4704.53 points",
        "- After flip: 197, previous net −24654.29 points",
        "",
        "## How many configurations net-positive?",
        f"Positive net (all sizes): {total_positive}/{len(summary)}.",
        f"Positive net with >=60 trades: {robust_positive}/{len(robust)}.",
        "",
        "## Predefined percent examples — volume >=1.0, ATR>=0.20%",
        chosen[kcols].to_markdown(index=False) if len(chosen) else "(none)","",
        "## All 15x13 percent net points-per-trade: AFTER LINE TOUCH",
        table("after_line_touch"),"",
        "## All 15x13 percent net points-per-trade: AFTER BULLISH FLIP",
        table("after_bullish_flip"),"",
        "## Best 30 configurations with >=60 trades (selected after viewing the same data)",
        top[kcols].head(30).to_markdown(index=False),"",
        "## 2025-only ranking (>=30 2025 trades, >=60 full trades; descriptive)",
        rank[kcols+["trades_2025","net_pts_2025","avg_pts_2025"]].head(20)
            .to_markdown(index=False),"",
        "## Limitations",
        "- All combinations in the full CSV; 5% SL or TP may almost never hit",
        "  before the 15m Supertrend close-stop, so observed exit behavior is",
        "  often determined by the original close-stop, not the percentage.",
        "- A % SL and TP are PRICE percentages, not ROI with leverage.",
        "- Fill cost and GST can exceed tiny 0.1–0.2% target margins.",
        "- True intra-1m sequence cannot be recovered; stop always wins ties.",
        "- Missing order book spread, liquidity, funding, liquidation and margin.",
        "- Previously researched periods mean historical parameter selection is",
        "  NOT independent out-of-sample validation or forward evidence.",
        "- No shorts; one long entry per bullish Supertrend cycle.",
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("QUALITY",json.dumps({
          "cases":len(summary),"net_positive":total_positive,
          "min60_positive":robust_positive}),flush=True)
    print("SELECTED_RESULTS\n"+chosen[kcols].to_string(index=False),flush=True)
    print("TOP_30_ROBUST\n"+top[kcols].head(30).to_string(index=False),flush=True)
    print("DONE",str(OUT/"RESEARCH_REPORT.md"),flush=True)

if __name__=="__main__":
    main()
