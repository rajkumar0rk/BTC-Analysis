#!/usr/bin/env python3
"""Reclaim V2: can we raise profitable-month count without losing locked V1 profit?

This is a proper per-trade 1m OHLC replay of alternative *exit* settings and
per-entry causal adaptive lock selection. Signal rules, entry timestamps,
volume threshold, position quantity and fee/GST/slippage remain fixed.
Locked baseline never edited. Every entry gate uses COMPLETED H1 signal candle.

Strict goals across BOTH OHLC path assumptions and all 22 IST months:
  - every previously profitable month's net USD stays >= locked V1
  - net 2025, net Jan-Oct 2026 and 22-month net >= locked V1
  - target >=16 positive months in both paths; original 15 positive.
Also evaluate stronger "no month can become worse" constraint.
IMPORTANT: validation is in-sample; does not establish forward reliability.
"""
from __future__ import annotations
import itertools
import json
from pathlib import Path
import numpy as np
import pandas as pd
from research_st_ema20_initial_sl_grid_20261122 import (
    eng,prepare_entries,run,summarize,MONTHS,PATHS)
from research_st_ema20_reclaim_loss_months_20261122 import (
    indicator_features,signal_table,gates)

OUT=Path("analysis/reclaim_v2_preserve_monthly_profit_20261124")
BASE=(2.,3.,5.)
BASE_STOP=2.
BASELINE_NET={
 "open_high_low_close":20.037378,
 "open_low_high_close":20.261506,
}
EPS=1.5e-6
LOCKED_SELECTION={"ema_gap_pct_max":1.,"ema_slope_pct_min":-.2,"st_gap_pct_min":.5}
FEETYPES=["volume","atr_pct","atr_expand","ema_slope","ema_gap","st_gap","rsi",
          "adx","body","range","age","weekday","session","direction"]

def settings():
    opts={(BASE_STOP,BASE)}
    firsts=(.14,.25,.5,.75,1.,1.25,1.5,1.75,2.,2.25,2.5,3.,3.5)
    tails=(
       (2.,3.,5.),(2.5,3.,5.),(3.,5.),(3.,4.,5.),(4.,5.),
       (3.,5.,8.),(2.,3.,4.,5.),(2.,5.),(3.,),
       (5.,),(4.,8.),(2.25,3.,4.,5.))
    for first in firsts:
        for tail in tails:
            ladder=(first,)+tuple(x for x in tail if x>first+1e-6)
            opts.add(ladder if False else (2.,ladder))
    # Adjust initial stops with baseline profit lock (and a few early-lock sets).
    for stop in (.5,.75,1.,1.25,1.5,1.75,2.,2.25,2.5,2.75,3.,4.):
        for ladder in (BASE,(.5,1.,2.,3.,5.),(1.,2.,3.,5.),
                       (1.5,2.,3.,5.),(1.75,2.,3.,5.),(2.,2.5,3.,5.)):
            opts.add((stop,ladder))
    return sorted(opts,key=lambda x:(x[0],len(x[1]),x[1]))

def key(stop,levels):
    return "sl"+str(stop).replace(".","p")+"__"+("_".join(str(x).replace(".","p") for x in levels))

def to_matrix(trades):
    assert len(trades)==55,len(trades)
    idx={m:i for i,m in enumerate(MONTHS)}
    arr=np.zeros((55,len(MONTHS)),float)
    entry_utc=list(trades.entry_utc.astype(str))
    for i,t in enumerate(trades.itertuples(index=False)):
        if t.exit_reason=="still_open":continue
        month=pd.Timestamp(t.exit_utc).tz_convert("Asia/Kolkata").strftime("%Y-%m")
        if month in idx:arr[i,idx[month]]=float(t.net_usd)
    return arr,entry_utc

