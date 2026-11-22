#!/usr/bin/env python3
"""Touch V2 improvements subject to preserving EVERY original profitable month.

Frozen BTCUSD signal:
  1H Supertrend(10,3), first EMA20 touch within cycle, volume ratio 1.25..2.5,
  3% initial SL, 1m simulated stop execution, 0.001 BTC, standard fees/slip.
Frozen V1 profit locks: 0.16 -> 0.20 -> 0.30 -> 0.50 -> 1 -> 2% of entry.
The Touch V1 baseline has 21 positive IST months, July 2025 FLAT (no trade),
and ZERO losing months across both 1m hypothetical path orders.

Evaluate milestone refinements:
 - all prior 337 candidates,
 - single/two extra intermediate milestone inserts,
 - dropped milestones / alternate step sizes,
 - first-lock perturbations.
Reject any config which makes a profitable baseline month negative or flat.
Stricter screening: reject reduction of USD profit in ANY baseline month.
This is in-sample exploration; not independent validation.
"""
from __future__ import annotations
import itertools
import json
from pathlib import Path
import numpy as np
import pandas as pd
from research_st_ema20_initial_sl_grid_20261122 import (
    eng, prepare_entries, run, summarize, PATHS, MONTHS
)
from backtest_st_ema20_touch_profit_lock_grid_20261122 import ladders as previous_ladders

OUT=Path("analysis/st_ema20_touch_v2_preserve_monthly_profit_20261122")
BASE=(0.16,0.20,0.30,0.50,1.,2.)
SL_PCT=3.
YEAR_SPLIT=12
E=1.5e-6
BASE_NET={
    "open_high_low_close":4.055329,
    "open_low_high_close":3.462267,
}
SENSITIVITY_EXTRA_POINTS_PER_LEG=(0,5,10,15,20,30,50)

def candidate_ladders():
    p=set(previous_ladders())
    p.add(BASE)
    insertion=[.17,.18,.19,.21,.22,.23,.24,.25,.26,.28,.32,.35,.40,.45,
               .55,.60,.65,.70,.75,.80,.90,1.25,1.50,1.75]
    for x in insertion:
        p.add(tuple(sorted(set(BASE+(x,)))))
    for a,b in itertools.combinations(insertion,2):
        p.add(tuple(sorted(set(BASE+(a,b)))))
    for mask in range(1<<5):
        p.add((BASE[0],)+tuple(BASE[i+1] for i in range(5) if mask&(1<<i)))
    for first in (.145,.15,.155,.16,.165,.17,.175,.18,.185,.19,.195,.2,.21,.22,.25):
        p.add((first,)+tuple(x for x in BASE[1:] if x>first))
        for after in ((.22,.3,.5,1.,2.),(.25,.35,.5,1.,2.),
                      (.3,.4,.6,1.,2.),(.3,.5,1.,2.),(.5,1.,2.),(1.,2.)):
            p.add(tuple(sorted(set((first,)+tuple(x for x in after if x>first)))))
    for a,b in itertools.combinations((.18,.22,.25,.28,.35,.4,.6,.75,1.25,1.5),2):
        p.add(tuple(sorted(set((.16,a,b,2.)))))
    # Nearby exit staircases after reaching the original first activation.
    for end in ((.2,.3,.5),( .2,.3,.5,1.),(.2,.35,.6,1.,2.),
                (.2,.4,.6,1.,2.),(.25,.3,.5,1.,2.),
                (.25,.4,.5,1.,2.),(.18,.25,.4,.6,1.,2.),
                (.2,.3,.5,1.,1.5,2.),(.2,.3,.5,1.,2.,3.),
                (.2,.25,.3,.4,.5,1.,2.)):
        p.add((.16,)+end)
    p={tuple(round(float(z),5) for z in x) for x in p
       if 1<=len(x)<=9 and all(0<z<=10 for z in x)
       and all(a<b for a,b in zip(x,x[1:]))}
    assert BASE in p and len(p)>400, len(p)
    return sorted(p,key=lambda q:(q[0],len(q),q))

