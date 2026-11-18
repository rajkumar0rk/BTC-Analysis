# Pre-run novelty gate — mark-vs-last dislocation mean reversion
Decision: **NEW candidate signal, conditional on data quality checks**.
Date: 2026-11-18. Separate branch; main and unrelated research untouched.

## Hypothesis and exact causal rules
Use ORIGINAL Delta India 1-minute BTCUSD and ETHUSD trade-price OHLC and their respective independent MARK:BTCUSD / MARK:ETHUSD 1m mark-price candles. Compute 5m completed-candle last-trade close vs mark close premium (last/mark - 1). On each completed 5m candle, compute 24-hour trailing rolling mean and standard deviation of that premium using only 288 *completed* 5m observations. If the standardized dislocation z-score exceeds a preset threshold 2.0 or 3.0, SELL last-trade futures, or if below negative threshold BUY. Enter at the following 1m open, not on the signal candle. Initial stop 1.5x or 2.5x causal 5m ATR14; target is 2x stop distance; timeout 12h; one position per asset, no pyramiding. Stop-first on each minute, gap-aware. Sizing 0.5% NAV risk per trade, capped 3x notional. One fixed rule set tested identically for both assets. 2025-only selection, 2026 diagnostic historical period. Account NAV marked at calendar month-end; trade PnL booked at exit. Fees 0.05% per side +18% GST, BTC 5 points slippage per side, ETH 0.02% per side. Avoid forced month-end exits. All 22 months shown even if negative.

## Closest prior work and economic novelty
- codex/STRATEGY_NOVELTY_GATE.md, stages 2–4 OI/price action and institutional carry stage1 funding/basis proxies: these use open interest or funding-rate carry rather than observed native *mark-to-last 5m dislocation* and 24h z-score convergence.
- scripts/research_btc_eth_profit_factor_pairs.py, 52 prior candle/indicator families: these rely on OHLCV price-action patterns, not separate MARK: series.
- research/independent-pairs-residual-20261118-v1: two-leg BTC-vs-ETH residual, not within-instrument mark-to-last dislocation.
- research/btc-eth-hourly-wick-imbalance-20261118: OHLC wick imbalance, not last-vs-mark.
- Partial overlap with mean reversion as a general economic thesis; increment is previously unused independent historical mark-price series. If historical MARK is algorithmically tied to last price and offers no genuine independent signal, reject as unsuitable.

## Data and validation
Verify original 22 1m UTC partition SHA256 manifests and mark native source, timestamps, no duplicates/gaps, no Jan2025 IST first 5.5h, 2026-10-31 BTC repaired partition, exclude November 2026. Mark history manifest reports 100% dense through 2026-11-17, but verify row alignment and economic meaning. 2026 already researched, NOT virgin out-of-sample. No historical L2 spreads or real fills. No changes to existing code. Preserve exact 22-month BTC and ETH monthly ledgers and trade ledgers. No leverage escalation, no live orders.
