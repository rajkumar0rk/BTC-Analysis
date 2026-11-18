# ETHUSD six-failed-engine repair — institutional

All source market data genuinely comes from ETHUSD; canonical BTC code untouched.
ETH prices are price-normalized for legacy rules; NOT native ETH 200-USD exits.
This is a repair of six failed engines, not 6 profitable strategies.

Previously failed engines rerun: 4
Repaired engines completed: 4

## Execution outcomes
- research_behavioral_discovery.py: **completed**, 4.34 seconds, 
- research_directional_acceptance.py: **completed**, 4.34 seconds, 
- research_retest_reclaim_stage4.py: **completed**, 4.13 seconds, 
- research_volatility_scaled_exits_stage5.py: **completed**, 5.76 seconds, 

## Source verification
- ETH mark / OI / funding source manifests: {"mark_1m": {"partitions": 23, "observations": 987840, "coverage_pct": 100.0, "original_symbol": "MARK:ETHUSD", "price_scaled": true, "prices_from": "ETHUSD, never BTCUSD"}, "open_interest_5m": {"partitions": 23, "observations": 197568, "coverage_pct": 100.0, "original_symbol": "OI:ETHUSD", "price_scaled": false, "prices_from": "ETHUSD, never BTCUSD"}, "funding_1h": {"partitions": 23, "observations": 16464, "coverage_pct": 100.0, "original_symbol": "FUNDING:ETHUSD", "price_scaled": false, "prices_from": "ETHUSD, never BTCUSD"}}

## Stage18 selection audit
{}
If Stage18 eligibility is 0, it is NOT a qualifying monthly-profitable selection.

## Model/monthly summaries

## Limitations
- All BTC strategy engines and original results remain unchanged
- ETH futures and mark OHLC scaled by the SAME fixed Jan 1 2025 BTC/ETH price ratio; ETH open interest and funding copied without price scaling
- BTC-coded 200 price-point exits are VIRTUAL scaled points, NOT $200 ETHUSD exits; native ETH ATR reports are separate
- No OI, mark or funding series is taken from BTC history; no fake market data
- Fee model of original engines: modeled Delta India taker 0.05% per leg + 18% GST and 5 VIRTUAL points slippage per leg
- Additional actual ETH order-book spread, funding paid over held trades, liquidation and market impact are not fully simulated
- Months January 2025–October 2026 only; November incomplete and excluded from claims
- January 2025 IST begins five and a half hours before the January 1 UTC archive and is not fully covered
- Rerun engine completed != trade profitable; monthly consistency requires positive after-cost returns in all 22 months
