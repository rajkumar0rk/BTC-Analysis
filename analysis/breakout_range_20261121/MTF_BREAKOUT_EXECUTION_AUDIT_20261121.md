# Breakout & Range — source-level execution audit (2026-11-21, third research iteration)

Status: **REJECT publisher performance as evidence; SKIP reproduction as a new strategy under novelty gate**. This is a source audit, **not a historical Delta BTC backtest**. No fees, GST, funding, slippage, verified trade ledger or independent NAV results exist for this candidate.

## Primary source and immutable observations
- Author: Maksat Narmyradov; repository: https://github.com/MAKSAT-DEL/mtf-breakout-bot
- Exact inspected source paths: `main.py` and `README.md` on the default branch, 2026-11-21. For fully immutable provenance pin a commit SHA before any later implementation.
- Publisher README claims BTC/USDT 3.2 years, 209 trades, 42.1% wins, PF 1.46, CAGR 7.4%, final $12,534. These are **publisher-only**, unverified. README also says 3.5 years in its overview, an internal inconsistency.
- Main strategy parameters in `main.py`: 50 EMA on 1h/4h/1d, require 3 aligned; prior daily high/low exceeded by 1.5% closing buffer; ADX(14)>=25; current volume>=1.2x rolling 20; ATR(14), initial 3.5 ATR stop, 2 ATR breakeven, 2 ATR trail; nominal 1% equity risk. Assumes supplied CSV is hourly, no validated data provenance.

## Source defects invalidating the published metrics as executable BTC evidence
1. **Future 4h/1d close leakage:** `df.close.resample("4h").last().ewm(...).reindex(df.index).ffill()` and analogous `1D` are used on a 1h decision bar without shifting the higher-timeframe value to the first bar AFTER completion. The 4h/daily last close can include data unavailable at earlier hours in that bucket. Must compute and align fully CLOSED 4h/1d bars only, with explicit timestamp labels and DST conventions.
2. **Impossible intrabar trailing stop:** on each `next_row`, `next_row.close` moves the trailing stop, then `next_row.low/high` is checked against that new stop on the SAME bar. That new stop is only known at the end of the bar, but the wick may have occurred earlier. Likewise the stop is advanced to breakeven based on the same bar high/low before the bar's adverse excursion is checked. This permits hindsight fills at prices not known when the wick occurred.
3. **Exit management bypassed by entry filters:** the loop `continue` when ADX or volume fail occurs BEFORE `if in_trade` management. Existing positions skip stops/trailing checks on those bars. A backtest can miss stop hits or delay exits.
4. **Entry and exit same next bar with ambiguous sequencing:** positions are entered at `next_row.open` and their stop and trail can be computed using `next_row.close` and checked against `next_row.low/high` immediately. Intrabar path is unobservable from 1h OHLC.
5. **Fees/GST/slippage/funding omitted** in capital updates; no trade ledger with timestamps, equity mark-to-market, month-by-month NAV, leverage/margin or actual lot size. Thus reported PF/CAGR cannot be interpreted as net Delta India execution results.
6. **Open positions and data coverage:** no forced end-of-sample close, no monthly account ledger; the dataset is named `btc_real_data.csv` but not provided or verified in the inspected code.

## Novelty comparison
- `analysis/institutional_discovery_stage24_structure_monthly10/RESEARCH_REPORT.md` on `research/stage24-monthly10`: 1,920 15m squeeze/retest/breakout configurations with 1m stop-first replay, fees/GST/$5 per-side slip, none met all-month target.
- `analysis/independent_stage25_hourly_trend/RESEARCH_REPORT.md` on `research/stage25-new-trend`: 2,880 1h momentum/Donchian/inside-bar variants with 1m stop-first replay, fees/GST/$5 slip, none met all-month target.
- The source is an MTF **trend-filtered prior-day breakout with ATR trailing**, not a clearly novel range-event mechanism. Distinct 1.5% buffer/ADX threshold alone does not pass `codex/STRATEGY_NOVELTY_GATE.md`. Decision **SKIP** until exact economic difference from Stage24/25 and other range-event studies is established. Also no LICENSE file was found at repository root; do not copy its implementation without licensing review.

## Execution and data blockers
The main branch's `codex/DATA_CONVENTIONS.md` documents an unverified 5m archive, not a verified complete 22-month Delta BTC 1m archive. Prior Stage24/25 reports describe Delta 1m and note missing Jan 2025 IST early hours and all 2026-10-31 UTC candles. A complete 22/22 verified month claim is not possible from these reports. No independent new backtest was run because this candidate failed the mandatory novelty and causal-execution gates.

## Next concrete action
Identify a **genuinely distinct** session-anchored range-boundary mechanism from published executable source, compare its exact signal and exit against Stage19/23/24/25 and independent failed-breakout branches, verify Delta BTC 1m archive manifest and provenance, commit a new `NOVELTY_CHECK.md` with approved differential, then run a 2025 zero-slip BTC screen charging both 0.05% fees and 18% GST, next-1m open fills, stop-first replay, complete monthly NAV and trades. If positive with adequate sample, freeze before 2026 and ETH and run cost stress. No changes to main or live trading.
