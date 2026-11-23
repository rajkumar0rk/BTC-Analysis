# BTCUSD 15M — separate 80% / 100% ATR-strategy optimization (verified)

**Status:** Completed historical simulation grid. Two profiles ranked independently; nothing merged into deployable strategy.

**Dataset:** BTCUSD futures, January 2025 through October 2026 inclusive, 22 completed India-local (IST) months. 15-minute ST(10,3)/EMA20 confirmed-break-and-reclaim entry. 15-minute ATR(10) / 15-minute close >= 0.20% at signal. 1-minute OHLC exit replay, both O-H-L-C and O-L-H-C path assumptions, net after 0.05% taker fee each leg, GST 18% on trading fee, and 0.02% adverse slippage per leg. No futures funding, actual spread/orderbook/liquidation/latency. Drawdown = **peak-to-trough floating equity**, not closed-only.

## Final verified head-to-head

| Profile | Old compounded net profit | Best new compounded net profit | Profit change | Old max floating DD | New max floating DD | Positive months | Losing months | Closed trades |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 80% global exposure | +163.492% | **+180.6308%** | +17.1388 pp | 11.879% | **11.879%** | 18/22 | 4/22 | 73 |
| 100% global exposure | +229.037% | **+255.8336%** | +26.7966 pp | 14.740% | **14.740%** | 18/22 | 4/22 | 73 |

Each profile retains its own separate benchmark, with no profit/drawdown/month-count deterioration. The result is identical under both simulated intraminute price paths for these specific winners.

## Trading logic for both improved profiles

- LONG/SHORT: wait for a valid ST(10,3) regime; EMA20 post-flip interaction closes on the wrong side, and a subsequent completed 15-minute candle reclaims the correct side (reclaim wait=4). First valid reclaim signal per Supertrend cycle.
- Entry at next 1-minute open using adverse 0.02% price slippage.
- Additional completed 15-minute bar entry filter: ATR(10) / BTC close >= 0.20%.
- **Stop-loss 3% of filled BTC entry price; take profit 9%** (3R price target).
- **Revised profit protection:** once price first reaches +8% favorable move relative to raw entry, ratchet stop to **+2% favorable move relative to raw entry**; never loosen it. Configured increment = +0.25 percentage points of locked favorable move per further 1% favorable move. This increment does not materially activate before the 9% target on these trades; equivalent step = 2% / +0.5% had the same results.
- Supertrend reversal exit OFF; original fixed stop, target and profit protection still manage exit.
- After five **realized net losing trade exits in the same IST month**, pause new entries until next IST month. One open position at a time.
- Max 1x notional exposure (no leverage).

### Profile-specific exposure ladder

| Realized net losing exits this IST month | 80%-exposure candidate | 100%-exposure candidate |
|---|---:|---:|
| 0–1 | 80% of contemporaneous equity notional | 100% |
| 2 | 52% | 65% |
| 3 | 24% | 30% |
| 4 | 8% | 10% |
| 5+ | New entries paused | New entries paused |

## Yearly returns of each improved candidate

| Year | 80% exposure | 100% exposure |
|---|---:|---:|
| 2025 (12 months) | +43.892% | +55.993% |
| January–October 2026 (10 months) | +95.029% | +128.109% |

The two annual returns compound multiplicatively to each 22-month result, not additively.

## Exact month-by-month compounded equity returns (both best winners)

| IST month | 80% exposure | 100% exposure |
|---|---:|---:|
| 2025-01 | -2.766% | -3.500% |
| 2025-02 | +6.634% | +8.283% |
| 2025-03 | -3.179% | -4.012% |
| 2025-04 | +7.317% | +9.046% |
| 2025-05 | -5.446% | -6.791% |
| 2025-06 | +6.722% | +8.395% |
| 2025-07 | +5.835% | +7.257% |
| 2025-08 | +3.205% | +3.940% |
| 2025-09 | +1.801% | +2.252% |
| 2025-10 | +22.370% | +28.394% |
| 2025-11 | +3.794% | +4.615% |
| 2025-12 | -6.283% | -7.805% |
| 2026-01 | +0.914% | +1.046% |
| 2026-02 | +16.734% | +21.056% |
| 2026-03 | +5.739% | +7.114% |
| 2026-04 | +3.292% | +4.054% |
| 2026-05 | +13.322% | +16.755% |
| 2026-06 | +7.065% | +8.727% |
| 2026-07 | +0.527% | +0.654% |
| 2026-08 | +9.848% | +12.375% |
| 2026-09 | +6.722% | +8.397% |
| 2026-10 | +6.013% | +7.498% |

Four identical losing months in both profiles: January, March, May and December 2025. Worst month is December 2025: -6.283% for 80%, -7.805% for 100%. These losing months and the total maximum floating DD were **not** improved. Most gain arose from better returns in positive 2026 months.

## Sweep audit / selection conditions

Two grids, evaluated for both independent profiles on both 1-minute OHLC ordering assumptions:

1. **72 SL/TP rules**: SL 2, 2.25, 2.5, 2.75, 3, 3.25, 3.5, 3.75, 4% and TP 6–13% in 1% increments; the prior +8.25% activation / breakeven protection remained fixed.
2. **90 profit-protection rules**: activation 3–8.5% favorable move, locks 0–3%, two step schedules; SL3%/TP9% fixed.

**162 rules × 2 profiles × 2 price paths = 648 full 22-month simulations**. Every simulation shard reproduced both profile benchmarks before running its sweep. Summary CSVs retrieved from the completed GitHub Actions simulation artifacts, grouped by unique sweep/profile/rule and assessed using **minimum net profit and minimum positive-month count, maximum floating DD** across both paths.

There were 25 non-degrading, strictly improved profit-protection settings per exposure profile, **zero qualifying stop-loss/take-profit-only changes**, zero candidates increasing profitable months without profit/DD regression, and **zero candidates strictly reducing DD** while preserving each profile's baseline return and 18 positive months. The best reward was achieved by activation=8%, first-lock=2%, with 73 trades.

For a less optimized nearby setting, activation=8.25%, first-lock=2% gave +176.5598% (80%) and +249.4044% (100%) at the same DD/month-count.

## Reliability restrictions (critical)

This 22-month BTC sample has been explored exhaustively across many rounds. Selecting the best of 162 exit parameters on it is susceptible to **multiple-testing and hindsight selection bias** even when signal calculations use only prior bars. The ATR >= 0.20% entry filter is **fragile** to neighboring values; prior threshold stability experiments found no neighboring threshold preserving the entire stringent profit/DD/month-count target.

Nothing here demonstrates future 18/22 profitable months. Not production-ready without unseen holdout/forward data, trade-by-trade order-execution validation, market gap and funding models, and recalculated liquidation/margin risk where leverage is used.

### Reproducibility

Backtest code: `scripts/research_btc15m_atr_two_profile_exit_sweeps_20261123.py`; workflow `.github/workflows/research-btc15m-atr-two-profile-exit-sweeps.yml`. Source-faithful original simulation from `scripts/research_btc15m_worst_month_loss_pause_20261123.py`, with isolated 80%/100% exposure sizing and unchanged 15-minute ATR filter. Complete 32-shard full dataset from Actions run `45132411511` (simulation shards succeeded; its aggregation's final Git push conflicted with a simultaneous later code edit; results were independently recomputed from all archived shard CSVs).
