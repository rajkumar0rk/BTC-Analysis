# BTC ST V1.0 bearish-flip SHORT add-on: independent trade-by-trade audit

The 67 original Line Touch and 18 Bullish Flip LONG trades remain
EXACTLY as locked. New 23 bearish SHORT trades use a fresh explicit
1m bar-by-bar conservative replay, not the research grid's
vectorized cached exits. Original 85 trades are not blocked.

## Cost and stop sensitivity (SHORT leg only, LONG original costs unchanged)
| scenario                    |   short_count |   short_wins |   short_losses |   original_core_count | original_core_unchanged   |   short_net |   combined_total |   net_2025 |   net_2026 |   profitable_months |   losing_months |   original_profitable_months_degraded |   improved_old_losing_months |   max_closed_equity_drawdown |   short_win_rate_pct |   short_tp_exits |   short_stops |   short_st_close_exits |   same_minute_sl_tp_conflicts |
|:----------------------------|--------------:|-------------:|---------------:|----------------------:|:--------------------------|------------:|-----------------:|-----------:|-----------:|--------------------:|----------------:|--------------------------------------:|-----------------------------:|-----------------------------:|---------------------:|-----------------:|--------------:|-----------------------:|------------------------------:|
| reference_costs             |            23 |           23 |              0 |                    85 | True                      |     3534.28 |          22633.9 |    16723.1 |    5910.76 |                  18 |               4 |                                     0 |                            1 |                      2642.53 |               100    |               23 |             0 |                      0 |                             0 |
| higher_slippage_10pt        |            23 |           23 |              0 |                    85 | True                      |     3419    |          22518.6 |    16663   |    5855.63 |                  18 |               4 |                                     0 |                            1 |                      2652.56 |               100    |               23 |             0 |                      0 |                             0 |
| higher_slippage_20pt        |            23 |           23 |              0 |                    85 | True                      |     3188.45 |          22288.1 |    16542.7 |    5745.37 |                  18 |               4 |                                     0 |                            1 |                      2672.61 |               100    |               23 |             0 |                      0 |                             0 |
| higher_slippage_30pt        |            23 |           23 |              0 |                    85 | True                      |     2957.89 |          22057.5 |    16422.4 |    5635.1  |                  18 |               4 |                                     0 |                            1 |                      2692.66 |               100    |               23 |             0 |                      0 |                             0 |
| higher_fee_0p1pct           |            23 |           23 |              0 |                    85 | True                      |     1173.99 |          20273.6 |    15281   |    4992.65 |                  18 |               4 |                                     0 |                            1 |                      2811.7  |               100    |               23 |             0 |                      0 |                             0 |
| higher_fee_0p1pct_plus_10pt |            23 |           23 |              0 |                    85 | True                      |     1058.79 |          20158.4 |    15220.9 |    4937.55 |                  18 |               4 |                                     0 |                            1 |                      2821.72 |               100    |               23 |             0 |                      0 |                             0 |
| stop_loss_0p75pct           |            23 |           22 |              1 |                    85 | True                      |     2780.45 |          21880.1 |    16723.1 |    5156.94 |                  18 |               4 |                                     1 |                            1 |                      2642.53 |                95.65 |               22 |             1 |                      0 |                             0 |
| stop_loss_1p5pct            |            23 |           23 |              0 |                    85 | True                      |     3534.28 |          22633.9 |    16723.1 |    5910.76 |                  18 |               4 |                                     0 |                            1 |                      2642.53 |               100    |               23 |             0 |                      0 |                             0 |

## Reference-case monthly before and after third SHORT leg
| scenario        | month_ist   |   core_net |   combined_net |   addition_net |
|:----------------|:------------|-----------:|---------------:|---------------:|
| reference_costs | 2025-01     |    3133.33 |        3501.63 |         368.3  |
| reference_costs | 2025-02     |    1184.61 |        1184.61 |           0    |
| reference_costs | 2025-03     |    2029.28 |        2328.9  |         299.62 |
| reference_costs | 2025-04     |    1599.33 |        1599.33 |           0    |
| reference_costs | 2025-05     |    2331.96 |        2523.2  |         191.24 |
| reference_costs | 2025-06     |    -293.78 |        -293.78 |           0    |
| reference_costs | 2025-07     |    1662.05 |        1873.05 |         211    |
| reference_costs | 2025-08     |   -1596.71 |       -1596.71 |           0    |
| reference_costs | 2025-09     |     486.27 |         691.07 |         204.8  |
| reference_costs | 2025-10     |    3769.88 |        4188.57 |         418.69 |
| reference_costs | 2025-11     |     327.91 |         481.06 |         153.15 |
| reference_costs | 2025-12     |     -80.79 |         242.2  |         322.99 |
| reference_costs | 2026-01     |     372.88 |         372.88 |           0    |
| reference_costs | 2026-02     |     267.6  |         267.6  |           0    |
| reference_costs | 2026-03     |   -1916.69 |       -1665.14 |         251.55 |
| reference_costs | 2026-04     |    1328.47 |        1574.47 |         246    |
| reference_costs | 2026-05     |    1686.73 |        1686.73 |           0    |
| reference_costs | 2026-06     |     543.11 |         765.56 |         222.45 |
| reference_costs | 2026-07     |     213.71 |         431.69 |         217.97 |
| reference_costs | 2026-08     |    1422.57 |        1422.57 |           0    |
| reference_costs | 2026-09     |    1445.21 |        1581.39 |         136.18 |
| reference_costs | 2026-10     |    -817.32 |        -526.98 |         290.34 |

## Important limits
Multiple thousands of configurations were evaluated, 2025 and
2026 already repeatedly inspected; NOT a genuine untouched
holdout. This audit reproduces but does not prove forward alpha.
SHORT margin, funding, liquidation and order-book depth are
not modeled. All figures in BTC price points per 1 BTC equivalent.
