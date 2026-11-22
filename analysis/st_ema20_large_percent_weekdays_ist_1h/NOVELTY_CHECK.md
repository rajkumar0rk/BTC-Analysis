# NOVELTY CHECK — Weekday-only IST entry filter for large-percent BTCUSD 1H ST EMA20 profit locks

Date: 2026-11-22. **PARTIAL OVERLAP — user-requested controlled differential, approved**.

## Comparison against existing research
- Closest direct baseline: `research/st-ema20-large-percent-profit-locks-20261122:scripts/backtest_st_ema20_large_percent_locks.py` and `analysis/st_ema20_large_percent_locks_1h/comparison.csv`: 144 scenarios, **entries permitted all 7 days**.
- Earlier `research/st-ema20-percent-direct-lock-grid-20261122:scripts/backtest_st_ema20_percent_direct_profit_locks.py`: 156 small-percentage lock scenarios, also no weekday-only trade filter.
- `codex/STRATEGY_NOVELTY_GATE.md` identifies earlier weekday filters in unrelated intraday model families. This differential concerns **the already-used 1H Supertrend + EMA20 touch/reclaim entry and up-to-10%-of-entry direct lock**, untested with precise IST weekday-only fill gating.

## Prespecified change: exclude Saturday and Sunday only for NEW ENTRY
- **ENTRY FILL** must occur Monday–Friday in `Asia/Kolkata` time; determine from the actual 1-minute candidate fill timestamp, **not the previous 1H signal timestamp nor the UTC weekday**. Saturday 00:00 IST through Monday 00:00 IST are non-entry periods.
- Signals can form on weekends, but if their eligible fill would occur Saturday or Sunday IST that fill is excluded and must **not consume** the one-fill-per-Supertrend-cycle budget. A later valid weekday signal in the same cycle may enter, preserving one-trade-per-cycle constraint. No artificial queued weekend entry. Same signal's next-hour entry window remains unchanged.
- Previously-opened positions may remain open over weekends and can exit at the currently active protective lock or Supertrend reversal at any time. **No forced Friday close**; user only asked to exclude Saturday and Sunday from trading entries. Evaluate exits continuously with 1-minute OHLC even through weekends.
- No other entry rule changes: 1H ST(10,3) + EMA20 Touch / Reclaim / Combined signals, after fully completed hour, next-hour high+0.5 LONG or low−0.5 SHORT breakout; same gap-aware entry and one position per cycle.
- Same exact 24 ladders including single 0.14%, 0.5%, 0.75%, **1%, 2%, 5%**, up to 10%, and 1→2→5, 2→3→5, 2→5→10 etc. Same 2 intraminute paths O-H-L-C and O-L-H-C; rung touch immediately moves locked stop to EXACT price corresponding to favorable entry percentage. No initial SL, fixed TP or new timeout. Supertrend flip fallback.
- Fixed 0.001 BTC quantity, $100 illustrative initial equity, taker 0.0005×1.18 each side, 5 BTCUSD price points adverse slippage each side; no liquidation/funding/depth/mark simulation.

## Data/replay integrity and comparison
- Revalidate 1m Delta Exchange India BTCUSD archive 2025-01-01 through 2026-11-20, 23 gz monthly files; timestamps contiguous and full 1h groups.
- Assert all weekday-only entries have IST weekday 0–4; no duplicate cycle IDs. Assert ALL-DAYS baseline candidate entry counts are unchanged for Touch=253, Reclaim=227, Combined=297; mark how many baseline entries fell on IST weekends, how many weekday entries now exist and how many are replacement candidates in same cycle.
- Test IST midnight cutovers explicitly: Friday UTC late night may be Saturday IST, Sunday UTC late night may be Monday IST; ensure timezone-aware conversion precedes entry day filtering.
- Run 24 ladders × 3 entry modes × 2 paths = **144 new complete backtests**; save full trade and IST monthly files, compare each to matched original all-days scenario, fees, net, PF, win/loss, max realized drawdown and full-month profitability.
- November 2026 is partial; 22 full historical months. Explicitly no untouched holdout. Real tick sequence and execution latency unknown, paths hypothetical. No permission to auto-deploy or merge to main.
