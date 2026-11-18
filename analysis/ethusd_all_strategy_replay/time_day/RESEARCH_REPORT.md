# ETHUSD — time_day strategy family backtest

BTC-Analysis native rule engines replayed on ETHUSD
via a fixed initial BTC/ETH price-normalization factor.
Original BTC source and prior reports were NOT changed.
Fixed normalization factor: 28.03749382
5 virtual price points of slippage = 0.17833 actual ETH USD
Fees: modeled 0.05% taker on each side plus 18% GST on fees
Target: 22 complete IST months Jan2025–Oct2026; November excluded.

## Engine status
- research_one_trade_every_day_200.py: **completed**, 12.35s
- research_time_day_strategies.py: **completed**, 38.55s
- research_price_action_time_day.py: **completed**, 7.82s
- research_previous_day_range_swing.py: **completed**, 41.13s
- research_selective_big_moves.py: **completed**, 2.69s
- research_daily_200_500_points.py: **completed**, 2.76s

## Completed source backtest model summaries


## Limitations
- Fixed ex-ante price normalization preserves BTC-coded absolute point thresholds in virtual units rather than forcing them on unscaled ETH prices
- Individual model labels may still print BTCUSD; data used is ETHUSD
- ETH order-book spreads, actual funding, maker fills, contract step sizes, liquidation and market impact not provided
- Fixed 5 virtual point adverse slippage is a proxy, not measured actual ETH execution
- Models may have hard-coded BTC-specific volume or OI assumptions; record these as limitations
- No on-chain or spot/perp cross-market hedging is inferred
- No guarantee of future profitability
