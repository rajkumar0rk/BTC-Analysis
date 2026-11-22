# BTCUSD 15m why portfolio failed Jan-Oct 2026 — verified trade postmortem

Original three selected configurations, no retuning or future leakage;
one-position portfolio default breakout>touch>flip, one ST bullish
cycle; all net metrics in 1-BTC-equivalent price points.

## Primary 2025 vs Jan-Oct 2026 trade attribution
| policy                      | segment     |   trades |   wins |   losses |   win_rate_pct |   net_pts |   gross_win_pts |   gross_loss_pts |   mean_win_pts |   mean_loss_pts |   max_loss_trade_pts |   profit_factor |
|:----------------------------|:------------|---------:|-------:|---------:|---------------:|----------:|----------------:|-----------------:|---------------:|----------------:|---------------------:|----------------:|
| exclusive_all_three_default | 2025_JanOct |       64 |     26 |       38 |          40.62 |  13926    |         30565.4 |         -16639.3 |        1175.59 |         -437.88 |             -1422.37 |           1.837 |
| exclusive_all_three_default | 2025_full   |       76 |     31 |       45 |          40.79 |  15816.5  |         34957   |         -19140.5 |        1127.65 |         -425.35 |             -1422.37 |           1.826 |
| exclusive_all_three_default | 2026_JanOct |       67 |     17 |       50 |          25.37 |  -2917.62 |         12241.9 |         -15159.5 |         720.11 |         -303.19 |             -1554.8  |           0.808 |

## Contribution by strategy and period (actual exit month)
| segment     | strategy      |   trades |   wins |   losses |   net_pts |   gross_win_pts |   gross_loss_pts |   mean_win_pts |   mean_loss_pts |   max_loss_trade_pts |
|:------------|:--------------|---------:|-------:|---------:|----------:|----------------:|-----------------:|---------------:|----------------:|---------------------:|
| 2025_JanOct | bullish_flip  |        2 |      2 |        0 |    808.7  |          808.7  |             0    |         404.35 |          nan    |               363.91 |
| 2025_JanOct | flip_breakout |       22 |     14 |        8 |   9178.68 |        16621    |         -7442.29 |        1187.21 |         -930.29 |             -1422.37 |
| 2025_JanOct | line_touch    |       40 |     10 |       30 |   3938.67 |        13135.7  |         -9197.04 |        1313.57 |         -306.57 |              -391.96 |
| 2025_full   | bullish_flip  |        4 |      4 |        0 |   1513.78 |         1513.78 |             0    |         378.45 |          nan    |               340.71 |
| 2025_full   | flip_breakout |       24 |     15 |        9 |   9685.37 |        17809.3  |         -8123.98 |        1187.29 |         -902.66 |             -1422.37 |
| 2025_full   | line_touch    |       48 |     12 |       36 |   4617.35 |        15633.9  |        -11016.6  |        1302.83 |         -306.02 |              -391.96 |
| 2026_JanOct | bullish_flip  |        4 |      3 |        1 |     73.96 |          804.06 |          -730.1  |         268.02 |         -730.1  |              -730.1  |
| 2026_JanOct | flip_breakout |       10 |      4 |        6 |  -1292.8  |         3129.95 |         -4422.75 |         782.49 |         -737.13 |             -1554.8  |
| 2026_JanOct | line_touch    |       53 |     10 |       43 |  -1698.78 |         8307.88 |        -10006.6  |         830.79 |         -232.71 |              -299.74 |

## Contribution by exit reason and period
| segment     | reason                        |   trades |   wins |   losses |   net_pts |   mean_win_pts |   mean_loss_pts |
|:------------|:------------------------------|---------:|-------:|---------:|----------:|---------------:|----------------:|
| 2025_JanOct | original_15m_supertrend_close |       16 |      4 |       12 |  -6393.14 |         403.64 |         -667.31 |
| 2025_JanOct | percent_stop_loss             |       26 |      0 |       26 |  -8631.61 |         nan    |         -331.99 |
| 2025_JanOct | percent_take_profit           |       22 |     22 |        0 |  28950.8  |        1315.95 |          nan    |
| 2025_full   | original_15m_supertrend_close |       18 |      4 |       14 |  -7310.66 |         403.64 |         -637.52 |
| 2025_full   | percent_stop_loss             |       31 |      0 |       31 | -10215.3  |         nan    |         -329.53 |
| 2025_full   | percent_take_profit           |       27 |     27 |        0 |  33342.5  |        1234.91 |          nan    |
| 2026_JanOct | original_15m_supertrend_close |       14 |      3 |       11 |  -5561.8  |          99.31 |         -532.7  |
| 2026_JanOct | percent_stop_loss             |       39 |      0 |       39 |  -9299.78 |         nan    |         -238.46 |
| 2026_JanOct | percent_take_profit           |       14 |     14 |        0 |  11944    |         853.14 |          nan    |

