# Novelty check — Supertrend 15m bullish line-touch

Date: 2026-11-22. Decision: **NEW** (rule-specific descriptive comparison; not independent OOS evidence).

## Deterministic predeclared experiment
- Delta Exchange India BTCUSD perpetual 1m archived candles, aggregate 15 complete minutes to each UTC-aligned 15m signal bar.
- Long only. Supertrend standard ATR(10) Wilder RMA, factor 3. A bullish **closed** 15m flip opens an eligible cycle; never fill on the signal bar.
- During subsequent 15m blocks, rest a buy-limit at the last **closed** bullish Supertrend line (the frozen line known at the start of the 15m block). Fill on the first 1m low touching it; a downward opening gap fills at 1m open, not an invented line fill. Exactly one entry per bullish cycle, no overlapping positions. No shorts, no reentries in the same cycle, no time/day filter.
- Fixed limit take-profit at +0.2%, +0.4%, +0.5%, +0.6%, or +1.0% of entry's assumed effective filled price. Execute TP from **subsequent** 1m bar highs only, never award same-1m favorable sequencing after the low touch.
- Stop only upon the close of the 15m block BELOW the Supertrend support published at its start, or a completed bearish Supertrend flip; exit at the next available 1m open. The 15m close check is not a hard intrabar stop. A 1m TP may occur before a later closing stop.
- One hypothetical 1 BTC-equivalent price-unit position. Standard conservative taker fee 0.05% per side + 18% GST; 5 USD adverse slippage per side. No funding, liquidation, spread/depth, exchange contract rounding or account leverage model. Report gross and net price points, trade/target/stop counts, positive months, drawdown, profit factor.
- Chronological split: 2025 baseline, Jan–Jun 2026 check, Jul–Oct 2026 previously researched recheck. Nov 2026 incomplete and separated. Months in IST, assigned by exit month. Recheck continuity and completed 15m bars; fail rather than fabricate gap data.

## Closest completed experiments and incremental difference
- `scripts/research_trend_pullback_breakout_stage13.py`, `analysis/institutional_discovery_stage13_4h_1h_15m/`: 4H/1H/15M multi-regime price-action breakout; **not** 15m Supertrend line-touch limit/reversal-close stop.
- `analysis/institutional_discovery_stage24_structure_monthly10/RESEARCH_REPORT.md` on `research/stage24-monthly10`: 15m squeeze/breakout/retest with next 1m entry, 1m stop and structural R targets; materially different indicator-support limit with delayed 15m-close stop.
- `analysis/independent_stage25_hourly_trend/RESEARCH_REPORT.md` on `research/stage25-new-trend`: 1H momentum/inside-bar/Donchian direction; not Supertrend support retest.
- GitHub main code search for `supertrend` found no direct identical strategy.

## Limitations
The older novelty gate mentions the formerly missing 2026-10-31 UTC data. The current `data/delta_india/BTCUSD/1m/manifest.json` (2026-11-22) reports 44,640/44,640 observations in October; the new run must independently validate the expected continuous timeline and disclose any exclusion. No pristine holdout remains; five TP choices are multiple comparisons. The 1m OHLC path does not establish tick-level ordering, resting-limit queue position, spread or fills.