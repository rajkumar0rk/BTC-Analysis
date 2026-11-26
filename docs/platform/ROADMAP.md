# Milestones and acceptance gates

M1 Foundation: typed v1 contracts, Python SDK interfaces, deterministic encoding, fail-closed execution policy, architecture/security/data/migration docs, package tests on Python 3.11 and 3.12, legacy dashboard unchanged. CI success required to mark verified. Independent maintainer review remains a distinct gate.

M2 Data engine: Delta archive ingestion, content-addressed Parquet, manifest checks, bounded queries, session-aware coverage, completed-bar aggregation and CI benchmark. See [historical data](HISTORICAL_DATA.md). Open-label attestation and external independent review remain separate gates; actual coverage determined by audit.
M3 Backtest engine: [trusted reference simulator](BACKTEST_ENGINE.md), chronological fills, two-path replay, order lifecycle, FIFO positions, fee/tax reconciliation and deterministic tests. Exchange-specific leverage, funding, spread, liquidation and untrusted code remain later gates.
M4 Python SDK + indicators: [streaming library and SDK](PYTHON_SDK.md), 13 indicator families, declared multi-timeframe access, separate warmup, formula fixtures and trusted example. External library and frozen-strategy parity remain separate gates.
M5 Venue execution: verified fees/tax/funding, sizing/lot constraints, mark-price margin/liquidation, isolated/cross and portfolio when evidence permits.
M6 API/jobs: authenticated strategy versions, idempotent submission, isolated worker, cancellation, progress, authorization and limits.
M7 Frontend shell: accessible React/TypeScript navigation and job/results views.
M8 Python editor: Monaco, diagnostics, safe submission and versioning.
M9 Visual Python builder: typed graph, validation/compiler, code preview, deterministic graph/code parity, custom code mode.
M10 Runner: run configuration, live progress, cancellation, status/history.
M11 Analytics and replay: standard results, actual fills/reasons, account vs points, monthly MTM.
M12 Registry: immutable versions, freeze/clone/archive, provenance and retention.
M13 Optimization: bounded parallel grid/random, train-only and reproducible search.
M14 Validation: chronological OOS, sensitivity, stress, data and liquidation audits.
M15 Forward paper: newly arriving data, separate execution state, reconciliation.
M16 Multi-market: venue calendars, dated contracts/rollovers, options only with verified specifications.
M17 Production: independent security, load, failure recovery, backup and deployment gates.

## Migration
Keep main research, dashboard-data, retained/archived refs, original frozen strategy JSON and historical raw data intact. Add platform components under src and tests. Migrate one explicit strategy via exact source snapshot; record old/new assumptions, unit-level indicator parity, chronological trade ledger parity and numerical discrepancies. Any deliberate correction produces a new version with an audit note. Do not replace original ledgers or promote in-sample performance as live validation. Existing workflows and Pages remain operational until the new path independently passes acceptance.