## 2026 losing months' precise strategy contributions
| exit_month_ist   | strategy      |   trades |   wins |   losses |   net_pts |   gross_win_pts |   gross_loss_pts |
|:-----------------|:--------------|---------:|-------:|---------:|----------:|----------------:|-----------------:|
| 2026-01          | flip_breakout |        3 |      1 |        2 |    537.93 |         1251.53 |          -713.59 |
| 2026-01          | line_touch    |        4 |      0 |        4 |  -1108.52 |            0    |         -1108.52 |
| 2026-03          | bullish_flip  |        2 |      1 |        1 |   -466.72 |          263.38 |          -730.1  |
| 2026-03          | line_touch    |        6 |      0 |        6 |  -1345.03 |            0    |         -1345.03 |
| 2026-06          | flip_breakout |        2 |      0 |        2 |  -2482.19 |            0    |         -2482.19 |
| 2026-06          | line_touch    |        4 |      1 |        3 |    254.64 |          861.69 |          -607.04 |
| 2026-07          | flip_breakout |        1 |      1 |        0 |    848.68 |          848.68 |             0    |
| 2026-07          | line_touch    |        6 |      0 |        6 |  -1246.09 |            0    |         -1246.09 |
| 2026-10          | flip_breakout |        1 |      1 |        0 |    127.59 |          127.59 |             0    |
| 2026-10          | line_touch    |        2 |      0 |        2 |   -435.17 |            0    |          -435.17 |

## 2026 all months
| month_ist   |   newly_entered_trades |   exit_month_realized_net_pts |
|:------------|-----------------------:|------------------------------:|
| 2026-01     |                      7 |                       -570.58 |
| 2026-02     |                      9 |                        330.36 |
| 2026-03     |                      8 |                      -1811.75 |
| 2026-04     |                      4 |                        293.26 |
| 2026-05     |                      6 |                        855.9  |
| 2026-06     |                      6 |                      -2227.55 |
| 2026-07     |                      7 |                       -397.41 |
| 2026-08     |                      5 |                        469.86 |
| 2026-09     |                     12 |                        447.86 |
| 2026-10     |                      3 |                       -307.58 |

## Worst individual trades in the combined portfolio
| strategy      | entry_utc                 | exit_utc                  |   entry_fill |   exit_fill |   net_pts | reason                        |   holding_minutes |
|:--------------|:--------------------------|:--------------------------|-------------:|------------:|----------:|:------------------------------|------------------:|
| flip_breakout | 2026-06-05 21:00:00+00:00 | 2026-06-06 04:15:00+00:00 |      61587   |     60104   | -1554.8   | original_15m_supertrend_close |               435 |
| flip_breakout | 2025-04-09 06:15:00+00:00 | 2025-04-09 11:45:00+00:00 |      77249.5 |     75917.5 | -1422.37  | original_15m_supertrend_close |               330 |
| flip_breakout | 2025-01-08 23:00:00+00:00 | 2025-01-09 02:15:00+00:00 |      95252.5 |     94066   | -1298.2   | original_15m_supertrend_close |               195 |
| flip_breakout | 2025-02-11 22:00:00+00:00 | 2025-02-12 04:00:00+00:00 |      96349   |     95246.5 | -1215.54  | original_15m_supertrend_close |               360 |
| flip_breakout | 2025-05-12 23:30:00+00:00 | 2025-05-13 02:15:00+00:00 |     103064   |    102063   | -1122.53  | original_15m_supertrend_close |               165 |
| flip_breakout | 2026-06-09 20:15:00+00:00 | 2026-06-10 02:45:00+00:00 |      62198.5 |     61344   |  -927.39  | original_15m_supertrend_close |               390 |
| flip_breakout | 2025-09-22 22:00:00+00:00 | 2025-09-23 02:00:00+00:00 |     112916   |    112122   |  -926.772 | original_15m_supertrend_close |               240 |
| flip_breakout | 2025-02-25 22:15:00+00:00 | 2025-02-26 12:30:00+00:00 |      88967   |     88280   |  -791.576 | original_15m_supertrend_close |               855 |
| bullish_flip  | 2026-03-17 18:15:00+00:00 | 2026-03-17 23:45:00+00:00 |      74556.5 |     73914   |  -730.098 | original_15m_supertrend_close |               330 |
| flip_breakout | 2025-12-26 02:30:00+00:00 | 2025-12-26 08:00:00+00:00 |      89014   |     88437   |  -681.696 | original_15m_supertrend_close |               330 |
| flip_breakout | 2026-02-03 20:45:00+00:00 | 2026-02-04 11:15:00+00:00 |      76359   |     75787   |  -661.766 | original_15m_supertrend_close |               870 |
| flip_breakout | 2026-05-18 20:30:00+00:00 | 2026-05-19 02:00:00+00:00 |      77105   |     76630.5 |  -565.204 | original_15m_supertrend_close |               330 |

## Supertrend 15m bullish cycle regime diagnostic
| period      |   bullish_ST_flips |   flips_shorter_than_or_eq_1hr |   flips_shorter_than_or_eq_4hr |   flips_shorter_than_or_eq_8hr |   pct_flips_revert_within_1hr |   pct_flips_revert_within_4hr |   pct_flips_revert_within_8hr |   median_bull_run_15m_bars |
|:------------|-------------------:|-------------------------------:|-------------------------------:|-------------------------------:|------------------------------:|------------------------------:|------------------------------:|---------------------------:|
| 2025_full   |                439 |                             12 |                            111 |                            215 |                          2.73 |                         25.28 |                         48.97 |                         33 |
| 2025_JanOct |                406 |                             12 |                            105 |                            199 |                          2.96 |                         25.86 |                         49.01 |                         33 |
| 2026_JanOct |                363 |                             18 |                            101 |                            191 |                          4.96 |                         27.82 |                         52.62 |                         31 |

## Important interpretation
2025 full year has 12 months, 2026 Jan-Oct has 10 months.
Use the 2025 Jan-Oct segment for apples-to-apples length.
Exit reasons are empirical from 1m replay; this test does not
prove market microstructure caused the profitability change.
Price data is the same archive used to SELECT these exact settings.
No independent holdout; no margin/liquidation/funding models.
