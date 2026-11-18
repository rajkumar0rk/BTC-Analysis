#!/usr/bin/env python3
"""Stage 21: seek a 23/23 monthly-positive BTC strategy PORTFOLIO without changing Stage18/20.

Strict train/check:
* Optimize fixed, nonnegative monthly portfolio sleeve weights on 2025 only.
* Freeze weights; inspect all previously research-exposed 2026 months.
* Show an explicitly UNDEPLOYABLE full-history oracle feasibility upper bound.
* No month-number timing, no negative weights, no switch to future winners.
* Mark 2026 Nov as incomplete and Oct31 historical source gap.

Inputs are reproducible, already replayed and fee-adjusted from Stage16,
Stage17, Stage18, Stage19. This is a portfolio-of-separate-capital-sleeves
study, not an integrated Delta order/margin engine.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy.optimize import linprog

OUT=Path("analysis/institutional_discovery_stage21_monthly_perfect_search")
STAGE16=Path("analysis/institutional_discovery_stage16_monthly_regime_switch/monthly_results.csv")
STAGE17=Path("analysis/institutional_discovery_stage17_swing_breakout/monthly_mark_to_market.csv")
STAGE18=Path("analysis/institutional_discovery_stage18_monthly_dual_strategy/monthly_blended_returns.csv")
STAGE19=Path("analysis/institutional_discovery_stage19_new_1h_patterns/monthly_results.csv")
MONTHS=pd.period_range("2025-01","2026-11",freq="M").astype(str).tolist()
YEAR25=np.arange(12)
YEAR26=np.arange(12,23)
BASELINE=dict(stage15="quiet_1h_weekly_3R",
    stage17="1D_channel_20_no_trend_filter_trail_3atr",swing_weight=.25)

def load_monthly_series():
    assets=[]
    origin=[]
    raw=pd.read_csv(STAGE18)
    sel=raw[(raw.stage15==BASELINE["stage15"])&
        (raw.stage17==BASELINE["stage17"])&
        (np.isclose(raw.swing_weight,BASELINE["swing_weight"]))].sort_values("month_ist")
    assert sel.month_ist.tolist()==MONTHS
    assets.append(("Preserved Stage18 75/25",sel.portfolio_pct.to_numpy(float)))
    origin.append("stage18")
    other=pd.read_csv(STAGE19)
    for name,g in other.groupby("model",sort=True):
        g=g.sort_values("month_ist")
        if g.month_ist.tolist()!=MONTHS:raise AssertionError("Stage19 missing "+name)
        assets.append(("Stage19 "+name,g.modeled_return_pct.to_numpy(float)))
        origin.append("stage19")
    old=pd.read_csv(STAGE16)
    for (name,guard),g in old.groupby(["profile","guard"],sort=True):
        if name=="stage14_unchanged" or name.startswith("rolling_"):
            g=g.sort_values("month_ist")
            if g.month_ist.tolist()!=MONTHS:raise AssertionError("Stage16 missing "+name)
            assets.append((f"Stage16 {name} : {guard}",
                g.modeled_equity_return_pct.to_numpy(float)))
            origin.append("stage16")
    swing=pd.read_csv(STAGE17)
    for name,g in swing.groupby("model",sort=True):
        g=g.sort_values("month_ist")
        if g.month_ist.tolist()!=MONTHS:raise AssertionError("Stage17 missing "+name)
        assets.append(("Stage17 "+name,g.month_return_pct.to_numpy(float)))
        origin.append("stage17")
    # Deduplicate series that are exactly the same on all month ends.
    unique=[]
    seen=set()
    for (nm,v),kind in zip(assets,origin):
        sig=tuple(np.round(v,6))
        if sig in seen:continue
        seen.add(sig)
        unique.append((nm,kind,v))
    names=[x[0] for x in unique]
    kinds=[x[1] for x in unique]
    matrix=np.column_stack([x[2] for x in unique])
    return names,kinds,matrix

def solve_floor(matrix,indices,selected,lower_base=0.,upper_other=.35):
    """Constrained maximum of minimum MONTHLY portfolio net return.

    The optimizer has only the training-period rows specified by indices.
    Caps on different sleeves limit absurd 100%-allocation to one overfit signal.
    All returns are percentages already net of modeled fees.
    """
    ids=list(selected)
    M=matrix[np.ix_(indices,ids)]
    if M.size==0:return None
    n=len(ids)
    objective=np.zeros(n+1)
    objective[-1]=-1.
    # maximize t subject to M @ weights >= t each month
    Aub=np.hstack([-M,np.ones((len(indices),1))])
    bub=np.zeros(len(indices))
    caps=[1. if ids[j]==0 else upper_other for j in range(n)]
    bounds=[(lower_base if ids[j]==0 else 0.,cap) for j,cap in enumerate(caps)]
    bounds.append((None,None))
    eq=np.zeros((1,n+1))
    eq[0,:n]=1.
    res=linprog(objective,A_ub=Aub,b_ub=bub,A_eq=eq,b_eq=[1.],
        bounds=bounds,method="highs")
    if not res.success:return None
    weights=res.x[:n]
    out=np.zeros(matrix.shape[1])
    out[ids]=weights
    return out,float(res.x[-1])

def scores(v):
    def m(ar):
        return dict(winners=int((ar>1e-6).sum()),
            losers=int((ar<-1e-6).sum()),
            neutral=int((abs(ar)<=1e-6).sum()),
            min_month_pct=round(float(ar.min()),4),
            compounded_pct=round(float(100*(np.prod(1+ar/100)-1)),4))
    equity=100*np.r_[1.,np.cumprod(1+v/100)]
    dd=100*np.max(1.-equity/np.maximum.accumulate(equity))
    return m(v[:12]),m(v[12:]),round(float(dd),4)

def select_sparse(matrix,train,anchor,limit=6):
    """One-pass sparse greedy: all selection scores use training months ONLY.

    Start with an unaltered anchor; add the model that maximizes the worst
    month of 2025 after re-optimizing train-only nonnegative weights.
    """
    chosen=[0]
    track=[]
    for step in range(1,limit):
        best=None
        for j in range(1,matrix.shape[1]):
            if j in chosen:continue
            trial=solve_floor(matrix,train,chosen+[j],anchor)
            if trial is None:continue
            w,floor=trial
            if best is None or floor>best[0]+1e-10:
                best=(floor,j,w)
        if best is None:break
        floor,j,w=best
        chosen.append(j)
        track.append(dict(step=step,model_index=int(j),floor_pct=round(float(floor),6)))
    final=solve_floor(matrix,train,chosen,anchor)
    return chosen,final,track

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    names,kinds,X=load_monthly_series()
    baseline=X[:,0]
    configs=[]
    for anchor in (0.,.25,.5,.65,.75):
        for slots in (4,6,9):
            choose,solution,trace=select_sparse(X,YEAR25,anchor,limit=slots)
            if solution is None:continue
            w,floor=solution
            v=X@w
            train,check,dd=scores(v)
            configs.append(dict(name=f"2025_train_anchor{anchor:.2f}_slots{slots}",
                train_anchor=anchor,max_sleeves=slots,chosen=choose,
                trace=trace,weights=w,month_returns=v,
                train_floor=floor,train=train,check=check,drawdown=dd))
    # A full-history ORACLE has access to future winners and therefore
    # deliberately cannot count as a valid forward-consistency strategy.
    # Its sole purpose is to learn whether the existing menu COULD
    # explain 23 positive months even with retrospective fitting.
    oracle_all=solve_floor(X,np.arange(23),range(X.shape[1]),0.,.35)
    # Train-only full LP is also an optimistic in-sample upper bound.
    oracle_train=solve_floor(X,YEAR25,range(X.shape[1]),0.,.35)
    if not configs:raise RuntimeError("No train-only portfolio solutions")
    chosen=sorted(configs,key=lambda z:(
        -z["train"]["winners"],z["train"]["losers"],
        -z["train"]["min_month_pct"],-z["train"]["compounded_pct"]))[0]
    def desc(w):
        active=np.flatnonzero(w>1e-6)
        return [dict(strategy=names[j],family=kinds[j],
            weight_pct=round(float(w[j]*100),3),
            component_return_2025_pct=round(
                float(100*(np.prod(1+X[:12,j]/100)-1)),3))
            for j in active]
    records=[]
    for z in configs:
        records.append(dict(name=z["name"],train_anchor=z["train_anchor"],
            max_sleeves=z["max_sleeves"],
            weights=" | ".join(f"{names[j]} {z['weights'][j]*100:.1f}%"
                for j in np.flatnonzero(z["weights"]>1e-6)),
            positive_2025=z["train"]["winners"],
            losing_2025=z["train"]["losers"],
            neutral_2025=z["train"]["neutral"],
            worst_2025_pct=z["train"]["min_month_pct"],
            compound_2025_pct=z["train"]["compounded_pct"],
            positive_2026=z["check"]["winners"],
            losing_2026=z["check"]["losers"],
            neutral_2026=z["check"]["neutral"],
            worst_2026_pct=z["check"]["min_month_pct"],
            compound_2026_pct=z["check"]["compounded_pct"],
            max_month_end_dd=z["drawdown"]))
    out=pd.DataFrame(records)
    out.to_csv(OUT/"train2025_weight_solutions.csv",index=False)
    selected=desc(chosen["weights"])
    pd.DataFrame(selected).to_csv(OUT/"selected_weight_allocations.csv",index=False)
    reference=X[:,0]
    ret=chosen["month_returns"]
    history=[]
    for i,m in enumerate(MONTHS):
        history.append(dict(month_ist=m,
            stage18_reference_pct=round(float(reference[i]),5),
            stage21_train_selected_pct=round(float(ret[i]),5),
            status=("Profit" if ret[i]>1e-6 else
                    "Loss" if ret[i]<-1e-6 else "Neutral")))
    pd.DataFrame(history).to_csv(OUT/"selected_monthly_returns.csv",index=False)
    def oracle_stats(oracle,tag):
        if oracle is None:return dict(status="infeasible")
        w,floor=oracle
        tr,ch,dd=scores(X@w)
        result=dict(status="feasible",train_2025=tr,seen_2026=ch,
            floor_pct=round(float(floor),4),
            max_month_end_dd=dd,top_allocations=desc(w)[:30])
        pd.DataFrame(desc(w)).to_csv(OUT/(tag+"_weights.csv"),index=False)
        pd.DataFrame([dict(month_ist=m,modeled_portfolio_pct=round(float(x),6))
            for m,x in zip(MONTHS,X@w)]).to_csv(OUT/(tag+"_monthly.csv"),index=False)
        return result
    optimistic_train=oracle_stats(oracle_train,"optimistic_2025_only_lp")
    hindsight=oracle_stats(oracle_all,"NONCAUSAL_hindsight_23month_oracle")
    metadata=dict(
        monthly_target="23 of 23 positive months, all after costs",
        observed_months=MONTHS,source_assets=len(names),
        source_families=kinds,train_only_configurations=len(configs),
        selected_using_2025_only=dict(
            name=chosen["name"],train_stats=chosen["train"],
            chronological_2026=chosen["check"],
            max_month_end_drawdown_pct=chosen["drawdown"],
            weights=selected),
        optimistic_2025_train_only_lp=optimistic_train,
        explicitly_noncausal_all_23_months_oracle=hindsight,
        costs="source strategy backtests account for standard taker fees, 18% GST and adverse 5-point slippage per side",
        warnings=[
            "This is a fixed-weight blend of independently traded strategy ledgers, not a live tradable unified execution engine",
            "All underlying strategies and 2026 history have been inspected in previous research; not untouched forward data",
            "No future month labels enter train-only selector; full-history oracle is explicitly NOT deployable",
            "Fitting 2025 12 points with many models greatly overfits; sparse 4-8 sleeve selection is exploratory",
            "Month-end equity can mask severe intramonth drawdown, stops and risk gaps",
            "Spreads, funding payments, margin/contract step sizing, portfolio rebalance fees not modeled",
            "2026 November has only first 16 days, Oct 31 source gap",
            "No strategy can assure a positive month in future"])
    (OUT/"quality.json").write_text(json.dumps(metadata,indent=2)+"\n")
    summary=[
        "# Stage21 — Fixed-weight sparse portfolio search for monthly-positive BTC returns",
        "",
        "The historical target is positive in EVERY one of the 23 observed IST months.",
        "Uses original source net monthly returns from Stage16, 17, 18 and 19.",
        "**Stage18 and Stage20 are preserved unchanged.**",
        "",
        "## Valid research approach",
        "Choose model constituents and fixed nonnegative weights from 2025 only.",
        "Then hold exactly the same weights in the previously seen 2026 data.",
        "Do not use future labels, historical month exclusions, or negative weights.",
        "",
        "## Best sparse model selected on 2025 months",
        pd.DataFrame([dict(method=chosen["name"],
            profitable_2025=chosen["train"]["winners"],
            losing_2025=chosen["train"]["losers"],
            no_profit_2025=chosen["train"]["neutral"],
            profit_2026=chosen["check"]["winners"],
            loss_2026=chosen["check"]["losers"],
            no_profit_2026=chosen["check"]["neutral"],
            modeled_return_2025=chosen["train"]["compounded_pct"],
            modeled_return_2026=chosen["check"]["compounded_pct"])]).to_markdown(index=False),
        "",
        "## Selected strategy weights",
        pd.DataFrame(selected).to_markdown(index=False),
        "",
        "## Monthly returns: Stage18 and 2025-only selected portfolio",
        pd.DataFrame(history).to_markdown(index=False),
        "",
        "## Search diagnostics",
        "2025-only unconstrained-sparse LP upper bound:",
        str(optimistic_train.get("train_2025")),
        "Its 2026 check:",str(optimistic_train.get("seen_2026")),"",
        "23-month HINDSIGHT oracle LP (INVALID as a live strategy):",
        str(hindsight.get("floor_pct")),
        str(hindsight.get("train_2025")),
        str(hindsight.get("seen_2026")),"",
        "This full-history oracle is NOT an executable predictive strategy.",
        "",
        "## Full selection runs",out.to_markdown(index=False),"",
        "## Limitations",
        *["- "+c for c in metadata["warnings"]]]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(summary)+"\n")
    print("STAGE21_COMPLETE "+json.dumps({
        "models":len(names),"configs":len(configs),
        "selected":chosen["name"],
        "train_2025":chosen["train"],
        "checked_2026":chosen["check"],
        "valid_23month_target":bool(chosen["train"]["winners"]==12 and
                                     chosen["check"]["winners"]==11),
        "hindsight_upper_bound_floor_pct":hindsight.get("floor_pct"),
        "hindsight_upper_bound_stats":[hindsight.get("train_2025"),
                                        hindsight.get("seen_2026")]
    }))
    print("SELECTED_WEIGHTS\n"+pd.DataFrame(selected).to_string(index=False))
    print("SELECTED_MONTHS\n"+pd.DataFrame(history).to_string(index=False))
if __name__=="__main__":
    main()
