# TSMOM component novelty decision — 2026-11-22

Source: Engineer Investor, CRYPTO_SPEC.md, pinned commit de27263d630303d32fe0df3d5b688e1b8a27350a, https://github.com/engineerinvestor/systematic-trend-following-with-managed-futures/blob/de27263d630303d32fe0df3d5b688e1b8a27350a/CRYPTO_SPEC.md

This source specifies daily-calendar 30/90/365-day sign of trailing log return, lagged 60-day COM EWMA volatility, 40% per-instrument normalization and portfolio-level 10% volatility targeting, with long/short and long/flat comparisons. The original 1/3/12-month ensemble cannot be reproduced for January 2025 without 2024 historical daily reference prices. BTCUSD perpetual OHLC is not the author's reference series and funding is unmodeled.

Closest prior art: analysis/independent_stage25_hourly_trend/ (research/stage25-new-trend), analysis/institutional_discovery_stage13_4h_1h_15m/, and analysis/convex_trend_acceleration_20261119/. Stage25 studies hourly acceleration; this study's differentiator is multi-week lagged time-series momentum on seven-day calendar with low-turnover, daily decisions. Not a Donchian breakout. Decision: PARTIAL OVERLAP — approved differential for a component experiment only; do NOT label a 30/90-only test as faithful reproduction of the full 30/90/365 ensemble.

Predeclared component comparisons: 30D sign momentum long/short, 90D sign momentum long/short, and 30D long/flat. Signals computed from fully closed daily candles, filled no earlier than next minute open. Apply 0.05% notional fee per side plus 18% GST; first screen zero slippage, no funding. Any missing warmup months are explicitly untestable; do not infer 22/22 months. BTC2025 discovery only; freeze settings before BTC2026 and ETH checks. Reject if after-cost PF <=1 or positive-month fraction is not materially better than prior trend baselines. No leverage/martingale. Never execute source scripts.

Note: Source license must be independently confirmed before copying code; this research uses original implementation of publicly described mathematical signals, not copied code.
