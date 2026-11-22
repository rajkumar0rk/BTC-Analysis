# Novelty check — BTCUSD 1H Supertrend EMA20 touch vs reclaim, 1m execution

Date: 2026-11-22 UTC
Decision: **PARTIAL OVERLAP — approved differential** for this explicitly requested comparison.

## Pre-registered rules

- Instrument: Delta Exchange India BTCUSD perpetual; available monthly 1m traded-price OHLCV. No fabricated minutes.
- Completed 1H candles only: EMA20 close and Supertrend (ATR10, factor3), bullish trades only in green cycle and bearish only in red cycle.
- Exclude flip candle. Setup **touch**: 1H price touches EMA20 and closes back in Supertrend direction without an earlier completed close across EMA20 in the same excursion. Setup **reclaim**: at least one completed 1H close against EMA20, followed by a completed 1H close back on the trend side, provided Supertrend has not flipped.
- One-hour-valid entry: 1m break of prior completed 1H confirmation high+0.5 (LONG) / low-0.5 (SHORT), including worse open on gaps, plus 5 points slippage.
- Stop: below/above signal structure with 10-point buffer; 1m stop-first ambiguity treatment and worse-open gap handling. Stop distance no more than 5x 1H ATR.
- After 1.5R excursion, protect modeled round-trip costs; after 2R use a ratcheting prior-three-completed-1H low/high trailing stop; exit on confirmed opposite Supertrend using next 1m open.
- One filled trade per Supertrend cycle; no overlapping positions. Backtest three independent variants: TOUCH, RECLAIM, COMBINED.
- Base quantity 0.001 BTC; starting equity $100 for illustrative account returns; taker fee per side 0.05% + GST18%, 5 BTC price points slippage each side. Do not model funding or liquidation or claim executable quotes.

## Nearest previous work

- `research/btc-ema-st-screenshot-20261119:scripts/replay_btc_ema_st_screenshot.py`: earlier EMA20/Supertrend entry and execution variants.
- `research/btc-15m-ema-st-1m-execution-20261120:scripts/replay_btc_ema_st_15m_signals_1m_execution_20261120.py`: prior 15m signals / 1m fills.
- `research/btc-tv-ema-st-screenshot-20261120:scripts/backtest_tv_ema_st_screenshot_20261120.py`: TradingView screenshot parity backtest.
- `main:scripts/research_retest_reclaim_stage4.py`: different hourly-expansion/5m retest family.

The incremental measurable hypotheses are (a) *1H cross-and-reclaim* versus *1H same-candle touch* when the Supertrend trend persists, and (b) one-hour stop-entry breakout confirmation with 1m causal stops and explicit multi-regime handling. Previous work does not independently report this side-by-side distinction.

## Validation and quality

- Split 2025 exploratory, Jan–Jun 2026 chronological review, Jul–Oct 2026 recheck and November partial. **None are an untouched holdout; all months have been seen during earlier research.**
- `data/delta_india/BTCUSD/1m/manifest.json` was generated 2026-11-21 and claims zero missing minutes through 2026-11-20; validate every candle again in the runner. Older novelty gate mentioned October gaps, which conflicts with the later archive: rely on verified bytes, not either claim alone.
- Output: all trades, net monthly IST PnL including no-trade months, drawdown, fees, win/loss, and quality record. No assumption of daily profit or live accuracy.
