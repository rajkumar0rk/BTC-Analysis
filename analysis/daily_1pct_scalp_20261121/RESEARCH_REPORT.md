# BTC daily 1% NET ACCOUNT scalp (research; not a guaranteed daily return)

## Predeclared settings

- BTCUSD Delta India 1m authentic candles; 15m triggers and completed 1h EMA confirmation.
- 2x notional leverage at each entry; one trade per IST day; 12:00-18:59 IST.
- Stop exactly -1% account NAV and TP exactly +1% account NAV after 0.05% taker/side, 18% GST and 5 USD/side slippage.
- 4h maximum hold or before day boundary, 1m stop-first OHLC execution.

## Summary per fixed setup

| model    |   capital_start_usd |   capital_end_usd |   net_compounded_return_pct |   max_trade_close_drawdown_pct |   trades |   profitable_trades |   losing_or_flat_trades | profit_factor_usd   |   days_in_sample |   positive_days |   negative_days |   no_trade_or_flat_days |   days_net_1pct_target_reached |   daily_target_hit_pct_all_days |   months_positive |   months_negative |   months_zero |   model_gross_usd |   total_fee_gst_usd |   total_slippage_usd |   year2025_return_pct |   year2026_JanOct_return_pct |
|:---------|--------------------:|------------------:|----------------------------:|-------------------------------:|---------:|--------------------:|------------------------:|:--------------------|-----------------:|----------------:|----------------:|------------------------:|-------------------------------:|--------------------------------:|------------------:|------------------:|--------------:|------------------:|--------------------:|---------------------:|----------------------:|-----------------------------:|
| trend    |               10000 |             10000 |                           0 |                              0 |        0 |                   0 |                       0 |                     |              669 |               0 |               0 |                     669 |                              0 |                               0 |                 0 |                 0 |            22 |                 0 |                   0 |                    0 |                     0 |                            0 |
| sweep    |               10000 |             10000 |                           0 |                              0 |        0 |                   0 |                       0 |                     |              669 |               0 |               0 |                     669 |                              0 |                               0 |                 0 |                 0 |            22 |                 0 |                   0 |                    0 |                     0 |                            0 |
| combined |               10000 |             10000 |                           0 |                              0 |        0 |                   0 |                       0 |                     |              669 |               0 |               0 |                     669 |                              0 |                               0 |                 0 |                 0 |            22 |                 0 |                   0 |                    0 |                     0 |                            0 |

## Every complete IST month

