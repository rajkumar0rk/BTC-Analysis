# Novelty gate — FIRST EMA9/21 crossover, maximum ONE trade per Supertrend regime

Pre-registered 2026-11-22. Decision: **NEW entry gate + explicit one-trade-per-regime restriction** (user's latest request), not a new market-data source or exit model.

## Precise strategy being evaluated
- BTCUSD Delta India perpetual futures, actual authentic 1m OHLCV from `data/delta_india/BTCUSD/1m/`, calendar Jan 2025–Oct 2026 IST. January 2025 IST is missing 330 minutes at beginning; remaining months complete.
- Each timeframe independently 5m, 15m, 1H from **fully closed** candles; Supertrend Wilder ATR(10) x3, EMA9 and EMA21, warm up 100 full bars. No lookahead or incomplete indicator data.
- **LONG:** Supertrend flips GREEN to begin a GREEN regime. **First subsequent EMA9 crossover ABOVE EMA21**, with Supertrend GREEN on prior and current completed candles, generates one (and only one) LONG opportunity, next 1m open. If no valid crossover while GREEN, **NO trade**.
- **SHORT:** symmetric. Supertrend flips RED and the **first subsequent EMA9 crossover BELOW EMA21** with Supertrend RED on prior and current closed candles permits exactly one SHORT opportunity. If no valid crossover, no trade.
- One trade maximum per Supertrend regime: after this first valid crossover, mark regime as **consumed**, even if an existing open position prevents actual entry. Do not take second, third or later EMA cross in that regime after take-profit/stop/close. Reset consumed flag **only on Supertrend color flip**. A crossover simultaneous with a Supertrend flip does not count; Supertrend must already have been favorable on previous completed candle. A Supertrend flip alone cannot trigger entry.
- A position may persist across a Supertrend color flip; a signal while position is active is dropped, and never queued. At most one simultaneous position.
- Compare explicitly against `research/supertrend-second-ema-cross-20261122` (user requested retaining this variant, which remains completely unchanged), plus `research/supertrend-first-ema-cross-20261122` (old first crossover had NO one-trade-per-Supertrend cap), `research/supertrend-ema921-20261122` (first combined alignment) and prior fixed grid scripts. This is neither the earlier *first alignment* nor the earlier *first cross permitting multiple trades in same Supertrend regime*. No previous branch or report is overwritten.
- Fixed exits only: 20 pre-registered stop/target pairs from prior experiment. 1:3 = (100/300,150/450,200/600,300/900,400/1200,500/1500,600/1800,800/2400,1000/3000); 1:4 = (100/400,200/800,300/1200,400/1600,500/2000,600/2400,800/3200,1000/4000); plus reference (100/200,200/2000,1000/2000). Three timeframes × 20 pairs = **60 configurations**. No new parameters selected after results.
- Entry at next actual 1-minute OPEN after the higher-timeframe bar closes; fixed TP/SL measured from adverse-slippage entry fill, 1m High/Low hit detection, conservative stop-first on ambiguous 1m candle and adverse-open stop-gap. End-of-IST-month flatten for monthly P&L only; one position at a time; trading 7 days, no daily limits. No indicator exits when fixed TP/SL active.
- 1× notional compounded returns, taker 0.05% fee per side, 18% GST on fee, adverse $5 BTC price-point slippage per side. No funding, true spread/depth, margin/liquidation, live order delay/slippage model.
- Output all 60 variants, win/loss counts, win%, monthly returns all 22, net account return, gross/fees/slippage in point-equivalent, profit factor, max **trade-close** drawdown, separate 2025 vs Jan–Oct 2026, full trade ledger and quality report.
- These dates are research-exposed and NOT blind out-of-sample. Parameter screens increase selection bias. No assurance of consistent live profit.

## Explicit tests
1. First bullish EMA crossover while green gives one LONG.
2. Second and later bullish crossovers while green give **zero further** signals.
3. Flipping RED resets the count and first bearish EMA cross allows exactly one SHORT.
4. Flipping GREEN while EMAs already aligned above does **not** generate LONG until genuine new bullish crossover.
5. Simultaneous ST flip and EMA crossover excluded.
6. No crossover within regime => no trade.
7. Any first-cross event while another trade active is consumed, not held for future entry.

Branch remains isolated: `research/supertrend-first-cross-one-trade-20261122`, output `analysis/supertrend_first_cross_one_trade/`. All existing second-crossover research artifacts untouched.
