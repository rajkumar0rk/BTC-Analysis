# Final completion phase
17 reference milestones have passing CI at their respective verified commits; this does not establish production readiness.

## Priority 1: dependency remediation
M17 baseline CI: foundation 45771856437, web 45771856451, readiness 45771856445, all succeeded. Readiness audit found Python and npm exit 1. Artifact 15094621848 contains advisory details. Bounded local benchmark: 100 requests, four threads, no errors, median 7.398 ms, p95 10.946 ms, elapsed 0.2037s; 600-bar synthetic worker 0.4156s; peak RSS process 109492 KiB, child 107524 KiB. Backup restore passed. Not target-VPS load certification.

Upgrade vulnerable dependencies, enforce audit pass, verify both Python versions, historical archive audit and Chromium; then commit resolved dependency locks and enforce reproducibility. All status remains pending until exact-head results are inspected.

## Remaining implementation/acceptance order
1. Dependency remediation and locked builds.
2. Multi-year historical engine and bounded memory/result shards; verify actual BTC and ETH.
3. Full historical venue costs/risk adapters with attested parameters, mark and funding settlement evidence.
4. Larger optimization and genuine chronological walk-forward validation with frozen holdouts.
5. Independently isolated arbitrary Python execution, no network/credentials, resource quotas and security escape testing. Keep fail-closed until verified.
6. Multi-market data and execution, actual paper-feed comparison.
7. Target-host secure deployment, backup/restore drills, load/soak and independent review.

No live trading permissions or production approval.
