# BTC 4H direction model repair — separate sign from expansion / range

## Fix implemented
Previous 3-class predictor achieved 64.515% accuracy versus 64.583% training-majority baseline mainly by predicting the dominant RANGE class. This study forecasts next-4H **UP versus DOWN explicitly** and **>=1 ATR movement probability separately**, with fixed two model families and no test-period hyperparameter sweeps. A market label cannot be objectively declared correct absent independently labeled regimes; we measure future directional skill only.

## Training, data and execution audit
~~~json
{
  "source": "Delta India BTCUSD native 1M",
  "native_minutes": 992160,
  "partitions": 23,
  "complete_ist_months": 22,
  "training_only_months": 6,
  "evaluated_months": 16,
  "model_selection_on_test": false,
  "training_target_available_before_month": true,
  "no_lookahead_prefix_classifier_test": true,
  "direction_target": "sign(close[t+4]-close[t]) on completed 1H; future outcome release t+5h",
  "expansion_target": "abs(next4h move) >= ATR14 at signal hour",
  "signal": "boosted p(up)>=.62 or <=.38 and p(expansion)>=.35",
  "initial_equity_usd": 10000.0,
  "risk_fraction": 0.005,
  "max_leverage": 3.0,
  "maker_fee_assumed": false,
  "taker_fee_plus_gst_each_side": 0.00059,
  "adverse_slip_points_each_side": 5.0,
  "funding_settlement_spread_and_liquidation_missing": true,
  "all_histories_previously_explored": true,
  "external_blind_holdout": false
}
~~~

All feature hours are closed. Next4H label released only after four later fully closed 1H candles. Each IST month has its own model trained exclusively on prior-released labels; no same-month outcome used for that month's model. Jan-Jun 2025 initial training-only months; July 2025 to Oct 2026 tested by chronological month. 2026 history is previously researched; NOT a genuinely untouched holdout.

## 4H nonoverlapping directional forecasts vs last4H momentum and historical-prior baselines
|   accuracy_pct |   balanced_accuracy_pct |      auc |     brier |   logloss | period     | model               |    n |   actual_up_pct |   confident_hours |   confident_direction_hit_pct |   boosted_move_gated_signal_hours |
|---------------:|------------------------:|---------:|----------:|----------:|:-----------|:--------------------|-----:|----------------:|------------------:|------------------------------:|----------------------------------:|
|         55.344 |                  55.258 |   0.5642 |   0.24799 |   0.68921 | 2025H2     | boosted             | 1104 |           50.45 |               120 |                         57.5  |                                70 |
|         53.08  |                  53.017 |   0.5551 |   0.24787 |   0.68885 | 2025H2     | logistic            | 1104 |           50.45 |               100 |                         61    |                               nan |
|         50.453 |                  50     |   0.4894 |   0.25005 |   0.69325 | 2025H2     | training_prior      | 1104 |           50.45 |                 0 |                        nan    |                               nan |
|         49.004 |                  49     | nan      | nan       | nan       | 2025H2     | previous4h_momentum | 1104 |           50.45 |               nan |                        nan    |                               nan |
|         49.616 |                  49.607 |   0.4932 |   0.25396 |   0.70127 | 2026JanOct | boosted             | 1824 |           50.16 |                71 |                         43.66 |                                34 |
|         48.849 |                  48.831 |   0.4822 |   0.25356 |   0.70034 | 2026JanOct | logistic            | 1824 |           50.16 |                13 |                         38.46 |                               nan |
|         49.945 |                  49.814 |   0.4918 |   0.25003 |   0.6932  | 2026JanOct | training_prior      | 1824 |           50.16 |                 0 |                        nan    |                               nan |
|         47.094 |                  47.094 | nan      | nan       | nan       | 2026JanOct | previous4h_momentum | 1824 |           50.16 |               nan |                        nan    |                               nan |
|         51.776 |                  51.747 |   0.5217 |   0.25171 |   0.69672 | overall    | boosted             | 2928 |           50.27 |               191 |                         52.36 |                               104 |
|         50.444 |                  50.411 |   0.5129 |   0.25141 |   0.69601 | overall    | logistic            | 2928 |           50.27 |               113 |                         58.41 |                               nan |
|         50.137 |                  49.898 |   0.4951 |   0.25004 |   0.69322 | overall    | training_prior      | 2928 |           50.27 |                 0 |                        nan    |                               nan |
|         47.814 |                  47.813 | nan      | nan       | nan       | overall    | previous4h_momentum | 2928 |           50.27 |               nan |                        nan    |                               nan |

