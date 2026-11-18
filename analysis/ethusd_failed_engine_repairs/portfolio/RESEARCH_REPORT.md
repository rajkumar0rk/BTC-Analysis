# ETHUSD six-failed-engine repair — portfolio

All source market data genuinely comes from ETHUSD; canonical BTC code untouched.
ETH prices are price-normalized for legacy rules; NOT native ETH 200-USD exits.
This is a repair of six failed engines, not 6 profitable strategies.

Previously failed engines rerun: 1
Repaired engines completed: 1

## Execution outcomes
- research_monthly_regime_stage14.py: **completed**, 10.0 seconds, 
- research_july_drawdown_stage15.py: **completed**, 1.89 seconds, 
- research_swing_donchian_stage17.py: **completed**, 2.62 seconds, 
- research_monthly_portfolio_stage18.py: **completed**, 0.45 seconds, 

## Source verification
- ETH mark / OI / funding source manifests: {"mark_1m": {"partitions": 23, "observations": 987840, "coverage_pct": 100.0, "original_symbol": "MARK:ETHUSD", "price_scaled": true, "prices_from": "ETHUSD, never BTCUSD"}, "open_interest_5m": {"partitions": 23, "observations": 197568, "coverage_pct": 100.0, "original_symbol": "OI:ETHUSD", "price_scaled": false, "prices_from": "ETHUSD, never BTCUSD"}, "funding_1h": {"partitions": 23, "observations": 16464, "coverage_pct": 100.0, "original_symbol": "FUNDING:ETHUSD", "price_scaled": false, "prices_from": "ETHUSD, never BTCUSD"}}

## Stage18 selection audit
{'stage18_qualified_2025_models': 0, 'stage18_selected_unqualified_fallback': True}
If Stage18 eligibility is 0, it is NOT a qualifying monthly-profitable selection.

## Model/monthly summaries
{'folder': 'institutional_discovery_stage17_swing_breakout', 'model': '4H_channel_24_ema50_agrees_trail_3atr', 'positive_months_2025': 7, 'positive_months_2026': 3, 'net_2025_pct': 6.0958, 'net_2026_pct': 5.4983, 'total_closed_trades': None, 'wins': None, 'losses': None, 'models_with_full_22_months': 16, 'any_22_positive_historical': 0, 'selected_by': '2025 only: profitable months, then 2025 compounded return'}
{'folder': 'institutional_discovery_stage18_monthly_dual_strategy', 'model': 'quiet_1h_weekly_3R + 1D_channel_55_ema50_agrees_trail_3atr + swing_75pct', 'positive_months_2025': 3, 'positive_months_2026': 6, 'net_2025_pct': 1.6714, 'net_2026_pct': 0.0036, 'total_closed_trades': None, 'wins': None, 'losses': None, 'models_with_full_22_months': 105, 'any_22_positive_historical': 0, 'selected_by': '2025 only: profitable months, then 2025 compounded return'}

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
