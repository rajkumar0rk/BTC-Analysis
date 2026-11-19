# Daily-profit hunt — 2026-11-20 01:15 IST — execution gate

Status: BLOCKED FOR NEW EXPERIMENT EXECUTION (not a backtest; do not alert).

## Verified reads
- Existing volatility-of-volatility study closed as REJECTED by prior completed GitHub Actions run 44558873365; no retuning warranted.
- Read `codex/STRATEGY_NOVELTY_GATE.md` on main, blob 87215853264cfbfd928421152e752ce106a685a7. It documents extensive prior time/volume/OI/funding/trend/structure research and an Oct 2026 missing 1,440 UTC-minute coverage issue.
- GitHub branch search confirmed this isolated branch and 22 other `research/daily-*` branches. The most relevant existing mechanisms include OI absorption, premium pressure, maker spread feasibility, realized skew, jump aftershock, volatility shock fade, and compression breakout. Reuse of those without new causal data is not novel.
- Connector `fetch_commit_workflow_runs` for commit 13369bbc70ff0407cb18f088f92c2afc0cb056d5 returned [] but the connector explicitly filters only PR-triggered runs; this **cannot** establish whether a branch push workflow ran.
- Attempts to fetch four guessed ledger/workflow paths on the isolated branch returned HTTP 404; their real paths need repository tree discovery, not guesses.

## Exact blocker and repair
Available GitHub connector has no general list-workflow-runs-by-branch or dispatch action, and its commit lookup omits push events. Before any new experiment is claimed running, use an authenticated GitHub Actions REST GET `/repos/rajkumar0rk/BTC-Analysis/actions/runs?branch=<research-branch>&event=push` (or gh api), plus workflow file inspection and action permissions; capture actual run ID, jobs and artifacts. Ensure workflow is eligible for push on a nondefault branch. Retrieve historical BTC/ETH archive coverage hashes and schema and confirm no gap-sensitive entries before testing.

## Next hypothesis gate
Do not relaunch vol-vol or recycle existing OI/volume/price action under new labels. A distinct mechanism needs verified historical executable data (e.g., genuine settled funding/basis or L1 book), otherwise mark INCONCLUSIVE. No new strategy, fills, return figures, or monthly statistics were produced in this iteration. No production or other research branches touched.
