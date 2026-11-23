# Novelty check — EMA9/21 1m quality upgrade (pre-run)

Decision: **PARTIAL OVERLAP — approved differential on existing 1-minute EMA9/21 family**, not a wholesale new strategy discovery.

## Current reference
- `scripts/research_ema9_21_daily_quality_1m.py`, artifacts from GitHub Action run 45157193892: weekday-only EMA9/21 1m reclaim, 5m/15m aligned, VWAP, ADX and volume; 343 trades, net -4.078% (10% notional exposure), two winning months across 2025-01..2026-10.
- `scripts/research_wide_monthly_stage23.py` / Stage23 report: 5m EMA pullback/sweep/breakout families, with 1m exit replay.
- `scripts/research_retest_reclaim_stage4.py` / Stage4: 5m retest after hourly expansion, not 1m EMA9/21 confirmation.
- `scripts/research_one_trade_every_day_200.py`: forces an entry each NY day and fixed 200 point goal.
- Stage24 branch: 15m structure; Stage25 branch: 1h trend. Entry causality and horizons differ.

## Precise incremental hypothesis
Poor baseline expectancy is caused by microscopically tight 1m 5-bar stops/targets relative to the round-trip taker fee (~0.118% of notional). **Preserve EMA9/21 1m as entry trigger, but test a wider 5-minute ATR risk unit and momentum/breakout confirmation**. This specifically challenges baseline exit scale and microstructure entry without redoing general 5m pattern search.

## Pre-registered (before any run)
- BTCUSD 1m Delta India archive, 2025-01 through 2026-10, November tail only to close open positions.
- Weekday IST *signal AND entry* only, one max entry per IST weekday, zero-trade days allowed; only one position at a time; long & short.
- `CROSS`: EMA9 crosses above/below EMA21 on 1m, 5m+15m confirmed EMA9/21 align, signal candle directional, 1m volume >=1.1x SMA20, 1m 14-bar ADX >=18 and matching DI direction.
- `PULLBACK_BREAK`: 1m EMA9>EMA21 (reverse short), EMA21 sloping over 3 bars, prior 1-5 bars touched EMA21, close breaks last 5 *previous* candle highs/lows with directional body, 5m+15m align, 1m volume>=1.1x mean20, ADX>=18, matching DI.
- `TREND_BREAK`: 1m EMA9>21 (reverse), 5m+15m align, direction closes past prior 15-minute high/low, volume >=1.3x mean20, 1m candle body >=55% of high/low range, ADX>=22, DI align.
- `RECLAIM`: baseline 1m EMA21 touch + EMA9 close-cross, EMA21 slope, 5m/15m align; **remove VWAP**, volume>=1.1x SMA20, ADX>=18, DI aligned. Compare loosened reclaim with known baseline.
- Entry signal available at completed 1m close; trade next 1m open with adverse 5-pt slippage on each side, 0.05% fee each side +18% GST; run 0.5-pt sensitivity only after primary selection.
- Session: full weekday vs 13:30-23:30 IST (London/US overlap proxy; ignores seasonal DST shifts deliberately).
- Risk: 5m ATR14 of *completed* 5m bars, entry-stop distance = 1.5 or 2.5 x ATR5; stop static, TP 2R or 3R; risk/target determined from next-minute entry fill, not from future candle; stop-first when both hit one 1m candle; gap-aware stop; maximum holding 720 minutes (no overnight wait), time-out fill at next minute OPEN. 4 signals x 2 sessions x 2 stop sizes x 2 RR = 32 fixed variants.
- No daily or weekly future selection, no intra-day retrospective 'best' signal; first eligible signal while flat wins. No same-day re-entry even if stopped out.
- Account results: 10% notional (1x), compounded on trade close, 2025 used to rank; 2026 recheck reported without retuning. Profit factor, 22 IST months, win/loss, gross, cost, drawdown. Funding not modeled (<= 12-hour holds, can cross funding).
- Compare old baseline as reference; avoid interpreting best of 32 as validation. Report any failure prominently. Never force exactly one trade per day.
- Source quality: new 1m manifest 2025-01..2026-10 declares complete 1m continuity. Old Codex note about missing 2026-10-31 is superseded by updated 2026-11-22 archive; runner still checks gaps.
