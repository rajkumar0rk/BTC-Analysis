# Data, configuration and result contract v1

The typed Python boundary in contracts.py is authoritative for M1. Serialization produces canonical UTF-8 JSON with sorted keys, exact decimal strings, UTC ISO-8601 Z timestamps and enum string values. No binary floats at this boundary. Schema v1 config and run manifest hashes are SHA-256 of canonical bytes. Inputs are not dynamically deserialized/executed. Future API decoder will reject unknown fields and invalid versions.

| Contract | Required fields / invariants |
| --- | --- |
| Instrument | venue, symbol, asset type, tick/lot, multiplier, quote/settlement currency; dated expiry and option strike/right |
| Candle | instrument, timeframe, open/close UTC, OHLCV, valid range and exact duration |
| DatasetRef | immutable manifest hash, provenance, interval, coverage status/gaps |
| BacktestConfig | strategy revision, instrument, datasets, range, timeframes, capital/currency, leverage/margin, fee model, path policy, timezone, calendar, seed |
| OrderIntent | unique ID, decision time, order type, aligned quantity/prices, reason |
| Fill | order link, exact execution time, aligned price/quantity, fee/tax, reason |
| ClosedTrade | original entry/exit fills, reasons, matched quantity, currency, gross/net cash P&L and reconciled costs |
| RunManifest | code/config/data/result hashes, engine version, UTC creation, limitations |

## M2 requirements
Map existing Delta monthly gzip CSV into immutable partitions with source checksum and verified candle-open convention. Explicit source schema and units; sorted unique timestamps; detect duplicates, gaps, off-grid timestamps and invalid rows. Report actual coverage (not inferred from filename). No fill-forward. Keep source bytes; create derived Parquet under separate storage; support bounded reads and caching. Validate warmup separately from evaluation dates. Session-aware missing-data checks for exchange calendars. Data kinds can have different observation cadences; absence of funding/mark/quotes never treated as zero. DatasetRef coverage assertions must be backed by M2 manifests.

## M3 result requirements
Record every accepted/rejected order intent, event ordering, fills, partial positions, funding events, margin, liquidation events and equity snapshots; capture original execution reason. Extend v1 closed-trade contract to handle multi-currency FX and exchange-specific gross P&L; do not assume linear P&L for inverse contracts. MTM drawdown, realized drawdown, account return and instrument points must be named independently. Record all costs, omitted components, data gaps and ambiguous fills. Unit and reconciliation tests before publication.
