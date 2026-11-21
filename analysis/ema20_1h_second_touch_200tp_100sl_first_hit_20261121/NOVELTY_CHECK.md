# Pre-registered first-hit test: TP +200 vs SL -100 after original 1H EMA20 second-touch entry

## Locked entry
Use BTC-Analysis original features() and SHA-checked read_source() on Delta India BTCUSD and ETHUSD 1m candles for Jan 2025 through Oct 2026 IST.
- 1H Supertrend(10,3) from FULLY completed 1H candle and 1H EMA20 from same completed 1H candle; never look ahead.
- Ignore the 1H candle that flips Supertrend; require first and second DISTINCT later 1H candles to touch the frozen EMA20 (on 1m OHLC).
- Enter immediately when the second 1H touch candle's 1m intrabar path first reaches EMA20, one trade per Supertrend direction cycle, one open trade per asset. No 1H volume or volatility gate.

## Primary experimental question
After that exact entry, **which first**: favorable +200 BTC PRICE points TP, or adverse -100 BTC PRICE points SL? Fixed two-barrier first-passage, not previous stepwise 200-point profit lock.
- LONG: TP=executed entry+200; SL=executed entry-100.
- SHORT: TP=executed entry-200; SL=executed entry+100.
- ETH: fixed per-trade BTC percentage equivalent from executed entry/last completed 1m BTC close: TP=200*ETHentry/BTCprior, SL=100*ETHentry/BTCprior. Not absolute ETH points.
- First touch exits at modeled barrier (adverse gap at worse open; TP at target even on gap). No trailing.
- Costed account: $1000 initial per asset, 1x account notional per trade, 0.05% taker per side plus 18% GST, adverse slippage 0.02% each side. Funding, spread, margin liquidation, true tick sequence, latency excluded.
- Neither hit by Oct 2026: count SAMPLE_END_ACCOUNTING_ONLY, not TP nor SL.

## Two explicitly separated variants
A. BARRIER_ONLY (answers literal TP200 before SL100): ignore Supertrend flip for exits, close on first barrier hit. Supertrend can flip during open trades but entry eligibility remains one per Supertrend cycle.
B. FLIP_EXIT (current Supertrend strategy): if confirmed 1H Supertrend flips while a trade remains open, exit at following 1H candle first 1m OPEN with adverse fees/slippage, counted SUPERTREND_FLIP separately, not TP or SL.
Same entry logic, no other changes.

## OHLC ambiguity
Historical source has 1-minute OHLC, not complete 2025-26 tick prices. When both barriers are touched inside one minute, real first hit unknown. Replay TWO hypothetical continuous within-minute paths O-H-L-C and O-L-H-C, including the entry minute, respecting sequence of entry and exits. These are sensitivity scenarios, not tight guaranteed outcome bounds. Count ambiguous exit 1m bars; do not imply exact live execution.

## Research-gate decision
PARTIAL OVERLAP: User explicitly requests isolated first-hit test. Existing research_ema20_second_touch_fixed_tpsl.py tested fixed 200/100 but allowed MULTIPLE entries per Supertrend cycle, unlike the current rule. Preserve strict latest one-entry-per-cycle and current flip mode separately. Pre-registered before outputs; 2026 previously mined, no pristine untouched holdout.
