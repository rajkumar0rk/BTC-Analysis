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
| range_pullback_plus_trend_pullback |      290 |                   12 |                        6 |      -29.449 |                     -14.114 |                   11 |                        6 |      -20.917 |                     -10.233 |                            24.775 |
| risk_limited_regime_switch         |      249 |                   12 |                        3 |      -21.865 |                     -10.685 |                   11 |                        5 |       -4.059 |                      -2.395 |                            15.432 |
| stage14_unchanged                  |       91 |                    7 |                        2 |       -0.981 |                      -0.571 |                    9 |                        4 |       -3.599 |                      -1.876 |                             5.146 |
| rolling_180day_selector            |       38 |                    6 |                        2 |       -0.884 |                      -0.477 |                    6 |                        1 |       -8.399 |                      -4.153 |                             5.53  |
| rolling_90day_selector             |      106 |                    8 |                        2 |      -12.994 |                      -6.357 |                    9 |                        1 |      -21.296 |                     -10.289 |                            16.801 |
| full_three_regime_switch           |     1398 |                   12 |                        2 |     -223.163 |                     -68.141 |                   11 |                        0 |     -166.545 |                     -57.226 |                            86.579 |
| range_sweep_plus_trend_compression |     1123 |                   12 |                        2 |     -247.826 |                     -71.638 |                   11 |                        0 |     -167.838 |                     -57.263 |                            88.087 |
| range_pullback_plus_trend_breakout |      612 |                   12 |                        1 |      -90.915 |                     -37.149 |                   11 |                        3 |      -44.704 |                     -20.718 |                            50.909 |

