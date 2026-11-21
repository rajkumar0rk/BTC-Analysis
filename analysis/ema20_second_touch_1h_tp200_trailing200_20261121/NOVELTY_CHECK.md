# 1H EMA20 second-touch: fixed TP200 + fixed-distance trailing 200, one trade per ST

Pre-registered on 2026-11-21 prior to backtest, on separate research branch.

## User request and assumption
User: "add 200 point with trailer points" following the TP100 / TP200 / TP500 experiments and ATR-trailing variant.
Interpretation for this run: **fixed BTC 200 price-point TAKE PROFIT, paired with an immediately-active 200 BTC point trailing-stop distance**. No separate activation trigger is specified; activate stop from entry. This is NOT ATR trailing. The trail itself supplies initial downside protection (not a second fixed stop). If the user intended a different trail distance/activation threshold, this experiment is only the explicitly labelled 200/200 variant.

ETH uses analogous percentage-based distances frozen at entry: `ETH distance = 200 * ETH entry price / previous completed 1m BTC close`, independently for both TP and trailing distance. This is **not** 200 absolute ETH price points.

## Reused strategy
BTCUSD / ETHUSD independent 1H Supertrend(10,3) regime, EMA20 second touch. Ignore Supertrend direction flip candle, count at most one EMA20 touch per subsequent distinct 1H candle. On second 1H touch use 1m candle wick crossing previous fully closed 1H EMA20 and enter immediately (1m OHLC execution approximation), no candle-close wait. ONE entry maximum per confirmed Supertrend direction epoch; if exited at TP or stop, cannot re-enter that same epoch, only after opposite confirmed ST flip. Any still-open position remains open through Supertrend reversals; no reverse-on-flip exit. No 1H volume or volatility filters.

## Exit rules, sequencing
- Fixed TP = 200 points long/short BTC, 200 BTC-equivalent percentage ETH.
- Trailing stop starts at entry -/+ 200 price points or scaled ETH; activate immediately, no separate fixed SL, no breakeven feature, no ATR trailing or timed exit.
- For LONG after a one-minute bar that did **not** exit, trail = max(old trail, highest observed **completed 1m** high since entry minus frozen distance). For SHORT, trail = min(old trail, lowest observed completed 1m low plus frozen distance). Trail never retreats. A newly tightened trail is actionable on NEXT 1m candle, not the candle which provided the new high/low.
- Prior active stop is checked FIRST on every subsequent 1m bar. If both TP and stop would be crossed within one 1m candle, classify the result as trailing stop first, conservative. Long gap through stop fills at worse of 1m open or previous stop, likewise shorts; then 0.02% adverse exit slippage. TP fills at original target (no fictitious favorable gap price improvement), with 0.02% adverse exit slippage; assumed marketable execution may differ from real limit orders.
- Entry 1m candle itself: trade is opened when it touched EMA but minute OHLC ordering is unknown. To avoid optimistic TP fill, DO NOT count entry-minute TP. If entry-minute adverse wick reaches initial trailing stop, assume immediate stop fill at the stop price (no use of the bar's pre-entry OPEN to make gap worse, because it predates entry); otherwise do not credit favorable entry-minute wick to advance the trail. This is a conservative proxy, not tick-level replay.
- Position model: one independent asset position and 1× evolving equity notional from $1,000 initial equity per asset; 0.05% taker fee per side + 18% GST (FEE=0.00059) and 0.02% adverse entry/exit slippage each side. Entry and exit fees included in P&L.
- Include all 22 IST months from Jan 2025 to Oct 2026 using sha-validated Delta India 1m BTCUSD/ETHUSD OHLC (first 330 minutes of 2025 IST outside UTC-start dataset). Track realized trade P&L and year returns, mark to market month ends and maximum intraminute floating drawdown, profitable months, exit breakdown and possible equity below zero. End-of-sample forced close only for accounting and marked as such, not an intended live exit.

Unknown: actual bid/ask spread, funding, orderbook, latency, margin/liquidation and tick path. The user has repeatedly tested this 2026 archive; 2026 is not untouched out-of-sample.

## Novelty decision
Related existing experiments:
- `analysis/ema20_second_touch_1h_one_trade_per_st_20261121/` — 200 TP, no stop/trail; direct controlled baseline.
- `analysis/ema20_second_touch_1h_tp100_no_trail_20261121/` — TP100 only.
- `analysis/ema20_second_touch_1h_tp500_no_trail_20261121/` — TP500 only.
- `analysis/ema20_second_touch_1h_atr_trail_20261121/` and `analysis/ema20_second_touch_1h_atr3_20261121/` — ATR-distance trailing, no fixed TP; not equivalent.

**PARTIAL OVERLAP — approved incremental paired-exit differential**, no parameter sweep or cherry-picked asset selection.
