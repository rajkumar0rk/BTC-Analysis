#!/usr/bin/env python3
"""Stage 11: BTC market-structure entry patterns with STRUCTURAL stops and R:R exits.

Unlike fixed 200-point tests, entry determines stop from already-confirmed
swing / sweep / breakout support; TP = entry +/- risk * (1.5,2,3,4).
5m signals are known only at full 5m close. Order at same timestamp's 1m OPEN.
Test all hours, both directions. No fixed-time requirement. Historical research
exposure means the 2026 chronological checks are NOT pristine out-of-sample.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from numba import njit
from research_every_candle_200 import (
    read_archive, periods, PERIOD_NAMES, FEE, SLIPPAGE
)

OUT=Path("analysis/institutional_discovery_stage11_structure_rr")
MAX_HOLD=240
RATIOS=(1.5,2.,3.,4.)
HOLDS=(60,240)
RISK_BANDS={"tight_100_700":(100.,700.),"wide_200_1200":(200.,1200.)}
VOL_FILTERS={"any_volume":1.0,"volume_ge_1p5x":1.5}
SIDE={1:"LONG",-1:"SHORT"}


def candidates(f,seg_start,seg_end,period):
    """8 distinct completed 5m pattern families, with symmetric LONG/SHORT."""
    b=f[["open","high","low","close","volume"]].resample(
        "5min",label="right",closed="left").agg({
        "open":"first","high":"max","low":"min","close":"last","volume":"sum"})
    b["count"]=f.close.resample("5min",label="right",closed="left").count()
    b["span"]=b.high-b.low
    b["location"]=(b.close-b.low)/b.span.replace(0,np.nan)
    b["rmed"]=b.span.shift(1).rolling(24,min_periods=24).median()
    b["vmean"]=b.volume.shift(1).rolling(24,min_periods=24).mean()
    b["vr"]=b.volume/b.vmean.replace(0,np.nan)
    b["rr"]=b.span/b.rmed.replace(0,np.nan)
    b["ph12"]=b.high.shift(1).rolling(12,min_periods=12).max()
    b["pl12"]=b.low.shift(1).rolling(12,min_periods=12).min()
    b["ph6"]=b.high.shift(1).rolling(6,min_periods=6).max()
    b["pl6"]=b.low.shift(1).rolling(6,min_periods=6).min()
    b["ph3"]=b.high.shift(1).rolling(3,min_periods=3).max()
    b["pl3"]=b.low.shift(1).rolling(3,min_periods=3).min()
    complete=(b["count"].rolling(34,min_periods=34).min()==5)&(
        b.rmed>0)&(b.vmean>0)
    bull=(b.close>b.open)&(b.location>=.7)
    bear=(b.close<b.open)&(b.location<=.3)
    buffer=np.maximum(10.,b.rmed*.10)
    prior_green=(b.close.shift(1)>b.open.shift(1))
    prior_red=(b.close.shift(1)<b.open.shift(1))
    patterns={}
    def add(name, long, short, long_stop, short_stop):
        patterns[name]=(long.fillna(False)&complete,
                        short.fillna(False)&complete,
                        long_stop,short_stop)

    # 1. Single-bar rejection after a known 12-bar liquidity sweep.
    add("01_sweep_rejection",
        (b.low<b.pl12)&(b.close>b.pl12)&bull,
        (b.high>b.ph12)&(b.close<b.ph12)&bear,
        b.low-buffer,b.high+buffer)

    # 2. A sweep, then a SEPARATE completed bar confirms reversal.
    prior_sweepL=(b.low.shift(1)<b.low.shift(2).rolling(12).min())&(
        b.close.shift(1)>b.low.shift(2).rolling(12).min())
    prior_sweepS=(b.high.shift(1)>b.high.shift(2).rolling(12).max())&(
        b.close.shift(1)<b.high.shift(2).rolling(12).max())
    add("02_sweep_then_confirm",
        prior_sweepL & bull & (b.close>b.high.shift(1)),
        prior_sweepS & bear & (b.close<b.low.shift(1)),
        pd.concat((b.low,b.low.shift(1)),axis=1).min(axis=1)-buffer,
        pd.concat((b.high,b.high.shift(1)),axis=1).max(axis=1)+buffer)

    # 3. Break prior known 12-bar range and retest its level on NEXT bar.
    prior_breakL=(b.close.shift(1)>b.high.shift(2).rolling(12).max())&(
        b.location.shift(1)>=.7)
    prior_breakS=(b.close.shift(1)<b.low.shift(2).rolling(12).min())&(
        b.location.shift(1)<=.3)
    high_level=b.high.shift(2).rolling(12).max()
    low_level=b.low.shift(2).rolling(12).min()
    add("03_breakout_retest",
        prior_breakL & (b.low<=high_level+.20*b.rmed)&(
            b.close>high_level)&bull,
        prior_breakS & (b.high>=low_level-.20*b.rmed)&(
            b.close<low_level)&bear,
        pd.concat((b.low,b.low.shift(1)),axis=1).min(axis=1)-buffer,
        pd.concat((b.high,b.high.shift(1)),axis=1).max(axis=1)+buffer)

    # 4. Prior 12-bar trend + opposite-colored pullback + engulf/reclaim.
    trendL=(b.close.shift(2)-b.close.shift(14)>=2*b.rmed)
    trendS=(b.close.shift(2)-b.close.shift(14)<=-2*b.rmed)
    add("04_trend_pullback_engulf",
        trendL & prior_red & bull & (b.close>b.open.shift(1)),
        trendS & prior_green & bear & (b.close<b.open.shift(1)),
        pd.concat((b.low,b.low.shift(1)),axis=1).min(axis=1)-buffer,
        pd.concat((b.high,b.high.shift(1)),axis=1).max(axis=1)+buffer)

    # 5. Short-term structure shift: close beyond prior 3-bar structure
    # after a bearish/bullish 6-bar displacement.
    down6=(b.close.shift(1)-b.close.shift(7)<-2*b.rmed)
    up6=(b.close.shift(1)-b.close.shift(7)>2*b.rmed)
    add("05_market_structure_shift",
        down6 & bull & (b.close>b.ph3)&(b.rr>=1.),
        up6 & bear & (b.close<b.pl3)&(b.rr>=1.),
        pd.concat((b.low,b.low.shift(1),b.low.shift(2)),axis=1).min(axis=1)-buffer,
        pd.concat((b.high,b.high.shift(1),b.high.shift(2)),axis=1).max(axis=1)+buffer)

    # 6. Complete inside bar, followed by confirmed breakout of mother range.
    inside=(b.high.shift(1)<b.high.shift(2))&(
        b.low.shift(1)>b.low.shift(2))
    add("06_inside_bar_break",
        inside & bull & (b.close>b.high.shift(2)) & (b.rr>=1.),
        inside & bear & (b.close<b.low.shift(2)) & (b.rr>=1.),
        pd.concat((b.low,b.low.shift(1),b.low.shift(2)),axis=1).min(axis=1)-buffer,
        pd.concat((b.high,b.high.shift(1),b.high.shift(2)),axis=1).max(axis=1)+buffer)

    # 7. A completed failed breakout followed by opposite-direction bar.
    prev_false_long=(b.low.shift(1)<b.low.shift(2).rolling(12).min())&(
        b.close.shift(1)>b.low.shift(2).rolling(12).min())
    prev_false_short=(b.high.shift(1)>b.high.shift(2).rolling(12).max())&(
        b.close.shift(1)<b.high.shift(2).rolling(12).max())
    add("07_failed_break_followthrough",
        prev_false_long&bull&(b.close>b.close.shift(1))&(b.vr>=1.2),
        prev_false_short&bear&(b.close<b.close.shift(1))&(b.vr>=1.2),
        pd.concat((b.low,b.low.shift(1)),axis=1).min(axis=1)-buffer,
        pd.concat((b.high,b.high.shift(1)),axis=1).max(axis=1)+buffer)

    # 8. Expansion after three lower-range candles, confirmed 6bar breakout.
    shrink=(b.span.shift(1)+b.span.shift(2)+b.span.shift(3))/3 <= .75*b.rmed
    add("08_compression_breakout",
        shrink & bull &(b.close>b.ph6)&(b.rr>=1.5),
        shrink & bear &(b.close<b.pl6)&(b.rr>=1.5),
        pd.concat((b.low,b.low.shift(1),b.low.shift(2)),axis=1).min(axis=1)-buffer,
        pd.concat((b.high,b.high.shift(1),b.high.shift(2)),axis=1).max(axis=1)+buffer)

    ix=f.index
    entrydata=[]
    missing=0
    for pattern, (l,s,st_l,st_s) in patterns.items():
        for side,mask,stops in ((1,l,st_l),(-1,s,st_s)):
            times=b.index[mask.to_numpy(bool)]
            pos=ix.get_indexer(times)
            keep=pos>=0
            times=times[keep];pos=pos[keep]
            for ts,k in zip(times,pos):
                if k-seg_start[k]<200 or seg_end[k]-k<MAX_HOLD:
                    missing+=1;continue
                if period[k]!=period[k+MAX_HOLD-1]:
                    continue
                stop=float(stops.at[ts]);entry=float(f.open.iloc[k])
                risk=side*(entry-stop)
                if not np.isfinite(risk) or risk<=0:
                    continue
                vr=float(b.at[ts,"vr"]);rr=float(b.at[ts,"rr"])
                entrydata.append((pattern,side,int(k),int(f.time.iloc[k]),
                                  stop,risk,vr,rr,int(period[k])))
    if not entrydata: raise ValueError("No setup events")
    cand=pd.DataFrame(entrydata,columns=["pattern","side","k","unix",
                    "stop_price","risk_points","volume_ratio","range_ratio","period_code"])
    cand["period"]=np.asarray(PERIOD_NAMES,dtype=object)[cand.period_code.to_numpy()]
    cand["direction"]=cand.side.map(SIDE)
    return cand,dict(patterns=len(patterns),skipped_missing_or_incomplete=missing,
                     raw_eligible=len(cand))


@njit(cache=True)
def replay_one(O,H,L,C,entry_idx,side,stop_price,target_r,horizon):
    """Midprice OHLC replay; stop priority, target not overfilled if gap."""
    entry=O[entry_idx]
    risk=side*(entry-stop_price)
    target=entry+side*risk*target_r
    end=entry_idx+horizon
    for j in range(entry_idx,end):
        hitstop=L[j]<=stop_price if side==1 else H[j]>=stop_price
        hittake=H[j]>=target if side==1 else L[j]<=target
        if hitstop:
            exitmid=min(O[j],stop_price) if side==1 else max(O[j],stop_price)
            reason=0
            break
        if hittake:
            exitmid=target
            reason=1
            break
    else:
        j=end-1
        exitmid=C[j]
        reason=2
    fillin=entry+side*SLIPPAGE
    fillout=exitmid-side*SLIPPAGE
    gross=side*(exitmid-entry)
    net=side*(fillout-fillin)-FEE*(fillin+fillout)
    fee_offer=side*(fillout-fillin)-FEE*fillin-(0.0 if j-entry_idx+1<=30 else FEE*fillout)
    return j,reason,gross,net,fee_offer,net/risk,risk


def execute(candidates, O,H,L,C):
    records=[]
    # One position across both directions, each predefined standalone model.
    for pat,g in candidates.groupby("pattern",sort=True):
        for vname,vmin in VOL_FILTERS.items():
            v=g[g.volume_ratio>=vmin]
            if v.empty:continue
            for riskname,(minrisk,maxrisk) in RISK_BANDS.items():
                filt=v[(v.risk_points>=minrisk)&(v.risk_points<=maxrisk)].sort_values(
                    ["k","side"])
                if filt.empty:continue
                entries=list(filt.itertuples(index=False))
                for rr in RATIOS:
                    for hold in HOLDS:
                        busy=-1
                        for z in entries:
                            if z.k<=busy:continue
                            last,reason,gross,net,offer,actualR,risk=replay_one(
                                O,H,L,C,int(z.k),int(z.side),float(z.stop_price),float(rr),int(hold))
                            busy=int(last)
                            records.append((pat,vname,riskname,rr,hold,z.period,z.direction,
                                int(z.unix),int(z.unix+60*(last-z.k)),
                                round(float(risk),2),int(reason),round(float(gross),2),
                                round(float(net),2),round(float(offer),2),
                                round(float(actualR),4),int(last-z.k+1)))
    return pd.DataFrame(records,columns=["pattern","vol_filter","risk_band","target_R",
         "hold_min","period","direction","entry_unix","exit_unix","risk_pts",
         "reason_code","gross_pts","net_pts","offer_whatif_pts","realized_net_R",
         "held_minutes"])


def summarize(tr):
    rows=[]
    keys=["pattern","vol_filter","risk_band","target_R","hold_min","period"]
    for key,g in tr.groupby(keys,sort=True):
        for label,column in (("standard_taker","net_pts"),
                             ("scalper_hypothetical","offer_whatif_pts")):
            v=g[column].to_numpy(float)
            eq=np.r_[0.,np.cumsum(v)]
            wins=v[v>0].sum()
            losses=-v[v<0].sum()
            rows.append(dict(zip(keys,key),fee_model=label,trades=len(g),
                long_trades=int((g.direction=="LONG").sum()),
                short_trades=int((g.direction=="SHORT").sum()),
                win_pct=round(100*float((v>0).mean()),2),
                avg_net_pts=round(float(v.mean()),2),
                avg_net_R=round(float((g.realized_net_R).mean()),3) if label=="standard_taker" else None,
                net_total_pts=round(float(v.sum()),2),
                worst_net_pts=round(float(v.min()),2),
                profit_factor=round(float(wins/losses),3) if losses else None,
                max_drawdown_pts=round(float(np.max(np.maximum.accumulate(eq)-eq)),2),
                target_hit_pct=round(float((g.reason_code==1).mean()*100),2),
                avg_risk_pts=round(float(g.risk_pts.mean()),2),
                avg_hold_min=round(float(g.held_minutes.mean()),2),
                losing_trades=int((v<=0).sum())))
    return pd.DataFrame(rows)


def stability(summary):
    out=[]
    keys=["pattern","vol_filter","risk_band","target_R","hold_min"]
    z=summary[summary.fee_model=="standard_taker"]
    for key,g in z.groupby(keys,sort=True):
        d={p.period:p for p in g.itertuples(index=False)}
        if not all(x in d for x in PERIOD_NAMES[:3]):continue
        a,b,c=[d[n] for n in PERIOD_NAMES[:3]]
        adequate=(a.trades>=70 and b.trades>=35 and c.trades>=25)
        out.append(dict(zip(keys,key),
            trades_2025=a.trades,net_2025=a.avg_net_pts,
            trades_2026_h1=b.trades,net_2026_h1=b.avg_net_pts,
            trades_2026_h2=c.trades,net_2026_h2=c.avg_net_pts,
            sufficient_samples=adequate,
            consistent_positive=bool(adequate and
                min(a.avg_net_pts,b.avg_net_pts,c.avg_net_pts)>0)))
    return pd.DataFrame(out)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    f,seg_start,seg_end,q=read_archive()
    p=periods(f.index)
    c,quality=candidates(f,seg_start,seg_end,p)
    O=f.open.to_numpy(np.float64)
    H=f.high.to_numpy(np.float64)
    L=f.low.to_numpy(np.float64)
    C=f.close.to_numpy(np.float64)
    trades=execute(c,O,H,L,C)
    if trades.empty:raise ValueError("No executed models")
    report=summarize(trades)
    robust=stability(report)
    good=robust[robust.consistent_positive]
    trades.to_csv(OUT/"trade_ledger.csv.gz",index=False,
                  compression={"method":"gzip","mtime":0,"compresslevel":5})
    c.to_csv(OUT/"structural_events.csv.gz",index=False,
             compression={"method":"gzip","mtime":0,"compresslevel":5})
    report.to_csv(OUT/"rr_strategy_summary.csv",index=False)
    robust.to_csv(OUT/"chronological_stability.csv",index=False)
    standard=report[report.fee_model=="standard_taker"]
    detail=dict(source="Delta Exchange India 1m BTCUSD futures",candles=len(f),
        timestamps_from_utc=str(f.index[0]),timestamps_through_utc=str(f.index[-1]),
        missing_minutes=q["missing_minutes"],**quality,
        executed_independent_model_trades=len(trades),
        total_summary_cells=len(report),tested_R=list(RATIOS),
        tested_holding_windows=list(HOLDS),risk_limits=RISK_BANDS,
        relative_volume_filters=VOL_FILTERS,
        positive_standard_cells=int((standard.avg_net_pts>0).sum()),
        stable_positive_models=len(good),
        no_loss_standard_cells=int((standard.losing_trades==0).sum()),
        realistic_execution_assumptions=[
            "5m bars fully closed then enter at following minute's OPEN",
            "Risk is difference from entry OPEN to PRECONFIRMED market-structure stop",
            "Stop-first when both touch same 1m bar, gaps worse-of-open-or-stop",
            "Stop and TP frozen at entry: no dynamic lookahead or intrabar stop move",
            "Risk band filters use only entry-known risk, relative volume references prior 24 bars",
            "One open position across LONG+SHORT in each independent model",
            "Trading costs 0.05% taker each side plus 18% GST and 5pt per-side slippage",
            "Scalper offer only shown as hypothetical fee scenario if <=30m",
            "Funding, order book, actual bid-ask spread, liquidation and margin excluded",
            "Every 2026 segment has been researched before; no pristine forward sample",
            "Multiple patterns/R ratios can appear promising by chance",
            "Profit targets are a multiple of initial STRUCTURAL risk, not a fixed 200pts"
        ])
    (OUT/"quality.json").write_text(json.dumps(detail,indent=2)+"\n")
    sel=standard[(standard.target_R.isin((2.,3.)))&
                 (standard.hold_min==240)]
    # Rank based on 2025 only, display all later period results side by side.
    train=sel[(sel.period=="2025_train")&
              (sel.trades>=70)].sort_values("avg_net_pts",ascending=False).head(15)
    picks=train[["pattern","vol_filter","risk_band","target_R","hold_min"]].copy()
    compare=picks.merge(sel,on=["pattern","vol_filter","risk_band","target_R","hold_min"])
    report_text=[
        "# Stage 11 — Rule-based market-structure LONG/SHORT with structural SL and 1:2 / 1:3 R:R",
        "",
        "## Core: stop defines risk, target is risk multiple",
        "R = abs(next 1m entry OPEN - confirmed setup swing stop).",
        "Take profit uses 1.5R, 2R, 3R, or 4R. No fixed time or day of entry.",
        "Stop includes volatility-derived buffer from PREVIOUS completed 5m candles.",
        "Trade only if risk is in a fixed predeclared band; at most one trade concurrently",
        "across both directions per pattern/volume/risk/R/hold standalone strategy.",
        "Exit intraminute by conservative stop-first OHLC, else a forced 60/240m close.",
        "",
        "## 8 distinct event rules",
        "- 01: liquidity sweep of prior 12 bars, strong rejection close; stop beyond sweep",
        "- 02: sweep then separate confirmation candle; stop beyond 2-bar extreme",
        "- 03: 12-bar breakout, following-bar retest and holding close; stop below/above retest",
        "- 04: 12-bar trend, opposite pullback candle engulfed; stop beyond setup pair",
        "- 05: prior down/up displacement then break of 3-bar opposite structure",
        "- 06: inside candle, then decisive breakout of mother bar",
        "- 07: liquidity failed break then followthrough in reversal direction",
        "- 08: prior three 5m bars compressed then 6-bar breakout on expansion",
        "",
        "## Top 2025 candidates based on net points, 2R/3R 240min max, followed by already-seen 2026",
        compare[["pattern","vol_filter","risk_band","target_R","period",
                 "trades","long_trades","short_trades","win_pct","avg_net_pts",
                 "profit_factor","avg_risk_pts","losing_trades"]].to_markdown(index=False),"",
        "## Chronological research stability",
        robust.to_markdown(index=False),"",
        "## Consistent positive 2025/H1/H2 (sample minimum 70/35/25)",
        good.to_markdown(index=False) if len(good) else "No tested combination meets these requirements.", "",
        "## Why this is NOT a live signal yet",
        *["- "+x for x in detail["realistic_execution_assumptions"]],"",
        "## Reproduce",
        "- scripts/research_structure_rr_stage11.py",
        "- rr_strategy_summary.csv: all models, net expectancy, RR and drawdown",
        "- chronological_stability.csv: strict history consistency",
        "- trade_ledger.csv.gz and structural_events.csv.gz as GitHub Actions artifacts",
        "- quality.json: sample and execution settings",
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report_text)+"\n")
    print("STAGE11_DONE "+json.dumps({k:detail[k] for k in (
        "candles","raw_eligible","executed_independent_model_trades",
        "positive_standard_cells","stable_positive_models","no_loss_standard_cells")}))
    print("2025_SELECTED_2R_3R\n"+train.to_string(index=False))
    print("STABLE_POSITIVE\n"+good.to_string(index=False))
    print("R2R3_2026_H1_TOP\n"+
          sel[(sel.period=="2026_H1_validation")&(sel.trades>=35)].
          sort_values("avg_net_pts",ascending=False).head(12).to_string(index=False))
    print("R2R3_2026_H2_TOP\n"+
          sel[(sel.period=="2026_H2_seen_recheck")&(sel.trades>=25)].
          sort_values("avg_net_pts",ascending=False).head(12).to_string(index=False))

if __name__=="__main__":
    main()
