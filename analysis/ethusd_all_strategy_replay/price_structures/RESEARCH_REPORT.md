# ETHUSD — price_structures strategy family backtest

BTC-Analysis native rule engines replayed on ETHUSD
via a fixed initial BTC/ETH price-normalization factor.
Original BTC source and prior reports were NOT changed.
Fixed normalization factor: 28.03749382
5 virtual price points of slippage = 0.17833 actual ETH USD
Fees: modeled 0.05% taker on each side plus 18% GST on fees
Target: 22 complete IST months Jan2025–Oct2026; November excluded.

## Engine status
- research_structure_rr_stage11.py: **completed**, 8.74s
- research_pretrend_market_state_stage12.py: **completed**, 8.99s
- research_trend_pullback_breakout_stage13.py: **completed**, 1.65s
- research_monthly_regime_stage14.py: **completed**, 9.16s
- research_july_drawdown_stage15.py: **completed**, 1.86s
- research_monthly_regime_switch_stage16.py: **completed**, 3.7s
- research_swing_donchian_stage17.py: **completed**, 2.52s
- research_new_1h_patterns_stage19.py: **completed**, 3.33s
- research_monthly_portfolio_stage18.py: **failed**, 0.42s — exit_code=1
- research_three_sleeve_stage20.py: **completed**, 0.32s
- research_monthly_fixed_weight_stage21.py: **completed**, 14.68s

## Completed source backtest model summaries

- institutional_discovery_stage17_swing_breakout: {'folder': 'institutional_discovery_stage17_swing_breakout', 'model': '4H_channel_24_ema50_agrees_trail_3atr', 'positive_months_2025': 7, 'positive_months_2026': 3, 'net_2025_pct': 6.0958, 'net_2026_pct': 5.4983, 'total_closed_trades': None, 'wins': None, 'losses': None, 'models_with_full_22_months': 16, 'any_22_positive_historical': 0, 'selected_by': '2025 only: profitable months, then 2025 compounded return'}
- institutional_discovery_stage19_new_1h_patterns: {'folder': 'institutional_discovery_stage19_new_1h_patterns', 'model': 'failed_break_12h__4h_atr_ratio_le1__3R__480min', 'positive_months_2025': 8, 'positive_months_2026': 3, 'net_2025_pct': 11.7437, 'net_2026_pct': -14.8507, 'total_closed_trades': 174, 'wins': None, 'losses': None, 'models_with_full_22_months': 140, 'any_22_positive_historical': 0, 'selected_by': '2025 only: profitable months, then 2025 compounded return'}
- institutional_discovery_stage18_monthly_dual_strategy: {'folder': 'institutional_discovery_stage18_monthly_dual_strategy', 'model': 'quiet_1h_weekly_3R + 1D_channel_55_ema50_agrees_trail_3atr + swing_75pct', 'positive_months_2025': 3, 'positive_months_2026': 6, 'net_2025_pct': 1.6714, 'net_2026_pct': 0.0036, 'total_closed_trades': None, 'wins': None, 'losses': None, 'models_with_full_22_months': 105, 'any_22_positive_historical': 0, 'selected_by': '2025 only: profitable months, then 2025 compounded return'}
- institutional_discovery_stage20_three_sleeve: {'folder': 'institutional_discovery_stage20_three_sleeve', 'model': 'overextension_reversal__4h_atr_ratio_le1__2R__480min + auxiliary 20%', 'positive_months_2025': 9, 'positive_months_2026': 5, 'net_2025_pct': 1.626, 'net_2026_pct': -2.8132, 'total_closed_trades': None, 'wins': None, 'losses': None, 'models_with_full_22_months': 1, 'any_22_positive_historical': 0, 'selected_by': '2025 only: profitable months, then 2025 compounded return'}
- institutional_discovery_stage16_monthly_regime_switch: {'folder': 'institutional_discovery_stage16_monthly_regime_switch', 'model': 'risk_limited_regime_switch:month_profit_lock_plus3R', 'positive_months_2025': 6, 'positive_months_2026': 5, 'net_2025_pct': -0.7268, 'net_2026_pct': -1.9621, 'total_closed_trades': 177, 'wins': None, 'losses': None, 'models_with_full_22_months': 24, 'any_22_positive_historical': 0, 'selected_by': '2025 only: profitable months, then 2025 compounded return'}

## Limitations
- Fixed ex-ante price normalization preserves BTC-coded absolute point thresholds in virtual units rather than forcing them on unscaled ETH prices
- Individual model labels may still print BTCUSD; data used is ETHUSD
- ETH order-book spreads, actual funding, maker fills, contract step sizes, liquidation and market impact not provided
- Fixed 5 virtual point adverse slippage is a proxy, not measured actual ETH execution
- Models may have hard-coded BTC-specific volume or OI assumptions; record these as limitations
- No on-chain or spot/perp cross-market hedging is inferred
- No guarantee of future profitability
