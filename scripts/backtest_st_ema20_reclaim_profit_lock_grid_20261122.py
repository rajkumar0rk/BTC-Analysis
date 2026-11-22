#!/usr/bin/env python3
"""BTCUSD 1H EMA20 Reclaim: initial 2% stop and multivalue step-profit protection.

Frozen entry signal: ST(10,3) + EMA20 Reclaim, volume >=1.25x at closed 1H
signal, entry in following hour, one fill per Supertrend cycle.
All lock configurations are percentages of EXECUTION ENTRY. At each milestone
the stop rises to the highest crossed favorable level, without lowering it.
Runs the established 1m OHLC path replay under BOTH intraminute path orders.
Full 22 complete IST months: Jan 2025-Oct 2026. Research only.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from research_st_ema20_initial_sl_grid_20261122 import (
    eng, prepare_entries, run, summarize, PATHS
)

OUT=Path("analysis/st_ema20_reclaim_profit_lock_grid_20261122")
INITIAL_STOP_PCT=2.
MONTHS=pd.period_range("2025-01","2026-10",freq="M").astype(str).tolist()
BASELINE=(2.0,3.0,5.0)
FIRSTS=(.14,.25,.50,.75,1.,1.25,1.5,1.75,2.,2.25,2.5,3.,3.5,4.,5.)
TAILS=(
    (),(.25,),(.5,),(.75,),(1.,),(1.5,),(2.,),(2.5,),(3.,),(4.,),(5.,),
    (1.,1.5,2.,3.),(1.,2.,3.,5.),(1.25,1.5,2.,3.,5.),
    (1.5,2.,3.,4.,5.),(2.,3.,5.),(2.,3.,5.,8.),
    (2.,3.,4.,5.),(2.,4.,6.,8.),(2.5,3.,4.,5.),
    (2.5,3.5,5.,7.5),(3.,4.,5.),(3.,5.,7.5,10.),
    (3.,5.,10.),(4.,6.,8.),(4.,5.,7.5),(5.,7.5,10.),
    (6.,8.,10.),(7.5,10.)
)
EXTRA_FIRSTS=(.75,1.,1.5,2.,2.5)
EXTRA_SECONDS=(1.,1.25,1.5,1.75,2.,2.25,2.5,2.75,3.,3.5,4.,4.5,5.)
EXTRA_TAILS=((),(2.,3.),(2.,3.,5.),(2.5,3.,5.),
             (3.,4.,5.),(3.,5.,10.),(4.,5.,7.5),(5.,7.5,10.))

def candidates():
    pool={BASELINE, (2.,), (2.,3.), (2.,3.,5.,10.),
          (1.,2.,3.,5.), (1.,1.5,2.,3.,5.), (1.5,2.,3.,5.)}
    for first in FIRSTS:
        pool.add((first,))
        for tail in TAILS:
            levels=(first,)+tuple(v for v in tail if v>first+1e-10)
            pool.add(levels)
    for first in EXTRA_FIRSTS:
        for second in EXTRA_SECONDS:
            if second<=first: continue
            for more in EXTRA_TAILS:
                levels=tuple(sorted(set((first,second)+tuple(v for v in more if v>second))))
                pool.add(levels)
    for first in (.5,.75,1.,1.5,2.,2.5):
        for mult in ((1.25,1.5,2.,3.),(1.5,2.,3.,5.),
                     (2.,3.,5.),(2.,4.,8.),(3.,5.,8.)):
            pool.add(tuple(sorted(set([first]+[round(first*x,4) for x in mult if first*x<=10]))))
    pool={tuple(round(v,5) for v in vals) for vals in pool
          if vals and all(v>0 and v<=10 for v in vals) and
          all(a<b for a,b in zip(vals,vals[1:]))}
    assert BASELINE in pool and len(pool)>300,len(pool)
    return sorted(pool,key=lambda x:(x[0],len(x),x))

def label(levels):
    return "lock_"+"_".join(f"{v:g}".replace(".","p") for v in levels)

def main():
    engine=eng();engine.smoke_test()
    m,h,nfiles=engine.load()
    h=engine.features(h)
    h["volume_ratio"]=(h.volume/h.volume.shift(1).rolling(20,min_periods=20).mean().replace(0,np.nan))
    entries=prepare_entries(engine,m,h,"reclaim")
    assert len(entries)==62,len(entries)
    versions=candidates()
    print("Candidate Reclaim ladders",len(versions),"paths",len(PATHS),"entry candidates",len(entries),flush=True)
    summary=[]; monthlies=[];audits=[]
    for i,ladder in enumerate(versions):
        for path in PATHS:
            t=run(engine,m,h,entries,"reclaim",path,"2%","pct",INITIAL_STOP_PCT,
                  ladder_override=ladder)
            score,monthly=summarize(t,"reclaim","2%",path)
            score["variation"]=label(ladder)
            score["milestones_pct"]=" -> ".join(f"{v:g}%" for v in ladder)
            score["milestones_json"]=json.dumps(ladder)
            score["first_lock_pct"]=ladder[0]
            score["milestone_count"]=len(ladder)
            monthly["variation"]=score["variation"]
            summary.append(score);monthlies.append(monthly)
            if ladder==BASELINE:
                expected={"open_high_low_close":(62,13.522615,14),
                          "open_low_high_close":(62,13.746743,15)}[path]
                assert score["trades"]==expected[0],(path,score)
                assert abs(score["total_net_usd"]-expected[1])<1e-5,(path,score)
                assert score["profitable_months"]==expected[2],(path,score)
                t=t.copy();t["variation"]=label(ladder);audits.append(t)
            if i%60==0 and path==PATHS[-1]:
                print("Progress",i+1,"/",len(versions),flush=True)
    assert len(summary)==len(versions)*len(PATHS)
    ss=pd.DataFrame(summary); mm=pd.concat(monthlies,ignore_index=True)
    OUT.mkdir(parents=True,exist_ok=True)
    ss.to_csv(OUT/"full_grid_by_path.csv",index=False)
    mm.to_csv(OUT/"monthly.csv",index=False)
    pd.concat(audits,ignore_index=True).to_csv(OUT/"baseline_trade_audit.csv",index=False)
    pairs=[]
    for name,gr in ss.groupby("variation",sort=False):
        assert len(gr)==2
        x=gr.iloc[0]
        pairs.append(dict(variation=name,milestones_pct=x.milestones_pct,
            first_lock_pct=x.first_lock_pct,milestone_count=int(x.milestone_count),
            profitable_months_worst=int(gr.profitable_months.min()),
            profitable_months_best=int(gr.profitable_months.max()),
            profitable2025_worst=int(gr.profitable_2025.min()),
            profitable2026_worst=int(gr.profitable_2026.min()),
            losing_months_worst=int(gr.losing_months.max()),
            flat_months_worst=int(gr.flat_months.max()),
            trades=int(gr.trades.min()),wins_worst=int(gr.wins.min()),losses_worst=int(gr.losses.max()),
            initial_sl_hits_max=int(gr.stopped_trades.max()),
            net_worst_usd=float(gr.total_net_usd.min()),
            net_best_usd=float(gr.total_net_usd.max()),
            net2025_worst=float(gr.net_2025.min()),
            net2025_best=float(gr.net_2025.max()),
            net2026_worst=float(gr.net_2026.min()),
            net2026_best=float(gr.net_2026.max()),
            realized_dd_worst_pct=float(gr.max_realized_dd_pct.max()),
            positive_both_years=bool((gr.net_2025.gt(0)&gr.net_2026.gt(0)).all())))
    pp=pd.DataFrame(pairs).sort_values(
         ["positive_both_years","profitable_months_worst","net_worst_usd"],
         ascending=[False,False,False])
    pp.to_csv(OUT/"paired_comparison.csv",index=False)
    eligible=pp[(pp.net_worst_usd>0)&pp.positive_both_years]
    elite=eligible.sort_values(["profitable_months_worst","net_worst_usd"],
                               ascending=[False,False]).head(30)
    elite.to_csv(OUT/"top_30_positive_both_years.csv",index=False)
    net_top=pp[pp.net_worst_usd>0].sort_values("net_worst_usd",ascending=False).head(30)
    net_top.to_csv(OUT/"top_30_net_profit.csv",index=False)
    control=pp[pp.variation==label(BASELINE)]
    assert len(control)==1
    report="# EMA20 Reclaim: 2% initial SL with multivalue profit-lock grid\n\n"
    report+=f"Evaluated **{len(versions)}** distinct profit-lock ladders on each of two assumed intraminute OHLC paths (**{len(ss)}** path-level tests). Frozen **62** entry candidates; 22 complete months Jan 2025-Oct 2026.\n"
    report+="All USD P&L includes 0.001 BTC position, modeled taker fees + GST and 5 BTC-point execution slippage per side.\n\n"
    report+="## Original 2% -> 3% -> 5% baseline with 2% SL\n\n"+control.to_markdown(index=False)+"\n\n"
    report+="## Highest profitable months, positive 2025 AND 2026 on both price paths\n\n"+elite.to_markdown(index=False)+"\n\n"
    report+="## Highest total net profit, not necessarily positive in both years\n\n"+net_top.head(10).to_markdown(index=False)+"\n\n"
    report+="## Cautions\n\nNo true intraminute tick sequence, order book, stop amendment latency, liquidation, margin, funding, or forward holdout. Reported maximum drawdown is on realized closed-trade equity, NOT floating exposure. The settings were compared in sample. The two price-path assumptions give a bounded sensitivity test, not an execution guarantee.\n"
    (OUT/"RESEARCH_REPORT.md").write_text(report)
    (OUT/"quality.json").write_text(json.dumps({
      "source":"Delta Exchange India BTCUSD 1m OHLCV",
      "signal":"1H Supertrend(10,3) + EMA20 Reclaim",
      "entry_volume_ratio_min":1.25,
      "position_btc":engine.QTY,
      "initial_sl_pct":INITIAL_STOP_PCT,
      "profit_ladders_tested":len(versions),"path_level_tests":len(ss),
      "paths":list(PATHS),"completed_months":MONTHS,
      "taker_fee_per_side_with_GST":engine.FEE,
      "slippage_in_BTC_points_per_side":engine.SLIP,
      "baseline_control":"2%-3%-5% profit lock and 2% SL validated exactly for both paths",
      "risk_caveats":["No funding, margin, liquidation or real tick/order-book fills",
       "Stop amendments assumed instant following the 1m simulated intrabar path",
       "Historical selection; not independently forward validated",
       "Realized drawdown excludes interim mark-to-market adverse exposure"]},indent=2)+"\n")
    print("FINISHED",len(versions),"ladder variants",len(eligible),"eligible on both paths/years",flush=True)
    print(elite.head(12).to_string(index=False),flush=True)

if __name__=="__main__":
    main()
