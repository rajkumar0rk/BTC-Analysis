#!/usr/bin/env python3
"""Stage 5: Test whether volatility-scaled exits rescue predeclared directional signals.

This is new EXIT logic, not another indicator search. All outcomes historical,
including already-seen 2026 H2. No live edge is claimed.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from research_retest_reclaim_stage4 import aligned_features, STANDARD_SIDE_FEE, SLIP
from research_directional_acceptance import signals

OUT = Path("analysis/institutional_discovery_stage5")
HORIZON = 240
TESTS = {
    "fixed_60m_reference": dict(mode="fixed", max_bars=60),
    "vol_2R_4h": dict(mode="vol_target", max_bars=240),
    "vol_trail_4h": dict(mode="vol_trail", max_bars=240),
    "vol_timeout_4h": dict(mode="vol_timeout", max_bars=240),
}
RULES = ("expansion_follow", "accepted_12h_breakout", "rejected_12h_sweep")
SEED = 20261117

def bucket(t):
    if t < pd.Timestamp("2026-01-01",tz="UTC"): return "2025_train"
    if t < pd.Timestamp("2026-07-01",tz="UTC"): return "2026_H1_validation"
    return "2026_H2_seen_recheck"

def simulate(op, hi, lo, cl, k, side, typical, mode, max_bars):
    mid = float(op[k])
    entry = mid + side * SLIP
    risk = float(np.clip(typical, 200, 1200))
    if mode == "fixed":
        risk, tgt = 350.0, 500.0
    else:
        risk, tgt = risk, 2.0*risk
    stop = mid-side*risk
    target = mid+side*tgt
    peak = 0.0
    max_good = 0.0
    max_bad = 0.0
    for j in range(k,min(k+max_bars,len(op))):
        # At an entry-minute gap or a prior candle-induced trailing stop,
        # use the worse open/stop fill, not an idealized stop price.
        stop_hit = (lo[j] <= stop) if side == 1 else (hi[j] >= stop)
        target_hit = (hi[j] >= target) if side == 1 else (lo[j] <= target)
        good = (float(hi[j])-mid) if side == 1 else (mid-float(lo[j]))
        bad = (mid-float(lo[j])) if side == 1 else (float(hi[j])-mid)
        max_good = max(max_good,good)
        max_bad = max(max_bad,bad)
        if stop_hit:
            exit_mid = min(float(op[j]),stop) if side==1 else max(float(op[j]),stop)
            reason = "stop"
            break
        if mode in ("fixed","vol_target") and target_hit:
            exit_mid = target
            reason = "target"
            break
        # Trailing stop is updated at completed minute close only,
        # and cannot stop out retroactively inside this same minute.
        if mode=="vol_trail":
            peak=max(peak, side*(float(cl[j])-mid))
            if peak >= 0.75*risk:
                proposed = float(cl[j])-side*0.50*risk
                stop = max(stop,proposed) if side==1 else min(stop,proposed)
    else:
        j = min(k+max_bars,len(op))-1
        exit_mid = float(cl[j])
        reason = "timeout"
    exit_fill=exit_mid-side*SLIP
    gross=side*(exit_mid-mid)
    net=side*(exit_fill-entry)-STANDARD_SIDE_FEE*(entry+exit_fill)
    return dict(last=j, reason=reason, risk_pts=risk,
        gross_pts=gross, net_pts=net,
        cost_pts=gross-net, mfe_pts=max_good,mae_pts=max_bad,
        hold_min=j-k+1)

def stats(tr):
    result=[]
    for keys,g in tr.groupby(["rule","exit_model","period"],sort=True):
        v=g.net_pts.to_numpy(float)
        eq=np.r_[0,np.cumsum(v)]
        gain=v[v>0].sum()
        loss=-v[v<0].sum()
        d=g.groupby("ny_date").net_pts.agg(["sum","count"]).to_numpy(float)
        low=high=np.nan
        if len(d)>=12 and len(g)>=20:
            rng=np.random.default_rng(SEED)
            idx=rng.integers(0,len(d),size=(350,len(d)))
            draws=d[idx].sum(axis=1)
            x=draws[:,0]/draws[:,1]
            low,high=np.quantile(x,[.025,.975])
        result.append(dict(zip(["rule","exit_model","period"],keys),
            trades=len(g),days=g.ny_date.nunique(),
            avg_net=round(float(v.mean()),2),
            win_pct=round(100*float((v>0).mean()),2),
            profit_factor=round(float(gain/loss),3) if loss else np.nan,
            max_drawdown_pts=round(float(np.max(np.maximum.accumulate(eq)-eq)),2),
            avg_gross=round(float(g.gross_pts.mean()),2),
            avg_cost=round(float(g.cost_pts.mean()),2),
            avg_mfe=round(float(g.mfe_pts.mean()),2),
            avg_mae=round(float(g.mae_pts.mean()),2),
            avg_hold_min=round(float(g.hold_min.mean()),1),
            ci95_low=round(float(low),2),ci95_high=round(float(high),2)))
    return pd.DataFrame(result)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    f,h,q=aligned_features()
    sig=signals(h)
    ix=f.index
    op=f.open.to_numpy(float);hi=f.high.to_numpy(float)
    lo=f.low.to_numpy(float);cl=f.close.to_numpy(float)
    records=[]
    count=0
    for rule in RULES:
        mask,sides=sig[rule]
        flat=np.flatnonzero(mask.to_numpy(bool))
        for model,args in TESTS.items():
            last_exit=-1
            for i in flat:
                t=h.index[i]
                enter_time=t+pd.Timedelta(hours=1)
                k=int(ix.searchsorted(enter_time))
                if k+HORIZON>=len(ix) or ix[k]!=enter_time or ix[k+HORIZON-1]!=enter_time+pd.Timedelta(minutes=HORIZON-1):
                    continue
                if k<=last_exit:
                    continue
                count+=1
                z=h.iloc[i]
                side=int(sides[i])
                sim=simulate(op,hi,lo,cl,k,side,float(z.typical),
                            args["mode"],args["max_bars"])
                last_exit=sim["last"]
                records.append(dict(rule=rule,exit_model=model,
                    period=bucket(t),ny_date=z.ny_date,side=side,
                    signal_utc=str(t),entry_utc=str(ix[k]),
                    exit_utc=str(ix[sim["last"]]),reason=sim["reason"],
                    **{a:round(float(v),4) if isinstance(v,(float,np.floating)) else v
                       for a,v in sim.items() if a!="last"}))
    df=pd.DataFrame(records)
    if df.empty:raise ValueError("No trades in Stage 5")
    sm=stats(df)
    df.to_csv(OUT/"trade_ledger.csv",index=False)
    sm.to_csv(OUT/"trade_summary.csv",index=False)
    meta=dict(source="Delta Exchange India archived 1m futures and matched mark/OI/funding",
        source_quality=q,replayed_trades=len(df),decisions_considered=count,
        rule_names=list(RULES),exit_models=TESTS,
        assumptions=dict(fee_per_side_plus_gst=STANDARD_SIDE_FEE,
            slippage_per_side_pts=SLIP,risk_pts="clipped prior 48h median hourly range 200..1200",
            volatility_target_R=2,trail_activation_R=.75,
            trailing_distance_R=.5,trail_updates="after each completed minute close only",
            signal="completed hourly candle; entry next hourly open",
            priority="stop first on ambiguous 1m bars",
            portfolios="non-overlapping trades independently within model/rule"),
        caveats=["The later 2026 period is previously researched, not untouched",
                 "Stop and take fills are 1m OHLC approximations",
                 "No historical spread, L2 impact or funding cashflows",
                 "No live position sizing, liquidation/margin, or account PNL",
                 "Multiple comparisons; bootstrap intervals are exploratory",
                 "No conclusions from 2026 seen recheck alone"])
    (OUT/"quality.json").write_text(json.dumps(meta,indent=2,default=str)+"\n")
    rep=[
        "# Stage 5 — Can volatility-scaled exits improve BTC directional expectancy?",
        "",
        "## Method",
        "Signals from Stage 3 are **unchanged**: expansion follow, accepted 12h breakout, and rejected 12h sweep.",
        "Entry at first next-hour 1m open. No entry optimization. Independent model/rule strategies never overlap trades.",
        "Compare Stage 3-style 500/350 60m fixed exits with risk-scaled 2R target, 4h trailing, or 4h timeout.",
        "Risk: prior 48h typical hourly range clipped to 200–1200 points; volatility stop 1R.",
        "Trailing activation 0.75R, trail distance 0.5R; trailing changes only after fully completed minute closes.",
        "Every model uses 0.05% per side taker + 18% GST and 5 points adverse slippage per side.",
        "",
        "## Net point results",sm.to_markdown(index=False),"",
        "## Interpretation",
        "Returns are BTC price points on a 1 BTC-price-unit equivalent, NOT actual account USD.",
        "Compare signs, cost robustness, trade counts and confidence intervals across periods;",
        "any isolated positive cell does not demonstrate a repeatable edge.",
        "",
        "## Limitations",
        *["- "+x for x in meta["caveats"]],
        "",
        "Further research must be frozen and prospectively evaluated on uninspected fresh data.",
        ""]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(rep))
    print("STAGE5_DONE",json.dumps({"trades":len(df),"models":len(TESTS),"rules":len(RULES)}))
    print(sm.to_string(index=False))

if __name__=="__main__":
    main()
