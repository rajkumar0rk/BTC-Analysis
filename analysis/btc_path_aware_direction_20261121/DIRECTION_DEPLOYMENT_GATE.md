# BTC event-side directional release decision — BLOCKED

## Result
Both the 4H closing-direction model and the economically path-aware alternative failed to establish reliable after-cost directional predictions. A higher 4H closing-price hit rate cannot override native 1M stops and costs.

## Explicit fail-closed decision
~~~json
{
  "status": "REJECTED_NOT_DIRECTIONALLY_RELIABLE",
  "research_checks_passed": true,
  "no_trade_when_unproven": true,
  "research_only": true,
  "approved_to_predict_real_money_direction": false,
  "approved_to_trade": false,
  "has_independent_unseen_holdout": false,
  "historical_orderbook_spreads_available": false,
  "realized_funding_payments_reconstructed": false,
  "both_years_meet_directional_quality": false,
  "after_cost_account_passes": false,
  "target_22_months_profitable": false,
  "path_aware_account_net_return_pct": -20.5727,
  "path_aware_profit_factor": 0.5301,
  "year_detail": {
    "2025H2": {
      "evidence_sample_size": 229,
      "accepted_nonoverlapping": 26,
      "direction_net_outcome_auc": 0.5503,
      "boost_brier": 0.23162,
      "prior_win_rate_brier": 0.22811,
      "accepted_isolated_positive_pct": 38.462,
      "all_event_isolated_positive_pct": 34.934,
      "adequate_evidence": false,
      "discriminative_and_calibrated": false,
      "positive_selector_advantage": false
    },
    "2026JanOct": {
      "evidence_sample_size": 331,
      "accepted_nonoverlapping": 18,
      "direction_net_outcome_auc": 0.5247,
      "boost_brier": 0.22906,
      "prior_win_rate_brier": 0.22644,
      "accepted_isolated_positive_pct": 33.333,
      "all_event_isolated_positive_pct": 34.441,
      "adequate_evidence": false,
      "discriminative_and_calibrated": false,
      "positive_selector_advantage": false
    }
  },
  "reference_all_events_net_pct": -60.1432,
  "selected_trade_count": 140,
  "training_event_labels": 3187,
  "why": "Past-only, economically matched 1M first-touch labels were available and audited, but forecasting failed calendar-year discrimination / calibration / year sample and profit gates. Refuse all live directional trading."
}
~~~

## Required before enabling any future model
Repeatedly exceed prior-only forecast quality and sampled conditional hit rate on each chronological year, have enough accepted trades in every evaluated year, demonstrate positive net return / PF on conservative 1M exclusive-position replay, secure independent unresearched forward sample, and reconstruct actual funding / spreads / margin feasibility. This gate authorizes neither real-money trading nor strategy merging.

All results are for research only. No claim is made that the probability of BTC price rising or falling can be predicted reliably from these observed data.
