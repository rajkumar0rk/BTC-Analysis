# Trend Following — iteration 3, 2026-11-21: replay data location verified

Status: **DATA LOCATION CONFIRMED; NO HISTORICAL BACKTEST EXECUTED**. This report corrects the earlier unverified statement that the 1m dataset was not established.

## Verified GitHub facts
- The isolated branch `research/trend-following-family-20261121` has genuine repository paths `data/delta_india/BTCUSD/1m/2025-01.csv.gz`, `2025-02.csv.gz`, ... and existing `scripts/sync_delta_btcusd_1m.py`; GitHub contents API verified 2025-01 blob SHA `30d5018194a10d36aa381c6ba2f5b6f35b842352`, size 663,909 bytes.
- Existing historical replay examples: `scripts/research_trend_pullback_breakout_stage13.py`, `scripts/research_v7_2_daily_4h_2025.py`, `scripts/research_swing_donchian_stage17.py`, and their GitHub Actions workflows. These are references for engineering only, not novelty.
- No GitHub Actions workflow runs were returned for branch `research/trend-following-family-20261121` by the GitHub REST API query at this iteration. No verified trade ledger or 2025 NAV output for this family exists yet.
- The repository root README is stale: it describes the original 5m archive and does not enumerate the newer Delta India 1m files. Do NOT interpret README absence as data absence.
- Earlier source audit established that `xy3293/crypto-strategy-backtest` lists Ichimoku 4h rules, but code-level causal displacement, source license and novelty are not yet verified. Do not copy source code or invent missing parameters.

## Required immediate next execution
1. Read the existing 1m loader in `scripts/research_v7_2_daily_4h_2025.py` and compare `scripts/research_trend_pullback_breakout_stage13.py` for novelty. Verify January 2025 CSV schema, first and last timestamps, missing minutes and bar-open labeling in an executable GitHub Actions job. Dataset filenames and Git blob hashes do NOT by themselves verify OHLCV content/provenance or continuity.
2. Resolve source license and Ichimoku displacement; if blocked, choose a differently licensed, clearly source-defined trend persistence strategy, rather than another plain SuperTrend/EMA/ADX clone.
3. On THIS branch only, commit an executable strategy, workflow and preregistered risk/fee assumptions. Launch and complete BTC2025 historical 1m backtest, publish job URL, original trade ledger, full monthly IST NAV, PF, drawdown, trade count, fees and GST. Zero slippage FIRST; no funding claim. Freeze 2025-selected settings before later BTC2026/ETH recheck.

No live accounts, protected branches or other research families changed.