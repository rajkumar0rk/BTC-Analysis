#!/usr/bin/env python3
"""Independent Stage18 exit redesign; real 1m OHLC stop-first, no same-candle trail lookahead.

Freeze the successful Stage18 signal: S13 near-half-ATR, prior-month efficiency
<=0.25, 4H ADX<=18, 1H volume<=1.2, no loss gate, 5R/240m baseline.
Each candidate rebuilds its own nonoverlapping trade sequence from ORIGINAL
pre-entry Stage14 candidates. Stage17 Donchian sleeve is fixed for comparison.
Never select using 2026. Not a full shared margin replay.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from research_every_candle_200 import read_archive, FEE, SLIPPAGE
import research_july_drawdown_stage15 as s15
import research_stage18_stage20_signal_exit_improvement_20261120 as core
import research_stage18_stage20_guard_free_20261120 as old

OUT=Path("analysis/stage18_exit_improvement_20261121")
MONTHS=core.MONTHS
# variant, target_R, hold_minutes, dynamic exit mode, parameters
CASES=[
 ("baseline_5R_240",5,240,"fixed",{}),
 ("fixed_3R_240",3,240,"fixed",{}),
 ("fixed_4R_240",4,240,"fixed",{}),
 ("fixed_6R_240",6,240,"fixed",{}),
 ("fixed_5R_180",5,180,"fixed",{}),
 ("fixed_5R_300",5,300,"fixed",{}),
 ("fixed_5R_360",5,360,"fixed",{}),
 ("fixed_5R_480",5,480,"fixed",{}),
 ("be_at_1R",5,240,"lock",{"steps":[(1.,0.)]}),
 ("be_at_1p5R",5,240,"lock",{"steps":[(1.5,0.)]}),
 ("be_at_2R",5,240,"lock",{"steps":[(2.,0.)]}),
 ("lock_half_R_at_1p5",5,240,"lock",{"steps":[(1.5,.5)]}),
 ("lock_1R_at_2R",5,240,"lock",{"steps":[(2.,1.)]}),
 ("step_1p5_2p5_3p5",5,240,"lock",{"steps":[(1.5,0.),(2.5,1.),(3.5,2.)]}),
 ("step_2_3_4",5,240,"lock",{"steps":[(2.,.5),(3.,1.5),(4.,2.5)]}),
 ("trail_activate_1p5_dist_1R",5,240,"trail",{"activate":1.5,"distance":1.}),
 ("trail_activate_2_dist_1R",5,240,"trail",{"activate":2.,"distance":1.}),
 ("trail_activate_2_dist_1p5R",5,240,"trail",{"activate":2.,"distance":1.5}),
 ("trail_activate_3_dist_1R",5,240,"trail",{"activate":3.,"distance":1.}),
 ("trail_activate_3_dist_1p5R",5,240,"trail",{"activate":3.,"distance":1.5}),
 ("trail_activate_2_dist_2R",5,240,"trail",{"activate":2.,"distance":2.}),
 ("trail_activate_3_dist_2R",5,240,"trail",{"activate":3.,"distance":2.})
]
def replay(O,H,L,C,k,side,stop,targetR,hold,mode,params):
    entry=float(O[k])
    risk=float(side*(entry-stop))
    if risk<=0:raise AssertionError("Invalid structural stop")
    target=entry+side*targetR*risk
    live_stop=float(stop)
    favorable=0.
    for j in range(k,k+hold):
        # Use stop active at START of minute. If target and stop touch
        # during same minute, stop wins. Gaps cannot improve a stop fill.
        hitstop=(L[j]<=live_stop if side==1 else H[j]>=live_stop)
        hittarget=(H[j]>=target if side==1 else L[j]<=target)
        if hitstop:
            mid=min(float(O[j]),live_stop) if side==1 else max(float(O[j]),live_stop)
            reason="stop"
            break
        if hittarget:
            mid=target
            reason="target"
            break
        # Now the whole 1m OHLC bar is COMPLETED. Calculate the NEW stop
        # for the NEXT bar, never the current bar.
        best=(float(H[j])-entry) if side==1 else (entry-float(L[j]))
        favorable=max(favorable,best)
        if mode=="trail" and favorable>=params["activate"]*risk:
            proposed=entry+side*(favorable-params["distance"]*risk)
            if side*(proposed-live_stop)>0:live_stop=proposed
        elif mode=="lock":
            for at,locked in params["steps"]:
                if favorable>=at*risk:
                    proposed=entry+side*locked*risk
                    if side*(proposed-live_stop)>0:live_stop=proposed
    else:
        j=k+hold-1
        mid=float(C[j])
        reason="timeout"
    fill_in=entry+side*SLIPPAGE
    fill_out=mid-side*SLIPPAGE
    gross=float(side*(mid-entry))
    net=float(side*(fill_out-fill_in)-FEE*(fill_in+fill_out))
    return int(j),reason,gross,net,net/risk,risk

def simulate(events,f,c):
    name,rr,hold,mode,params=c
    e=events[(events.family==s15.FAMILY)&
             (events.previous_month_eff<=.25)&
             (events.h4_adx<=18)&(events.h1_vr<=1.2)]
    e=e.sort_values(["k","side"],kind="stable")
    O=f.open.to_numpy(float);H=f.high.to_numpy(float)
    L=f.low.to_numpy(float);C=f.close.to_numpy(float)
    times=f.time.to_numpy(np.int64)
    last=-1
    rows=[]
    for z in e.itertuples(index=False):
        k=int(z.k)
        if k<=last:continue
        if k+hold>len(O):continue
        if times[k+hold-1]-times[k]!=60*(hold-1):continue
        j,reason,gross,net,netR,risk=replay(O,H,L,C,k,int(z.side),
           float(z.stop_price),rr,hold,mode,params)
        last=j
        rows.append(dict(variant=name,k=k,entry_unix=int(times[k]),
            exit_unix=int(times[j]),side=int(z.side),reason=reason,
            entry_mid=float(O[k]),initial_risk_pts=risk,
            net_pts=net,net_R=round(float(netR),6),
            gross_pts=gross,held_minutes=j-k+1))
    g=pd.DataFrame(rows).sort_values(["exit_unix","entry_unix"],kind="stable")
    g["exit_month_ist"]=pd.to_datetime(g.exit_unix,unit="s",utc=True).dt.tz_convert("Asia/Kolkata").dt.strftime("%Y-%m")
    g=g[g.exit_month_ist.isin(MONTHS)].copy().reset_index(drop=True)
    g["risk_fraction"]=np.minimum(core.RISK_FRACTION,
                                  core.MAX_LEVERAGE*g.initial_risk_pts/g.entry_mid)
    if len(g)==0:raise RuntimeError("No trades "+name)
    return g

def metrics(a):
    v=np.asarray(a,float)
    equity=np.cumprod(1+v/100)
    peak=np.maximum.accumulate(np.r_[1.,equity])[1:]
    return dict(net=float(100*(equity[-1]-1)),
        profitable=int((v>1e-10).sum()),negative=int((v< -1e-10).sum()),
        flat=int((abs(v)<=1e-10).sum()),
        worst_month=float(v.min()),
        month_end_dd=float(100*np.max(1-equity/peak)))
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    f,_,_,q=read_archive()
    events=pd.read_csv(core.EVENTS)
    # Original Stage14 rows were generated before a historical 1m archive
    # repair. Re-align by immutable UTC timestamp rather than stale row number.
    # This protects October/November boundary candles against shifted arrays.
    timestamps=f.time.to_numpy(np.int64)
    source_indices=events.k.to_numpy(int)
    source_times=events.entry_unix.to_numpy(np.int64)
    mismatched=(timestamps[source_indices]!=source_times)
    print("SOURCE_INDEX_ALIGNMENT",json.dumps({
        "source_events":len(events),"stale_indices":int(mismatched.sum()),
        "earliest_mismatch_utc":str(pd.to_datetime(source_times[mismatched].min(),unit="s",utc=True))
             if mismatched.any() else None}))
    repaired=pd.Index(timestamps).get_indexer(source_times)
    if (repaired<0).any():raise AssertionError("Stage14 event timestamp absent from repaired archive")
    events=events.copy()
    events["k"]=repaired
    # Verify our custom baseline against archived Stage15 execution engine.
    ref_case=next(x for x in old.CASES if x[0]=="5R_broader_eff25_no_gate")
    ref,_=old.execute(events,f,ref_case)
    base=simulate(events,f,CASES[0])
    if len(base)!=len(ref):raise AssertionError(f"BASELINE trade count {len(base)} vs {len(ref)}")
    if not (base.entry_unix.to_numpy()==ref.entry_unix.to_numpy()).all():raise AssertionError("Entry parity failed")
    if not (base.exit_unix.to_numpy()==ref.exit_unix.to_numpy()).all():raise AssertionError("Exit parity failed")
    maxdiff=float(np.max(np.abs(base.net_R.to_numpy()-ref.net_R.to_numpy())))
    if maxdiff>0.000005:raise AssertionError(f"Net R parity failed {maxdiff}")
    print("BASELINE_PARITY",json.dumps({"trades":len(base),"max_net_R_diff":maxdiff}))
    original=core.saved_sleeves()
    results=[];monthly=[];ledgers=[]
    for case in CASES:
        g=base.copy() if case[0]==CASES[0][0] else simulate(events,f,case)
        ledgers.append(g)
        for stress in (0,2,5):
            b=core.replay_nav(g,stress)
            cr=np.array([x["net_pct"] for x in b["monthly"]])
            combined=.75*cr+.25*original["d55"]
            allm=metrics(combined)
            train=metrics(combined[:12])
            future=metrics(combined[12:])
            row=dict(variant=case[0],targetR=case[1],holdMinutes=case[2],
                mode=case[3],parameters=json.dumps(case[4]),
                extra_slippage_bps_side=stress,core_trades=len(g),
                core_PF_net_R=b["pf_net_R"],core_positive_trades=int((g.net_R>0).sum()),
                core_stop=int((g.reason=="stop").sum()),
                core_target=int((g.reason=="target").sum()),
                core_timeout=int((g.reason=="timeout").sum()),
                train_2025_pct=train["net"],train_2025_positive=train["profitable"],
                exposed_2026JanOct_pct=future["net"],
                exposed_2026_positive=future["profitable"],
                net_22_pct=allm["net"],positive_22=allm["profitable"],
                negative_22=allm["negative"],flat_22=allm["flat"],
                worst_month=allm["worst_month"],month_end_dd=allm["month_end_dd"])
            results.append(row)
            monthly += [dict(variant=case[0],extra_slippage_bps_side=stress,
                  month_ist=m,core_pct=float(a),daily55_pct=float(d),
                  portfolio_pct=float(p)) for m,a,d,p in zip(MONTHS,cr,original["d55"],combined)]
    summary=pd.DataFrame(results)
    details=pd.DataFrame(monthly)
    # Check published Stage18 22m baseline without hidden assumption changes.
    b=summary[(summary.variant=="baseline_5R_240")&
              (summary.extra_slippage_bps_side==0)].iloc[0]
    if abs(float(b.net_22_pct)-13.8789647516)>.005:
        raise AssertionError(f"Full model changed; baseline {b.net_22_pct}")
    # Select 2025 only, with post-cost 2bps sensitivity. Never use 2026 for selection.
    eligible=summary[summary.extra_slippage_bps_side==2].copy()
    eligible["selection_score_2025"]=(
       eligible.train_2025_pct + .2*eligible.train_2025_positive -
       .8*eligible.month_end_dd)
    eligible=eligible.sort_values(["selection_score_2025","train_2025_pct"],
                                  ascending=False,kind="stable")
    winner=str(eligible.iloc[0].variant)
    summary.to_csv(OUT/"all_exit_variants.csv",index=False)
    details.to_csv(OUT/"all_months.csv",index=False)
    pd.concat(ledgers,ignore_index=True).to_csv(OUT/"all_exit_trade_ledgers.csv.gz",index=False,compression="gzip")
    (OUT/"selection.json").write_text(json.dumps(dict(
        baseline="baseline_5R_240",selected_2025_only=winner,
        training_only="2025 after +2 bps extra adverse slippage EACH side",
        exposed_test="2026 Jan-Oct, historically reused and not pristine",
        source=q,baseline_parity_max_net_R_diff=maxdiff,
        limitations=["1m OHLC, stop-first for same-bar ambiguous path",
           "Trailing stops update only AFTER completed 1m candles",
           "Taker fee 0.05% per side + 18% GST + 5 pts slip per side",
           "No funding, true bid/ask, order depth, liquidation or shared margin",
           "Stage17 Daily55 fixed historical monthly MTM, not rerun integrated",
           "Prior historical research exposes BOTH 2025 and 2026",
           "Multiple variants create multiple-testing risk"] ),indent=2,default=str))
    for stress in (0,2,5):
        focus=summary[(summary.extra_slippage_bps_side==stress)&
                    (summary.variant.isin(["baseline_5R_240",winner]))]
        print("FOCUS_RESULTS",focus.to_json(orient="records"))
    print("2025_RANKED",eligible[["variant","train_2025_pct","train_2025_positive",
            "exposed_2026JanOct_pct","net_22_pct","positive_22"]].to_json(orient="records"))
    print("STAGE18_EXIT_IMPROVEMENT_COMPLETE",json.dumps(dict(selected=winner,variants=len(CASES))))
if __name__=="__main__":main()
