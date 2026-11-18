# ETHUSD — high_frequency strategy family backtest

BTC-Analysis native rule engines replayed on ETHUSD
via a fixed initial BTC/ETH price-normalization factor.
Original BTC source and prior reports were NOT changed.
Fixed normalization factor: 28.03749382
5 virtual price points of slippage = 0.17833 actual ETH USD
Fees: modeled 0.05% taker on each side plus 18% GST on fees
Target: 22 complete IST months Jan2025–Oct2026; November excluded.

## Engine status
- research_every_candle_200.py: **completed**, 58.69s
- research_time_day_volume_200.py: **completed**, 218.87s
- research_anytime_volume_volatility_patterns.py: **completed**, 6.33s
- research_adaptive_anytime_entries_stage9.py: **failed**, 0.24s — exit_code=1
- research_dynamic_exit_stage10.py: **completed**, 3.06s

## Completed source backtest model summaries


## Limitations
- Fixed ex-ante price normalization preserves BTC-coded absolute point thresholds in virtual units rather than forcing them on unscaled ETH prices
- Individual model labels may still print BTCUSD; data used is ETHUSD
- ETH order-book spreads, actual funding, maker fills, contract step sizes, liquidation and market impact not provided
- Fixed 5 virtual point adverse slippage is a proxy, not measured actual ETH execution
- Models may have hard-coded BTC-specific volume or OI assumptions; record these as limitations
- No on-chain or spot/perp cross-market hedging is inferred
- No guarantee of future profitability
