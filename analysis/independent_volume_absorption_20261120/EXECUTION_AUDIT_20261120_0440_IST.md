# Execution audit — 2026-11-20 04:40 IST (append-only)

Study: volume absorption convex BTC-first. Previous source/ledger commit 03146d8a. Prior OI, spot lead-lag, variance-endload studies are already closed REJECTED; do not reopen them.

Verified source workflow on this isolated branch: .github/workflows/independent-volume-absorption-20261120.yml; push branch/path trigger, Python 3.12, pandas/numpy, evidence artifact path analysis/independent_volume_absorption_20261120/. GitHub connector fetch_file returned workflow blob e040c5b023473f5d686b88a2c6aa43b284feafcd.

Execution integrity defect discovered in script: the comment forbade same-bar reentry, but entry condition did not track an exit on the current minute. Corrected by explicit closed_this_bar flag, commit 7986cabc0aeeffb0024bdad281bb5320ee8174c7. No entry/exit parameter tuning. This code change matches the branch-scoped workflow push path and should trigger an execution.

Execution verification BLOCKER: GitHub fetch rejects workflow-run collection URL (HTTP 400: URL is not an allowed public GitHub repository or search endpoint); fetch_commit_workflow_runs only covers pull_request-triggered runs, not push. Web workflow page was inaccessible (DisabledError). Therefore no new run ID, job logs, original trade/equity CSV or performance result can be verified from this check. This is a connector access limitation, not proof that the job failed or succeeded. Next check: inspect https://github.com/rajkumar0rk/BTC-Analysis/actions/workflows/independent-volume-absorption-20261120.yml for push run from commit 7986cabc0aeeffb0024bdad281bb5320ee8174c7; fetch job logs/artifact, repair on this branch if failed, and independently reconcile BTC 2025 / BTC 2026 / ETH months before decision. No claims of profitable performance.

Additional audit limitations to check: historical funding cashflows unavailable, no L2 spread, forced gap exits use previous observed close, intrabar stop-first behavior and monthly MTM reconciliation. Do not classify as PROMISING or VERIFIED until original executed evidence is audited. No changes to other branches or live trading.
