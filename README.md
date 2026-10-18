# BTC-Analysis — BTC futures OHLCV research archive

Research archive from the October 2026 ChatGPT analysis of a supplied BTC futures 5-minute OHLCV dataset. Includes the original data, 15m/30m aggregates, exploratory statistical outputs, and all available research notes.

> **Research only — no live-trading signal is validated.** Findings may reflect multiple-testing bias, correlated signals, unknown exchange data quality, assumed bar-label conventions, and absent execution costs. This repository preserves observations, not guarantees.

## Start here

- [Research index](codex/FINDINGS_INDEX.md) — headline findings by timeframe and supporting artifacts
- [Context and research handoff](codex/RESEARCH_CONTEXT.md) — decisions, definitions, and current limitations
- [Data conventions](codex/DATA_CONVENTIONS.md) — source provenance, candle alignment, New York daylight saving, future-return definitions
- [Future research plan](codex/NEXT_ANALYSIS.md) — priority experiments and validation gates
- [Codex agent instructions](codex/AGENTS.md) — guidelines for later Codex sessions
- [File inventory](manifest.csv) — path, source filename, size, SHA-256 of archived files

## Structure

```text
BTC-Analysis/
├── README.md
├── AGENTS.md
├── requirements.txt
├── manifest.csv
├── data/
│   ├── raw/underlying_bars(1).csv
│   └── derived/btc_futures_{15m,30m}_ohlcv.csv
├── analysis/
│   ├── 5m/              # predefined studies + candle-by-candle time discovery
│   ├── 15m/             # 15m clock and candle-shape discovery
│   ├── 30m/             # 30m clock and candle-shape discovery
│   └── institutional/   # 30m sessions/level-interaction/event tests
├── codex/               # durable context for future research
└── scripts/             # new independent scanning & integrity utilities
```

The supplied analysis outputs are *snapshots*. The original notebooks/scripts that generated the historical detailed tests were not available in this session, so `scripts/scan_clock.py` is a **new reusable baseline analysis tool**, not a claim to reproduce every existing metric exactly.

## Quick start

```bash
python -m pip install -r requirements.txt
python scripts/verify_archive.py
python scripts/scan_clock.py --input 'data/raw/underlying_bars(1).csv' --timeframe 30 --output-dir scratch/30m
```

Use `--timeframe 5`, `15`, `30` or `60` for further clock-time scans. Outputs under `scratch/` are ignored by Git and should be checked before being promoted into `analysis/`.

## Scope and date caveats

- Original file covers approximately **2025-12-31 to 2026-08-01 UTC**, with **61,206 consecutive 5-minute observations**.
- Historical discovery is mostly restricted to **2026-01-01 through 2026-07-31 UTC**; 15-minute subset contains 20,352 bars and 30-minute subset 10,176 bars; the derived CSVs include boundary-day records.
- `America/New_York` conversions account for daylight saving; confirm whether raw bar timestamps represent *open* or *close* before transferring any time rule to TradingView.
- The original input supplies OHLCV only. Exchange, exact instrument, mark price, funding, order book, open interest, transaction costs, and bid/ask fills are not established here.

## Rules for new findings

Pre-register a test before viewing its holdout set, compare against time-of-day/volatility baselines, account for repeated tests and overlapping positions, report absolute price moves plus uncertainty, then run realistic execution replay. Retain null/failed hypotheses as well as successful ones.