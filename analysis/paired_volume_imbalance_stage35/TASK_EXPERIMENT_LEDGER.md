# Stage35 — isolated experiment ledger
## 2026-11-20 08:55 IST — new hypothesis committed; launch verification unresolved
- Stage34 independently audited and REJECTED, source ledger `analysis/paired_serial_dependence_stage34/TASK_EXPERIMENT_LEDGER.md`, run 44659473431, artifact 14595016405. BTC only 8 trades, PF 0.524705, -0.987045%; no improvement.
- Novel Stage35 signed-volume absorption hypothesis preregistered at `NOVELTY_CHECK.md`, SHA 6692968e9b4f2e07b11104d897cb4b6bf0bef41a. Differentiated from Stage32 volume-normalized price impact and Stage34 serial return covariance.
- Source script `scripts/research_paired_volume_imbalance_stage35.py`, commit d07c3292d331b3bdf8c50dddd90053df1b4893cf.
- Dedicated branch-scoped push workflow `.github/workflows/research-stage35-volume-imbalance.yml`, commit b61a87d8f1e34d3c70770919e7b17e9c807f831f.
- Workflow commit accepted by GitHub. Connector `fetch_commit_workflow_runs` returned [] because it filters to pull-request runs; `get_commit_combined_status` returned [] and does not establish a push Actions run. **Not yet verified launched or completed.** No BTC/ETH results claimed.
- Exact next action: obtain Stage35 branch workflow run ID from GitHub Actions (workflow name `BTC-first Stage35 signed-volume absorption`), check latest job status and logs. If failed, repair same branch and rerun. If successful, download `stage35-original-ledgers`, inspect run_identity.txt, source SHA, quality.json, trade ledger, all_22_months.csv, summary.csv; reconcile month-end NAV, cost sensitivity and data coverage. No new study until this closes.
- Known limitations: signed hourly volume is not true aggressor order flow; funding, spread, historical market impact, contract rounding and maintenance liquidation not verified. January 2025 IST start and October 2026 gaps must be treated as incomplete where applicable.
- No changes to main, other schedules or live accounts.
