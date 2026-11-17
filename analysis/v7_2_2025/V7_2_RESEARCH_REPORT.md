# V7.2 — BTC longer-term trend following (2025)

**Experimental backtest, not a proven edge. No 2026 data.**

## Fixed, causal rules
- Daily direction: completed daily close above/below EMA20; EMA20 above/below EMA50 and slopes in the same direction across 3 days.
- 4H confirmation: completed close above/below EMA20, with EMA20/EMA50 aligned.
- Breakout entry: completed 1H close breaks previous 12 completed 1H high/low; close in outer 25% of range.
- Pullback entry: 1H touches EMA20 and closes back through it beyond previous 1H high/low.
- Enter at next 1M OPEN; weekdays IST only for new entries. One position at a time per variant.
- Initial stop: 2×4H ATR14, minimum 250, maximum 1,000 BTC price points; checked on every 1M candle.
- Exit A: completed 4H close opposite EMA20 OR completed daily close opposite EMA20.
- Exit B: completed 4H close beyond the previous 10 4H candle high/low OR completed daily close opposite EMA20.
- Max holding 10 days. No fixed take profit. Stop checked with conservative gap fill.
- Costs: taker 0.05% per side + 18% GST on trading fees, 5 BTC points adverse slippage each side.

## Results by variant

| Entry | Exit | Trades | Win rate | Net points | Months positive | Realized 1,000+ point wins | Avg hours |
|---|---|---:|---:|---:|---:|---:|---:|
| breakout | ema | 52 | 13.46% | -14656.39 | 1/10 | 5 | 26.1 |
| breakout | structure | 49 | 12.24% | -11860.75 | 2/10 | 5 | 30.7 |
| pullback | ema | 60 | 13.33% | -15538.07 | 3/10 | 6 | 24.4 |
| pullback | structure | 50 | 14.0% | -11131.51 | 3/10 | 7 | 36.9 |

## Monthly net points (after modeled costs)

| Month | Breakout/EMA | Breakout/Structure | Pullback/EMA | Pullback/Structure |
|---|---:|---:|---:|---:|
| 2025-03 | -6609.95 | -6609.95 | -3322.61 | -4410.75 |
| 2025-04 | -8557.5 | -8860.82 | -10178.65 | -7697.73 |
| 2025-05 | -1032.12 | -1097.41 | 534.86 | 3923.52 |
| 2025-06 | -1155.82 | -1155.82 | 907.89 | 907.89 |
| 2025-07 | -3506.83 | 1417.64 | -1089.55 | -1323.37 |
| 2025-08 | -3437.62 | -3437.62 | -1145.48 | -1145.48 |
| 2025-09 | -1159.17 | -2282.51 | -4118.49 | -3725.74 |
| 2025-10 | -333.69 | -333.69 | -523.27 | -523.27 |
| 2025-11 | 15565.89 | 14929.01 | 10412.78 | 10441.8 |
| 2025-12 | -4429.58 | -4429.58 | -7015.55 | -7578.38 |

## Limitations
- These are modeled BTC price-point results for a 1-BTC-equivalent position, NOT USD account P&L; actual margin, financing and liquidation are not modeled.
- Funding, L1 depth, market impact, live slippage and execution outages excluded.
- Four variants were compared on the same 2025 development window: do not treat the best as out-of-sample proof.
- Exit month determines monthly realized P&L; forced year-end closure has no January 2026 data.
- Profitability in all 10 months is a goal, not an assumption.

