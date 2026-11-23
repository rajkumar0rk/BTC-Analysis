# Step 12 — causal month-to-date recovery: improve profitable months without losing any daily trades

**Novelty decision: PARTIAL OVERLAP — approved incremental monthly objective and pre-entry regime**, NOT a new untested class of BTC signals. Previous work already optimized raw net, daily winning trades, fallback direction and static trailing stops extensively. The differentiator is **within-calendar-month causal switching based only on results of earlier completed days**, with monthly profitability as the primary objective.

## Previously executed research and reproducible baseline
- `scripts/research_btc_every_weekday_reset_step1.py`: 51,840 mandatory-trade static BTC daily models.
- `scripts/research_btc_every_weekday_adaptive_step2.py`: forced 9PM fallback when no 18/19/20 IST volume signal.
- `scripts/research_btc_every_weekday_exit_protection_step3.py`: causally next-bar-activated 1m stop/lock/trail exit designs.
- `scripts/research_btc_daily_online_direction_step6.py`: strictly earlier completed weekday arm performance.
- `scripts/research_btc_daily_causal_neighbors_step8.py`: 864 nearest-neighbor models using preentry indicators; selected 2025 model 277/477 days, 15/22 profitable months.
- `scripts/research_btc_daily_five_min_event_step9.py`: 5-minute continuous signal scanning failed.
- `scripts/research_btc_daily_structure_step10.py`: 85 static structure overrides, 2025 selection retained baseline.
- `scripts/research_btc_daily_online_structure_step11.py`: **2025-selected** 60-previous-fallback-day mean after-cost direction policy. **477/477 weekdays, 279 profitable, +22.141056% compounded account net, 3.008746% max closed-trade DD, 17/22 positive months (2025:9/12, 2026:8/10)** under hypothetical preactivated regular Scalper Offer. Exact adverse five months: Jan2025 −1.662335%; Jun2025 −0.131703%; Dec2025 −0.154829%; Jan2026 −0.564834%; May2026 −0.369659%. Negative months have different event versus fallback attribution so targeting one universal fixed exit is not the goal.
- Previous separate November 2–20, 2026 Step11 audit: 10/15 positive weekdays, +0.019249%, same as Step8. The November period is already **research-exposed**; do not use it to select new models.

## Immutable trade/instrument/execution constraints
- Delta Exchange India BTCUSD futures, genuine continuous historical 1m OHLCV, 477 complete IST weekdays 2025-01-02 through 2026-10-30 (260 in 2025; 217 in Jan–Oct 2026), no Saturday or Sunday entry, no skipped weekday, exactly one trade on each date.
- Trading timestamps remain EXACT Step11: first available 18:00/19:00/20:00 IST with 5m completed volume ratio >=1.5x previous 20 completed 5m bars; else mandatory 21:00 fallback. Both always fill at 1m OPEN. All directional choices made before trade using completed data and prior settled trading days.
- Exit rules **unchanged** from Step11: event SL0.5% gross, TP3%, 30m max with +0.10% lock after +0.25% favorable, live following 1m; fallback SL0.5% or SL0.75% according to preentry 5m vol ratio 1.25x, trail activates +0.35%, distance0.20%, TP3% and 30m cap. Assume stop-first if both TP/SL hit same 1m bar, gap-worse stop fills. No same-bar favorable-stop backfills.
- 1× daily account notional, **100% exposure per trade**, no leverage optimization or skipped entries.
- Each trade includes 5 BTC quote points adverse slippage **each leg**, 0.05% taker entry/exit + GST18%; hypothetical previously enabled regular Scalper Offer waives closing taker/GST only for <=30m hold. Standard-fee version is the SAME chosen positions repriced, not a separate directional optimization. Not based on verified historic offer activation, order book, funding, latency, margin or liquidation.

