# Differential test — 1H Supertrend reversal exit plus existing 200-point step-lock

Date 2026-11-21. User clarified: strategy **must exit an open trade on a confirmed Supertrend flip**. This requirement was missing from the previous research variant, causing prolonged losing open positions. Compare with same prior 200-step lock, no trend-flip exit.

## Entry and prior profit-lock rules (identical to latest baseline)
- BTCUSD and ETHUSD, 1H Supertrend(10,3) direction confirmed only after 1H candle closes; EMA20 from previous completed 1H bar.
- Do not count the reversal candle itself; count two separate following 1H candles where a 1m high/low touches frozen EMA20, and enter at touch without waiting for that 1H close.
- One entry per Supertrend direction epoch even after exiting; one concurrent position per asset. No 1H volume / volatility gate.
- No fixed TP, no fixed SL, no ATR trailing. Profit locking activates at +200 BTC points, then jumps lock levels to entry+200, +400, +600 etc for a long, or equivalent negative levels for a short. Between milestones stop remains unchanged. Strict first breach below last locked level (illustrative 1 price-point below for BTC) exits. ETH step and strict breach increment scaled from entry ETH / last completed 1m BTC close. BEFORE first milestone no profit-lock stop.

## NEW mandatory exit
- On a **Supertrend flip against the open position**, close the position at **the opening price of the immediately following 1H candle** (first available 1m open) with adverse 0.02% slippage and 0.05% taker fee plus 18% GST. This is the first moment the fully formed 1H flip is causally observable and executable with 1m bars.
- Never assume exit inside the still-forming 1H reversal candle or at the prior hour's closing price (cannot trade before confirming reversal).
- Exit when either the profit-lock breach happens earlier inside an earlier 1m candle, OR confirmed Supertrend flip at next 1H candle open; no waiting for lock activation on a flip. If price gaps through a previous lock and simultaneously an ST flip is first confirmed, report a flip exit at next open (same opening fill either way).
- Maintain one entry per Supertrend epoch: exiting old trend on reversal does NOT allow a same-epoch second entry, but new confirmed trend can produce its own two fresh qualifying EMA touches.

## Data, modeled constraints, transparency
- Delta India original SHA-checked BTC and ETH 1m OHLC, Jan 2025 through Oct 2026, monthly MTM including open positions, starting $1000 per asset, 1x current modeled account equity notional; slippage 0.02% adverse per side, fee 0.05% taker per side + 18% GST.
- Funding, margin/liquidation, market impact, actual spread, orderbook, tick path, execution latency not modeled.
- 200-point step-lock strict-breach backtest is NOT tick-verifiable from 1m OHLC. Continue testing two explicit H-L or L-H synthetic OHLC paths, do not present them as actual historical ticks or rigorous upper/lower bounds. Supertrend-flip exit, however, is causally timed using confirmed hourly candles.
- Report both assets all 22 IST months Jan 2025–Oct 2026, count exit reason `SUPERTREND_FLIP` vs `STEP_LOCK_BREACH`, trades, after-cost wins and losses, floating drawdown, monthly mark-to-market, whether synthetic equity <= 0, and sample-end closures.

## Novelty gate
- `analysis/ema20_second_touch_1h_step200_lock_20261121/` + `scripts/research_ema20_second_touch_1h_step200_lock_paths.py`: exact user 200-step profit-lock rule but MISSING Supertrend flip exit. Direct baseline.
- `analysis/ema20_second_touch_1h_activation200_trail1_20261121/`: previous 1-point continuous trailing (different exit, missing flip).
- `analysis/ema20_second_touch_1h_atr3_20261121/`: ATR trailing (different).
**PARTIAL OVERLAP — approved one explicit reversal-exit rule addition; do not tune other inputs.** Revisited 2026 historical data not pristine independent OOS.
