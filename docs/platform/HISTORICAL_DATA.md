# M2 Historical data engine

## Usage

```bash
python -m pip install '.[data]'
python -m btc_analysis.data.cli --symbol BTCUSD --symbol ETHUSD --report .platform-local/data-audit.json
```

Use a pinned HistoryStore snapshot, bounded query (100,000 minute interval limit), or streaming iter_batches (maximum 4096 rows per batch). Each source monthly gzip is checked against the existing manifest SHA-256 and exact count; CSV timestamp ordering, minute alignment, valid OHLCV and precision are checked. Missing intervals are recorded, never interpolated. Derived Parquet uses exact decimal128(38,18), Zstandard compression, row-group pruning and bounded handle cache. The content-addressed objects and manifest snapshots are separate from raw data; latest is atomically switched after complete validation. No new backtest or dashboard deployment is needed.

## Timestamp and causality
Source archives currently say as_returned_by_API. Public REST docs describe epoch seconds but do not settle open/close semantics. M2 preserves raw time and refuses strict causal access without explicit verified-open attestation. The audit uses assume_open=True solely to check raw data parity, never asserts that label is verified. A later comparison to independent exchange timestamps/trades must be reviewed before production causal use. Explicit research-only assumption is available; DatasetRef cannot attest an unverified label. Aggregation emits completed full buckets only; partial/gapped buckets never fabricated. For noncontinuous sessions supply explicit reviewed UTC intervals and anchors; no exchange holiday calendar supplied yet. Strict coverage reports missing expected bars across partitions and calendar windows.

## Scope
Delta India BTCUSD/ETHUSD 1m source files on main only. Older 2024 gap-repair branches are not silently merged. Funding, quote, mark, tick, other venues and real exchange calendars are not implemented by this OHLCV adapter. The Parquet store is derived locally or on CI; not committed to main and not deployed to VPS. Source provenance, data integrity, actual coverage and timestamp semantics are distinct. Future M3 consumes the pinned dataset and chronological completed candle interface.

## CI
Platform historical data audit runs synthetic tests plus full BTC/ETH actual archive import, streaming count parity, unchanged-source reuse parity and records maximum RSS / wall time. Reports are downloadable action artifacts. M1 unit CI runs both foundation and data unit tests on 3.11/3.12. Independent review remains separate.

## Browser repository snapshot loader
The release build stages checksum-verified public BTCUSD/ETHUSD compressed monthly archives from main as same-origin content-addressed binary assets. The browser downloads only partitions overlapping the selected inclusive UTC dates, verifies gzip SHA-256, manifest row counts and exact 1m continuity, and refuses missing dates or invalid rows. Optional Cache Storage retains up to four public partition files; cache hits are rehashed. Custom CSV remains available. The existing 31-day/16 MiB execution limits and explicit timestamp-open research assumption remain; this is not a multi-year engine or verified venue contract model. Data changes on main trigger a new published snapshot through the existing CI/release workflows. No R2/D1 history storage, API credentials or new paid service required.

## Extended browser archives
The retained BTC 2024 verified archive is preserved byte-for-byte from cda60e8e4aa0808469db5d07304dbaed52e190bb. Only trade rows are normalized to UTC months for browser use; gaps (including year-end if uncovered) fail closed. Native main 1m source remains unchanged. Existing 2025–2026 mark/funding observation files are structurally checked at build and content-addressed; their original manifests lack independent hashes. Browser risk runner can fetch matching mark prices for full UTC days within 31 days. Funding observations are staged but never converted to settlement inputs; historical settlement convention/reference mark verification remains pending. 2024 mark/funding retained but not published for risk execution. UI coverage reports source counts/gaps, not timestamp attestation.

## M40 retained BTC 2024 risk integration
The original mark and hourly funding gzip files are hash-checked with their retained manifest, including five-column source risk files (blank volume remains blank). Real rows are normalized by UTC month, and exact observed counts and gaps are preserved; year boundary exclusions are not backfilled. BTC 2024 mark prices are available for both short and continuous leveraged reference runs wherever trade coverage is contiguous. Hourly funding observations extend published coverage but are not settlement data. Actual archive CI and browser integration added; no source files changed. ETH 2024, BTC trade gaps, historical settlement evidence and independent timestamp attestation remain outstanding.
