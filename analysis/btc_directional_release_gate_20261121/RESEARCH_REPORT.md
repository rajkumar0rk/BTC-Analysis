# BTC directional predictor deployment gate — FAIL CLOSED

## Decision
The trading selector must NOT treat either tested directional model as validated or enable orders. Two preregistered predictor families were independently evaluated on chronological months, and simple prior/momentum controls were measured. **Correcting the label-imbalance bug does not automatically create predictive edge.** No training or model selection occurs in this gate.

## What passes and fails
{
  "price_only": {
    "direction_prediction_evidence_passed": false,
    "historical_backtest_economics_passed": false,
    "directional_strategy_promotion_allowed": false,
    "directional_strategy_trading_enabled": false,
    "causality_test_completed": true,
    "external_blind_holdout_available": false,
    "observed_2025_2026_periods_previously_explored": true,
    "volatility_probability_candidate_for_new_research": true,
    "volatility_probability_live_trade_allowed": false,
    "goal_22_profitable_months_met": false,
    "net_trade_return_pct": -32.9615,
    "profitable_months": 2,
    "why_failed": "No durable 2025H2+2026 directional skill with positive after-cost PnL; all year-specific safety gates required, plus new untouched data before enabling trading."
  },
  "oi_mark_funding": {
    "direction_prediction_evidence_passed": false,
    "historical_backtest_economics_passed": false,
    "directional_strategy_promotion_allowed": false,
    "directional_strategy_trading_enabled": false,
    "causality_test_completed": true,
    "external_blind_holdout_available": false,
    "observed_2025_2026_periods_previously_explored": true,
    "volatility_probability_candidate_for_new_research": true,
    "volatility_probability_live_trade_allowed": false,
    "goal_22_profitable_months_met": false,
    "net_trade_return_pct": -33.5052,
    "profitable_months": 3,
    "why_failed": "No durable 2025H2+2026 directional skill with positive after-cost PnL; all year-specific safety gates required, plus new untouched data before enabling trading."
  }
}

## Correctly scored by calendar year, genuine future UP-v-DOWN instead of majority RANGE
| source          |   year | model   |    n |   directional_accuracy_pct |   training_prior_accuracy_pct |   direction_accuracy_advantage_pp |   accuracy_advantage_utc_day_bootstrap_ci_low_pp |   accuracy_advantage_utc_day_bootstrap_ci_high_pp |   directional_auc |   direction_brier |   training_prior_dir_brier |   expansion_auc |   expansion_brier |   expansion_prior_brier |   expansion_prevalence_pct |
|:----------------|-------:|:--------|-----:|---------------------------:|------------------------------:|----------------------------------:|-------------------------------------------------:|--------------------------------------------------:|------------------:|------------------:|---------------------------:|----------------:|------------------:|------------------------:|---------------------------:|
| price_only      |   2025 | boosted | 1104 |                     55.344 |                        50.453 |                             4.891 |                                            1.538 |                                             8.553 |           0.56416 |           0.24799 |                    0.25005 |         0.65622 |           0.21299 |                 0.22907 |                      35.51 |
| price_only      |   2026 | boosted | 1824 |                     49.616 |                        49.945 |                            -0.329 |                                           -3.29  |                                             2.522 |           0.49319 |           0.25396 |                    0.25003 |         0.67011 |           0.20967 |                 0.22861 |                      35.36 |
| oi_mark_funding |   2025 | boosted | 1104 |                     52.899 |                        50.453 |                             2.446 |                                           -1.27  |                                             6.097 |           0.55738 |           0.24761 |                    0.25005 |         0.65226 |           0.21391 |                 0.22907 |                      35.51 |
| oi_mark_funding |   2026 | boosted | 1824 |                     49.342 |                        49.945 |                            -0.603 |                                           -3.565 |                                             2.407 |           0.48901 |           0.25408 |                    0.25003 |         0.66325 |           0.21091 |                 0.22861 |                      35.36 |

