# Novelty check — prior-channel compression breakout
Decision: **PARTIAL OVERLAP — differential audit, not a novel original family**.

## Deterministic setup
Use completed 1h candle closing beyond prior 12/24/48h high/low channel, whose prior width / lagged ATR is <= 3/5/8. Require directional candle body / current ATR >= 0.3/0.6; execute next 1m open; ATR stop 1.5 or 2.5, target 2R or 3R, 1-day timeout, one position at a time, 0.5% stop-risk capped at 3x notional. Matched BTC/ETH native 1m replay with 0.05% per-side fee + GST, BTC 5 points adverse slippage per side, ETH 0.02% per side. Close at IST month boundary per inherited simulator.

## Overlap and incremental distinction
- codex/STRATEGY_NOVELTY_GATE.md lists Stage19 and Stage23 compression and Stage24 15m squeeze breakout (research/stage24-monthly10, analysis/institutional_discovery_stage24_structure_monthly10).
- research/stage25-new-trend, analysis/independent_stage25_hourly_trend includes hourly momentum and breakout.
- scripts/eth_native_crossfamily_v2.py includes Donchian breakout and inside-bar strategies.
This is **not** a wholly novel idea: it is a matched cross-market, ATR-normalized prior-channel compression width conditional on 1h confirmed close and body, with monthly PF and account return, explicitly testing incremental regime conditioning. Prior family reports cannot be substituted for this exact paired comparison. Do not claim an original signal discovery.

## Quality and split
Use SHA-checked original native Delta India 1m partitions for BTC and ETH, BTC repaired October UTC source where present; Jan2025 IST first 5.5 hours missing; 2026 historical sample previously inspected. Select candidate variants using 2025 only, 2026 descriptive validation. No funding, verified spreads, market impact, lot/margin/liquidation included. No full live reproducibility. Historical profit is not forward proof.

## Important limitation
This record was committed after the workflow was first queued; the pre-run novelty gate ordering was not satisfied. Treat output as a supplemental differential audit, not as a novelty-passing independent discovery. Do not use this to bypass future pre-run novelty checks.
