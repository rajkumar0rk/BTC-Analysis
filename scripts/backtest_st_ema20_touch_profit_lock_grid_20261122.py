#!/usr/bin/env python3
"""BTCUSD 1H EMA20 Touch: multi-value stepped profit-lock sweep with 3% initial SL.

Frozen entry rules and exact historical Delta 1m OHLC archive. The only
independent variable is the entry-relative profit protection ladder.
Scenarios run under two hypothetical intraminute path assumptions and
are ranked by BOTH-path profitable month count, both-year profitability
and net profit. This is in-sample exploratory research, not forward proof.
"""
from __future__ import annotations
from collections import defaultdict
import json
from pathlib import Path
import numpy as np
import pandas as pd
from research_st_ema20_initial_sl_grid_20261122 import (
    eng, prepare_entries, run, summarize, PATHS
)

OUT=Path("analysis/st_ema20_touch_profit_lock_grid_20261122")
INITIAL_STOP_PCT=3.
MONTHS=pd.period_range("2025-01","2026-10",freq="M").astype(str).tolist()
BASELINE=(0.14,)
PREVIOUS_LADDER=(0.14,0.50,1.,2.,5.)
FIRSTS=[0.12,0.14,0.16,0.18,0.20,0.25,0.30,0.40,0.50,0.75,1.0]
TAILS=[
    (),(.20,),(.25,),(.30,),(.40,),(.50,),(.75,),(1.,),(1.5,),
    (.20,.3,.5,1.,2.),(.25,.5,1.,2.,5.),(.3,.6,1.,2.,5.),
    (.4,.75,1.5,3.,5.),(.5,1.,2.,3.,5.),(.5,1.,2.,5.),
    (.5,1.,3.,5.),(.75,1.5,3.,5.),(1.,2.,3.,5.),
    (1.,2.,5.),(1.,3.,5.),(1.,2.,4.,8.),(2.,3.,5.),
    (2.,4.,6.),(2.,5.,10.),(3.,5.,10.),(5.,10.)
]

def ladders():
    pools={BASELINE,PREVIOUS_LADDER}
    for first in FIRSTS:
        pools.add((first,))
        for tail in TAILS:
            levels=(first,)+tuple(x for x in tail if x>first+1e-10)
            pools.add(levels)
    # Varied short profit-step schedules for the requested 0.14% baseline.
    for second in (.18,.20,.25,.30,.35,.40,.50,.60,.75,1.,1.25,1.5,2.):
        for after in ((),(1.,2.),(1.,2.,3.),(1.,2.,5.),
                      (2.,3.,5.),(2.,5.,10.),(3.,5.,10.)):
            pools.add(tuple(sorted(set((0.14,second)+tuple(x for x in after if x>second)))))
    # Dynamic milestone scaling from first activation rather than fixed 1/2/5.
    for first in (.14,.2,.3,.5):
        for mult in ((2,3,5),(2,4,8),(3,6,10),(5,10),
                     (2,3,4,5),(3,5,8)):
            pools.add(tuple(sorted(set([first]+[round(first*v,4) for v in mult if first*v<=10]))))
    pools={tuple(round(x,5) for x in p) for p in pools
           if p and all(0<x<=10 for x in p)}
    assert BASELINE in pools and PREVIOUS_LADDER in pools
    assert len(pools)>110, len(pools)
    return sorted(pools,key=lambda x:(x[0],len(x),x))

def label(levels):
    return "lock_"+"_".join(f"{v:g}".replace(".","p") for v in levels)

def max_drawdown_rolling(t):
    # Closed-equity drawdown is not floating equity drawdown.
    x=t[t.exit_reason!="still_open"].copy().sort_values("exit_utc")
    x=x[pd.to_datetime(x.exit_utc,utc=True)<pd.Timestamp("2026-11-01",tz="Asia/Kolkata").tz_convert("UTC")]
    values=x.net_usd.to_numpy(float)
    if not len(values):return 0.
    equity=100.+np.cumsum(values)
    peaks=np.maximum.accumulate(np.r_[100.,equity])[1:]
    return round(float(np.max((peaks-equity)/peaks*100)),3)

