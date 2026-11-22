# Preregistered differential: 1H first EMA20 touch, no TP, 2× or 3×ATR14 trailing stop

User request 2026-11-22: "remove tp add 3xatr14 or 2xatr14" after the 1H first-touch filtered 1R test.

## Interpretation / assumptions
- **Remove all take-profit orders/targets**.
- Test **two distinct ATR-based trailing-stop settings** (2×ATR14 and 3×ATR14); comparison does not infer superiority without results.
- Last completed 1H Wilder ATR(14) at entry is **frozen as the trailing distance**: `D = multiplier*ATR14[previous completed 1H bar]`. 1H ATR14 does NOT update during position life in this sensitivity, so effects isolate the two multipliers rather than mixing volatility updates. ATR-based stop begins **immediately at entry** (not only after profit) and ratchets at every favorable 1-minute price extreme:
  - LONG: initial stop = executed entry − D, update = max(old stop, latest favorable price − D); if 1m price subsequently falls to/below stop, sell at stop (gap open through stop fills at open, with slippage).
  - SHORT: initial stop = executed entry + D, update = min(old stop, latest favorable price + D); if 1m price subsequently rises to/above stop, cover at stop (gap open through stop fills at open).
- Confirmed **opposite 1H Supertrend flip remains another exit**, executed at next 1H opening 1-minute price. First exit among ATR stop and confirmed ST flip wins. No 1R/2R fixed TP, no fixed point target, no profit lock. ATR stop is an additional protective exit and deliberately changes prior ST-flip-only stop semantics.

## All other rules identical to latest 1H filtered 1R baseline
- 1H ST with Wilder ATR10 multiplier3, 1H EMA20. Ignore flip candle. FIRST subsequent distinct 1H candle whose 1m path crosses last completed 1H EMA20 -> immediate entry in direction of confirmed ST, max one entry per ST epoch.
- BOTH gate on last fully completed 1H candle: volume >1.2×SMA20(volume), Wilder ATR14 >SMA20(ATR14). Reject first touch / whole ST epoch if either gate fails.
- BTCUSD and ETHUSD, 22 completed IST months Jan2025–Oct2026 from original SHA-verified 1m Delta India OHLC, both long and short 1x current-equity position sizing, initial $1000 per asset/multiplier, fee 0.05% taker per side + GST18%, adverse slippage 0.02% per side.
- Within each 1m bar replay two hypothetical continuous OHLC sequences O→H→L→C and O→L→H→C so that the ordering of EMA touch, trailing-stop ratchet and stop execution is explicit. These are NOT actual tick data or strict best/worst bounds. Intraminute path can change realized results.
- Report trades/wins/losses, ATR stop and ST flip exit counts, PF, net returns, every IST month MTM, max floating drawdown, insolvency, side-by-side vs prior 1R take-profit baseline. No real order-book, liquidation/margin, funding, spread, market impact or latency. 2026 is previously researched, not pristine OOS.

Prior matched reference: `analysis/st_firsttouch_1h_filtered_tp1r_20261122/` and script `scripts/research_st_firsttouch_1h_filtered_tp1r_flip_20261122.py`.
Novelty gate: **PARTIAL OVERLAP**, a user-requested alternative exit with no TP and ATR-based stop. Original research branch unchanged; do not merge to master.
