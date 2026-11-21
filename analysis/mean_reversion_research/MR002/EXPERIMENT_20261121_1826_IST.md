# MR002 execution checkpoint — 2026-11-21 18:26 IST (append-only)
- Candidate: pinned vaultik/algo-trading-system source commit 7f9bcd24d0e1cf7258699f4835ecd80dcb684a84, VWAP z-score crossback.
- Earlier run state: workflow file exists and is configured for push to this isolated branch; no completed job URL, artifacts, trade ledger or results were retrievable/verified at this checkpoint. DO NOT claim a completed backtest.
- Recovered code: scripts/research_mean_reversion_mr002_20261121.py; existing 22-month genuine Delta BTC 1m loader: scripts/research_every_candle_200.py; novelty file analysis/mean_reversion_research/MR002/NOVELTY_CHECK.md.
- Actual repair in commit 54f1c06f16807b1299df6f4c4fbaa9a97c9e94c8: pre-entry minute NAV was incorrectly filled with cash *after* entry fees. It is now marked with prior cash, before fees; removed redundant month-end lookup. No parameter tuning.
- Commit changed a path watched by .github/workflows/mean-reversion-mr002.yml, intended to trigger real 22-month Actions backtest on push. Trigger success / job completion still needs confirmation via workflow run list, logs and artifact.
- Next: inspect the most recent workflow run and job; if failed, repair the same study. If successful, retrieve artifact and verify all 22 IST monthly NAV returns, trade count, PF, drawdown, funding caveat and NAV reconciliation. Do not start another candidate until this baseline is completed.
- Data quality: existing loader checks duplicates, timestamps, OHLC bounds, gap segments. Recheck the run's real data quality JSON; no invented missing bars.
- Costs: 0.05% taker notional per side plus GST 18%, zero slippage first screen; funding unmodeled.
- No other family branch, main, VPS, or live trading touched.
