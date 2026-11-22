# Stage18 21/22 — historical allocation retune, 22 November 2026

**Research only. Not live-ready or forward validated.** This model blends
separately backtested BTC 1m core / daily Donchian returns and archived Stage19
1H returns at **month end**; it is NOT a synchronized shared-margin execution
backtest. The full 2026 history was already inspected when selecting weights.

## Unchanged component strategies

- Core: **core_maxrisk_700** — 4H/1H/15M pullback and breakout, initial
  structural stop capped at 700 BTC points, 5R target, 240-minute max hold.
- Daily Donchian: **channel20_2atrtrail** — Donchian 20 completed daily
  breakout, EMA50 confirmation, initial stop 2xATR, trail 2xATR.
- Hourly: **ema20_pullback_confirm__4h_efficiency_ge30__3R__480min**.

## 22-month modeled results, January 2025–October 2026 IST

| Metric | Original 70/25/5 | Return-focused 73.5/22.5/4 | Stress-month 72/23.5/4.5 |
| --- | ---: | ---: | ---: |
| Compounded model return | +13.5695% | **+14.2991%** | +13.9764% |
| Positive / losing months | 21 / 1 | 21 / 1 | 21 / 1 |
| Max month-end drawdown | 0.2135% | **0.1848%** | 0.1977% |
| September 2026 | -0.2135% | **-0.1848%** | -0.1977% |
| October 2026 | +0.0021% | +0.0068% | +0.0039% |
| +2bp core/Don only, return | +11.0012% | **+11.5908%** | +11.3285% |
| +2bp core/Don only, positive months | 17 | 18 | **19** |
| +5bp core/Don only, return | +7.2585% | **+7.6490%** | +7.4726% |
| +5bp core/Don only, positive months | 12 | 13 | 13 |

## Reproduce using source data

The native independently executed 1-minute core and Donchian studies are
archived in completed GitHub Actions run:
https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44889747997

Download the two artifacts named stage18-core-standalone-20261121 and
stage18-donchian-standalone-20261121. The hourly monthly source is already
committed at analysis/institutional_discovery_stage19_new_1h_patterns/monthly_results.csv.

The isolated workflow is
.github/workflows/research-stage18-21-profit-robustness-20261122.yml
and the runnable script is
scripts/research_stage18_21_profit_robustness_20261122.py.
The script asserts that the original 21/22 and +13.569514% result exactly
reconcile, and saves complete monthly/source-sleeve CSV ledgers.

## Important limitations

1. The allocations were screened on **all 22 months**. These candidates are
   hindsight-optimized, NOT independently forward verified.
2. Additional stress is only applied to core and Donchian. Hourly performance
   is intentionally held at its originally archived cost assumptions, so
   +2bp/+5bp comparisons **overestimate robustness**.
3. No integrated 1m execution, cross-strategy netting or collateral, historical
   funding, L1 spreads, live lot sizing, liquidation, rebalance fill fees, or
   actual intramonth equity drawdown has been verified.
4. Positive October 2026 is extremely close to zero and may disappear under
   slightly more adverse fills.
5. Historical results are **not forecasts**. Do not deploy these weights with
   real money without independently forward testing an executable simulator.

Decision: preserve the 70/25/5 baseline and treat 73.5/22.5/4 as an
exploratory improved historical return/drawdown candidate, not a proven upgrade.
