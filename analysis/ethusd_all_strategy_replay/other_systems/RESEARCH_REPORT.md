# ETHUSD — other_systems strategy family backtest

BTC-Analysis native rule engines replayed on ETHUSD
via a fixed initial BTC/ETH price-normalization factor.
Original BTC source and prior reports were NOT changed.
Fixed normalization factor: 28.03749382
5 virtual price points of slippage = 0.17833 actual ETH USD
Fees: modeled 0.05% taker on each side plus 18% GST on fees
Target: 22 complete IST months Jan2025–Oct2026; November excluded.

## Engine status
- research_retest_reclaim_stage4.py: **failed**, 0.26s — exit_code=1
- research_volatility_scaled_exits_stage5.py: **failed**, 0.26s — exit_code=1
- research_directional_acceptance.py: **failed**, 0.74s — exit_code=1
- research_behavioral_discovery.py: **failed**, 0.74s — exit_code=1
- research_big_trend_stage1.py: **completed**, 5.32s
- research_failed_auction_stage24.py: **completed**, 1.7s

## Completed source backtest model summaries

- institutional_discovery_stage24_failed_auction: {'folder': 'institutional_discovery_stage24_failed_auction', 'model': '1.5:2.0:720', 'positive_months_2025': 5, 'positive_months_2026': 2, 'net_2025_pct': -1.9996, 'net_2026_pct': -16.9274, 'total_closed_trades': 285, 'wins': 111, 'losses': 174, 'models_with_full_22_months': 8, 'any_22_positive_historical': 0, 'selected_by': '2025 only: profitable months, then 2025 compounded return'}

## Limitations
- Fixed ex-ante price normalization preserves BTC-coded absolute point thresholds in virtual units rather than forcing them on unscaled ETH prices
- Individual model labels may still print BTCUSD; data used is ETHUSD
- ETH order-book spreads, actual funding, maker fills, contract step sizes, liquidation and market impact not provided
- Fixed 5 virtual point adverse slippage is a proxy, not measured actual ETH execution
- Models may have hard-coded BTC-specific volume or OI assumptions; record these as limitations
- No on-chain or spot/perp cross-market hedging is inferred
- No guarantee of future profitability