## Novel pre-registered month-to-date risk state
For every IST weekday `d`, **before** today's order:
- Determine current `YYYY-MM` and compounded **month-to-date NET ACCOUNT PnL from earlier COMPLETED actual trades under hypothetical Scalper Offer**, reset to zero at new month. Today's realized PnL **MUST NOT** affect today's direction; it only updates state for `d+1`.
- If preentry MTD return is **at or below 0.00%, −0.25%, or −0.50%** depending on variant, allow a switch to a historically better LONG/SHORT arm; otherwise execute Step11 original direction.
- Event entry base direction remains EXACT Step8 prior-neighbor/event indicator. Alternative arm is the OPPOSITE of that base direction, evaluated on previously completed EVENT days.
- Mandatory 21h fallback base arm remains EXACT Step11 prior-60-fallback-days mean-after-cost online choice among six frozen structural arms, min15 history, no margin. Alternative selection may choose among SAME six arms: Step8 baseline, Donchian120 fade1, 60m range edge follow, 60m momentum fade, SMA20/60 follow, 09:00 session VWAP fade; each arm's historical counterfactual is computable using past OHLC at completed earlier trading days. Do not introduce future price into feature formation.
- Switching method for event separately: `fixed`, `same_month_net`, `recent_net`, `recent_win`.
- Switching method for fallback separately: `fixed`, `same_month_net`, `recent_net`, `recent_win`, `recent_risk`.
- `same_month_net` scores candidate arms using ONLY previous completed **same-calendar-month, same-entry-type** daily shadow returns, requiring >=2 or >=4 such past days depending on variant. `recent_*` uses prior 20 completed same-type weekdays (regardless of month), requiring >=2/4 observations. Net score = mean after-cost net account fraction; win = fraction of profitable previous shadow trades; risk = mean return minus 0.3×downside RMS. If arm score exceeds the baseline's score by >0.0002 account return or >0.05 win fraction, replace direction, otherwise baseline. All comparisons are against today's precomputed baseline arm, not against the previous day's arm.
- On insufficient previous comparable observations or nonnegative MTD (for negative thresholds), always use the exact Step11 baseline direction. Warm start is **not tuned to January**. Selected daily orders are never rescheduled, and no second order is opened after an early exit.
- Frozen 3 MTD loss triggers × 4 event methods × 5 fallback methods × 2 minimum sample counts = **120 models**, plus the unchanged Step11 baseline. Precommitted no other thresholds, no future-informed month-specific exceptions, no changes to stops/targets/time.

## Selection and evaluation
- Primary selection **using 2025 ONLY**: maximize number of positive COMPLETE calendar months (target at least **10/12**), subject to 2025 net compounded return >= **+8.5%**, profitable 2025 weekdays >= **147/260**, and 2025 maximum closed-trade DD <= **3.05%**. Rank by monthly wins, then 2025 compounded net, 2025 winning weekdays, then lower DD. If no new model meets >=10 months and these constraints, choose *no upgrade* and report best alternatives as tradeoffs; do not lower thresholds after seeing 2026.
- Freeze chosen policy before applying to January–October 2026 (217 weekday trades). 2026 is **research-exposed historical recheck**, not independent blind out-of-sample.
- Actual promotion requires **overall** >=18/22 profitable months, total modeled net return >= Step11 +22.141056%, max DD <=3.008746%, and 2026 positive months >= Step11 8/10, plus no reduction from 477 trades. If 2026 profit declines or winning-day count declines, flag it explicitly, never pretend improvement is unqualified.
- Report 2025 and 2026 annual net/win days and DD, all 22 compounded monthly account returns (loss and zero months counted against monthly win rate), total net, max closed DD, worst day/month, PF and standard taker fee sensitivity. Also count changed event/fallback sides per year, what fraction switched on MTD loss, per-month attribution of positive/negative trades, and absolute cost effects.
- A maximum based on all 22 months may be included ONLY as a labeled **hindsight counterexample**. No selecting different policies for specific losing months after seeing those results, and no pretending 2026 is untouched. No forward paper-trading has occurred.

## Risks
This entire time span has been investigated extensively; searching 120 more policies risks serious overfitting. A month-to-date rule cannot know whether a trade will win and can worsen expectancy. Historical Scalper Offer activation cannot be deduced from 1m OHLCV; if unavailable, the same Step11 model loses −7.812987% after normal taker fees. The result is research, not a deployable strategy.
