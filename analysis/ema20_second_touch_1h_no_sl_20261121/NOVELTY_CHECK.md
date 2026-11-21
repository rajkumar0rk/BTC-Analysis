# Novelty assessment — 1H second EMA20 touch without stop-loss
2026-11-21

## Proposed locked rules
Using the same 1H baseline as the earlier fixed BTC/ETH 200/100 backtest, keep Supertrend(10,3) and EMA20 second qualifying touch, exclude the Supertrend flip candle, touch monitored using independent 1m OHLC and the last closed 1H EMA20, no candle close entry confirmation. Volume and volatility filters **not enabled for 1H**; those were specific to 15M.

Close only at take-profit: BTCUSD 200 dollar price points favorable, ETHUSD ex-ante BTC-equivalent fractional price target `200 * ETH_entry / previous completed 1m BTC_close`. No SL, no breakeven, no trailing, no discretionary Supertrend reversal exit or maximum holding duration. At final October 2026 observation, forcibly close only to account for the remaining inventory, marking it as an artificial sample-end exit.

Use historical 1-minute OHLC and adverse entry/exit slippage 0.02% per side, assumed taker fee 0.05% per side + 18% GST, 1x evolving account-equity notional with starting $1,000. Mark unrealized positions to market at every month end and record adverse excursion, holding duration, peak-to-worst intraminute MTM drawdown and any hypothetical crossing of zero equity. Do not treat high TP completion as proof of profitability; funding, liquidation, tick-level fill latency, actual spreads/order book are absent.

Jan 2025–Oct 2026 22 IST months, exclude partial Nov. Verify 22 month 1m partitions for BTC & ETH, check hashes and alignment. Year 2026 has prior research exposure and is not an untouched holdout. Initial UTC archive means first Jan 2025 IST 5h30m absent.

## Closest experiments and novelty
- `scripts/research_ema20_second_touch_fixed_tpsl.py`, `analysis/ema20_second_touch_fixed_tpsl_20261121/` — exactly same 1H entry and TP; **original SL=100 BTC points / scaled ETH**. Changing SL-off is the controlled economic contrast.
- `scripts/research_ema20_second_touch_no_sl.py` — same exit removal but 15M with volume/volatility filters enabled. Different signal frequency and gates.
- `scripts/research_ema20_second_touch.py` — 1H same entry with ATR stop and profit trailing.
- Stage 19 hourly EMA pullback, Stage 24 structure breakout; different signals.

Decision **PARTIAL OVERLAP — approved differential**. Precisely isolates SL removal in user's 1H rules. No parameter fitting/optimization. Never report a nonexistent execution result.