## Model vs baseline comparisons (both linear and nonlinear)
| source          |   year | model    |    n |   directional_accuracy_pct |   training_prior_accuracy_pct |   direction_accuracy_advantage_pp |   accuracy_advantage_utc_day_bootstrap_ci_low_pp |   accuracy_advantage_utc_day_bootstrap_ci_high_pp |   directional_auc |   direction_brier |   training_prior_dir_brier |   expansion_auc |   expansion_brier |   expansion_prior_brier |   expansion_prevalence_pct |
|:----------------|-------:|:---------|-----:|---------------------------:|------------------------------:|----------------------------------:|-------------------------------------------------:|--------------------------------------------------:|------------------:|------------------:|---------------------------:|----------------:|------------------:|------------------------:|---------------------------:|
| price_only      |   2025 | boosted  | 1104 |                     55.344 |                        50.453 |                             4.891 |                                            1.538 |                                             8.553 |           0.56416 |           0.24799 |                    0.25005 |         0.65622 |           0.21299 |                 0.22907 |                      35.51 |
| price_only      |   2025 | logistic | 1104 |                     53.08  |                        50.453 |                             2.627 |                                           -0.544 |                                             5.973 |           0.55513 |           0.24787 |                    0.25005 |         0.60093 |           0.22315 |                 0.22907 |                      35.51 |
| price_only      |   2026 | boosted  | 1824 |                     49.616 |                        49.945 |                            -0.329 |                                           -3.29  |                                             2.522 |           0.49319 |           0.25396 |                    0.25003 |         0.67011 |           0.20967 |                 0.22861 |                      35.36 |
| price_only      |   2026 | logistic | 1824 |                     48.849 |                        49.945 |                            -1.096 |                                           -3.781 |                                             1.864 |           0.48223 |           0.25356 |                    0.25003 |         0.61636 |           0.22061 |                 0.22861 |                      35.36 |
| oi_mark_funding |   2025 | boosted  | 1104 |                     52.899 |                        50.453 |                             2.446 |                                           -1.27  |                                             6.097 |           0.55738 |           0.24761 |                    0.25005 |         0.65226 |           0.21391 |                 0.22907 |                      35.51 |
| oi_mark_funding |   2025 | logistic | 1104 |                     54.801 |                        50.453 |                             4.348 |                                            1.267 |                                             7.492 |           0.56242 |           0.24747 |                    0.25005 |         0.59992 |           0.2238  |                 0.22907 |                      35.51 |
| oi_mark_funding |   2026 | boosted  | 1824 |                     49.342 |                        49.945 |                            -0.603 |                                           -3.565 |                                             2.407 |           0.48901 |           0.25408 |                    0.25003 |         0.66325 |           0.21091 |                 0.22861 |                      35.36 |
| oi_mark_funding |   2026 | logistic | 1824 |                     48.739 |                        49.945 |                            -1.206 |                                           -3.919 |                                             1.859 |           0.48532 |           0.25339 |                    0.25003 |         0.61653 |           0.2206  |                 0.22861 |                      35.36 |

## Deployability rules
- No directional model can be promoted without both-year direction AUC >=0.55, >=2 point accuracy improvement vs past-only majority, directional Brier improvement >=0.005, paired day-bootstrap 95% lower bound >0, and independently profitable modeled trade PnL with PF >1.1.
- Even if these retrospective gates pass, a new untouched period with known true spread, realized funding settlement, fill and liquidation feasibility is REQUIRED. All models stay disabled for real money.
- Next-4H expansion probability is a potentially promising information source only if both years outperform historical expansion frequency; this is NOT proof of trade profitability or direction.
- No strategy is authorized to force an UP or DOWN trade because the market is currently trending; the fallback is NO_TRADE.
- Historical 2026 results already studied across the repo, so this is an analysis of previous observations, NOT a new blind holdout.