def main():
    engine=eng()
    engine.smoke_test()
    m,h,nfiles=engine.load()
    h=engine.features(h)
    h["volume_ratio"]=(h.volume/h.volume.shift(1).rolling(20,min_periods=20).mean().replace(0,np.nan))
    entries=prepare_entries(engine,m,h,"touch")
    assert len(entries)==52,len(entries)
    variations=ladders()
    print("Grid variations",len(variations),"Price-paths",len(PATHS),
          "Entry candidates",len(entries),flush=True)
    rows=[];monthlies=[];audit=[]
    for i,levels in enumerate(variations):
        for path in PATHS:
            t=run(engine,m,h,entries,"touch",path,"3%","pct",INITIAL_STOP_PCT,
                  ladder_override=levels)
            score,monthly=summarize(t,"touch","3%",path)
            score["variation"]=label(levels)
            score["milestones_pct"]=" -> ".join(f"{v:g}%" for v in levels)
            score["milestones_json"]=json.dumps(levels)
            score["milestone_count"]=len(levels)
            score["first_lock_pct"]=levels[0]
            score["realized_dd_rechecked_pct"]=max_drawdown_rolling(t)
            monthly["variation"]=score["variation"]
            rows.append(score);monthlies.append(monthly)
            if levels==BASELINE:
                assert score["trades"]==50,(path,score)
                assert score["profitable_months"]==21,(path,score)
                expected={"open_high_low_close":0.725036,
                          "open_low_high_close":0.723046}[path]
                assert abs(score["total_net_usd"]-expected)<1e-5,(path,score)
            if levels==PREVIOUS_LADDER:
                expected={"open_high_low_close":2.085741,
                          "open_low_high_close":1.425514}[path]
                assert abs(score["total_net_usd"]-expected)<1e-5,(path,score)
            if levels in (BASELINE, PREVIOUS_LADDER):
                t=t.copy();t["variation"]=score["variation"];audit.append(t)
        if (i+1)%20==0:
            print("Processed",i+1,"/",len(variations),flush=True)
    raw=pd.DataFrame(rows)
    monthly=pd.concat(monthlies,ignore_index=True)
    raw.to_csv(OUT/"full_grid_by_path.csv",index=False)
    monthly.to_csv(OUT/"monthly.csv",index=False)
    pd.concat(audit,ignore_index=True).to_csv(OUT/"baseline_and_previous_trade_audit.csv",index=False)
    pair=[]
    for variant,gr in raw.groupby("variation",sort=False):
        assert len(gr)==2,(variant,gr)
        r=gr.iloc[0]
        yr2025=(gr.net_2025>0).all()
        yr2026=(gr.net_2026>0).all()
        pair.append(dict(variation=variant,milestones_pct=r.milestones_pct,
            first_lock_pct=r.first_lock_pct,milestone_count=r.milestone_count,
            profitable_months_worst=int(gr.profitable_months.min()),
            profitable_months_best=int(gr.profitable_months.max()),
            losing_months_worst=int(gr.losing_months.max()),
            flat_months_worst=int(gr.flat_months.max()),
            net_worst_usd=float(gr.total_net_usd.min()),
            net_best_usd=float(gr.total_net_usd.max()),
            net2025_worst=float(gr.net_2025.min()),
            net2025_best=float(gr.net_2025.max()),
            net2026_worst=float(gr.net_2026.min()),
            net2026_best=float(gr.net_2026.max()),
            profitable2025_worst=int(gr.profitable_2025.min()),
            profitable2026_worst=int(gr.profitable_2026.min()),
            wins_worst=int(gr.wins.min()),losses_worst=int(gr.losses.max()),
            initial_sl_hit_max=int(gr.stopped_trades.max()),
            realized_dd_pct_worst=float(gr.realized_dd_rechecked_pct.max()),
            profitable_both_years=bool(yr2025 and yr2026)))
    paired=pd.DataFrame(pair)
    paired=paired.sort_values(["profitable_both_years","profitable_months_worst",
        "net_worst_usd","realized_dd_pct_worst"],
        ascending=[False,False,False,True])
    paired.to_csv(OUT/"paired_comparison.csv",index=False)
    positive=paired[paired.net_worst_usd>0]
    both=positive[positive.profitable_both_years]
    top=both.sort_values(["profitable_months_worst","net_worst_usd"],
                         ascending=[False,False]).head(30)
    top.to_csv(OUT/"best_30_positive_both_years.csv",index=False)
    useful=paired[paired.variation.isin([label(BASELINE),label(PREVIOUS_LADDER)])]
    report="# BTCUSD EMA20 Touch 3% initial SL: Profit-lock milestone grid\n\n"
    report+=f"Evaluated {len(variations)} distinct ladder designs on {len(PATHS)} alternative 1m OHLC paths, using identical {len(entries)} EMA20 Touch signal candidates.\n"
    report+="Criteria: 22 completed IST months (Jan 2025-Oct 2026), net USD after standard taker fees, GST and 5 BTC-point slippage per execution leg.\n\n"
    report+="## Frozen prior controls\n\n"+useful.to_markdown(index=False)+"\n\n"
    report+="## Top 30 across both paths, positive in both calendar years\n\n"+top.to_markdown(index=False)+"\n\n"
    report+="## Audit\n\n"
    report+=f"Candidate ladders: {len(variations)}, path-level tests: {len(raw)}, gross-profit-positive in both paths: {len(positive)}, positive both years and paths: {len(both)}.\n"
    report+="IMPORTANT: The 3% initial SL is active from entry and stop is moved directly to the highest crossed percentage rung. No fixed stop increment beyond these percentage rungs.\n"
    report+="Limitations: simulated intraminute price-order assumptions; no order amendment latency, funding, liquidation, fill depth, cross margin, or pristine OOS validation. All configurations were evaluated on the same history, so apparent winners are subject to optimization bias. 0% closed-equity drawdown is not 0% floating equity risk.\n"
    (OUT/"RESEARCH_REPORT.md").write_text(report)
    (OUT/"quality.json").write_text(json.dumps({
        "source":"Delta Exchange India BTCUSD 1-minute OHLCV",
        "signal":"1H Supertrend(10,3) + 1H first EMA20 Touch",
        "entry_volume_ratio":"1.25 through 2.5 on signal hour",
        "quantity_btc":engine.QTY,"initial_sl_pct":INITIAL_STOP_PCT,
        "slippage_points_per_side":engine.SLIP,
        "taker_fee_with_gst_per_side":engine.FEE,
        "simulated_intraminute_paths":list(PATHS),
        "candidate_ladders":len(variations),"path_tests":len(raw),
        "completed_months":MONTHS,"validation":"Frozen 0.14% and 0.14/0.5/1/2/5 ladder baselines match",
        "caveats":["No stop execution latency or true tick sequence",
                   "No liquidation, funding, margin or forced unwind",
                   "Monthly counts are historic outcomes not guarantees",
                   "Return and zero closed-equity DD exclude intratrade unrealized drawdown"]
    },indent=2)+"\n")
    print("PASS; highest both-year-consistent rows:",flush=True)
    print(top.head(10).to_string(index=False),flush=True)
    print("Wrote",OUT,flush=True)

if __name__=="__main__":
    OUT.mkdir(parents=True,exist_ok=True)
    main()
