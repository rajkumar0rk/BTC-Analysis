# High-PF external candidate — execution handoff, 2026-11-20 16:23 IST

Status: BLOCKED BEFORE NATIVE BACKTEST. No simulated results or workflow run claimed.

Source reviewed: https://github.com/pooriag/crypto-strategy-backtest (author pooriag; MIT code, Coin Metrics data CC BY-NC 4.0; exact external commit NOT YET PINNED). Public README says daily long-only spot time-series momentum (11 lookbacks 7–365 days), MA crossover (17 fast/slow combinations), optional 40% annualized volatility target and 10% no-trade band. Signal decided at daily close earns next-day return. Original research uses Coin Metrics reference daily data and 10 bps commission + 5 bps slippage per turnover unit; its published combined BTC/ETH results are NOT Delta India futures evidence. README explicitly reports no statistically convincing risk-adjusted advantage over buy-and-hold. External code version, exact momentum rule and MA pair must be read from pinned src/cryptobt/signals.py before implementing; do not substitute invented details.

Novelty: Stage25 hourly trend and earlier MA research overlap. A daily long-only rule-for-rule reproduction might be a useful *external replication*, not a novel strategy. Keep distinct from other schedules.

Required next execution:
1. Pin upstream SHA, inspect signals.py/backtest.py and license; record exact entry/exit and original parameters.
2. Locate genuine Delta India BTC candles in this repo and audit Jan 2025 IST start, Oct 2026 completeness and daily resampling.
3. Implement isolated branch-scoped push-triggered GitHub Actions screening on BTC 2025, **0 slippage both sides**, 0.05% taker fee each side plus 18% GST on fees. Include raw trades, NAV and monthly PF with stop-first/no-lookahead. Do not execute untrusted upstream installation scripts.
4. Only positive credible BTC-2025 screen passes to frozen BTC 2026 / ETH and $0.5 / $5 per-side slippage stress. Funding UNMODELED, spread/order book/impact/margin UNVERIFIED. No live deployment.

Execution blocker in THIS iteration: no exact pinned external strategy source or verified native dataset path had been established, so launching a purported rule-for-rule backtest would be fabricated. GitHub connector exposes file reads but no general directory listing or branch-wide push-run listing. This file records the exact incomplete prerequisites, not a completed test. Next check must resolve these and run code, not repeat novelty review.
