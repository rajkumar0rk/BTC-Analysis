# BTC 48h monthly-profit-lock attempt — strict 22/22 check

## Actual execution evidence

[Completed GitHub Actions run 44677058163](https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44677058163), success. Artifact: **btc-48h-22monthly-profit-lock-evidence**, ID 14602606316. Repo branch: `research/btc-monthly-profit-lock-20261120`. No main merge, no real orders.

Original 48-completed-hour BTC breakout / 1H and 4H EMA trend confirmation / 2xATR initial and hourly trailing stop was replayed on actual historical BTCUSD 1-minute OHLC data. Original unchanged exit engine parity: **198 trades and exactly equal month-end NAV (maximum drift 0)**. Then 15 predeclared *causal* variants investigated monthly stop-new-entries thresholds after the current month had BANKED +0.5/+1/+2/+3/+4/+5 net R, monthly downside gates −2/−3/−4 net R, and combinations.

No hindsight trade skipping: locks can only trigger from **realized net R in trades already closed during the current IST month**. Existing open positions always obey their unchanged stop/trailing exit. Every calendar month Jan 2025–Oct 2026 is counted; zero/flat is NOT profitable. Month profit is modeled account NAV percent after fee/GST/slippage. Slippage and funding assumptions are described below.

## BTC-2025-selected variant

2025-only rank for monthly consistency under *extra adverse +2bp/side* identified **profit_after_0p5R**, stop taking new entries for the remainder of that IST calendar month once current-month already-closed trades net at least +0.5R. Never move the initial stop or change remaining open position execution. This is not a "take profit from future knowledge" and does NOT guarantee a month finishes green.

| Model | Original unchanged 48h breakout | Selected +0.5R monthly entry lock |
|---|---:|---:|
| 22m profitable months, base assumed slippage | 12/22 | **15/22** |
| 22m losing months, base | 10/22 | **7/22** |
| 22m net return, base | **+16.9431%** | +15.1464% |
| Average calendar-month return, base | **+0.7475%** | +0.6745% |
| Completed trades, base | 198 | 105 |
| 2025 net, base | +7.2669% | +4.1663% |
| Jan–Oct 2026 net, base | +9.0207% | +10.5410% |
| Net 22m, extra adverse +2bps per fill side | +12.7836% | **+13.0160%** |
| Profitable months under +2bps fill stress | 12/22 | **15/22** |
| Net 22m, extra adverse +5bps per fill side | +6.8184% | **+9.8931%** |
| Profitable months under +5bps fill stress | 12/22 | **14/22** |

## All 22 monthly net returns of selected model

| IST month | Base source-cost model | Additional +2bps adverse slippage each side |
|---|---:|---:|
| 2025-01 | +0.405% | +0.353% |
| 2025-02 | +0.407% | +0.384% |
| 2025-03 | +1.357% | +1.330% |
| 2025-04 | +2.593% | +2.557% |
| 2025-05 | +0.742% | +0.718% |
| 2025-06 | +0.408% | +0.391% |
| 2025-07 | +0.753% | +0.588% |
| 2025-08 | +0.904% | +0.886% |
| 2025-09 | **−1.445%** | **−1.650%** |
| 2025-10 | +0.994% | +0.975% |
| 2025-11 | **−0.938%** | **−1.071%** |
| 2025-12 | **−2.003%** | **−2.116%** |
| 2026-01 | +0.509% | +0.404% |
| 2026-02 | +1.334% | +1.317% |
| 2026-03 | +0.298% | +0.288% |
| 2026-04 | **−1.256%** | **−1.413%** |
| 2026-05 | +0.521% | +0.318% |
| 2026-06 | +3.594% | +3.576% |
| 2026-07 | **−1.534%** | **−1.691%** |
| 2026-08 | +10.529% | +10.417% |
| 2026-09 | **−1.674%** | **−1.779%** |
| 2026-10 | **−1.658%** | **−1.809%** |

## Why another weight blend is not a valid 22/22 solution

We inspected the completed CSVs from run **44652343750** (Stage18/Stage20 original/widened settings, monthly NAV) and this run's 15 profit-lock settings. Under BASE model **every candidate from these two current families has a negative September 2026 monthly result**: the best of all Stage18/20 variants is **−0.1039%**, and the best BTC breakout locked variant is **−1.1367%**. Under +2bps adverse fills the best Stage18/20 month is **−0.1295%** and the best BTC breakout variant **−1.1794%**. Thus NO NONNEGATIVE FULLY INVESTED WEIGHTING of just these strategy sleeves—even a hindsight reweighting—can deliver a positive September 2026. Getting 22/22 requires a genuinely different positive-edge signal or structurally different execution, not simply shifting weights or reducing market exposure.

An exploratory fixed-weight Stage18/20 + locked BTC breakout matrix found at most 19/22 under base source costs and at most 17/22 under +2bps stress **when choosing weights using all 22 months**. Those are explicitly INVALID for any live inference because weights were inspected with future-month outcomes. Choosing a split solely from BTC 2025 at +2bps stress never achieved even 17/22 across all periods. No 22/22 result has been found.

## Model limitations

- Base costs from original Stage17: 0.05% taker per side, GST 18% on fees, adverse 5 BTCUSD price points per side. Additional +2/+5bps per side is a sensitivity only, not actual bid/ask evidence.
- 1-minute OHLC stop-first exit simulation and next-open entry, not tick-level orderbook, queue position, actual slippage, funding, contract lot granularity, margin requirements, liquidation or shared multi-sleeve collateral.
- Source has known missing first IST hours of Jan2025 and missing final UTC day Oct2026.
- Trades crossing month-ends are marked to monthly NAV; monthly profit-lock is triggered by closed trades only; marked-to-market month-end returns can differ from closed-trade R and can remain negative after a historical lock.
- BTC2025 and 2026 both historically researched: 2026 chronological result is NOT a pristine independent holdout. 15 variants constitute multiple-testing risk.
- No true native ETH validation of this specific monthly lock, no paper-trading forward validation.
- **Research status only. 22/22 positive months NOT achieved and no live deployment.**

The next valid method to pursue 22/22 is a new independent positive after-cost trading mechanism specifically complementary to periods where both existing families fail, frozen on earlier training and checked unchanged on later/out-of-sample data. No calendar-outcome foresight, no leverage escalation or skipped red months.
