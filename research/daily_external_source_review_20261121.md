# External source review — 2026-11-21 IST

Research-only provenance. No strategy validated, no new backtest executed in this review.

## Trend Day Pullback (MNQ 5m)
Source: https://roboquant.dev/t/d196c274-57a2-4f2d-9f31-63fa68cfa963
Publisher listed: chudtrader; public version 1 dated 2026-11-12; open-source remix with attribution per listing, exact code/license not retrieved. Original X post by @algojan not verified. MNQ CME 5-minute, Nov 2025–Nov 2026. Published simulation: 229 trades, 46.7% wins, PF 1.67, +57.8%, 3.7% max DD. From 10:30 New York assess session VWAP and daily range; VWAP pullback and continuation candle; 1x ATR stop, 2R target; one trade/day, no entries after 12:30, flat by 15:50; $400 risk/trade, $800 daily loss stop, $1000 daily profit cap. Missing precise code/entry thresholds, fill timing, costs, underlying data and crypto-specific session translation. **BLOCKED — not yet reproducible on Delta BTC**. Do not invent rules or claim reported MNQ performance applies to BTC.

## Bitcoin SuperTrend
Source: https://roboquant.dev/t/c630aaf2-3d6c-480f-ae16-82478a385012
Publisher listed on related marketplace page: sird (not @algojan). CME micro BTC, 10/5 SuperTrend, 200 SMA rising/falling, 52-bar efficiency >=0.05, enter on flip, stop at SuperTrend, exit opposite flip; published simulation +230.8%, PF 1.32, DD 16.3%, 1321 trades, Dec 2021–Oct 2026. Exact code, fees, version, license and duplicate-check against previous SuperTrend studies still required. **INCONCLUSIVE, novelty gate pending**.

## Execution handoff
Latest task-specific branches visible include research/daily-external-keltner-bounce-screen-20261120-v1 and research/daily-external-ema-vwap-armed-20261120-v1. Current connector exposes no general workflow-run listing, so actual latest GitHub Actions run, jobs and artifact state could not be established here. Do not claim a successful backtest, screen pass, 22/22 profitable months or advance to slippage stress without audited zero-slippage-first BTC results. Resume by identifying latest workflow run and its ledger, finish/repair that study first. Preserve task isolation; do not change other schedules or live accounts.
