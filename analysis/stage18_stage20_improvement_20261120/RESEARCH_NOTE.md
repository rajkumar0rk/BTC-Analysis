# Stage18 / Stage20 controlled BTC-first portfolio study — audited outcome

Verified GitHub Actions completion: [run 44645724206](https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44645724206) (completed success). Source revision: `ba6f8d927ab0d13e411029c53f0d158efff6d12b`. Original output and all BTC/ETH monthly ledgers: Actions artifact **stage18-stage20-controlled-improvement-evidence** (artifact ID 14587274377).

## Status

**RESEARCH-ONLY, NOT LIVE READY.** This is a **monthly-portfolio return allocation and additional-cost replay** of the original Stage15/Stage17/Stage19 historical component results, **not** a new native 1-minute entry/exit execution backtest. It cannot resolve source execution, funding or margin assumptions.

Candidate selection: predeclared, small set of allocation and prior-completed-month risk throttles, scored **BTC January–December 2025 only**, then frozen BTC January–October 2026 and unchanged ETH; neither later market used to select the variant. Source families themselves were already researched on 2026; no pristine independent out-of-sample.

| Fixed research variant | BTC 2025 net | BTC Jan–Oct 2026 | BTC total 22-month net | BTC positive / negative / flat months | ETH total 22-month net | BTC month-end DD |
|---|---:|---:|---:|---|---:|---:|
| Stage18 original 75% quiet 1H + 25% Daily20 | +4.2616% | +5.5870% | +10.0868% | 17 / 3 / 2 | −2.3067% | 1.0197% |
| Stage20 original: 90% Stage18 + 10% 1H momentum | +3.4131% | +4.2994% | +7.8593% | 18 / 3 / 1 | −2.2214% | 0.9746% |
| Stage20 selected improvement: **95% Stage18 + 5% 1H momentum** | **+3.8371%** | **+4.9418%** | **+8.9686%** | **19 / 2 / 1** | **−2.2635%** | 0.9730% |

The BTC Stage20 improvement is only **+1.1093 percentage points across 22 months**; Stage18 did not improve under the predeclared 2025 selection method.

## Additional conservative friction stress

These amounts are **extra deterministic NAV haircuts on every calendar month** beyond the original component fee/GST/assumed slippage assumptions, **not independently observed exchange transaction costs**.

| Variant | No extra haircut | Extra 0.10% NAV each month | Extra 0.25% NAV each month |
|---|---:|---:|---:|
| BTC Stage18 original | +10.0868% | +7.7004% | +4.2132% |
| BTC Stage20 original | +7.8593% | +5.5191% | +2.0994% |
| BTC Stage20 improved | +8.9686% | +6.6054% | +3.1521% |
| ETH Stage20 improved | −2.2635% | −4.3936% | −7.5058% |

The 0.25% extra-cost stress reduces the improved Stage20 BTC profitable months from 19 to **11 of 22**. Thus BTC positive months are sensitive to modest additional account-level costs.

## Before any trading recommendation

1. Rebuild native BTC and ETH 1-minute trade-by-trade Stage15/17/19 signals, fills, trades, concurrent portfolio positions, and margin, preserving original baseline settings. Do not silently treat the blended month NAV experiment as an integrated execution replay.
2. Verify DST/timezone boundaries, source gaps, ETH price normalization, actual contract tick/lot minimums, spread/impact, GST, funding, liquidation and rebalance costs; use authenticated exchange fee terms.
3. Reconcile each trade to daily/IST monthly account NAV, including open trade marks and intramonth equity drawdown. Trade-level PF cannot be recovered from monthly portfolio NAV alone and remains **unverified** for this study.
4. Run honest cost/parameter robustness and fresh paper/forward tests on genuinely new data. Do not retune using BTC 2026 or ETH.

All analysis was committed to an isolated research branch; nothing was merged to main or deployed live.
