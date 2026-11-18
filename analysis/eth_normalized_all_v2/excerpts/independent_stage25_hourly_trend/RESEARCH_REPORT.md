# Stage25 -- Independent BTC 1H trend and momentum search for +10% NET each month

## Model and validity
Original Delta ETHUSD raw 1m data. Closed 1H signals, optional 4H trend confirmation
option, next 1m open fill, 1m stop-first replay, monthly flattening.
One position at a time per model. Model selection 2025 only;
2026 checked without adjustment. Fees 0.05% per side, 18% GST
and 5 USD adverse slip each side (no funding/bid-ask modeled).

**All-22-month winners: 0 of 2880 modeled account configurations**

## 2025-ranked candidates (2026 scores shown only for audit)
| pattern        |   lookback | hour_align   |   stop_atr | exit_policy   |   max_hold_minutes |   risk_pct |   max_leverage |   trades_total |   wins |   losses |   2025_months_ge10 |   2026_months_ge10 |   2025_positive |   2026_positive |   worst_2025_pct |   worst_2026_pct |   net_2025_pct |   net_2026_pct |   max_trade_close_drawdown_pct |
|:---------------|-----------:|:-------------|-----------:|:--------------|-------------------:|-----------:|---------------:|---------------:|-------:|---------:|-------------------:|-------------------:|----------------:|----------------:|-----------------:|-----------------:|---------------:|---------------:|-------------------------------:|
| donchian_break |         12 | False        |        1.5 | trail_2R      |               2880 |          2 |              3 |            516 |    187 |      329 |                  5 |                  2 |               7 |               6 |         -23.8953 |         -23.7477 |       19.626   |      -13.5622  |                        58.8114 |
| donchian_break |         12 | False        |        1.5 | trail_2R      |               2880 |          2 |              5 |            516 |    187 |      329 |                  5 |                  2 |               7 |               6 |         -23.8953 |         -23.6921 |       18.5252  |      -10.5251  |                        58.5883 |
| donchian_break |         12 | False        |        1.5 | trail_2R      |               2880 |          2 |             10 |            516 |    187 |      329 |                  5 |                  2 |               7 |               6 |         -23.8953 |         -23.6921 |       18.5252  |      -10.2415  |                        58.45   |
| momentum_accel |         12 | False        |        1.5 | trail_3R      |               2880 |          2 |              3 |            409 |    123 |      286 |                  5 |                  2 |               7 |               6 |         -24.4351 |         -13.7217 |        0.78844 |       18.304   |                        51.4733 |
| momentum_accel |         12 | False        |        1.5 | trail_3R      |               2880 |          2 |              5 |            409 |    123 |      286 |                  5 |                  2 |               7 |               6 |         -24.4351 |         -13.2199 |        0.24787 |       18.5417  |                        51.2528 |
| momentum_accel |         12 | False        |        1.5 | trail_3R      |               2880 |          2 |             10 |            409 |    123 |      286 |                  5 |                  2 |               7 |               6 |         -24.4351 |         -13.2199 |        0.24787 |       17.637   |                        51.4028 |
| momentum_accel |         12 | False        |        1.5 | trail_2R      |               2880 |          2 |              3 |            443 |    155 |      288 |                  5 |                  2 |               6 |               5 |         -24.6347 |         -18.3734 |       -4.86373 |       -6.16616 |                        56.8605 |
| momentum_accel |         12 | False        |        1.5 | trail_2R      |               2880 |          2 |              5 |            443 |    155 |      288 |                  5 |                  2 |               6 |               5 |         -24.6347 |         -19.7166 |       -5.37399 |       -5.24691 |                        56.8447 |
| momentum_accel |         12 | False        |        1.5 | trail_2R      |               2880 |          2 |             10 |            443 |    155 |      288 |                  5 |                  2 |               6 |               5 |         -24.6347 |         -20.0834 |       -5.37399 |       -5.36479 |                        56.7005 |
| donchian_break |         24 | False        |        1.5 | trail_2R      |               2880 |          2 |              3 |            391 |    139 |      252 |                  4 |                  2 |               9 |               3 |         -20.487  |         -15.4497 |       13.2235  |      -17.7367  |                        50.7064 |
| donchian_break |         24 | False        |        1.5 | trail_2R      |               2880 |          2 |              5 |            391 |    139 |      252 |                  4 |                  2 |               9 |               3 |         -20.487  |         -15.4497 |       12.6577  |      -16.1611  |                        49.8675 |
| donchian_break |         24 | False        |        1.5 | trail_2R      |               2880 |          2 |             10 |            391 |    139 |      252 |                  4 |                  2 |               9 |               3 |         -20.487  |         -15.4497 |       12.6577  |      -16.1604  |                        49.7    |

## 2025-only selected candidate monthly actual net account P&L
| month_ist   |   return_pct |   trades |   wins |   losses |   flat |
|:------------|-------------:|---------:|-------:|---------:|-------:|
| 2025-01     |     -3.00894 |       21 |      7 |       14 |      0 |
| 2025-02     |      2.2668  |       26 |     10 |       16 |      0 |
| 2025-03     |     13.2946  |       19 |      8 |       11 |      0 |
| 2025-04     |    -14.9279  |       30 |      8 |       22 |      0 |
| 2025-05     |     43.6164  |       20 |     12 |        8 |      0 |
| 2025-06     |     14.6468  |       27 |      9 |       18 |      0 |
| 2025-07     |    -23.8953  |       31 |      8 |       23 |      0 |
| 2025-08     |     12.8623  |       29 |     15 |       14 |      0 |
| 2025-09     |     -3.93181 |       23 |      7 |       16 |      0 |
| 2025-10     |     15.8819  |       28 |     13 |       15 |      0 |
| 2025-11     |    -22.557   |       27 |      7 |       20 |      0 |
| 2025-12     |      2.6265  |       19 |      7 |       12 |      0 |
| 2026-01     |      2.70414 |       25 |      9 |       16 |      0 |
| 2026-02     |      1.18671 |       23 |      9 |       14 |      0 |
| 2026-03     |     -9.13205 |       20 |      6 |       14 |      0 |
| 2026-04     |      2.39839 |       19 |      9 |       10 |      0 |
| 2026-05     |    -23.7477  |       24 |      6 |       18 |      0 |
| 2026-06     |     -8.44753 |       23 |      5 |       18 |      0 |
| 2026-07     |      5.51963 |       21 |     10 |       11 |      0 |
| 2026-08     |     22.3854  |       16 |      6 |       10 |      0 |
| 2026-09     |     17.089   |       22 |     10 |       12 |      0 |
| 2026-10     |    -15.3189  |       23 |      6 |       17 |      0 |

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