def label(q):
    return "lock_"+"_".join(f"{x:g}".replace(".","p") for x in q)

def classify(q,base):
    good=bool(np.all((base<=E)|(q>E)))
    dollars=bool(np.all(q+E>=base))
    losing=int(np.sum(q<-E))
    flat=int(np.sum(abs(q)<=E))
    pos=int(np.sum(q>E))
    return good,dollars,pos,losing,flat

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    engine=eng()
    engine.smoke_test()
    m,h,nfiles=engine.load()
    h=engine.features(h)
    h["volume_ratio"]=h.volume/h.volume.shift(1).rolling(20,min_periods=20).mean().replace(0,np.nan)
    entries=prepare_entries(engine,m,h,"touch")
    assert len(entries)==52,(len(entries),"signal_count")
    variations=candidate_ladders()
    print("Candidates",len(variations),"path tests",len(variations)*2,flush=True)
    baseline_month={}
    baseline_summary={}
    base_trades={}
    for path in PATHS:
        t=run(engine,m,h,entries,"touch",path,"3%","pct",SL_PCT,ladder_override=BASE)
        summary,monthly=summarize(t,"touch","3%",path)
        assert summary["trades"]==50 and summary["profitable_months"]==21,(path,summary)
        assert summary["losing_months"]==0 and summary["flat_months"]==1,(path,summary)
        assert summary["wins"]==50 and summary["losses"]==0,(path,summary)
        assert abs(summary["total_net_usd"]-BASE_NET[path])<E,(path,summary)
        baseline_month[path]=monthly.net_usd.to_numpy(float)
        baseline_summary[path]=summary
        base_trades[path]=t
        flat=[mon for mon,net in zip(MONTHS,monthly.net_usd) if abs(net)<=E]
        assert flat==["2025-07"],(path,flat)
    selected_audits=[]
    row=[];rows_month=[]
    candidate_best={}
    for i,steps in enumerate(variations):
        variant=label(steps)
        result={}
        for path in PATHS:
            if steps==BASE:
                t=base_trades[path]
            else:
                t=run(engine,m,h,entries,"touch",path,"3%","pct",SL_PCT,ladder_override=steps)
            summary,monthly=summarize(t,"touch","3%",path)
            base=baseline_month[path]
            vals=monthly.net_usd.to_numpy(float)
            keep,dollars,positive,losing,flat=classify(vals,base)
            info=dict(variation=variant,steps=" -> ".join(f"{v:g}%" for v in steps),
                path=path,initial_stop_pct=SL_PCT,
                profitable_months=positive,losing_months=losing,flat_months=flat,
                preserved_all_21_baseline_profit_months=keep,
                preserved_baseline_usd_in_each_month=dollars,
                net_usd=summary["total_net_usd"],net2025=summary["net_2025"],
                net2026=summary["net_2026"],wins=summary["wins"],
                losses=summary["losses"],initial_stop_exits=summary["stopped_trades"],
                net_delta_usd=round(float(vals.sum()-base.sum()),6),
                months_profit_improved=int(((vals-base)>E).sum()),
                months_profit_reduced=int(((vals-base)<-E).sum()),
                minimum_month_delta=round(float((vals-base).min()),6),
                profit_july2025=float(vals[MONTHS.index("2025-07")]))
            row.append(info)
            result[path]=(info,vals)
        if all(result[p][0]["preserved_baseline_usd_in_each_month"] for p in PATHS):
            candidate_best[variant]=(steps,result)
        if (i+1)%40==0:
            print("Completed",i+1,"of",len(variations),flush=True)
    all_result=pd.DataFrame(row)
    combos=[]
    for variant,g in all_result.groupby("variation",sort=False):
        assert len(g)==2
        x=g.iloc[0]
        combos.append(dict(variation=variant,steps=x.steps,
            profitable_months_min=int(g.profitable_months.min()),
            losing_months_max=int(g.losing_months.max()),
            flat_months_max=int(g.flat_months.max()),
            preserves_all_21_months=bool(g.preserved_all_21_baseline_profit_months.all()),
            preserves_every_month_usd=bool(g.preserved_baseline_usd_in_each_month.all()),
            net_worst_usd=float(g.net_usd.min()),net_best_usd=float(g.net_usd.max()),
            net2025_worst=float(g.net2025.min()),net2026_worst=float(g.net2026.min()),
            improved_months_min=int(g.months_profit_improved.min()),
            reduced_months_max=int(g.months_profit_reduced.max()),
            total_trades_min=int((g.wins+g.losses).min()),
            initial_stop_hits_max=int(g.initial_stop_exits.max())))
    paired=pd.DataFrame(combos).sort_values(
       ["preserves_all_21_months","net_worst_usd"],ascending=False)
    strict=paired[paired.preserves_every_month_usd & (paired.net_worst_usd>min(BASE_NET.values())+E)]
    status=paired[paired.preserves_all_21_months & (paired.net_worst_usd>min(BASE_NET.values())+E)]
    by2025=paired[(paired.preserves_all_21_months)&(paired.net2025_worst>=
        min(baseline_summary[p]["net_2025"] for p in PATHS)-E)].sort_values(
        ["net2025_worst","net_worst_usd"],ascending=False)
    strict=strict.sort_values("net_worst_usd",ascending=False)
    status=status.sort_values("net_worst_usd",ascending=False)
    all_result.to_csv(OUT/"all_variations_by_path.csv",index=False)
    paired.to_csv(OUT/"all_variations_paired.csv",index=False)
    strict.head(50).to_csv(OUT/"no_month_dollar_loss_improvements.csv",index=False)
    status.head(50).to_csv(OUT/"keep_all_profitable_months_top.csv",index=False)
    by2025.head(40).to_csv(OUT/"2025_friendly_rankings.csv",index=False)
    # Only fully recompute monthly rows for the baseline and the actual top candidates.
    selected=[label(BASE)]
    selected+=strict.head(4).variation.tolist()
    selected+=status.head(4).variation.tolist()
    for variant in dict.fromkeys(selected):
        steps=next((x for x in variations if label(x)==variant))
        for path in PATHS:
            if steps==BASE:t=base_trades[path]
            else:t=run(engine,m,h,entries,"touch",path,"3%","pct",SL_PCT,ladder_override=steps)
            info,monthly=summarize(t,"touch","3%",path)
            vals=monthly.net_usd.to_numpy(float)
            for j,mon in enumerate(MONTHS):
                rows_month.append(dict(variation=variant,steps=str(steps),path=path,
                   month_ist=mon,baseline_net_usd=round(float(baseline_month[path][j]),6),
                   candidate_net_usd=round(float(vals[j]),6),
                   delta_usd=round(float(vals[j]-baseline_month[path][j]),6),
                   baseline_positive=bool(baseline_month[path][j]>E),
                   still_positive=bool(vals[j]>E)))
            if variant==label(BASE) or (len(strict)>0 and variant==strict.iloc[0].variation):
                u=t.copy();u["variation"]=variant;u["path"]=path;selected_audits.append(u)
    pd.DataFrame(rows_month).to_csv(OUT/"selected_month_by_month.csv",index=False)
    pd.concat(selected_audits,ignore_index=True).to_csv(OUT/"reference_and_top_trades.csv",index=False)
    # Extra slippage sensitivity approximation. Does not change threshold-trigger timing.
    sensitivity=[]
    pair_candidates=[label(BASE)]
    pair_candidates+=strict.head(1).variation.tolist()
    pair_candidates+=status.head(1).variation.tolist()
    for variant in dict.fromkeys(pair_candidates):
        steps=next((x for x in variations if label(x)==variant))
        for path in PATHS:
            t=base_trades[path] if steps==BASE else run(
                engine,m,h,entries,"touch",path,"3%","pct",SL_PCT,ladder_override=steps)
            for extra in SENSITIVITY_EXTRA_POINTS_PER_LEG:
                test=t.copy()
                test["net_usd"]=test.net_usd-2*engine.QTY*extra
                summary,monthly=summarize(test,"touch","3%",path)
                sensitivity.append(dict(variation=variant,path=path,
                    assumed_additional_slippage_points_per_leg=extra,
                    effective_slippage_points_per_leg=engine.SLIP+extra,
                    approximate_net_usd=summary["total_net_usd"],
                    profitable_months=summary["profitable_months"],
                    losing_months=summary["losing_months"],
                    flat_months=summary["flat_months"]))
    pd.DataFrame(sensitivity).to_csv(OUT/"additional_slippage_sensitivity_approx.csv",index=False)
    report=(
        "# BTCUSD EMA20 Touch — improve while preserving each profitable month\n\n"
        "Frozen V1: 3% initial SL, 0.16% -> 0.20% -> 0.30% -> 0.50% -> 1% -> 2% entry-relative profit lock, "
        "ST(10,3) and EMA20 first touch, 1.25–2.5x signal volume, 1m replay, 0.001 BTC. "
        "Both OHLC minute-path scenarios examined separately.\n\n"
        f"Tested **{len(variations)}** entry-relative lock schedules (2 OHLC paths each), "
        f"including all prior candidates and fine-grained ladder modifications.\n"
        "Baseline **21 profitable / 0 losing / 1 flat** months, Jan 2025–Oct 2026; "
        "July 2025 had **no qualifying trade**, so merely adjusting the profit-lock ladder "
        "CANNOT turn July 2025 profitable without changing entries.\n\n"
        "## V1 baseline by 1m OHLC path\n\n"
        +pd.DataFrame(baseline_summary).T.to_markdown(index=True)+"\n\n"
        f"## Improved net USD without decreasing **any** month (both OHLC paths): {len(strict)} candidates\n\n"
        +(strict.head(20).to_markdown(index=False) if len(strict) else "No such configuration found.")+"\n\n"
        f"## Higher net profit while retaining positive status in all 21 original positive months: {len(status)} candidates\n\n"
        +(status.head(20).to_markdown(index=False) if len(status) else "None found.")+"\n\n"
        "## 2025 historical rank: checks on same in-sample data, NOT an untouched forward holdout\n\n"
        +by2025.head(20).to_markdown(index=False)+"\n\n"
        "## Stress sensitivity\n\n"
        "Additional per-side slippage is applied as a P&L adjustment per trade **without rerunning entry trigger and stop filling**. "
        "Therefore this is an approximate sensitivity only; more robust tick/order-book forward testing required.\n\n"
        "## Limitations\n\n"
        "All results based on the same 2025-26 dataset already used to tune V1; severe selection bias. "
        "Positive historical profits are small relative to execution model uncertainty. "
        "Does NOT model funding, margin, liquidation, exact tick sequence, order amendment latency, market depth or missing orders. "
        "Realized drawdown 0% is not maximum intratrade risk.\n")
    (OUT/"RESEARCH_REPORT.md").write_text(report)
    (OUT/"quality.json").write_text(json.dumps({
        "base_ladder_entry_pct":BASE,"initial_SL_pct":SL_PCT,
        "qualifying_touch_entries":len(entries),
        "completed_ist_months":[MONTHS[0],MONTHS[-1]],
        "baseline_no_trade_month":"2025-07",
        "candidate_lock_schedules":len(variations),
        "path_level_tests":len(all_result),
        "strict_no_month_dollar_decrease_while_improving_worstpath_net":len(strict),
        "all_profitable_months_preserved_higher_worstpath_net":len(status),
        "basis":"historical BTCUSD 1-minute OHLC 1H signals two alternative within-minute paths",
        "limitations":["Overfit in-sample; not forward validated","Underlying 3% initial SL is not account risk",
          "Additional slippage sensitivity approximates without rerunning order fills",
          "No funding, liquidation, orderbook, live amendment latency"]
    },indent=2)+"\n")
    print("FINISHED",len(variations),"candidates",flush=True)
    print("STRICT NO MONTH WORSE:",len(strict),flush=True)
    print(strict.head(8).to_string(index=False),flush=True)
    print("KEEP POSITIVE MONTH STATUS:",len(status),flush=True)
    print(status.head(8).to_string(index=False),flush=True)

if __name__=="__main__":
    main()
