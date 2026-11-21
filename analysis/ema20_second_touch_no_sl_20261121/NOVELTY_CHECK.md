# EMA20 second touch 15m — TP-only, no SL — novelty gate
2026-11-21. Exact user request: compare previous BTC and ETH 15-minute second EMA20 touch with volume and volatility gates enabled, removing stop-loss and leaving TP unchanged.

## Pre-registered strategy
- BTCUSD and ETHUSD independent 15m Supertrend(10,3) regime, EMA20 second touch in a distinct 15m candle after excluding Supertrend-flip candle; touch inferred with 1m OHLC on last completely closed 15m EMA. No close confirmation.
- Volume filter: last completed 15m volume >= 1.2x average of 20 PRECEDING complete 15m volume bars.
- Volatility filter: last completed 15m ATR14 >= average of 20 PRECEDING ATR14 readings.
- Only both filters enabled (previous current default); checked at second touch only, rejection resets count. No trade stacking per asset, independent balances.
- Fixed take-profit: BTCUSD +200 points for long, -200 points for short, ETHUSD equivalent percentage using entry price * 200 / preceding completed 1m BTCUSD close. Frozen at entry. **No stop-loss, no breakeven, no trailing, no reverse-on-Supertrend-flip, no timeout.** Positions close only at TP or at final Oct-2026 sample boundary (explicit sample-end forced close for reporting, not a tradeable recurring exit rule).
- 1m hit detection on bars strictly after entry minute (no optimistic same-minute entry and target ordering); target price fill with 0.02% adverse exit slippage, 0.02% adverse entry slippage. 0.05% taker fee per side plus 18% GST. Initial $1,000 model equity, 1x notional, reuse realized equity after fees, no deposit or leveraged margin assumptions. Limit orders are simplified; actual venue target execution could differ.
- Mark-to-market minute by minute including unrealized PnL, hypothetical exit fees and slippage, track worst intratrade adverse excursion, longest holding, and estimated max intrabar equity drawdown including adverse minute extremes. Show month-end MTM returns *including floating loss* alongside realized cash and forced close.
- Jan 2025–Oct 2026 (22 months, IST) with BTC/ETH 1m data alignment & SHA verification; Nov 2026 excluded.
- The no-SL policy could have huge floating losses, unlimited losses on shorts, bankruptcy/liquidation exposure not modeled. **Do not call trades winning merely because most eventually hit TP**. Funding, spread, order book, latency, exchange liquidation and tick order unknown. Label research only.

## Prior related work and novelty decision
- `analysis/ema20_second_touch_15m_filters_20261121/`: identical entry, filter settings and BTC/ETH TP, but also -100 BTC / equivalent ETH SL. This is the direct baseline.
- `analysis/ema20_second_touch_fixed_tpsl_20261121/`: same entry without filters and fixed 200/100 TP/SL.
- `analysis/ema20_second_touch_20261121/`: same entry with ATR/1R stop/breakeven/trailing.
- `analysis/delta_1m_exit_research/` and `analysis/institutional_discovery_stage19_new_1h_patterns/`: related exits and EMA pullbacks, different entry.

Decision: **PARTIAL OVERLAP — approved differential**. Isolate SL removal on precisely same gated second touch. No parameter optimization. 2026 extensively previously researched, not a pristine holdout. First 330 minutes of Jan 2025 IST missing because data begins at Jan 1 UTC; all scored UTC minutes present otherwise. No positive-outcome guarantee.
