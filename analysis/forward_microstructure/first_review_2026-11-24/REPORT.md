# Forward BTC Arbitrage Feasibility — 24 November 2026

**No strategy profit is claimed.** Based only on observed forward REST snapshots.
The report is a 1-week feasibility check, not an executable market-making or arbitrage backtest.

## Data quality

| Metric | Result |
|---|---:|
| First snapshot | 2026-11-17T14:39:56.224000+00:00 |
| Last snapshot | 2026-11-23T21:36:21.633000+00:00 |
| Unique snapshots | 22 |
| Approx expected snapshots | 634 |
| Coverage % | 3.47 |
| Quotes from both exchanges with <=5s receive skew | 22 |
| Gaps >35m | 21 |
| Maximum gap (min) | 731.1657 |
| Minimum 300 synchronized quotes reached | False |
| Delta funding rate available | 22 |
| Binance published funding available | 0 |

## Quote and indicative basis

| Measurement | Result |
|---|---:|
| Median Delta bid/ask spread (points) | 0.5 |
| Median Binance spot bid/ask spread (points) | 0.01 |
| Median Delta bid minus Binance ask (points) | -29.39 |
| Entry quotes with Delta bid above Binance ask (%) | 0.0 |

## Hypothetical two-leg basis marks after modeled taker fees

LONG Binance spot / SHORT Delta perp; entry on one snapshot, exit at nearest later snapshot.
Greedy nonoverlapping sampled pairs; **not trade fills, not realized P&L**.
| Marking window | Paired snapshots | Positive after model costs | Mean net points proxy | Median fee points proxy |
|---|---:|---:|---:|---:|
| 15 minutes | 0 | 0 (None%) | None | None |
| 60 minutes | 0 | 0 (None%) | None | None |

## Collection / modeling issues

- API error (binance_usdm_btcusdt_published_funding_events): 22 snapshot(s)
- **Data threshold not met (300 synchronized samples)**; do not interpret small sample rates.

## Decision

**Do not deploy arbitrage or maker trading based on these snapshots.**
We can inspect whether quoted basis merits higher-frequency WebSocket collection.
Market making requires depth/order-flow/trade ticks with live queue/fill modeling.
Funding-based carry requires actual settlement cashflows and hedging/financing reconciliation.
No 2025 L2 backfill, no 2026 directional strategy, and no guarantee of a positive month.

## Modeling assumptions

- Binance USDT and Delta USD prices are not fungible; quote basis results are NOT executable.
- Fills, depth available at quoted size, Delta contracts, exchange access and capital transfer not verified.
- Delta funding is an hourly rate proxy; account-level settlement data unavailable.
- 15-minute snapshots miss transient microstructure and maker order queue dynamics.
- Per-side Binance spot taker fee assumed 0.10%; Delta taker 0.05% plus 18% GST; slippage assumes 5 price points per execution.
- This analysis is only a first data-collection feasibility study; insufficient for claims of consistent monthly profits.
