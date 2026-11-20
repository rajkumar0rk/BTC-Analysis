# Native zero-slippage screen execution checkpoint — 2026-11-20

Status: IMPLEMENTED, WORKFLOW TRIGGER UNVERIFIED; NOT BACKTESTED.

Source commit 7fcd992231aa64461ea5b4151693ad71826a7150 introduced scripts/highpf_external_tsmom_screen_v1.py.
Workflow commit f0867dc0d8299444fc078359b9ff8a00ca0b5839 introduced .github/workflows/highpf-external-tsmom-screen.yml on research/highpf-external-source-audit-20261120.

Direct authenticated GitHub API GET /repos/rajkumar0rk/BTC-Analysis/actions/runs?branch=research/highpf-external-source-audit-20261120&per_page=10 returned total_count=0 immediately after workflow push. No run ID exists to verify; no results claimed. Next iteration: re-query Actions for the branch and workflow file, inspect any run/job/log, repair branch push trigger if absent. Do not start unrelated candidate until resolved.

Potential data blocker: genuine files are named by UTC month; 2025-01 begins at UTC midnight, so IST 2025-01-01 00:00–05:29 may require 2024-12-31 candles. Screen explicitly fails closed if 2025 IST calendar boundaries are missing; it must not silently fill candles. Existing script also requires valid contiguous 1m timestamps. If failed, obtain authentic boundary candles and rerun; do not fake.

Cost stage: zero slippage both sides, 0.05% commission per turnover side, 18% GST on commission. Historical funding UNMODELED; spread, market impact, margin, contract rounding unverified. Stage-2 0.5/5 BTC price-point slippage is prohibited until credible positive screen. No live orders.
