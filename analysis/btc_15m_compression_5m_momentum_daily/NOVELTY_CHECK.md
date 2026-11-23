# Pre-registered novelty gate — BTCUSD 15m compression → 5m momentum breakout → 1m execution

**Decision:** PARTIAL OVERLAP — approved differential study, not discovery of a wholly novel price-action family.

## Closest prior work

- `scripts/research_monthly_10pct_stage19.py`, `analysis/institutional_discovery_stage19_monthly_10pct/`: 5-minute 3-bar range compression and 5m prior 6-bar breakout, multiple daily trades, assorted leverage/risk.
- `scripts/research_one_trade_every_day_200.py`, `analysis/one_daily_trade_200_points/`: every NY calendar day forced to trade, 5m range breaks, fixed BTC price-point target; not selective IST-day volume-normalized 15m compression.
- Stage24 `research/stage24-monthly10`: 15m structure retest and squeeze, per project novelty gate (separate research branch).
- Stage25 `research/stage25-new-trend`: 1h trend price-action entries, not 5m post-compression first break.
- Existing EMA9/21 1m microtrend research is intentionally **not reused** as the underlying signal.

## Incremental hypothesis

**15-minute multi-candle compression that resolves via a close-confirmed, high-volume 5-minute impulse in the direction of a fully completed hourly trend** may yield fewer false breakouts and larger post-fee daily wins than simple 5m compression or EMA signals. This is a new timeframe relationship and daily-return evaluation, but related to previously researched breakout/compression families. No 2026 profitability claim can be treated as out-of-sample because prior research already examined that period.

## Fixed rules (before running)

- Data: Delta India BTCUSD perpetual-futures **continuous 1m OHLCV** archive 2025-01 through 2026-11-21. Verify minute continuity, duplicate timestamps, OHLC and nulls. Evaluate **2025-01-02 through 2026-10-30 inclusive**, full available IST weekdays only; 2025-01-01 IST is partially absent from UTC-start archive, so omit it. November 2026 is tail data only, no entries.
- Signal: 15m bars constructed from groups of exactly 15 complete 1m candles, labeled by end time; range compression of last **4 bars with range <=1.9×ATR15(14)** or **8 bars with range <=2.8×ATR15(14)** (range = rolling max high − rolling min low; ATR Wilder). The 15m range **excludes** the 15m bar containing the breakout 5m bar; use the latest 15m bar whose close is <= the breakout bar's **start-of-current-15m** boundary.
- 5m breakout: complete five 1-minute candles; close crosses above/below the prior 15m compression range high/low (and previous completed 5m close not already outside the *same* boundary); volume of signal 5m bar >= **1.10× or 1.35×** preceding 20 completed 5m bars' mean (excludes current signal bar); candle body >=0.6 of range, closes in top/bottom 20% of range, range >=0.7×5m ATR14. Long and short symmetrical.
- Hourly confirmed trend modes: (a) last completed 1H close>EMA20>EMA50, opposite short; or (b) close>EMA9>EMA21, opposite short. Hourly bar for 5m signal is strictly completed *before* the breakout 5m bar started, no partial bars or same-hour signal lookahead.
- Entry: next 1m OPEN immediately after 5m breakout CLOSE. Weekdays Monday–Friday, 09:00–19:00 IST signal, one entry maximum per day, zero-trade days allowed; no overlapping positions.
- Stop: static **1.25× or 1.75× ATR5(14)** (fully formed 5m signal bar); target fixed **2R or 3R**. Reject a signal if after an estimated standard taker fee+GST+slippage round-trip, its target outcome would be <+0.2% account profit with **100% notional (1x)** exposure. Intrabar 1m stop-first tie, gap-aware stop, max 4-hour hold, exit at next 1m open after timeout.
- 32 fixed variants = 2 compression profiles × 2 volume thresholds × 2 hourly trend settings × 2 ATR stops × 2 reward ratios. No tuning, month-by-month adaptation or oracle date selection.
- Cost baseline: taker 0.05% per side, GST 18% on fee, 5 BTC quote-price points adverse slippage each side. Second cost sensitivity: Delta regular **Scalper Offer** waives *closing taker fee only when exit within <=30 minutes*, with opt-in assumed; opening fee+GST remains. Historical offer availability/activation is not verified in all months. Funding, spread/order book, liquidation, maker fills excluded.
- Sizing: **100% account notional, unleveraged 1x**. Account percent means **net account** PnL, not BTC price move or risk/R. No leverage used to manufacture +0.2% daily target.
- Evaluation: daily net account return; count winning, losing, no-trade days; total and % days with net **>=+0.2%**, worst daily loss and max closed-trade drawdown, 2025 vs 2026 net return, net month count. 2025 selection: maximize count of +0.2% days **among positive 2025 net-return variants**, tie-break 2025 compounded return and lower 2025 drawdown; if none positive in 2025 select the least negative *for diagnosis only* and mark failure. Report best-full-sample hindsight as non-selectable curiosity.
- Daily eligibility denominator: full available weekdays in 2025-01-02–2026-10-30; **zero-trade weekdays count as 0% and fail +0.2% target**. No trade may be opened after 19:00 IST; 4-hour maximum ensures exits by 23:00 same IST weekday, avoiding ambiguous daily attribution.

## Quality / limitations

Old project notes flag missing October 31, 2026, but current data archive manifest (generated 2026-11-22) declares zero missing 1m candles in the 22 months; runner must verify continuity and report failure if absent. 2026 has been researched previously and cannot be considered independent blind data. Not a guarantee of +0.2% net profit daily.
