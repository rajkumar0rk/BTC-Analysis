# BTC + ETH 1H EMA20/Supertrend — 1 / 0.1 trailing sensitivity
All other strategy settings matched in old versus new, isolated 100x test model.
Source: verified raw Delta India one-minute files Jan 2025-Oct 2026.

| Asset | Trailing | Fee policy | Net USD | PF | Trades | Positive months | Liquidations |
|---|---|---|---:|---:|---:|---:|---:|
| BTC | old | no offer | -92.67 | 0.3573 | 132 | 0/22 | 0 |
| BTC | old | assumed offer | -92.58 | 0.6088 | 226 | 0/22 | 0 |
| BTC | new | no offer | -91.38 | 0.2514 | 182 | 0/22 | 0 |
| BTC | new | assumed offer | -91.03 | 0.5636 | 530 | 1/22 | 0 |
| ETH | old | no offer | -92.88 | 0.5477 | 154 | 0/22 | 0 |
| ETH | old | assumed offer | -95.99 | 0.7556 | 322 | 0/22 | 0 |
| ETH | new | no offer | -90.11 | 0.5619 | 259 | 0/22 | 0 |
| ETH | new | assumed offer | -93.17 | 0.7271 | 428 | 2/22 | 0 |

See summary.json and per-asset trade/monthly CSVs.

## Limitations
- BTC 0.1 point is below assumed 0.5 venue tick, so distance 0.5 is used in executable simulation. A hypothetical 0.1 BTC stop is not submitted.
- 1m OHLC cannot establish exact order fill, spread, intraminute path, stop latency or mark-price liquidation.
- Fee model 0.05% taker per side and 18% GST; alternative scenario assumes 27m Scalper offer on every eligible historical trade; entitlement not verified.
- Synthetic isolated 100x liquidation/preliq proxy is not current shared Delta Demo Portfolio Margin.
- No funding, spread, latency, slippage or options premium are modeled.
- Trade entry on next 1m OPEN after fully closed 1h signal; matching historical data spans Jan 2025-Oct 2026; excludes Nov partial month.
- Changing trailing by such tiny amounts produces near-zero gross winners relative to fees; this is not evidence of an investable strategy.
- All changes research branch only; running VPS bots have not been modified.
