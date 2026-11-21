# Pre-run novelty check — 1H second EMA20 touch with no TP and no SL
Date 2026-11-21.

## Exact scope and execution policy
User requested removing TP from latest 1H one-entry-per-Supertrend trading strategy. Preserve other settings: Supertrend(10,3), EMA20 second touch (two distinct post-flip 1H candles; flip candle does not count), intrabar entry using 1m exchange OHLC crossing last completed 1H EMA20; no 1H volume/volatility filters. Rule one entry per Supertrend direction epoch. Existing rules also had no SL, no trailing or breakeven and no exit upon reversal. Therefore **NO AUTOMATIC EXIT WHATSOEVER** in user-requested variant. The first entry remains open throughout the data sample (unless simulated mark-to-market at end). One trade per Supertrend becomes an inactive limiting constraint because exclusive position never closes; flipping Supertrend will not close an open position. No additional exit invented.

For BTCUSD and ETHUSD, 1-minute OHLC 2025-01-01 UTC through 2026-10-31 18:29 UTC from Delta India, ensure hashes, aligned. One isolated $1000/asset modeled 1x evolving account notional. Entry slippage 0.02% and taker fee 0.05% *1.18 GST. Estimate **hypothetical** mark-to-market liquidation at each minute close with 0.02% adverse slippage and exit fee with GST, but do not actually exit until forced sample-end mark. Month-end IST equity includes unrealized PnL and estimated exit costs. Report entry, side, holding duration, minimum/max floating equity, worst adverse excursion, drawdown including adverse wick on each 1m candle, and hypothetical insolvency. This is not an executable automated trading strategy as no planned exit exists; actual liquidation, funding, spread, margin and book data unavailable. Data first 330 minutes of Jan 2025 IST absent; 2026 history repeatedly researched, not untouched.

## Closest previous experiments
- scripts/research_ema20_second_touch_1h_one_trade_per_st.py / analysis/ema20_second_touch_1h_one_trade_per_st_20261121: exact entry/one-per-trend but **with** TP. This delta removes last remaining exit.
- scripts/research_ema20_second_touch_1h_no_sl.py: TP-only 1H without one-per-trend restriction.
- scripts/research_ema20_second_touch_fixed_tpsl.py: fixed 200 BTC / 100 BTC equivalents with no volume filter.

Decision: PARTIAL OVERLAP — approved differential. One explicit exit-removal variant, no search or tuning. Maintain prior input data/fee assumptions. No false win-rate claim for single never-closed position.
