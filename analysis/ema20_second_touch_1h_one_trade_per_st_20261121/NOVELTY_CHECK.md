# Novelty check — one trade per completed Supertrend direction cycle, 1H

2026-11-21. This is a controlled incremental backtest of the user's most recent 1H TP-only experiment, **not** a new entry/exit signal.

## Pre-registered trade rules
BTCUSD and ETHUSD perpetual futures, 1H signal candles, 1m historical execution. Supertrend (10, 3), EMA20 values only from completed 1H bars. Exclude the Supertrend flip candle from EMA touch count. On the second distinct subsequent 1H candle that touches frozen EMA20 during a single confirmed Supertrend direction cycle, execute immediate entry at modeled EMA price plus adverse slippage, without waiting for 1H close. One trade per asset concurrently.

**NEW rule:** one entry per Supertrend direction cycle (bullish or bearish). Once any entry is opened, set `epoch_traded = True` and ignore subsequent EMA20 touch setups until Supertrend flips to the opposite direction. This prohibition remains even if previous trade reaches TP; it resets **only** on confirmed Supertrend direction flip observed at end of 1H candle. If position remains open across reversal, do NOT close merely because Supertrend flipped; when eventually flat the current epoch is eligible, provided two new post-flip EMA touches occur. Never permit two entries in same cycle, even if price returns to EMA.

No 1H volume or volatility filter (those were configured for 15M only).

Exit: TP-only, BTC 200 price points, ETH-equivalent 200 points scaled by ex-ante ETH entry / prior complete 1m BTC close. NO stop-loss, no breakeven, no trailing, no opposite-Supertrend-flip liquidation, no time exit. All normal exits are fixed TP, and at final 2026-10-31 IST-boundary any remaining open position forcibly marked/closed for accounting ONLY. Model entry and exit adverse slippage 0.02% per side, fee 0.05% taker per side plus GST 18%, $1,000 starting model equity with 1x current equity notional (not exchange margin), 1m OHLC TP ordering after entry-minute, no assumed same-minute target fill.

Report BTC and ETH separately for 22 IST months 2025-01..2026-10, with realized PnL, month-end unrealized mark-to-market PnL, maximum estimated intraminute MTM drawdown, prolonged hold and largest adverse exposure. Verify 1m data checksums and no gaps. Funding, forced liquidation, real exchange bid/ask/latency, mark margin and actual orderbook unmodeled. Backtest results cannot establish actual feasibility.

## Prior experiments / novelty decision
- `scripts/research_ema20_second_touch_1h_no_sl.py` and `analysis/ema20_second_touch_1h_no_sl_20261121/` are same no-SL 1H entry/exit but allow repeated post-TP trades in same Supertrend trend. Direct baseline for controlled comparison.
- `scripts/research_ema20_second_touch_fixed_tpsl.py`: same second EMA touch but has SL100 BTC equivalent. Not an appropriate baseline for isolating this change.
- `scripts/research_ema20_second_touch_15m_filters.py`, `scripts/research_ema20_second_touch_no_sl.py`: 15M volume/volatility variants not relevant to 1H changes.

**Decision: PARTIAL OVERLAP — approved differential**. Explicitly tests the rule prohibiting repeat trades within one Supertrend regime, while holding all existing 1H no-SL assumptions constant. No retuning of TP/slippage or attempt to present selected positive history as untouched validation. First 330 IST minutes of Jan 2025 outside archive; November 2026 not complete; 2026 previously explored, not pristine out-of-sample.
