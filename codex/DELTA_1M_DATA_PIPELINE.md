# Delta Exchange India BTCUSD 1-minute history

Source: `https://api.india.delta.exchange/v2/history/candles` with `symbol=BTCUSD` and `resolution=1m`. Use the public endpoint without credentials; **this source is distinct from the Binance BTCUSDT futures candles and from the earlier uploaded 5m OHLCV file whose exchange was not confirmed**.

## Run in GitHub Actions (cloud; not your computer)

Open **Actions → Sync Delta India BTCUSD 1m candles → Run workflow** on `main`. Leave start at `2025-01-01` and through blank to download until the previous UTC day. Daily updates are scheduled at 02:30 UTC; Actions can be disabled by repository settings. The GitHub runner makes the HTTP requests, not the user's PC.

Monthly gzip CSV files will appear in `data/delta_india/BTCUSD/1m/YYYY-MM.csv.gz`; `manifest.json` includes coverage counts and checksums. No missing bars are interpolated. This is **true exchange 1m candles**, not reconstructed from 5m, and it includes OHLCV only (not funding, spreads, or execution prices).

## Limitations and verification

* Public endpoint rate limits and historical retention can change. Cloud runner access to the Delta endpoint is not guaranteed. Check Actions run logs.
* Historical gaps or missing periods can cause the validation step to fail; fix the source/range instead of inventing bars.
* Timestamp labeling is preserved as returned by the API; verify whether your chart uses open/close candle timestamps before time-of-day research.
* Closed monthly partitions are reused and checked; force re-download is available from the CLI.
* A workflow commit is not complete merely because these files have been added. Confirm the Action passes and data partitions are in GitHub.

Manual local alternative: `python scripts/sync_delta_btcusd_1m.py --start 2025-01-01`.
