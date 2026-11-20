# NOVELTY_CHECK — 2026-11-20 10:42 IST
Decision: PARTIAL OVERLAP — approved differential (testable, not yet evidence of edge).
## Economic hypothesis
Continuous directional repricing during high realized variance may reflect persistent informed flow and produce convex trend continuation, unlike a single discontinuous liquidation jump that mean-reverts. The differentiator is *bipower-variation-estimated discontinuity fraction* of minute returns, rather than raw candle direction, hourly OHLC extrema order, signed volume or end-loaded volatility.
## Closest previous research
- scripts/research_independent_extrema_order_20261120.py — extrema order, not continuous-vs-jump decomposition; rejected, run 44667863689.
- prior independent variance-endload workflow — timing of variance, not bipower decomposition; rejected, run 44600868061.
- analysis/institutional_discovery_stage7_time_volume/ — volume/time patterns, not bipower jump decomposition.
- research/btc-first-shock-drift-stage31-20261119 — shock drift; this experiment explicitly excludes discontinuous jump-dominated bars rather than trading shock follow-through.
## Frozen deterministic rules
For each UTC hour require exactly 60 distinct contiguous 1m bars. Compute 59 within-hour log-close returns; RV=sum(r²); BV=pi/2 sum(|r_i||r_(i-1)|); jump fraction=max(0,RV-BV)/RV. Require 168 prior consecutive complete hours, current RV>1.5× median prior RV, jump fraction<0.20, directional efficiency>0.65, |hour log(close/open)|>0.002. Enter next hour first observed minute open, direction of hour return. One position; stop at 0.65% entry, risk 0.25% NAV; 2× max notional, 4R activation with 2R trailing offset; 48h max hold. Stop-first, gap-through adverse fills, no same-bar reentry. Model 0.05% taker fee each side plus 18% GST, 0.02% adverse slippage per side minimum $5 BTC, double slippage stress, reverse-direction control. 2025 BTC discovery is selection; unchanged 2026 BTC and ETH are checks. No retrospective tuning.
## Falsifier
BTC 2025 negative after-cost expectancy, insufficient independent trades, destructive drawdown, failure when largest winner removed, or poor cost robustness. ETH never selects rules.
## Data quality
Read original gzip minute bars from data/delta_india/{BTCUSD,ETHUSD}/1m, SHA256 each source, reject duplicate or malformed OHLCV. Jan 2025 IST start gap and October 2026 gaps may prevent complete month claims. Historical funding and order book are unavailable; results cannot be considered fully verified live economics.
