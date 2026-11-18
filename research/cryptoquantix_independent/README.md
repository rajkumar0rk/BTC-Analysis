# CryptoQuantix independent BTCUSD replay (isolated research)

**Source data:** `rajkumar0rk/BTC-Analysis`, **read only**. **Code location:** `research/cryptoquantix_independent/` on a separate `feature/cryptoquantix-isolated-20261118` branch. No existing analysis or cron/schedule is changed. The new GitHub Actions workflow only runs upon this branch's code push; it writes all output to a separate artifact, not the repository.

This is an **independent implementation** of the published [CryptoQuantix](https://github.com/CryptoQuantix/CryptoQuantix) rules, not the original author’s backtest running unchanged. Its three sleeves are:

- **MacroCore:** Daily close above SMA200 -> buy next daily open, 5×ATR20 daily-close Chandelier exit next open, 25% catastrophe stop and 30% annual-volatility exposure with 25% step sizing.
- **TrendBreakdown:** Long on 168h high breakout in daily uptrend; short on 48h low breakdown in daily downtrend, 48h SMA gate, 2×ATR14 stop. Short 2R TP/24h max hold, long no TP/168h max hold. **Needs taker buy ratio**, not present in the Delta OHLCV archive. `--flow-mode binance-proxy` uses Binance BTCUSDT Futures hourly aggressor-volume ratios, so results **are not exact Delta rule parity**. For genuine Delta data supply `--flow-mode strict --flow-csv file.csv` containing UTC `time,buy_ratio`. With no CSV, the sleeve is disabled rather than pretending to have the missing data. `--flow-mode no-flow-filter` removes the condition and is an explicitly different strategy.
- **FundingSqueeze:** Short in macro bear when the daily 200SMA is falling relative to 30 days prior, 1h close below SMA48, and the last completed Delta funding-rate observation is at least 0.01% around an assumed 8h funding event; 2×ATR14 SL/2R TP/24h max hold. Funding is an **hourly chart rate observation, not an actual funding payment ledger**. This is a research proxy and needs live parity tests.

## Data access, gaps and 2024 warm-up

- Uses original gzip CSV partitions in `data/delta_india/BTCUSD/1m`, verified against the repo manifest's SHA256; no files under `data/` are overwritten.
- Only fetches missing minutes via Delta Exchange India historical 1-minute REST API, into **memory**. Its existing 2026-10 manifest shows 1,440 missing minutes; if the public API cannot supply them, October is explicitly marked incomplete.
- Only fetches 2024-03 through 2024-12 daily BTCUSD candles for the missing 200-day SMA warm-up, again **without editing existing data**. If unavailable, January–July 2025 are not treated as verified backtest months.
- Uses existing archived hourly FUNDING candles; only attempts to fetch missing observations. Treats 00:00/08:00/16:00 UTC prior-hour rate as a settlement **proxy**. It cannot verify actual settled cash transfers.
- Data-quality statuses in `monthly_results.csv` prevent incompletely sourced months from being misreported as fully comparable.

## Modeling limitations and costs

Default assumed market (taker) orders: 0.05% fee per side, 18% GST **on fees only**, and an assumed 0.02% slippage per side. Native BTCUSD contract increment 0.001 BTC, total gross notional cap 2× account equity, 1% risk per tactical position, monthly mark-to-market account returns. These are **explicit modeling assumptions**; a verified historical Delta user fee tier, true fills, leverage liquidation and maker-queue data are not provided. Optional `--scalper-offer` waives **closing fees only** for eligible completed round trips of 30 minutes or less; the offer's historic validity and account eligibility are not established by the backtest. Most strategies hold much longer than 30 minutes.

The model deliberately does not fabricate historical trade direction or actual funding payments. Consequently, **even a positive modeled month is not proven after all real exchange costs**. Historical optimization and regime selection remain overfitting risks. For high-confidence verification obtain Delta taker-side trade archives, actual funding settlements and your applicable fee schedule; then re-run in strict mode.

## Run

In a GitHub Actions runner or local clone of BTC-Analysis:

```bash
pip install -r research/cryptoquantix_independent/requirements.txt
python research/cryptoquantix_independent/run_all.py --self-test
python research/cryptoquantix_independent/run_macrocore.py --self-test
python research/cryptoquantix_independent/run_all.py \
  --data-root . --output-dir /tmp/cryptoquantix-independent-results \
  --flow-mode binance-proxy --capital 10000 --fee .0005 --slippage .0002 --gst .18
```

For no external requests (returns valid results only where existing data permit):

```bash
python research/cryptoquantix_independent/run_all.py --data-root . \
  --output-dir /tmp/cryptoquantix-existing-data-only --flow-mode strict --no-api
```

The isolated branch-only `.github/workflows/cryptoquantix-independent.yml` performs the first run when code is pushed to **its own branch**, and uploads `monthly_results.csv`, `daily_equity.csv`, `closed_trades.csv`, `fills.csv`, `archive_manifest_verified.csv`, `summary.json`. Existing workflows are not modified and nothing is pushed to `main`.

**Benchmark:** January 2025–October 2026, exactly 22 months. Compare monthly return and loss severity, win/loss counts, maximum daily marked-to-market drawdown, cost breakdown. **Do not accept a high total profit with -15% months as a match for the goal.**

Source: [CryptoQuantix MacroCore](https://github.com/CryptoQuantix/CryptoQuantix/blob/main/src/strategies/macro_core.py), [TrendBreakdown](https://github.com/CryptoQuantix/CryptoQuantix/blob/main/src/strategies/trend_breakdown.py), [FundingSqueeze](https://github.com/CryptoQuantix/CryptoQuantix/blob/main/src/strategies/funding_squeeze.py), [C4 portfolio](https://github.com/CryptoQuantix/CryptoQuantix/blob/main/scripts/equity_sim.py). [Delta BTCUSD fees and GST](https://www.delta.exchange/support/solutions?articleId=80001177864), [Scalper Offer](https://www.delta.exchange/support/solutions?articleId=80001172745).