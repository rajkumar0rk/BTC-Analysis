# Stage18/20 monthly-improvement attempt: independent BTC 1H breakout edge

## Verified executed research

- [New independent BTC 1H signals and 1m exits — run 44663189203](https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44663189203): success.
- [Independent 1m cost-engine parity and alternative trailing/TP exits — run 44663629644](https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44663629644): success. On original zero-stress config, custom cost-engine reproduced **198 trades and every month-end NAV exactly** (maximum drift 0).
- Branch `research/stage18-stage20-independent-hourly-edge-20261120-v1`, no main merge or live orders. Each run's Actions artifact holds complete results, 22-month NAV tables and native 1m trade ledgers.

## Independent strategy selected using BTC 2025 alone

**48 completed 1-hour-bar Donchian breakout**, 4-hour EMA20/EMA50 trend filter and hour EMA20/50 confirmation, next 1-minute candle open entry, 2x 1H ATR(14) structural stop, original 2x ATR trailing updated only on completed 1H bars, opposite signal or max 14-day time exit. One position per standalone strategy, risk 0.5% of NAV per trade, reject theoretical implied leverage >3x at signal. No fee discounts or maker assumptions.

16 distinct strategies tested: 1H channel breakouts 24/48/72, EMA-pullback continuations, trend/volume filters, 2x/3x/4xATR trailers. Winner selected using 2025 return, number of positive months and month-end DD. BTC 2026 was **not used** to rank choices, but it has been researched previously and is NOT pristine out-of-sample.

| BTC standalone, January 2025–October 2026 | Base fills | Extra 2 bps adverse slippage each side | Extra 5 bps each side | Extra 10 bps each side |
|---|---:|---:|---:|---:|
| Net compounded 22m | **+16.9431%** | +12.7836% | +6.8184% | **−2.4349%** |
| Full 2025 | +7.2669% | +5.0632% | +1.8412% | −3.3131% |
| Jan–Oct 2026 | +9.0207% | +7.3483% | +4.8872% | +0.9083% |
| Net trade-R profit factor | 1.3559 | 1.2692 | 1.1527 | **0.9892** |
| Profitable / losing calendar months | 12 / 10 | 12 / 10 | 12 / 10 | 10 / 12 |
| Completed trades | 198 | 198 | 198 | 198 |

Fee/slippage baseline: 0.05% taker EACH side plus GST18% on taker fees and adverse 5 BTC price points each side, based on the original Stage17 code. Extra 2/5/10bps EACH side represents worsening fills and isn't observed historical L1 spread evidence.

## Why the new signal did NOT solve Stage18/20 monthly consistency

The standalone breakout has only **12 profitable months out of 22**. Capital-neutral blends that substitute a 25% or 50% allocation to the new signal for part of Stage18/20 typically improved return slightly while worsening monthly consistency. Examples at base modeled fills:

| Existing baseline (22m) | Original return / positive months | 25% new signal mix return / positive months | 50% new signal mix return / positive months |
|---|---:|---:|---:|
| Stage18 fixed 5R | +12.0163%, 15/22 | +13.38%, 15/22 | +14.66%, **13/22** |
| Stage18 wider regime / no weekly entry guard | +13.8790%, **18/22** | +14.80%, **15/22** | +15.62%, **13/22** |
| Stage20 fixed 5R | +9.5921%, **18/22** | +11.53%, **15/22** | +13.40%, **13/22** |
| Stage20 wider regime / no weekly entry guard | +11.2282%, **18/22** | +12.78%, **16/22** | +14.25%, **13/22** |

The blends are monthly capital reallocations, **not integrated native concurrent fills**, with rebalancing transaction costs and cross-collateral margin unknown. Never use full base return + full new signal return as if the same risk/collateral could earn both without consequence.

## Actual alternative exit replay and failure

12 alternative exit variants (delayed trailing activation after +1/2/3R, ATR trail spacing, fixed 5R/8R targets) were executed under an independently coded 1m cost model and reconciled exactly against the original 198-trade ledger at base settings. **Winner from BTC 2025 under +5bps/side stress was activate 2R → 2xATR trailing + 8R TP cap.** But it significantly disappointed in the already-seen chronological 2026 period:

| Exit | 2025 base | 2026 Jan–Oct base | 22m base | 22m with +5bps/side |
|---|---:|---:|---:|---:|
| Original immediate 2xATR trailer | +7.27% | **+9.02%** | **+16.94%** | **+6.82%** |
| BTC-2025-selected 2R activation / 2xATR / 8R TP | +10.17% | **−1.72%** | +8.28% | −0.02% |

This is a direct example of why 2025 optimization alone does not prove an exit is robust.

## Decision and remaining execution blockers

**RESEARCH LEAD only. Not a validated solution to monthly consistency, not live ready.**

- This higher-expectancy standalone breakout is directionally promising on the historical 1m *midprice* tape, but has too many losing months and significant extra-fill-cost fragility.
- The old Stage18/20 baseline remains superior for profitable-month count.
- Neither 2025 nor 2026 is a pristine independent holdout: many historical strategies and outputs already inspected.
- Historical data have known missing source periods (earliest Jan2025 IST and October31 2026 UTC).
- Native ETH backtest, historical funding, actual bid/ask, integer lot requirements, portfolio shared margin/liquidation, rebalance costs and paper-trade forward validation have NOT been completed.
- Model-only monthly equity drawdown understates intramonth peak-to-trough and risk of liquidation; 1m OHLC does not prove tick-level stop fills.
- Future work: validate execution/costs at 1m and new forward paper data; pursue genuinely orthogonal independent signals with favorable 2025 and 2026 after realistic stress. Do not promote the 2025 exit winner that failed 2026; do not overfit historical 2026 to manufacture green months.

Nothing on main and nothing deployed live.
