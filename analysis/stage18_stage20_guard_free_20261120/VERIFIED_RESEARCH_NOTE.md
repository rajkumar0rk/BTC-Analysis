# Stage18 / Stage20 — removing the weekly loss entry cap (actual BTC 1m research)

**Verified execution:** [GitHub Actions run 44652343750](https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44652343750), completed successfully. Original BTC Stage14 candidate events; 1-minute stop-first BTC replay of Stage15 core. The original Stage17 swing and Stage19 auxiliary remain archived **monthly** sleeve contributions; this is NOT a fully integrated shared-margin backtest. Full trade and 22-month ledgers, all 16 variants and cost stresses are in the run artifact `btc-guard-free-stages18-20-complete`.

## Verdict: MODEST, NOT A BREAKTHROUGH

When choosing strictly using **BTC 2025 after-cost return, number of profitable months and month-end DD** with extra +2bps/slippage per execution side, the selected rule for both portfolios was **5R_broader_eff25_no_gate**.

The actual changes to the core trade logic are (1) stop suppressing entries after -3R in the current week; (2) increase the PREVIOUS COMPLETED CALENDAR MONTH 4H directional efficiency limit from 0.15 to 0.25. Leave 4H ADX <=18, 1H volume ratio <=1.2, structural stop, fixed 5R TP, four-hour maximum holding, and 0.5%-NAV nominal entry risk subject to 3x notional cap unchanged. No calendar-month labels or future returns used for entering trades. Two-sided trading remains enabled.

| Historical BTC 22-month modeled outcome | Prior fixed 5R Stage18 | Selected Stage18 | Prior fixed 5R Stage20 | Selected Stage20 |
|---|---:|---:|---:|---:|
| Net return (base costs) | +12.0163% | **+13.8790%** | +9.5921% | **+11.2282%** |
| Positive months | 15/22 | **18/22** | 18/22 | 18/22 |
| Losing months | 4/22 | **3/22** | 3/22 | 3/22 |
| Flat months | 3/22 | 1/22 | 1/22 | 1/22 |
| Core 1m trade count | 64 | 75 | 64 | 75 |
| Core modeled net-R profit factor | 2.1507 | 2.1517 | 2.1507 | 2.1517 |
| 2025 compounded NAV | +6.7313% | +8.0691% | +5.1873% | +6.3714% |
| 2026 Jan–Oct NAV | +4.9517% | +5.3761% | +4.1875% | +4.5659% |

The new core trade opportunities change months (base cost comparison):

| Month IST | Original Stage18 | Selected Stage18 | Original Stage20 | Selected Stage20 |
|---|---:|---:|---:|---:|
| March 2025 | 0.0000% | +0.4009% | +0.0592% | +0.4199% |
| July 2025 | +0.6519% | +0.1118% | +0.3805% | **−0.1055%** |
| December 2025 | **−1.0197%** | +0.3594% | **−0.9263%** | +0.3149% |
| July 2026 | 0.0000% | +0.4043% | +0.2036% | +0.5675% |

Hence the result accepts a real newly losing Stage20 month (July 2025), not hidden or skipped; improvements in December 2025 and extra entry opportunities exceed it in modeled totals. This is why month count ALONE can be misleading.

## Research integrity / incomplete execution

- Results calculated on repeated-historical BTC 2025 (training) and BTC 2026 (research-exposed chronological check). **No untouched fresh validation**. Do not call this a proven strategy.
- Models include simulated 0.05% taker per side, 18% GST on trading fees, 5 BTC-points adverse slippage each side, with additional 0/2/5-basis-point-per-side stress scenarios. The stress adds to assumed base slippage, it is NOT actual historical bid/ask evidence.
- Stage15 core trade returns book to exit month; Stage17/Stage19 are old monthly NAV. Combined returns are not a full native simultaneous order-matching portfolio backtest with shared margin, funding, spread, minimum contract size, cross-sleeve overlap, liquidation or financing.
- Source gaps at early Jan 2025 IST and Oct 31 2026 UTC. Max drawdown from month-end NAV is not maximum intramonth drawdown.
- Stage20 source component's old monthly replay differs slightly from newer 1m Stage17 replay in October 2026. Present study intentionally holds original archived secondary sleeves fixed for direct same-source comparison.
- ETH execution with frozen changes not conducted. No new prospective data.
- 16 variants were explored, which introduces multiple-testing risk. Even though the winning variant used BTC 2025 only, the family itself was already developed on historically exposed 2025/2026.
- The total net gain is only +1.86 percentage points (Stage18) or +1.64pp (Stage20) over 22 months. **Not sufficient to meet the user's desire for a substantial monthly return improvement. Do not deploy live.**

## Recommendation

Treat the Stage18/Stage20 variants as low-return research baselines. Stop claiming marginal parameter or loss-guard adjustments are a material breakthrough. A meaningful improvement now requires an **independent higher-expectancy signal or complementary strategy** with enough trades, realistic execution and truly new forward paper data, not increasing leverage or suppressing bad months.

Nothing merged to main, no real orders sent.