def evaluate(arrs,base):
    results=[]
    for path in PATHS:
        v=arrs[path].sum(axis=0)
        b=base[path]
        positive=(v>EPS)
        oldprof=(b>EPS)
        keep=bool(np.all(v[oldprof]+EPS>=b[oldprof]))
        status=bool(np.all(positive[oldprof]))
        neverworse=bool(np.all(v+EPS>=b))
        yr25=float(v[:12].sum());yr26=float(v[12:].sum());total=float(v.sum())
        b25=float(b[:12].sum());b26=float(b[12:].sum());btot=float(b.sum())
        results.append(dict(path=path,positive_months=int(positive.sum()),
            losing_months=int((v<-EPS).sum()),
            flat_months=int((abs(v)<=EPS).sum()),
            net25=yr25,net26=yr26,total_net=total,
            preserved_each_original_month_net=keep,
            preserved_each_original_positive_status=status,
            no_month_worse=neverworse,
            total_nondecreasing=bool(total+EPS>=btot),
            both_years_nondecreasing=bool(yr25+EPS>=b25 and yr26+EPS>=b26),
            new_positive_months=[MONTHS[i] for i in range(len(MONTHS))
                                  if b[i]<=EPS and positive[i]],
            old_months_worse=[MONTHS[i] for i in range(len(MONTHS))
                              if v[i]<b[i]-EPS]))
    return dict(positive_min=min(x["positive_months"] for x in results),
       positive_max=max(x["positive_months"] for x in results),
       losing_max=max(x["losing_months"] for x in results),
       flat_max=max(x["flat_months"] for x in results),
       worst_net=min(x["total_net"] for x in results),
       best_net=max(x["total_net"] for x in results),
       net25_worst=min(x["net25"] for x in results),
       net26_worst=min(x["net26"] for x in results),
       preserve_month_dollars=all(x["preserved_each_original_month_net"] for x in results),
       preserve_profit_status=all(x["preserved_each_original_positive_status"] for x in results),
       no_month_worse=all(x["no_month_worse"] for x in results),
       preserve_years_and_total=all(x["total_nondecreasing"] and x["both_years_nondecreasing"] for x in results),
       months_promoted_intersection=";".join(sorted(set(results[0]["new_positive_months"])&
                                                    set(results[1]["new_positive_months"]))),
       months_promoted_union=";".join(sorted(set(results[0]["new_positive_months"])|
                                             set(results[1]["new_positive_months"]))),
       months_worse_union=";".join(sorted(set(results[0]["old_months_worse"])|
                                          set(results[1]["old_months_worse"]))))

