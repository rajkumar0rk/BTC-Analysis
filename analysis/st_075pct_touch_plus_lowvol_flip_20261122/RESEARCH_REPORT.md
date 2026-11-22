# BTCUSD 15M: 0.75% / 1.5% Touch + 3% / 0.5% Flip combined

Two exact user-selected previously profitable in BOTH calendar 2025
and January-October 2026 strategies, no retuning; 1m historical data.
15m ST 10/3 closing exit retained, actual 1m stops/targets;
one concurrent open position in exclusive portfolios.

## One-position portfolio policies vs standalone
| policy                               |   trades |   wins |   losses |   win_rate_pct |   net_pts |   profitable_realized_exit_months |   losing_realized_exit_months |   flat_realized_exit_months |   max_realized_trade_equity_drawdown_pts |   blocked_overlaps |   blocked_one_cycle |
|:-------------------------------------|---------:|-------:|---------:|---------------:|----------:|----------------------------------:|------------------------------:|----------------------------:|-----------------------------------------:|-------------------:|--------------------:|
| standalone_line_touch                |      108 |     36 |       72 |          33.33 |   7928.77 |                                12 |                            10 |                           0 |                                  4505.01 |                  0 |                   0 |
| standalone_bullish_flip              |       42 |     33 |        9 |          78.57 |   3401.08 |                                14 |                             5 |                           3 |                                  2556.04 |                  0 |                   0 |
| parallel_both_not_one_position       |      150 |     69 |       81 |          46    |  11329.9  |                                13 |                             9 |                           0 |                                  4845.13 |                  0 |                   0 |
| combined_touch_priority              |      143 |     67 |       76 |          46.85 |  10608.6  |                                13 |                             9 |                           0 |                                  5192.53 |                  4 |                   3 |
| combined_touch_priority_no_cycle_cap |      146 |     67 |       79 |          45.89 |   9524.06 |                                12 |                            10 |                           0 |                                  5767.53 |                  4 |                   0 |
| combined_flip_priority               |      143 |     67 |       76 |          46.85 |  10608.6  |                                13 |                             9 |                           0 |                                  5192.53 |                  4 |                   3 |
| combined_flip_priority_no_cycle_cap  |      146 |     67 |       79 |          45.89 |   9524.06 |                                12 |                            10 |                           0 |                                  5767.53 |                  4 |                   0 |

## Yearly results by actual exit month
| policy                               | period      |   trades |   wins |   losses |   net_pts |   profitable_months |   losing_months |   flat_months |   max_monthly_loss_pts |
|:-------------------------------------|:------------|---------:|-------:|---------:|----------:|--------------------:|----------------:|--------------:|-----------------------:|
| standalone_line_touch                | 2025_full   |       52 |     18 |       34 |   7039.37 |                   7 |               5 |             0 |               -1666.23 |
| standalone_line_touch                | 2026_JanOct |       56 |     18 |       38 |    889.4  |                   5 |               5 |             0 |               -1741.11 |
| standalone_line_touch                | 22_months   |      108 |     36 |       72 |   7928.77 |                  12 |              10 |             0 |               -1741.11 |
| standalone_bullish_flip              | 2025_full   |       28 |     23 |        5 |   3394.93 |                   9 |               2 |             1 |               -1643.21 |
| standalone_bullish_flip              | 2026_JanOct |       14 |     10 |        4 |      6.15 |                   5 |               3 |             2 |                -697.31 |
| standalone_bullish_flip              | 22_months   |       42 |     33 |        9 |   3401.08 |                  14 |               5 |             3 |               -1643.21 |
| parallel_both_not_one_position       | 2025_full   |       80 |     41 |       39 |  10434.3  |                   7 |               5 |             0 |               -2478.07 |
| parallel_both_not_one_position       | 2026_JanOct |       70 |     28 |       42 |    895.56 |                   6 |               4 |             0 |               -2161.66 |
| parallel_both_not_one_position       | 22_months   |      150 |     69 |       81 |  11329.9  |                  13 |               9 |             0 |               -2478.07 |
| combined_touch_priority              | 2025_full   |       76 |     40 |       36 |  10060.4  |                   8 |               4 |             0 |               -1745.71 |
| combined_touch_priority              | 2026_JanOct |       67 |     27 |       40 |    548.16 |                   5 |               5 |             0 |               -1945.56 |
| combined_touch_priority              | 22_months   |      143 |     67 |       76 |  10608.6  |                  13 |               9 |             0 |               -1945.56 |
| combined_touch_priority_no_cycle_cap | 2025_full   |       77 |     40 |       37 |   9550.91 |                   7 |               5 |             0 |               -1745.71 |
| combined_touch_priority_no_cycle_cap | 2026_JanOct |       69 |     27 |       42 |    -26.84 |                   5 |               5 |             0 |               -2161.66 |
| combined_touch_priority_no_cycle_cap | 22_months   |      146 |     67 |       79 |   9524.06 |                  12 |              10 |             0 |               -2161.66 |
| combined_flip_priority               | 2025_full   |       76 |     40 |       36 |  10060.4  |                   8 |               4 |             0 |               -1745.71 |
| combined_flip_priority               | 2026_JanOct |       67 |     27 |       40 |    548.16 |                   5 |               5 |             0 |               -1945.56 |
| combined_flip_priority               | 22_months   |      143 |     67 |       76 |  10608.6  |                  13 |               9 |             0 |               -1945.56 |
| combined_flip_priority_no_cycle_cap  | 2025_full   |       77 |     40 |       37 |   9550.91 |                   7 |               5 |             0 |               -1745.71 |
| combined_flip_priority_no_cycle_cap  | 2026_JanOct |       69 |     27 |       42 |    -26.84 |                   5 |               5 |             0 |               -2161.66 |
| combined_flip_priority_no_cycle_cap  | 22_months   |      146 |     67 |       79 |   9524.06 |                  12 |              10 |             0 |               -2161.66 |

