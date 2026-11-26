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
