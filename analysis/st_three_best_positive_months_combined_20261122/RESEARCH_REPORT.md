# BTCUSD 15M three best positive-month strategies combined

Original Supertrend (10,3) closing exit unchanged. Third candle
LONG market entries, fixed percent SL/TP using conservative 1m bars;
ONE POSITION across all strategies in exclusive variants.

Exact user-selected rules:
- Line Touch: SL .2%, TP 1.5%, volume>=1x, ATRpct>=.20%.
- Bullish Flip: SL 3%, TP .5%, volume<=.8x, ATRpct>=.20%.
- Bullish Flip+Breakout: SL 3%, TP 1.5%, volume<=.8x, ATRpct>=.20%.
- Breakout = next 15m candle green, CLOSE above flip candle HIGH.

DEFAULT: when candidate entry moments tie, breakout wins before
touch then flip. One new live position only AFTER prior exit minute.
Also globally one trade per ST bullish cycle in default. Tested
both alternate priorities and allowing multiple trades per ST cycle.
Only positions ENTERED in 2025Jan through 2026Oct are counted.

## Combined result, independently summed reference and sensitivities
| policy                                   |   trades |   wins |   losses |   win_rate_pct |   net_pts |   profitable_entry_months |   losing_entry_months |   flat_entry_months |   profitable_realized_exit_months |   losing_realized_exit_months |   flat_realized_exit_months |   profitable_mark_to_market_months |   losing_mark_to_market_months |   ending_oct_equity_mtm_pts |   max_realized_trade_equity_drawdown_pts |   blocked_overlaps |   blocked_one_cycle |
|:-----------------------------------------|---------:|-------:|---------:|---------------:|----------:|--------------------------:|----------------------:|--------------------:|----------------------------------:|------------------------------:|----------------------------:|-----------------------------------:|-------------------------------:|----------------------------:|-----------------------------------------:|-------------------:|--------------------:|
| standalone_line_touch                    |      108 |     24 |       84 |          22.22 |   4060.14 |                        14 |                     8 |                   0 |                                14 |                             8 |                           0 |                                 14 |                              8 |                     4060.14 |                                  3055.27 |                nan |                 nan |
| standalone_bullish_flip                  |       42 |     33 |        9 |          78.57 |   3401.08 |                        14 |                     5 |                   3 |                                14 |                             5 |                           3 |                                 14 |                              5 |                     3401.08 |                                  2556.04 |                nan |                 nan |
| standalone_flip_breakout                 |       34 |     19 |       15 |          55.88 |   8392.57 |                        12 |                     4 |                   6 |                                12 |                             4 |                           6 |                                 12 |                              4 |                     8392.57 |                                  3769.29 |                nan |                 nan |
| parallel_sum_not_executable_one_position |      184 |     76 |      108 |          41.3  |  15853.8  |                        14 |                     8 |                   0 |                                14 |                             8 |                           0 |                                 14 |                              8 |                    15853.8  |                                  8127.6  |                nan |                 nan |
| exclusive_touch_plus_flip                |      143 |     55 |       88 |          38.46 |   6319.65 |                        15 |                     7 |                   0 |                                15 |                             7 |                           0 |                                 15 |                              7 |                     6319.65 |                                  3763.28 |                  4 |                   3 |
| exclusive_touch_plus_breakout            |      138 |     43 |       95 |          31.16 |  13617.5  |                        14 |                     8 |                   0 |                                14 |                             8 |                           0 |                                 14 |                              8 |                    13617.5  |                                  4976.53 |                  3 |                   1 |
| exclusive_flip_plus_breakout             |       42 |     26 |       16 |          61.9  |   9980.31 |                        14 |                     5 |                   3 |                                14 |                             5 |                           3 |                                 14 |                              5 |                     9980.31 |                                  3732.47 |                 34 |                   0 |
| exclusive_all_three_default              |      143 |     48 |       95 |          33.57 |  12898.9  |                        14 |                     8 |                   0 |                                14 |                             8 |                           0 |                                 14 |                              8 |                    12898.9  |                                  5089.22 |                 39 |                   2 |
| exclusive_all_three_flip_first           |      143 |     55 |       88 |          38.46 |   6319.65 |                        15 |                     7 |                   0 |                                15 |                             7 |                           0 |                                 15 |                              7 |                     6319.65 |                                  3763.28 |                 38 |                   3 |
| exclusive_all_three_touch_first          |      143 |     48 |       95 |          33.57 |  12898.9  |                        14 |                     8 |                   0 |                                14 |                             8 |                           0 |                                 14 |                              8 |                    12898.9  |                                  5089.22 |                 39 |                   2 |
| exclusive_all_three_no_cycle_cap         |      145 |     48 |       97 |          33.1  |  12461.2  |                        14 |                     8 |                   0 |                                14 |                             8 |                           0 |                                 14 |                              8 |                    12461.2  |                                  5526.86 |                 39 |                   0 |

