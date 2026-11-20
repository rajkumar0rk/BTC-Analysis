# Stage36 isolated execution ledger

## 2026-11-20: failed screen repaired and relaunched
- Original workflow: https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44698097026, completed **failure**; job 136159603852, step "BTC zero-slippage screening with two-sided commission and GST" failed. Python dependencies installed successfully. Artifact 14612090711 (SHA256 ec b0086c112a149daf95f27495a4b2a731c86d0c0235ecbfa00fcfacc686fdb1 without space) contained only NOVELTY_CHECK.md and run_identity.txt; no trades, monthly returns or valid screening outcome.
- Source diagnosis: scripts/research_paired_external_ema_vwap_stage36.py blob 47febb9dd9901e0e9b2d7b32bfa121e5209d13bb contained literal backslash-n sequences between Python statements inside main(), causing invalid Python syntax. This is source-level evidence; no full original Actions traceback was accessible.
- Repair: commit a15957bfa81c4513c8efa68f9f1400dc29f81717 replaces the two escaped newline sequences with real line breaks, without changing strategy rules, fills, sizing, commissions, or GST.
- Replacement push-triggered run: https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44707954594, observed **queued** at inspection; source SHA a15957bfa81c4513c8efa68f9f1400dc29f81717. Not yet a completed backtest.
- Next check: inspect run 44707954594 jobs, logs, artifacts; if successful, audit data coverage, exact original trade ledger, 22 IST monthly NAV rows, PF, expectancy and equity reconciliation. Zero-slippage BTC screen with two-sided 0.05% taker fees and 18% GST only. If screen fails, reject; if credible positive, run separate frozen BTC slippage 0.5 and 5 USD/side tests, then ETH. Funding/spread/impact/contract rounding are unmodeled.
- No other branch, main, automation or live account touched.
