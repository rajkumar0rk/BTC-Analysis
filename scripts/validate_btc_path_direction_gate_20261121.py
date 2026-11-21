#!/usr/bin/env python3
"""Fail-closed quality and economics gate for BTC direction meta-forecast.

This report may PASS as a successful audit run while the *strategy itself*
is BLOCKED. It never changes, arms or deploys a live trading service.
"""
import json
from pathlib import Path
import pandas as pd
import numpy as np

OUT=Path("analysis/btc_path_aware_direction_20261121")
score=pd.read_csv(OUT/"conditional_direction_score.csv")
accounts=pd.read_csv(OUT/"account_comparison.csv")
month=pd.read_csv(OUT/"monthly_account_comparison.csv")
training=pd.read_csv(OUT/"monthly_training_audit.csv")
cases=pd.read_csv(OUT/"isolated_event_outcome_training_labels.csv")
assert len(training)==16, "Expected 16 chronological monthly trainings"
assert len(month)==44,"Expected 22 monthly returns for each of two comparators"
assert len(score)==12,"Expected all yearly and combined model comparisons"
assert len(accounts)==2,"Expected both account scenarios"
assert len(cases)>3000,"Path-aware training labels missing"
assert (pd.to_datetime(training.training_last_released_utc,utc=True) <=
        pd.to_datetime(training.month_open_utc,utc=True)).all(),\
    "Lookahead in monthly training: release after cutoff"
assert (pd.to_datetime(cases.release_utc,utc=True)>
        pd.to_datetime(cases.exit_utc,utc=True)).all(),\
    "Trade label became known before the exit minute ended"
assert (cases.modeled_fee_price_points>=0).all()
assert (cases.modeled_slippage_price_points>=0).all()
assert (cases.outcome_profitable==(cases.net_price_points>0)).all()

bo=accounts[accounts.model=="conditional_meta"].iloc[0]
reference=accounts[accounts.model=="event_baseline"].iloc[0]
checks={}
for period in ["2025H2","2026JanOct"]:
    gm=score[(score.period==period)&(score.model=="boosted")].iloc[0]
    prior=score[(score.period==period)&(score.model=="trained_event_prior")].iloc[0]
    checks[period]=dict(
        evidence_sample_size=int(gm.events),
        accepted_nonoverlapping=int(gm.acceptance_events),
        direction_net_outcome_auc=float(gm.direction_auc),
        boost_brier=float(gm.brier_score),
        prior_win_rate_brier=float(prior.brier_score),
        accepted_isolated_positive_pct=float(gm.accepted_isolated_net_win_pct),
        all_event_isolated_positive_pct=float(gm.actual_net_win_rate_pct),
        adequate_evidence=bool(
           int(gm.events)>=200 and int(gm.acceptance_events)>=40),
        discriminative_and_calibrated=bool(
           float(gm.direction_auc)>=.57 and
           float(gm.brier_score)<=float(prior.brier_score)-.005),
        positive_selector_advantage=bool(
           float(gm.accepted_isolated_net_win_pct)>=
           float(gm.actual_net_win_rate_pct)+8))
final=dict(
    status="REJECTED_NOT_DIRECTIONALLY_RELIABLE",
    research_checks_passed=True,
    no_trade_when_unproven=True,
    research_only=True,
    approved_to_predict_real_money_direction=False,
    approved_to_trade=False,
    has_independent_unseen_holdout=False,
    historical_orderbook_spreads_available=False,
    realized_funding_payments_reconstructed=False,
    both_years_meet_directional_quality=all(
        x["adequate_evidence"] and x["discriminative_and_calibrated"] and
        x["positive_selector_advantage"] for x in checks.values()),
    after_cost_account_passes=bool(
        float(bo.net_return_pct)>0 and
        float(bo.profit_factor)>1.15 and
        int(bo.profitable_months)>=12),
    target_22_months_profitable=bool(bo.is_22_of_22),
    path_aware_account_net_return_pct=float(bo.net_return_pct),
    path_aware_profit_factor=float(bo.profit_factor),
    year_detail=checks,
    reference_all_events_net_pct=float(reference.net_return_pct),
    selected_trade_count=int(bo.trades),
    training_event_labels=len(cases),
    why="Past-only, economically matched 1M first-touch labels were available and audited, but forecasting failed calendar-year discrimination / calibration / year sample and profit gates. Refuse all live directional trading.",
)
assert not (final["approved_to_trade"] and not final["both_years_meet_directional_quality"])
assert not final["target_22_months_profitable"]
(OUT/"DIRECTION_DEPLOYMENT_GATE.json").write_text(json.dumps(final,indent=2)+"\n")
summary=[
"# BTC event-side directional release decision — BLOCKED",
"",
"## Result",
"Both the 4H closing-direction model and the economically path-aware alternative failed to establish reliable after-cost directional predictions. A higher 4H closing-price hit rate cannot override native 1M stops and costs.",
"",
"## Explicit fail-closed decision","~~~json",json.dumps(final,indent=2),"~~~","",
"## Required before enabling any future model",
"Repeatedly exceed prior-only forecast quality and sampled conditional hit rate on each chronological year, have enough accepted trades in every evaluated year, demonstrate positive net return / PF on conservative 1M exclusive-position replay, secure independent unresearched forward sample, and reconstruct actual funding / spreads / margin feasibility. This gate authorizes neither real-money trading nor strategy merging.",
"",
"All results are for research only. No claim is made that the probability of BTC price rising or falling can be predicted reliably from these observed data."
]
(OUT/"DIRECTION_DEPLOYMENT_GATE.md").write_text("\n".join(summary)+"\n")
print(json.dumps(final,indent=2))
print("AUDIT_SUCCEEDED_MODEL_STILL_BLOCKED")
