# BTC next-4H predictive market-state model: monthly walk-forward 1M backtest

## Objective
Measure whether a monthly past-only logistic model can improve prediction of whether BTC moves up > 1 ATR, down >1 ATR, or neither in the NEXT 4H, beyond training-prior majority and climatology controls. Trade only the frozen >=0.55 high-confidence directional predictions. The 22-month research target remains positive net performance in every complete month.

## Data quality, causal features and limits
~~~json
{
  "data": "BTCUSD 1M Delta India, SHA and minute continuity verified",
  "native_minutes": 992160,
  "expected_minutes": 992160,
  "source_partitions": 23,
  "hourly_bars": 16536,
  "features_known_at_1H_close": true,
  "monthly_training_only_available_released_labels": true,
  "first_replayed_month": "2025-07",
  "initial_training_only_months": [
    "2025-01",
    "2025-02",
    "2025-03",
    "2025-04",
    "2025-05",
    "2025-06"
  ],
  "target": "forward 4H close difference / ATR14 at signal close; UP >1, DOWN <-1, else RANGE",
  "model": "fixed L2 logistic regression with StandardScaler, C=1, max_iter=500, past-only fit",
  "signal_threshold": "prob_up/down >=0.55 AND 0.15 margin over both other classes",
  "fees": "taker 0.05% each side plus GST 18%",
  "assumed_slippage_price_points_each_side": 5.0,
  "historical_spreads_real_funding_liquidation_missing": true,
  "truly_blind_external_holdout": false
}
~~~

UTC 1H bar must be completed before features are used. Target released only after four later complete hours: monthly training excludes the last 5h label embargo. StandardScaler and logistic model are fit separately on only training rows prior to month start. 2025 Jan-Jun training only; 2026 has already been researched globally and is NOT a pristine unseen independent holdout.

## Directional prediction vs past-only baselines (non-overlapping 4H origins)
| period       |   scored_nonoverlapping_4h_hours |   model_accuracy_pct |   train_majority_accuracy_pct |   model_macro_f1 |   train_majority_macro_f1 |   model_logloss |   train_climatology_logloss |   model_confident_direction_signal_hours |
|:-------------|---------------------------------:|---------------------:|------------------------------:|-----------------:|--------------------------:|----------------:|----------------------------:|-----------------------------------------:|
| 2025-Jul-Dec |                             1104 |               64.493 |                        64.493 |           0.2653 |                    0.2614 |         0.88746 |                     0.89716 |                                        0 |
| 2026-Jan-Oct |                             1824 |               64.529 |                        64.638 |           0.2658 |                    0.2617 |         0.88212 |                     0.89518 |                                        0 |
| combined     |                             2928 |               64.515 |                        64.583 |           0.2655 |                    0.2616 |         0.88414 |                     0.89592 |                                        0 |

## Frozen directional strategy account summary
~~~json
{
  "trades": 2,
  "win_rate_pct": 0.0,
  "net_return_pct": -1.1429,
  "net_profit_usd": -114.29,
  "ending_equity_usd": 9885.71,
  "profit_factor": 0.0,
  "max_trade_close_drawdown_pct": 1.143,
  "profitable_months": 0,
  "losing_months": 2,
  "idle_months": 20,
  "evaluation_profitable_months": 0,
  "fee_gst_usd": 13.57,
  "slippage_usd": 1.02,
  "passes_22_positive_months": false
}
~~~

## All 22 monthly actual account net returns
| month_ist   |   trades |   wins |   losses |   net_return_pct |   pnl_usd |   fee_gst_usd |   slippage_usd |   end_equity_usd | status   |
|:------------|---------:|-------:|---------:|-----------------:|----------:|--------------:|---------------:|-----------------:|:---------|
| 2025-01     |        0 |      0 |        0 |          0       |      0    |          0    |           0    |         10000    | No trade |
| 2025-02     |        0 |      0 |        0 |          0       |      0    |          0    |           0    |         10000    | No trade |
| 2025-03     |        0 |      0 |        0 |          0       |      0    |          0    |           0    |         10000    | No trade |
| 2025-04     |        0 |      0 |        0 |          0       |      0    |          0    |           0    |         10000    | No trade |
| 2025-05     |        0 |      0 |        0 |          0       |      0    |          0    |           0    |         10000    | No trade |
| 2025-06     |        0 |      0 |        0 |          0       |      0    |          0    |           0    |         10000    | No trade |
| 2025-07     |        0 |      0 |        0 |          0       |      0    |          0    |           0    |         10000    | No trade |
| 2025-08     |        1 |      0 |        1 |         -0.61027 |    -61.03 |         10.25 |           0.77 |          9938.97 | Loss     |
| 2025-09     |        0 |      0 |        0 |          0       |      0    |          0    |           0    |          9938.97 | No trade |
| 2025-10     |        1 |      0 |        1 |         -0.53593 |    -53.27 |          3.32 |           0.25 |          9885.71 | Loss     |
| 2025-11     |        0 |      0 |        0 |          0       |      0    |          0    |           0    |          9885.71 | No trade |
| 2025-12     |        0 |      0 |        0 |          0       |      0    |          0    |           0    |          9885.71 | No trade |
| 2026-01     |        0 |      0 |        0 |          0       |      0    |          0    |           0    |          9885.71 | No trade |
| 2026-02     |        0 |      0 |        0 |          0       |      0    |          0    |           0    |          9885.71 | No trade |
| 2026-03     |        0 |      0 |        0 |          0       |      0    |          0    |           0    |          9885.71 | No trade |
| 2026-04     |        0 |      0 |        0 |          0       |      0    |          0    |           0    |          9885.71 | No trade |
| 2026-05     |        0 |      0 |        0 |          0       |      0    |          0    |           0    |          9885.71 | No trade |
| 2026-06     |        0 |      0 |        0 |          0       |      0    |          0    |           0    |          9885.71 | No trade |
| 2026-07     |        0 |      0 |        0 |          0       |      0    |          0    |           0    |          9885.71 | No trade |
| 2026-08     |        0 |      0 |        0 |          0       |      0    |          0    |           0    |          9885.71 | No trade |
| 2026-09     |        0 |      0 |        0 |          0       |      0    |          0    |           0    |          9885.71 | No trade |
| 2026-10     |        0 |      0 |        0 |          0       |      0    |          0    |           0    |          9885.71 | No trade |

## Before live use
- Prediction accuracy is not necessarily trading profitability. Confidence thresholds were fixed before backtest; not tuned to results.
- STOP=1 ATR14, TP=2R, 4H max hold, entry next native 1M open, stop-before-target same minute, IST month-end flatten, 0.5% stop-risk and 3x notional cap.
- Simulated taker 0.05% each side +18% GST and $5 price-point slip each side. Real spreads, funding, realized settlements, liquidation, contract quantities and depth unavailable.
- Win rate / drawdown samples on closed trades do NOT guarantee live fills or investor safety.
- Historical backtest selection context is already researched; prospective paper trading is needed to validate any positive score.
