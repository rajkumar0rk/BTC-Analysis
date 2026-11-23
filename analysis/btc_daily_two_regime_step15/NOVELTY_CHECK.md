# Step 15 — independently causal Event / Fallback month-equity exit overlays

**Novelty classification: PARTIAL OVERLAP.** It is a constrained compositional extension of Step13/14, not a new technical indicator. In particular, Step14 reported two opposing facts: (i) one 2025-selected first-five-day profit cut improved 2025 to 11/12 but harmed 2026 to 8/10, and (ii) an after-the-fact 2026-sensitive fallback rule brought retrospective results to 20/22. Because 2026 is already research-exposed, **no claim of independent OOS validation is possible** even if both effects combine.

## Closest code and immutable baseline
- `scripts/research_btc_every_weekday_reset_step1.py`, `scripts/research_btc_every_weekday_adaptive_step2.py`: 477 full IST weekday BTC 1m futures trades and hourly volume event else 21h fallback.
- `scripts/research_btc_every_weekday_exit_protection_step3.py`, `scripts/research_btc_daily_exit_invalidation_step7.py`: exact 1m stop-first, bar-closed trailing and next-open early exits.
- `scripts/research_btc_daily_online_structure_step11.py`: strictly previous-day-only direction model.
- `scripts/research_btc_daily_monthly_exit_step13.py`: **frozen baseline** 19/22 profitable months, +23.261256% modeled net, 290/477 winning weekdays, 3.008746% max closed DD, 2025 10/12, Jan-Oct2026 9/10. Special rule: fallback only and current prior month-to-date equity return<=+0.25%, profit exit NEXT 1m OPEN if previous completed 1m CLOSE after 20 minutes is >=+0.10% gross. November 2–20 2026: negative −0.47076% vs Step11 +0.019249%; so not proven to generalize.
- `scripts/research_btc_daily_monthly_equity_step14.py`: 300 single-condition overlays; 2025-selected variant 11/12 positive months but 2026 only 8/10 and lower profit, rejected. Nine full-history hindsight-only 20/22 results, none 2025-selected with 20 months, so no validation.

## Frozen execution/economic constraints
Authentic Delta India BTCUSD 1m OHLCV Jan2025 through Oct2026. Exactly **477 IST Monday–Friday trades**, 260 full 2025 and 217 full Jan–Oct2026; one position each weekday, zero skipped days, 100% of 1× account notional per trade. No size/trade-count variation. Entry hour and side EXACT Step11: earliest 18:00/19:00/20:00 completed 5m RVOL>=1.5× last 20 completed bars, otherwise mandatory 21:00; side from frozen Step8/Step11 prior-only online directions. All baseline Step11 stop, target, 30m max, next-bar trailing and Step13 special fallback rules unchanged when no additional overlay. Entry 1m OPEN, adverse 5 BTC quote points slippage per leg, standard taker 0.05% per side +18% GST; hypothetical preactivated regular Scalper Offer closing fee zero only for eligible <=30m trades, opening charged. No real historical offer eligibility, funding, L1/L2 spread, market depth, latency or intrabar tick ordering available. When both TP and SL touch during 1m bar assume stop-first. A CLOSE-triggered exit occurs only at NEXT 1m OPEN.

## Precisely 144 event/fallback pairs, preregistered before run
Each day, BEFORE today's entry, recompute **current-month** equity, its previously observed high-water mark, consecutive losing days and number of previously completed weekdays. For today the engine separately decides which early exit option applies to its original event or fallback entry using that historical state. Today's outcome affects only TOMORROW's state. This may influence whether next day's stop/early exit is active, never creates an additional trade or skips current one.

Four EVENT activation gates × three event exit choices:
1. No event override (baseline).
2. Month-to-date net<=0%.
3. Prior monthly high-water mark>=+1.0% AND giveback>=0.50 percentage points.
4. First five trading weekdays of month.
Event exits: unchanged (no overlay), adverse early abort if a completed minute CLOSE after >=10m shows signed gross loss<=−0.08% (exit next 1m OPEN), or early +0.10% signed gross profit after >=10m (next 1m OPEN).

Four FALLBACK activation gates × three fallback exit choices:
1. No fallback override (baseline).
2. Prior monthly peak>=+1.0% and giveback>=0.50 percentage points.
3. Previous-month completed-day MTD account net >=+1.0%.
4. Peak-to-current-month equity giveback>=0.50 percentage points.
Fallback exit alternatives: unchanged frozen Step13 choice, early profit from a completed 1m CLOSE after >=10m at gross >=+0.10% next 1m OPEN, or forced exit at 20m (baseline stops still checked until 20m).

The cross-product is **4×3×4×3 = 144 fixed models**; duplicate default policies retained as audit controls, NO extra thresholds or cherry-picked month exceptions. Select arms only from state previously observed that month; state updated using current chosen exit's realized after-assumed-offer PnL only AFTER the position finishes.

## Selection, recheck, promotion
- **2025-only** 260-day 12-month selection, predeclared score: require at least **11/12 profitable months**, 2025 compounded net >=**+9.5%**, 2025 positive weekdays>=**157/260**, max closed-trade DD in 2025<=**3.05%**. Rank eligible by 2025 positive months, compounded 2025 net, 2025 win-day count, lower 2025 DD. Otherwise retain original Step13 baseline.
- Freeze selected settings and apply unchanged to Jan–Oct2026 (which is NOT independent, as it has been repeatedly inspected). For a superior historical monthly profile require **at least 20/22 positive months**, 2026 >=9/10, compounded 22-month net>=Step13 +23.261256%, max DD<=Step13 3.008746%, and all 477 trades unchanged. Report 2025/2026 profit changes and winning weekdays separately, whether improving 2026 without sacrificing either year, worst month/day, loss streak, all months and standard-fee reprice same choices.
- Publish exact baseline per-day match with Step13 both fee models, all 144 configurations×2 fee models, selected full 477 trade ledger, all 22 monthly returns, historical full-period high-score explicitly HINDSIGHT NOT SELECTED, plus counts of different exit decisions. Use ZERO data from 2026 for selecting model.
- Do NOT optimize against November 2026: this 15-day period was already inspected and is not pristine. A later fixed check is allowed as cautionary diagnostic only. Do not claim the best 22-month result is forward profitable.

## Warning
Only 22 months and huge prior search exposure. A 144-model grid can produce false positives. The biggest obstacle remains hypothetical fee waiver: Step13 standard-fee version lost −6.967115% even with 19/22 under modeled waiver.
