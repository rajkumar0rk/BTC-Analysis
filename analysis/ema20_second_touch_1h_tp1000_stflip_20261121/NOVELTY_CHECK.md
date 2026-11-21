# Pre-run novelty and method: 1H second-touch TP1000 + confirmed Supertrend flip
Date 2026-11-21, user-requested. This is a single-parameter exit change from the immediately preceding confirmed-flip strategy.

Same entry: completed 1H Supertrend(10,3) direction and completed 1H EMA20; skip flip candle; wait for two separate post-flip 1H candles whose 1m price intersects the last completed 1H EMA20, enter at second touch immediately with adverse entry slippage; one entry per Supertrend direction epoch.

**No profit lock of any kind; no trailing, no standalone stop.** Exit first of (1) fixed favorable **1000 BTC price point** target for BTC LONG/SHORT or percentage-equivalent ETH distance frozen at entry, `1000 * ETH executed entry / prior 1m BTC close`; (2) confirmed opposite Supertrend(10,3) direction after 1H close, executable at immediately following 1H candle open (first 1m open); (3) hypothetical forced end-of-sample accounting closure. Do not exit just because price travels 200/400/etc.

BTC and ETH Delta India 1m SHA-verified candles Jan 2025–Oct 2026, 22 IST months, capital $1000 each, 1x evolving equity notional, fee 0.05% taker each side + GST 18%, 0.02% adverse slippage each side; monthly MTM, floating stress, win/loss counts, exit reason counts, PF. Same entry path sensitivity as prior study: hypothetical O-H-L-C and O-L-H-C per 1m candle to avoid presuming unknown ordering between 1m EMA entry and TP. 1000 TP hit on a later 1m candle is generally identifiable in 1m OHLC, unlike the old 1-point breach; both paths remain synthetic for entry-minute ordering. Order prices, funding, margin and real exchange liquidation not modeled. Same-day 2026 historical archive already researched, not a pristine OOS period.

Previous closest baseline `analysis/ema20_second_touch_1h_step200_flip_exit_20261121/` (BTC -56%, ETH -38% to -41%). New exit deliberately replaces 200-point step lock with 1000-point TP. Other variants include `analysis/ema20_second_touch_1h_tp500_no_trail_20261121/` but those did NOT exit on Supertrend flips, so not same strategy.

Novelty gate: PARTIAL OVERLAP — user-requested, approved distinct exit design. No optimization sweep, never promote results as live tradable without further execution validation.
