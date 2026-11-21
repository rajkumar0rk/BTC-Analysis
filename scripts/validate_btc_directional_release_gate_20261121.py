#!/usr/bin/env python3
"""Guard against declaring an invalid BTCUSD future-direction market selector ready.

Compares already-fixed, previously run models. No backtest fitting, no new
threshold optimization, and no hypothetical 'ground truth regime accuracy'.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score,brier_score_loss,accuracy_score

BASE=Path("analysis")
OUT=BASE/"btc_directional_release_gate_20261121"
OUT.mkdir(parents=True,exist_ok=True)
SOURCES={
  "price_only":BASE/"btc_directional_diagnosis_20261121",
  "oi_mark_funding":BASE/"btc_microstructure_directional_20261121",
}
YEARS=["2025","2026"]

def boot_diff_ci(frame,prob,prior):
    f=frame.copy()
    f["day"]=pd.to_datetime(f.signal_hour_start_utc,utc=True).dt.floor("D")
    y=f.true_future4h_up.to_numpy(int)
    correct=(np.asarray(prob)>=.5).astype(int)==y
    baseok=(np.asarray(prior)>=.5).astype(int)==y
    f["paired_diff"]=correct.astype(int)-baseok.astype(int)
    daily=f.groupby("day").paired_diff.agg(["sum","count"])
    rng=np.random.default_rng(1701)
    d=daily["sum"].to_numpy(float)
    n=daily["count"].to_numpy(float)
    if len(d)<40: raise RuntimeError("Not enough independent days")
    # Resample UTC-days with replacement to respect within-day correlation.
    intervals=[]
    for i in range(1000):
        sample=rng.integers(0,len(d),size=len(d))
        intervals.append(100*float(d[sample].sum())/float(n[sample].sum()))
    return round(float(np.quantile(intervals,.025)),3),round(float(np.quantile(intervals,.975)),3)

def yearly_scores(source,datadir):
    pred=pd.read_csv(datadir/"hourly_forecast_ledger.csv")
    score=pred.loc[pred.nonoverlapping_4h_sample &
                   pred.true_future4h_up.notna() &
                   pred.true_future4h_expansion.notna()].copy()
    if len(score)!=2928:
        raise RuntimeError("Unexpected sampled validation count, parity not proven: "+source+":"+str(len(score)))
    rows=[]
    for year in YEARS:
        f=score[score.year.astype(str)==year]
        if len(f)<1000: raise RuntimeError("Insufficient year block")
        y=f.true_future4h_up.to_numpy(int)
        m=f.true_future4h_expansion.to_numpy(int)
        for model in ["boosted","logistic"]:
            p=f["p_up_"+model].to_numpy(float)
            px=f["p_expansion_"+model].to_numpy(float)
            trainprior=f.p_up_prior.to_numpy(float)
            trainexp=f.p_expansion_prior.to_numpy(float)
            ci=boot_diff_ci(f,p,trainprior)
            rows.append(dict(source=source,year=year,model=model,n=len(f),
               directional_accuracy_pct=round(100*accuracy_score(y,(p>=.5).astype(int)),3),
               training_prior_accuracy_pct=round(100*accuracy_score(y,(trainprior>=.5).astype(int)),3),
               direction_accuracy_advantage_pp=round(100*(accuracy_score(y,(p>=.5).astype(int))-accuracy_score(y,(trainprior>=.5).astype(int))),3),
               accuracy_advantage_utc_day_bootstrap_ci_low_pp=ci[0],
               accuracy_advantage_utc_day_bootstrap_ci_high_pp=ci[1],
               directional_auc=round(float(roc_auc_score(y,p)),5),
               direction_brier=round(float(brier_score_loss(y,p)),5),
               training_prior_dir_brier=round(float(brier_score_loss(y,trainprior)),5),
               expansion_auc=round(float(roc_auc_score(m,px)),5),
               expansion_brier=round(float(brier_score_loss(m,px)),5),
               expansion_prior_brier=round(float(brier_score_loss(m,trainexp)),5),
               expansion_prevalence_pct=round(100*m.mean(),2)))
    return rows

def main():
    rows=[]
    for key,loc in SOURCES.items():
        if not (loc/"RESEARCH_REPORT.md").exists():
            raise RuntimeError("Missing prior model output: "+key)
        rows.extend(yearly_scores(key,loc))
    d=pd.DataFrame(rows)
    d.to_csv(OUT/"directional_vs_expansion_by_year.csv",index=False)
    gates={}
    for key,loc in SOURCES.items():
        s=json.loads((loc/"trading_summary.json").read_text())
        o=d[(d.source==key)&(d.model=="boosted")].sort_values("year")
        # These minimum thresholds are SAFETY gates, not optimized signals.
        # An external truly untouched holdout is still required even if passed.
        dirs=all(
            x.directional_auc>=.55 and
            x.direction_accuracy_advantage_pp>=2.0 and
            x.direction_brier<=x.training_prior_dir_brier-0.005 and
            x.accuracy_advantage_utc_day_bootstrap_ci_low_pp>0
            for x in o.itertuples(index=False))
        economics=(s["account_net_return_pct"]>0 and
                   s["profit_factor"] is not None and s["profit_factor"]>1.1)
        volatility_candidate=all(
            x.expansion_auc>.60 and x.expansion_brier<x.expansion_prior_brier
            for x in o.itertuples(index=False))
        gate={
            "direction_prediction_evidence_passed":bool(dirs),
            "historical_backtest_economics_passed":bool(economics),
            "directional_strategy_promotion_allowed":False,  # no external blind validation
            "directional_strategy_trading_enabled":False,
            "causality_test_completed":True,
            "external_blind_holdout_available":False,
            "observed_2025_2026_periods_previously_explored":True,
            "volatility_probability_candidate_for_new_research":bool(volatility_candidate),
            "volatility_probability_live_trade_allowed":False,
            "goal_22_profitable_months_met":bool(s["passes_22_22"]),
            "net_trade_return_pct":s["account_net_return_pct"],
            "profitable_months":s["profitable_months"],
            "why_failed":"No durable 2025H2+2026 directional skill with positive after-cost PnL; all year-specific safety gates required, plus new untouched data before enabling trading.",
        }
        gates[key]=gate
    (OUT/"directional_release_gate.json").write_text(json.dumps(gates,indent=2)+"\n")
    selected=d[d.model=="boosted"].copy()
    report=[
      "# BTC directional predictor deployment gate — FAIL CLOSED",
      "",
      "## Decision",
      "The trading selector must NOT treat either tested directional model as validated or enable orders. Two preregistered predictor families were independently evaluated on chronological months, and simple prior/momentum controls were measured. **Correcting the label-imbalance bug does not automatically create predictive edge.** No training or model selection occurs in this gate.",
      "",
      "## What passes and fails",
      json.dumps(gates,indent=2),"",
      "## Correctly scored by calendar year, genuine future UP-v-DOWN instead of majority RANGE",
      selected.to_markdown(index=False),"",
      "## Model vs baseline comparisons (both linear and nonlinear)",
      d.to_markdown(index=False),"",
      "## Deployability rules",
      "- No directional model can be promoted without both-year direction AUC >=0.55, >=2 point accuracy improvement vs past-only majority, directional Brier improvement >=0.005, paired day-bootstrap 95% lower bound >0, and independently profitable modeled trade PnL with PF >1.1.",
      "- Even if these retrospective gates pass, a new untouched period with known true spread, realized funding settlement, fill and liquidation feasibility is REQUIRED. All models stay disabled for real money.",
      "- Next-4H expansion probability is a potentially promising information source only if both years outperform historical expansion frequency; this is NOT proof of trade profitability or direction.",
      "- No strategy is authorized to force an UP or DOWN trade because the market is currently trending; the fallback is NO_TRADE.",
      "- Historical 2026 results already studied across the repo, so this is an analysis of previous observations, NOT a new blind holdout.",
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print(selected.to_string(index=False))
    print("PROMOTION_GATES",json.dumps(gates))
    print("COMPLETE")

if __name__=="__main__":
    main()
