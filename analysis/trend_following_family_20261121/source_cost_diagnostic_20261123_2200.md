# Trend family source-cost diagnostic — 2026-11-23 22:00 IST

Status: SOURCE ANALYSIS ONLY. Not a new historical BTC backtest or a verified profit result.

## Immutable source
Artur Sepp / V. Lucic, *The Science and Practice of Trend-Following Systems*, https://ssrn.com/abstract=3167787 .
Code https://github.com/ArturSepp/TrendFollowingSystems/tree/d4988caa02535add61bc0f77df0286d40ccb9803 ; MIT license (verify LICENSE at pinned revision before code reuse).
Exact code paths: `src/trendfollowing/analytics/sharpe.py`, `src/trendfollowing/analytics/expected_return.py`, `papers/tf_systems/replication/net_sharpe_analysis.py`, `examples/predict_sharpe_from_acf.py`.

## Recovered diagnostics and applicability
- `compute_daily_moments` derives theoretical gross return and variance from a population ACF and drift under jointly Gaussian volatility-normalized returns, not a historical realized BTC P&L ledger.
- `sr_net_analytic` computes net Sharpe as gross Sharpe minus `2 * af * cost / sqrt(pi) * sqrt(1-nu) / sqrt(var_f)`, with `nu=(span-1)/(span+1)`. Its `cost` is **per unit of volatility-normalized turnover**, not Delta's 0.05% of executed USD notional per side; direct substitution of 0.00059 would be dimensionally wrong.
- `break_even_cost_ar1(phi)` = `sqrt(pi/(2*af))*phi/(1-phi)` is an AR(1), zero-drift, long-span analytical result, not a BTC empirical threshold.
- The published `examples/predict_sharpe_from_acf.py` estimates the sample ACF on the same historical sample used to compare predicted and realized Sharpe: useful retrospective attribution, **not** out-of-sample forecasting.
- For actual Delta fee screen, the correct directly observable empirical diagnostic is `gross realized PnL / sum(abs(executed USD notional))`, compared to 0.00059 per side (0.05% fee times 1.18 GST); only a full chronological ledger determines realized net NAV, drawdown and monthly outcomes.
- Existing Kali-Uga replay: 104,366 orders, $75.01 modeled fee+GST, net -70.92%, workflow https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/45131335895 . Using $75.01/0.00059 implies about $127,136 total executed USD notional; this is an accounting cross-check, not independent verification of gross PnL.

## Novelty gate
Decision: **DIAGNOSTIC ONLY; no strategy test authorized.** This is a transaction-cost / trend-persistence attribution method, not a novel complete trade-entry/exit baseline. The European EMA-filter trading system overlaps prior TSMOM / continuous EMA studies in `scripts/trend_family_tsmom_components_2025.py` and `scripts/trend_family_kali_uga_2025.py`. Do not run as another renamed EMA strategy. The distinct contribution is a preregistered *screening diagnostic*, conditional on using past-only BTC2025 data and independently mapping normalized costs to actual dollar turnover.

## Next executable work
(1) Use the archived authentic BTC2025 minute runner to compute past-only rolling ACF/persistence and gross-to-turnover ratio for already-completed strategy ledgers; (2) separately source a fully specified lower-turnover novel trend system and pass `codex/STRATEGY_NOVELTY_GATE.md`; (3) execute baseline with next-minute fills, stop-first checks, fee/GST NAV and monthly reconciliation; (4) only then assess frozen 2026/ETH. No 2026 tuning, no synthetic data, no live orders.
