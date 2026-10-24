# Delta India RWA momentum scanner

Research-only, read-only scanner inspired by Ross Cameron's first-pullback method. Does **not** submit orders or assert guaranteed profitability.

## Run
```bash
python rwa_scanner/scan.py --output rwa_scanner/output --max-symbols 10
python -m unittest discover -s rwa_scanner -p 'test_*.py'
```

Uses Delta India public tickers + one-minute candle history, with a curated **explicit** Delta-symbol -> underlying-US-equity mapping. No API key needed for Delta market-data endpoints. Known symbols may be delisted or renamed. Only matches reported by Delta live tickers are scanned. Scans the top 10 mapped symbols by Delta turnover by default; set `--max-symbols 0` to scan all mapped symbols. A completed 1-minute candle (not intra-bar execution) confirms a first pullback.

For share float, actual US equity prices and stock news, add an Actions repository secret `FMP_API_KEY` from [Financial Modeling Prep](https://financialmodelingprep.com/). FMP endpoint availability depends on subscription; missing/quota-denied metrics stay **N/A**, never invented. For news without FMP, a Google News RSS search limited to major attributed publishers is a best-effort fallback. A headline is NOT validated positive news. RSS is not guaranteed and coverage may be delayed.

The original Ross Cameron screen requires **underlying US stock** gain ≥10%, daily relative volume ≥5×, $2–$20 stock, float below 20 million shares and meaningful favorable news. This tool instead presents Delta futures 24-hour percentage change and **1-minute volume relative to prior 20 minutes** as clearly labeled *proxies*. These are not interchangeable with stock-day metrics. It does not verify all original conditions.

The workflow runs on push to `main` and manually with **Actions → Scan Delta RWA momentum → Run workflow**. Daily scheduled scans are intentionally not enabled to avoid unnecessary polling. Download the `rwa-momentum-scan` artifact for full `results.json` and `summary.md`; this workflow does not auto-commit time-sensitive market observations. Results include a timestamp, missing-data flags, and source URLs.

Failures: when Delta is unavailable, results are still written and the job fails. When enrichment fails, a partial report is written and unknowns remain unknown. No order placement, no account credentials, no investment advice.
