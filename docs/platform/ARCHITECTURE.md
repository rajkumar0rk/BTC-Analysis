# BTC-Analysis platform architecture — M1
Status: Foundation contracts implemented; engines, APIs and visual editor not yet implemented.

## Goals
One Python strategy SDK and deterministic, multi-asset simulation core. Visual graphs compile to Python targeting the same SDK as handwritten strategies; no alternate JSON trading engine. JSON is a portable versioned configuration, result and visual-graph representation, never arbitrary executable expressions. Existing historical research remains immutable evidence.

## Boundaries
| Module | M1 contract / next implementation |
| --- | --- |
| `src/btc_analysis/contracts.py` | Market, dataset, cost, config, order, fill, closed trade and run manifest contracts |
| `src/btc_analysis/sdk.py` | Causal market context and strategy/indicator protocols |
| `src/btc_analysis/serialization.py` | Canonical wire encoding and reproducible SHA-256 |
| `src/btc_analysis/execution_policy.py` | Fail-closed policy specification; execution disabled |
| `data/`, `analysis/`, `scripts/`, `dashboard/` | Existing research/data/dashboard; not replaced |
| Future data module | Partitioned Parquet, manifest, calendar, ingestion/quality, coverage |
| Future simulation modules | Clock, event queue, execution, order matching, margin, costs, risk, account |
| Future apps and workers | Authenticated FastAPI, job queue, isolated workers, React/TypeScript studio |
| Future research services | Optimization, robustness, paper replay, registry |

Use a single installable Python package now; introduce subpackages and app directories when functional components are implemented. Avoid empty scaffolding. Core simulation never imports HTTP, GitHub, UI, database or exchange credentials. Exchange adapters supply instrument specs, calendars, costs and margin policies. Storage and execution use explicit interfaces. Initial instrument BTCUSD, then ETHUSD, dated futures, options, spot. An enum is not proof the instrument's engine is supported.

## Causality and accounting
All instants aware UTC. Candle intervals [open, close), completed data visible at close only. Reporting month timezone explicitly selected (e.g. Asia/Kolkata). 15m or 1h signals may use 1m execution. No same-bar retrospective fill; next eligible execution event and conservative ambiguous intrabar scenarios. Missing candles remain missing; strict runs fail unless explicitly configured otherwise. Every signal and actual fill emits a reason when it occurs. No reconstructed reasons. Prices, quantity, fees, taxes and funding use Decimal at boundaries; optimized numerical kernels may use float only with explicit tolerances and reconciliation. Contract size/expiry/settlement currency explicit. Account USD, price points and percent are separate units. Funding paid signed; costs not silently waived; tax rate fraction; bps = 1/10000. Mark price required for configured liquidation; quote evidence required for spread; funding input required if enabled. Data requirements are necessary, not sufficient for accurate exchange simulation. Portfolio margin and options require verified venue models later, not a generic approximation.

## Reproducibility
Store strategy code/parameter hashes, dataset manifests, engine version, config fingerprint, seed, result digest, limitations and report. Pinned frozen strategies are immutable revisions. Never label historical tests after prior exposure as untouched OOS. Separate training, validation and forward runs. Monthly MTM return and realized exit/entry-month sums are distinct.

## Deployment
Existing Pages UI + immutable dashboard-data snapshots continue independently. New services will expose authenticated API; no secrets in Pages. GitHub Actions can run trusted research jobs. Untrusted Python must use dedicated isolated workers, never a privileged workflow with repository write credentials. Initial low-resource deployment: one bounded worker, disk quotas and explicit scheduling; scale after measured benchmarks. Database and Parquet implementation deferred.

## Architectural decisions
1. Python-only strategy language; visual graph is a versioned source representation compiled deterministically, with explicit one-way behavior for arbitrary Python edits.
2. Event-driven canonical execution semantics; optimized vectorized indicators must pass reference parity.
3. Exact source/version hashes; append-only results with schema evolution and immutable frozen revisions.
4. Existing project retained; strangler migration with parity, never rewrite historical results.
5. No arbitrary Python execution until verified OS isolation (see SECURITY.md).