## All profiles including monthly risk guards
| profile                            | guard                    |   trades |   active_months_2025 |   profitable_months_2025 |   losing_months_2025 |   inactive_months_2025 |   net_R_2025 |   model_compounded_pct_2025 |   active_months_2026 |   profitable_months_2026 |   losing_months_2026 |   inactive_months_2026 |   net_R_2026 |   model_compounded_pct_2026 |   max_trade_to_trade_drawdown_pct |   modeled_total_return_pct | passed_research_gate   |   eligible_signals |   rejected_by_guard |   actual_trades |
|:-----------------------------------|:-------------------------|---------:|---------------------:|-------------------------:|---------------------:|-----------------------:|-------------:|----------------------------:|---------------------:|-------------------------:|---------------------:|-----------------------:|-------------:|----------------------------:|----------------------------------:|---------------------------:|:-----------------------|-------------------:|--------------------:|----------------:|
| full_three_regime_switch           | month_profit_lock_plus3R |     1050 |                   12 |                        3 |                    9 |                      0 |     -201.71  |                     -64.266 |                   11 |                        4 |                    7 |                      0 |     -115.725 |                     -44.602 |                            80.504 |                    -80.204 | False                  |               2283 |                 621 |            1050 |
| full_three_regime_switch           | month_stop_minus3R       |      255 |                   12 |                        1 |                   11 |                      0 |      -23.178 |                     -11.333 |                   11 |                        0 |                   11 |                      0 |      -36.386 |                     -16.931 |                            26.551 |                    -26.345 | False                  |               2283 |                1844 |             255 |
| full_three_regime_switch           | no_guard                 |     1398 |                   12 |                        2 |                   10 |                      0 |     -223.163 |                     -68.141 |                   11 |                        0 |                   11 |                      0 |     -166.545 |                     -57.226 |                            86.579 |                    -86.373 | False                  |               2283 |                   0 |            1398 |
| range_pullback_plus_trend_breakout | month_profit_lock_plus3R |      447 |                   12 |                        2 |                   10 |                      0 |      -90.544 |                     -36.911 |                   11 |                        5 |                    6 |                      0 |      -34.296 |                     -16.174 |                            47.899 |                    -47.115 | False                  |                858 |                 225 |             447 |
| range_pullback_plus_trend_breakout | month_stop_minus3R       |      277 |                   12 |                        1 |                   11 |                      0 |      -32.074 |                     -15.124 |                   11 |                        2 |                    9 |                      0 |      -23.256 |                     -11.419 |                            25.826 |                    -24.816 | False                  |                858 |                 473 |             277 |
| range_pullback_plus_trend_breakout | no_guard                 |      612 |                   12 |                        1 |                   11 |                      0 |      -90.915 |                     -37.149 |                   11 |                        3 |                    8 |                      0 |      -44.704 |                     -20.718 |                            50.909 |                    -50.17  | False                  |                858 |                   0 |             612 |
| range_pullback_plus_trend_pullback | month_profit_lock_plus3R |      248 |                   12 |                        6 |                    6 |                      0 |      -28.708 |                     -13.714 |                   11 |                        6 |                    5 |                      0 |      -14.177 |                      -7.134 |                            22.246 |                    -19.869 | False                  |                400 |                  62 |             248 |
| range_pullback_plus_trend_pullback | month_stop_minus3R       |      206 |                   12 |                        3 |                    9 |                      0 |      -15.873 |                      -7.927 |                   11 |                        6 |                    5 |                      0 |       -7.216 |                      -3.826 |                            13.6   |                    -11.45  | False                  |                400 |                 111 |             206 |
| range_pullback_plus_trend_pullback | no_guard                 |      290 |                   12 |                        6 |                    6 |                      0 |      -29.449 |                     -14.114 |                   11 |                        6 |                    5 |                      0 |      -20.917 |                     -10.233 |                            24.775 |                    -22.903 | False                  |                400 |                   0 |             290 |
| range_sweep_plus_trend_compression | month_profit_lock_plus3R |      894 |                   12 |                        4 |                    8 |                      0 |     -226.62  |                     -68.327 |                   11 |                        2 |                    9 |                      0 |     -140.69  |                     -50.953 |                            84.732 |                    -84.465 | False                  |               1836 |                 374 |             894 |
| range_sweep_plus_trend_compression | month_stop_minus3R       |      250 |                   12 |                        1 |                   11 |                      0 |      -34.59  |                     -16.295 |                   11 |                        0 |                   11 |                      0 |      -40.263 |                     -18.409 |                            31.704 |                    -31.704 | False                  |               1836 |                1414 |             250 |
| range_sweep_plus_trend_compression | no_guard                 |     1123 |                   12 |                        2 |                   10 |                      0 |     -247.826 |                     -71.638 |                   11 |                        0 |                   11 |                      0 |     -167.838 |                     -57.263 |                            88.087 |                    -87.879 | False                  |               1836 |                   0 |            1123 |
| risk_limited_regime_switch         | month_profit_lock_plus3R |      183 |                   12 |                        6 |                    6 |                      0 |       -0.902 |                      -0.727 |                   11 |                        5 |                    6 |                      0 |       -5.894 |                      -3.191 |                            13.631 |                     -3.895 | False                  |                294 |                  74 |             183 |
| risk_limited_regime_switch         | month_stop_minus3R       |      179 |                   12 |                        3 |                    9 |                      0 |      -14.003 |                      -7.023 |                   11 |                        3 |                    8 |                      0 |      -22.288 |                     -10.771 |                            18.383 |                    -17.038 | False                  |                294 |                  84 |             179 |
| risk_limited_regime_switch         | no_guard                 |      249 |                   12 |                        3 |                    9 |                      0 |      -21.865 |                     -10.685 |                   11 |                        5 |                    6 |                      0 |       -4.059 |                      -2.395 |                            15.432 |                    -12.824 | False                  |                294 |                   0 |             249 |
| rolling_180day_selector            | month_profit_lock_plus3R |       36 |                    6 |                        2 |                    4 |                      6 |       -0.884 |                      -0.477 |                    6 |                        1 |                    5 |                      5 |       -5.776 |                      -2.884 |                             4.278 |                     -3.347 | False                  |                 52 |                   2 |              36 |
| rolling_180day_selector            | month_stop_minus3R       |       34 |                    6 |                        2 |                    4 |                      6 |       -0.884 |                      -0.477 |                    6 |                        1 |                    5 |                      5 |       -6.229 |                      -3.102 |                             4.494 |                     -3.565 | False                  |                 52 |                   5 |              34 |
| rolling_180day_selector            | no_guard                 |       38 |                    6 |                        2 |                    4 |                      6 |       -0.884 |                      -0.477 |                    6 |                        1 |                    5 |                      5 |       -8.399 |                      -4.153 |                             5.53  |                     -4.611 | False                  |                 52 |                   0 |              38 |
| rolling_90day_selector             | month_profit_lock_plus3R |       78 |                    8 |                        2 |                    6 |                      4 |      -12.994 |                      -6.357 |                    9 |                        3 |                    6 |                      2 |       -9.961 |                      -4.975 |                            11.873 |                    -11.016 | False                  |                133 |                  34 |              78 |
| rolling_90day_selector             | month_stop_minus3R       |       93 |                    8 |                        2 |                    6 |                      4 |      -11.327 |                      -5.555 |                    9 |                        1 |                    8 |                      2 |      -19.814 |                      -9.6   |                            15.445 |                    -14.622 | False                  |                133 |                  14 |              93 |
| rolling_90day_selector             | no_guard                 |      106 |                    8 |                        2 |                    6 |                      4 |      -12.994 |                      -6.357 |                    9 |                        1 |                    8 |                      2 |      -21.296 |                     -10.289 |                            16.801 |                    -15.992 | False                  |                133 |                   0 |             106 |
| stage14_unchanged                  | month_profit_lock_plus3R |       89 |                    7 |                        2 |                    5 |                      5 |       -2.141 |                      -1.145 |                    9 |                        4 |                    5 |                      2 |       -3.599 |                      -1.876 |                             5.477 |                     -3     | False                  |                134 |                   2 |              89 |
| stage14_unchanged                  | month_stop_minus3R       |       83 |                    7 |                        2 |                    5 |                      5 |       -3.829 |                      -1.958 |                    9 |                        4 |                    5 |                      2 |       -1.316 |                      -0.745 |                             5.462 |                     -2.688 | False                  |                134 |                  12 |              83 |
| stage14_unchanged                  | no_guard                 |       91 |                    7 |                        2 |                    5 |                      5 |       -0.981 |                      -0.571 |                    9 |                        4 |                    5 |                      2 |       -3.599 |                      -1.876 |                             5.146 |                     -2.437 | False                  |                134 |                   0 |              91 |

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
| full_three_regime_switch           | no_guard | 2025-01     |       50 | -29.9147 |                    -14.0107 | Loss      |
| full_three_regime_switch           | no_guard | 2025-02     |       80 | -24.5612 |                    -11.8048 | Loss      |
| full_three_regime_switch           | no_guard | 2025-03     |       31 | -12.1815 |                     -5.9832 | Loss      |
| full_three_regime_switch           | no_guard | 2025-04     |       62 | -24.5434 |                    -11.7118 | Loss      |
| full_three_regime_switch           | no_guard | 2025-05     |       93 | -13.4949 |                     -6.8328 | Loss      |
| full_three_regime_switch           | no_guard | 2025-06     |       64 | -40.0474 |                    -18.2993 | Loss      |
| full_three_regime_switch           | no_guard | 2025-07     |       91 |  11.0119 |                      5.3101 | Profit    |
| full_three_regime_switch           | no_guard | 2025-08     |       91 | -28.7845 |                    -13.6705 | Loss      |
| full_three_regime_switch           | no_guard | 2025-09     |      101 | -39.3228 |                    -18.1608 | Loss      |
| full_three_regime_switch           | no_guard | 2025-10     |       58 | -21.6891 |                    -10.4507 | Loss      |
| full_three_regime_switch           | no_guard | 2025-11     |       46 |  17.976  |                      9.1834 | Profit    |
| full_three_regime_switch           | no_guard | 2025-12     |       69 | -17.6113 |                     -8.6024 | Loss      |
| full_three_regime_switch           | no_guard | 2026-01     |       60 |  -4.4656 |                     -2.4147 | Loss      |
| full_three_regime_switch           | no_guard | 2026-02     |       70 |  -0.6792 |                     -0.5808 | Loss      |
| full_three_regime_switch           | no_guard | 2026-03     |       80 | -22.0689 |                    -10.6714 | Loss      |
| full_three_regime_switch           | no_guard | 2026-04     |       59 | -10.4945 |                     -5.2709 | Loss      |
| full_three_regime_switch           | no_guard | 2026-05     |       53 | -35.2397 |                    -16.2715 | Loss      |
| full_three_regime_switch           | no_guard | 2026-06     |       48 |  -1.785  |                     -1.0311 | Loss      |
| full_three_regime_switch           | no_guard | 2026-07     |       43 | -19.4676 |                     -9.3656 | Loss      |
| full_three_regime_switch           | no_guard | 2026-08     |       43 | -13.2917 |                     -6.5199 | Loss      |
| full_three_regime_switch           | no_guard | 2026-09     |       46 | -26.9226 |                    -12.7045 | Loss      |
| full_three_regime_switch           | no_guard | 2026-10     |       32 | -20.4653 |                     -9.8145 | Loss      |
| full_three_regime_switch           | no_guard | 2026-11     |       28 | -11.6653 |                     -5.7373 | Loss      |
| range_pullback_plus_trend_breakout | no_guard | 2025-01     |       14 |  -8.2038 |                     -4.0477 | Loss      |
| range_pullback_plus_trend_breakout | no_guard | 2025-02     |       21 |  -6.8033 |                     -3.4023 | Loss      |
| range_pullback_plus_trend_breakout | no_guard | 2025-03     |       12 |  -6.1887 |                     -3.0699 | Loss      |
| range_pullback_plus_trend_breakout | no_guard | 2025-04     |       26 | -13.8257 |                     -6.7428 | Loss      |
| range_pullback_plus_trend_breakout | no_guard | 2025-05     |       21 |   7.7306 |                      3.8404 | Profit    |
| range_pullback_plus_trend_breakout | no_guard | 2025-06     |       27 | -11.8258 |                     -5.8024 | Loss      |
| range_pullback_plus_trend_breakout | no_guard | 2025-07     |       44 |  -0.5492 |                     -0.4133 | Loss      |
| range_pullback_plus_trend_breakout | no_guard | 2025-08     |       48 | -11.511  |                     -5.735  | Loss      |
| range_pullback_plus_trend_breakout | no_guard | 2025-09     |       37 | -16.6056 |                     -8.0819 | Loss      |
| range_pullback_plus_trend_breakout | no_guard | 2025-10     |       26 | -10.3088 |                     -5.0945 | Loss      |
| range_pullback_plus_trend_breakout | no_guard | 2025-11     |       23 |  -1.3076 |                     -0.7273 | Loss      |
| range_pullback_plus_trend_breakout | no_guard | 2025-12     |       33 | -11.5161 |                     -5.6656 | Loss      |
| range_pullback_plus_trend_breakout | no_guard | 2026-01     |       33 |   7.8834 |                      3.8996 | Profit    |
| range_pullback_plus_trend_breakout | no_guard | 2026-02     |       43 |  10.7352 |                      5.3421 | Profit    |
| range_pullback_plus_trend_breakout | no_guard | 2026-03     |       32 |  -3.1401 |                     -1.6606 | Loss      |
| range_pullback_plus_trend_breakout | no_guard | 2026-04     |       15 |  -2.4468 |                     -1.2517 | Loss      |
| range_pullback_plus_trend_breakout | no_guard | 2026-05     |       23 | -12.8038 |                     -6.2722 | Loss      |
| range_pullback_plus_trend_breakout | no_guard | 2026-06     |       30 |   3.046  |                      1.4362 | Profit    |
| range_pullback_plus_trend_breakout | no_guard | 2026-07     |       22 |  -9.2949 |                     -4.5797 | Loss      |
| range_pullback_plus_trend_breakout | no_guard | 2026-08     |       24 |  -8.1562 |                     -4.0441 | Loss      |
| range_pullback_plus_trend_breakout | no_guard | 2026-09     |       16 |  -6.4044 |                     -3.2088 | Loss      |
| range_pullback_plus_trend_breakout | no_guard | 2026-10     |       20 | -14.4409 |                     -7.0254 | Loss      |
| range_pullback_plus_trend_breakout | no_guard | 2026-11     |       22 |  -9.6818 |                     -4.7797 | Loss      |
| range_sweep_plus_trend_compression | no_guard | 2025-01     |       42 | -21.5949 |                    -10.3406 | Loss      |
| range_sweep_plus_trend_compression | no_guard | 2025-02     |       78 | -33.9939 |                    -15.8148 | Loss      |
| range_sweep_plus_trend_compression | no_guard | 2025-03     |       23 |  -1.0223 |                     -0.5852 | Loss      |
| range_sweep_plus_trend_compression | no_guard | 2025-04     |       48 | -11.9473 |                     -5.9063 | Loss      |
| range_sweep_plus_trend_compression | no_guard | 2025-05     |       94 | -28.8199 |                    -13.6451 | Loss      |
| range_sweep_plus_trend_compression | no_guard | 2025-06     |       48 | -25.9667 |                    -12.294  | Loss      |
| range_sweep_plus_trend_compression | no_guard | 2025-07     |       75 |   5.2062 |                      2.3835 | Profit    |
| range_sweep_plus_trend_compression | no_guard | 2025-08     |       67 | -32.8635 |                    -15.3443 | Loss      |
| range_sweep_plus_trend_compression | no_guard | 2025-09     |       90 | -32.037  |                    -15.0585 | Loss      |
| range_sweep_plus_trend_compression | no_guard | 2025-10     |       51 | -30.2423 |                    -14.1645 | Loss      |
| range_sweep_plus_trend_compression | no_guard | 2025-11     |       36 |   1.477  |                      0.6191 | Profit    |
| range_sweep_plus_trend_compression | no_guard | 2025-12     |       53 | -36.0214 |                    -16.5893 | Loss      |
| range_sweep_plus_trend_compression | no_guard | 2026-01     |       43 | -29.0236 |                    -13.6083 | Loss      |
| range_sweep_plus_trend_compression | no_guard | 2026-02     |       48 | -11.8567 |                     -5.8821 | Loss      |
| range_sweep_plus_trend_compression | no_guard | 2026-03     |       63 | -12.8074 |                     -6.3703 | Loss      |
| range_sweep_plus_trend_compression | no_guard | 2026-04     |       59 | -13.8048 |                     -6.8041 | Loss      |
| range_sweep_plus_trend_compression | no_guard | 2026-05     |       36 | -30.9235 |                    -14.3931 | Loss      |
| range_sweep_plus_trend_compression | no_guard | 2026-06     |       36 |  -7.3712 |                     -3.7223 | Loss      |
| range_sweep_plus_trend_compression | no_guard | 2026-07     |       34 | -14.7919 |                     -7.209  | Loss      |
| range_sweep_plus_trend_compression | no_guard | 2026-08     |       33 |  -7.9537 |                     -3.9702 | Loss      |
| range_sweep_plus_trend_compression | no_guard | 2026-09     |       31 | -21.8564 |                    -10.4139 | Loss      |
| range_sweep_plus_trend_compression | no_guard | 2026-10     |       21 | -14.2936 |                     -6.951  | Loss      |
| range_sweep_plus_trend_compression | no_guard | 2026-11     |       14 |  -3.1548 |                     -1.6111 | Loss      |
| rolling_90day_selector             | no_guard | 2025-01     |        2 |  -2.6165 |                     -1.304  | Loss      |
| rolling_90day_selector             | no_guard | 2025-02     |        1 |   2.7991 |                      1.3995 | Profit    |
| rolling_90day_selector             | no_guard | 2025-03     |        0 |   0      |                      0      | No trades |
| rolling_90day_selector             | no_guard | 2025-04     |        6 |  -2.793  |                     -1.3965 | Loss      |
| rolling_90day_selector             | no_guard | 2025-05     |        6 |  -3.23   |                     -1.6205 | Loss      |
| rolling_90day_selector             | no_guard | 2025-06     |        9 |  -5.6031 |                     -2.7765 | Loss      |
| rolling_90day_selector             | no_guard | 2025-07     |        3 |   2.2704 |                      1.1387 | Profit    |
| rolling_90day_selector             | no_guard | 2025-08     |        0 |   0      |                      0      | No trades |
| rolling_90day_selector             | no_guard | 2025-09     |        6 |  -2.3202 |                     -1.1621 | Loss      |
| rolling_90day_selector             | no_guard | 2025-10     |        0 |   0      |                      0      | No trades |
| rolling_90day_selector             | no_guard | 2025-11     |        0 |   0      |                      0      | No trades |
| rolling_90day_selector             | no_guard | 2025-12     |        1 |  -1.5004 |                     -0.7502 | Loss      |
| rolling_90day_selector             | no_guard | 2026-01     |        4 |  -1.9051 |                     -0.9625 | Loss      |
| rolling_90day_selector             | no_guard | 2026-02     |        8 |  -2.2237 |                     -1.1298 | Loss      |
| rolling_90day_selector             | no_guard | 2026-03     |       28 |  -3.0549 |                     -1.6159 | Loss      |
| rolling_90day_selector             | no_guard | 2026-04     |        6 |  -6.3003 |                     -3.112  | Loss      |
| rolling_90day_selector             | no_guard | 2026-05     |        6 |  -0.1117 |                     -0.0826 | Loss      |
| rolling_90day_selector             | no_guard | 2026-06     |        1 |   0.6262 |                      0.3131 | Profit    |
| rolling_90day_selector             | no_guard | 2026-07     |        8 |  -3.0958 |                     -1.5434 | Loss      |
| rolling_90day_selector             | no_guard | 2026-08     |       10 |  -3.9169 |                     -1.9599 | Loss      |
| rolling_90day_selector             | no_guard | 2026-09     |        1 |  -1.3135 |                     -0.6567 | Loss      |
| rolling_90day_selector             | no_guard | 2026-10     |        0 |   0      |                      0      | No trades |
| rolling_90day_selector             | no_guard | 2026-11     |        0 |   0      |                      0      | No trades |
| stage14_unchanged                  | no_guard | 2025-01     |        0 |   0      |                      0      | No trades |
| stage14_unchanged                  | no_guard | 2025-02     |        5 |   3.4246 |                      1.7112 | Profit    |
| stage14_unchanged                  | no_guard | 2025-03     |        0 |   0      |                      0      | No trades |
| stage14_unchanged                  | no_guard | 2025-04     |        7 |  -3.9609 |                     -1.9723 | Loss      |
| stage14_unchanged                  | no_guard | 2025-05     |        8 |  -0.5022 |                     -0.2761 | Loss      |
| stage14_unchanged                  | no_guard | 2025-06     |        2 |  -1.3156 |                     -0.6577 | Loss      |
| stage14_unchanged                  | no_guard | 2025-07     |        7 |   4.1869 |                      2.1001 | Profit    |
| stage14_unchanged                  | no_guard | 2025-08     |        0 |   0      |                      0      | No trades |
| stage14_unchanged                  | no_guard | 2025-09     |        6 |  -2.3202 |                     -1.1621 | Loss      |
| stage14_unchanged                  | no_guard | 2025-10     |        0 |   0      |                      0      | No trades |
| stage14_unchanged                  | no_guard | 2025-11     |        0 |   0      |                      0      | No trades |
| stage14_unchanged                  | no_guard | 2025-12     |        5 |  -0.4935 |                     -0.2506 | Loss      |
| stage14_unchanged                  | no_guard | 2026-01     |        6 |   0.871  |                      0.4246 | Profit    |
| stage14_unchanged                  | no_guard | 2026-02     |        5 |  -0.6546 |                     -0.3355 | Loss      |
| stage14_unchanged                  | no_guard | 2026-03     |        3 |   1.0977 |                      0.5492 | Profit    |
| stage14_unchanged                  | no_guard | 2026-04     |        7 |  -1.0404 |                     -0.5262 | Loss      |
| stage14_unchanged                  | no_guard | 2026-05     |        5 |   3.2683 |                      1.6261 | Profit    |
| stage14_unchanged                  | no_guard | 2026-06     |        2 |   3.355  |                      1.6818 | Profit    |
| stage14_unchanged                  | no_guard | 2026-07     |        8 |  -3.0958 |                     -1.5434 | Loss      |
| stage14_unchanged                  | no_guard | 2026-08     |       14 |  -6.1995 |                     -3.0769 | Loss      |
| stage14_unchanged                  | no_guard | 2026-09     |        0 |   0      |                      0      | No trades |
| stage14_unchanged                  | no_guard | 2026-10     |        1 |  -1.2004 |                     -0.6002 | Loss      |
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
