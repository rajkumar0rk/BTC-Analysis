# Step 2 — target-first and stop-first from locked fixed IST entry times (pre-run)

Decision: **PARTIAL OVERLAP — approved differential**, building on Step 1's no-stop oracle. It is diagnostic, not a novel independently profitable strategy.

## Historical and closely related experiments
- Step 1, analysis/btc_daily_opportunity_step1/NOVELTY_CHECK.md: 477 complete IST weekdays, ex-post future favorable high/low from all 24 fixed hours; no stops and no direction. 19:00–20:00 IST emerged as 2025 highest opportunity. Step 2 tests the *pre-selected* clocks with actual 1-minute stop-first ordering and fee-adjusted net profit target.
- scripts/research_every_candle_200.py, Stage6: exhaustive every-minute fixed BTC price-point first-passage, not net-percent target from locked IST hour with realistic time-based closing fee.
- scripts/research_daily_200_500_points.py: BTC 200/500 point signals and stop-first replay, not account 0.2% net target.
- scripts/research_one_trade_every_day_200.py: calendar NY trading clock signals, forced trade, not IST fixed hour with step1 cost-adjusted target levels.
- Stage7 intraday weekday/hour analysis is relevant but only fixed 200pt net target and volume/volatility strata, not price-dependent account 0.2% and eligible offer fees.

## Exact, fixed test — do not change after run
- Full 2025-01-02..2026-10-30 **477 IST Monday–Friday days** from Delta India BTCUSD authenticated continuous 1m feed.
- Anchor times **09:00, 15:00, 18:00, 19:00, 20:00, 21:00 IST**, chosen before observing stop-first outcomes (19 and 20 studied in Step 1, so their selection already has hindsight risk; other times are comparisons).
- Every anchor/day tests LONG and SHORT **separately** as counterfactuals. Never claim a real strategy can choose the better side in advance, and never add both simultaneous positions.
- Entry at exact selected minute's 1-minute OPEN, with adverse 5 price-point slippage on the entry. Stop at entry mid-price +/- 0.10%, 0.20%, 0.30%, or 0.50% opposite trade direction.
- Targets: account **NET +0.20%** at 1x notional, with *correct time dependent* fee threshold; and independent fixed price-move targets +0.35% gross, +0.50% gross (from entry MID; not account net). Only the NET0.20% target is a direct user-goal test.
- Fixed holding windows **30 minutes and 120 minutes**; exit first touch on 1-minute high/low, if stop and TP touch in same candle assume STOP FIRST, and gap-at-open stop execution pessimistic. At timeout exit at 1-minute OPEN at exactly 30m or 120m after entry, never based on future closing price.
- Cost: 0.05% taker opening fee +18% GST plus 5-point adverse slippage on each side; hypothetical regular Scalper Offer waives **closing taker fee** (including its GST) if held <=30m assuming prior activation. Any exit after 30m pays the full standard closing fee; no waiver on opening. When constructing net +0.20% target, the target price must **increase** (become harder) once position passes 30m since closing-fee waiver is lost.
- Detailed ledger for 2025-selected example only; aggregate all variants by year (2025, 2026) and across both years: first-TP counts, first-stop counts, timeouts, wins/losses after cost, daily win/goal rate, compounded account return of *one fixed side entered once every eligible weekday* at 1x notional, max closed-trade drawdown; no-trade days don't exist for these hypothetical fixed-time baselines.
- Also compute **oracle either-side first-TP reach** for each day (choose profitable long/short knowing outcome); never call this tradable.
- Selection diagnostic only: among fixed-long/short combinations choose the 2025 strongest (compounded after-cost return); show 2026 historical check *unchanged*, never validate with 2026 fitting. No leverage, no position sizing optimization. Funding (especially if overnight, though 2h max), orderbook spread/impact, liquidation omitted.
- Results answer Step 2 only. Do not introduce RSI, EMA, volume, trend or any signal filter until Steps 3–4.

## Important limitations
1-minute OHLC cannot resolve which crossed first **inside** a single 1-minute candle. Stop-first tie is conservative. Actual fills, 30-minute offer eligibility and liquidity are approximations. 2026 has been studied previously and is not pristine blind holdout.
