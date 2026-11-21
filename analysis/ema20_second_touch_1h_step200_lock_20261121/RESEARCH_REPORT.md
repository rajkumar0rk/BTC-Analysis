# 1H Supertrend + EMA20 second touch: step-up profit lock every 200 BTC points

This models the user-defined step lock — NOT 200-point trailing gap or 1-point continuous trailing.
**Exploratory model only**: two fabricated within-1m OHLC paths; not historically verified tick-level execution.
At entry 80000, reaching 80200 locks 80200; reaching 80300 does not move it; reaching 80400 locks 80400; a later 80399 trade triggers exit. Reverse for shorts.

| Synthetic 1m path | Asset | Trades | Net model return | Win rate | Profit factor | Max floating DD | Profitable months | Equity at/below zero? |
|---|---|---:|---:|---:|---:|---:|---:|---|
| O-H-L-C | BTCUSD | 113 | 10.06065% | 99.115% | 2.1083 | 57.7298% | 14/22 | False |
| O-H-L-C | ETHUSD | 170 | 30.8171% | 100.0% | None | 104.6468% | 18/22 | True |
| O-L-H-C | BTCUSD | 113 | 9.00028% | 99.115% | 2.0011 | 57.7298% | 14/22 | False |
| O-L-H-C | ETHUSD | 170 | 28.49207% | 100.0% | None | 104.6425% | 17/22 | True |

## Precise rules and serious limitations
- No fixed TP, ATR trailing, or stop BEFORE first +200 profit point.
- After first milestone, locked profit increments only in exact gross-price steps of +200, +400, +600, etc.
- Exit on first reversal BELOW the most recently locked level for a long (ABOVE for short); simulated first breach 1 BTC price point, not a 1-point trailing distance.
- ETH milestones and illustrative breach increments are scaled to its entry price divided by previous closed BTC 1m price.
- A stop held at the current market price is not a traditional resting stop; implementation requires subsequent tick-based breach detection and market execution. Real fills may be lower than locked level.
- 1m candles cannot reveal the order of activation, milestone, and 1-point retracement; O-H-L-C and O-L-H-C are NOT real historical ticks, and not rigorous worst/best bounds.
- Model includes 0.05% per-side taker + GST 18%, 0.02% adverse slippage and 1x evolving model equity from $1000 for each asset; excludes funding, margin liquidation, true spread, latency, LOB.
- Historical 2026 has been repeatedly researched, not pristine validation; an open position is forcibly marked at the dataset end only for accounting.

Artifacts: summary.csv, monthly_mark_to_market.csv, trade_ledger.csv.gz, quality.json.
