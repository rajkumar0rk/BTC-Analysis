# Stage25 -- Independent BTC 1H trend and momentum search for +10% NET each month

## Model and validity
Original Delta ETHUSD raw 1m data. Closed 1H signals, optional 4H trend confirmation
option, next 1m open fill, 1m stop-first replay, monthly flattening.
One position at a time per model. Model selection 2025 only;
2026 checked without adjustment. Fees 0.05% per side, 18% GST
and 5 USD adverse slip each side (no funding/bid-ask modeled).

**All-22-month winners: 0 of 360 modeled account configurations**

## 2025-ranked candidates (2026 scores shown only for audit)
| pattern        |   lookback | hour_align   |   stop_atr | exit_policy   |   max_hold_minutes |   risk_pct |   max_leverage |   trades_total |   wins |   losses |   2025_months_ge10 |   2026_months_ge10 |   2025_positive |   2026_positive |   worst_2025_pct |   worst_2026_pct |   net_2025_pct |   net_2026_pct |   max_trade_close_drawdown_pct |
|:---------------|-----------:|:-------------|-----------:|:--------------|-------------------:|-----------:|---------------:|---------------:|-------:|---------:|-------------------:|-------------------:|----------------:|----------------:|-----------------:|-----------------:|---------------:|---------------:|-------------------------------:|
| donchian_break |         12 | False        |        2.5 | fixed_2R      |                720 |          2 |              3 |              1 |      1 |        0 |                  0 |                  0 |               1 |               0 |                0 |                0 |        0.65328 |              0 |                              0 |
| donchian_break |         12 | False        |        2.5 | fixed_2R      |                720 |          2 |              5 |              1 |      1 |        0 |                  0 |                  0 |               1 |               0 |                0 |                0 |        0.65328 |              0 |                              0 |
| donchian_break |         12 | False        |        2.5 | fixed_2R      |                720 |          2 |             10 |              1 |      1 |        0 |                  0 |                  0 |               1 |               0 |                0 |                0 |        0.65328 |              0 |                              0 |
| donchian_break |         12 | False        |        2.5 | fixed_3R      |                720 |          2 |              3 |              1 |      1 |        0 |                  0 |                  0 |               1 |               0 |                0 |                0 |        0.65328 |              0 |                              0 |
| donchian_break |         12 | False        |        2.5 | fixed_3R      |                720 |          2 |              5 |              1 |      1 |        0 |                  0 |                  0 |               1 |               0 |                0 |                0 |        0.65328 |              0 |                              0 |
| donchian_break |         12 | False        |        2.5 | fixed_3R      |                720 |          2 |             10 |              1 |      1 |        0 |                  0 |                  0 |               1 |               0 |                0 |                0 |        0.65328 |              0 |                              0 |
| donchian_break |         12 | False        |        2.5 | trail_2R      |                720 |          2 |              3 |              1 |      1 |        0 |                  0 |                  0 |               1 |               0 |                0 |                0 |        0.65328 |              0 |                              0 |
| donchian_break |         12 | False        |        2.5 | trail_2R      |                720 |          2 |              5 |              1 |      1 |        0 |                  0 |                  0 |               1 |               0 |                0 |                0 |        0.65328 |              0 |                              0 |
| donchian_break |         12 | False        |        2.5 | trail_2R      |                720 |          2 |             10 |              1 |      1 |        0 |                  0 |                  0 |               1 |               0 |                0 |                0 |        0.65328 |              0 |                              0 |
| donchian_break |         12 | False        |        2.5 | trail_3R      |                720 |          2 |              3 |              1 |      1 |        0 |                  0 |                  0 |               1 |               0 |                0 |                0 |        0.65328 |              0 |                              0 |
| donchian_break |         12 | False        |        2.5 | trail_3R      |                720 |          2 |              5 |              1 |      1 |        0 |                  0 |                  0 |               1 |               0 |                0 |                0 |        0.65328 |              0 |                              0 |
| donchian_break |         12 | False        |        2.5 | trail_3R      |                720 |          2 |             10 |              1 |      1 |        0 |                  0 |                  0 |               1 |               0 |                0 |                0 |        0.65328 |              0 |                              0 |

## 2025-only selected candidate monthly actual net account P&L
| month_ist   |   return_pct |   trades |   wins |   losses |   flat |
|:------------|-------------:|---------:|-------:|---------:|-------:|
| 2025-01     |     0        |        0 |      0 |        0 |      0 |
| 2025-02     |     0.653279 |        1 |      1 |        0 |      0 |
| 2025-03     |     0        |        0 |      0 |        0 |      0 |
| 2025-04     |     0        |        0 |      0 |        0 |      0 |
| 2025-05     |     0        |        0 |      0 |        0 |      0 |
| 2025-06     |     0        |        0 |      0 |        0 |      0 |
| 2025-07     |     0        |        0 |      0 |        0 |      0 |
| 2025-08     |     0        |        0 |      0 |        0 |      0 |
| 2025-09     |     0        |        0 |      0 |        0 |      0 |
| 2025-10     |     0        |        0 |      0 |        0 |      0 |
| 2025-11     |     0        |        0 |      0 |        0 |      0 |
| 2025-12     |     0        |        0 |      0 |        0 |      0 |
| 2026-01     |     0        |        0 |      0 |        0 |      0 |
| 2026-02     |     0        |        0 |      0 |        0 |      0 |
| 2026-03     |     0        |        0 |      0 |        0 |      0 |
| 2026-04     |     0        |        0 |      0 |        0 |      0 |
| 2026-05     |     0        |        0 |      0 |        0 |      0 |
| 2026-06     |     0        |        0 |      0 |        0 |      0 |
| 2026-07     |     0        |        0 |      0 |        0 |      0 |
| 2026-08     |     0        |        0 |      0 |        0 |      0 |
| 2026-09     |     0        |        0 |      0 |        0 |      0 |
| 2026-10     |     0        |        0 |      0 |        0 |      0 |

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
