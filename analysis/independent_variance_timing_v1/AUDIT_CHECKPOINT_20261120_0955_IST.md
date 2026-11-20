# Independent audit checkpoint — 2026-11-20 09:55 IST

Study: intrahour realized-variance timing. Status: REJECTED; no positive BTC discovery edge.

Verified using GitHub Actions connected API on this check:
- Run: https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44664160577
- Job 136049282983 completed success, including `python scripts/independent_variance_timing_v1.py` and artifact upload.
- Artifact 14597395897, `variance-timing-v1-ledgers`, 295585 bytes, SHA256 `38b5956de288f6b7606b444434be1314f201be8fad2fe39a6496266dd7cc3805`, not expired, run head SHA `d92f2f39e0debc3af5a59b81f3ff94bf08e226b4`.
- BTC 2025 discovery configurations all negative. Frozen continuation model threshold 0.35, 1.5 ATR stop, 2R target: BTC PF 0.779, 472 trades, 2025 -9.22%, 2026 Jan-Oct -22.99%, 22-month -30.09%; ETH PF 0.901, 505 trades, 2025 -9.00%, 2026 Jan-Oct -5.27%, 22-month -13.80%. These are model-reported figures, not independently reconciled.

Unresolved audit: download and independently reconcile all individual trades, NAV and 22 monthly records; inspect source for pre-entry leakage, margin, funding, spread and cost stress. The available connector can inspect this known run but has no general list-push-workflow-runs operation; public GitHub API access from local container failed with DNS resolution error. This is an execution-verification limitation, not evidence of a missing or successful new experiment. No new hypothesis was launched in this checkpoint. Next research iteration must check for newer pending studies and otherwise launch one economically distinct mechanism; do not re-optimize rejected variance timing.
