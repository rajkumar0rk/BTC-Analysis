# Stage 16 — Can regime switching improve consistency of monthly BTC returns?

## Definitions
Preserve original Stage14 pullback 3R model, replay from original Stage14
event snapshots and original full trade ledger. Reconciliation: {"original_trade_count": 91, "maximum_net_points_drift": 0.0}

Test fixed complementary entry families:
- Range-bound: 1H pullback reversal, confirmed sweep/failure
- Trending: inside-bar and retest breakout, trend pullback engulf, compression breakout
- Transition: market structure shift with high 1H+5M volume
- Rolling 90/180-day shadow performance gate: uses ONLY already-closed outcomes
- Optional monthly realized net-risk guard at -3R or +3R

All models: one exclusive position, structural stop, 2R or 3R, max 240 min.
Standard taker/GST/slippage included; monthly returns modeled at 0.5% risk per trade.
Monthly returns booked in IST EXIT month (not entry month); no-trade months are neutral.

## Best comparison with zero monthly lock
| profile                            |   trades |   active_months_2025 |   profitable_months_2025 |   net_R_2025 |   model_compounded_pct_2025 |   active_months_2026 |   profitable_months_2026 |   net_R_2026 |   model_compounded_pct_2026 |   max_trade_to_trade_drawdown_pct |
|:-----------------------------------|---------:|---------------------:|-------------------------:|-------------:|----------------------------:|---------------------:|-------------------------:|-------------:|----------------------------:|----------------------------------:|
| stage14_unchanged                  |       91 |                   10 |                        6 |       12.401 |                       6.241 |                    7 |                        4 |        8.026 |                       4.02  |                             3.267 |
| rolling_180day_selector            |       55 |                   11 |                        4 |        2.87  |                       1.337 |                    4 |                        1 |       -1.525 |                      -0.787 |                             3.452 |
| rolling_90day_selector             |       78 |                    8 |                        3 |        2.934 |                       1.379 |                    6 |                        1 |      -10.454 |                      -5.225 |                             7.857 |
| range_pullback_plus_trend_breakout |      624 |                   12 |                        2 |     -162.077 |                     -56.009 |                   11 |                        3 |      -47.76  |                     -21.948 |                            65.712 |
| risk_limited_regime_switch         |      287 |                   12 |                        1 |      -34.028 |                     -16.028 |                   11 |                        5 |       -8.108 |                      -4.398 |                            20.739 |
| range_pullback_plus_trend_pullback |      337 |                   12 |                        1 |      -86.25  |                     -35.372 |                   11 |                        2 |      -18.225 |                      -9.105 |                            41.913 |
| full_three_regime_switch           |     1262 |                   12 |                        0 |     -434     |                     -88.853 |                   11 |                        2 |     -158.32  |                     -55.432 |                            95.032 |
| range_sweep_plus_trend_compression |      961 |                   12 |                        0 |     -388.689 |                     -85.946 |                   11 |                        2 |     -109.284 |                     -42.745 |                            92.012 |

