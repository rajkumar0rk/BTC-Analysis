# BTC-Analysis — research and backtesting platform

The existing research archive and [Backtest Explorer](https://rajkumar0rk.github.io/BTC-Analysis/) remain available. A new Python-first multi-asset platform is being added incrementally, without replacing historical results.

## Platform foundation (M1)

- [Architecture](docs/platform/ARCHITECTURE.md)
- [Historical data engine (M2)](docs/platform/HISTORICAL_DATA.md)
- [Reference backtesting engine (M3)](docs/platform/BACKTEST_ENGINE.md)
- [Python strategy SDK and indicators (M4)](docs/platform/PYTHON_SDK.md)
- [Reference margin and funding engine (M5)](docs/platform/MARGIN_ENGINE.md)
- [Authenticated backend and job queue (M6)](docs/platform/BACKEND_API.md)
- [React Strategy Studio (M7)](docs/platform/FRONTEND.md)
- [Advanced Python editor (M8)](docs/platform/PYTHON_EDITOR.md)
- [Data and result contracts](docs/platform/DATA_AND_RESULTS.md)
- [Execution security](docs/platform/SECURITY.md)
- [Milestone roadmap and migration](docs/platform/ROADMAP.md)
- [Foundation CI](https://github.com/rajkumar0rk/BTC-Analysis/actions/workflows/platform-foundation.yml)

Install and test the foundation with Python 3.11 or 3.12:

```bash
python -m pip install '.[data,api]'
python -m unittest discover -s tests/platform -v
```

M1–M4 supply validated contracts, an audited historical data engine, a trusted 1x reference backtest simulator and a streaming strategy SDK. M5 adds explicit reference margin/funding scenarios; certified venue margin and untrusted code execution remain unavailable. Existing research scripts and dashboard workflows are unchanged.

---

## Original research archive

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
## GitHub upload status (2026-10-18)

This repository has been initialized and contains the complete 5-minute source, complete reconstructed 15-minute and 30-minute OHLCV aggregates, Codex research-handoff notes, and selected research reports/results. **It is not yet a complete mirror of the original 46-file local research archive.** Some large generated CSV scans and the reusable scripts remain in the downloadable archive. The archived local file manifest is not yet published here. Do not interpret missing research tables as negative results; refer to the original archive until synchronization is completed.
