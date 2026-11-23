# Step 11 — prior-trading-day-only structural fallback selector (mandatory 477 weekdays)

**Novelty: PARTIAL OVERLAP — approved differential on an existing entry family.** New part is strictly chronological policy switching among predeclared structural direction overlays, not a new EMA/Donchian signal or independently validated profit claim.

## Prior coverage, limitations and exact difference
- `scripts/research_btc_every_weekday_reset_step1.py`: static forced daily entries, and no robust winner in a much larger search.
- `scripts/research_btc_daily_online_direction_step6.py`: 1,152 prior-day-only mean-return direction policies with volume/impulse binary context.
- `scripts/research_btc_daily_causal_neighbors_step8.py`: 864 prior-day-only multidimensional nearest-neighbor direction policies; **2025-selected Step8** = 477 trades, 277 winning, +21.423313% modeled Scalper net, 15/22 positive months, 3.008746% max closed DD, but 2026 unchanged from Step6.
- `scripts/research_btc_daily_five_min_event_step9.py`: checking high volume every 5m rather than only 18/19/20 IST failed—all 384 models net negative in 2025.
- `scripts/research_btc_daily_structure_step10.py`: 85 fixed intraday structure overlays; the 2025-only selection retained the Step8 baseline. An after-the-fact Donchian120 fade fallback at price breakout >0.1% performed better in 2026 but made 2025 worse, so is NOT validated.
- `scripts/research_btc_daily_exit_invalidation_step7.py`: more win days but much lower net or failure on November audit; Step11 keeps exits unchanged.

**Different hypothesis:** Instead of adopting any structurally switched strategy based on its 2026 returns, learn daily whether the baseline or a candidate rule has performed better during the **most recent completed fallback days**, with a conservative threshold. The rule selected for today's trade may never consume today's or any future outcome. Each rule must still enter one position for every IST weekday.

## Frozen entries and costs
- Delta India BTCUSD authentic continuous 1min OHLCV, Jan2025–Oct2026, **477 full IST Monday–Friday days** between Jan 2 2025 and Oct 30 2026, no weekends. Event entry is unchanged first 18/19/20 IST 5m volume>1.5x prior20 complete 5m mean, and event direction is EXACT existing Step8 preentry/online selection. When no event, exactly one mandatory 21:00 IST fallback trade.
- Every candidate keeps identical entry timestamps, position count, stop/TP/trailing/candle ordering and 1x account notional/100% exposure. Event exit: SL0.5% gross, TP3% gross, lock+0.10% after +0.25% profit, max30m. Fallback: SL0.5% or 0.75% if preentry 5m volume>=1.25x, 0.35% trail activation, distance0.20%, max30m, same TP3%. Stops only move on NEXT 1m candle after confirmed closed-bar favorable move; stop-first on both-hit candle, gap-aware stop fill.
- Costs 0.05% taker each side + 18% GST. Hypothetical previously activated regular Scalper Offer closes eligible BTCUSD futures positions for free within 30m, but opening fee charged; 5 BTC price-point adverse slippage per leg. Future real trading cannot guarantee historical offer opt-in/fills; no orderbook/latency/funding/liquidation model.

## Exactly predeclared 6 direction arms, FALLBACK ONLY
Each arm has exactly one trade on every day, with default Step8 for volume-event days. Fallback direction changes only if current completed prior-minute candles satisfy a deterministic structural condition; otherwise retain original Step8 chosen direction:
1. `baseline`: keep Step8 direction.
2. `donchian120_fade1`: if completed preentry last-close exceeds the prior 120m HIGH (excluding most recent 5m) by >0.10% enter SHORT, or below the prior 120m LOW by >0.10% enter LONG. Else baseline. *This arm was examined by hindsight in Step10; do NOT describe it as unseen.*
3. `edge60_follow0`: if current close lies in top20% of previous 60m range enter LONG; in bottom20% enter SHORT; else baseline.
4. `momentum60_fade1`: if prior completed 60m return magnitude>=0.4%, enter contrary to that return; else baseline.
5. `sma20v60_follow0`: if preceding 20 completed 1m closes' average differs from 60 completed 1m closes' average by at least 0.03%, follow the gap sign; else baseline.
6. `vwap0900_fade0`: if last complete 1m close >/+0.15% above 09:00 IST-session anchored trade-volume-weighted VWAP, SHORT; if below/-0.15%, LONG; else baseline.
All data are known BEFORE 21:00 OPEN. No future highs/closes or scenario outcome access.

## Adaptive meta-strategy, frozen parameter grid
- Each day when fallback is required, look at the last 30 / 60 / 90 COMPLETED previous fallback trading days; consider those days' *counterfactual settled trade returns under all fixed arms*, computed using the previous actual OHLC. Minimum 15 prior fallback days to switch, else baseline.
- Choose among 2 arms `baseline + Donchian` or all 6 predeclared arms; tie-break baseline. Rank by (a) mean net account fraction, (b) profitable-day frequency, or (c) mean net minus 0.3× downside deviation. Baseline preference margin either zero or **+0.0003 net account fraction / +5 percentage points profitable-day fraction**.
- **3 windows ×2 arm pools ×3 scores ×2 preferences = 36 models**, each 477 trades. Historical shadow returns for arm alternatives NEVER form a live order; only one chosen arm order taken each day. At day index d, allowable source days are strictly <d.
- Model selection uses **2025 ONLY** and same Step8 2025 constraints: >=147 2025 profitable weekdays, net >=+8.10265%, max 2025 closed DD <=3.00875%. If no new candidate passes, select previous baseline. Rank qualified variants by 2025 winning days, 2025 return, then 2025 DD. Freeze and report 2026 unchanged—not an independent blind period, it was researched repeatedly.
- Report each year's returns and winning days, the number of forced 21h fallbacks 117 in 2025 and 100 in 2026, 22 monthly account compounded returns, worst day/month, max loss streak, closed DD, PF, fees, and exact 477 daily trading ledger. Compare Step8 and Step6. Report if new policy improves BOTH annual winning days and return without DD or months deterioration.
- **No post-2026 selection or threshold change.** Best all-history model if shown is hindsight-only, not a recommendation. November 2026 was inspected in several earlier studies and cannot be called pristine forward data.

This is historical research only; cannot imply daily profit or safe deployment. Live market fees/spreads/fills and separate forward paper trading are required.
