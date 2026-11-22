# NOVELTY_CHECK — five exact direct profit-lock ladders, immediate intrabar activation

Date: 2026-11-22. Decision **PARTIAL OVERLAP — explicitly requested execution semantic differential**, not new strategy discovery.

## The five EXACT requested direct-lock sequences
- 100 → 200 → 400 → 800
- 100 → 200 → 300 → 400 → 500
- 100 → 300 → 600 → 900
- 100 → 400 → 800
- 100 → 500 → 1000

Every BTCUSD price-point number is both an **activation threshold** of favorable mark-to-entry movement and **the profit-lock stop level** relative to actual entry execution fill. E.g. LONG 80,000 fill, when price first trades to 80,100 the stop immediately moves to 80,100, not +0 and not waiting for +200/+500. If price trades to 80,200, stop immediately moves to 80,200, etc. SHORT symmetric. Use *only the named levels*, no invented extra ladder rungs beyond last level (the stop stays at the highest listed level if price travels further). No initial SL, no fixed take-profit, no timeout, no special EMA exit, 1H Supertrend reversal exits at the next 1m open after a completed 1H flip. Stop never goes backward.

## Entry/data/account rules
Unmodified prior `research/st-ema20-variable-lock-ladders-20261122:scripts/backtest_st_ema20_variable_profit_ladders.py`: BTCUSD Delta Exchange India 1m OHLCV Jan 1 2025–Nov 20 2026, 1H Supertrend ATR10 multiplier3 + EMA20 completed touch / reclaim / combined setup; enter on next hour 1m break above signal HIGH+0.5 (LONG), below LOW−0.5 (SHORT), one filled trade per Supertrend cycle, no overlapping positions. Base 1m entry fills are gap-aware (5 points adverse per side). $100 starting illustrative cash, fixed 0.001 BTC; taker fee 0.05% each way × 1.18 GST = 0.00059 per side and 5 BTC price-point exit slippage. Monthly PnL on IST exit date. Recheck all source 1m timestamps.

## Critical 1m intraminute ambiguity
A 1-minute OHLC candle does **not tell whether high happened before low**, so do not pretend a same-minute instantaneous stop can be uniquely replayed. The new work simulates TWO explicit continuous, monotonic paths per 1m candle:
- `open_high_low_close` (O→H→L→C)
- `open_low_high_close` (O→L→H→C).
For both, process each price segment in time order. Enter at actual breakout threshold within entry 1m candle (or open on an entry gap). When a segment crosses a rung, immediately ratchet stop; later on this same candle, stop executes if the segment crosses the active stop (unless gap opens beyond, then exit at worse open). In real execution stop update and actual fill require exchange latency and live ticks, so both modeled paths remain hypothetical; report side-by-side and never call either verified exchange live performance. If an entire favorable candle closes on the threshold, stop remains active into following 1m. No entry-bar omission: explicitly track the path after breakout event, not before.

For each entry mode × five ladders × two candle paths = **30 simulations**. Output trade ledger, exit reasons, close P&L, win count, PF, max realized DD, 22 complete IST monthly reports, fees, and marked adverse excursions, and compare to earlier delayed-update research. Check no future-hour close or unobservable signal used.

## Closest prior results
- `research/st-ema20-variable-lock-ladders-20261122:analysis/st_ema20_variable_lock_ladders_1h` included a `direct` version but activated only on **next 1m candle** after 1m HIGH/LOW; also incorrectly extended listed ladders. Therefore cannot answer same-minute immediate stop problem.
- `research/st-ema20-100pt-step-lock-20261122:analysis/st_ema20_step_lock_100_1h` tested another fixed +100 step, next-minute only.
- `research/st-ema20-rr-grid-profit-protected-20261122:analysis/ema20_st_rr_grid_protected_1h` fixed initial stop and TP; unrelated exit execution.
- `research/st-ema20-reversal-only-20261122:analysis/ema20_st_reversal_only_1h` original no-stops baseline.

## Research limitations
One-minute OHLC is NOT tick path or bid/ask/stop-trigger prices and cannot confirm tick-exact instant lock fills, nor intraminute order. No mark/index price, liquidation, funding, order-book depth, real exchange latency or margin model; stops at the current traded price may trigger instantly and are vulnerable to slippage. Historical months were already inspected, so results are in-sample only; 2026-11 is incomplete. Archive is revalidated directly despite older codex gate warning about October gap. Treat measured differences across OHLC paths as model risk, not empirical bounds on tick reality.