## Combined portfolio by month (default exclusive)
| month_ist   |   newly_entered_trades |   entry_month_net_pts |   exit_month_realized_net_pts |   month_to_month_mtm_change_pts |   month_end_equity_mtm_pts |   month_end_open_positions |
|:------------|-----------------------:|----------------------:|------------------------------:|--------------------------------:|---------------------------:|---------------------------:|
| 2025-01     |                     10 |               -456.1  |                       -456.1  |                         -456.1  |                    -456.1  |                          0 |
| 2025-02     |                      8 |              -2546.37 |                      -2546.37 |                        -2546.37 |                   -3002.47 |                          0 |
| 2025-03     |                      7 |               2424.79 |                       2424.79 |                         2424.79 |                    -577.67 |                          0 |
| 2025-04     |                      4 |               2168.65 |                       2168.65 |                         2168.65 |                    1590.98 |                          0 |
| 2025-05     |                      9 |               3303.73 |                       3303.73 |                         3303.73 |                    4894.71 |                          0 |
| 2025-06     |                      3 |               1385.5  |                       1385.5  |                         1385.5  |                    6280.21 |                          0 |
| 2025-07     |                      7 |               1496.14 |                       1496.14 |                         1496.14 |                    7776.35 |                          0 |
| 2025-08     |                      4 |              -1511.68 |                      -1511.68 |                        -1511.68 |                    6264.67 |                          0 |
| 2025-09     |                      6 |               2026.86 |                       2026.86 |                         2026.86 |                    8291.53 |                          0 |
| 2025-10     |                      6 |               5634.52 |                       5634.52 |                         5634.52 |                   13926    |                          0 |
| 2025-11     |                      7 |                731.08 |                        731.08 |                          731.08 |                   14657.1  |                          0 |
| 2025-12     |                      5 |               1159.36 |                       1159.36 |                         1159.36 |                   15816.5  |                          0 |
| 2026-01     |                      7 |               -570.58 |                       -570.58 |                         -570.58 |                   15245.9  |                          0 |
| 2026-02     |                      9 |                330.36 |                        330.36 |                          330.36 |                   15576.3  |                          0 |
| 2026-03     |                      8 |              -1811.75 |                      -1811.75 |                        -1811.75 |                   13764.5  |                          0 |
| 2026-04     |                      4 |                293.26 |                        293.26 |                          293.26 |                   14057.8  |                          0 |
| 2026-05     |                      6 |                855.9  |                        855.9  |                          855.9  |                   14913.7  |                          0 |
| 2026-06     |                      6 |              -2227.55 |                      -2227.55 |                        -2227.55 |                   12686.1  |                          0 |
| 2026-07     |                      7 |               -397.41 |                       -397.41 |                         -397.41 |                   12288.7  |                          0 |
| 2026-08     |                      5 |                469.86 |                        469.86 |                          469.86 |                   12758.6  |                          0 |
| 2026-09     |                     12 |                447.86 |                        447.86 |                          447.86 |                   13206.5  |                          0 |
| 2026-10     |                      3 |               -307.58 |                       -307.58 |                         -307.58 |                   12898.9  |                          0 |

## Critical month accounting
- Legacy entry-month attribution assigns whole trade P&L to the
  opening calendar month even if it closes in a later month.
- Realized exit-month P&L counts only trades closed in that month.
- MTM end-month includes cumulative realized P&L plus unrealized
  open position mark net of estimated exit fees and slippage.
- Complete 22 months are Jan 2025 through Oct 2026 IST; positions
  opened in Oct and closed in Nov contribute realized P&L to Nov,
  not the preceding 22 exit-month figures.

## Warnings
- Net is BTC price points per 1 BTC equivalent, NOT USDT account ROI.
- All three parameters selected on the SAME historical dataset;
  combing them does not make historical selection out-of-sample.
- Funding, liquidation, leverage, fill depth and queued orders
  are absent. Stacked margin in the independent sum is NOT modeled.
- Conservative one-minute SL-before-TP ordering is modeled, but
  one-minute OHLC cannot recreate actual tick sequence.
