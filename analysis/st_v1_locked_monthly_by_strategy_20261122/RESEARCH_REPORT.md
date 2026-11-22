# Locked V1.0 BTCUSD ST: actual exit-month strategy breakdown

Original frozen strategy. Line Touch: SL 0.75%, TP 1.5%,
1h close>EMA20 + rising EMA20, Volume>=1, ATR%>=.2,
profit stop locked at +0.4% following a PRIOR completed
1m candle reaching +1%. Bullish Flip: SL 3%, TP .5%,
last completed 1h RSI14>=50, vol<=.8, ATR%>=.2.
Both LONG ONLY, one concurrent, one per ST bullish cycle,
and original ST closing exit. All estimates include fees/GST/slippage.

## Totals by strategy inside the combined one-position portfolio
| strategy           |   trades |   wins |   2025_net_points |   2026_JanOct_net_points |   total_net_points |
|:-------------------|---------:|-------:|------------------:|-------------------------:|-------------------:|
| Line Touch         |       67 |     33 |          10252.1  |                  3563.92 |           13816.1  |
| Bullish Flip       |       18 |     17 |           4301.21 |                   982.35 |            5283.56 |
| Combined portfolio |       85 |     50 |          14553.4  |                  4546.27 |           19099.6  |

## 2025 monthly by individual component
| exit_month_ist   |   line_touch |   bullish_flip |   combined_points |   total_trades |
|:-----------------|-------------:|---------------:|------------------:|---------------:|
| 2025-01          |      2747.97 |         385.36 |           3133.33 |              8 |
| 2025-02          |       820.7  |         363.91 |           1184.61 |              3 |
| 2025-03          |      1689.03 |         340.25 |           2029.28 |              6 |
| 2025-04          |      1278.82 |         320.51 |           1599.33 |              2 |
| 2025-05          |      1155.13 |        1176.83 |           2331.96 |              6 |
| 2025-06          |      -293.78 |           0    |           -293.78 |              1 |
| 2025-07          |      1217.26 |         444.79 |           1662.05 |              3 |
| 2025-08          |     -1596.71 |           0    |          -1596.71 |              4 |
| 2025-09          |      -374.31 |         860.59 |            486.28 |              3 |
| 2025-10          |      3360.91 |         408.97 |           3769.88 |              3 |
| 2025-11          |       327.91 |           0    |            327.91 |              2 |
| 2025-12          |       -80.79 |           0    |            -80.79 |              2 |

## Jan-Oct 2026 monthly by individual component
| exit_month_ist   |   line_touch |   bullish_flip |   combined_points |   total_trades |
|:-----------------|-------------:|---------------:|------------------:|---------------:|
| 2026-01          |      -304.57 |         677.45 |            372.88 |              6 |
| 2026-02          |        12.75 |         254.85 |            267.6  |              3 |
| 2026-03          |     -1449.97 |        -466.72 |          -1916.69 |              5 |
| 2026-04          |      1328.47 |           0    |           1328.47 |              3 |
| 2026-05          |      1686.73 |           0    |           1686.73 |              3 |
| 2026-06          |       543.11 |           0    |            543.11 |              2 |
| 2026-07          |       -17.23 |         230.94 |            213.71 |              4 |
| 2026-08          |      1422.57 |           0    |           1422.57 |              5 |
| 2026-09          |      1159.38 |         285.83 |           1445.21 |              9 |
| 2026-10          |      -817.32 |           0    |           -817.32 |              2 |

## Execution and caveats
P&L reported in BTC price points for 1 BTC-equivalent position.
No funding, margin liquidation, leverage account ROI, order latency.
History used to optimize strategy; not true out-of-sample.
