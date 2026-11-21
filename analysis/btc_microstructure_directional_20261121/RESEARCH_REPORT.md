# BTC 4H direction model repair — separate sign from expansion / range

## Fixed additional institutional inputs
Previous 3-class predictor achieved 64.515% accuracy versus 64.583% training-majority baseline mainly by predicting the dominant RANGE class. This separate experiment adds causally aligned open-interest, funding-rate observation and futures/mark-price basis features to the frozen directional model; these are NOT settled funding and NOT live order-book data. This study forecasts next-4H **UP versus DOWN explicitly** and **>=1 ATR movement probability separately**, with fixed two model families and no test-period hyperparameter sweeps. A market label cannot be objectively declared correct absent independently labeled regimes; we measure future directional skill only.

## Training, data and execution audit
~~~json
{
  "source": "Delta India BTCUSD native 1M plus MARK 1M, OI 5M, FUNDING 1H rate",
  "native_minutes": 992160,
  "partitions": 23,
  "extra_market_data": [
    "MARK:BTCUSD 1M",
    "OI:BTCUSD 5M",
    "FUNDING:BTCUSD 1H rate proxy"
  ],
  "extra_sources_known_after_complete_1H_close": true,
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
|         52.899 |                  52.841 |   0.5574 |   0.24761 |   0.68833 | 2025H2     | boosted             | 1104 |           50.45 |                99 |                         63.64 |                                58 |
|         54.801 |                  54.773 |   0.5624 |   0.24747 |   0.68816 | 2025H2     | logistic            | 1104 |           50.45 |               128 |                         60.16 |                               nan |
|         50.453 |                  50     |   0.4894 |   0.25005 |   0.69325 | 2025H2     | training_prior      | 1104 |           50.45 |                 0 |                        nan    |                               nan |
|         49.004 |                  49     | nan      | nan       | nan       | 2025H2     | previous4h_momentum | 1104 |           50.45 |               nan |                        nan    |                               nan |
|         49.342 |                  49.332 |   0.489  |   0.25408 |   0.70148 | 2026JanOct | boosted             | 1824 |           50.16 |                70 |                         47.14 |                                36 |
|         48.739 |                  48.72  |   0.4853 |   0.25339 |   0.69995 | 2026JanOct | logistic            | 1824 |           50.16 |                25 |                         64    |                               nan |
|         49.945 |                  49.814 |   0.4918 |   0.25003 |   0.6932  | 2026JanOct | training_prior      | 1824 |           50.16 |                 0 |                        nan    |                               nan |
|         47.094 |                  47.094 | nan      | nan       | nan       | 2026JanOct | previous4h_momentum | 1824 |           50.16 |               nan |                        nan    |                               nan |
|         50.683 |                  50.659 |   0.5167 |   0.25164 |   0.69652 | overall    | boosted             | 2928 |           50.27 |               169 |                         56.8  |                                94 |
|         51.025 |                  50.998 |   0.5184 |   0.25116 |   0.69551 | overall    | logistic            | 2928 |           50.27 |               153 |                         60.78 |                               nan |
|         50.137 |                  49.898 |   0.4951 |   0.25004 |   0.69322 | overall    | training_prior      | 2928 |           50.27 |                 0 |                        nan    |                               nan |
|         47.814 |                  47.813 | nan      | nan       | nan       | overall    | previous4h_momentum | 2928 |           50.27 |               nan |                        nan    |                               nan |

## Frozen boosted directional trade rule, independently 1M replayed
Stop 1x ATR14, TP 2R, max hold 4H, high-confidence p(up)>=.62 or <=.38 AND p(move)>=.35; no force trading. Next 1M open after closed 1H, same-minute stop before target, 0.5% current equity stop risk, max 3x notional, IST month-end flatten, taker 0.05% per side plus 18% GST and 5 BTCUSD points adverse slippage per leg.
~~~json
{
  "trades": 234,
  "wins": 87,
  "win_rate_pct": 37.179,
  "profitable_months": 3,
  "losing_months": 13,
  "no_trade_months": 6,
  "account_net_return_pct": -33.5052,
  "account_net_usd": -3350.52,
  "profit_factor": 0.4767,
  "max_trade_close_drawdown_pct": 34.566,
  "fees_gst_usd": 2257.38,
  "slippage_usd": 191.77,
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
| 2025-07     |       39 |     16 |       23 |          -5.59678 |          -559.68 |        616.77 |          46.02 | Loss     |
| 2025-08     |       41 |     16 |       25 |          -7.83176 |          -739.34 |        446.83 |          33.11 | Loss     |
| 2025-09     |       18 |      6 |       12 |          -3.86214 |          -336.04 |        260.91 |          19.54 | Loss     |
| 2025-10     |       28 |     13 |       15 |          -2.22442 |          -186.07 |        205.15 |          15.29 | Loss     |
| 2025-11     |       16 |      5 |       11 |          -3.15264 |          -257.85 |         92.39 |           8.13 | Loss     |
| 2025-12     |       10 |      3 |        7 |          -1.72138 |          -136.35 |         68.63 |           6.53 | Loss     |
| 2026-01     |       20 |      7 |       13 |          -4.69112 |          -365.19 |        206.43 |          19.43 | Loss     |
| 2026-02     |       17 |      5 |       12 |          -3.83486 |          -284.53 |         57.27 |           7.07 | Loss     |
| 2026-03     |       11 |      4 |        7 |          -1.98693 |          -141.77 |         64.7  |           7.88 | Loss     |
| 2026-04     |        5 |      2 |        3 |           0.10864 |             7.6  |         37.13 |           4.14 | Profit   |
| 2026-05     |        2 |      1 |        1 |          -0.20225 |           -14.16 |         16.1  |           1.78 | Loss     |
| 2026-06     |       15 |      3 |       12 |          -5.35875 |          -374.4  |         84.86 |          10.94 | Loss     |
| 2026-07     |        6 |      2 |        4 |          -0.09438 |            -6.24 |         53.72 |           7.02 | Loss     |
| 2026-08     |        1 |      1 |        0 |           0.37203 |            24.58 |          5.86 |           0.65 | Profit   |
| 2026-09     |        2 |      0 |        2 |          -1.31426 |           -87.14 |         19.07 |           1.96 | Loss     |
| 2026-10     |        3 |      3 |        0 |           1.62087 |           106.06 |         21.56 |           2.27 | Profit   |

## Additional files
hourly_forecast_ledger.csv, directional_score.csv, expansion_probability_score.csv, monthly_training_audit.csv, direction_calibration.csv, three confusion matrices, large_move_ex_post_diagnostic.csv, monthly_account_net.csv and boosted_trades.csv.

## Disqualifiers and cautions
- A meaningful predictive system must outperform strong chronological baselines in direction and probability scores, and demonstrate positive independent after-cost expectancy. A code repair does not guarantee such an edge.
- Large-move-only future diagnostic uses ex-post realized future movement; it is NOT a tradable condition.
- This simulation omits historical order-book bid/ask spreads, realized funding settlements, latency, exchange contract granularity and liquidation/margin rules. Not live-ready.
- Static thresholds and model families were predeclared BEFORE this run. Never pick the best model or tweak threshold using the same tested months and call it independently validated.
- Drawdown is measured at trade closes, not intratrade margin extremes.
