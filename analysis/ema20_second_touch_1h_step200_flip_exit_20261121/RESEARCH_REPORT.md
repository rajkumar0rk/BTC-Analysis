# 1H Supertrend + EMA20 second touch: 200-point step-lock AND Supertrend flip exit

This models the user-defined step lock — NOT 200-point trailing gap or 1-point continuous trailing.
**Exploratory model only**: two hypothetical within-1m OHLC paths; Supertrend flips exit at next hourly opening, but strict step-lock fills cannot be verified without historical ticks.
At entry 80000, reaching 80200 locks 80200; reaching 80300 does not move it; reaching 80400 locks 80400; a later 80399 trade triggers exit. Reverse for shorts.

| Synthetic 1m path | Asset | Trades | Step-lock exits | Supertrend flip exits | Losing flip exits | Net model return | Win rate | PF | Max floating DD | Positive months | Equity at/below zero? |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| O-H-L-C | BTCUSD | 361 | 280 | 81 | 81 | -55.96383% | 77.5623% | 0.2808 | 56.4553% | 0/22 | False |
| O-H-L-C | ETHUSD | 344 | 300 | 44 | 44 | -37.92586% | 87.2093% | 0.4778 | 41.311% | 7/22 | False |
| O-L-H-C | BTCUSD | 361 | 280 | 81 | 81 | -56.50019% | 77.5623% | 0.265 | 57.0351% | 0/22 | False |
| O-L-H-C | ETHUSD | 344 | 299 | 45 | 45 | -41.30784% | 86.9186% | 0.4269 | 44.2553% | 7/22 | False |

## Precise rules and serious limitations
- NO fixed TP or ATR trailing. Before first +200 price point, there is no protective stop, BUT a confirmed Supertrend flip always exits.
- Exit on CONFIRMED 1H Supertrend reversal at first 1m open of next 1H candle. Do not exit using the still-forming flip candle.
- After first milestone, locked profit increments only in exact gross-price steps of +200, +400, +600, etc.
- Exit on first reversal BELOW the most recently locked level for a long (ABOVE for short); simulated first breach 1 BTC price point, not a 1-point trailing distance.
- ETH milestones and illustrative breach increments are scaled to its entry price divided by previous closed BTC 1m price.
- A stop held at the current market price is not a traditional resting stop; implementation requires subsequent tick-based breach detection and market execution. Real fills may be lower than locked level.
- 1m candles cannot reveal the order of activation, milestone, and 1-point retracement; O-H-L-C and O-L-H-C are NOT real historical ticks, and not rigorous worst/best bounds.
- Model includes 0.05% per-side taker + GST 18%, 0.02% adverse slippage and 1x evolving model equity from $1000 for each asset; excludes funding, margin liquidation, true spread, latency, LOB.
- Historical 2026 has been repeatedly researched, not pristine validation; an open position is forcibly marked at the dataset end only for accounting.

Artifacts: summary.csv, monthly_mark_to_market.csv, trade_ledger.csv.gz, quality.json.
