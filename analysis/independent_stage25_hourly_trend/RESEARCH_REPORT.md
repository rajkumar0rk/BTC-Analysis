# Stage25 -- Independent BTC 1H trend and momentum search for +10% NET each month

## Model and validity
Original Delta BTCUSD raw 1m data. Closed 1H signals, optional 4H trend confirmation
option, next 1m open fill, 1m stop-first replay, monthly flattening.
One position at a time per model. Model selection 2025 only;
2026 checked without adjustment. Fees 0.05% per side, 18% GST
and 5 USD adverse slip each side (no funding/bid-ask modeled).

**All-22-month winners: 0 of 2880 modeled account configurations**

## 2025-ranked candidates (2026 scores shown only for audit)
| pattern          |   lookback | hour_align   |   stop_atr | exit_policy   |   max_hold_minutes |   risk_pct |   max_leverage |   trades_total |   wins |   losses |   2025_months_ge10 |   2026_months_ge10 |   2025_positive |   2026_positive |   worst_2025_pct |   worst_2026_pct |   net_2025_pct |   net_2026_pct |   max_trade_close_drawdown_pct |
|:-----------------|-----------:|:-------------|-----------:|:--------------|-------------------:|-----------:|---------------:|---------------:|-------:|---------:|-------------------:|-------------------:|----------------:|----------------:|-----------------:|-----------------:|---------------:|---------------:|-------------------------------:|
| inside_bar_break |         24 | False        |        1.5 | fixed_3R      |               2880 |          2 |             10 |            295 |     97 |      198 |                  3 |                  1 |               5 |               5 |         -15.8114 |         -19.139  |       -16.1344 |      -10.1067  |                        56.1142 |
| momentum_accel   |         24 | False        |        2.5 | trail_3R      |               2880 |          2 |              3 |            285 |     98 |      187 |                  3 |                  0 |               5 |               6 |         -16.6239 |         -16.6583 |       -16.7738 |       -9.04512 |                        43.9618 |
| momentum_accel   |         24 | False        |        2.5 | trail_3R      |               2880 |          2 |              5 |            285 |     98 |      187 |                  3 |                  0 |               5 |               6 |         -17.278  |         -16.9426 |       -16.3567 |      -12.9282  |                        45.3343 |
| momentum_accel   |         24 | False        |        2.5 | trail_3R      |               2880 |          2 |             10 |            285 |     98 |      187 |                  3 |                  0 |               5 |               6 |         -17.4376 |         -16.9426 |       -16.5181 |      -13.4426  |                        45.4398 |
| inside_bar_break |         24 | False        |        1.5 | fixed_3R      |               2880 |          2 |              5 |            295 |     97 |      198 |                  3 |                  1 |               4 |               5 |         -15.8114 |         -18.7037 |       -17.6177 |       -8.27579 |                        56.4514 |
| donchian_break   |         12 | False        |        2.5 | trail_3R      |               2880 |          2 |              5 |            391 |    125 |      266 |                  3 |                  0 |               4 |               3 |         -17.1374 |         -14.3918 |       -25.9899 |      -28.7035  |                        49.4292 |
| donchian_break   |         12 | False        |        2.5 | trail_3R      |               2880 |          2 |             10 |            391 |    125 |      266 |                  3 |                  0 |               4 |               3 |         -17.1374 |         -14.3918 |       -25.9899 |      -29.2638  |                        49.8267 |
| donchian_break   |         12 | False        |        2.5 | trail_3R      |               2880 |          2 |              3 |            391 |    125 |      266 |                  3 |                  0 |               4 |               3 |         -17.238  |         -12.761  |       -28.0187 |      -24.762   |                        47.1839 |
| momentum_accel   |         12 | False        |        2.5 | trail_3R      |               2880 |          2 |              3 |            347 |    117 |      230 |                  3 |                  0 |               4 |               5 |         -20.5791 |         -10.4641 |       -22.9196 |       -1.75512 |                        46.6307 |
| momentum_accel   |         12 | False        |        2.5 | trail_3R      |               2880 |          2 |              5 |            347 |    117 |      230 |                  3 |                  0 |               4 |               5 |         -21.3846 |         -10.7696 |       -22.7162 |       -6.70079 |                        47.9191 |
| momentum_accel   |         12 | False        |        2.5 | trail_3R      |               2880 |          2 |             10 |            347 |    117 |      230 |                  3 |                  0 |               4 |               5 |         -21.5363 |         -10.7696 |       -22.8654 |       -7.25193 |                        48.0196 |
| donchian_break   |         24 | False        |        2.5 | trail_3R      |               2880 |          2 |              5 |            319 |    104 |      215 |                  3 |                  1 |               3 |               5 |         -17.9643 |         -16.9426 |       -38.4134 |      -17.8768  |                        51.0986 |

