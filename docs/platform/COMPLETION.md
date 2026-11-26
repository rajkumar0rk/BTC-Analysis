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

M18: upgrade CI 45772559003/45772558986/45772558936/45772558916 passed; Python and npm audits both exit zero. Pin runtime versions from the successful audit. Import exact audited npm lock (artifact 15094622990, SHA-256 378fdda9e7820bbafb15d9c9751cfc1e0c3fc3d2ad8dd6ebe2b37b106af2f000), then enforce npm ci and Python pinned runtime installs in CI. Exact-lock reruns pending. Python pins versions, not wheel hashes; Linux 3.11/3.12 scope. Build toolchain and action commit pinning remain separate security work.

M19: long reference CLI with 1098-day request bound, same continuous simulator, two OHLC paths, NDJSON disk event archives with per-file hashes, exact monthly/MTM metrics and short-run parity tests. Full BTC/ETH benchmark CI required. Existing 24-hour API/optimization/validation remains unchanged; browser/remote orchestration, funded/leverage risk, measured speed and multi-year user-facing UI remain pending. Archive quota 1 GiB per stream, existing 1M order/fill cap and order-ID set retained; not a constant-memory guarantee. Incomplete output has no manifest; ordinary errors remove new output directory. No custom code execution.
M18 lock import succeeded at e68571f; earlier npm CI failed before bot lock commit (GITHUB_TOKEN push did not trigger workflows). New source commit retriggers exact locked builds. Runtime pins are not wheel hash locks.

M18/M19 verified at e03a453: all five workflows passed; both audits exit 0, full BTC 997920 bars/2 paths 143.548s RSS 141496 KiB, ETH 987840 bars/2 paths 251.805s RSS 141916 KiB. M20 introduces standalone trusted browser Python runner, user CSV up to 7 days, editable graph/exact generated source, same simulator, native parity oracle and warm rerun. No arbitrary source execution or server deployment. Pyodide 0.29.3 staged at build with wheel checks from upstream lock; upstream core asset digests recorded, not yet independently pinned/reviewed. Browser-specific performance and dependency audit remain pending. M21 cache and larger history pending.

M20 verified at 5020653: web 45783398209, foundation 45783398205 and readiness 45783398207 all passed. M21: 31-day CSV browser input, optional IndexedDB validated CSV per symbol, worker-local parsed candle cache keyed by exact input hash and instrument, exact indicator output cache keyed by canonical spec, completed-candle clock guard, LRU bound, result parity tests. Actual 31-day BTC/ETH native cache benchmark queued; browser full-month timing and automatic archive download still pending. No credentials or strategy code persistence added; no arbitrary Python execution.
