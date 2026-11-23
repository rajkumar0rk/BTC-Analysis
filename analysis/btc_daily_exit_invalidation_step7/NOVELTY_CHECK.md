# BTCUSD Step 7 — prior-minute exit invalidation without sacrificing daily entries

**Novelty decision: PARTIAL OVERLAP — a new intratrade *signal invalidation after a closed 1m bar* hypothesis**, relative to prior static SL/TP, one-step lock, and trailing-profit tests.

## Why
The strongest previous **2025-selected** daily BTCUSD system (Step 6) enters exactly once each IST weekday with 2025-2026 results +17.7862% modeled net / 275 positive days / 16 positive months / 3.265838% closed DD after hypothetical Scalper Offer. But only two trades hit the oversized 3% target; 219 trades hit protective stops and 256 timed out. Potential improvement comes from abandoning a losing trade at the **next minute OPEN after a measurable prior-minute invalidation**, or preserving a winning 1m CLOSE, without future lookahead.

## Related prior studies
- `scripts/research_btc_every_weekday_reset_step1.py`: forced 477 daily entries; 51,840 static stop/TP/clock variants.
- `scripts/research_btc_every_weekday_adaptive_step2.py`: 85 first-condition adaptive daily entry policies.
- `scripts/research_btc_every_weekday_exit_protection_step3.py`: 1m bar-close activation of profit stop with static target and 30m timeout.
- `scripts/research_btc_daily_fallback_regime_step4.py` and `research_btc_daily_causal_regime_step5.py`: last preentry volume regimes and fallback stop choice; 8,064 and 26,400 models, many full-sample hindsight choices.
- `scripts/research_btc_daily_online_direction_step6.py`: genuine online preentry event-side model, no current-day data for direction, 1,152 settings. Step 6 chosen 2025-only candidate improved DD, win days and return; November 15-day audit matched E because no switch fired.
- Old 1H/15m strategy Stage19/23/24/25 trailing exits differ by event-entry and not necessarily daily.

## Fixed entries and economics
Use *exact* Step6 selected online side method: event first completed 5m volume>=1.5× previous 20 complete 5m mean at 18:00,19:00,20:00 IST, normally FADE previous 5m, but online switch to FOLLOW only when last 30 completed event days **in same |r5|>=0.15% preentry context**, at least 12, with mean Scalper after-cost shadow FOLLOW result better than FADE by >0.0003 fraction; else FADE. Mandatory no-event 21:00 IST FOLLOW previous completed 5m. **ALL 477 IST Monday–Friday 2025-01-02..2026-10-30 have one and only one trade**.
Baseline E exit: events SL0.50%, gross TP3%, 30m hold, profit stop activated at favorable +0.25%, locks +0.10%; fallback SL0.50% if previous completed 5m volume ratio <1.25 otherwise SL0.75%, gross TP3%, trailing activates at +0.35%, distance0.20%, 30m hold. Stops updated using completed 1m bar ONLY for following minute. All entries/exits use 1m trade simulations, stop-first if both TP and SL touched in same bar; gap-aware stop fills, timeouts at NEXT 1m OPEN.
Costs identical: **1× account notional**, standard taker 0.05% on each leg plus 18% GST; alternative hypothetical previously activated <=30m Scalper closing fee waiver. **5 BTC price points adverse slippage per side**, no funding, bid/ask depth, latency, margin/liquidation, or actual offer activation verification.

## Frozen novel exit-rule grid, separately for event/fallback
All exit modifications are evaluated **ONLY AFTER** base stop / TP at 1m bar, with new early-exit actions at the **NEXT minute OPEN**. Every trade may close early but cannot be skipped or rescheduled. For long/short the "signed 1m CLOSE movement" is measured relative to original entry midpoint.
- baseline 30m no extra rule.
- timed exits: max hold **10,15,20,25,30** minutes, same base stops/profit protection.
- adverse CLOSE invalidation: if last completed 1m signed close move at or below **−0.04%, −0.08%, −0.12%, −0.20%, −0.30%** at any minute after **3,5,8,10,15,20** completed minutes, exit next 1m OPEN, max hold30; only earliest cutoff applies.
- stalled trade: if MAX favorable high/low excursion so far remains below **0.05%,0.10%,0.15%,0.20%** after **5,10,15,20** completed minutes, exit next minute OPEN, max hold30.
- realized profit early: if signed completed 1m close is up at least **+0.10%, +0.15%, +0.20%, +0.30%** after **5,10,15,20** minutes, exit next minute OPEN, max hold30.
- Pairs of adverse invalidation and profit early will NOT be searched here; no within-2026 retuning.
- Total **1 + 4 unique shorter holds + 30 adverse + 16 stall + 16 early-profit = 67 base exit rules** applied separately to event vs fallback; two fee modes.
- For every rule, show event-only or fallback-only improvement versus Step6. To avoid a 67×67 full-history cherry-pick, select the **top 10 event exit rules and top 10 fallback rules by *2025 group-only* profitable days, then 2025 group sum(log(1+account return)); always include unmodified baseline**. Test these up to 121 pairs. Among them choose 2025 **positive compounded account return** and <=6% 2025 closed DD; prioritize 2025 profitable weekdays, 2025 net return, then lower DD. If none qualify, report no qualifying improvement.
- 2026 Jan–Oct is applied **UNCHANGED** and is not a pristine holdout because already researched; must report if selected model's 2026 net return, winning-day rate or DD worsens.
- Compare against exact reproduced Step6 prior baseline **275 winning weekdays, +17.7862% 1× net, 16/22 profitable months, 3.265838% DD**, standard fee net −11.101745%. Dynamic early-exit code MUST reproduce these numbers when cutoff policy baseline only.
- Publish all 67 event-only, 67 fallback-only, up to 121 combined 2025-selected candidates, 477 daily trade ledger of selected and baseline, 22 monthly returns, 2025 and 2026 separately, worst losing streak/day/month, cost assumptions. No missing trades, no skipping weekend rule exceptions, no same-bar retroactive early exit.
- Distinguish 2025-selected model from full-period hindsight. This strategy still uses a repeatedly analyzed and thus research-exposed 2026 and Nov 2026 time period; do not claim forward readiness or assume daily profits guaranteed.
