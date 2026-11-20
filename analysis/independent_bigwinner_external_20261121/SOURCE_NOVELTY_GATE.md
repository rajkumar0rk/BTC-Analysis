# Big-winner external discovery gate — 2026-11-21 01:52 IST

Status: SOURCE SCREEN / NO NEW BACKTEST LAUNCHED. This is not a completed experiment or profitable finding.

## Precedence and continuity
Prior study: independent bipower continuous, GitHub run 44679516754 completed, zero BTC closed trades; REJECT for insufficient observations. Its prior audit commit is 59a26c3e2a197d39b497a8496cb2bdc9f8f76a79. No rerun justified. Earlier volume-absorption run 44635317067 was negative; do not revive.

## External discovery searches (public)
- Search: `site:github.com/aurelien-gentile/turtle-strategy-backtest strategy rules`
- Search: `site:github.com/EstebanSP23/crypto_systematic_research breakout`
- Source: https://github.com/aurelien-gentile/turtle-strategy-backtest ; classic hourly BTC Turtle long-only 20/10-style Donchian, 2ATR stop, risk-based sizing and optional pyramiding. Repository itself reports failure to beat HODL over 2023–2024. Source commit/license must be checked before adaptation. NOVELTY: SKIP as ordinary Donchian breakout overlaps prior institutional Stage 19/24 and independent Quattro research; not a novel economic mechanism.
- Source: https://github.com/EstebanSP23/crypto_systematic_research ; Quattro BTC 4H Donchian 20, daily EMA200 rising, 4-unit pyramiding, 2ATR trailing and 5% catastrophe stop. Published +1107% / 94 trades are self-reported and NOT validated here. Quattro was already covered in `research/asymmetric-quattro-independent-20261118`. NOVELTY: SKIP duplicate.
- Source: https://github.com/0xpg/crypto-breakouts ; independent daily long-only 10/20/40/80-day high recency signal, 5-day freshness, four-signal averaged exposure, 2.5% per-coin cap, next open fill, 10bps one-way turnover. Distinct exposure-weighting mechanism, but no defined per-trade bounded stop and designed for multi-coin breadth. On single BTC it does not directly meet small-bounded-loss big-winner objective; adaptation would change core strategy. SOURCE CANDIDATE — HOLD, do not misrepresent as a screened backtest. Exact source SHA, license, and rule-for-rule reproduction remain unverified.
- Source: https://github.com/JuRose99/turtle_strategy ; 20/10 ATR Turtle on CSI 300 ETF, 32 trades in eight years, self-reported PF 1.98. Not BTC evidence, duplicates known Donchian. SKIP.
- Source: https://github.com/EstebanSP23/crypto_systematic_research/tree/main/2_strategies/02_apex_no_pyramid ; 1080 4H-bar high, SMA50>SMA200, volume>1.5x mean. Multi-asset source and previously studied Donchian family. SKIP until genuinely different incremental hypothesis.
- Sources not yet reviewed: chickenopoulos/strategy-library, arxiv.org/abs/2009.12155, TradingView and Freqtrade. This is a partial discovery cycle, not a claim of comprehensive search.

## BTC-first backtest gate
No accepted sufficiently novel, reproducible, licensed, small-loss-convex strategy in this pass. Therefore **no native BTC backtest was launched**; no zero-slippage PASS or live-ready result. Next cycle must finish source license/commit/rules and novelty checks before implementing one source. If accepted: original rule-for-rule BTC 2025, 0 slippage both sides with 0.05% taker commission each side and 18% GST; only positive credible screen gets frozen 0.5-point and 5-point per-fill BTC adverse slippage, then ETH scaled sensitivity. Historical funding UNMODELED; 2025 Jan IST start and Oct 2026 gap qualified; never claim 22 fully covered months without data.

## Execution blocker
No executable new hypothesis cleared the novelty and reproducibility gate in this iteration. This is a candidate-selection blocker, **not** a GitHub Actions failure. Do not create an empty workflow or fabricate results. Prioritize identifying an original, complete external rule set with bounded downside, source license and version. No main/live changes.
