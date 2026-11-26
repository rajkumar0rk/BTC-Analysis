# Milestones and acceptance gates

M1 Foundation: typed v1 contracts, Python SDK interfaces, deterministic encoding, fail-closed execution policy, architecture/security/data/migration docs, package tests on Python 3.11 and 3.12, legacy dashboard unchanged. CI success required to mark verified. Independent maintainer review remains a distinct gate.

M2 Data engine: Delta archive ingestion, content-addressed Parquet, manifest checks, bounded queries, session-aware coverage, completed-bar aggregation and CI benchmark. See [historical data](HISTORICAL_DATA.md). Open-label attestation and external independent review remain separate gates; actual coverage determined by audit.
M3 Backtest engine: [trusted reference simulator](BACKTEST_ENGINE.md), chronological fills, two-path replay, order lifecycle, FIFO positions, fee/tax reconciliation and deterministic tests. Exchange-specific leverage, funding, spread, liquidation and untrusted code remain later gates.
M4 Python SDK + indicators: [streaming library and SDK](PYTHON_SDK.md), 13 indicator families, declared multi-timeframe access, separate warmup, formula fixtures and trusted example. External library and frozen-strategy parity remain separate gates.
M5 Venue execution: [reference fixed-tier risk engine](MARGIN_ENGINE.md), explicit isolated/cross collateral, mark-first liquidation scenarios, signed settlement input and fee/tax reconciliation. Historical profiles, actual settlement attestation, spread, tiered/portfolio margin and exchange parity remain outstanding.
M6 API/jobs: [local authenticated API and durable queue](BACKEND_API.md), immutable source revisions, idempotent submission, trusted synthetic subprocess worker, cancellation, leases, progress and ownership. Arbitrary-code isolation, historical jobs and deployment remain gated.
M7 Frontend shell: [React/TypeScript studio](FRONTEND.md), real local API, source revisions, synthetic runner, responsive job/results views and browser CI. Production deployment remains gated.
M8 Python editor: [Monaco and compiler diagnostics](PYTHON_EDITOR.md), SDK catalog/snippets, syntax-gated UI saves and immutable versions. Semantic checks and secure arbitrary execution remain later gates.
M9 Visual Python builder: [typed rule graph and deterministic Python compiler](VISUAL_BUILDER.md), grouped conditions, multi-timeframe indicators, fixed risk brackets, source round-trip, generated/handwritten parity fixture, and code mode. Arbitrary code execution and advanced graph/risk features remain gated.
M10 Runner: [bounded historical visual research jobs](HISTORICAL_RUNNER.md), pinned datasets and versions, explicit assumptions, progress/cancel/results. Multi-year, leveraged historical jobs and arbitrary Python remain gated.
M11 Analytics and replay: [stored-result analytics and pinned replay](ANALYTICS.md), closed-trade metrics, account MTM, monthly tiles, searchable ledger, fill details and CSV.
M12 Registry: [immutable strategy lifecycle](REGISTRY.md), freeze/clone/archive/restore, transactional state and submission gates, lineage, comparison and linked job history. Permanent retention/backup policy remains pending.
M13 Optimization: bounded parallel grid/random, train-only and reproducible search.
M14 Validation: chronological OOS, sensitivity, stress, data and liquidation audits.
M15 Forward paper: newly arriving data, separate execution state, reconciliation.
M16 Multi-market: venue calendars, dated contracts/rollovers, options only with verified specifications.
M17 Production: independent security, load, failure recovery, backup and deployment gates.

## Migration
Keep main research, dashboard-data, retained/archived refs, original frozen strategy JSON and historical raw data intact. Add platform components under src and tests. Migrate one explicit strategy via exact source snapshot; record old/new assumptions, unit-level indicator parity, chronological trade ledger parity and numerical discrepancies. Any deliberate correction produces a new version with an audit note. Do not replace original ledgers or promote in-sample performance as live validation. Existing workflows and Pages remain operational until the new path independently passes acceptance.
