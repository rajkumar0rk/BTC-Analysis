#!/usr/bin/env python3
"""Stage18 independent complementary BTC strategy research.

Goal: find genuinely distinct archived after-cost BTC 1m-executed 5M/1H
candidates that make all 22 months positive when combined with the immutable
70/30 research baseline. Differentiate 2025-only candidate selection from
explicit INVALID all-month hindsight optimization.

No filtering by calendar month, direction chosen after result, or future signals.
All monthly portfolios are synthetic monthly rebalances, not shared margin
simulations. Historical 2026 has been examined repeatedly, and is not a
pristine holdout.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy.optimize import linprog
from research_wide_monthly_stage23 import make_model_pool

OUT=Path("analysis/stage18_september_hedge_search_20261121")
BASE=Path("/tmp/stage18-70-30/scenario_monthly_22.csv")
MONTHS=pd.period_range("2025-01","2026-10",freq="M").astype(str).tolist()
EPS=1.e-8

def stats(v):
    v=np.asarray(v,float)
    nav=np.cumprod(1+v/100)
    peak=np.maximum.accumulate(np.r_[1.,nav])[1:]
    return dict(
      positive=int((v>EPS).sum()),
      negative=int((v<-EPS).sum()),
      flat=int((abs(v)<=EPS).sum()),
      return_pct=float(100*(nav[-1]-1)),
      train_2025_positive=int((v[:12]>EPS).sum()),
      train_2025_return_pct=float(100*(np.prod(1+v[:12]/100)-1)),
      seen_2026_positive=int((v[12:]>EPS).sum()),
      seen_2026_return_pct=float(100*(np.prod(1+v[12:]/100)-1)),
      worst_month_pct=float(v.min()),
      jan2025=float(v[0]),jan2026=float(v[12]),sept2026=float(v[20]),oct2026=float(v[21]),
      max_monthend_dd_pct=float(100*np.max(1-nav/peak)),
    )

def admissible(m):
    # Strictly different causal trade models, not other portfolio blends.
    src=m["source"]
    if src=="stage19_5m" or src=="stage20_inverse_5m":
        # String suffix encodes actual source risk=0.5%, max leverage=5x.
        # No retrospective 1% risk/10x variants that change the cost exposure.
        return m["name"].endswith(":0.5:5.0")
    return src in ("stage19_hourly","stage17")

def train_score(v):
    s=stats(v[:12])
    # first maximize profitable 2025 months, then 2025 return; never 2026.
    return (s["positive"],s["return_pct"])

def make_records(baseline,models):
    weights=[.02,.05,.10,.15,.20,.25,.30]
    rec=[]
    best_train=None; best_hindsight=None
    candidates_jan25_and_sep_positive=[]
    for m in models:
        x=np.asarray(m["returns"][:22],float)
        q=stats(x)
        if q["jan2025"]>EPS and q["sept2026"]>EPS:
            candidates_jan25_and_sep_positive.append(dict(
                strategy=m["name"],source=m["source"],strategy_2025=q["train_2025_return_pct"],
                sep2026=q["sept2026"],jan2026=q["jan2026"],
                oct2026=q["oct2026"]))
        for w in weights:
            blend=(1-w)*baseline+w*x
            s=stats(blend)
            row=dict(model=m["name"],source=m["source"],extra_weight=w,
                2025_source_trades=int(np.maximum(0,m["trades"][:12]).sum()),
                september_source_trades=int(max(0,m["trades"][20])),
                september_source_return=float(x[20]),
                **s)
            rec.append(row)
            # Select ONLY using 2025. Negative equity or missing dates not allowed.
            key=(s["train_2025_positive"],s["train_2025_return_pct"])
            if best_train is None or key>best_train[0]:
                best_train=(key,row.copy(),blend.copy())
            # Diagnostic, INVALID selection with hindsight.
            key=(s["positive"],s["return_pct"])
            if best_hindsight is None or key>best_hindsight[0]:
                best_hindsight=(key,row.copy(),blend.copy())
    return (pd.DataFrame(rec),best_train,best_hindsight,
            pd.DataFrame(candidates_jan25_and_sep_positive))

def maximize_floor(X,base,min_anchor=.70,max_extra=.10,train_only=True):
    # X: rows=months, cols=component candidate return series.
    # baseline assigned minimum weight >=0.70, other weights <=10%.
    z=np.column_stack([base,X])
    idx=np.arange(12) if train_only else np.arange(22)
    n=z.shape[1]
    # maximize minimum month return f using: -z @ w + f <= 0
    A=np.column_stack([-z[idx],np.ones(len(idx))])
    obj=np.zeros(n+1);obj[-1]=-1
    equality=np.zeros((1,n+1));equality[0,:n]=1.
    bounds=[(min_anchor,1.)]+[(0.,max_extra)]*(n-1)+[(None,None)]
    result=linprog(obj,A_ub=A,b_ub=np.zeros(len(idx)),A_eq=equality,
                   b_eq=[1.],bounds=bounds,method="highs")
    if not result.success:raise RuntimeError("No LP solution: "+result.message)
    return result.x[:n],float(result.x[-1])

def output_monthly(path,v):
    pd.DataFrame(dict(month_ist=MONTHS,portfolio_return_pct=np.asarray(v,float),
      status=np.where(np.asarray(v)>EPS,"Profit",
           np.where(np.asarray(v)<-EPS,"Loss","Flat")))).to_csv(OUT/path,index=False)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    raw=pd.read_csv(BASE)
    row=raw[(raw.scenario=="stage18_70_30_30d") &
            (raw.extra_bps_side==0)].set_index("month_ist").reindex(MONTHS)
    assert row.portfolio_month_pct.notna().all()
    base=row.portfolio_month_pct.to_numpy(float)
    bs=stats(base)
    if abs(bs["return_pct"]-14.438074)>.001 or (bs["positive"],bs["negative"],bs["flat"])!=(19,2,1):
        raise AssertionError("Source 70/30 parity invalid: "+str(bs))
    print("BASELINE_70_30",json.dumps(bs))

    raw_models,count=make_model_pool()
    allmodels=[m for m in raw_models if admissible(m)]
    if len(allmodels)<100:raise AssertionError("Too few authentic 5m/1h strategies")
    print("CANDIDATE_CATALOG",json.dumps(dict(total_source_models=count,
        admissible_after_cost=len(allmodels),
        sources={k:sum(m["source"]==k for m in allmodels)
                 for k in set(m["source"] for m in allmodels)})))
    tab,training,expost,overlap=make_records(base,allmodels)
    # Note full history is NOT allowed for a trading rule.
    tab.to_csv(OUT/"all_fixed_third_sleeve_comparisons.csv.gz",index=False,
               compression="gzip")
    overlap.to_csv(OUT/"independent_models_profitable_in_both_jan25_and_sep26.csv",index=False)
    print("JAN25_SEP26_POSITIVE_MODELS",len(overlap))
    for label,item in [("SELECTED_2025_ONLY_SINGLE",training),
                       ("INVALID_HINDSIGHT_SINGLE",expost)]:
        _,summary,vec=item
        print(label,json.dumps(summary,default=str))
        output_monthly(label.lower()+"_monthly.csv",vec)

    # All variants retained using 2025 criteria ONLY (no 2026 screening).
    # Select unique candidates with >=3 profitable 2025 months and no 2025
    # loss exceeding 20% of that sleeve, pre-declared, so live risk may still
    # be poor (not executable with actual margin).
    eligible=[m for m in allmodels if (
        np.count_nonzero(m["returns"][:12]>EPS)>=3 and
        np.min(m["returns"][:12])>-20 and
        np.prod(1+np.asarray(m["returns"][:12])/100)>.6)]
    assert len(eligible)>=20
    X=np.column_stack([m["returns"][:22] for m in eligible])
    trainw,trainfloor=maximize_floor(X,base,train_only=True)
    trainvec=np.column_stack([base,X])@trainw
    trainout=[dict(name="immutable_stage18_70_30",source="core+donchian",
                  weight=float(trainw[0]))]
    trainout.extend(dict(name=m["name"],source=m["source"],weight=float(trainw[i+1]))
                    for i,m in enumerate(eligible) if trainw[i+1]>1.e-7)
    print("2025_ONLY_MAXIMIN",json.dumps(dict(
        train_min_month_pct=trainfloor,selection=trainout,
        realized_22m=stats(trainvec)),default=str))
    output_monthly("2025_only_fixed_portfolio_monthly.csv",trainvec)

    # An explicit theoretical bound, invalid for strategy selection.
    futurew,futurefloor=maximize_floor(X,base,train_only=False)
    futurevec=np.column_stack([base,X])@futurew
    futureout=[dict(name="immutable_stage18_70_30",source="core+donchian",weight=float(futurew[0]))]
    futureout.extend(dict(name=m["name"],source=m["source"],weight=float(futurew[i+1]))
                     for i,m in enumerate(eligible) if futurew[i+1]>1.e-7)
    print("INVALID_2025_2026_HINDSIGHT_LP",json.dumps(dict(
        hindsight_min_month_pct=futurefloor,
        selection=futureout,returns=stats(futurevec)),default=str))
    output_monthly("INVALID_hindsight_maximin_monthly.csv",futurevec)

    summary=dict(
        baseline=bs,catalog=count,admissible_models=len(allmodels),
        tested_fixed_single_portfolios=len(tab),weights=[.02,.05,.10,.15,.2,.25,.3],
        overlap_jan2025_and_sep2026_models=len(overlap),
        selected_single_using_2025=training[1],
        invalid_hindsight_single=expost[1],
        selected_portfolio_using_2025=dict(training_floor_pct=trainfloor,monthly_results=stats(trainvec),sleeves=trainout),
        INVALID_hindsight_full_period_LP=dict(fitted_floor_pct=futurefloor,
             monthly_results=stats(futurevec),sleeves=futureout),
        limitations=[
            "Models are archival, independently simulated 1m stop-first 5m and 1h signals; no new joint trade-level simulation",
            "Portfolio weighted monthly returns are synthetic, not a live shared-margin account",
            "2025-only tuning does not prevent selection overfit; prior 2026 research makes it non-pristine",
            "Hindsight full-period LP must NEVER be presented as a tradable 22-month solution",
            "Profitability of single month may be smaller than unmodeled extra execution costs and funding",
            "Only initial standard 0.05% taker fee per side + 18%GST + 5 BTC-point slip per side included",
            "Stage19 5m source model uses risk .5% per trade with max 5x leverage and 1m next-open fills",
            "No funding, spread, liquidation, exact lot or intramonth portfolio risk",
        ],NO_LIVE_TRADING=True)
    (OUT/"summary.json").write_text(json.dumps(summary,indent=2,default=str)+"\n")
    print("THIRD_SLEEVE_RESEARCH_DONE",json.dumps(dict(
      base=bs,valid_2025_selected=stats(trainvec),invalid_hindsight=stats(futurevec),
      report=OUT.as_posix()),default=str))
if __name__=="__main__":main()
