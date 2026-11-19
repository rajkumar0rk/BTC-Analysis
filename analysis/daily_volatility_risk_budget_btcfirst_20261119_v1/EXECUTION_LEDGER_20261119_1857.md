# Independent Daily-Profit Strategy Hunt — append-only execution ledger

## 2026-11-19 18:57 IST — continuation of unfinished volatility-of-volatility study
- **Decision: RETEST / PENDING EXECUTION; no profitability claim.**
- Read the preregistration and integrity-audit source on this isolated branch. Earlier status was preregistered but not backtested.
- Reused the verified archive location and schema from a previously executed independent BTC-first study: `data/delta_india/{BTCUSD,ETHUSD}/1m/20??-??.csv.gz`, Unix-second time and OHLC columns.
- Added `backtest.py` with the preregistered frozen seven-day daily-RV coefficient-of-variation gate, prior-day direction, 00:01 UTC entry, stop-first OHLC, 04:00 UTC time exit, 25% initial-equity notional, 0.158% and 0.238% modeled round-trip cost, all-calendar-day accounting, annual/monthly PF, full trades and data hashes.
- Added a branch-scoped push-triggered workflow `.github/workflows/daily-volvol-btcfirst-20261119.yml` with evidence artifact upload. Last source commit: `e84b369c349fafd0e33afca51a948d57e3c81580`.
- **Execution verification outstanding:** GitHub connector exposes workflow jobs by known run ID but does not expose workflow dispatch or a general list-runs endpoint. A workflow YAML newly introduced only on a non-default branch may not be registered/triggered by GitHub. Do not claim a run exists without a verified run ID. The next run must check Actions for this branch and, if absent, resolve branch-only trigger registration without touching main or another researcher's branch.
- **Known limitations:** modeled fees not independently validated; no executable bid/ask, settled funding, actual contract tick/lot/margin, or verified intrabar fills. Stop-first is conservative when both barriers touch, but gap fills remain an unresolved risk. The script is not independently executed or validated in this iteration.
- BTC 2025 is selection, BTC 2026 historical robustness (research exposed); ETH is frozen secondary only. No live orders, main edits, other branches or automations changed.
