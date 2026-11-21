# 1H EMA20 second touch: activation +200, 1-point peak reversal

**These figures are hypothetical 1m OHLC path assumptions, NOT confirmed tick-data backtests.**
The real tick order can produce significantly different exit count, fill price, profit and drawdown.

| 1m synthetic path | Asset | Trades | Net model return | Win rate | PF | Max MTM DD | Profitable months | Equity <= 0? |
|---|---|---:|---:|---:|---:|---:|---:|---|
| O-H-L-C | BTCUSD | 113 | 16.11849% | 99.115% | 2.683 | 57.6729% | 14/22 | False |
| O-H-L-C | ETHUSD | 170 | 43.64592% | 100.0% | None | 104.6488% | 18/22 | True |
| O-L-H-C | BTCUSD | 113 | 16.71276% | 99.115% | 2.7362 | 57.6729% | 14/22 | False |
| O-L-H-C | ETHUSD | 170 | 41.44575% | 100.0% | None | 104.6488% | 18/22 | True |

## Explicit execution limitations
- Stop arms at +200 BTC-price points; then it exits on first 1 BTC-point pullback from peak, no fixed TP.
- For shorts, trail follows low+1. ETH both distances percent-scaled at entry from previous BTC close.
- 1m OHLC O-H-L-C versus O-L-H-C are TWO invented continuous paths consistent with OHLC, not measured historical ticks or rigorous upper/lower performance bounds.
- A trade can encounter many >$1 reversals inside one minute that 1m OHLC cannot reveal; actual orderbook fills might be worse and trailing update latency matters.
- No fixed stop before activation: exposures and liquidation can be severe. Forced end-of-sample close is accounting-only.
- 1x assumed notional, $1000 starting equity per asset, 0.05% taker each side plus 18% GST, 0.02% adverse slippage each side.
- 2026 archive previously researched; not a pristine untouched validation.

See summary.csv, monthly_mark_to_market.csv, trade_ledger.csv.gz, quality.json.
