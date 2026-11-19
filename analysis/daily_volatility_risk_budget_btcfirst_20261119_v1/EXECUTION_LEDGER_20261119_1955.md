# Daily-profit research execution ledger — 2026-11-19 19:55 IST

Status: BLOCKED / EXECUTION UNVERIFIED, not a completed backtest.

Inspected the actual isolated branch against main (five commits ahead, one behind) and fetched the preregistration, archive audit, backtest and workflow. Confirmed code exists at `analysis/daily_volatility_risk_budget_btcfirst_20261119_v1/backtest.py` and branch-only workflow `.github/workflows/daily-volvol-btcfirst-20261119.yml`. No run ID, logs or output artifact was available for verification: connected GitHub run discovery is restricted to PR-triggered runs for a known commit, and the GitHub REST workflow-runs endpoint was not accessible via web. Do not interpret this as a successful run.

Code audit findings to repair before credible metrics:
1. Current `backtest.py` labels a sum of daily fixed-initial-equity PnL as annual/monthly "net_account_pct"; this is NOT sequential compounded NAV and cannot satisfy the required account return or month-end equity reconciliation.
2. Its monthly PF is computed from daily net sums rather than the explicitly required positive/negative closed-trade net PnL ledger. They coincide only when exactly one trade per day and no cross-midnight positions; the implementation should calculate from trades explicitly.
3. It records date-only trades, not entry/exit timestamps, minute-bar touch evidence, fill prices or mark-to-market NAV. Intrabar/gap risk and actual execution remain unverified.
4. Its cost assumption is 0.158% round trip, but 0.05% per side plus 18% GST is 0.118% BEFORE spread/slippage. BTC stress must explicitly cover at least 5 BTC points per side; ETH >=0.02% per side. Funding and actual bid/ask unknown.
5. The audit script expects uncompressed CSV command arguments whereas the workflow calls only the backtest on monthly .csv.gz files; it is not actually running the preregistered data audit. Current backtest checks duplicates and OHLC but does not emit full timestamp/gap diagnostics.
6. Seven-day prerequisite makes Jan 1–7 2025 ineligible without 2024 history; missing Oct 2026 source and IST month boundaries must be reported, not silently interpreted as a full 22-month result.
7. The `prior` and `future` minute-index membership check repeats for every day; runtime feasibility on GitHub Actions has not been measured.

Next exact repair: integrate gzip archive audit into the workflow, implement sequential NAV with IST monthly reconciliation and trade-level PF, timestamped fills and gap/fee-stress diagnostics, then trigger branch push and retrieve actual run ID/logs/artifacts. Preserve frozen signal/exit parameters and BTC-first policy. Do not begin a new hypothesis.

This ledger addition is a branch-scoped push trigger attempt; it is not proof that GitHub Actions accepted or executed the workflow. No main, other branch, automation or trading changes.
