# ETHUSD — five_minute strategy family backtest

BTC-Analysis native rule engines replayed on ETHUSD
via a fixed initial BTC/ETH price-normalization factor.
Original BTC source and prior reports were NOT changed.
Fixed normalization factor: 28.03749382
5 virtual price points of slippage = 0.17833 actual ETH USD
Fees: modeled 0.05% taker on each side plus 18% GST on fees
Target: 22 complete IST months Jan2025–Oct2026; November excluded.

## Engine status
- research_monthly_10pct_stage19.py: **completed**, 13.09s
- research_signal_inversion_stage20.py: **completed**, 90.1s

## Completed source backtest model summaries

- institutional_discovery_stage19_monthly_10pct: {'folder': 'institutional_discovery_stage19_monthly_10pct', 'model': 'compression_break:hour_align:atr1p5:2.0:240:5.0:5.0', 'positive_months_2025': 5, 'positive_months_2026': 1, 'net_2025_pct': -65.6094, 'net_2026_pct': -86.7737, 'total_closed_trades': 557, 'wins': None, 'losses': None, 'models_with_full_22_months': 1440, 'any_22_positive_historical': 0, 'selected_by': '2025 only: profitable months, then 2025 compounded return'}
- institutional_discovery_stage20_inverse_direction: {'folder': 'institutional_discovery_stage20_inverse_direction', 'model': 'compression_break:original:large_atr:atr3:1.5:120:2.0:5.0:offer_whatif', 'positive_months_2025': 6, 'positive_months_2026': 2, 'net_2025_pct': 3.1176, 'net_2026_pct': -13.8523, 'total_closed_trades': 45, 'wins': None, 'losses': None, 'models_with_full_22_months': 15120, 'any_22_positive_historical': 0, 'selected_by': '2025 only: profitable months, then 2025 compounded return'}

## Limitations
- Fixed ex-ante price normalization preserves BTC-coded absolute point thresholds in virtual units rather than forcing them on unscaled ETH prices
- Individual model labels may still print BTCUSD; data used is ETHUSD
- ETH order-book spreads, actual funding, maker fills, contract step sizes, liquidation and market impact not provided
- Fixed 5 virtual point adverse slippage is a proxy, not measured actual ETH execution
- Models may have hard-coded BTC-specific volume or OI assumptions; record these as limitations
- No on-chain or spot/perp cross-market hedging is inferred
- No guarantee of future profitability
