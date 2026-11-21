# Trend Following family — initial novelty gate (2026-11-21)

Status: **SKIP proposed duplicate baseline; no historical backtest was run in this iteration.** Research family branch only; main unchanged.

## Sources inspected
- User repository novelty gate: `codex/STRATEGY_NOVELTY_GATE.md`, main.
- Prior work: `analysis/convex_trend_acceleration_20261119/RESEARCH_REPORT.md` at `research/convex-trend-acceleration-20261119`; 64 trend-acceleration models, zero qualifying, top BTC models PF roughly 1.1–1.28, not robust; some results use a funding proxy, not actual cashflows.
- Public strategy candidate: https://github.com/xy3293/crypto-strategy-backtest — publicly documented `supertrend_4h` (Wilder ATR(10), multiplier 3, close crossing active line), `ema_ribbon_4h` (EMA 9/21/55 alignment, 2 ATR stop), and `adx_trend_4h` (ADX14 >25 and directional DI, exit ADX<20 or DI flips, 2 ATR stop). Source HEAD SHA/license not yet pinned; README is a discovery lead, NOT a reproducible verified source snapshot.
- Other references: https://github.com/coding-kitties/PyIndicators and https://github.com/NJiHin/TA_Chandelier (indicator implementations, not proof of profitable strategies).

## Proposed first baseline — 4H SuperTrend(10,3)
Closed 4H SuperTrend bullish => long on next eligible 1m open; bearish => short. Flip exits and reverses at next eligible 1m open; 3 ATR emergency stop from entry as documented by source. Risk size and cost handling must be fixed and recorded before execution. No hindsight candle fills. This is a candidate for source verification only.

## Novelty decision
**SKIP**: plain 4H SuperTrend flip with ATR stop is economically equivalent to the previously studied SuperTrend/trend variants and does not pass the required novelty gate merely because source repository differs. Do not launch a redundant backtest.

## Incremental research direction
Seek a **causally distinct trend persistence mechanism** such as confirmed multi-day Hurst regime persistence with a Chandelier exit, but only if source code, licensing, indicator lag, parameter semantics and prior-art comparison establish a material difference from Stage13, Stage25 and prior trend-acceleration work. Avoid inventing a rule to force novelty. Preserve a source-faithful original baseline and predeclare small improvements separately.

## Data and cost constraints
Require authentic Delta India BTC 1m bars, completed higher-timeframe aggregation, zero-slippage first screen, 0.05% fee per side and GST 18% of fees; funding UNMODELED absent real rates. Historical dataset October 2026 has a documented 1440 UTC-minute gap, and 2026 has been inspected previously. Do not claim 22 complete profitable IST months without resolving coverage. Preserve all losses and all monthly NAV.

## Next concrete execution
1. Inspect Stage25 and other source-level trend runs to decide whether a proposed persistence gate is genuinely different.
2. Pin a reproducible licensed source implementation and verify exact rules against its README.
3. Commit an approved novelty check, source-faithful implementation and workflow; run BTC2025 genuine historical screen, archive original trades and 2025 monthly NAV.
4. Freeze any selected settings before later BTC2026 and ETH rechecks; only then run slippage stress.
