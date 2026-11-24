# Step30 — fallback-specific loss memory gating recovery (BTC January 2025, no month special cases)

**Novelty gate: PARTIAL OVERLAP / new gate variable.** Existing Step29 investigated 1,200 combined previous-total-calendar-month loss, preentry fallback direction, fallback stop and early-close rules. **0/1,200 reached 22/22**, and 3 made Jan2025 slightly positive but hurt 4–9 other months; their losing-month state was too blunt because it responded to total monthly account equity (including profitable event trades). Step30 instead uses **ONLY previous COMPLETED 21:00 FALLBACK position outcomes in the current IST month** to detect whether that specific entry engine has recently been losing, then changes ONLY subsequent FALLBACK trades. Event entries remain exactly original Step28 (plus its independent overall-month high-water guard). This state differs materially from Step29's combined event/fallback calendar MTD net. Still observational data-mining, NOT a new predictive strategy.

## Correct Jan and baseline
- January **2025** (not January2026) loss under fully verified Step28 +28.574051% net model is **−1.047101% compounded**, 22/22 weekday orders: 14 volume events 9 winning, +0.631713 percentage points sum; eight forced fallback entries 3 winning, **−1.672284pp** sum, with four fallback losers about−0.47% each.
- January2026 already profitable **+0.910871918%** and is not a failure month. Original Step28 has **21/22 profitable months (2025 11/12, 2026 10/10), +28.574051% hypothetical net, 281/477 winning weekdays, closed DD2.617670%, 2025+11.982383%, Jan–Oct2026+14.816320%** and standard taker net−2.954186%.
- All 477 complete IST Mon–Fri dates Jan2025–Oct2026, one FULL 1× account-notional BTCUSD futures trade EVERY weekday, no skipping, no weekend, no extra positions, no size/down leverage. Frozen event clock18/19/20h at first prior completed5m RVOL>=1.5×previous20 5m bars, else 21h fallback. Frozen original Step11 event side and Step22 Ridge fallback side last120 previous completed fallback shadow outcomes, min40 samples, threshold0.30. Step28 calendar-month peak guard retained: prior completed *total* monthly account peak≥+1.0%, previous finished equity gave back≥0.75 percentage points; if so initial SL cap0.18% and guarded event lock activation+0.30% lock+0.15%, fallback trail activation+0.35% trailing0.15%. Otherwise original event SL0.50% with lock after+0.25% at+0.10%, fallback SL0.50 or0.75% by completed5m RVOL with trail at+0.35% dist0.20%, plus the Step20 B+Step25 preentry SL caps. Gross TP3%, 30m max, 1m stop-first and next-OPEN confirmed 1m early exit. All entry direction/exit recipes are ex ante.
- Cost hypotheses: 5 BTC quote-price-point adverse slippage each leg, entry taker0.05%+GST18%, hypothetical PREACTIVATED <=30m regular Delta Scalper closing-fee waiver; standard taker charged both sides+GST18%. Same trade actions repriced both; real historical exchange waiver, spread/market depth/latency/funding, liquidation unknown.

## EXACT preregistered 1200 fallback-only combinations
At each FALLBACK order, use ONLY prior COMPLETED FALLBACK trades in SAME calendar IST month to derive a fallback-loss flag, reset histories on month start; never use any current trade result or future candle. Eight alternative flags, each requiring >=1 earlier fallback:
1. `last_fallback_lost`: immediately previous fallback net account return negative;
2. `last_fallback_lost025`: immediately previous fallback net account return<=−0.25%;
3. `last_two_fallback_losses`: last two fallback trades both negative;
4. `last_two_fallback_sum_negative025`: sum of last two fallback trade account returns<=−0.25%;
5. `two_of_last_three_fallback_losses`: at least two of up to previous three (require >=3 fallback trades) negative;
6. `fallback_month_cumulative_negative`: compounded net of ONLY prior fallback positions this month<0%;
7. `fallback_month_cumulative_below025`: compounded only fallback net<=−0.25%;
8. `fallback_month_cumulative_below050`: compounded only fallback net<=−0.50%.

If triggered, select one of **five** preentry direction options, only for that fallback:
- `keep_ridge` exactly original (control in grid);
- `invert_high_rvol` flip Ridge direction iff last CLOSED 5m RVOL>=1.25;
- `invert_always` reverse Ridge regardless of RVOL;
- `follow60` if abs prior completed60m signed return>=0.15%, use sign(return), else Ridge;
- `fade5` if abs prior completed5m signed return>=0.05%, use opposite sign(return), else Ridge.
At actual entry recompute original Step20/25 stop masks for that chosen side.

Apply one extra INITIAL STOP cap to this FALLBACK only if that fallback-loss condition is true, min(existing SL, cap) with one of **0.15%,0.20%,0.25%,0.30%,0.35%** (five), never widen. Event stops/side unchanged from frozen Step28.

When flagged, replace only that FALLBACK's optional extra close with one of six:
- `base` unchanged Step25 previous-account-month early-close logic (profit-close +0.10% after20min iff prior total month account<=+0.25%, otherwise none),
- `profit010_after5`,
- `profit010_after10`,
- `adverse008_after5`,
- `adverse008_after10`,
- `timeout20`. All closed 1m triggers, execute next OPEN, stop-first for SL/TP, no conditional signals from unclosed current bar.
**8 fallback loss gates×5 fallback side choices×5 protective stop caps×6 fallback early exits=1,200 models, plus unchanged Step28 baseline, both fee cases =2,402 scenario results.** Absolutely no threshold additions after results.

## Selection: don't confuse training January with independent validation
- Select on **2025 ONLY** and REQUIRE 12/12 positive 2025 calendar months, positive-month improvement from 11/12, 2025 compounded net >=+11.982383%, 2025 winning weekdays>=154, 2025 max closed DD <=2.617670%+0.0001pp. If no candidate meets these, keep Step28 unchanged, regardless of retrospective January-only improvements.
- Freeze selected configuration for the 217 Jan–Oct2026 trading dates (2026 repeatedly studied, NOT independent blind OOS). Complete historical target would have 22/22 positive months, +28.574051% full net or more, DD<=2.617670%, every weekday full1x position. Any 22/22 result from ranking whole history or just Jan2025 is HINDSIGHT diagnostics, not proven edge.
- Save full 2402 results, exact baseline and 2025-selected and highest January hindsight complete 477 daily + 22 month ledgers and fees, monthly/2025/2026 totals, number of alternatives with Jan2025>0 and 12/12 2025, number of total22/22; compare standard fees and don't claim live profitability. Never merge master or deploy orders.

## Bias warning
We are explicitly observing January2025's failure and repeatedly running large searches. A perfect-looking 22/22 model can be severe multiple-testing artifact. Actual Scalper waiver, bid/ask, stop crossing at tick path, funding, latency, liquidation unverified; the historical fee assumption is necessary for any positive net to date.
