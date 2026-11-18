# Stage 12 — Before BTC's directional move: 1H/4H structure, volatility and participation

## Research design
- Keep the Stage 11 **8 entry patterns identical**: break-retest, sweep-reclaim,
  engulfing, inside-bar break, structure shift, compression breakout, etc.
- Test only market-state modifiers derived from completed higher-timeframe bars:
  4H or 1H trend agreement, countertrend pullback, volume/range participation,
  channel acceptance, 1H quiet-to-expansion transition, and 5m activity.
- Require >=16 fully complete consecutive 1H/4H candles for prior context.
- Entry = following 1m open; stop beyond completed structure; TP = 2R or 3R.
- One trade per configuration at a time, both LONG and SHORT.
- Compare each condition to the exact pattern with no condition.
- Standard taker + GST and adverse slippage included; separate conditional Scalper Offer study.
- Historical 2025 used for rankings, chronological 2026 already inspected, not pristine OOS.

## Best condition-specific 2025 models (research only)
| pattern   | environment   | reward_R   | hold_minutes   | trades   | win_pct   | avg_net_pts   | profit_factor   | avg_risk_pts   |
|-----------|---------------|------------|----------------|----------|-----------|---------------|-----------------|----------------|

## Those exact selections in the research-exposed 2026 periods
| pattern   | environment   | reward_R   | hold_minutes   | period   | trades   | win_pct   | avg_net_pts   | profit_factor   |
|-----------|---------------|------------|----------------|----------|----------|-----------|---------------|-----------------|

## Stable-positive filters (>=60/30/20 trades across 2025, H1 and H2)
No repeated positive setup at the chosen minimum sample sizes.

## How much did MTF filtering change net expectancy versus the same unfiltered entry?
| pattern   | environment   | reward_R   | hold_minutes   | trades   | baseline_trades   | avg_net_pts   | baseline_net   | delta_net_pts   |
|-----------|---------------|------------|----------------|----------|-------------------|---------------|----------------|-----------------|

## What cannot be claimed
- Unchanged Stage 11 structural 5m entry rules; only known-in-advance MTF market-state filters are added
- Completed 1H/4H candles, aligned to exact next-minute OPEN; prior 16 complete bars required to avoid stale gap joins
- 1H/4H structures, volume, slopes computed from historical completed candles only
- No time-of-day filter; entries can occur any day/hour
- Stops beyond confirmed setup levels, 2R/3R targets, <=4h holds
- Stop-first 1m OHLC tie; worse fill on stop gaps
- Separate strategy simulation per entry pattern/environment/R/hold; trades across models overlap
- 0.05% taker each side, 18% GST, 5-point adverse slippage per side
- Fee-offer sensitivity is conditional, not verified from historical executions
- No tick order book or realized bid/ask spread, market impact, margin, liquidation or funding cashflows
- Every 2026 period already investigated, not pristine independent validation
- Many comparisons cause selection bias; cannot guarantee positive expected results or no losses

Reproduce: scripts/research_pretrend_market_state_stage12.py; raw ledgers and
feature snapshots are stored as downloadable GitHub Actions artifacts.

