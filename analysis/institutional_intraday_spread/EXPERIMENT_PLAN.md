# Intraday institutional-style research: cross-venue spread convergence

Status: **pre-registered design**; generated before executing the next historical study.

## Objective
Look for *temporary relative-value dislocations*, NOT predict BTC up/down. Buy 0.001 BTC spot (Binance BTCUSDT) and short one 0.001 BTC lot of Delta India BTCUSD perpetual when the perpetual premium is abnormally wide compared with its own trailing 12-hour average. Close BOTH legs when the spread returns to the signal-time average or at a short predefined deadline.

## Real archive, no fabricated L2
- Delta 1m BTCUSD futures OPEN/CLOSE from this repo, January 2025-Oct 2026.
- Independently download official Binance BTCUSDT **1m spot** ZIP files October 2025–September 2026, verify contiguous UTC timestamps, record ZIP SHA256.
- Delta BTCUSD and Binance BTCUSDT are *not fungible prices*. USD/USDT basis, INR margin, venue accessibility/transfer risk, and execution frictions remain unmeasured; this is **indicative relative-value backtesting**, not confirmed arbitrage.
- No historical synchronized bid/ask or order-book queues. OHLCV trade-price proxies cannot confirm fills.

## Fixed parameter grid (do not optimize on the recheck window)
- 1m/5m/15m **completed-bar signals**, all fills on later 1m OPEN only. Signal occurs when the signal-time perp-minus-spot CLOSE spread exceeds its trailing 720 completed 1m spread closes (rolling mean plus 2 or 3 rolling standard deviations). Rolling baseline explicitly shifts one minute, excluding the signal bar.
- Optional economic hurdle: excess premium above rolling mean must be at least 0% (exploratory) or 0.32% of BTC spot (approximately the assumed round-trip two-leg taker fee hurdle).
- Enter at next 1m OPEN for both legs; close at next 1m OPEN after spread closes back at or below the original signal-time mean, or after fixed maximum **15, 60 or 120 minutes**. One position at a time in each scenario. No forward-looking spread state on entry.
- Exclude all entries whose whole possible holding window intersects 00:00, 08:00 or 16:00 UTC, using the *known calendar*, so unmodeled funding settlements cannot contribute; do not attribute rate-proxy cashflows.
- Evaluate 36 predeclared decision rules (3 signal TF × 2 z-score thresholds × 2 fee-hurdle gates × 3 max holds).
- Baseline: Delta BTCUSD taker 0.05% each side +18% GST on fees, Binance spot fee illustrative 0.10% each side, 5 points adverse slippage on each of four leg executions. Also 15-point per-execution adverse slippage + 5% annual spot capital carry; and gross-before-fees diagnostic only.
- Evaluate every configuration separately in 2025 Q4, 2026 H1 and 2026 Q3. 2026 Q3 is previously investigated in other studies and is NOT independent virgin OOS.
- Outputs: complete per-scenario ledger, all configurations including zero-trade configurations, net P&L in USD/USDT-proxy and % initial spot value, trades, win rate, profit factor, average spread capture, median hold, maximum sequential realized drawdown, gross vs net breakdown, excludable calendar counts, source provenance.
- Actual maker profitability is not testable without quote/trade-by-trade historical data. Do not treat theoretical spread gross returns as executable P&L or model invented maker fills.
- Do not promote 1-year in-sample selection as a persistent tradable edge; genuine later out-of-sample and synchronized quote-depth data required.

Research only, no live trading orders. Preserve failures and no-trade scenarios.