def save_monthly(scenarios,base):
    out=[]
    for scenario,arrs in scenarios:
        for path in PATHS:
            v=arrs[path].sum(axis=0);b=base[path]
            for i,mo in enumerate(MONTHS):
                out.append(dict(scenario=scenario,path=path,month_ist=mo,
                      locked_v1_net_usd=round(float(b[i]),6),
                      candidate_net_usd=round(float(v[i]),6),
                      month_net_delta_usd=round(float(v[i]-b[i]),6),
                      locked_v1_positive=bool(b[i]>EPS),
                      candidate_positive=bool(v[i]>EPS)))
    pd.DataFrame(out).to_csv(OUT/"selected_monthly_audit.csv",index=False)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    engine=eng();engine.smoke_test()
    m,h,nfiles=engine.load()
    h=indicator_features(engine.features(h))
    all_entries=prepare_entries(engine,m,h,"reclaim")
    assert len(all_entries)==62,len(all_entries)
    full_features=signal_table(all_entries,h)
    selected=(full_features.ema_gap_pct<=1)&(full_features.ema_slope_pct>=-.2)&(
              full_features.supertrend_gap_pct>=.5)
    selected_ids=np.flatnonzero(selected.to_numpy()).tolist()
    entries=[all_entries[i] for i in selected_ids]
    features=full_features.iloc[selected_ids].reset_index(drop=True)
    assert len(entries)==55,(len(entries),"frozen selection")
    print("FROZEN ENTRY SIGNALS",len(all_entries),"LOCKED EXECUTED",len(entries),flush=True)

    base={}
    base_trades={}
    arrays={}
    comparisons=[]
    configs=settings()
    print("Direct replay configurations",len(configs),"two intraminute paths",flush=True)
    for n,(sl,levels) in enumerate(configs):
        name=key(sl,levels)
        path_matrices={}
        for path in PATHS:
            trades=run(engine,m,h,entries,"reclaim",path,"sl","pct",sl,ladder_override=levels)
            arr,dates=to_matrix(trades)
            assert len(dates)==55
            path_matrices[path]=arr
            if sl==BASE_STOP and levels==BASE:
                assert len(trades[trades.exit_reason!="still_open"])==55
                summary,monthly=summarize(trades,"reclaim","2%",path)
                assert summary["profitable_months"]==15 and summary["losing_months"]==5
                assert summary["flat_months"]==2,(path,summary)
                assert abs(summary["total_net_usd"]-BASELINE_NET[path])<1e-5,(path,summary)
                base[path]=arr.sum(axis=0)
                base_trades[path]=trades
        arrays[name]=path_matrices
        if (n+1)%25==0:
            print("Direct replay",n+1,"/",len(configs),flush=True)
    assert len(base)==2
    base_key=key(BASE_STOP,BASE)
    gates_on_locked=gates(features)
    # Always include gates that select very few trades, but label as high-risk.
    conditionals=[]
    for gate in gates_on_locked:
        conditionals.append((gate["name"],gate["mask"],gate["category"]))
    # Stable gates matching an EMA regime or more fine-grained volume threshold.
    for col,thresholds in {
        "ema_gap_pct":(.05,.1,.2,.3,.4,.6,.8,1.),
        "supertrend_gap_pct":(.5,.65,.75,1.,1.25,1.5,2.),
        "ema_slope_pct":(-.15,-.1,-.05,0.,.05,.1,.15,.2),
        "adx14":(15.,20.,25.,30.,35.,40.),
        "dir_rsi14":(45.,50.,55.,60.,65.),
        "volume_ratio":(1.5,2.,2.5,3.,4.)
    }.items():
        v=features[col].to_numpy(float)
        for threshold in thresholds:
            for relation,mask in (("le",v<=threshold),("ge",v>=threshold)):
                if 0<mask.sum()<55:
                    conditionals.append((f"{col}_{relation}_{threshold:g}",mask,col))
    unique={}
    for name,mask,family in conditionals:
        sign=np.packbits(mask).tobytes()
        if sign not in unique:unique[sign]=(name,mask,family)
    cond=list(unique.values())
    print("Unique entry-time regime gates",len(cond),flush=True)
    base_arrays=arrays[base_key]
    # Every unconditional full-session exit variation is compared against V1.
    for name,mat in arrays.items():
        row=evaluate(mat,base)
        comparisons.append(dict(method="UNCONDITIONAL",setting=name,gate="none",
            gated_trade_count=55,**row))
    # Conditional exit policy: apply alt exit to qualifying 1H completed-signal
    # profiles, otherwise run exact frozen V1. Trade entry remains unchanged.
    for i,(name,mat) in enumerate(arrays.items()):
        if name==base_key:continue
        for gate_name,mask,family in cond:
            if mask.sum()<5 or mask.sum()>50:continue
            # First quickly evaluate the relevant month equations.
            variant={path:np.where(mask[:,None],mat[path],base_arrays[path])
                     for path in PATHS}
            row=evaluate(variant,base)
            comparisons.append(dict(method="CAUSAL_ADAPTIVE_EXIT",
                setting=name,gate=gate_name,gated_trade_count=int(mask.sum()),**row))
        if (i+1)%30==0:print("Adaptive candidate",i+1,"/",len(arrays),flush=True)
    scores=pd.DataFrame(comparisons)
    scores["worthy"]=scores.preserve_month_dollars & scores.preserve_years_and_total & (
        scores.positive_min>=16)
    scores["strong_worthy"]=scores.worthy & scores.no_month_worse
    scores=scores.sort_values(["strong_worthy","worthy","positive_min","worst_net"],
                              ascending=[False,False,False,False])
    scores.to_csv(OUT/"all_exits_and_adaptive_regimes.csv",index=False)
    worth=scores[scores.worthy].sort_values(["positive_min","worst_net"],ascending=False)
    strong=scores[scores.strong_worthy].sort_values(["positive_min","worst_net"],ascending=False)
    worthy_status=scores[scores.preserve_profit_status & scores.preserve_years_and_total &(
        scores.positive_min>=16)].sort_values(["positive_min","worst_net"],ascending=False)
    worth.head(50).to_csv(OUT/"strict_no_profit_sacrifice_winners.csv",index=False)
    strong.head(50).to_csv(OUT/"strict_no_month_worse_winners.csv",index=False)
    worthy_status.head(50).to_csv(OUT/"status_only_not_dollar_safe.csv",index=False)
    # No invented positive results; empty result files are valid failed research.
    def candidate_arrays(row):
        mat=arrays[row.setting]
        if row.method=="UNCONDITIONAL":return mat
        gate_name=row.gate
        mask=next(mask for n,mask,fam in cond if n==gate_name)
        return {p:np.where(mask[:,None],mat[p],base_arrays[p]) for p in PATHS}
    top=[("locked_v1",base_arrays)]
    for title,df in (("strong",strong),("strict",worth),("status_only",worthy_status)):
        if len(df):top.append((title+"_"+df.iloc[0].setting+"_"+df.iloc[0].gate,candidate_arrays(df.iloc[0])))
    save_monthly(top,base)
    # 2025 selection *only* and unmodified 2026 measurement, must NOT market
    # as pristine OOS due to prior 2026 data exploration.
    scores2025=scores[
       (scores.net25_worst>=min(base[p][:12].sum() for p in PATHS)-EPS)]
    scores2025=scores2025.sort_values(["positive_min","net25_worst"],ascending=False).head(60)
    scores2025.to_csv(OUT/"2025_development_2026_diagnostic.csv",index=False)
    metrics=dict(
       source_archive="Delta Exchange India BTCUSD 1m",
       completed_months_ist=[MONTHS[0],MONTHS[-1]],
       loaded_minute_bars=len(m),hourly_bars=len(h),source_files=nfiles,
       all_reclaim_signals=len(all_entries),frozen_v1_entries=len(entries),
       direct_exit_configurations=len(arrays),unique_causal_gates=len(cond),
       path_level_unconditional_replays=len(arrays)*2,
       scored_adaptive_and_unconditional_policies=len(scores),
       pass_exact_per_profit_month_dollars_and_total_and_improve=len(worth),
       pass_never_worse_any_month_and_improve=len(strong),
       pass_status_only_improvements=len(worthy_status),
       original_per_path_nets=BASELINE_NET,
       original_profit_months=15,original_loss_months=5,original_flat_months=2,
       initial_SL_percent=2,profit_lock_pct=[2,3,5],
       quantity_btc=engine.QTY,fee_per_side_with_GST=engine.FEE,
       BTC_points_slippage_per_side=engine.SLIP,
       comparability="Trade entries are exactly frozen V1; conditional exit only based on completed H1 signal features",
       warning="All historical 2025-26 optimization; 2026 is NOT untouched out-of-sample. Tick order, funding, liquidation, amend delay not modeled")
    (OUT/"quality.json").write_text(json.dumps(metrics,indent=2)+"\n")
    report=(
      "# Reclaim V2 — raise profitable months without reducing locked Reclaim V1 profit\n\n"
      "**Locked base untouched:** 15 profitable / 5 losing / 2 flat months; $20.037378/$20.261506 across 2 possible 1m OHLC paths. "
      "55 original trade entries, volume >=1.25x, H1 ST(10,3)+EMA20 Reclaim, completed-hour EMA gap<=1%, EMA slope>=-0.2%, ST gap>=0.5%; 2% initial stop and 2%-3%-5% profit lock.\n\n"
      f"**Search:** {len(arrays)} variations of initial-stop/profit-lock settings, with {len(cond)} different causal 1H signal gates for conditional execution, "
      f"across {len(scores)} policy combinations. No entry changes or hindsight month-blacklisting.\n"
      f"**Candidates improving profitable-month count AND preserving the USD profit of each original profitable month:** {len(worth)}. "
      f"**Also avoid reducing the USD P&L in every other month:** {len(strong)}.\n\n"
      "## Strongest strictly no-month-worse positive-month improvements\n\n"
      +(strong.head(20).to_markdown(index=False) if len(strong) else "NONE found in tested parameter grid.\n")
      +"\n\n## More general per-profitable-month USD preservation\n\n"
      +(worth.head(20).to_markdown(index=False) if len(worth) else "NONE found.\n")
      +"\n\n## Status-only preservation (does not meet no-profit-decrease requirement)\n\n"
      +(worthy_status.head(15).to_markdown(index=False) if len(worthy_status) else "NONE found.\n")
      +"\n\n## Methodology and limitations\n\n"
      "All profit levels based on underlying BTCUSD price, NOT leveraged account return. "
      "All decisions are either unconditional or based ONLY on completed 1H signal data. "
      "Simulations reproduce original 1m OHLC assumed price paths. Fills include taker fees, GST, 5-point slippage each side. "
      "No tick ordering, funding, order-book, amendment latency, exchange margin, or liquidation. "
      "This 2025–2026 parameter search is IN-SAMPLE and subject to strong selection bias; 2026 is not new holdout.\n")
    (OUT/"RESEARCH_REPORT.md").write_text(report)
    print("SUCCESS",json.dumps({k:metrics[k] for k in (
        "direct_exit_configurations","unique_causal_gates",
        "scored_adaptive_and_unconditional_policies",
        "pass_exact_per_profit_month_dollars_and_total_and_improve",
        "pass_never_worse_any_month_and_improve")}),flush=True)
    print("TOP STRONG",strong.head(6).to_string(index=False),flush=True)
    print("TOP STRICT",worth.head(6).to_string(index=False),flush=True)

if __name__=="__main__":
    main()
