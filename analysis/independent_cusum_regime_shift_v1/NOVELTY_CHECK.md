# NOVELTY CHECK — sequential CUSUM drift-change (2026-11-19)

Decision: **PARTIAL OVERLAP — approved differential**. It is not a renamed breakout or candle-shock test; the statistical event is a sustained *sequence* of abnormal returns accumulating beyond a drift-adjusted volatility budget. However, its economic thesis overlaps momentum continuation and reversal, and no guaranteed novel edge is claimed.

## Predeclared causal hypothesis

At the close of each complete 1H bar reconstructed from original native 1m BTCUSD/ETHUSD, compute log close-to-close return. Estimate mean and standard deviation from the *prior* 48 complete hourly returns only. Set z=(current return - prior mean)/prior std, clipped to [-5,5]. Update one-sided CUSUM scores P=max(0,P+z-kappa), N=min(0,N+z+kappa). Emit a directional event if P>=h (+) or N<=-h (-), then reset both scores. The detector uses past and current complete bars only and enters at the following 1m open. Test both CONTINUATION and CONTRARIAN position side with the EXACT same signal calculation on both coins. No hindsight regime/month switch.

Predeclared grid: kappa in [0.20,0.40], threshold h in [3.5,5.0], direction in [continuation,contrarian], 1h ATR(14) 1.5x stop, target 2.5R, maximum 12h holding, 1m stop-first gap-aware execution. Risk per trade 0.5% sequential realized account equity, max gross notional 3x account equity, one trade at a time. Initial equity $1,000 per market. Model exchange taker fee 0.05% each side plus GST 18%, BTC 5 USD points adverse each side, ETH 0.02% adverse each side; report sensitivity with doubled adverse slippage for the 2025-selected candidate. No martingale, no fixed BTC points copied to ETH as strategy parameters.

For selection score candidates **only on combined BTC+ETH 2025 results** using monthly material-return consistency and drawdown penalties; apply exactly one shared selected parameter combination to both 2026 series without retuning. The research-exposed 2026 sample is a historical check, not genuinely untouched OOS.

## Closest prior strategies and differences

- `scripts/research_monthly_10pct_stage19.py`, `analysis/institutional_discovery_stage19_monthly_10pct/`: price-pattern breakout/shock/RSI/EMA events and 1m stops. Our detector integrates the sequence of mean-adjusted normalized hourly returns and fires on CUSUM boundary crossing, rather than comparing a candle or fixed lookback extremum.
- `analysis/independent_stage25_hourly_trend/` on `research/stage25-new-trend`: 1H momentum/inside bar/trend tests. Both test direction, but that study does not use a stateful sequential statistical change detector.
- `analysis/independent_bipower_jump_fade_v1/` and `scripts/independent_bipower_jump_fade_v1.py` on the base reference: single-bar shock conditioned on estimated discontinuous-vs-continuous volatility, rather than cumulative signed likelihood-like drift.
- `research/btc-eth-hourly-directional-entropy-20261118`, `research/efficiency-shock-trend-20261118-2331`: path entropy/directional efficiency signals, not one-sided CUSUM with lagged standardized residuals.

A GitHub branch-name search for CUSUM and code search for `cusum`, `change point`, and `sequential drift` on main returned no matches on 2026-11-19. This is not proof there are no similar unpublished experiments. Retain "partial overlap" classification, not claim invention of a brand-new market mechanism.

## Input and validation quality

Native Delta India BTCUSD and ETHUSD UTC monthly gzipped CSV source partitions verified against SHA256 and observed-minute manifests by `scripts/eth_native_crossfamily_v2.py`; inspect the 2026-10-31 repaired BTC partition and ETH original data from those manifests at runtime. Original 2025-01 history starts 00:00 UTC, omitting first 5.5 IST calendar hours. Test only Jan 2025–Oct 2026 IST calendar months, exclude November, do not force liquidation at intermediate month ends. For each month report exit-month net-trade PF and month-end marked-to-market account equity return separately, net USD exit PnL, trades/wins/losses, drawdown; year figures compound from same monthly NAV.

Known omissions: actual bid/ask spread, funding settlement, market impact, margin/liquidation and contract lot restrictions; report clearly and reject unrealistic performance. Intraminute OHLC ambiguity resolved stop-first; adverse stop gaps filled at minute open and slippage charged. Backtest is not proof of achievable live profit.

## Isolation

Only `research/independent-cusum-regime-shift-20261119-v1`; new runner `scripts/independent_cusum_regime_shift_v1.py`, workflow `.github/workflows/independent-cusum-regime-shift-v1.yml`, outputs `analysis/independent_cusum_regime_shift_v1/`. Prior code imported only for data loading/manifest verification and account replay base implementation; prior trade selections and results are not used. No live orders, main modifications, or unrelated schedule changes.
