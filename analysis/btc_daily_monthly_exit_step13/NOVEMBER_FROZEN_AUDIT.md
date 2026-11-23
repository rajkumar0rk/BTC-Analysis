# Frozen Step13 monthly-recovery November 2026 audit — preregistered

**Policy chosen using 2025 ONLY, frozen before inspecting November**: Step11 unchanged mandatory 477-day entry-side selection and 1m exits; Step13 adds a rule ONLY on forced 21:00 IST fallback days if current IST calendar month's **previously completed** traded account return, compounded from earlier weekdays under the hypothetical preactivated Scalper Offer, is **at or below +0.25%** before entry. The optional close triggers if after 20 completed 1m candles signed previous 1m CLOSE is at least +0.10% gross from entry mid price, then executes next 1m OPEN (after regular SL/TP and prior-bar trailing have been processed). Otherwise retain original trailing stop and 30min timeout. Never reduce trade count or notional.

## Historical result and selection rule
Step11 original: 17/22 positive months, +22.141056% total net, 279/477 winning weekdays, max closed-trade DD 3.008746%.
Step13 2025-selected + Jan-Oct2026 recheck: **19/22 positive months, 290/477 winning, +23.261256% net, 3.008746% DD**, with assumed offer+GST and 5 BTC price points adverse slippage per leg; 2025 10/12 positive months and 2026 Jan–Oct 9/10. Its earlier five negative months fell to three: Jan2025, Jun2025, Jan2026.
Standard taker fee model: **−6.967115%** total net and only 6/22 positive months despite the improvement, so the hypothesized offer waiver remains critical.

## Later chronological audit — frozen 15 weekdays
November 2–20, 2026 are the only 15 complete Mon–Fri IST dates to audit in this check. The original Step11 previous November audit measured exactly 15 trades, 10 positive, +0.019249% compounded assumed-offer net and −0.860928% standard. This November range was ALREADY examined for other policies; **not a pristine blind holdout**.
- Choose original Step11 event/fallback direction causally using only PRIOR completed 2025–Oct2026 and earlier November days' **shadow returns from original fixed exits**; no new Step13-specific side fitting or retuning. Previous Step11 November audit found no actual side differences from Step8 baseline; assert original Step11 Nov PnL parity.
- Every Nov weekday enters exactly one 1m-open position, event first eligible 18/19/20 IST or 21h forced fallback. Original event SL0.5%/lock+0.10% after +0.25%; fallback trail SL0.5% or 0.75% by 5m volume>=1.25, activation +0.35%, distance0.20%, TP3%, 30m max, next-1m stops, stop-first same bar.
- For new Step13 actual exits, November MTD monthly return starts at 0 on Nov1/2, and changes only after completing each actual position. For standard-fee sensitivity, **use identical chosen exits as hypothetical offer regime**, only recalculate net fees; no using the standard-fee outputs to select exits.
- Include modeled 0.05% taker per leg+18% GST, hypothetical prior activated regular Scalper <=30m exit closing waiver, 5 BTC quote price points adverse slippage each leg. Position notional 1× account, no leverage/risk scaling, none of the 15 days skipped.
- Publish all 15 trades for both strategies and fee scenarios; total net, profitable days, winning month outcome Nov sample, max DD, worst day, count of early exit signals, fees. Do not modify the Step13 trigger based on the audit. Mark results as a short research-exposed chronology extension, not live proof.

Past research and strategy novelty documented in `analysis/btc_daily_monthly_exit_step13/NOVELTY_CHECK.md`.
