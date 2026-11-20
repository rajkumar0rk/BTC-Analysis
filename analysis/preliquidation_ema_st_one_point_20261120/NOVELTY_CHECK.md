# Novelty / comparison gate: 1 BTC-point pre-liquidation stop (2026-11-20)

Decision: **PARTIAL OVERLAP — explicit risk/fee differential**, not a new entry strategy. Reuse exactly the prior BTC/ETH EMA20 + Supertrend 15m entries, volume/ATR filters, 2xATR original stop, ETH scaling, $100 wallet, <=$10 isolated initial margin, 100x leverage, and historical modeled 30-minute offer.

Prior sources: scripts/replay_btc_ema_st_fixed_10_margin.py and scripts/replay_eth_ema_st_fixed10_100x.py. These remain unchanged. The original BTC optimistic replay included 42 modeled liquidations, ETH 113.

Single change: pre-liquidation EXIT price one BTC dollar before each position's approximate liquidation threshold (LONG threshold+$1, SHORT threshold-$1), ETH equivalent derived from ETH entry / $80,000 BTC reference rounded UP to $0.05 tick. Initial position stop is whichever of pre-liquidation and original ATR stop is closer to entry. Existing trailing rule continues tightening stop. **Do not reject entries based on liquidation/ATR distance.**

Input data original verified 1-minute partitions; price path original estimated 15m OHLC. An opening gap beyond liquidation STILL liquidates. If OHLC path touches protective stop before liquidation, this model assumes fill at exact stop (zero latency and slippage), an **optimistic assumption especially dangerous with a 1-dollar buffer**. Liquidation uses a maintenance proxy on traded OHLC, not actual historical exchange mark price. Real stop trigger/fill may occur after liquidation. Fee/GST/offer entitlement historical not proven, funding/spread omitted.

This is a fee-impact scenario analysis, NOT executable stop guarantee. Results may overestimate fewer liquidations and net gains. No new untouched holdout. When comparing outputs never conflate historical baseline with true forward price process. The live futures runner uses the exchange position API's reported liquidation price, not the model.