## 2025 full vs Jan-Oct 2025 vs Jan-Oct 2026
| policy                  | period      |   net_pts |   profitable_months |   losing_months |   flat_months |
|:------------------------|:------------|----------:|--------------------:|----------------:|--------------:|
| combined_touch_priority | 2025_full   |  10060.4  |                   8 |               4 |             0 |
| combined_touch_priority | 2025_JanOct |  10076.1  |                   7 |               3 |             0 |
| combined_touch_priority | 2026_JanOct |    548.16 |                   5 |               5 |             0 |
| combined_touch_priority | 22_months   |  10608.6  |                  13 |               9 |             0 |
| combined_flip_priority  | 2025_full   |  10060.4  |                   8 |               4 |             0 |
| combined_flip_priority  | 2025_JanOct |  10076.1  |                   7 |               3 |             0 |
| combined_flip_priority  | 2026_JanOct |    548.16 |                   5 |               5 |             0 |
| combined_flip_priority  | 22_months   |  10608.6  |                  13 |               9 |             0 |

## Every actual-exit month: two priority choices
| policy                  | month_ist   |   realized_closed_trades |   exit_month_realized_net_pts |   month_to_month_mtm_change_pts |   month_end_open_positions |
|:------------------------|:------------|-------------------------:|------------------------------:|--------------------------------:|---------------------------:|
| combined_touch_priority | 2025-01     |                       10 |                       -202.54 |                         -202.54 |                          0 |
| combined_touch_priority | 2025-02     |                        8 |                      -1745.71 |                        -1745.71 |                          0 |
| combined_touch_priority | 2025-03     |                        7 |                       2675.82 |                         2675.82 |                          0 |
| combined_touch_priority | 2025-04     |                        4 |                       2200.49 |                         2200.49 |                          0 |
| combined_touch_priority | 2025-05     |                        9 |                       1453.72 |                         1453.72 |                          0 |
| combined_touch_priority | 2025-06     |                        3 |                        500.5  |                          500.5  |                          0 |
| combined_touch_priority | 2025-07     |                        7 |                       1261.61 |                         1261.61 |                          0 |
| combined_touch_priority | 2025-08     |                        4 |                      -1659.07 |                        -1659.07 |                          0 |
| combined_touch_priority | 2025-09     |                        6 |                        394.49 |                          394.49 |                          0 |
| combined_touch_priority | 2025-10     |                        6 |                       5196.81 |                         5196.81 |                          0 |
| combined_touch_priority | 2025-11     |                        7 |                       -961.15 |                         -961.15 |                          0 |
| combined_touch_priority | 2025-12     |                        5 |                        945.44 |                          945.44 |                          0 |
| combined_touch_priority | 2026-01     |                        7 |                       -174.59 |                         -174.59 |                          0 |
| combined_touch_priority | 2026-02     |                        9 |                       -387.95 |                         -387.95 |                          0 |
| combined_touch_priority | 2026-03     |                        8 |                      -1945.56 |                        -1945.56 |                          0 |
| combined_touch_priority | 2026-04     |                        4 |                         85.92 |                           85.92 |                          0 |
| combined_touch_priority | 2026-05     |                        6 |                        459.79 |                          459.79 |                          0 |
| combined_touch_priority | 2026-06     |                        6 |                        237.4  |                          237.4  |                          0 |
| combined_touch_priority | 2026-07     |                        7 |                      -1151.27 |                        -1151.27 |                          0 |
| combined_touch_priority | 2026-08     |                        5 |                       1422.57 |                         1422.57 |                          0 |
| combined_touch_priority | 2026-09     |                       12 |                       2517.56 |                         2517.56 |                          0 |
| combined_touch_priority | 2026-10     |                        3 |                       -515.72 |                         -515.72 |                          0 |
| combined_flip_priority  | 2025-01     |                       10 |                       -202.54 |                         -202.54 |                          0 |
| combined_flip_priority  | 2025-02     |                        8 |                      -1745.71 |                        -1745.71 |                          0 |
| combined_flip_priority  | 2025-03     |                        7 |                       2675.82 |                         2675.82 |                          0 |
| combined_flip_priority  | 2025-04     |                        4 |                       2200.49 |                         2200.49 |                          0 |
| combined_flip_priority  | 2025-05     |                        9 |                       1453.72 |                         1453.72 |                          0 |
| combined_flip_priority  | 2025-06     |                        3 |                        500.5  |                          500.5  |                          0 |
| combined_flip_priority  | 2025-07     |                        7 |                       1261.61 |                         1261.61 |                          0 |
| combined_flip_priority  | 2025-08     |                        4 |                      -1659.07 |                        -1659.07 |                          0 |
| combined_flip_priority  | 2025-09     |                        6 |                        394.49 |                          394.49 |                          0 |
| combined_flip_priority  | 2025-10     |                        6 |                       5196.81 |                         5196.81 |                          0 |
| combined_flip_priority  | 2025-11     |                        7 |                       -961.15 |                         -961.15 |                          0 |
| combined_flip_priority  | 2025-12     |                        5 |                        945.44 |                          945.44 |                          0 |
| combined_flip_priority  | 2026-01     |                        7 |                       -174.59 |                         -174.59 |                          0 |
| combined_flip_priority  | 2026-02     |                        9 |                       -387.95 |                         -387.95 |                          0 |
| combined_flip_priority  | 2026-03     |                        8 |                      -1945.56 |                        -1945.56 |                          0 |
| combined_flip_priority  | 2026-04     |                        4 |                         85.92 |                           85.92 |                          0 |
| combined_flip_priority  | 2026-05     |                        6 |                        459.79 |                          459.79 |                          0 |
| combined_flip_priority  | 2026-06     |                        6 |                        237.4  |                          237.4  |                          0 |
| combined_flip_priority  | 2026-07     |                        7 |                      -1151.27 |                        -1151.27 |                          0 |
| combined_flip_priority  | 2026-08     |                        5 |                       1422.57 |                         1422.57 |                          0 |
| combined_flip_priority  | 2026-09     |                       12 |                       2517.56 |                         2517.56 |                          0 |
| combined_flip_priority  | 2026-10     |                        3 |                       -515.72 |                         -515.72 |                          0 |

## Caveats
- Historical results use the SAME 22 months used to choose settings.
- 2025 has 12 months and 2026 Jan-Oct has 10; compare Jan-Oct windows.
- Parallel sum DOUBLE COUNTS overlapping positions; not executable
  with one open position and fixed capital per trade.
- Trading fee model: taker 0.05% per side plus 18% GST, 5 BTC
  points adverse slippage at each fill.
- Net points per 1 BTC-equivalent, not dollar account P&L;
  margin, leverage, liquidation, funding, real bid-ask and
  live order latency NOT modeled.
