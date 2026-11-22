# Two BTC ST Touch+Flip variants with 17/22 profitable months

Historical exploratory candidates: 2026 outcomes were viewed during
hypothesis selection. This confirms exact replay parity, NOT OOS.
Only entry filters change; fees, original ST closing exit and
conservative 1m fixed % stops/targets remain unchanged.

## Yearly trades, profit factor, max drawdown and win months
| name                        |   total_trades |   total_net_pts |   closed_equity_max_drawdown_pts |   2025_full_net |   2025_full_win_months |   2025_full_loss_months |   2025_full_trades |   2025_full_win_trades |   2025_full_pf |   2026_JanOct_net |   2026_JanOct_win_months |   2026_JanOct_loss_months |   2026_JanOct_trades |   2026_JanOct_win_trades |   2026_JanOct_pf |   2026_H1_net |   2026_JulOct_net |
|:----------------------------|---------------:|----------------:|---------------------------------:|----------------:|-----------------------:|------------------------:|-------------------:|-----------------------:|---------------:|------------------:|-------------------------:|--------------------------:|---------------------:|-------------------------:|-----------------:|--------------:|------------------:|
| baseline                    |            143 |         10608.6 |                          5192.53 |        10060.4  |                      8 |                       4 |                 76 |                     40 |          1.502 |            548.16 |                        5 |                         5 |                   67 |                       27 |            1.031 |      -1724.99 |           2273.15 |
| touch_1h_bull_di_4h_ema20   |             99 |         12457   |                          5218.08 |         8176.19 |                      9 |                       3 |                 55 |                     33 |          1.599 |           4280.81 |                        8 |                         2 |                   44 |                       22 |            1.44  |       2141.45 |           2139.36 |
| touch_1h_4h_above_ema20     |            100 |         13447.5 |                          4958.07 |         9560.31 |                      9 |                       3 |                 55 |                     34 |          1.706 |           3887.15 |                        8 |                         2 |                   45 |                       22 |            1.377 |       1739.11 |           2148.04 |
| both_1h_above_ema20         |             85 |         17122.7 |                          2454.89 |        13323    |                      9 |                       3 |                 42 |                     24 |          2.504 |           3799.7  |                        7 |                         3 |                   43 |                       19 |            1.366 |       1979.39 |           1820.32 |
| both_1h_above_ema50         |             82 |         15423.4 |                          2467.86 |        11075.6  |                      9 |                       3 |                 40 |                     21 |          2.213 |           4347.83 |                        7 |                         3 |                   42 |                       18 |            1.425 |       2733.19 |           1614.64 |
| both_1h_above_ema20_weekday |             77 |         17379.6 |                          2743.96 |        14763.7  |                      9 |                       3 |                 39 |                     24 |          2.99  |           2615.88 |                        7 |                         3 |                   38 |                       17 |            1.274 |        527.54 |           2088.34 |

## Top consistency setup: 1H DMI direction + 4H EMA20 for TOUCH only
For Line Touch, require +DI > -DI on the last completed 1H
candle AND close above EMA20 on the last completed 4H candle.
Bullish Flip (3% SL/0.5% TP) retains existing low-volume criteria.

| month_ist   |   newly_entered_trades |   realized_closed_trades |   exit_month_realized_net_pts |   month_end_equity_mtm_pts |
|:------------|-----------------------:|-------------------------:|------------------------------:|---------------------------:|
| 2025-01     |                      8 |                        8 |                      -1563.8  |                   -1563.8  |
| 2025-02     |                      4 |                        4 |                      -2184.96 |                   -3748.76 |
| 2025-03     |                      4 |                        4 |                       2384.66 |                   -1364.09 |
| 2025-04     |                      3 |                        3 |                        921.67 |                    -442.42 |
| 2025-05     |                      7 |                        7 |                       2372.76 |                    1930.33 |
| 2025-06     |                      3 |                        3 |                        500.5  |                    2430.83 |
| 2025-07     |                      5 |                        5 |                       1756.75 |                    4187.59 |
| 2025-08     |                      4 |                        4 |                      -1659.07 |                    2528.51 |
| 2025-09     |                      6 |                        6 |                        394.49 |                    2923.01 |
| 2025-10     |                      4 |                        4 |                       4179.57 |                    7102.57 |
| 2025-11     |                      4 |                        4 |                       1032.99 |                    8135.57 |
| 2025-12     |                      3 |                        3 |                         40.63 |                    8176.19 |
| 2026-01     |                      5 |                        5 |                       1177.83 |                    9354.02 |
| 2026-02     |                      5 |                        5 |                       1575.52 |                   10929.5  |
| 2026-03     |                      6 |                        6 |                       -986.5  |                    9943.04 |
| 2026-04     |                      2 |                        2 |                        517.8  |                   10460.8  |
| 2026-05     |                      3 |                        3 |                         11    |                   10471.8  |
| 2026-06     |                      4 |                        4 |                       -154.2  |                   10317.6  |
| 2026-07     |                      4 |                        4 |                        205.03 |                   10522.7  |
| 2026-08     |                      5 |                        5 |                       1422.57 |                   11945.2  |
| 2026-09     |                      8 |                        8 |                        380.26 |                   12325.5  |
| 2026-10     |                      2 |                        2 |                        131.49 |                   12457    |

## Negative months remaining in top consistency configuration
| month_ist   |   exit_month_realized_net_pts |   newly_entered_trades |
|:------------|------------------------------:|-----------------------:|
| 2025-01     |                      -1563.8  |                      8 |
| 2025-02     |                      -2184.96 |                      4 |
| 2025-08     |                      -1659.07 |                      4 |
| 2026-03     |                       -986.5  |                      6 |
| 2026-06     |                       -154.2  |                      4 |

## Risk warnings
- BTC point profit is 1 BTC equivalent, not account ROI.
- Estimated 0.05% taker each side, 18% GST and 5 point slip each side.
- ST close and minute stops are honored; no leverage/funding/liquidation.
- 121 related filter tests increase the chance of hindsight overfit.
- Genuine validation requires forward paper trading on unseen data.
