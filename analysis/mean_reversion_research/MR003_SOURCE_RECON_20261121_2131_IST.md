# MR-003 candidate source reconstruction — 2026-11-21 21:31 IST

Status: SOURCE RULES RECOVERED; NOVELTY UNRESOLVED; NO BACKTEST LAUNCHED. Do not treat as completed experiment.

Original author: zevrichards; repository https://github.com/zevrichards/freqtrade-strategies ; source https://github.com/zevrichards/freqtrade-strategies/blob/main/MeanReversion.py ; imported source https://github.com/zevrichards/freqtrade-strategies/blob/main/regime_filter.py . Source files read directly via GitHub connector on 2026-11-21. Immutable upstream commit SHA and exact license remain unverified: do NOT copy implementation or claim source-pinned reproducibility yet.

Publisher's own comment: bear Oct 2025–Jun 2026, 18 pairs, 4h, -5.3%, 7.77% drawdown. This is not BTCUSD-only or independently verified, and no PF, trade count, costs, or BTC-specific return was supplied. No local result exists.

Exact defaults observed: Freqtrade LONG-only 4h; 210-candle warmup; pandas_ta BB(close,20,2) lower band; RSI(close,14)<32; volume greater than SMA(volume,20) and >0; ADX14 >12 and <25; absolute close-vs-EMA200 percentage <15%; get_regime() == RANGING. Exit signal disabled; ROI tiers {0min:3%,60min:2%,180min:1%,360min:0.5%}, stoploss -5%; no trailing. All signals evaluated on completed 4h bars, next eligible 1m open if adapted to Delta BTC. Original Freqtrade stop/ROI fill semantics must be reproduced, including stop-first and gap-aware handling.

Crucial imported regime precedence: RANGING initially when ADX14<20 OR abs(close-EMA200)/EMA200<3%; later BEAR overrides when price<EMA200, EMA50<EMA200, RSI<50, ADX>20; BULL overrides when price>EMA200, RSI>50, ADX>20; EARLY_BULL overrides when price>EMA200, close five bars ago <= EMA200 five bars ago, RSI rising vs three bars ago, RSI>45. Thus a simple ADX<20 filter is NOT source-faithful. The intersection with ADX>12 and <25 is subtle and must be reproduced exactly.

Novelty gate: this is a BB+RSI oversold entry closely related to MR-001 and prior Stage19/23 envelope/RSI studies. Added ADX regime, EMA200 proximity, and above-average volume may be an incremental hypothesis, not automatically NEW. Need compare exact older scripts and completed reports and obtain upstream immutable commit/license before approval. Given partial overlap, no experiment launched here. No parameter tuning and no source code execution.

Reproduction hazards: Freqtrade ROI tiers are in minutes even though timeframe is 4h; intrabar 1m fill and entry-bar stop checks essential. Original was multi-pair spot and its stated bear results cannot be transferred to BTC perpetual futures. Zero assumed slippage does not remove 0.05% per-side taker fee plus 18% GST; funding unmodeled. First January 2025 IST month incomplete from 2025-01-01 00:00 UTC source start.

Next feasible step: pin upstream commit and license; resolve exact novelty versus Stage19/23/24; if approved, implement source-faithful BTC 1m 4h-completed-bar replay with sequential NAV and launch a real GitHub Actions job. Otherwise mark SKIP and source a genuinely distinct mechanism. Existing MR-002 completed historical result remains rejected (run 44911975169).
