# Novelty review — second EMA9/21 crossover in the Supertrend regime

Date 2026-11-22. Decision: **NEW signal rule** compared with all prior Supertrend+EMA research; user-specified ordered two-event entry.

## Exact entry specification (frozen before results)

- **LONG:** Wait until Supertrend ATR(10) × 3 changes to GREEN. Then count only fully CLOSED EMA9-above-EMA21 bullish crossover events while Supertrend stays GREEN on both the previous and current closed bars. The **first** bullish crossover is recorded but NEVER traded. Enter BUY at the **next 1-minute OPEN following the second bullish crossover** (and only that crossover) while ST remains green. No second crossover => NO trade. A bearish EMA crossover between the first and second is allowed and necessary for a second bullish crossover.
- **SHORT:** Wait until Supertrend flips RED. Count only closed bearish EMA9-below-EMA21 crossovers while Supertrend remains RED on previous and current completed bars; enter at the next 1m open after the **second** bearish crossover only.
- When Supertrend switches color in either direction, **reset both counts** and mark new active regime; do not count simultaneous Supertrend flip/EMA crossover. A further third, fourth etc. crossover in the same Supertrend color regime **cannot initiate further entries** even if the first second-crossover signal occurred while another trade was open; there is at most one signal per Supertrend regime.
- EMA9 crossover formula: fast previous <= slow previous AND fast current > slow current; bearish previous >= slow previous AND fast current < slow current. Crossover tested on one independent completed 5m/15m/60m timeframe, not aligned 1H/15M/5M multi-TF signals.
- Warm-up 100 full bars; no partial candle signals, no lookahead, no repaint.
- In examples: green and first cross only => no entry; green and two crossovers up with intervening down-cross => one LONG; green flips red between two crosses => reset, never enter; green flips at same instant as cross => that cross not counted.

## Relation to existing studies and novelty assessment

- `analysis/supertrend_first_ema_cross/` on `research/supertrend-first-ema-cross-20261122`: **first** EMA crossover after Supertrend already favorable, not the second. That baseline is different and may not be relabeled as second-cross results.
- `analysis/supertrend_ema921_rr_ratios/` on `research/supertrend-ema921-rr-ratios-20261122`: entries triggered by alignment of indicators; not a second crossover.
- `analysis/supertrend_ema921_fixed_grid/` and original `analysis/supertrend_ema921/`: same alignment-entry family; not second crossover.
- `analysis/ema921_fixed100_200/` and `analysis/ema921_1h15m5m_rr/`: EMA-only MTF confirmation; no Supertrend event count.
- `analysis/independent_stage25_hourly_trend/` on `research/stage25-new-trend`: different trend/breakout signal components.
- This is substantive **entry sequence gating**, not a fixed-exit parameter optimization. Research-only branch; do not merge or deploy.

## Freeze all remaining assumptions to compare fairly

- Original historical Delta Exchange India BTCUSD perpetual 1m bars `data/delta_india/BTCUSD/1m`, Jan 2025–Oct 2026 IST. Jan 2025 first 330 minutes absent, other months complete. Reject source minute gaps. No external downloaded prices.
- Every independent 5-minute, 15-minute, 1-hour timeframe, with real 1-minute entry at next OPEN and 1-minute fixed SL/TP high/low first-touch simulation. Favor stop when stop and TP hit in same 1m candle, account for adverse stop-gap at 1m open.
- 20 unique fixed TP/SL pairs exactly as first-cross experiment: 1:3 = [100/300,150/450,200/600,300/900,400/1200,500/1500,600/1800,800/2400,1000/3000]; 1:4 = [100/400,200/800,300/1200,400/1600,500/2000,600/2400,800/3200,1000/4000]; additional [100/200,200/2000,1000/2000]. **60 configurations**, no adding candidates after viewing results.
- Single open position; second-cross entry ignored if position already active, no waiting to queue missed signals. Only one second-cross signal per ST regime. No trade/day cap; weekends allowed. Positions flattened IST calendar-month end for isolated monthly results.
- 1× compounded notional, 0.05% taker per side, 18% GST on fee, adverse $5 BTC price-point slippage per side. No real-time orderbook, true spread, funding/liquidation/margin or live slippage measurement.
- Report all trades, wins/losses, win%, profit factor, compounded net 1× account return, monthly profitability counts, monthly returns, and max trade-close drawdown. Store complete trade ledger and signal counts.
- Both 2025 and 2026 data are research-exposed, not a blind out-of-sample holdout. Historical performance cannot prove future profitability.

## Must-pass unit tests

1. One bullish EMA crossover after ST turns green does not trade.
2. Second bullish crossover in the SAME green regime triggers exactly once.
3. ST flips while waiting: count resets and subsequent one crossover alone does not trade.
4. Simultaneous ST turn-green and cross-up does not count as first crossover.
5. After the second cross triggered, the third cross cannot trigger another trade in same ST regime.
6. Shorts identical, with two cross-down events and continuous red Supertrend.

Outputs saved in `analysis/supertrend_second_ema_cross/`, separately from all previous experiments.
