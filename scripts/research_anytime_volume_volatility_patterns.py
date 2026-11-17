#!/usr/bin/env python3
"""Stage 8: anywhere-in-time BTCUSD directional price/volume/volatility patterns.

Research question: can a sequence of fully closed 5-minute candles, independent
of clock time, anticipate +200 gross or NET BTCUSD points before a stop?

Event decision is at a COMPLETED 5m candle's closing boundary. Entry is the
same timestamp's NEXT 1m OPEN. No signal uses entry-candle information.
All historical periods have been seen previously, so chronological checks
are stability tests, NOT untouched out-of-sample validation.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from research_every_candle_200 import (
    read_archive, periods, first_passage, STOP, MAX_MINUTES, FEE, SLIPPAGE,
    PERIOD_NAMES
)

OUT=Path("analysis/institutional_discovery_stage8_dynamic_patterns")
HORIZONS=(30,60)
STOPS=(100,200)
TP_MODELS=("gross200","net200")
SIDE_NAMES={1:"LONG",-1:"SHORT"}
MIN_OBS=30


def detect(f):
    """Completed 5m bars with previous 24 five-minute bars as baseline."""
    a=f[["open","high","low","close","volume"]].resample(
        "5min",closed="left",label="right").agg({
        "open":"first","high":"max","low":"min","close":"last",
        "volume":"sum"})
    a["count"]=f.close.resample("5min",closed="left",label="right").count()
    a["rng"]=a.high-a.low
    a["body"]=a.close-a.open
    a["loc"]=(a.close-a.low)/a.rng.replace(0,np.nan)
    # Reference only PRIOR fully completed bars. No current-bar contribution.
    a["rmed"]=a.rng.rolling(24,min_periods=24).median().shift(1)
    a["vmean"]=a.volume.rolling(24,min_periods=24).mean().shift(1)
    a["rr"]=a.rng/a.rmed.replace(0,np.nan)
    a["vr"]=a.volume/a.vmean.replace(0,np.nan)
    a["ph12"]=a.high.rolling(12,min_periods=12).max().shift(1)
    a["pl12"]=a.low.rolling(12,min_periods=12).min().shift(1)
    a["ph24"]=a.high.rolling(24,min_periods=24).max().shift(1)
    a["pl24"]=a.low.rolling(24,min_periods=24).min().shift(1)
    a["bodyshare"]=abs(a.body)/a.rng.replace(0,np.nan)
    # Make all early and gap-adjacent bars ineligible.
    a["complete"]=((a["count"].rolling(30,min_periods=30).min()==5)&
                   (a["count"]==5)&a.rr.notna()&a.vr.notna())
    pos=a.body>0
    neg=a.body<0
    upstrong=pos&(a["loc"]>=.80)&(a.bodyshare>=.50)
    dnstrong=neg&(a["loc"]<=.20)&(a.bodyshare>=.50)
    event={}
    def add(name,long,short):
        event[name]=(long.fillna(False)&a.complete,
                     short.fillna(False)&a.complete)
    # Thresholds all relative to historic bar activity, not a fixed time.
    add("A_volume2_range2_directional",
        (a.vr>=2)&(a.rr>=2)&upstrong,
        (a.vr>=2)&(a.rr>=2)&dnstrong)
    add("B_volume3_range2_directional",
        (a.vr>=3)&(a.rr>=2)&upstrong,
        (a.vr>=3)&(a.rr>=2)&dnstrong)
    add("C_volume2_range1p5_directional",
        (a.vr>=2)&(a.rr>=1.5)&upstrong,
        (a.vr>=2)&(a.rr>=1.5)&dnstrong)
    add("D_volume2_12bar_breakout",
        (a.vr>=2)&(a.rr>=1.5)&upstrong&(a.close>a.ph12),
        (a.vr>=2)&(a.rr>=1.5)&dnstrong&(a.close<a.pl12))
    add("E_volume2_24bar_breakout",
        (a.vr>=2)&(a.rr>=1.5)&upstrong&(a.close>a.ph24),
        (a.vr>=2)&(a.rr>=1.5)&dnstrong&(a.close<a.pl24))
    add("F_volume2_liquidity_sweep_reject",
        (a.vr>=2)&(a.rr>=1.5)&(a.low<a.pl12)&
        (a.close>a.pl12)&(a["loc"]>=.75),
        (a.vr>=2)&(a.rr>=1.5)&(a.high>a.ph12)&
        (a.close<a.ph12)&(a["loc"]<=.25))
    add("G_volume3_sweep_reject",
        (a.vr>=3)&(a.rr>=1.5)&(a.low<a.pl12)&
        (a.close>a.pl12)&(a["loc"]>=.75),
        (a.vr>=3)&(a.rr>=1.5)&(a.high>a.ph12)&
        (a.close<a.ph12)&(a["loc"]<=.25))
    # Observe impulse then a separately completed follow-through candle.
    prior_up=upstrong.shift(1).fillna(False)
    prior_dn=dnstrong.shift(1).fillna(False)
    impulse=(a.vr.shift(1)>=2)&(a.rr.shift(1)>=1.5)
    add("H_5m_impulse_then_breakout",
        impulse&prior_up&upstrong&(a.close>a.high.shift(1))&(a.vr>=1),
        impulse&prior_dn&dnstrong&(a.close<a.low.shift(1))&(a.vr>=1))
    add("I_5m_impulse_then_hold",
        impulse&prior_up&(a.low>=a.low.shift(1))&
        (a.close>=a.close.shift(1))&pos&(a["loc"]>=.7),
        impulse&prior_dn&(a.high<=a.high.shift(1))&
        (a.close<=a.close.shift(1))&neg&(a["loc"]<=.3))
    # Previous candle is large but closes indecisively; subsequent bar
    # resolves its range with a strong CLOSE outside the large candle.
    prior_absorb=(a.vr.shift(1)>=2)&(a.bodyshare.shift(1)<=.3)&(a.rr.shift(1)>=1.2)
    add("J_absorption_then_resolution",
        prior_absorb&upstrong&(a.close>a.high.shift(1))&(a.vr>=1.25),
        prior_absorb&dnstrong&(a.close<a.low.shift(1))&(a.vr>=1.25))
    # Prior-three-bar contraction plus present bar's participation surge.
    contraction=((a.rng.shift(1)+a.rng.shift(2)+a.rng.shift(3))/3 <=
                 .65*a.rmed)
    add("K_compression_to_expansion",
        contraction&(a.vr>=2)&(a.rr>=1.5)&upstrong&(a.close>a.ph12),
        contraction&(a.vr>=2)&(a.rr>=1.5)&dnstrong&(a.close<a.pl12))
    # Up/down signed-volume PROXY from candle body; not actual taker flow.
    trend3_up=(a.close>a.close.shift(1))&(a.close.shift(1)>a.close.shift(2))&(
        a.close.shift(2)>a.close.shift(3))
    trend3_dn=(a.close<a.close.shift(1))&(a.close.shift(1)<a.close.shift(2))&(
        a.close.shift(2)<a.close.shift(3))
    acceler=(a.volume>a.volume.shift(1))&(a.volume.shift(1)>a.volume.shift(2))
    add("L_3bar_volume_acceleration",
        trend3_up&acceler&(a.vr>=1.5)&upstrong,
        trend3_dn&acceler&(a.vr>=1.5)&dnstrong)
    # A strong impulse loses acceptance in the next 5m: reversal bet.
    midprev=(a.high.shift(1)+a.low.shift(1))/2
    add("M_exhaustion_reversal",
        impulse&prior_dn&upstrong&(a.close>midprev)&(a.vr>=1.25),
        impulse&prior_up&dnstrong&(a.close<midprev)&(a.vr>=1.25))
    # A volatility regime jump after previously calm candles.
    quiet=(a.rr.shift(1)<.8)&(a.rr.shift(2)<.8)
    add("N_quiet_then_volume2_range2",
        quiet&(a.vr>=2)&(a.rr>=2)&upstrong,
        quiet&(a.vr>=2)&(a.rr>=2)&dnstrong)
    # Price/volume agreement but avoid most stretched events.
    add("O_moderate_expansion_breakout",
        (a.vr>=1.5)&(a.vr<3)&(a.rr>=1.2)&(a.rr<2)&
        upstrong&(a.close>a.ph12),
        (a.vr>=1.5)&(a.vr<3)&(a.rr>=1.2)&(a.rr<2)&
        dnstrong&(a.close<a.pl12))
    # Volume very high without a proportionate candle range, plus direction.
    add("P_volume_absorption_unconfirmed",
        (a.vr>=3)&(a.rr<=1.2)&upstrong,
        (a.vr>=3)&(a.rr<=1.2)&dnstrong)
    add("Q_volume2_range2_strong_wick",
        (a.vr>=2)&(a.rr>=2)&pos&(a["loc"]>=.95),
        (a.vr>=2)&(a.rr>=2)&neg&(a["loc"]<=.05))
    return a,event


def build_events(f,seg_start,seg_end,p,a,patterns):
    fi=f.index
    candidate=[]
    omitted=0
    for label,(up,down) in patterns.items():
        for side,signals in ((1,up),(-1,down)):
            for ts in a.index[signals.to_numpy(bool)]:
                k=int(fi.searchsorted(ts))
                if k>=len(fi) or fi[k]!=ts:continue
                if k-seg_start[k]<180 or seg_end[k]-k<MAX_MINUTES:continue
                if p[k]!=p[k+MAX_MINUTES-1]:continue
                candidate.append((label,side,k,float(a.at[ts,"vr"]),float(a.at[ts,"rr"])))
    if not candidate:raise ValueError("No eligible patterns")
    ev=pd.DataFrame(candidate,columns=["pattern","side","k","volume_ratio","range_ratio"])
    ev["period"]=np.array(PERIOD_NAMES,dtype=object)[p[ev.k.to_numpy()]]
    ev["entry_utc"]=fi[ev.k.to_numpy()].astype(str)
    ev["direction"]=ev.side.map(SIDE_NAMES)
    return ev


def first_passage_stats(ev,t200,tnet,tstop,mae):
    data=[]
    for (pat,side,period),g in ev.groupby(["pattern","side","period"],sort=True):
        k=g.k.to_numpy(np.int32)
        d=0 if side==1 else 1
        tg=t200[k,d]; nt=tnet[k,d]
        s100=tstop[k,d,3];s200=tstop[k,d,5]
        for horizon in HORIZONS:
            gross=(tg>=0)&(tg<horizon)
            net=(nt>=0)&(nt<horizon)
            grossfirst100=gross&((s100<0)|(tg<s100))
            netfirst100=net&((s100<0)|(nt<s100))
            grossfirst200=gross&((s200<0)|(tg<s200))
            zero_adverse=gross&(mae[k,d]<=0)
            data.append(dict(pattern=pat,direction=SIDE_NAMES[side],period=period,
                horizon_min=horizon,signals=len(k),
                gross200_pct=round(100*gross.mean(),2),
                gross200_before_sl100_pct=round(100*grossfirst100.mean(),2),
                gross200_before_sl200_pct=round(100*grossfirst200.mean(),2),
                net200_possible_pct=round(100*net.mean(),2),
                net200_before_sl100_pct=round(100*netfirst100.mean(),2),
                clean_gross200_pct=round(100*zero_adverse.mean(),3),
                avg_volume_ratio=round(float(g.volume_ratio.mean()),2),
                avg_range_ratio=round(float(g.range_ratio.mean()),2)))
    return pd.DataFrame(data)


def run_trade(k,side,stop,horizon,target_mode,op,cl,t200,tnet,tstop):
    d=0 if side==1 else 1
    entrymid=float(op[k])
    goal=(200.+2*SLIPPAGE+2*FEE*entrymid)/(1-FEE*side)
    target_pts=200. if target_mode=="gross200" else goal
    t=int(t200[k,d] if target_mode=="gross200" else tnet[k,d])
    si=int(np.flatnonzero(STOP==stop)[0])
    st=int(tstop[k,d,si])
    if t>=horizon:t=-1
    if st>=horizon:st=-1
    if st>=0 and (t<0 or st<=t):
        j=k+st; reason="stop"
        level=entrymid-side*stop
        exitmid=(min(float(op[j]),level) if side==1
                 else max(float(op[j]),level))
    elif t>=0:
        j=k+t;reason="target"
        exitmid=entrymid+side*target_pts
    else:
        j=k+horizon-1; reason="timeout"
        exitmid=float(cl[j])
    fin=entrymid+side*SLIPPAGE
    fout=exitmid-side*SLIPPAGE
    realized=side*(fout-fin)
    fees=FEE*(fin+fout)
    netstd=realized-fees
    # Historical offer is conditional/unverified. 30m exit waiver only.
    netoffer=realized-FEE*fin-(0 if j-k+1<=30 else FEE*fout)
    return j,reason,round(side*(exitmid-entrymid),3),round(netstd,3),round(netoffer,3)


def replay(ev,p,op,cl,t200,tnet,tstop):
    records=[]
    for (pattern,side), g in ev.groupby(["pattern","side"],sort=True):
        kk=g.k.to_numpy(np.int32)
        pp=p[kk]
        for model in TP_MODELS:
            for stop in STOPS:
                for horizon in HORIZONS:
                    last=-1
                    for k,period_id in zip(kk,pp):
                        if k<=last: continue
                        j,why,gross,net,offer=run_trade(
                            k,side,stop,horizon,model,op,cl,t200,tnet,tstop)
                        last=j
                        records.append(dict(pattern=pattern,side=side,
                            direction=SIDE_NAMES[side],period=PERIOD_NAMES[period_id],
                            model=f"{model}_sl{stop}_{horizon}m",
                            entry_index=int(k),exit_index=int(j),reason=why,
                            gross_pts=gross,net_pts=net,offer_whatif_pts=offer,
                            holding_minutes=int(j-k+1)))
    return pd.DataFrame(records)


def summarize(tr):
    all_rows=[]
    for keys,g in tr.groupby(["pattern","direction","period","model"],sort=True):
        for mode,column in (("standard_taker","net_pts"),
                            ("scalper_hypothetical","offer_whatif_pts")):
            v=g[column].to_numpy(float)
            wins=v[v>0].sum()
            losses=-v[v<0].sum()
            eq=np.r_[0,np.cumsum(v)]
            all_rows.append(dict(zip(["pattern","direction","period","model"],keys),
                fee_mode=mode,trades=len(g),win_pct=round(100*(v>0).mean(),2),
                winners=int((v>0).sum()),losses_or_flat=int((v<=0).sum()),
                mean_net_pts=round(float(v.mean()),3),
                sum_net_pts=round(float(v.sum()),2),
                worst_trade_pts=round(float(v.min()),2),
                profit_factor=round(float(wins/losses),3) if losses else None,
                max_drawdown_pts=round(float(np.max(np.maximum.accumulate(eq)-eq)),2),
                target_hits=int((g.reason=="target").sum()),
                avg_duration_min=round(float(g.holding_minutes.mean()),1)))
    return pd.DataFrame(all_rows)


def robust_check(summary):
    """Pre-declared rule selection: 2025 and both 2026 seen windows must be positive."""
    rows=[]
    std=summary[summary.fee_mode=="standard_taker"]
    for (pattern,direction,model),group in std.groupby(
            ["pattern","direction","model"],sort=True):
        periods={z.period:z for z in group.itertuples()}
        a=periods.get("2025_train")
        b=periods.get("2026_H1_validation")
        c=periods.get("2026_H2_seen_recheck")
        if not all((a,b,c)):continue
        robust=(a.trades>=60 and b.trades>=30 and c.trades>=30
                and a.mean_net_pts>0 and b.mean_net_pts>0 and c.mean_net_pts>0)
        rows.append(dict(pattern=pattern,direction=direction,model=model,
            train_trades=a.trades,train_net=a.mean_net_pts,
            H1_trades=b.trades,H1_net=b.mean_net_pts,
            H2_trades=c.trades,H2_net=c.mean_net_pts,stable_positive=robust))
    return pd.DataFrame(rows)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    f,seg_start,seg_end,quality=read_archive()
    p=periods(f.index)
    a,signals=detect(f)
    ev=build_events(f,seg_start,seg_end,p,a,signals)
    op=f.open.to_numpy(np.float64)
    hi=f.high.to_numpy(np.float64)
    lo=f.low.to_numpy(np.float64)
    cl=f.close.to_numpy(np.float64)
    t200,tnet,tstop,mae=first_passage(op,hi,lo,seg_end,STOP,MAX_MINUTES)
    rates=first_passage_stats(ev,t200,tnet,tstop,mae)
    tr=replay(ev,p,op,cl,t200,tnet,tstop)
    sm=summarize(tr)
    stable=robust_check(sm)
    # Do not git-add full per-trade ledger (available as workflow artifact).
    ev.to_csv(OUT/"events.csv.gz",index=False,
        compression={"method":"gzip","compresslevel":5,"mtime":0})
    tr.to_csv(OUT/"trade_ledger.csv.gz",index=False,
        compression={"method":"gzip","compresslevel":5,"mtime":0})
    rates.to_csv(OUT/"pattern_probabilities.csv",index=False)
    sm.to_csv(OUT/"strategy_results.csv",index=False)
    stable.to_csv(OUT/"chronological_stability.csv",index=False)
    nstable=int(stable.stable_positive.sum()) if len(stable) else 0
    metrics=dict(
        candles=len(f),first_utc=str(f.index[0]),last_utc=str(f.index[-1]),
        missing_minutes=quality["missing_minutes"],
        event_patterns=len(signals),eligible_directional_events=len(ev),
        simulated_trades=len(tr),report_rows=len(sm),
        robust_positive_patterns=nstable,
        standard_positive_cells=int(((sm.fee_mode=="standard_taker")&
                                      (sm.mean_net_pts>0)).sum()),
        standard_zero_loss_cells=int(((sm.fee_mode=="standard_taker")&
                                      (sm.losses_or_flat==0)).sum()),
        model=list(TP_MODELS),stop_points=list(STOPS),horizons_min=list(HORIZONS),
        fee_per_side=FEE,slippage_per_side_pts=SLIPPAGE,
        old_archive_studies="ALL 2026 windows have already been researched; none untouched",
        limitations=[
            "1m OHLC stop-first on same-bar ambiguity; tick fills unobserved",
            "Historical order book/spread, impact, funding, liquidation and margin not modeled",
            "Candle volume directional sign is a proxy, NOT real taker/order flow",
            "Positive cells from many variants may be random; no multiple-test adjustment",
            "Gross200 can be much less than 200 NET after fees",
            "5m completed candles enter at immediate following 1m OPEN only",
            "Multiple event models overlap, do NOT sum into a portfolio",
            "No stop guarantees no loss; overnight gaps may exceed stops",
            "Always need fresh forward research before live trading"])
    (OUT/"quality.json").write_text(json.dumps(metrics,indent=2)+"\n")
    show=rates[(rates.horizon_min==30)&
               (rates.period.isin(("2025_train","2026_H1_validation","2026_H2_seen_recheck")))]
    train=show[(show.period=="2025_train")&(show.signals>=60)].sort_values(
        ["gross200_before_sl100_pct","signals"],ascending=[False,False])
    # Freeze top train-ranked candidates for readable cross-period display.
    best=train.head(12)[["pattern","direction"]].drop_duplicates()
    bits=[]
    for z in best.itertuples():
        bits.append(show[(show.pattern==z.pattern)&
                         (show.direction==z.direction)])
    audited=pd.concat(bits,ignore_index=True) if bits else show.iloc[:0]
    net=sm[(sm.fee_mode=="standard_taker")&
           (sm.model=="gross200_sl100_30m")]
    winner=sm[(sm.fee_mode=="standard_taker")].sort_values("mean_net_pts",
                                                        ascending=False).head(12)
    report=[
        "# Stage 8 — Anytime BTCUSD directional participation patterns",
        "",
        "## Test definition",
        "- Use genuine Delta India BTCUSD 1m OHLCV resampled into complete 5m bars.",
        "- Signal uses only **fully completed** candles and previous 24 complete 5m bars.",
        "- Entry always at the next 1m candle's OPEN, not signal-bar extreme.",
        "- Identify relative volume and volatility spikes; test breakouts, failed sweeps,",
        "  follow-through, absorption, 3-bar momentum, compression, exhaustion, etc.",
        "- Evaluate first passage to +200 GROSS and +200 NET (price-scaled fee threshold)",
        "  before stops 100/200, in 30 and 60 minute windows.",
        "- Replay one position at a time per pattern/side/model. Same-bar stop prioritized.",
        "- Cost: taker 0.05% per side, GST 18% on fees, 5 points adverse slip each side.",
        "- Scam prevention: +200 in the future does not imply a deployable direction prediction.",
        "- Chronology used for stability, NOT pristine validation; 2026 already inspected.",
        "",
        "## 2025 highest directional probabilities, followed by both 2026 windows",
        audited.to_markdown(index=False), "",
        "## 200 gross target / 100 stop / 30-minute hold: selected rule outcomes",
        net[["pattern","direction","period","trades","win_pct",
             "mean_net_pts","profit_factor","losses_or_flat"]].to_markdown(index=False), "",
        "## Top historical net cells (exploratory only)",
        winner[["pattern","direction","period","model","trades",
                "win_pct","mean_net_pts","losses_or_flat"]].to_markdown(index=False), "",
        "## Stable positive expectancy across known chronological periods",
        f"**{nstable}** of {len(stable)} candidate rule-direction-model triples"
        " achieved positive net results in 2025, Jan-Jun 2026, AND Jul-Oct 2026"
        " with at least 60/30/30 non-overlapping trades respectively.",
        "", stable[stable.stable_positive].to_markdown(index=False)
            if nstable else "None found at the predeclared sample thresholds.",
        "",
        "## Caveats",
        *["- "+v for v in metrics["limitations"]],
        "",
        "## Files",
        "- pattern_probabilities.csv: every pattern, period, side and horizon",
        "- strategy_results.csv: all fee, stop and horizon variants",
        "- chronological_stability.csv: selection audit",
        "- events.csv.gz and trade_ledger.csv.gz: full evidence in Actions artifacts",
        "- quality.json: test assumptions",
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("STAGE8_DONE "+json.dumps(metrics))
    print("TOP_TRAIN_GROSS_TP100 "+train.head(15).to_string(index=False))
    print("STABLE "+stable[stable.stable_positive].to_string(index=False))
    print("TOP_MODEL_NET "+winner.to_string(index=False))
    print("PATTERN_NET_200_100_30 "+net.to_string(index=False))

if __name__=="__main__":
    main()
