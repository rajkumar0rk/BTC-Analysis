#!/usr/bin/env python3
"""Stage 14: test identifiable pre-entry BTC market regimes for monthly consistency.

Never select months based on their future returns. Regimes use completed
4H/1H and previous calendar month data. Structural 5m patterns from Stage 11
and separate 4H->1H->15M signals from Stage 13 are unchanged. Each model
is replayed independently with stop-first 1m fills, 2R/3R and costs.
Existing 2026 periods are research exposed; none is pristine forward validation.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd

from research_every_candle_200 import read_archive, periods, PERIOD_NAMES, FEE, SLIPPAGE
from research_structure_rr_stage11 import candidates, replay_one
from research_pretrend_market_state_stage12 import event_features
from research_trend_pullback_breakout_stage13 import events as trend_events

OUT=Path("analysis/institutional_discovery_stage14_monthly_regimes")
REGIMES=(
 "all_entries",
 "4h_adx25",
 "4h_efficiency30_adx25",
 "4h_adx25_directional_drift",
 "4h_low_atr_then_5m_burst",
 "4h_high_atr_adx25",
 "1h_volume_burst_adx20",
 "1h_quiet_4h_trending",
 "4h_channel_break_in_direction",
 "4h_ranging_adx18",
 "previous_month_trending_4h_adx25",
 "previous_month_ranging_4h_adx18",
)
REWARDS=(2.,3.)
HOLDS=(240,480)
MIN_RISK=150.
MAX_RISK=1200.
BASE_MONTHS=pd.period_range("2025-01","2026-11",freq="M").astype(str)
MIN_COUNTS=(60,30,20)
END_DATES={
  "2025_train":("2025-01","2025-12"),
  "2026_H1_validation":("2026-01","2026-06"),
  "2026_H2_seen_recheck":("2026-07","2026-10"),
  "2026_Nov_recent_exploratory":("2026-11","2026-11")
}

def regime_data(f):
    def tf(name,n):
        a=f[["open","high","low","close","volume"]].resample(
            name,closed="left",label="right").agg({
            "open":"first","high":"max","low":"min","close":"last","volume":"sum"})
        a["cnt"]=f.close.resample(name,closed="left",label="right").count()
        a["valid"]=(a.cnt.rolling(21,min_periods=21).min()==n)
        return a
    h4=tf("4h",240)
    h1=tf("1h",60)
    previous=h4.close.shift(1)
    tr=pd.concat([h4.high-h4.low,(h4.high-previous).abs(),
                  (h4.low-previous).abs()],axis=1).max(axis=1)
    atr=tr.ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    up=h4.high.diff()
    down=-h4.low.diff()
    dm_up=up.where((up>down)&(up>0),0.)
    dm_dn=down.where((down>up)&(down>0),0.)
    smooth_up=dm_up.ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    smooth_dn=dm_dn.ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    pdi=100*smooth_up/atr.replace(0,np.nan)
    mdi=100*smooth_dn/atr.replace(0,np.nan)
    dx=100*(pdi-mdi).abs()/(pdi+mdi).replace(0,np.nan)
    h4["adx"]=dx.ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    h4["atr_ratio"]=atr/atr.shift(1).rolling(20,min_periods=20).median().replace(0,np.nan)
    h4["vr"]=h4.volume/h4.volume.shift(1).rolling(20,min_periods=20).mean().replace(0,np.nan)
    h4["eff8"]=(h4.close-h4.close.shift(8)).abs()/(
        h4.close.diff().abs().rolling(8,min_periods=8).sum().replace(0,np.nan))
    h4["directional_drift8"]=(h4.close-h4.close.shift(8))/atr.replace(0,np.nan)
    h4["highest12"]=h4.high.shift(1).rolling(12,min_periods=12).max()
    h4["lowest12"]=h4.low.shift(1).rolling(12,min_periods=12).min()
    h4["channel_long"]=(h4.close>h4.highest12).astype(float)
    h4["channel_short"]=(h4.close<h4.lowest12).astype(float)
    h1["vr"]=h1.volume/h1.volume.shift(1).rolling(20,min_periods=20).mean().replace(0,np.nan)
    h1["span"]=h1.high-h1.low
    h1["prior3quiet"]=(h1.span.shift(1)+h1.span.shift(2)+h1.span.shift(3))/(
        3*h1.span.shift(1).rolling(20,min_periods=20).median().replace(0,np.nan))
    # Previous calendar month's 4H close-to-close directional efficiency,
    # never same-month returns as an entry feature.
    h4["month_ist"]=h4.index.tz_convert("Asia/Kolkata").strftime("%Y-%m")
    vals=[]
    for month,g in h4.groupby("month_ist",sort=True):
        g=g[g.cnt==240]
        if len(g)<100:continue
        diff=g.close.diff().abs().sum()
        eff=(abs(float(g.close.iloc[-1]-g.close.iloc[0]))/float(diff)) if diff>0 else 0.
        vals.append(dict(month=month,trend_eff=eff,
            vol_atr=float(g.atr_ratio.iloc[-1]),bar_count=len(g)))
    months=pd.DataFrame(vals).sort_values("month")
    # One-month lag mapping; if the prior month is absent, leave missing.
    x=pd.DataFrame({"month":BASE_MONTHS})
    x["previous_month"]=(pd.PeriodIndex(x.month,freq="M")-1).astype(str)
    x=x.merge(months.rename(columns={"month":"previous_month"}),
              on="previous_month",how="left")
    prev_map=dict(zip(x.month,x.trend_eff))
    return h4,h1,months,prev_map

def prepare_events(f,seg_start,seg_end,p):
    raw,_=candidates(f,seg_start,seg_end,p)
    # Stage12 x has only entry-known 1H/4H states. No reuse of future labels.
    old=event_features(f,raw)
    old=old.rename(columns={"risk_points":"risk_pts","unix":"entry_unix"})
    old["family"]="S11_"+old.pattern
    old["volume_ratio_5m"]=old.volume_ratio
    old["range_ratio_5m"]=old.range_ratio
    # Stage13 is a separately defined 15-minute breakout, 1m execution.
    newer,_=trend_events(f,seg_start,seg_end,p)
    newer=newer.rename(columns={"pullback":"family",
                                "volume_ratio":"volume_ratio_5m",
                                "unix":"entry_unix",
                                "risk_pts":"risk_pts"})
    newer["family"]=newer.family.map(lambda s:"S13_pullback_"+s)
    newer["range_ratio_5m"]=np.nan
    old=old[["family","k","side","entry_unix","risk_pts","stop_price",
             "volume_ratio_5m","range_ratio_5m"]]
    newer=newer[["family","k","side","entry_unix","risk_pts","stop_price",
                 "volume_ratio_5m","range_ratio_5m"]]
    e=pd.concat([old,newer],ignore_index=True).sort_values(["k","family","side"])
    future_ok=(seg_end[e.k.to_numpy(np.int32)]-e.k.to_numpy(np.int32)>=max(HOLDS))
    e=e[future_ok].copy()
    forward=e.k.to_numpy(np.int32)+max(HOLDS)-1
    e=e[p[e.k.to_numpy(np.int32)]==p[forward]].copy()
    e=e[(e.risk_pts>=MIN_RISK)&(e.risk_pts<=MAX_RISK)]
    h4,h1,monthly_regimes,prior_month=regime_data(f)
    index=f.index[e.k.to_numpy(np.int32)]
    four=h4.reindex(index,method="ffill")
    hour=h1.reindex(index,method="ffill")
    e["month_ist"]=index.tz_convert("Asia/Kolkata").strftime("%Y-%m")
    e["period"]=[PERIOD_NAMES[i] for i in p[e.k.to_numpy(np.int32)]]
    for fld in ("valid","adx","eff8","atr_ratio","vr","directional_drift8",
                "channel_long","channel_short"):
        e["h4_"+fld]=four[fld].to_numpy()
    for fld in ("valid","vr","prior3quiet"):
        e["h1_"+fld]=hour[fld].to_numpy()
    e["previous_month_eff"]=e.month_ist.map(prior_month)
    required=["h4_adx","h4_eff8","h4_atr_ratio","h1_vr"]
    v=e.h4_valid.fillna(False)&e.h1_valid.fillna(False)
    v &= e[required].notna().all(axis=1)
    e=e[v].copy()
    if e.empty:raise RuntimeError("No eligible completed 4H/1H events")
    return e,monthly_regimes

def regime_masks(e):
    sign=e.side.to_numpy(int)
    d=sign*e.h4_directional_drift8.to_numpy(float)
    h4direction=np.where(sign==1,e.h4_channel_long,e.h4_channel_short)
    masks={
      "all_entries":np.ones(len(e),dtype=bool),
      "4h_adx25":(e.h4_adx>=25).to_numpy(bool),
      "4h_efficiency30_adx25":((e.h4_eff8>=.30)&(e.h4_adx>=25)).to_numpy(bool),
      "4h_adx25_directional_drift":((e.h4_adx>=25)&(d>=1.5)).to_numpy(bool),
      "4h_low_atr_then_5m_burst":((e.h4_atr_ratio<=.85)&
              (e.volume_ratio_5m>=1.5)&(e.range_ratio_5m>=1.3)).to_numpy(bool),
      "4h_high_atr_adx25":((e.h4_atr_ratio>=1.25)&(e.h4_adx>=25)).to_numpy(bool),
      "1h_volume_burst_adx20":((e.h1_vr>=1.5)&(e.h4_adx>=20)).to_numpy(bool),
      "1h_quiet_4h_trending":((e.h1_prior3quiet<=.75)&(e.h4_adx>=25)).to_numpy(bool),
      "4h_channel_break_in_direction":(h4direction>=1),
      "4h_ranging_adx18":((e.h4_adx<=18)&(e.h4_eff8<=.20)).to_numpy(bool),
      "previous_month_trending_4h_adx25":(
          (e.previous_month_eff>=.3)&(e.h4_adx>=25)).to_numpy(bool),
      "previous_month_ranging_4h_adx18":(
          (e.previous_month_eff<=.15)&(e.h4_adx<=18)).to_numpy(bool),
    }
    if tuple(masks)!=REGIMES:raise AssertionError("Unexpected regime definitions")
    return masks

def backtest(e,f):
    O=f.open.to_numpy(np.float64)
    H=f.high.to_numpy(np.float64)
    L=f.low.to_numpy(np.float64)
    C=f.close.to_numpy(np.float64)
    frames=[]
    masks=regime_masks(e)
    for family in sorted(e.family.unique()):
        fam=(e.family==family).to_numpy(bool)
        for regime,condition in masks.items():
            subset=e.loc[fam&condition].sort_values(["k","side"])
            if len(subset)<5:continue
            for r in REWARDS:
                for duration in HOLDS:
                    last=-1
                    for z in subset.itertuples(index=False):
                        k=int(z.k)
                        if k<=last:continue
                        j,why,gross,net,offer,netR,risk=replay_one(O,H,L,C,k,
                            int(z.side),float(z.stop_price),float(r),int(duration))
                        last=int(j)
                        frames.append((family,regime,float(r),int(duration),
                            z.period,z.month_ist,int(z.entry_unix),int(z.entry_unix+60*(j-k)),
                            "LONG" if z.side==1 else "SHORT",
                            int(why),round(float(risk),3),round(float(net),3),
                            round(float(offer),3),round(float(netR),4)))
    if not frames:raise ValueError("No strategy trades")
    return pd.DataFrame(frames,columns=[
      "family","regime","target_R","max_hold_min","period","month_ist",
      "entry_unix","exit_unix","direction","exit_reason","initial_risk_pts",
      "net_standard_pts","scalper_whatif_pts","net_R"])

def monthly_and_summary(tr):
    keys=["family","regime","target_R","max_hold_min"]
    months=[]
    overall=[]
    for config,g in tr.groupby(keys,sort=True):
        g=g.sort_values("entry_unix")
        month=g.groupby("month_ist").net_standard_pts.agg(["size","sum"])
        month=month.reindex(BASE_MONTHS,fill_value=0)
        for m,rec in month.iterrows():
            n=int(rec["size"])
            pnl=float(rec["sum"])
            months.append(dict(zip(keys,config),month_ist=m,
                trades=n,net_pts=round(pnl,2),
                status="No trades" if n==0 else "Profit" if pnl>0 else
                       "Loss" if pnl<0 else "Flat"))
        for period,z in g.groupby("period",sort=True):
            v=z.net_standard_pts.to_numpy(float)
            win=float(v[v>0].sum())
            loss=-float(v[v<0].sum())
            eq=np.r_[0.,np.cumsum(v)]
            overall.append(dict(zip(keys,config),period=period,
                trades=len(z),win_pct=round(100*float((v>0).mean()),2),
                avg_net_pts=round(float(v.mean()),2),
                net_total_pts=round(float(v.sum()),2),
                pf=round(win/loss,3) if loss>0 else None,
                worst_trade=round(float(v.min()),2),
                max_dd_pts=round(float(np.max(np.maximum.accumulate(eq)-eq)),2)))
    monthly=pd.DataFrame(months)
    period=pd.DataFrame(overall)
    criteria=[]
    for config,m in monthly.groupby(keys,sort=True):
        p=period
        for key,val in zip(keys,config):
            p=p[p[key]==val]
        periods={z.period:z for z in p.itertuples(index=False)}
        year25=m[m.month_ist.str.startswith("2025")]
        year26=m[m.month_ist.str.startswith("2026")]
        active25=int((year25.trades>0).sum())
        active26=int((year26.trades>0).sum())
        prof25=int((year25.status=="Profit").sum())
        prof26=int((year26.status=="Profit").sum())
        enough=all(t in periods for t in PERIOD_NAMES[:3]) and (
            periods[PERIOD_NAMES[0]].trades>=MIN_COUNTS[0] and
            periods[PERIOD_NAMES[1]].trades>=MIN_COUNTS[1] and
            periods[PERIOD_NAMES[2]].trades>=MIN_COUNTS[2])
        positive=all(t in periods for t in PERIOD_NAMES[:3]) and (
            min(periods[t].avg_net_pts for t in PERIOD_NAMES[:3])>0)
        monthgate=bool(enough and positive and
            active25>=9 and active26>=8 and
            prof25/max(active25,1)>=.75 and prof26/max(active26,1)>=.75)
        criteria.append(dict(zip(keys,config),
            year2025_n=int(year25.trades.sum()),
            profit_months_2025=prof25,loss_months_2025=int((year25.status=="Loss").sum()),
            no_trade_months_2025=int((year25.trades==0).sum()),
            active_months_2025=active25,net_2025=round(float(year25.net_pts.sum()),2),
            year2026_n=int(year26.trades.sum()),
            profit_months_2026=prof26,loss_months_2026=int((year26.status=="Loss").sum()),
            no_trade_months_2026=int((year26.trades==0).sum()),
            active_months_2026=active26,net_2026=round(float(year26.net_pts.sum()),2),
            positive_three_periods=bool(positive),minimum_sample=enough,
            passes_research_monthly_gate=monthgate))
    return monthly,period,pd.DataFrame(criteria)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    f,start,end,q=read_archive()
    p=periods(f.index)
    ev,mo_state=prepare_events(f,start,end,p)
    tr=backtest(ev,f)
    monthly,period,criteria=monthly_and_summary(tr)
    tr.to_csv(OUT/"trade_ledger.csv.gz",compression="gzip",index=False)
    ev.to_csv(OUT/"event_states.csv.gz",compression="gzip",index=False)
    mo_state.to_csv(OUT/"previous_month_regime_stats.csv",index=False)
    monthly.to_csv(OUT/"monthly_results.csv",index=False)
    period.to_csv(OUT/"period_results.csv",index=False)
    criteria.to_csv(OUT/"monthly_consistency.csv",index=False)
    passes=criteria[criteria.passes_research_monthly_gate]
    # Sorted strictly from 2025 statistics; later rows only for auditing.
    ranked=criteria[(criteria.year2025_n>=60)&
      (criteria.active_months_2025>=9)].sort_values(
        ["profit_months_2025","net_2025"],ascending=False).head(20)
    meta=dict(source="BTCUSD Delta India historical 1m OHLCV",
        dataset_observed_1m_candles=len(f),source_missing_minutes=q["missing_minutes"],
        event_rows=len(ev),standalone_trade_rows=len(tr),strategy_combinations=len(criteria),
        monthly_research_gate_passes=len(passes),
        period_split=list(PERIOD_NAMES),model_families=sorted(ev.family.unique()),
        tested_regimes=list(REGIMES),rewards_R=list(REWARDS),max_holds_min=list(HOLDS),
        risk_points=[MIN_RISK,MAX_RISK],
        gate=">=9 active 2025 and >=8 active 2026; >=75% profitable active months each year; >=60/30/20 trades and net-positive 2025/H1/H2",
        standard_costs="0.05pct taker each side, 18pct GST, 5pts adverse slip each side",
        caveats=[
          "Stage11 and Stage13 original entry criteria reused, no future information",
          "Previous-month regime values lag one calendar month, in Asia/Kolkata",
          "Higher-timeframe ADX and volume are from complete 4H/1H bars",
          "A no-trade month is not a winning month; sparse models excluded by sample gate",
          "Trade variants are standalone and overlap; never add net PnL across configurations",
          "All historical 2026 windows have already been used in research; no virgin holdout",
          "No bid/ask spread history, funding cashflows, order book impact, margin or liquidation",
          "1m OHLC stop-first, gapped stops fill at worse open or stop; intraminute uncertainty",
          "Many tested conditions create multiple-testing/selection bias",
          "Net BTC price points, not risk-sized dollar account monthly return",
          "2026-10-31 missing from source; 2026-11 through the 16th only",
          "Nothing establishes zero-loss months or future profitability"])
    (OUT/"quality.json").write_text(json.dumps(meta,indent=2)+"\n")
    chosen=ranked.head(5)[["family","regime","target_R","max_hold_min"]]
    if len(chosen):
        m=monthly.merge(chosen,on=["family","regime","target_R","max_hold_min"],how="inner")
        m.to_csv(OUT/"top_2025_candidate_months.csv",index=False)
    top=ranked[["family","regime","target_R","max_hold_min",
                "year2025_n","profit_months_2025","loss_months_2025","net_2025",
                "year2026_n","profit_months_2026","loss_months_2026","net_2026"]]
    report=[
      "# Stage14 — Finding monthly consistency from known-at-entry BTC market regime",
      "",
      "## What was measured",
      "Original Stage11 eight market-structure entry families and Stage13 two trend-pullback variants.",
      "Each compared across 12 predeclared 4H/1H/previous-month regimes, 2R/3R",
      "and 4h/8h maximum holds. Entries can occur at any time. Same structural stop.",
      "1m conservative stop-first replay and standard fees/GST/slippage.",
      "",
      "## Monthly consistency gate",
      meta["gate"],"",
      "Months with no trades are shown separately and cannot count as profitable.",
      "2026 windows are research-exposed and NOT independent tests.",
      "",
      f"**Models passing the research gate: {len(passes)} / {len(criteria)}**",
      "",
      "## 2025-selected leaders, and their actual 2026 behavior",
      top.to_markdown(index=False),"",
      "## Passing models",
      passes.to_markdown(index=False) if len(passes) else "None passed the predeclared criteria.",
      "",
      "## Monthly results for those 2025-selected leaders",
      m.to_markdown(index=False) if len(chosen) else "No models with adequate 2025 history.",
      "",
      "## Limitations",
      *["- "+c for c in meta["caveats"]],
      "",
      "Scripts and full trade logs are saved. To establish forward profitability",
      "freeze a single model and evaluate data acquired after this research.",
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("STAGE14_COMPLETE "+json.dumps({
      "events":len(ev),"trades":len(tr),
      "models":len(criteria),"passed":len(passes)}))
    print("TOP_2025_RANKED\n"+top.to_string(index=False))
    print("PASSED\n"+passes.to_string(index=False))
if __name__=="__main__":
    main()
