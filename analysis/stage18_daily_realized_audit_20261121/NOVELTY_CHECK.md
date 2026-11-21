# Incremental daily-profit audit for already backtested Stage18 70/30 (2026-11-21)

Decision: **PARTIAL OVERLAP — approved differential**, metrics-only audit of an *unchanged* strategy. Do not create a new parameter search or imply that daily realized P&L is portfolio daily marked-to-market.

## Fixed source and reason

Use the rigorously reproduced, separate 1-minute BTCUSD replay on branch `research/stage18-70-30-portfolio-implementation-20261121-v1`:

- Core: 4H/1H/15M Stage18 structural pullback with stop capped 700, 5R, 240min timeout, risk 0.5% of account per trade, core allocation 70%.
- Swing: 55-day Donchian breakout, EMA50 confirm, 2 ATR stop, 3 ATR trailing, max 30 days, 0.5% risk per trade, allocation 30%.
- Initial adverse slippage 5 BTC points/side and 0.05% taker fee per side + 18% GST. 1m stop-first replay.
- 2025-01 through 2026-10 (22 complete UTC-source months; IST first month partial opening 5h30m).
- Existing synthetic **monthly** NAV is immutable; no new strategy changes, data fitting, or new model candidate.
- `scripts/research_stage18_70_30_portfolio_20261121.py` is the exact reproducer; compare `analysis/stage18_btc_70core_30donchian_implementation/scenario_summary.csv`.

## Economic novelty

Earlier Stage18/Stage20 and the separate `analysis/one_daily_trade_200_points/` covered **monthly portfolio** outcomes and forced daily single-entry studies, respectively. Neither quantifies how often this *winning monthly* 70/30 candidate had a profitable **realized exit day**. This only measures realized-day frequency; it cannot make the underlying strategy deliver daily profit.

## Pre-registered audit

Join the original core and swing per-trade EXIT days by Asia/Kolkata, classify net positive/negative/zero exit days from the already-modeled after-cost net trade returns. Include every calendar date to count idle days. Report separate core and swing positive/negative/zero, plus an illustrative 70/30 weighted daily realized-exit proxy. Do not treat the latter as 70/30 daily portfolio NAV; the swing marks to market while open and the original portfolio only rebalances synthetically monthly. Do not sum profit on different months or hide no-trade days.

## Validity

This is previously researched data, NOT an untouched holdout. The exact historical study identified 19/22 profitable months at original cost assumptions, but this observation does not guarantee daily or future positive P&L. Actual fills, funding, mark-price liquidations, min lots, bid/ask depth and shared exchange margin remain unmodeled. All files remain on a research branch and do not modify live orders or `main`.
