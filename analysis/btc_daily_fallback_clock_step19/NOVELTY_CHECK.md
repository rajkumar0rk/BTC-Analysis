# Step19 — mandatory BTC weekday fallback entry clock sensitivity with causal decisions

**Novelty: PARTIAL OVERLAP.** The clock axis has been examined in Step1 static 24h, Step2 hourly event/fallback, Step4 21/22 choice and Step9 5-minute event scanning. The difference is **postponing an already mandatory 21:00 fallback order by a fixed few minutes based on price/volume information available at 21:00**, without changing its historical Step11 predetermined side, exiting within 30m of the actual fill, or losing any weekday trade. This cannot fix January 2025 by using calendar identity or known future profits.

## Prior evidence / immutable benchmarks
- Step13, official 2025-selected frozen baseline: **19/22 positive months, +23.261256% modeled Scalper net, 290/477 positive weekdays, max closed DD 3.008746%**.
- Step15 A, retrospectively selected based on full 22 months (NOT independent): **20/22 positive months, +24.648136% net, 292 winning weekdays, max DD2.715507%**.
- Step15 B, likewise HINDSIGHT family: **21/22 positive months (2025 11/12, 2026 10/10), +22.480405%, 293 positive weekdays, DD2.715507%**; only historical loss Jan2025 −1.450594%. Both A/B lost −0.396415% in previously inspected Nov2–20 2026 audit and lose money under standard fees.
- Step16 168 first-month-weekday stop caps, Step17 126 first-month-weekday directional overrides and Step18 540 pre-entry volume/volatility SL caps (none reached 22/22; none selected via strict 2025-only criteria). Do not use month-specific adjustments that exploit prior January loss. Historical 2026 is ALREADY research-exposed, never call it blind.

## Fixed 477-trade contract
Delta India BTCUSD futures authentic continuous 1m OHLCV January 2025–October 2026, **477 full IST Mon–Fri dates** (260 in 2025, 217 in 2026). One REAL nonzero-full-size 1× account-notional position each and every weekday, never zero skipped, never weekends, never extra trades. 
- EVENT entry remains unchanged at first qualifying 18:00/19:00/20:00 IST prior-completed-5m RVOL>=1.5× prior20 mean. EVENT direction and exit remain original Step11/Step13/Step15 exactly.
- For forced FALLBACK (no event), Step11 commits original side based solely on previously completed historical data at **21:00 IST**. At that same 21:00 checkpoint, fixed preentry indicators of preceding completed 5m volume ratio, prior60m signed price return, prior5m signed return, prior60m rolling high/low range normalized to the current price and location of last completed CLOSE, and already chosen original fallback side MAY authorize postponement. The subsequent order time is precommitted at 21:00, not chosen after seeing later bars. No later re-optimization, re-evaluation, cancellation or skipped entry even if price moves unfavorably. The SAME original LONG/SHORT signal trades at the shifted timestamp; no future price information determines the trade side.
- Shift fixed forced fallback entry from 21:00 IST by **+5, +10, +15, +20, +30, +45 or +60 minutes** (7 values), without changing its direction, original risk recipe determined at 21:00, target or stop percentage, 30-minute maximum from actual new entry time, or Step13/A/B causal month-to-date additional early-exit logic. No position is opened at 21:00 if a delayed signal was scheduled; only one trade fills at the agreed later time.
- Eight mutually predeclared eligibility conditions evaluated **at 21:00 ONLY**:
  1. `always` — every fallback.
  2. `low_vol` — RVOL5<=0.75 or<=1.00 (two thresholds).
  3. `high_vol` — RVOL5>=1.25 or>=1.75.
  4. `against_60m` — original chosen side contradicts last complete 60m move by >=0.15% or >=0.30%.
  5. `with_60m` — chosen side follows last complete 60m move by >=0.15% or >=0.30%.
  6. `wide60` — prior60m range normalized price >=0.50% or>=0.90%.
  7. `large5` — prior5m absolute return >=0.10% or >=0.20%.
  8. `range_edge` — last complete close is top/bottom20% or top/bottom10% of prior60m candle high-low.
  9. `against5` — chosen side against 5m signed move by >=0.05% or >=0.15%.
  Thus `always` has 1 setting and eight others have 2 thresholds each = **17 eligibility gates**.
- **17 × 7 fallback entry delays =119 causal clock policies**, each evaluated across 3 fixed family baselines Step13, A and B: **357 family-policy simulations +3 controls =360** and **720 cost scenarios**. Each family retains its own original Step13/A/B exit decision rule, with month-to-date equity computed only from prior COMPLETED chosen actual trades (not future close). Use the original 1m stop-first+next-bar early exit engine on OHLC of the NEW actual entry minute and 30min max. Fee model standard taker each leg0.05%+GST18% vs hypothetical previously activated regular Scalper <=30m exit fee waiver, 5 BTC quote price points adverse slippage EACH leg.
- Replay exact original Step13, A/B at zero delay to validate every individual past trading date under both fee models. Ensure all 477 IST weekday dates represented. Do not use 2026 PnL to set eligibility or select clock delay. Do not delay event entries.
- Selection **2025 ONLY, separately by family**: Step13 requires >=11/12 2025 profitable months (original 10), and 2025 account net>=+9.587865%, profitable weekdays>=157 and DD<=3.00875%. A and B require >=12/12 2025 months (original 11), 2025 profit >= respective original (+10.073418% A, +7.993545% B), weekday winning days>=155 A /154 B, DD<=2.71551%. Rank eligible by 2025 positive months, net, positive weekdays then lowest DD; if none pass, retain unchanged baseline. Report 2026 frozen settings as research-exposed historical recheck, not blind validation.
- Full-period hindsight 22/22 result (if it occurs) must be identified **IN SAMPLE / NOT SELECTED** unless the above preregistered 2025 rule independently identified the candidate. Even then, A/B original model-family identities were selected using 2026 hindsight. No claim of live profitability or consistently positive months.
- Output 720 policy/fee sensitivity rows, selected 477-trade ledger and 22 monthly results for each family, worst month/day, max closed DD, winning weekdays, relative timing/fees, count of delayed fallback dates, 2025/2026 positive month splits, time exit/SL/TP reasons.
- Previous November2–20 2026 range was already investigated and therefore cannot be considered clean independent forward paper validation.

## Data risk / economic caveats
The same 22 historical months have undergone many large searches. Further configuration searches can manufacture in-sample 22/22 with no future edge. Historical Scalper offer activation, real maker/taker executed orders, actual slippage, funding, bid/ask orderbook, latency, liquidation and tick-level within-minute order of trades are unmeasured. Full-size forced daily trading can lose entire calendar months.
