# Backtest Explorer

A dependency-free static web client using execution-time trade audit data. No server, credentials, or order execution.

## Run
1. Settings > Pages > Build and deployment > Source: GitHub Actions.
2. Actions > Backtest dashboard > Run workflow (main). Build also runs for relevant pushes/PRs.
3. The build uploads an HTML artifact even if Pages deployment is unavailable. For local use, extract and run `python -m http.server 8000 --directory dashboard-dist`.

Local build: install pandas 2.2.3 and numpy 2.2.6; run `python scripts/test_dashboard_audit.py`, `python scripts/export_dashboard.py`, then serve dashboard-dist. Do not commit generated output.

## Scope and evidence
This is a reproduction for observability, not a new strategy experiment or optimization. Novelty decision: SKIP new research. Existing engine: scripts/research_daily_200_500_points.py; original report: analysis/delta_points_200_500/README.md. The exporter replays exactly the original historical UTC interval (2025-01-01 through 2026-10-17), preserves the signal/exit/cost logic, writes only dashboard-dist and never overwrites archived results. Instrumentation runs during actual signal generation and exit handling. Exit timestamps identify the candle, not the exact trade fill time. No funding, leverage, actual exchange fills, or account-return claim. Existing research was previously observed.

30 independent configurations, not a portfolio. Net points are price units per BTC. Daily candle shards and per-configuration monthly trade shards; only needed data fetched. No full archive in the browser. No proprietary/private data should be added to a public Pages deployment. Other historical engines are not integrated yet; do not infer their missing entry/exit reasons.
