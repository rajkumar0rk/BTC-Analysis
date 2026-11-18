# ETHUSD futures historical data for independent backtesting

The feature branch `feature/ethusd-backtest-data-20261118` contains a new, **ETH-only** archive pipeline; it does not change any existing BTC history, BTC strategies, schedules, or `main`.

## Sources
Delta Exchange India public [Historical Candles API](https://docs.delta.exchange/), with native `ETHUSD`, `MARK:ETHUSD`, `OI:ETHUSD`, and `FUNDING:ETHUSD` symbols, by UTC month. All data are exchange-observed candles, not reconstructed or filled forward.

| Source | Resolution | Location |
|---|---|---|
| ETHUSD traded futures OHLCV | 1 minute | `data/delta_india/ETHUSD/1m/YYYY-MM.csv.gz` |
| ETHUSD mark-price OHLC | 1 minute | `data/delta_india/ETHUSD/institutional/history/mark_1m/YYYY-MM.csv.gz` |
| ETHUSD open interest | 5 minutes | `data/delta_india/ETHUSD/institutional/history/open_interest_5m/YYYY-MM.csv.gz` |
| ETHUSD historical funding-rate observations | 1 hour | `data/delta_india/ETHUSD/institutional/history/funding_1h/YYYY-MM.csv.gz` |

## Run independently

One-time push trigger on the isolated feature branch:

`Actions > Backfill Delta India ETHUSD backtest history`

The workflow runs only on its explicitly named feature branch and **has no schedule**. It downloads January 1, 2025 through the previous complete UTC day (Nov 2026 is a partial month until December begins). Running again reuses completed monthly price partitions. The files are gzip-compressed and each 1-minute partition has a SHA-256 hash and observed-vs-expected candle count in the price manifest. The institutional manifest records observations and any missing intervals.

To run manually:

```sh
python scripts/sync_delta_ethusd_1m.py --start 2025-01-01
python scripts/collect_delta_ethusd_institutional_data.py backfill
python scripts/verify_delta_ethusd_history.py
```

For a completed 22-month research window, pass `--through 2026-10-31` to the price collector, and `--end-exclusive 2026-11-01` to the institutional collector.

## Backtest data-quality constraints
- Even when a partition is nearly complete, **missing minutes remain missing**. Do not treat an incomplete month as a full-month result.
- `FUNDING:ETHUSD` provides *observed funding-rate candles*, **not actual realized funding payments**. Settled funding cashflows and fee taxation require separate reconciliation.
- ETHUSD price OHLCV does not include historical bid/ask depth or historical taker-buy volume.
- If your strategy requires a Daily SMA200 from January 1, 2025, pre-2025 warmup data are necessary. The baseline archive starts January 1, 2025.
- Historical data are for ETHUSD **futures**, not ETH options or ETH spot.

The workflow commits **only new ETH paths** to the feature branch, and uploads manifests/quality results as an Actions artifact. It never touches BTC paths or existing schedules.

## Audit
Run `python scripts/verify_delta_ethusd_history.py`, then review `reports/ethusd_data_quality/summary.json`, `data/delta_india/ETHUSD/1m/manifest.json`, and `data/delta_india/ETHUSD/institutional/history_manifest.json`.
