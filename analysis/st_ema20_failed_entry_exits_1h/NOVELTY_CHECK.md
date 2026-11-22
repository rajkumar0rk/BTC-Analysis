# NOVELTY_CHECK — filter early failures in BTCUSD EMA20 + 1H ST profit-lock system

Date 2026-11-22. **Decision: PARTIAL OVERLAP — approved incremental exit-rule experiments.**

## Why it merits a separate replay
Baseline: `research/st-ema20-variable-lock-ladders-20261122:analysis/st_ema20_variable_lock_ladders_1h/touch_L05_100_500_1000_behind_trades.csv`. In Touch mode 253 closed trades, $+1.2527 net after modeled fees, 192 profit-lock exits totaling +$89.28566, and **61 Supertrend-flip exits totaling −$88.032974**. All 61 had favorable movement <500 BTCUSD points (maximum 497.5), so first profit-lock checkpoint (+500 → lock +100) was never activated. Median adverse excursion ~1304 BTC points. Candidate improvements must be tested on **all** entries, not just already-labeled losers.

## Frozen entry and original profit-lock ladder
- BTCUSD Delta Exchange India perpetual, Jan 2025–20 Nov 2026 from real contiguous 1m historical trade-price candles; validate 1H full groups. 1H EMA20 and ST(10,3). Completed 1H touch/reclaim signal, next 1H breakout (signal high+0.5 LONG / low−0.5 SHORT), gap-aware fill plus 5 BTC point adverse slippage.
- One filled trade per Supertrend cycle and at most one open position; compare separately Touch, Reclaim, Combined.
- Existing nonuniform ladder `100→500→1000` **behind** interpretation as originally tested: at +500 movement lock +100; +1000 lock +500; +1500 lock +1000; then +500-point milestones with lock trailing one rung behind. Only update after completed 1m candle for NEXT minute; stop gap fill worsened if opening beyond lock; no lock in entry minute. No fixed TP.
- Fallback: on first confirmed opposite 1H Supertrend close, exit at next 1m open. Fee/tax model fixed 0.001 BTC, $100 illustrative cash, 0.05% taker fee +18% GST each side (0.00059), 5 points slippage each side. Monthly PnL booked by exit IST month.

## Incremental failure-management configurations
- **baseline** exactly reproduce original replay and assert net/exit counts match.
- **hard SL** at entry execution fill −/+ 300, 500, 800, 1200, or 2000 BTC points, active even before +500 movement, replaced only by a tighter active profit-lock stop. For ambiguous entry-minute high/low, assume stop hit conservatively; thereafter adverse gaps fill at opening price. If both stop/lock and another exit possible, stops first; Supertrend flip at boundary open before same minute high/low.
- **time-to-progress stop**: if after 120/240/480 minute boundaries since entry maximum completed-1m favorable price move is below 200/300/500 points, exit at current 1m open. Only while **no profit lock has activated**, so established winners are not cut by arbitrary time stop.
- **EMA20 hourly invalidation stop**: while no profit lock is active, after one completed adverse-side 1H close vs EMA20 or after two consecutive completed adverse closes, exit at next 1m open; no using the current incomplete hour.
- **hybrids**: hard SL 800 plus 240-minute/+300 progress filter, hard SL800 plus one adverse 1H EMA close, or 240-minute/+300 progress filter plus one adverse EMA20 close.
- Run all on all three entry modes. Compare realized net, gross fees, 22 complete monthly IST outcomes plus November partial, win/loss, drawdown, contribution from originally 61 ST-flip losers, harm to original 192 profit-lock exits. Do not select based only on a retrospectively labeled losing set.

## Closest prior sources
- `research/st-ema20-variable-lock-ladders-20261122:scripts/backtest_st_ema20_variable_profit_ladders.py`: exact frozen 100/500/1000 ladder, no initial SL/EMA/time failure exit.
- `research/st-ema20-rr-grid-profit-protected-20261122:scripts/backtest_supertrend_ema20_rr_grid_profit_lock.py`: 100–300 fixed stops and fixed TPs but not original irregular ladder or EMA/time fallback.
- `research/st-ema20-tp-profit-protection-20261122:scripts/backtest_supertrend_ema20_fixed_tp_profit_lock_1h.py`: fixed TP and one-time protective stops.
- `research/st-ema20-reversal-only-20261122:scripts/backtest_supertrend_ema20_reversal_only_1h.py`: no stop, no lock.

## Risk and validity
No clean out-of-sample holdout; earlier research and threshold selection inspected all historical months. This is **exploratory**, not proof of a trading edge. No funding, liquidation, actual spread/depth, mark-price, latency or order constraints are modeled. A nominal 1m stop or timed exit can experience gap slippage; the illustrative $100 may not support 0.001 BTC margin at required leverage. Do not deploy automatically.
