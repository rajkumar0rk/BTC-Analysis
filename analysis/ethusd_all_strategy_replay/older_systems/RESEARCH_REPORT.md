# ETHUSD — older_systems strategy family backtest

BTC-Analysis native rule engines replayed on ETHUSD
via a fixed initial BTC/ETH price-normalization factor.
Original BTC source and prior reports were NOT changed.
Fixed normalization factor: 28.03749382
5 virtual price points of slippage = 0.17833 actual ETH USD
Fees: modeled 0.05% taker on each side plus 18% GST on fees
Target: 22 complete IST months Jan2025–Oct2026; November excluded.

## Engine status
- v7_2025_trend_discovery.py: **completed**, 2.06s
- research_v7_1_retest_2025.py: **completed**, 3.62s
- research_v7_2_daily_4h_2025.py: **completed**, 1.81s
- research_v8_2025_big_moves.py: **completed**, 13.31s
- research_v8_1_2025_exits.py: **completed**, 2.31s
- research_mtf_swing_range_long.py: **completed**, 32.42s
- research_mtf_swing_range_long_fixed2r.py: **completed**, 101.62s
- research_mtf_swing_range_short_fixed2r.py: **completed**, 102.96s
- research_mtf_swing_range_short_fixed3r.py: **completed**, 94.98s
- research_mtf_swing_range_fixed3r.py: **completed**, 91.76s
- research_mtf_uptrend_short_fixed3r.py: **completed**, 98.25s

## Completed source backtest model summaries


## Limitations
- Fixed ex-ante price normalization preserves BTC-coded absolute point thresholds in virtual units rather than forcing them on unscaled ETH prices
- Individual model labels may still print BTCUSD; data used is ETHUSD
- ETH order-book spreads, actual funding, maker fills, contract step sizes, liquidation and market impact not provided
- Fixed 5 virtual point adverse slippage is a proxy, not measured actual ETH execution
- Models may have hard-coded BTC-specific volume or OI assumptions; record these as limitations
- No on-chain or spot/perp cross-market hedging is inferred
- No guarantee of future profitability
