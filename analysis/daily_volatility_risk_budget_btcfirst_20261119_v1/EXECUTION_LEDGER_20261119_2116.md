# Daily-profit study execution ledger — 2026-11-19 21:16 IST (append-only entry)

Status: REPAIRED / PUSH ATTEMPTED / RUN UNVERIFIED. This is not a completed backtest or a verified positive result.

Continued the same frozen BTC-first volatility-of-volatility hypothesis; did not change its entry, CV/volatility thresholds, stops, targets, sizing fraction, or ETH settings. Verified prior commit 3b64e8709a32c46e7f78a9dd2c8a42550aa817dc and found no discoverable PR-triggered runs. The GitHub connector's fetch_commit_workflow_runs only lists PR-event runs, so an empty response does NOT prove push workflows never executed.

Repair commits:
- f451e02a9cf7ec263c3af11b609c006b8684d5a2: sequential NAV compounding with 25% of current NAV per trade; trade-level realized PF; daily NAV and closed-equity drawdown; entry timestamp. These replace invalid fixed-initial-capital annual/monthly return sums.
- 62f48cc4baaf690457c62afbd81efa7a6b7c3856: monthly archive audit now reads original gzip files.
- 48879f49d1edb3d21909c527b00dc761bcaaf9eb: branch-scoped workflow now executes gzip archive audit before frozen backtest and uploads evidence files.

Unresolved critical blockers: No actual workflow run ID, job log, audit JSON, trades CSV, daily NAV CSV or monthly CSV could be retrieved; workflow dispatch/run listing is not available through this connector and external GitHub access is disabled. A green workflow or a real completed BTC backtest has NOT been observed. Must inspect the GitHub Actions page for the branch, capture run ID, job logs and artifacts, fix failures on THIS branch, and verify data hashes and actual 22-month coverage. Additional known limitations: month reporting still uses UTC rather than IST; fee/slippage are modeled as a single 0.158% or 0.238% round trip, not separately priced BTC $5/side and ETH 0.02%/side; gap-fill, true bid/ask, funding, tick/lot, liquidation and intrabar drawdown remain unverified. Do not publish profit results or call this executable until those are addressed. The branch-only workflow may not register as an active workflow if GitHub requires the workflow file on the default branch; do NOT change main without authorization.

Decision: REPAIR / EXECUTION BLOCKED, not REJECTED and not PROMISING. No other schedules, branches, main or trading positions modified.
