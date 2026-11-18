#!/usr/bin/env python3
"""Stage20: Third independent hourly pattern added to preserved Stage18.

Stage18 is NOT modified. The new proposed portfolio is a separate model
with fixed proportional sleeve allocation, monthly rebalanced:
90% Stage18 (75% range pullback / 25% Daily20 swing) and
10% Stage19 (1H compression breakout or other 1H pattern).
Scan Stage19 model catalog with 10, 15, 20% auxiliary weights.
Rank by 2025 data only, report 2026 historically exposed.

CAVEATS: Stage18 itself was chosen with prior 2026 exposure; this is
exploratory and carries multiple-testing selection bias.
Separate sleeves can hold concurrent positions; portfolio position
and margin interactions not directly simulated.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd

OUT=Path("analysis/institutional_discovery_stage20_three_sleeve")
STAGE18=Path("analysis/institutional_discovery_stage18_monthly_dual_strategy")
STAGE19=Path("analysis/institutional_discovery_stage19_new_1h_patterns")
FIXED_STAGE18=dict(stage15="quiet_1h_weekly_3R",
    stage17="1D_channel_20_no_trend_filter_trail_3atr",swing_weight=.25)
AUX_WEIGHTS=(.1,.15,.2)
MONTHS=pd.period_range("2025-01","2026-11",freq="M").astype(str)

def read():
    a=pd.read_csv(STAGE18/"monthly_blended_returns.csv")
    b=pd.read_csv(STAGE19/"monthly_results.csv")
    fixed=a[(a.stage15==FIXED_STAGE18["stage15"])&
            (a.stage17==FIXED_STAGE18["stage17"])&
            (a.swing_weight==FIXED_STAGE18["swing_weight"])].copy()
    fixed=fixed.sort_values("month_ist")
    if fixed.month_ist.tolist()!=list(MONTHS):
        raise AssertionError("Preserved Stage18 baseline missing month")
    if len(b.model.unique())!=140:
        raise AssertionError("Original Stage19 140 models not available")
    if b.month_ist.nunique()!=len(MONTHS):
        raise AssertionError("Stage19 monthly coverage incomplete")
    return fixed,b

def performance(returns):
    tr=returns[:12]
    check=returns[12:]
    def report(x):
        return int((x>1e-7).sum()),int((x<-1e-7).sum()),int((abs(x)<=1e-7).sum()),float(
            100*(np.prod(1.+x/100)-1))
    a=report(tr)
    b=report(check)
    eq=100.*np.r_[1.,np.cumprod(1.+returns/100)]
    peak=np.maximum.accumulate(eq)
    dd=100*float(np.max(1.-eq/peak))
    return a,b,dd

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    base,patterns=read()
    bret=base.portfolio_pct.to_numpy(float)
    base_stats=performance(bret)
    candidates=[]
    monthly=[]
    for name,group in patterns.groupby("model"):
        group=group.sort_values("month_ist")
        if group.month_ist.tolist()!=list(MONTHS):
            raise AssertionError("Stage19 month mismatch for "+name)
        newret=group.modeled_return_pct.to_numpy(float)
        for weight in AUX_WEIGHTS:
            x=(1-weight)*bret+weight*newret
            a,b,dd=performance(x)
            variant=name+f" + auxiliary {weight:.0%}"
            candidates.append(dict(variant=variant,stage19_model=name,
                new_pattern_weight=weight,
                quiet_volume_weight=(1-weight)*.75,
                daily20_weight=(1-weight)*.25,
                profitable_2025=a[0],losing_2025=a[1],idle_2025=a[2],
                return_2025_pct=round(a[3],5),
                profitable_2026=b[0],losing_2026=b[1],idle_2026=b[2],
                return_2026_pct=round(b[3],5),
                month_end_max_drawdown_pct=round(dd,5),
                all23_positive=bool(a[0]==12 and b[0]==11)))
            for index,month in enumerate(MONTHS):
                monthly.append(dict(variant=variant,stage19_model=name,
                    new_pattern_weight=weight,month_ist=month,
                    stage18_month_pct=float(bret[index]),
                    stage19_month_pct=float(newret[index]),
                    portfolio_month_pct=round(float(x[index]),6),
                    state=("Profit" if x[index]>1e-7 else
                           "Loss" if x[index]<-1e-7 else "No profit")))
    results=pd.DataFrame(candidates)
    monthly=pd.DataFrame(monthly)
    # The new pattern is selected strictly by 2025 only.
    rank=results.sort_values(["profitable_2025","losing_2025",
        "return_2025_pct","month_end_max_drawdown_pct"],
        ascending=[False,True,False,True],kind="stable")
    best=rank.iloc[0]
    # Compare 2026 AFTER choosing 2025 selection.
    winner=monthly[monthly.variant==best.variant].copy()
    base_report=dict(profitable_2025=base_stats[0][0],losing_2025=base_stats[0][1],
        idle_2025=base_stats[0][2],return_2025_pct=base_stats[0][3],
        profitable_2026=base_stats[1][0],losing_2026=base_stats[1][1],
        idle_2026=base_stats[1][2],return_2026_pct=base_stats[1][3],
        max_month_end_dd=base_stats[2])
    results.to_csv(OUT/"all_420_configurations.csv",index=False)
    rank.head(25).to_csv(OUT/"2025_selected_rank_with_2026_checks.csv",index=False)
    winner.to_csv(OUT/"selected_month_by_month.csv",index=False)
    quality=dict(
        stage18_preserved=True,
        stage18_baseline_config=FIXED_STAGE18,
        stage18_baseline_stats=base_report,
        stage19_distinct_model_count=int(patterns.model.nunique()),
        total_three_sleeve_variants=len(results),
        selection_method_2025="2025 profitable month count, then losing months, then compounded return, then worst month-end drawdown",
        historical_perfect_monthly_count=int(results.all23_positive.sum()),
        selected=best.to_dict(),
        position_sizing="compounded monthly NAV weights 67.5/22.5/10 percent if 10% auxiliary",
        monthly_costs="Component simulations include taker fees 0.05% each side, GST 18%, 5 adverse BTC points per side",
        important_caveats=[
          "All 2025/2026 candles previously explored; 2026 not pristine out of sample",
          "Stage18 baseline was itself selected using 2026 historical performance",
          "Exploratory 420 trials are subject to substantial data-mining bias",
          "Portfolio uses separate concurrent sleeves, modelled by monthly return blends rather than portfolio-level order replay",
          "Rebalancing commissions, margin, funding, true bid ask, liquidation are not included",
          "Stage19 1H hourly pattern trade net R is booked at exit IST month while Stage18 daily swing marks open positions at month-end",
          "Month-end max drawdown excludes intraday peaks and troughs",
          "Fractional 0.5% risk per component requires compatible exchange contract granularity",
          "Zero or no exposure is not a winning month",
          "November 2026 data through 16th; 2026-10-31 source missing",
          "Historical 100% consistency would not imply guaranteed future profits"])
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2)+"\n")
    report=[
        "# Stage20 — Add new hourly pattern to preserved Stage18",
        "",
        "## Baseline frozen",
        "Stage18 unchanged: 75% 1H quiet-volume pullback, 25% Daily 20 Donchian swing.",
        "",
        "## New model search",
        "140 Stage19 hourly strategies, combined with only 10%, 15%, or 20%",
        "auxiliary capital (420 cases). All historical monthly net returns include",
        "standard taker fees, GST and assumed 5-point adverse slippage per leg.",
        "",
        "## Frozen original and best selected by 2025 (then 2026 recheck)",
        pd.DataFrame([dict(model="Original Stage18",**base_report),
                      dict(model="New Stage20 2025 selected",**best.to_dict())]).to_markdown(index=False),
        "",
        "## 2025 selected candidate monthly results",
        winner[["month_ist","stage18_month_pct","stage19_month_pct",
                "portfolio_month_pct","state"]].to_markdown(index=False),
        "",
        f"**Historical all-month profitable models: {int(results.all23_positive.sum())}/{len(results)}**",
        "",
        "## Top 2025-ranked alternatives",
        rank.head(20).to_markdown(index=False),"",
        "## Caveats",
        *["- "+c for c in quality["important_caveats"]],
        "",
        "Never apply a monthly loser-exclusion label using hindsight.",
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("STAGE20_FINISHED "+json.dumps({
        "models":len(results),"perfect_month_models":int(results.all23_positive.sum()),
        "stage18_positive":[base_report["profitable_2025"],base_report["profitable_2026"]],
        "best_by_2025":best.variant,
        "new_positive":[int(best.profitable_2025),int(best.profitable_2026)],
        "net_return":[float(best.return_2025_pct),float(best.return_2026_pct)]}))
    print("BEST_MONTHS\n"+winner.to_string(index=False))
    print("TOP_2025_RANK\n"+rank.head(10).to_string(index=False))
if __name__=="__main__":
    main()
