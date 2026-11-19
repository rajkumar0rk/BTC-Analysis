# Exact user-requested portfolio sizing replay (2026-11-19)

**Novelty decision: PARTIAL OVERLAP — approved position-sizing differential.** This is not a new alpha discovery. Reuse existing engine and compare a different economic allocation.

## Original source and nearest prior studies
- `scripts/replay_btc_ema_st_screenshot.py` and `analysis/btc_ema_st_screenshot_20261119/`: confirmed 15m EMA20/Supertrend screenshot signal; native 150/50 trailing with ATR(14)*2 initial SL, same-bar exit.
- `scripts/replay_btc_ema_st_100x.py` and `analysis/btc_ema_st_100x_20261119/`: 100x isolated margin with **full available portfolio** reinvested each trade. This user's variant differs materially because **only $10 of margin** is allocated per trade, even if portfolio balance is $100 or grows.
- `scripts/research_monthly_10pct_stage19.py`: related but different EMA pullback studies, not this particular 15m execution replay.

## User-requested deterministic settings
- Account starts with $100; trade uses **at most $10 isolated initial margin** per position at 100x, about $1000 notional. Unallocated wallet capital is not added automatically to isolated positions.
- Position notional is $1000 maximum, subject to rounding down to 0.001 BTC contract units. Thus actual assigned margin is <=$10. If available wallet is insufficient for that fixed planned position + opening fee and GST, **skip trade**; do not silently shrink to a $5 margin trade or enlarge when account grows.
- One open position at a time, no compounding of per-trade margin despite changing total account equity; portfolio balance accumulates realized P&L and costs.
- EMA20 / confirmed Supertrend ATR10 factor3 established trend; 15m signal close, 15m stop checks; ATR14 >= prior 20 ATR mean and volume >= 1.5x prior 20 volume mean; initial stop 2x ATR14, fixed trail activates at 150 BTC price points and follows by 50 points, opposite confirmed Supertrend flip closes.
- Delta India BTCUSD 1m source verified SHA-256; aggregate complete 15m bars without lookahead.
- Taker fee 0.05% entry / 0.05% exit; exit fee waived if trade held at most 30 minutes, assuming entire sample has offer active (historical offer entitlement not verified); GST 18% on charged fees; modeled liquidation charge 0.05% and GST; zero assumed funding and slippage, not actual realized amounts.
- Isolated margin maintenance assumed 0.25%; all liquidations use historical traded price as **proxy** for unprovided exchange mark price, with threshold and bankruptcy-price stress exit models; bankruptcy loss of isolated position cannot directly consume reserve wallet beyond posted isolated margin, except separately paid opening fees. Ignore insurance fund and actual tier/liquidation fees.
- Report complete calendar months Jan2025-Oct2026 and partial Nov2026, plus a separate August 6–Nov 18 start-from-$100 test (last 10,000 15m bars). Per-month return uses portfolio balance at start of month; include fees, GST, liquidation charges and actual number of trades.
- **No optimization, no retuning**; past results have been research-exposed, not an independent holdout. The main branch must remain untouched.

These assumptions permit research-only performance estimates; they cannot guarantee matching TradingView, exchange liquidation, or actual live fills.
