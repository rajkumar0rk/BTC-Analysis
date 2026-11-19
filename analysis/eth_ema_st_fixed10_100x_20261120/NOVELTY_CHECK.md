# ETHUSD EMA20 + ST 15m — novelty gate (2026-11-20)

Decision: **PARTIAL OVERLAP — approved cross-asset differential.** This is exactly the earlier BTCUSD setup re-evaluated on **independent ETHUSD 1m futures history**, with instrument-correct lot sizing and BTC-price-point to ETH-price-relative trailing conversion. It is not a newly discovered strategy and is NOT optimized.

Closest prior:
- `scripts/replay_btc_ema_st_screenshot.py` — original indicator implementation and 15m OHLC broker emulation; reuse indicator code.
- `scripts/replay_btc_ema_st_100x.py` — margin liquidation and original 15m OHLC stop trail; benchmark for scenario arithmetic.
- `scripts/replay_btc_ema_st_fixed_10_margin.py` and `analysis/btc_ema_st_fixed_10_margin_20261119/` — $100 account, fixed <=$10 isolated margin, 100×; full 15m OHLC trade path.
- `scripts/replay_btc_ema_st_fixed_10_margin_guarded.py` and `analysis/btc_ema_st_fixed_10_margin_guarded_20261119/` — 100× risk guard; 0 modeled liquidations but 14/22 losing full months.
- Other research stages in `codex/STRATEGY_NOVELTY_GATE.md` on unrelated entry families.

Experimental question: Does the identical *causal* strategy produce positive NET wallet P&L on **ETH** and remain economically viable after realistic contract sizes, fees, and liquidation exposure?

## Frozen setup
- Input ETHUSD Delta India UTC 1m partitions, SHA256 verified against `data/delta_india/ETHUSD/1m/manifest.json`; expected 2025-01-01 UTC through 2026-11-17 23:59 UTC; no missing candles in manifest; aggregate complete UTC-aligned 15m candles.
- Original `indicators()` implementation: EMA20, ST(10,3) established direction, 15m wick-touches-EMA and close confirmation. ATR(14) >= prior 20 ATR mean and volume >= prior 20 volume mean * 1.5. One position, entry at signal candle close. Stop 2x ATR14 (ETHUSD $0.05 tick). Opposite ST flip exits at 15m signal candle close.
- **Instrument rescaling**: BTC original trailing activation 150 points & trailing 50 points. Anchor BTC reference $80,000 (a precommitted round anchor, not optimized); ETH activation is **0.1875% of ETH entry** (150/80000); ETH trailing distance is **0.0625% of ETH entry** (50/80000), both rounded to ETH tick ($0.05). Both are FROZEN for each trade. These are converted relative distances and NOT the literal 150/50 ETH points, nor claimed identical to Pine settings on ETH. Initial stop remains 2x ETH ATR14.
- 1 ETHUSD contract = 0.01 ETH, tick $0.05 per Delta Exchange India; assumed max initial margin $10 per trade, 100× **isolated**, max notional $1000, floor contract quantity, never auto compound margin or auto top up. Portfolio starts $100 and carries net P&L.
- Taker 0.05% entry, 0.05% exit, GST 18% on charged fees, estimated liquidation charge 0.05%, 0% assumed funding, no spread/slippage, no actual exchange mark history, no TradingView bar magnifier. Avoid claiming realistic parity.
- Two fee regimes: (a) qualifying **30-minute ETH Scalper Offer assumed active across entire historical sample** to compare with previous BTC model, (b) **no offer** anywhere (conservative). Real historical offer timing/eligibility not verified. Liquidations always pay modeled liquidation charge.
- Liquidation maintenance model proxy 0.25% notional; two forced-fill bounds (estimated threshold, bankruptcy). Isolated position loss limited to posted margin plus entry fees from wallet.
- Second risk model is *separate*: pre-entry guard if initial ATR stop distance exceeds `1/100 - 0.0025 maintenance - 0.0025 safety buffer` = 0.5% of ETH entry. This differs from original signal and must be labeled separately.
- Report all 22 complete months (Jan 2025–Oct 2026), November 2026 partial, and 10,000 most recent 15m candles starting independently at $100; note August partially covered. Report count, win rate, PF, monthly returns, liquidations, portfolio drawdown, cost audit.
- Temporal caution: 2025/2026 have been exposed to research; no new holdout. Do not select parameters by in-sample results or claim live expectancy.

Only this research branch is modified. Do not merge main. Use reproducible GitHub Actions and retain monthly/trade files.
