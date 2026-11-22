# BTCUSD Supertrend + EMA20 — fixed 1:3 R:R novelty check

Date: 2026-11-22.

Decision: **PARTIAL OVERLAP — approved differential, user-requested exit-only comparison**.

## Reproducible scope

Compare the same hourly Supertrend (ATR 10, factor 3) + EMA20 "touch", "reclaim", and "combined" signals from `scripts/backtest_supertrend_ema20_1h.py`; same completed-candle entry confirmation, break-level triggered during next hour using 1m OHLC, same initial stop (setup extreme +/-10 points), same 5*ATR risk eligibility, and 5 BTC point adverse slippage each side.

Replace *both* breakeven-at-1.5R and 1H swing-trailing-after-2R exits with **fixed take-profit exactly 3 times initial fill-to-stop price distance**. Keep initial stop, and exit if the previous completed 1H Supertrend flips (next minute open). Stop-first if stop/target hit on same 1m candle. Treat an entry-minute stop+target ambiguity conservatively. Fixed QTY=0.001 BTC; $100 illustrative initial account; taker fee 0.05% each side plus 18% GST. Neither liquidation nor funding modeled.

Report versions with (a) one filled trade per Supertrend cycle matching original and (b) repeat sequential entries in same cycle for sensitivity, with at most one open position. Comparing modes and counts is exploratory, not optimization.

## Closest previous research

- Original runner `research/ema20-supertrend-1h-touch-reclaim-1m-20261122:scripts/backtest_supertrend_ema20_1h.py` — exact signals and source; different exits only.
- Prior prior EM20/ST studies: `research/btc-ema-st-screenshot-20261119:scripts/replay_btc_ema_st_screenshot.py`, `research/btc-15m-ema-st-1m-execution-20261120:scripts/replay_btc_ema_st_15m_signals_1m_execution_20261120.py`.
- Closely related research `main:scripts/research_structure_rr_stage11.py` (different entries and stop designs).

## Validation limits

Historical BTCUSD minute source is `data/delta_india/BTCUSD/1m`. Validate continuous minutes and hourly completeness in runner. Full 2025 and Jan–Oct 2026 plus November through 2026-11-20, partial month excluded from full month count. Historically seen data **not untouched out-of-sample**. Compare net USD, fees/GST/slip, trade count, win rate, 3R target frequency, Supertrend exit frequency, monthly IST PnL, realized drawdown, and market costs. Stop-order high/low path approximated with 1-minute OHLC only and may not match tick fills. No guaranteed profitability.
