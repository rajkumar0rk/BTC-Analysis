# Backtest Explorer v2

Static GitHub Pages application. Main workflow: Backtest dashboard. GitHub Actions rebuilds after changes to analysis artifacts and dashboard inputs, or manual dispatch.

- Original execution-audited BTC experiment remains reproduced, with no changes to strategy rules.
- Explicit archive adapters cover native ETH ATR and Stage24 failed-auction where ledgers exist. The retired V7/V8, swing, big-trend and previous-day range families were removed from main. Unsupported/missing ledgers are listed. No inferred fills or reasons. Configuration-level comparisons are restricted to the same instrument and price-point units; cost assumptions differ.
- ETH native ATR engine now records modeled fills, stop/target levels, signal ATR and reasons during execution. Historical archives are not silently rewritten. The novelty gate applies to new strategy tests; this change is observability only.
- Realized P&L/drawdown is exit ordered, not account equity or mark-to-market; yearly/monthly points use entry month. Reference EMA20/50 uses displayed 1m data only. Recorded stop/trailing/liquidation levels are rendered only if present; actual dynamic trajectories are not reconstructed.
- Daily candles, monthly trade shards, bounded cache, sampled curve. Archive budget 330 MiB (split by instrument); missing/unsupported/oversize sources appear in coverage. Public Pages only: no private data.

Run locally: install pandas and numpy; python scripts/test_dashboard_audit.py; python scripts/test_dashboard_archive.py; python scripts/export_dashboard.py; python -m http.server 8000 --directory dashboard-dist.

## V3 verification and coverage
ETH ledger is downloaded from the latest successful native-ATR workflow artifact. Dashboard rebuilds on its successful completion and on a six-hour schedule. Source archive budget is split by instrument; summary-only configurations retain full metrics but omit trade shards. Research branches are cataloged, not merged or automatically replayed. CI validates generated data and exercises BTC/ETH UI in Chromium. Missing fills and actual trailing/liquidation trajectories remain unavailable unless recorded in the originating engine.

See [retired strategy index](../codex/RETIRED_STRATEGIES.md) for historical references. Market data and active research branches are unchanged.