## All profiles including monthly risk guards
| profile                            | guard                    |   trades |   active_months_2025 |   profitable_months_2025 |   losing_months_2025 |   inactive_months_2025 |   net_R_2025 |   model_compounded_pct_2025 |   active_months_2026 |   profitable_months_2026 |   losing_months_2026 |   inactive_months_2026 |   net_R_2026 |   model_compounded_pct_2026 |   max_trade_to_trade_drawdown_pct |   modeled_total_return_pct | passed_research_gate   |   eligible_signals |   rejected_by_guard |   actual_trades |
|:-----------------------------------|:-------------------------|---------:|---------------------:|-------------------------:|---------------------:|-----------------------:|-------------:|----------------------------:|---------------------:|-------------------------:|---------------------:|-----------------------:|-------------:|----------------------------:|----------------------------------:|---------------------------:|:-----------------------|-------------------:|--------------------:|----------------:|
| full_three_regime_switch           | month_profit_lock_plus3R |      971 |                   12 |                        2 |                   10 |                      0 |     -395.728 |                     -86.453 |                   11 |                        4 |                    7 |                      0 |     -127.842 |                     -47.764 |                            92.924 |                    -92.924 | False                  |               2120 |                 501 |             971 |
| full_three_regime_switch           | month_stop_minus3R       |      198 |                   12 |                        0 |                   12 |                      0 |      -46.377 |                     -20.825 |                   11 |                        1 |                   10 |                      0 |      -27.425 |                     -13.263 |                            31.326 |                    -31.326 | False                  |               2120 |                1778 |             198 |
| full_three_regime_switch           | no_guard                 |     1262 |                   12 |                        0 |                   12 |                      0 |     -434     |                     -88.853 |                   11 |                        2 |                    9 |                      0 |     -158.32  |                     -55.432 |                            95.032 |                    -95.032 | False                  |               2120 |                   0 |            1262 |
| range_pullback_plus_trend_breakout | month_profit_lock_plus3R |      369 |                   12 |                        6 |                    6 |                      0 |     -101.425 |                     -40.159 |                   11 |                        6 |                    5 |                      0 |      -36.766 |                     -17.237 |                            52.391 |                    -50.473 | False                  |                928 |                 362 |             369 |
| range_pullback_plus_trend_breakout | month_stop_minus3R       |      259 |                   12 |                        1 |                   11 |                      0 |      -37.889 |                     -17.521 |                   11 |                        3 |                    8 |                      0 |       -2.235 |                      -1.665 |                            19.433 |                    -18.894 | False                  |                928 |                 524 |             259 |
| range_pullback_plus_trend_breakout | no_guard                 |      624 |                   12 |                        2 |                   10 |                      0 |     -162.077 |                     -56.009 |                   11 |                        3 |                    8 |                      0 |      -47.76  |                     -21.948 |                            65.712 |                    -65.664 | False                  |                928 |                   0 |             624 |
| range_pullback_plus_trend_pullback | month_profit_lock_plus3R |      257 |                   12 |                        2 |                   10 |                      0 |      -80.662 |                     -33.477 |                   11 |                        3 |                    8 |                      0 |      -16.629 |                      -8.241 |                            39.323 |                    -38.959 | False                  |                476 |                 108 |             257 |
| range_pullback_plus_trend_pullback | month_stop_minus3R       |      210 |                   12 |                        0 |                   12 |                      0 |      -36.294 |                     -16.801 |                   11 |                        2 |                    9 |                      0 |       -9.81  |                      -5.148 |                            21.555 |                    -21.084 | False                  |                476 |                 176 |             210 |
| range_pullback_plus_trend_pullback | no_guard                 |      337 |                   12 |                        1 |                   11 |                      0 |      -86.25  |                     -35.372 |                   11 |                        2 |                    9 |                      0 |      -18.225 |                      -9.105 |                            41.913 |                    -41.257 | False                  |                476 |                   0 |             337 |
| range_sweep_plus_trend_compression | month_profit_lock_plus3R |      757 |                   12 |                        2 |                   10 |                      0 |     -344.498 |                     -82.432 |                   11 |                        4 |                    7 |                      0 |      -75.637 |                     -31.949 |                            88.132 |                    -88.045 | False                  |               1526 |                 325 |             757 |
| range_sweep_plus_trend_compression | month_stop_minus3R       |      183 |                   12 |                        0 |                   12 |                      0 |      -44.119 |                     -19.934 |                   11 |                        1 |                   10 |                      0 |      -29.612 |                     -14.128 |                            31.246 |                    -31.246 | False                  |               1526 |                1252 |             183 |
| range_sweep_plus_trend_compression | no_guard                 |      961 |                   12 |                        0 |                   12 |                      0 |     -388.689 |                     -85.946 |                   11 |                        2 |                    9 |                      0 |     -109.284 |                     -42.745 |                            92.012 |                    -91.954 | False                  |               1526 |                   0 |             961 |
| risk_limited_regime_switch         | month_profit_lock_plus3R |      199 |                   12 |                        4 |                    8 |                      0 |      -19.532 |                      -9.632 |                   11 |                        6 |                    5 |                      0 |       -1.977 |                      -1.241 |                            12.527 |                    -10.753 | False                  |                348 |                 107 |             199 |
| risk_limited_regime_switch         | month_stop_minus3R       |      181 |                   12 |                        1 |                   11 |                      0 |      -23.339 |                     -11.244 |                   11 |                        4 |                    7 |                      0 |       -6.417 |                      -3.474 |                            14.699 |                    -14.327 | False                  |                348 |                 128 |             181 |
| risk_limited_regime_switch         | no_guard                 |      287 |                   12 |                        1 |                   11 |                      0 |      -34.028 |                     -16.028 |                   11 |                        5 |                    6 |                      0 |       -8.108 |                      -4.398 |                            20.739 |                    -19.722 | False                  |                348 |                   0 |             287 |
| rolling_180day_selector            | month_profit_lock_plus3R |       44 |                   11 |                        5 |                    6 |                      1 |        4.906 |                       2.399 |                    4 |                        1 |                    3 |                      7 |       -1.525 |                      -0.787 |                             3.452 |                      1.593 | False                  |                 98 |                  20 |              44 |
| rolling_180day_selector            | month_stop_minus3R       |       55 |                   11 |                        4 |                    7 |                      1 |        2.87  |                       1.337 |                    4 |                        1 |                    3 |                      7 |       -1.525 |                      -0.787 |                             3.452 |                      0.539 | False                  |                 98 |                   0 |              55 |
| rolling_180day_selector            | no_guard                 |       55 |                   11 |                        4 |                    7 |                      1 |        2.87  |                       1.337 |                    4 |                        1 |                    3 |                      7 |       -1.525 |                      -0.787 |                             3.452 |                      0.539 | False                  |                 98 |                   0 |              55 |
| rolling_90day_selector             | month_profit_lock_plus3R |       67 |                    8 |                        4 |                    4 |                      4 |        4.969 |                       2.442 |                    6 |                        1 |                    5 |                      5 |      -10.454 |                      -5.225 |                             7.857 |                     -2.911 | False                  |                120 |                  20 |              67 |
| rolling_90day_selector             | month_stop_minus3R       |       75 |                    8 |                        3 |                    5 |                      4 |        2.934 |                       1.379 |                    6 |                        1 |                    5 |                      5 |       -6.227 |                      -3.193 |                             5.882 |                     -1.858 | False                  |                120 |                   3 |              75 |
| rolling_90day_selector             | no_guard                 |       78 |                    8 |                        3 |                    5 |                      4 |        2.934 |                       1.379 |                    6 |                        1 |                    5 |                      5 |      -10.454 |                      -5.225 |                             7.857 |                     -3.918 | False                  |                120 |                   0 |              78 |
| stage14_unchanged                  | month_profit_lock_plus3R |       70 |                   10 |                        8 |                    2 |                      2 |       18.903 |                       9.789 |                    7 |                        4 |                    3 |                      4 |        7.531 |                       3.763 |                             3.102 |                     13.921 | False                  |                161 |                  35 |              70 |
| stage14_unchanged                  | month_stop_minus3R       |       84 |                   10 |                        6 |                    4 |                      2 |        8.938 |                       4.427 |                    7 |                        4 |                    3 |                      4 |        8.026 |                       4.02  |                             3.784 |                      8.625 | False                  |                161 |                  14 |              84 |
| stage14_unchanged                  | no_guard                 |       91 |                   10 |                        6 |                    4 |                      2 |       12.401 |                       6.241 |                    7 |                        4 |                    3 |                      4 |        8.026 |                       4.02  |                             3.267 |                     10.512 | False                  |                161 |                   0 |              91 |