## Frozen boosted directional trade rule, independently 1M replayed
Stop 1x ATR14, TP 2R, max hold 4H, high-confidence p(up)>=.62 or <=.38 AND p(move)>=.35; no force trading. Next 1M open after closed 1H, same-minute stop before target, 0.5% current equity stop risk, max 3x notional, IST month-end flatten, taker 0.05% per side plus 18% GST and 5 BTCUSD points adverse slippage per leg.
~~~json
{
  "trades": 242,
  "wins": 93,
  "win_rate_pct": 38.43,
  "profitable_months": 2,
  "losing_months": 14,
  "no_trade_months": 6,
  "account_net_return_pct": -32.9615,
  "account_net_usd": -3296.15,
  "profit_factor": 0.4988,
  "max_trade_close_drawdown_pct": 34.262,
  "fees_gst_usd": 2259.27,
  "slippage_usd": 193.8,
  "passes_22_22": false
}
~~~

## Every one of 22 months, net account performance
| month_ist   |   trades |   wins |   losses |   account_net_pct |   net_profit_usd |   fee_gst_usd |   slippage_usd | status   |
|:------------|---------:|-------:|---------:|------------------:|-----------------:|--------------:|---------------:|:---------|
| 2025-01     |        0 |      0 |        0 |           0       |             0    |          0    |           0    | No trade |
| 2025-02     |        0 |      0 |        0 |           0       |             0    |          0    |           0    | No trade |
| 2025-03     |        0 |      0 |        0 |           0       |             0    |          0    |           0    | No trade |
| 2025-04     |        0 |      0 |        0 |           0       |             0    |          0    |           0    | No trade |
| 2025-05     |        0 |      0 |        0 |           0       |             0    |          0    |           0    | No trade |
| 2025-06     |        0 |      0 |        0 |           0       |             0    |          0    |           0    | No trade |
| 2025-07     |       37 |     17 |       20 |          -4.91853 |          -491.85 |        593.04 |          44.25 | Loss     |
| 2025-08     |       35 |     14 |       21 |          -7.28785 |          -692.94 |        381.77 |          28.22 | Loss     |
| 2025-09     |       21 |      7 |       14 |          -4.06355 |          -358.21 |        291.87 |          22.03 | Loss     |
| 2025-10     |       34 |     16 |       18 |          -2.87674 |          -243.29 |        258.32 |          19.39 | Loss     |
| 2025-11     |       24 |      8 |       16 |          -2.72774 |          -224.05 |        129.47 |          11.6  | Loss     |
| 2025-12     |       10 |      2 |        8 |          -3.69222 |          -295    |         74.17 |           7.05 | Loss     |
| 2026-01     |       17 |      6 |       11 |          -3.37795 |          -259.92 |        136.8  |          12.91 | Loss     |
| 2026-02     |       21 |      8 |       13 |          -2.66778 |          -198.34 |         72.52 |           8.98 | Loss     |
| 2026-03     |        6 |      2 |        4 |          -1.29564 |           -93.76 |         39    |           4.82 | Loss     |
| 2026-04     |        5 |      1 |        4 |          -0.73806 |           -52.72 |         35.62 |           3.98 | Loss     |
| 2026-05     |        2 |      0 |        2 |          -0.8333  |           -59.08 |         15.32 |           1.71 | Loss     |
| 2026-06     |       14 |      4 |       10 |          -4.27445 |          -300.53 |         83.59 |          10.69 | Loss     |
| 2026-07     |        7 |      1 |        6 |          -2.15595 |          -145.1  |         59.12 |           7.76 | Loss     |
| 2026-08     |        3 |      3 |        0 |           1.15665 |            76.17 |         42.15 |           5.56 | Profit   |
| 2026-09     |        2 |      0 |        2 |          -1.31426 |           -87.55 |         19.16 |           1.97 | Loss     |
| 2026-10     |        4 |      4 |        0 |           1.97772 |           130.01 |         27.34 |           2.88 | Profit   |

## Additional files
hourly_forecast_ledger.csv, directional_score.csv, expansion_probability_score.csv, monthly_training_audit.csv, direction_calibration.csv, three confusion matrices, large_move_ex_post_diagnostic.csv, monthly_account_net.csv and boosted_trades.csv.

## Disqualifiers and cautions
- A meaningful predictive system must outperform strong chronological baselines in direction and probability scores, and demonstrate positive independent after-cost expectancy. A code repair does not guarantee such an edge.
- Large-move-only future diagnostic uses ex-post realized future movement; it is NOT a tradable condition.
- This simulation omits historical order-book bid/ask spreads, realized funding settlements, latency, exchange contract granularity and liquidation/margin rules. Not live-ready.
- Static thresholds and model families were predeclared BEFORE this run. Never pick the best model or tweak threshold using the same tested months and call it independently validated.
- Drawdown is measured at trade closes, not intratrade margin extremes.
