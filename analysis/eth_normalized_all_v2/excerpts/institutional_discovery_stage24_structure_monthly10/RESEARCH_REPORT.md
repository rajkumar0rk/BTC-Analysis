# Stage24 -- BTC structure breakout / reversal search for +10% NET each month

## Model and validity
Delta India ETHUSD 1m archive. 15m closed-bar patterns, 1h trend alignment
option, next 1m open fill, 1m stop-first replay, monthly flattening.
One position at a time per model. Model selection 2025 only;
2026 checked without adjustment. Fees 0.05% per side, 18% GST
and 5 USD adverse slip each side (no funding/bid-ask modeled).

**All-22-month winners: 0 of 1920 modeled account configurations**

## 2025-ranked candidates (2026 scores shown only for audit)
| pattern   |   lookback | hour_align   |   stop_atr | exit_policy   |   max_hold_minutes |   risk_pct |   max_leverage |   trades_total |   wins |   losses |   2025_months_ge10 |   2026_months_ge10 |   2025_positive |   2026_positive |   worst_2025_pct |   worst_2026_pct |   net_2025_pct |   net_2026_pct |   max_trade_close_drawdown_pct |
|:----------|-----------:|:-------------|-----------:|:--------------|-------------------:|-----------:|---------------:|---------------:|-------:|---------:|-------------------:|-------------------:|----------------:|----------------:|-----------------:|-----------------:|---------------:|---------------:|-------------------------------:|
| breakout  |          8 | True         |        2.5 | fixed_2R      |                720 |          2 |              5 |            864 |    315 |      549 |                  4 |                  2 |               4 |               2 |        -21.4025  |         -30.6921 |      -54.3516  |       -59.533  |                        84.7604 |
| breakout  |          8 | True         |        2.5 | fixed_2R      |                720 |          2 |              3 |            864 |    315 |      549 |                  3 |                  2 |               4 |               2 |        -20.5032  |         -28.9648 |      -52.6113  |       -58.1314 |                        82.8187 |
| retest    |          8 | True         |        2.5 | fixed_2R      |                720 |          2 |              5 |            158 |     52 |      106 |                  2 |                  0 |               7 |               1 |         -7.43578 |         -13.7946 |        4.7987  |       -47.8824 |                        58.4334 |
| retest    |          8 | False        |        1.5 | fixed_3R      |                240 |          2 |              3 |            342 |    119 |      223 |                  2 |                  0 |               7 |               0 |        -16.2485  |         -16.9979 |       10.4393  |       -61.717  |                        65.5036 |
| retest    |          8 | False        |        1.5 | trail_3R      |                720 |          2 |              3 |            331 |     89 |      242 |                  2 |                  0 |               7 |               0 |        -16.6806  |         -22.4431 |       -0.72445 |       -75.5332 |                        80.0434 |
| retest    |          8 | False        |        1.5 | fixed_3R      |                240 |          2 |              5 |            342 |    119 |      223 |                  2 |                  0 |               7 |               0 |        -17.1378  |         -18.552  |       -0.96492 |       -69.3466 |                        75.2053 |
| retest    |          8 | False        |        1.5 | trail_3R      |                240 |          2 |              3 |            341 |    117 |      224 |                  2 |                  0 |               7 |               0 |        -17.6419  |         -16.9979 |        4.46722 |       -62.0068 |                        64.5169 |
| retest    |          8 | False        |        1.5 | trail_3R      |                240 |          2 |              5 |            341 |    117 |      224 |                  2 |                  0 |               7 |               0 |        -18.5164  |         -18.552  |       -6.94513 |       -69.5564 |                        74.9756 |
| retest    |          8 | True         |        2.5 | fixed_2R      |                720 |          2 |              3 |            158 |     52 |      106 |                  2 |                  0 |               6 |               1 |         -6.83276 |         -13.7946 |        3.84902 |       -45.298  |                        55.4794 |
| retest    |          8 | False        |        2.5 | fixed_3R      |                240 |          2 |              3 |            347 |    135 |      212 |                  2 |                  0 |               6 |               2 |        -10.2817  |         -18.9766 |        6.97506 |       -50.326  |                        54.2872 |
| retest    |          8 | True         |        2.5 | fixed_3R      |                720 |          2 |              5 |            157 |     45 |      112 |                  2 |                  0 |               6 |               1 |        -12.783   |         -13.7946 |        0.94528 |       -48.9439 |                        60.5901 |
| breakout  |          8 | False        |        2.5 | fixed_2R      |                720 |          2 |              3 |           1698 |    669 |     1029 |                  2 |                  0 |               6 |               1 |        -28.6187  |         -35.7884 |      -34.8994  |       -86.7277 |                        92.8854 |

## 2025-only selected candidate monthly actual net account P&L
| month_ist   |   return_pct |   trades |   wins |   losses |   flat |
|:------------|-------------:|---------:|-------:|---------:|-------:|
| 2025-01     |     0.153823 |        9 |      3 |        6 |      0 |
| 2025-02     |    -1.29637  |        6 |      2 |        4 |      0 |
| 2025-03     |     0.929977 |        5 |      2 |        3 |      0 |
| 2025-04     |    -1.77188  |        7 |      2 |        5 |      0 |
| 2025-05     |    10.7323   |        5 |      4 |        1 |      0 |
| 2025-06     |    -6.51661  |        8 |      3 |        5 |      0 |
| 2025-07     |    12.7668   |        9 |      6 |        3 |      0 |
| 2025-08     |     2.29022  |       12 |      4 |        8 |      0 |
| 2025-09     |     2.48111  |       15 |      6 |        9 |      0 |
| 2025-10     |     0.25371  |        8 |      4 |        4 |      0 |
| 2025-11     |    -5.83542  |       12 |      3 |        9 |      0 |
| 2025-12     |    -7.43578  |        7 |      2 |        5 |      0 |
| 2026-01     |    -9.50337  |       10 |      2 |        8 |      0 |
| 2026-02     |   -13.7946   |        8 |      1 |        7 |      0 |
| 2026-03     |    -4.42342  |        2 |      0 |        2 |      0 |
| 2026-04     |   -11.0084   |        5 |      0 |        5 |      0 |
| 2026-05     |   -10.6977   |        6 |      1 |        5 |      0 |
| 2026-06     |     6.58689  |        8 |      4 |        4 |      0 |
| 2026-07     |    -2.87627  |        4 |      1 |        3 |      0 |
| 2026-08     |    -8.95553  |        4 |      0 |        4 |      0 |
| 2026-09     |    -4.6218   |        2 |      0 |        2 |      0 |
| 2026-10     |    -2.1587   |        6 |      2 |        4 |      0 |

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
