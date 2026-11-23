# Preregistered research — FIRST EMA20 touch after Supertrend flip, TP = 2× Supertrend-line distance

User-requested fixed logic, 2026-11-22. Run both BTCUSD/ETHUSD independently on **1H and 15M**, 2025-01 to 2026-10 inclusive (22 IST months).

## Indicators and exact first-touch entry
- Supertrend uses **ATR Wilder length 10, multiplier 3** on completed signal-timeframe candles, EMA(20) of completed signal-timeframe closes. Note: some earlier research files labeled Supertrend(10,3) but calculated ATR14 (a mismatch); this run explicitly uses Wilder 10 ATR.
- At every confirmed Supertrend bullish flip (from RED to GREEN), reset eligibility. The flip candle itself is not touch-eligible. After its close, on **the very first distinct following 1H/15M candle** whose 1m price intersects **EMA20 from the immediately preceding completed signal candle**, open LONG at that EMA touch, adverse 0.02% entry slippage. A touch in the immediately following signal candle qualifies (no requirement to wait for a second touch).
- SHORT mirrors GREEN to RED, first touch, enter SHORT.
- **Only one entry per confirmed Supertrend direction cycle** regardless of exits. If first touch is reached while an existing position remains open (should be closed on flip), skip until eligible; do not re-enter after exit while ST direction unchanged.
- Supertrend *line* at entry is from the most recently completed signal-timeframe candle. To compute risk reference, need bullish line strictly below long executed entry, bearish line strictly above short executed entry; otherwise mark touch invalid and skip. Risk reference R=abs(entry executed price - frozen Supertrend line at entry).
- **Take profit** long = entry_fill + 2R; short = entry_fill - 2R. TP stays fixed, even as Supertrend line changes. TP fills at modeled target when 1m price reaches it (no favorable gap improvement); commissions/slippage deducted.
- **Only loss exit:** confirmed **OPPOSITE Supertrend flip on the completed signal bar**. Exit at **first 1m open of immediately following signal-timeframe candle** with adverse exit slippage; don't exit just because price touches ST line intrabar. No fixed stop, no profit lock, no ATR stop, no extra time-stop. At dataset end only an accounting exit (report separately).

## Same baseline assumptions
- Original checked Delta India historical 1m OHLC BTCUSD/ETHUSD Jan 2025 through Oct 2026; complete 22 IST months, 1m execution throughout, both weekends included.
- Begin $1000 USD model equity per asset/timeframe, size 1x changing equity. 0.05% taker each side, GST18% on those fees, 0.02% adverse execution slippage each side. No funding, real market depth/spread, margin, liquidation or order latency.
- One-minute OHLC cannot prove ordering between touch and TP inside entry minute. Run sensitivity to both **hypothetical** continuous 1-minute paths O-H-L-C and O-L-H-C, filling exactly at first EMA20 touch along segment and checking only subsequent movement. These paths are not real ticks or strict worst/best performance bounds.
- Trade ledger by entry and exit, TP/flip exit counts, net win/loss, PF, monthly mark-to-market and month-win count, floating drawdown and insolvency checks. Year-end forced close not a trading exit.
- 2026 has been researched before, not a pristine out-of-sample holdout.

## Novelty gate
- Prior `analysis/ema20_second_touch_1h_tp1000_stflip_20261121/`: SECOND EMA20 touch, fixed 1000 BTC-point TP or Supertrend flip; inappropriate for this user's FIRST touch and **2× Supertrend-line distance** TP.
- Prior `analysis/ema20_second_touch_20261121/`: 15M+1H SECOND EMA20 touch, ATR2 stop, breakeven and trailing, no ST flip exit.
- Prior `analysis/ema20_second_touch_1h_step200_flip_exit_20261121/`: SECOND touch, step lock, ST flip.
**PARTIAL OVERLAP, approved distinct entry and TP/SL definition, no optimization sweep.**

## Reproduction replay — 2026-11-23
- User requested an exact repeat of the published BTCUSD/ETHUSD 15M first-touch Supertrend-flip/2R historical test.
- Trigger the existing workflow on the same research branch using this documentation-only change; leave strategy code, data window, 1-minute execution assumptions, costs, and output calculation unchanged.
- Do not interpret the archived report as a newly completed run until workflow completion and result revision are independently verified.
