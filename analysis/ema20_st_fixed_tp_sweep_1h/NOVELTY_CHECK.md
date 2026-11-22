# Novelty gate — fixed BTC-point take-profit vs reversal-only Supertrend exit

Date: 2026-11-22. Decision: **PARTIAL OVERLAP — user-requested exit differential**.

## Hypothesis
A substantial proportion of earlier losing trades first experienced favorable 1-minute price excursions of 200, 500, or 1,000 BTCUSD price points, so earlier profit taking may improve realized results relative to exit-only-on-confirmed-1H-Supertrend-reversal. This is not an independent/untouched validation: earlier research identified those thresholds by inspecting losing trades.

## Exact frozen rules
- Dataset: historical Delta Exchange India BTCUSD perpetual 1-minute OHLCV, Jan 2025–2026-11-20, validate continuous timestamps and 60-minute 1H bars; 1H Supertrend ATR10, factor3, EMA20.
- Entry logic UNCHANGED from `research/st-ema20-reversal-only-20261122:scripts/backtest_supertrend_ema20_reversal_only_1h.py`: separately Touch / Reclaim / Combined, 1H completed candle signal, following-hour breakout high+0.5 LONG or low−0.5 SHORT, gap-aware stop entry, 1m monitoring, one filled position per Supertrend cycle and no overlapping trades.
- Remove ALL initial stops, 1R protections, breakeven, trailing, timed exits as before.
- Fixed TP scenario 200 / 500 / 1000 BTCUSD **price points measured from the entry execution fill**, LONG +target, SHORT −target. Fill TP on a later 1-minute candle whose high/low reaches the exact target; charge 5 price points slip on exit. If the first minute reaches TP, do not claim TP without knowing the order of intraminute events; only permit starting from the next minute.
- If TP is never hit, close only when the completed 1H Supertrend reverses, at next 1m open. An unclosed trade at dataset end is recorded as unrealized, never artificially closed.
- In a candle at a new 1H boundary, the confirmed reversal exit happens at the open, before same-minute TP checks. No protective stop, liquidation or margin model.
- Fixed 0.001 BTC quantity, $100 illustrative starting account, model 0.05%/side taker fee + 18% GST (0.00059/side), 5 BTCUSD price points/side slippage, do not claim funding, spread, mark prices, depth, margin and liquidation modeled.
- 9 scenarios: 3 entry modes x 3 take-profit values. Log trade details, reasons, 23-month IST reports (Nov partial), realized PnL, gross, total fees, PF, win percentage, peak-to-trough realized DD, MAE/MFE, unclosed positions. IST monthly returns booked on exit month.
- Compare against previously tested Supertrend reversal-only baseline, avoid claims based only on favorable-excursion counts.

## Closest completed studies / differences
- `research/st-ema20-reversal-only-20261122:scripts/backtest_supertrend_ema20_reversal_only_1h.py`, `analysis/ema20_st_reversal_only_1h`: identical entry, **no TP and reversal-only exit** — comparator.
- `research/ema20-supertrend-1h-touch-reclaim-1m-20261122:scripts/backtest_supertrend_ema20_1h.py`: identical core entry but 1H structure stop, R-based lock/trailing, Supertrend flip fallback.
- `research/btc-ema-st-screenshot-20261119:scripts/replay_btc_ema_st_screenshot.py`: related EMA20/Supertrend family with non-equivalent entry and exits.

## Validation limitations
All months were previously research-exposed. No protected holdout. A zero-stop trade can theoretically cause liquidation before fixed TP; realized equity curve is hypothetical and overstates executable live performance if margin is inadequate. Price OHLCV is neither bid/ask nor tick data, and the intra-minute path for TP/entry is unknown. The latest manifest shows zero missing 1m timestamps; the runner must recheck the data and report validation.
