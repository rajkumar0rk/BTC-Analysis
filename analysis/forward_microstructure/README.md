# Forward BTC market microstructure observations

**Started:** 2026-11-17 UTC. Read-only API snapshots. No orders or account keys.

## What is collected
- Delta India BTCUSD perpetual public L2 best bid/ask and top 20 levels, with native contract sizes.
- Binance BTCUSDT spot public L2 best bid/ask and top 20 levels, with BTC sizes.
- Delta FUNDING:BTCUSD hourly funding-rate candles (rate proxies, **not actual funding paid**).
- Binance USD-M BTCUSDT published funding events when endpoint is accessible.
- Cross-venue best-bid-minus-best-ask spread as a **non-executable indication**.

Samples append to `analysis/forward_microstructure/snapshots/YYYY-MM-DD.jsonl` every ~15 minutes via GitHub Actions; actual timing depends on runner scheduling. Every row includes source latency, any errors, original book levels, and timestamp.

## Initial live smoke test
On 2026-11-17, both order-book sources worked and Delta funding candles were available. Binance USD-M funding events returned HTTP 451 from the GitHub runner: this is recorded as an error and not silently imputed.

## Important limitations
- **Market making:** 15-minute REST snapshots cannot reconstruct quote queues, order arrival/cancellation, or fills. Use a continuously running websocket recorder on a VPS, synchronized trades, and account-specific fees before claiming a maker edge.
- **Funding:** rate candles and published event rates are not actual account settlement cashflows; private authenticated settlement history would be required to reconcile payments.
- **Arbitrage:** Delta BTCUSD is USD-denominated, Binance BTCUSDT is USDT-denominated. Cross-venue transfer, exchange access, collateral, fill risk, order-book liquidity, and USD/USDT conversion can wipe out apparent differences.
- **Backtesting:** no pre-start order-book history can be reconstructed from snapshots.
- **Sampling:** GitHub scheduled jobs can be delayed/skipped; timestamp gaps must be explicitly checked before analysis.
- Avoid adding secrets or exchange trading credentials to the repository.

See `.github/workflows/collect-btc-forward-microstructure.yml` and `scripts/collect_market_microstructure.py`.
