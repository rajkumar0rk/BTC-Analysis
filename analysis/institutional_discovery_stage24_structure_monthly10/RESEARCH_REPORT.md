# Stage24 -- BTC structure breakout / reversal search for +10% NET each month

## Model and validity
Delta India BTCUSD 1m archive. 15m closed-bar patterns, 1h trend alignment
option, next 1m open fill, 1m stop-first replay, monthly flattening.
One position at a time per model. Model selection 2025 only;
2026 checked without adjustment. Fees 0.05% per side, 18% GST
and 5 USD adverse slip each side (no funding/bid-ask modeled).

**All-22-month winners: 0 of 1920 modeled account configurations**

## 2025-ranked candidates (2026 scores shown only for audit)
| pattern       |   lookback | hour_align   |   stop_atr | exit_policy   |   max_hold_minutes |   risk_pct |   max_leverage |   trades_total |   wins |   losses |   2025_months_ge10 |   2026_months_ge10 |   2025_positive |   2026_positive |   worst_2025_pct |   worst_2026_pct |   net_2025_pct |   net_2026_pct |   max_trade_close_drawdown_pct |
|:--------------|-----------:|:-------------|-----------:|:--------------|-------------------:|-----------:|---------------:|---------------:|-------:|---------:|-------------------:|-------------------:|----------------:|----------------:|-----------------:|-----------------:|---------------:|---------------:|-------------------------------:|
| squeeze_break |          8 | False        |        2.5 | trail_3R      |                720 |          2 |              3 |            289 |     99 |      190 |                  5 |                  1 |               5 |               3 |        -23.1424  |         -16.4892 |        4.93965 |      -26.8864  |                        47.5384 |
| squeeze_break |          8 | False        |        2.5 | fixed_3R      |                720 |          2 |              3 |            290 |    102 |      188 |                  4 |                  2 |               6 |               4 |        -23.1424  |         -15.4921 |       -1.68462 |      -22.8463  |                        50.4434 |
| squeeze_break |          8 | False        |        2.5 | trail_3R      |                720 |          2 |              5 |            289 |     99 |      190 |                  4 |                  2 |               6 |               3 |        -27.0768  |         -19.2249 |       -7.72193 |      -36.1007  |                        59.2922 |
| squeeze_break |          8 | False        |        2.5 | fixed_3R      |                720 |          2 |              5 |            290 |    102 |      188 |                  4 |                  2 |               6 |               3 |        -27.0768  |         -17.6356 |       -9.20424 |      -30.8474  |                        60.6934 |
| squeeze_break |          8 | False        |        2.5 | trail_3R      |                720 |          1 |              5 |            289 |     99 |      190 |                  3 |                  1 |               6 |               2 |        -14.8896  |         -10.2325 |       -2.3394  |      -20.7393  |                        35.6796 |
| squeeze_break |         24 | False        |        2.5 | trail_2R      |                720 |          2 |              3 |            140 |     55 |       85 |                  3 |                  1 |               5 |               4 |         -9.12305 |         -10.077  |        1.26059 |      -13.7937  |                        33.0479 |
| squeeze_break |          8 | False        |        2.5 | trail_2R      |                720 |          2 |              5 |            295 |    115 |      180 |                  3 |                  2 |               5 |               3 |        -16.4306  |         -18.9171 |       -2.60032 |      -43.763   |                        61.8085 |
| retest        |          8 | True         |        2.5 | trail_3R      |                720 |          2 |              3 |            193 |     63 |      130 |                  3 |                  1 |               4 |               2 |        -14.6439  |         -12.416  |      -29.29    |      -14.2856  |                        41.198  |
| retest        |          8 | True         |        2.5 | trail_3R      |                720 |          2 |              5 |            193 |     63 |      130 |                  3 |                  1 |               4 |               2 |        -16.2481  |         -12.8839 |      -35.1967  |      -19.6642  |                        48.9521 |
| squeeze_break |         24 | False        |        2.5 | fixed_3R      |                720 |          2 |              5 |            139 |     48 |       91 |                  2 |                  1 |               7 |               6 |        -18.5425  |         -13.2053 |      -14.7107  |       -7.36354 |                        45.2814 |
| squeeze_break |          8 | False        |        2.5 | fixed_3R      |                240 |          2 |              3 |            308 |    118 |      190 |                  2 |                  1 |               6 |               2 |         -8.6552  |         -16.0367 |       10.8194  |      -29.7373  |                        43.3048 |
| squeeze_break |          8 | False        |        2.5 | fixed_3R      |                240 |          2 |              5 |            308 |    118 |      190 |                  2 |                  1 |               6 |               3 |        -10.2973  |         -20.1024 |        1.21396 |      -40.0444  |                        53.5535 |

## 2025-only selected candidate monthly actual net account P&L
| month_ist   |   return_pct |   trades |   wins |   losses |   flat |
|:------------|-------------:|---------:|-------:|---------:|-------:|
| 2025-01     |     8.19272  |       13 |      8 |        5 |      0 |
| 2025-02     |     3.87145  |       10 |      5 |        5 |      0 |
| 2025-03     |    -7.48835  |        9 |      1 |        8 |      0 |
| 2025-04     |   -14.8896   |       13 |      0 |       13 |      0 |
| 2025-05     |     1.04958  |       14 |      4 |       10 |      0 |
| 2025-06     |    -2.14125  |       17 |      4 |       13 |      0 |
| 2025-07     |    -7.17396  |       16 |      5 |       11 |      0 |
| 2025-08     |    10.3908   |        6 |      4 |        2 |      0 |
| 2025-09     |    -0.706318 |       18 |      8 |       10 |      0 |
| 2025-10     |    13.6964   |       15 |      8 |        7 |      0 |
| 2025-11     |    10.7438   |       12 |      6 |        6 |      0 |
| 2025-12     |   -12.8793   |       17 |      2 |       15 |      0 |
| 2026-01     |    -1.48934  |       14 |      5 |        9 |      0 |
| 2026-02     |     7.62731  |       14 |      8 |        6 |      0 |
| 2026-03     |    -3.07457  |       12 |      3 |        9 |      0 |
| 2026-04     |    -0.762366 |       12 |      5 |        7 |      0 |
| 2026-05     |    -2.68474  |       10 |      3 |        7 |      0 |
| 2026-06     |    11.6536   |       14 |      7 |        7 |      0 |
| 2026-07     |    -8.30049  |       12 |      2 |       10 |      0 |
| 2026-08     |    -5.34281  |       17 |      6 |       11 |      0 |
| 2026-09     |   -10.2325   |       12 |      2 |       10 |      0 |
| 2026-10     |    -8.19953  |       12 |      3 |        9 |      0 |

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
