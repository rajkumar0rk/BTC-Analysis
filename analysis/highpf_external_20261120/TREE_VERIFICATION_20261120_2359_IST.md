# 2026-11-20 23:59 IST — verified source-tree blocker and run check

Checked GitHub Actions branch filter `research/highpf-external-source-audit-20261120`: only run 44735120702 exists, completed FAILURE at native screening step. No newer repair run. Exact stderr remains unavailable; do not infer the observed exception.

Read the branch's recursive Git tree (1007 entries, truncated=false): `data/delta_india/BTCUSD/1m/2025-01.csv.gz` exists; no `data/delta_india/BTCUSD/1m/2024-12.csv.gz` and no matching 2024-12 source anywhere in the branch tree. The current screen explicitly globs only `2025-*.csv.gz`, while requiring 2024-12-31 18:30 UTC through 2025-12-31 18:29 UTC for a complete 2025 IST year. The required earlier bars cannot be loaded by that code; this is a verified reproducibility blocker, not an observed traceback. The 60-day upstream signal also requires authentic 2024 daily warmup to reproduce January/February entries. Code also has not reconciled position notional and closed-trade PF against account NAV.

Decision: BLOCKED / INCONCLUSIVE. No verified screen trade count, PF, NAV or return; no stage-two slippage stress, ETH or 2026. Do not rerun unchanged, manufacture candles, or claim 22-month coverage.

Repair sequence: acquire authentic Delta India BTC minute candles for at least 2024-10 through 2024-12, audit UTC boundaries, patch this branch's loader and 60-day warmup, correct ledger notional/fees/GST, then push and verify a native zero-slippage 2025 screen with full raw outputs. If source cannot be acquired, explicitly classify a partial-coverage experiment as partial, or close this candidate as data-blocked and select another testable source. Funding remains UNMODELED; spread/impact/margin unverified.

Evidence: https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44735120702 ; source pinned https://github.com/pooriag/crypto-strategy-backtest/commit/fd210a38e4786b31acd06bc081dca9d79ecd3ff4 . No main/live/other schedule changes.
