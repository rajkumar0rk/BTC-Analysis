#!/usr/bin/env python3
"""Stage 23: Broad BTC monthly-positive search with audit-friendly train/check.

NEW source families: archived Stage19 5M original and Stage20 direction-inverted
hourly/volume filtered 5M setups, plus preserved Stage18/20 and other historical
models. ALL net returns use their ORIGINAL standard taker/GST/5pts slippage,
with conservative 0.5% or 1% risk and at most 10x stated leverage.

Two VERY DIFFERENT outputs:
- TRAIN2025: Models and fixed non-negative portfolio allocations selected using
  2025 months ONLY, applied UNCHANGED to 2026. Check is still research-exposed.
- HINDSIGHT23: Oracle maximin fitted with ALL historical months, expressly NOT
  a deployable strategy; shows only mathematical feasibility. No manufactured
  future profit, switches based on month names or future trade labels.

Counts are number of independently executed trades in each source model.
Portfolio weights represent segregated capital sleeves, not a unified exchange
execution, and overlapping positions need more capital/margin. No guaranteed
future profits, even if historical 23/23 were feasible.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import json
from scipy.optimize import linprog

OUT=Path("analysis/institutional_discovery_stage23_broad_5m_monthly")
MONTHS=pd.period_range("2025-01","2026-11",freq="M").astype(str).tolist()
S19F=Path("analysis/institutional_discovery_stage19_monthly_10pct/monthly_net_account_returns.csv")
S20F=Path("analysis/institutional_discovery_stage20_inverse_direction/monthly_results.csv")
S18F=Path("analysis/institutional_discovery_stage18_monthly_dual_strategy/monthly_blended_returns.csv")
S20PORT=Path("analysis/institutional_discovery_stage20_three_sleeve/selected_month_by_month.csv")
S17F=Path("analysis/institutional_discovery_stage17_swing_breakout/monthly_mark_to_market.csv")
S19H=Path("analysis/institutional_discovery_stage19_new_1h_patterns/monthly_results.csv")
S16F=Path("analysis/institutional_discovery_stage16_monthly_regime_switch/monthly_results.csv")
NTRAD=23
HALF25=12
ZERO=1.e-7

def make_model_pool():
    models=[]
    def append(name,group,return_col,trade_col,source):
        group=group.sort_values("month_ist")
        if group.month_ist.tolist()!=MONTHS:
            raise AssertionError("Incomplete monthly series for "+name)
        vec=group[return_col].to_numpy(np.float64)
        if not np.isfinite(vec).all() or (vec<=-100).any():
            return
        if trade_col is None:
            n=np.full(NTRAD,-1,dtype=int)
        else:
            n=group[trade_col].to_numpy(int)
        if len(vec)!=NTRAD:raise AssertionError("Wrong month count")
        models.append(dict(name=name,source=source,returns=vec,trades=n))
    s18=pd.read_csv(S18F)
    s18=s18[(s18.stage15=="quiet_1h_weekly_3R")&
        (s18.stage17=="1D_channel_20_no_trend_filter_trail_3atr")&
        np.isclose(s18.swing_weight,.25)]
    append("PRESERVED_STAGE18",s18,"portfolio_pct",None,"stage18")
    s20=pd.read_csv(S20PORT)
    append("PRESERVED_STAGE20",s20,"portfolio_month_pct",None,"stage20_portfolio")
    s17=pd.read_csv(S17F)
    for name,g in s17.groupby("model",sort=True):
        append("SWING:"+name,g,"month_return_pct","entries","stage17")
    s19h=pd.read_csv(S19H)
    for name,g in s19h.groupby("model",sort=True):
        append("HOURLY:"+name,g,"modeled_return_pct","trades","stage19_hourly")
    s16=pd.read_csv(S16F)
    for (name,guard),g in s16.groupby(["profile","guard"],sort=True):
        if name=="stage14_unchanged":
            append("STAGE14:"+name+":"+guard,g,"modeled_equity_return_pct","trades","stage16")
    # Include new genuine source classes with after-taker-fee PNL.
    s19=pd.read_csv(S19F)
    s19=s19[s19.target_trade_risk_pct.isin([0.5,1.0])&
        s19.max_notional_leverage.isin([5.0,10.0])]
    keys=["pattern","trend_filter","stop_mode","reward_R","hold_min",
          "target_trade_risk_pct","max_notional_leverage"]
    for key,g in s19.groupby(keys,sort=True):
        name="FIVE_MIN_ORIG:"+":".join(map(str,key))
        append(name,g,"net_account_return_pct","trades","stage19_5m")
    s20inv=pd.read_csv(S20F)
    s20inv=s20inv[(s20inv.cost_mode=="standard_taker")&
        (s20inv.risk_fraction_pct.isin([0.5,1.0]))&
        (s20inv.max_leverage.isin([5.0,10.0]))]
    keys=["pattern","direction_mode","entry_filter","stop_mode",
        "target_R","hold_min","risk_fraction_pct","max_leverage"]
    for key,g in s20inv.groupby(keys,sort=True):
        name="FIVE_MIN_INVERT:"+":".join(map(str,key))
        append(name,g,"account_return_pct","trades","stage20_inverse_5m")
    if not models:raise RuntimeError("No sourced models")
    # Exact duplicates by historical outcomes are one independent model.
    unique=[]
    seen=set()
    for model in models:
        sig=tuple(np.round(model["returns"],6))
        if sig in seen:continue
        seen.add(sig)
        unique.append(model)
    return unique,dict(source_model_count=len(models),
        duplicate_return_series_removed=len(models)-len(unique))

def run_lp(X,row_idx,cap=.15,min_stage18=.25,force_stage18=True):
    """Linear optimization: maximize min monthly simple return from <=15% sleeves.

    The LP has non-negative fixed weights; no borrowed money or short models.
    The first variable is Stage18, fixed portfolio itself cannot be modified.
    """
    n=X.shape[1]
    A=np.column_stack([-X[np.asarray(row_idx)],np.ones(len(row_idx))])
    objective=np.zeros(n+1);objective[-1]=-1
    bounds=[(min_stage18 if force_stage18 and j==0 else 0.,
             1. if j==0 else cap) for j in range(n)]
    bounds.append((None,None))
    E=np.zeros((1,n+1));E[0,:n]=1.
    opt=linprog(objective,A_ub=A,b_ub=np.zeros(len(row_idx)),
        A_eq=E,b_eq=[1.],bounds=bounds,method="highs")
    if not opt.success:
        raise RuntimeError("LP infeasible: "+opt.message)
    return opt.x[:n],float(opt.x[-1]),opt.message

def scores(vec):
    def one(a):
        return dict(profitable=int((a>ZERO).sum()),
            losing=int((a<-ZERO).sum()),
            neutral=int((abs(a)<=ZERO).sum()),
            worst_pct=round(float(a.min()),6),
            compounded_pct=round(float((np.prod(1.+a/100)-1)*100),5))
    wealth=100.*np.r_[1.,np.cumprod(1+vec/100)]
    dd=100.*float(np.max(1.-wealth/np.maximum.accumulate(wealth)))
    return dict(y2025=one(vec[:HALF25]),y2026=one(vec[HALF25:]),
        all_months_positive=bool(np.all(vec>ZERO)),
        max_month_end_drawdown_pct=round(dd,4))

def serialize_alloc(models,weights,cap=40):
    ids=np.flatnonzero(weights>1.e-7)
    ids=sorted(ids,key=lambda j:-weights[j])
    return [dict(model=models[j]["name"],source=models[j]["source"],
        allocation_pct=round(float(100*weights[j]),5),
        gross_trades_2025=int(np.clip(models[j]["trades"][:12],0,None).sum()),
        gross_trades_2026=int(np.clip(models[j]["trades"][12:],0,None).sum()))
        for j in ids[:cap]]

def month_data(models,weights):
    X=np.column_stack([z["returns"] for z in models])
    vec=X@weights
    rows=[]
    for k,m in enumerate(MONTHS):
        rows.append(dict(month_ist=m,
            modeled_return_pct=round(float(vec[k]),6),
            status="Profit" if vec[k]>ZERO else
               "Loss" if vec[k]<-ZERO else "Neutral",
            modeled_weighted_sleeve_trades=round(float(sum(
                weights[j]*max(0,int(models[j]["trades"][k]))
                for j in np.flatnonzero(weights>1.e-7))),3),
            unique_component_closed_trades=sum(
                max(0,int(models[j]["trades"][k]))
                for j in np.flatnonzero(weights>1.e-7)),
            selected_sleeves=int((weights>1.e-7).sum())))
    return pd.DataFrame(rows)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    models,counts=make_model_pool()
    full=np.column_stack([z["returns"] for z in models])
    original=len(models)
    # The 2025 selection uses ONLY 2025 metrics. Absolutely no 2026
    # results enter this stage of model inclusion decisions.
    keep=[]
    for j,m in enumerate(models):
        prior=m["returns"][:12]
        profitable=int((prior>0).sum())
        # Keep one initially preserved model, plus heterogeneous helpful
        # sources with at least 2 positive training months and not total
        # collapse. All thresholds are fixed before seeing 2026 checks.
        if j<2 or (profitable>=2 and
                   np.min(prior)>-40 and
                   np.prod(1+prior/100)>0.40):
            keep.append(j)
    selected=[models[j] for j in keep]
    X=full[:,keep]
    if X.shape[1]<=50:raise AssertionError("Too few distinct source models")
    configurations=[
        ("Train2025_35pct_anchor15pct_cap",list(range(12)),.15,.35),
        ("Train2025_50pct_anchor10pct_cap",list(range(12)),.10,.50),
        ("Train2025_25pct_anchor15pct_cap",list(range(12)),.15,.25),
        ("HINDSIGHT_ALL23_35pct_anchor15pct_cap",list(range(23)),.15,.35)
    ]
    records={}
    for label,monthidx,cap,base in configurations:
        weights,floor,status=run_lp(X,monthidx,cap=cap,min_stage18=base)
        returns=X@weights
        score=scores(returns)
        records[label]=dict(label=label,floor_month_pct=round(floor,6),
            scores=score,selected_sleeves=int((weights>1.e-7).sum()),
            allocations=serialize_alloc(selected,weights))
        month_data(selected,weights).to_csv(
            OUT/(label+"_monthly.csv"),index=False)
        pd.DataFrame(serialize_alloc(selected,weights)).to_csv(
            OUT/(label+"_allocations.csv"),index=False)
        print("RESULT "+label+" "+json.dumps(dict(
            floor=floor,scores=score,
            n_sleeves=int((weights>1.e-7).sum()))))
    # Full historical hindsight mathematical feasibility with NO prior
    # model pruning, different from the fixed train-only model subset.
    # This calculation is explicitly NON-CAUSAL and must never be
    # presented as having predicted future gains.
    alt=run_lp(full,list(range(23)),cap=.15,min_stage18=.25)
    hindsight_weights,hindsight_floor,_=alt
    hindsight=scores(full@hindsight_weights)
    month_data(models,hindsight_weights).to_csv(
        OUT/"INVALID_full_hindsight_oracle_monthly.csv",index=False)
    pd.DataFrame(serialize_alloc(models,hindsight_weights)).to_csv(
        OUT/"INVALID_full_hindsight_oracle_allocations.csv",index=False)
    baseline=scores(full[:,0])
    meta=dict(
        target="Positive net monthly account PNL in all twelve 2025 and all observed 2026 months",
        models_total_before_pruning=counts["source_model_count"],
        models_unique_before_pruning=original,
        models_train_2025_only_filtered=len(selected),
        model_sources=sorted(set(z["source"] for z in models)),
        original_preserved_stage18=baseline,
        fixed_2025_train_allocations_and_2026_rechecks=records,
        historical_full_hindsight_oracle=dict(
            minimum_modeled_month_pct=round(hindsight_floor,6),
            scores=hindsight,
            noncausal_not_tradable=True),
        monthly_span=MONTHS,
        cost_model="Every candidate source includes standard taker 0.05% per side, GST 18%, adverse 5 BTC price points per side. Scalper Offer is NOT assumed.",
        limitations=[
          "The only test that uses 2026 in allocation fitting is clearly marked INVALID historical oracle",
          "Even 2025-only fit is likely overfit due to thousands of configurations",
          "All 2026 candle histories exposed by previous research; no pristine forward evaluation",
          "Original Stage18 and Stage20 are unchanged, only independent fixed-capital sleeves added",
          "Portfolio returns are fixed monthly weight averages of independently simulated strategies, not one integrated intraminute equity/margin engine",
          "No funding payments, actual spread, order book market impact, cross-venue hedge costs, monthly rebalancing fees, liquidation or contract lot granularity",
          "A positive historical NAV month does not imply guaranteed positive future months",
          "Some sources use exact fractional per-trade risk and max 5-10x exposure but actual exchange position feasibility unverified",
          "Trade counts in monthly output sum independent sleeves, which can overlap; not unique unified portfolio orders",
          "September 2026 is previously studied; no filter may select a strategy specifically because the month is September",
          "2026-10-31 source day missing; November 2026 only through November 16"
        ])
    (OUT/"quality.json").write_text(json.dumps(meta,indent=2)+"\n")
    report=[
        "# Stage23 — Wider BTC monthly profit search including 5M orig/fade strategies",
        "",
        "## Goal",
        "Positive returns in every observed month of **both 2025 and 2026**,",
        "after modeled Delta India taker fees, GST and slippage.",
        "",
        "## Candidate sources",
        f"{counts['source_model_count']} original configurations,",
        f"{original} distinct return series, {len(selected)} selected",
        "using ONLY 2025 training data for the real historical check.",
        "Original Stage18 and Stage20 preserved unchanged.",
        "",
        "## Important distinction",
        "TRAIN2025 portfolios are fixed using 2025 alone and then tested",
        "unchanged on 2026 (which has been exposed in prior research).",
        "**HINDSIGHT_ALL23 and INVALID_full_hindsight_oracle are mathematical",
        "upper bounds with future-month knowledge, NOT tradable strategies.**",
        "",
        "## Configuration results",
        pd.DataFrame([dict(name=k,
            train2025_winners=v["scores"]["y2025"]["profitable"],
            seen2026_winners=v["scores"]["y2026"]["profitable"],
            train2025_return_pct=v["scores"]["y2025"]["compounded_pct"],
            seen2026_return_pct=v["scores"]["y2026"]["compounded_pct"],
            minimum_fit_month_pct=v["floor_month_pct"],
            historical_all_positive=v["scores"]["all_months_positive"],
            selected_model_count=v["selected_sleeves"])
          for k,v in records.items()]).to_markdown(index=False),
        "",
        "## Historical full hindsight oracle (cannot be executed)",
        pd.DataFrame([dict(minimum_month_pct=round(hindsight_floor,6),
            **{k:v for k,v in hindsight.items() if k not in ("y2025","y2026")},
            prof2025=hindsight["y2025"]["profitable"],
            prof2026=hindsight["y2026"]["profitable"])]).to_markdown(index=False),
        "",
        "## TRAIN ONLY leading configuration monthly table",
        pd.read_csv(OUT/"Train2025_35pct_anchor15pct_cap_monthly.csv").to_markdown(index=False),
        "",
        "## HINDSIGHT upper bound monthly returns (NOT an actual profitable pattern)",
        pd.read_csv(OUT/"INVALID_full_hindsight_oracle_monthly.csv").to_markdown(index=False),
        "",
        "## Limitations",
        *["- "+x for x in meta["limitations"]]]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("STAGE23_COMPLETE "+json.dumps(dict(
        original_models=counts["source_model_count"],
        unique_models=original,train_only_selected=len(selected),
        train2025_35pct=scores(X@run_lp(X,list(range(12)),.15,.35)[0]),
        full_hindsight_23_months=hindsight)))
if __name__=="__main__":
    main()
