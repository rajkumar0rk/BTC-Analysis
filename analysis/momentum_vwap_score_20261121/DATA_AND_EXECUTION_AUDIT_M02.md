# M02 — Delta archive and replay feasibility audit (2026-11-21)

Status: **DATA FOUND / HISTORICAL REPLAY NOT YET RUN**. This is not a backtest result.

## Verified repository evidence
- Branch: `research/momentum-vwap-score-20261121`, existing source-locked M01 ledger.
- Authentic Delta India BTCUSD 1m partitions are in `data/delta_india/BTCUSD/1m/`: 2025-01 through 2026-10, plus partial 2026-11 and `manifest.json`. The 22 desired monthly files are present, **but file presence alone does not prove bar-level coverage or checksum integrity**.
- The repository documents the public Delta India candle endpoint and `scripts/sync_delta_btcusd_1m.py`; this is not Binance BTCUSDT data. The documented 2026-10 missing 1,440 UTC-minute candles requires validation before asserting a full 22-month result.
- Existing runner scripts and GitHub Actions workflows are present, but **no workflow run exists on this momentum branch** as checked in this iteration. A source-faithful Momentum VWAP replay and its artifacts are still missing.
- Source-locked external Pine/Python details are recorded in `EXPERIMENT_LEDGER.md` (M01), including 4h long-only score, anchored VWAP, cooldown and ATR stop. Do not confuse publisher-reported +16.27%, PF2.13/19 trades with independent Delta results.

## Novelty gate — preliminary PARTIAL OVERLAP, NOT YET APPROVED
- `codex/STRATEGY_NOVELTY_GATE.md` explicitly names Stage25 hourly momentum and Stage13 multi-timeframe trend/pullback studies, plus Stage24 squeeze/breakout. The proposed ROC+RSI+MACD-acceleration+ADX+VWAP score may have distinct economic content, but a line-by-line comparison with those branches' original rules and reports is required.
- No novel-study approval or new backtest is claimed. Do not bypass this gate to run generic momentum parameter grids.

## Exact next executable steps
1. Read `data/delta_india/BTCUSD/1m/manifest.json`; validate hashes, time boundaries, gaps, candle open/close timestamps and 4h resampling. Explicitly quarantine missing October 2026 minutes.
2. Compare Stage25 hourly momentum signal and Stage13 pullback rules with the 7-condition source-locked Fusion score; write a complete `NOVELTY_CHECK.md` with paths and economic difference, decision NEW/PARTIAL/SKIP.
3. If gate passes, implement original 4h Pine source faithfully, including daily VWAP anchoring (UTC reset), indicator warmup, cooldown, next-eligible-minute fills, ATR stop and conservative intraminute exits. Compare Pine versus companion Python discrepancies before treating one as ground truth.
4. Run actual GitHub Actions historical BTC2025 zero-slippage screen (0.05% fee per side plus 18% GST on fee), publish workflow/job URL, full trade ledger, month-by-month NAV and risk metrics. Funding unmodeled. Do not infer profit from unit tests.
5. If screening is promising, freeze source-derived parameters and recheck BTC2026/ETH before any adverse-slippage stress.

No other branch, live account or strategy schedule was changed.