## Predeclared consistency gate
Require >=9 active 2025 and >=8 active 2026 months, at least 75%
of active months profitable each year, positive net R both years,
>=90 trades and >=15 during Jul–Oct 2026. Passing historical gate
would NOT establish deployability without new forward data.

Passing combinations: **0 / 24**
None passed.

## Monthly comparison of representative unguarded alternatives
| profile                            | guard    | month_ist   |   trades |    net_R |   modeled_equity_return_pct | status    |
|:-----------------------------------|:---------|:------------|---------:|---------:|----------------------------:|:----------|
| full_three_regime_switch           | no_guard | 2025-01     |       50 | -42.4505 |                    -19.2396 | Loss      |
| full_three_regime_switch           | no_guard | 2025-02     |       82 | -25.2614 |                    -12.0979 | Loss      |
| full_three_regime_switch           | no_guard | 2025-03     |       49 | -34.7409 |                    -16.0629 | Loss      |
| full_three_regime_switch           | no_guard | 2025-04     |       36 | -13.9381 |                     -6.8331 | Loss      |
| full_three_regime_switch           | no_guard | 2025-05     |       69 | -46.4983 |                    -20.9254 | Loss      |
| full_three_regime_switch           | no_guard | 2025-06     |       50 | -20.7676 |                    -10.0207 | Loss      |
| full_three_regime_switch           | no_guard | 2025-07     |       94 | -16.9508 |                     -8.4061 | Loss      |
| full_three_regime_switch           | no_guard | 2025-08     |       58 | -46.1775 |                    -20.7727 | Loss      |
| full_three_regime_switch           | no_guard | 2025-09     |       55 | -45.131  |                    -20.3393 | Loss      |
| full_three_regime_switch           | no_guard | 2025-10     |       86 | -55.5779 |                    -24.4747 | Loss      |
| full_three_regime_switch           | no_guard | 2025-11     |       63 | -26.7978 |                    -12.7156 | Loss      |
| full_three_regime_switch           | no_guard | 2025-12     |       72 | -59.7085 |                    -25.9447 | Loss      |
| full_three_regime_switch           | no_guard | 2026-01     |       62 | -26.7069 |                    -12.6692 | Loss      |
| full_three_regime_switch           | no_guard | 2026-02     |       74 |  13.401  |                      6.6127 | Profit    |
| full_three_regime_switch           | no_guard | 2026-03     |       64 | -17.9308 |                     -8.7654 | Loss      |
| full_three_regime_switch           | no_guard | 2026-04     |       51 | -28.307  |                    -13.3223 | Loss      |
| full_three_regime_switch           | no_guard | 2026-05     |       40 | -25.9572 |                    -12.2744 | Loss      |
| full_three_regime_switch           | no_guard | 2026-06     |       57 |  11.4645 |                      5.6357 | Profit    |
| full_three_regime_switch           | no_guard | 2026-07     |       24 | -11.472  |                     -5.6395 | Loss      |
| full_three_regime_switch           | no_guard | 2026-08     |       36 | -20.8063 |                     -9.9764 | Loss      |
| full_three_regime_switch           | no_guard | 2026-09     |       40 | -25.1944 |                    -11.9374 | Loss      |
| full_three_regime_switch           | no_guard | 2026-10     |       23 | -15.3011 |                     -7.4366 | Loss      |
| full_three_regime_switch           | no_guard | 2026-11     |       27 | -11.51   |                     -5.6668 | Loss      |
| range_pullback_plus_trend_breakout | no_guard | 2025-01     |       16 | -14.991  |                     -7.2705 | Loss      |
| range_pullback_plus_trend_breakout | no_guard | 2025-02     |       29 |   3.0217 |                      1.4198 | Profit    |
| range_pullback_plus_trend_breakout | no_guard | 2025-03     |       21 | -23.9225 |                    -11.311  | Loss      |
| range_pullback_plus_trend_breakout | no_guard | 2025-04     |       20 |   1.4641 |                      0.6684 | Profit    |
| range_pullback_plus_trend_breakout | no_guard | 2025-05     |       35 | -17.7937 |                     -8.6103 | Loss      |
| range_pullback_plus_trend_breakout | no_guard | 2025-06     |       22 |  -4.4445 |                     -2.2691 | Loss      |
| range_pullback_plus_trend_breakout | no_guard | 2025-07     |       34 |  -6.1354 |                     -3.1286 | Loss      |
| range_pullback_plus_trend_breakout | no_guard | 2025-08     |       39 | -30.7277 |                    -14.3508 | Loss      |
| range_pullback_plus_trend_breakout | no_guard | 2025-09     |       17 |  -8.4352 |                     -4.1686 | Loss      |
| range_pullback_plus_trend_breakout | no_guard | 2025-10     |       58 | -32.2003 |                    -15.0379 | Loss      |
| range_pullback_plus_trend_breakout | no_guard | 2025-11     |       40 | -15.3364 |                     -7.498  | Loss      |
| range_pullback_plus_trend_breakout | no_guard | 2025-12     |       19 | -12.5757 |                     -6.1296 | Loss      |
| range_pullback_plus_trend_breakout | no_guard | 2026-01     |       39 | -23.4606 |                    -11.1575 | Loss      |
| range_pullback_plus_trend_breakout | no_guard | 2026-02     |       44 |  12.6873 |                      6.3744 | Profit    |
| range_pullback_plus_trend_breakout | no_guard | 2026-03     |       22 |   4.9916 |                      2.4441 | Profit    |
| range_pullback_plus_trend_breakout | no_guard | 2026-04     |       26 | -13.1273 |                     -6.4143 | Loss      |
| range_pullback_plus_trend_breakout | no_guard | 2026-05     |       27 | -13.0203 |                     -6.3746 | Loss      |
| range_pullback_plus_trend_breakout | no_guard | 2026-06     |       40 |   6.0317 |                      2.8962 | Profit    |
| range_pullback_plus_trend_breakout | no_guard | 2026-07     |       13 |  -0.1677 |                     -0.1289 | Loss      |
| range_pullback_plus_trend_breakout | no_guard | 2026-08     |       21 | -10.4325 |                     -5.1496 | Loss      |
| range_pullback_plus_trend_breakout | no_guard | 2026-09     |       10 |  -4.9871 |                     -2.4829 | Loss      |
| range_pullback_plus_trend_breakout | no_guard | 2026-10     |       12 |  -2.5349 |                     -1.3068 | Loss      |
| range_pullback_plus_trend_breakout | no_guard | 2026-11     |       20 |  -3.7405 |                     -1.9175 | Loss      |
| range_sweep_plus_trend_compression | no_guard | 2025-01     |       43 | -37.8207 |                    -17.3305 | Loss      |
| range_sweep_plus_trend_compression | no_guard | 2025-02     |       73 | -36.0045 |                    -16.6517 | Loss      |
| range_sweep_plus_trend_compression | no_guard | 2025-03     |       34 | -22.5169 |                    -10.7438 | Loss      |
| range_sweep_plus_trend_compression | no_guard | 2025-04     |       29 | -10.5446 |                     -5.2201 | Loss      |
| range_sweep_plus_trend_compression | no_guard | 2025-05     |       47 | -31.6169 |                    -14.7729 | Loss      |
| range_sweep_plus_trend_compression | no_guard | 2025-06     |       36 | -21.3826 |                    -10.245  | Loss      |
| range_sweep_plus_trend_compression | no_guard | 2025-07     |       79 | -32.1609 |                    -15.0306 | Loss      |
| range_sweep_plus_trend_compression | no_guard | 2025-08     |       48 | -36.837  |                    -16.9495 | Loss      |
| range_sweep_plus_trend_compression | no_guard | 2025-09     |       56 | -63.1456 |                    -27.2015 | Loss      |
| range_sweep_plus_trend_compression | no_guard | 2025-10     |       66 | -42.4714 |                    -19.3176 | Loss      |
| range_sweep_plus_trend_compression | no_guard | 2025-11     |       37 |  -4.5619 |                     -2.3884 | Loss      |
| range_sweep_plus_trend_compression | no_guard | 2025-12     |       64 | -49.6262 |                    -22.0975 | Loss      |
| range_sweep_plus_trend_compression | no_guard | 2026-01     |       39 | -11.6472 |                     -5.7818 | Loss      |
| range_sweep_plus_trend_compression | no_guard | 2026-02     |       49 |   1.4152 |                      0.5142 | Profit    |
| range_sweep_plus_trend_compression | no_guard | 2026-03     |       58 | -16.5824 |                     -8.1154 | Loss      |
| range_sweep_plus_trend_compression | no_guard | 2026-04     |       38 | -16.9545 |                     -8.2156 | Loss      |
| range_sweep_plus_trend_compression | no_guard | 2026-05     |       24 | -19.6165 |                     -9.4032 | Loss      |
| range_sweep_plus_trend_compression | no_guard | 2026-06     |       40 |   7.1083 |                      3.4439 | Profit    |
| range_sweep_plus_trend_compression | no_guard | 2026-07     |       18 | -12.3667 |                     -6.0428 | Loss      |
| range_sweep_plus_trend_compression | no_guard | 2026-08     |       20 |  -9.976  |                     -4.9132 | Loss      |
| range_sweep_plus_trend_compression | no_guard | 2026-09     |       32 | -14.3742 |                     -7.0269 | Loss      |
| range_sweep_plus_trend_compression | no_guard | 2026-10     |       17 | -10.747  |                     -5.287  | Loss      |
| range_sweep_plus_trend_compression | no_guard | 2026-11     |       14 |  -5.5434 |                     -2.7692 | Loss      |
| rolling_90day_selector             | no_guard | 2025-01     |        2 |  -2.4808 |                     -1.2365 | Loss      |
| rolling_90day_selector             | no_guard | 2025-02     |        6 |  -2.5825 |                     -1.3001 | Loss      |
| rolling_90day_selector             | no_guard | 2025-03     |        2 |  -1.9141 |                     -0.9555 | Loss      |
| rolling_90day_selector             | no_guard | 2025-04     |        1 |   2.7866 |                      1.3933 | Profit    |
| rolling_90day_selector             | no_guard | 2025-05     |        2 |  -0.7376 |                     -0.3685 | Loss      |
| rolling_90day_selector             | no_guard | 2025-06     |        5 |   6.0958 |                      3.0735 | Profit    |
| rolling_90day_selector             | no_guard | 2025-07     |       15 |  -0.0741 |                     -0.0746 | Loss      |
| rolling_90day_selector             | no_guard | 2025-08     |        1 |   1.8403 |                      0.9201 | Profit    |
| rolling_90day_selector             | no_guard | 2025-09     |        0 |   0      |                      0      | No trades |
| rolling_90day_selector             | no_guard | 2025-10     |        0 |   0      |                      0      | No trades |
| rolling_90day_selector             | no_guard | 2025-11     |        0 |   0      |                      0      | No trades |
| rolling_90day_selector             | no_guard | 2025-12     |        0 |   0      |                      0      | No trades |
| rolling_90day_selector             | no_guard | 2026-01     |        0 |   0      |                      0      | No trades |
| rolling_90day_selector             | no_guard | 2026-02     |        0 |   0      |                      0      | No trades |
| rolling_90day_selector             | no_guard | 2026-03     |        4 |   5.0408 |                      2.5314 | Profit    |
| rolling_90day_selector             | no_guard | 2026-04     |        7 |  -0.8179 |                     -0.4208 | Loss      |
| rolling_90day_selector             | no_guard | 2026-05     |        2 |  -1.4299 |                     -0.7151 | Loss      |
| rolling_90day_selector             | no_guard | 2026-06     |       12 |  -3.0764 |                     -1.5713 | Loss      |
| rolling_90day_selector             | no_guard | 2026-07     |        3 |  -1.5562 |                     -0.7784 | Loss      |
| rolling_90day_selector             | no_guard | 2026-08     |       16 |  -8.6146 |                     -4.2681 | Loss      |
| rolling_90day_selector             | no_guard | 2026-09     |        0 |   0      |                      0      | No trades |
| rolling_90day_selector             | no_guard | 2026-10     |        0 |   0      |                      0      | No trades |
| rolling_90day_selector             | no_guard | 2026-11     |        0 |   0      |                      0      | No trades |
| stage14_unchanged                  | no_guard | 2025-01     |        0 |   0      |                      0      | No trades |
| stage14_unchanged                  | no_guard | 2025-02     |       12 |  -0.4966 |                     -0.2769 | Loss      |
| stage14_unchanged                  | no_guard | 2025-03     |        0 |   0      |                      0      | No trades |
| stage14_unchanged                  | no_guard | 2025-04     |        5 |   3.9654 |                      1.9856 | Profit    |
| stage14_unchanged                  | no_guard | 2025-05     |        2 |  -0.7376 |                     -0.3685 | Loss      |
| stage14_unchanged                  | no_guard | 2025-06     |        5 |   6.0958 |                      3.0735 | Profit    |
| stage14_unchanged                  | no_guard | 2025-07     |       15 |  -0.0741 |                     -0.0746 | Loss      |
| stage14_unchanged                  | no_guard | 2025-08     |        1 |   1.8403 |                      0.9201 | Profit    |
| stage14_unchanged                  | no_guard | 2025-09     |        4 |   0.7123 |                      0.3504 | Profit    |
| stage14_unchanged                  | no_guard | 2025-10     |        3 |   1.597  |                      0.7945 | Profit    |
| stage14_unchanged                  | no_guard | 2025-11     |        5 |   0.4514 |                      0.2182 | Profit    |
| stage14_unchanged                  | no_guard | 2025-12     |       11 |  -0.9532 |                     -0.4917 | Loss      |
| stage14_unchanged                  | no_guard | 2026-01     |        3 |  -0.4668 |                     -0.2394 | Loss      |
| stage14_unchanged                  | no_guard | 2026-02     |        7 |   4.8267 |                      2.4205 | Profit    |
| stage14_unchanged                  | no_guard | 2026-03     |        4 |   5.0408 |                      2.5314 | Profit    |
| stage14_unchanged                  | no_guard | 2026-04     |        7 |  -0.8179 |                     -0.4208 | Loss      |
| stage14_unchanged                  | no_guard | 2026-05     |        4 |   1.1663 |                      0.5763 | Profit    |
| stage14_unchanged                  | no_guard | 2026-06     |        2 |  -1.8191 |                     -0.9077 | Loss      |
| stage14_unchanged                  | no_guard | 2026-07     |        0 |   0      |                      0      | No trades |
| stage14_unchanged                  | no_guard | 2026-08     |        0 |   0      |                      0      | No trades |
| stage14_unchanged                  | no_guard | 2026-09     |        1 |   0.0961 |                      0.048  | Profit    |
| stage14_unchanged                  | no_guard | 2026-10     |        0 |   0      |                      0      | No trades |
| stage14_unchanged                  | no_guard | 2026-11     |        0 |   0      |                      0      | No trades |

## Limitations
- No historical 2026 month is an untouched test; all exposed by earlier stages
- Selection of specific market-regime portfolios is exploratory and may overfit
- Rolling shadow results become usable only after completion, but shadow trades can overlap
- Equity model assumes exact fractional risk sizing without margin limits or contract rounding
- No liquidation, capital/margin/funding cashflows or actual bid-ask depth modeled
- One source gap on 2026-10-31; November 2026 is partial
- A risk cap or monthly lock cannot guarantee profit every month
- Any no-trade months count separately, never as profitable
- 1m OHLC with stop-first fills, historical slippage assumed 5 price points per side
- Standard Delta BTC taker fees plus GST included through Stage11 net R

The original baseline is unchanged. Results include failures.
