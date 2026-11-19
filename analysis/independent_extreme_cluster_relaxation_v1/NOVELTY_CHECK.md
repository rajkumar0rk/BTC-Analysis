# Novelty gate — clustered extreme-arrival relaxation (2026-11-19)

Decision: **PARTIAL OVERLAP — approved differential**; this is NOT an ordinary single-shock fade or CUSUM threshold adjustment.

## Falsifiable economic hypothesis
After an unusually dense cluster of large hourly price changes, temporary urgency or inventory stress may dissipate, creating conditional return continuation or reversal once the rate of extremes subsides. Hourly OHLC can test only clustering of *returns*, NOT assert forced liquidations, order flow or market-maker inventory. Test whether the first quiet hour after >=3 abnormal-return arrivals in the preceding eight completed hours predicts the subsequent return; compare continuation and fade, and report costs and monthly equity. A simple matched baseline would compare unconditional quiet-hour entries with the same trade controls; not yet established as causal microstructure.

## Exact causal entry
At each completed hourly boundary, compute log return and its magnitude relative to a 48-hour historical rolling median absolute return, using strictly prior 48 complete hours. Extreme indicator = absolute return > 2.0 or 2.5 times prior median. Event when prior 8 completed hourly indicators contain at least 3 extremes, current completed hour is non-extreme, previous completed hour was extreme, and 48h history is available. Direction = sign of summed last 8 completed hourly returns; evaluate trend continuation and fade as predeclared alternatives. Entry at following minute open. Exclusive trades; 0.5% account-equity risk, 3x notional cap, 1.5x hourly ATR14 stop, 2.5R target, 12h max hold, stop-first/gap-aware 1m execution. Same parameters BTC and ETH; 2025-only joint selection, unchanged 2026 check.

## Closest prior work
- `scripts/independent_cusum_regime_shift_v1.py` on `research/independent-cusum-regime-shift-20261119-v1`: detects cumulative signed drift CUSUM; NOT event-arrival count or quiet-hour relaxation.
- `scripts/independent_bipower_jump_fade_v1.py` on `research/independent-bipower-jump-fade-20261118-v1`: detects single hourly jump dominance and immediate fade; NOT a multi-hour extreme-arrival cluster followed by rate normalization.
- `scripts/research_monthly_10pct_stage19.py` and `analysis/institutional_discovery_stage19_monthly_10pct/`: candle shock and RSI/breakout combinations, NOT time-clustered exceedance arrivals.
- `research/btc-eth-monthly-shock-reversion-20261118`: single shock reversion, NOT arrival-intensity conditioning.
- `research/btc-eth-hourly-directional-entropy-20261118`: direction entropy, NOT magnitude-exceedance count or relaxation transition.

## Data, validity, controls
Native Delta India original UTC-month gzip partitions and SHA256 manifest via shared verified loader; BTC repaired Oct31; ETH IST Jan1 2025 initial 5.5h unavailable. 22 IST months through October 2026; November excluded. 2026 research-exposed, not truly untouched. Fees 0.05% taker each side plus 18% GST; BTC >=5 points slippage per side; ETH 0.02% each side, stress-test. Funding, spread, impact, margin and lot-size omitted and disclosed. Monthly PF uses exit trade PnL, month-end NAV marks open positions. Reuse historical simulator only as execution baseline, NOT as evidence of new alpha.
