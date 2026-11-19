# Daily-profit hunt — 2026-11-20 02:25 IST — new genuine microstructure-data feasibility test

Status: INCONCLUSIVE FOR NEW MICROSTRUCTURE STRATEGY; NO BACKTEST / NO TRADES. Previous vol-of-vol study remains REJECTED (run 44558873365). This is a data-availability falsification gate, not a return claim.

## New verified source (read-only main; no other research branches changed)
Source `analysis/forward_microstructure/snapshots/2026-11-19.jsonl`, blob SHA `441a3bb48d97c2b328d7daeaa582d70f94a48ec5`, introduced/updated by `d812ddd8d1a6c56152c663284d0b4d08f9e3e8b8`. Parsed all **3** JSONL observations successfully. Each includes actual REST top-20 bid/ask snapshots for Delta India BTCUSD perpetual and Binance BTCUSDT spot; observations are not synchronized tradeable quotes, and USD versus USDT are different denominations.

| UTC capture | Delta best bid USD | Binance spot best ask USDT | (Delta bid - spot ask)/spot ask, bps |
|---|---:|---:|---:|
| 2026-11-19 02:12:32.817 | 62834.00 | 62866.42 | -5.15697 |
| 2026-11-19 10:22:11.386 | 63824.50 | 63853.56 | -4.55104 |
| 2026-11-19 19:05:54.546 | 62731.00 | 62749.85 | -3.00399 |

This is **not** a valid arbitrage profit/loss calculation. It excludes currency conversion, both venues' commissions, GST, borrowing/financing, hedging, funding settlement, exchange latency, simultaneous executable fills, and order-book depth normalization. The three observations are separated by hours; they cannot establish intraday fill probability, daily net profitability, or 2025/2026 historical robustness. Funding is explicitly tagged `hourly_rate_proxy_not_settled_payment`, `funding_settlement_cashflow_verified=false`, and `maker_fill_verified=false`. Binance funding endpoint reports HTTP 451. Snapshot maximum reported single-venue HTTP latency is 433, 636 and 705 ms respectively.

## Decision and next exact experiment
Do NOT manufacture 22 months of historical L1 books, settled funding, or daily returns from three forward samples. Genuine forward data now exist (a material change since the previous execution gate), but are insufficient to pre-register a statistically testable passive-spread or cross-venue strategy. Continue collecting timestamped synchronized depth/trade/settled-funding observations over enough days, with tick/lot normalization, fees, FX conversion and reliable execution timing. First research test must quantify executable **gross** edge before any parameter selection, using BTC only. Frozen ETH secondary validation follows only if the BTC signal is supported by actual data. No new GitHub Actions backtest was launched; workflow-run discovery via the available connector still filters PR events only. No notification or change to automation cadence.

Novelty decision: NEW DATA SOURCE, STRATEGY NOT YET TESTABLE; not a rebranding of earlier carry proxies or maker-spread feasibility tests. Source is forward-only and cannot validate Jan 2025–Oct 2026 retrospectively.
