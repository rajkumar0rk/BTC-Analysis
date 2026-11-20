# 2026-11-20 15:19 IST — Quattro novelty disposition and execution gate

Status: **SKIP ORIGINAL QUATTRO AS DUPLICATE CORE; NO BACKTEST RUN / NO PROFIT CLAIM.**

## Verified evidence
- Source: Esteban Segura, MIT-licensed 2026 Quattro Donchian, commit 4fe0d2934b3bff5e3ad329897de3b51382446684, source blob 30f76a04e1ecc9a04574f6c0d5c84c3c315c4b85; full source and fill defects in SOURCE_AUDIT_20261120_1451.md.
- BTC-Analysis main: scripts/research_swing_donchian_stage17.py, 4H Donchian close breakouts, 2 ATR initial stop, higher-timeframe trailing stop, monthly NAV and historical BTC study. Also novelty gate identifies Stage24 15m breakouts and Stage25 hourly trend. This is the nearest prior economically equivalent entry family.
- External Quattro distinctive implementation: 4H 20-bar close breakout, prior completed daily EMA200 price filter, long-only, four-unit +0.5 ATR pyramid, common 2 ATR stop and account catastrophe stop. **Incremental execution/risk hypothesis**, not an independently novel economic signal. The user's rule prohibits treating pyramiding, parameter shifts or renamed breakouts as a novel signal without demonstrable differential.
- Source-original fill logic has optimistic intrabar ordering, gap-through prices, absent commissions/GST/funding and 20x cap; a literal source-performance comparison is not executable without documenting corrections. No zero-slippage BTC screening run exists for this candidate.
- Current branch head at inspection: 7d68c51ad7b908bd6445ad34dbadca8d600318d3. Repo Actions listing was accessible; no pending Quattro workflow exists on this branch. Do not confuse other schedules' runs with this task.

## Decision
**SKIP** Quattro as a *new independent strategy* due to core Donchian breakout overlap with Stage17. Its distinctive pyramid could be considered only in a separately preregistered incremental study if prior Stage17 trade-ledger evidence supplies a causal, material reason; do not run parameter-only rebranding now. Published Quattro returns are not Delta India evidence.

## Next iteration
Select an independently sourced economic mechanism with non-overlapping forward-observable entry logic. Search public GitHub/TradingView/academic/Freqtrade sources; compare against novelty gate and other branches read-only. For accepted NEW signal, commit exact source provenance/rules/license and dedicated branch-scoped workflow, launch actual BTC-2025 zero-slippage commission+GST screening and verify run/artifacts. Do not stress slippage until a credible positive screen. Funding UNMODELED. No other schedule, main, or live account modification.
