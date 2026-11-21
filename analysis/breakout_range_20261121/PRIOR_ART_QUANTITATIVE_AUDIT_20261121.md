# Breakout & Range — quantified prior-art gate, 2026-11-21 IST

Status: completed repository-based novelty audit; NO new strategy backtest run, no profitability claim.

## Verified prior work (read-only)
- Stage24 `research/stage24-monthly10:analysis/institutional_discovery_stage24_structure_monthly10/RESEARCH_REPORT.md` used genuine Delta India BTCUSD 1m, completed 15m structural breakout/retest/squeeze signals, next 1m open, 1m stop-first, 0.05% fee each side + 18% GST + $5 adverse price-point slippage each side. Tested **1,920** configurations; **zero** achieved +10% in every one of 22 months. The listed 2025 top-ranked squeeze_break 8-bar/2.5 ATR/trail3R/720m/risk2%/3x had 289 trades, 99 wins, 190 losses, +4.94% net 2025 and -26.89% net 2026, with only 5 positive 2025 months and 3 positive 2026 months. These are not zero-slippage results.
- Stage25 `research/stage25-new-trend:analysis/independent_stage25_hourly_trend/RESEARCH_REPORT.md` used completed 1H signals, next 1m open and 1m stop-first, same fees/GST and $5 adverse slippage. Tested **2,880** configurations; **zero** met the +10% all-22-month goal. Prior 1H donchian_break 12-bar/2.5 ATR/trail3R/2880m/risk2%/3x produced 391 trades (125 wins, 266 losses), -28.02% net 2025 and -24.76% net 2026. Hence basic Donchian threshold changes are duplicate research, not novel.
- Stage24 selected 2025-only candidate suffered March -7.49%, April -14.89%, December -12.88% and several 2026 negative months; claims of monthly consistency are contradicted by source reports.
- These historical reports contain known gaps: Jan 2025 IST first 5h30m missing, 2026-10-31 UTC 1,440 minutes missing; 2026 was previously inspected, funding and L2 not modeled. The reports' trade-close DD is not continuous mark-to-market DD.

## Novelty conclusions
- Generic Donchian20/55 breakout, channel breakout + EMA/ADX/volume, 15m squeeze breakout and immediate retest are **SKIP** absent a distinct causal signal. The first source audit's eight leads remain correctly rejected/blocked; do not reuse claimed publisher performance as native BTC evidence.
- A future candidate must explicitly isolate an **unexamined** range-boundary mechanism rather than merely varying lookback, stop, or trailing distance. Example *research hypothesis only, not a sourced strategy*: an objectively clock-anchored pre-break range followed by a confirmed false break and acceptance back inside the range, with a pre-committed session definition and subsequent independent confirmation. This example is **NOT APPROVED** for execution until prior failed-break branches and source rules are inspected.
- Need authentic data coverage manifest and source-faithful executable rules before a new screen. No new backtest workflow is justified by the currently inspected candidate set.

## Next run's executable decision
1. Read `research/daily-failed-breakout-20261119` and `research/daily-compression-breakout-20261119` implementations and compare exact causal signals to any newly discovered external candidate.
2. Confirm Delta 1m archive path and coverage, timestamp convention, October missing-day caveat and warmup.
3. Choose a source-complete novel candidate; commit deterministic `NOVELTY_CHECK.md` with NEW/PARTIAL APPROVED verdict before launching an isolated GitHub Actions screen. If none passes, continue external discovery rather than relabeling generic Donchian.
4. Only report native BTC returns after a completed Actions job and preserved ledger. Funding stays UNMODELED.

No other branches, automations, VPS, live trading, or main changed.