## 2025-only selected candidate monthly actual net account P&L
| month_ist   |   return_pct |   trades |   wins |   losses |   flat |
|:------------|-------------:|---------:|-------:|---------:|-------:|
| 2025-01     |     -8.85489 |       12 |      2 |       10 |      0 |
| 2025-02     |      3.26546 |       11 |      4 |        7 |      0 |
| 2025-03     |    -11.5904  |       19 |      4 |       15 |      0 |
| 2025-04     |     -6.40296 |       18 |      6 |       12 |      0 |
| 2025-05     |     10.2815  |       11 |      5 |        6 |      0 |
| 2025-06     |     24.939   |       15 |      8 |        7 |      0 |
| 2025-07     |     21.8318  |       12 |      8 |        4 |      0 |
| 2025-08     |    -10.1802  |        9 |      2 |        7 |      0 |
| 2025-09     |      0.70436 |       16 |      5 |       11 |      0 |
| 2025-10     |    -12.6598  |       16 |      4 |       12 |      0 |
| 2025-11     |    -15.8114  |       15 |      2 |       13 |      0 |
| 2025-12     |     -3.55396 |       11 |      4 |        7 |      0 |
| 2026-01     |     -3.20718 |       14 |      5 |        9 |      0 |
| 2026-02     |      2.47233 |       13 |      4 |        9 |      0 |
| 2026-03     |     -6.82527 |       16 |      5 |       11 |      0 |
| 2026-04     |    -19.139   |       14 |      2 |       12 |      0 |
| 2026-05     |     -1.52489 |        8 |      2 |        6 |      0 |
| 2026-06     |     21.0428  |       19 |      9 |       10 |      0 |
| 2026-07     |    -12.7619  |       14 |      3 |       11 |      0 |
| 2026-08     |      4.2518  |        9 |      4 |        5 |      0 |
| 2026-09     |      1.41404 |       13 |      4 |        9 |      0 |
| 2026-10     |      9.4176  |       10 |      5 |        5 |      0 |

## Caveats
- 2026 was previously researched and is NOT a blind out-of-sample check
- October 2026 is missing all 1m candles for Oct 31 UTC and is NOT fully verified
- November 2026 is excluded because incomplete
- 2025-01 first five and a half IST hours are missing because archive starts Jan 1 UTC
- Intraminute stop versus target uses conservative stop-first
- Open stop can gap; actual stop fill can be worse than stop
- One position per strategy, no opposite position concurrency
- Month-boundary flattening closes each trade at final 1m close and pays exit costs
- Selected strategies are ranked ONLY on 2025, then checked unchanged on 2026
- Selection over many settings still overfits 2025 training
- Funding, order book spreads, queue position, impact, exchange margin and liquidation not modeled
- Small account lot size feasibility not modeled, no assurance of profitable live trading
- Drawdown sampled at trade close, not true intratrade equity lows
- Risk size and max leverage are hypothetical caps, not live trading recommendations

An in-sample historical fit is NOT evidence of future guaranteed returns.
October 2026 is an INCOMPLETE-DATA calendar month despite its completed date.
