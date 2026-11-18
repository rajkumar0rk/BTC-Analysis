# Novelty check — bipower-variation jump fade (2026-11-18)

Decision: **NEW conditional on distinct bipower signal**, not a reparameterization of price-change shock filters.

## Predeclared deterministic hypothesis
Compute completed hourly log returns from native Delta India 1m OHLC. Over the trailing 24 **completed** hourly returns calculate realized variance RV = sum(r²), bipower variation BV = (pi/2) sum(|r_t| |r_(t-1)|) and jump fraction J=max(0,RV-BV)/RV. At the close of an hour, when J is above 0.25 or 0.40, and that hour's absolute return exceeds 1.8 or 2.5 times the lagged 24-hour hourly-return RMS, enter a **fade** (opposite last hourly direction) at the next 1m open. Exits: stop-first each native 1m high/low, ATR-based 1.5x stop, 2R take profit, 12h time stop; risk 0.5% of equity/trade, 3x notional cap, exclusive positions. Identical dimensionless rules BTC and ETH. 2025-only configuration ranking, 2026 no retuning.

## Closest prior research / economic distinction
- `analysis/independent_mark_last_dislocation_v1/` and `scripts/independent_mark_last_dislocation_v1.py`: native mark-versus-last premium anomaly, **not** realized-vs-bipower variation.
- `analysis/institutional_discovery_stage19_monthly_10pct/`, `scripts/research_monthly_10pct_stage19.py`: candle-based shock, RSI and breakout filters; no jump fraction RV−BV.
- `research/btc-eth-monthly-shock-reversion-20261118`: shock reversion based on candle shock; proposed signal distinguishes isolated jump variance from continuous volatility via bipower variation. This is a different measurable causal state; compare outcome, do not claim full independence from shock family.
- `research/independent-stage26-semivariance`: downside/upside variance imbalance, not bipower continuous-variance estimate.
- `research/btc-eth-hourly-return-autocorr-20261118`: serial correlation, not realized-vs-bipower variance decomposition.

## Quality and validation
Native BTCUSD/ETHUSD 1m original history, native data SHA checks via existing loader, 2025 Jan–2026 Oct IST months, no November. BTC Oct31 repaired original partition and ETH 2025-01-01 first 5.5h gap require verification via loader/manifests. 0.05% taker fee each side + 18% GST, BTC adverse 5 points/side, ETH 0.02%/side, stop-first, no month-end liquidation; month-end NAV vs exit-month PF. Unmodeled funding, actual spreads, market impact, margin/liquidation and lot rules. Research-exposed 2026 is not untouched OOS. If month-end NAV cannot be accurately marked, flag rather than treat exit-month PF as NAV return.
