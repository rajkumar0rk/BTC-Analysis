# Independent Big-Winner external discovery — 2026-11-20 16:42 IST

Status: INCONCLUSIVE; no BTC screening backtest launched, no profitability claim.

## Completed source discovery
Web searches: `github crypto trend following strategy python funding carry breakout backtest open source`, `site:github.com/chickenopoulos/strategy-library crypto strategy`.

- https://github.com/chickenopoulos/strategy-library — includes `Momentum RSI in Crypto - Trading Research Hub, Substack.ipynb`, `Regime-based Breakout in Crypto.ipynb`, and market-wide mean reversion. The former has a distinct RSI momentum thesis relative to RSI2 reversal, but exact code, source SHA, licensing, and reproducible execution rules remain to be checked before acceptance. The latter two overlap existing breakout/regime work and require differential analysis. No self-reported results accepted.
- https://github.com/gistrec/trade-lab — public `tsmom` and `pma_ratio` strategies, walk-forward and DSR; developer explicitly states conservative DSR about 0.037, not strong statistical validation. Potential source for multi-horizon time-series momentum; check source version and license.
- https://github.com/PravarP11/multi-timeframe-trend-retest-strategy — EMA retest, ADX and pyramiding, MIT license claimed; strong overlap with BTC-Analysis Stage13/24. Do not test without demonstrable novelty.
- https://github.com/0xpg/crypto-breakouts — daily multi-lookback breakout, next-open target, cost; overlap with existing Donchian/Stage17, not selected.

## Internal novelty reference
Read `codex/STRATEGY_NOVELTY_GATE.md` from this branch: Stage13 multi-timeframe pullback, Stage24 retest, Stage25 momentum, and Stage17 breakout context prevent relabeling those as new mechanisms.

## Execution limitation and next action
The available GitHub `fetch_commit_workflow_runs` tool explicitly filters to pull-request-triggered runs, so its empty result for commit `ea5f005c162265496c5c6ab618aa8912f94b5bc0` does **not** verify push-triggered Actions status. This is a visibility limitation, not proof a job failed. No new candidate is approved yet because exact source rules and license have not been verified. Next iteration: fetch original external RSI momentum notebook source and license, record source SHA, compare signal against Stage25, then implement original rules on an isolated branch with a push-triggered BTC2025 zero-slippage screen, commission 0.05% per side and GST 18%. Only if positive after those modeled costs, freeze and stress 0.5 and 5 BTC price points/side. Funding UNMODELED; spread/impact unavailable. Do not touch main, other schedules or live accounts.