| model    | month_ist   |   trades |   target_1pct_days |   winning_days |   losing_days |   no_trade_or_flat_days |   monthly_return_pct |
|:---------|:------------|---------:|-------------------:|---------------:|--------------:|------------------------:|---------------------:|
| trend    | 2025-01     |        0 |                  0 |              0 |             0 |                      31 |                    0 |
| trend    | 2025-02     |        0 |                  0 |              0 |             0 |                      28 |                    0 |
| trend    | 2025-03     |        0 |                  0 |              0 |             0 |                      31 |                    0 |
| trend    | 2025-04     |        0 |                  0 |              0 |             0 |                      30 |                    0 |
| trend    | 2025-05     |        0 |                  0 |              0 |             0 |                      31 |                    0 |
| trend    | 2025-06     |        0 |                  0 |              0 |             0 |                      30 |                    0 |
| trend    | 2025-07     |        0 |                  0 |              0 |             0 |                      31 |                    0 |
| trend    | 2025-08     |        0 |                  0 |              0 |             0 |                      31 |                    0 |
| trend    | 2025-09     |        0 |                  0 |              0 |             0 |                      30 |                    0 |
| trend    | 2025-10     |        0 |                  0 |              0 |             0 |                      31 |                    0 |
| trend    | 2025-11     |        0 |                  0 |              0 |             0 |                      30 |                    0 |
| trend    | 2025-12     |        0 |                  0 |              0 |             0 |                      31 |                    0 |
| trend    | 2026-01     |        0 |                  0 |              0 |             0 |                      31 |                    0 |
| trend    | 2026-02     |        0 |                  0 |              0 |             0 |                      28 |                    0 |
| trend    | 2026-03     |        0 |                  0 |              0 |             0 |                      31 |                    0 |
| trend    | 2026-04     |        0 |                  0 |              0 |             0 |                      30 |                    0 |
| trend    | 2026-05     |        0 |                  0 |              0 |             0 |                      31 |                    0 |
| trend    | 2026-06     |        0 |                  0 |              0 |             0 |                      30 |                    0 |
| trend    | 2026-07     |        0 |                  0 |              0 |             0 |                      31 |                    0 |
| trend    | 2026-08     |        0 |                  0 |              0 |             0 |                      31 |                    0 |
| trend    | 2026-09     |        0 |                  0 |              0 |             0 |                      30 |                    0 |
| trend    | 2026-10     |        0 |                  0 |              0 |             0 |                      31 |                    0 |
| sweep    | 2025-01     |        0 |                  0 |              0 |             0 |                      31 |                    0 |
| sweep    | 2025-02     |        0 |                  0 |              0 |             0 |                      28 |                    0 |
| sweep    | 2025-03     |        0 |                  0 |              0 |             0 |                      31 |                    0 |
| sweep    | 2025-04     |        0 |                  0 |              0 |             0 |                      30 |                    0 |
| sweep    | 2025-05     |        0 |                  0 |              0 |             0 |                      31 |                    0 |
| sweep    | 2025-06     |        0 |                  0 |              0 |             0 |                      30 |                    0 |
| sweep    | 2025-07     |        0 |                  0 |              0 |             0 |                      31 |                    0 |
| sweep    | 2025-08     |        0 |                  0 |              0 |             0 |                      31 |                    0 |
| sweep    | 2025-09     |        0 |                  0 |              0 |             0 |                      30 |                    0 |
| sweep    | 2025-10     |        0 |                  0 |              0 |             0 |                      31 |                    0 |
| sweep    | 2025-11     |        0 |                  0 |              0 |             0 |                      30 |                    0 |
| sweep    | 2025-12     |        0 |                  0 |              0 |             0 |                      31 |                    0 |
| sweep    | 2026-01     |        0 |                  0 |              0 |             0 |                      31 |                    0 |
| sweep    | 2026-02     |        0 |                  0 |              0 |             0 |                      28 |                    0 |
| sweep    | 2026-03     |        0 |                  0 |              0 |             0 |                      31 |                    0 |
| sweep    | 2026-04     |        0 |                  0 |              0 |             0 |                      30 |                    0 |
| sweep    | 2026-05     |        0 |                  0 |              0 |             0 |                      31 |                    0 |
| sweep    | 2026-06     |        0 |                  0 |              0 |             0 |                      30 |                    0 |
| sweep    | 2026-07     |        0 |                  0 |              0 |             0 |                      31 |                    0 |
| sweep    | 2026-08     |        0 |                  0 |              0 |             0 |                      31 |                    0 |
| sweep    | 2026-09     |        0 |                  0 |              0 |             0 |                      30 |                    0 |
| sweep    | 2026-10     |        0 |                  0 |              0 |             0 |                      31 |                    0 |
| combined | 2025-01     |        0 |                  0 |              0 |             0 |                      31 |                    0 |
| combined | 2025-02     |        0 |                  0 |              0 |             0 |                      28 |                    0 |
| combined | 2025-03     |        0 |                  0 |              0 |             0 |                      31 |                    0 |
| combined | 2025-04     |        0 |                  0 |              0 |             0 |                      30 |                    0 |
| combined | 2025-05     |        0 |                  0 |              0 |             0 |                      31 |                    0 |
| combined | 2025-06     |        0 |                  0 |              0 |             0 |                      30 |                    0 |
| combined | 2025-07     |        0 |                  0 |              0 |             0 |                      31 |                    0 |
| combined | 2025-08     |        0 |                  0 |              0 |             0 |                      31 |                    0 |
| combined | 2025-09     |        0 |                  0 |              0 |             0 |                      30 |                    0 |
| combined | 2025-10     |        0 |                  0 |              0 |             0 |                      31 |                    0 |
| combined | 2025-11     |        0 |                  0 |              0 |             0 |                      30 |                    0 |
| combined | 2025-12     |        0 |                  0 |              0 |             0 |                      31 |                    0 |
| combined | 2026-01     |        0 |                  0 |              0 |             0 |                      31 |                    0 |
| combined | 2026-02     |        0 |                  0 |              0 |             0 |                      28 |                    0 |
| combined | 2026-03     |        0 |                  0 |              0 |             0 |                      31 |                    0 |
| combined | 2026-04     |        0 |                  0 |              0 |             0 |                      30 |                    0 |
| combined | 2026-05     |        0 |                  0 |              0 |             0 |                      31 |                    0 |
| combined | 2026-06     |        0 |                  0 |              0 |             0 |                      30 |                    0 |
| combined | 2026-07     |        0 |                  0 |              0 |             0 |                      31 |                    0 |
| combined | 2026-08     |        0 |                  0 |              0 |             0 |                      31 |                    0 |
| combined | 2026-09     |        0 |                  0 |              0 |             0 |                      30 |                    0 |
| combined | 2026-10     |        0 |                  0 |              0 |             0 |                      31 |                    0 |

## Limitations

- The goal is 1% net account profit on qualifying days, NOT guaranteed daily income
- At most one trade each IST day; no-trade days are failures of daily-profit goal
- 5 USD/side slippage is assumed, not actual bid/ask prices; funding unmodeled
- Original 1m source label convention must be independently verified on live Delta candles
- Both years were already studied on earlier research, so 2026 is not untouched validation
- No forward trading recommendation until paper audit and independent data are positive
