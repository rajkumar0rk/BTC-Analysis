# Append-only experiment ledger — Monthly High-PF Search

## 2026-11-19 — volume-return covariance v1
- Status: RUNNING (GitHub Actions queued at last check)
- Run: https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44570604688
- Source branch: research/independent-volume-return-covariance-20261119-v1
- Source SHA at launch: 75a70bcde858ff3157287c73a3124dc2c555604f
- Novelty: analysis/independent_volume_return_covariance_v1/NOVELTY_CHECK.md
- BTC 2025 selection only; frozen BTC 2026 and ETH secondary validation; no live orders.
- Next check: verify run status and job logs; if failed repair same branch and retry; if successful audit raw source hashes, paired ledgers, 22 IST months, funding/margin gaps, after-cost returns/PF and NAV reconciliation; record REJECT/INCONCLUSIVE/PROMISING.
- Open limitations: unmodeled funding, spread, impact, margin/liquidation and lot constraints; first IST 2025 hours missing; 2026 research-exposed.

## 2026-11-19 — verified outcome, run 44570604688
- GitHub Actions status: completed/success; replay job 135724259487 successful, including artifact upload and result commit. Artifact 14554885553, SHA256 0328b986295ea8fdd89cbba26c773ca490d9ec8a3d173c482281b9963b730bcd.
- Decision: REJECT. BTC 2025-selected threshold 0.35, continuation mode +1, stop 1.5, reward/risk 2.0. BTC PF 0.81545, 2025 -29.04596%, Jan-Oct 2026 -36.51343%, 22-month -54.95371%, 1/22 months PF>=1.5 and NAV>=5%, 0/22 >=10%, 5 positive months, 1404 trades (565 wins/839 losses), month-end NAV drawdown -54.95371%. Goal A FALSE; full-year 2025 >500% FALSE.
- ETH frozen secondary: PF 0.81043, 2025 -35.43198%, Jan-Oct 2026 -41.82472%, 22-month -62.43737%, 0/22 >=5% and >=10%, 4 positive months, 1557 trades (586 wins/971 losses), month-end NAV drawdown -63.36880%. Full-year 2025 >500% FALSE.
- Evidence: paired_summary.csv, 2025_only_selected.csv, paired_monthly_22.csv, paired_trade_ledgers.csv, quality.json, RESEARCH_REPORT.md on this isolated branch; run https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44570604688.
- Source integrity recorded as native original SHA256 checked by loader, but source hash values and full trade-level reconciliation were not independently recomputed in this check. Funding, spread, impact, margin/liquidation and lot constraints remain omitted. Missing first 5.5 IST hours in Jan 2025. No favorable performance claim; no tuning of rejected candidate.
- Next research iteration: select economically distinct, novelty-checked BTC-first hypothesis; do not revisit this rejected covariance configuration absent genuinely new evidence.
