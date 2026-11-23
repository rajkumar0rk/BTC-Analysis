# Step 24 — preregistered 816 multi-axis combinations for BTC monthly consistency

**Novelty gate: PARTIAL OVERLAP, permitted exploratory research.** Prior Steps 1–23 have already investigated daily signals, initial-stop caps, monthly exits, timing and supervised entries separately. Step24's differential is a **fixed factorial combination** of causal fallback direction + preentry protective stop + previous-day-month-state early exit. This is not independently discovered alpha and may overfit because the same 22 months were extensively searched.

## Benchmarks and trade constraints (IMMUTABLE)
- Delta India BTCUSD futures 1m OHLCV, **477 full IST Monday-Friday dates Jan 2 2025–Oct 30 2026**, 260 in 2025 and 217 in Jan–Oct 2026, **exactly one full-size 1× notional position EVERY weekday**, no weekends, skips, size reductions or additional orders.
- Base is the verified Step20 `B_with60_plus_counter5` rule: **21/22 profitable months**, **+25.423847% compounded 1× net**, **292/477 winning days**, max closed DD **2.617670%**, January 2025 (only losing month) approximately −1.047101%. Model found retrospectively and NOT independently validated. Its standard-fee version **−5.332682%**.
- Keep frozen Step11 trade timestamp: 18/19/20 IST event at first qualifying 5m volume >=1.5× 20 previous 5m bars, else mandatory 21 IST fallback. Keep original Step11 event side unchanged for all 816 variants. Fallback side may change using only preentry completed candles. 1m OPEN fill, 5 BTC quote points adverse slip each side.
- Base SL: event 0.5% mid, lock +0.10% after +0.25% favorable from next closed minute. Fallback SL0.5% or 0.75% by previous 5m RVOL>=1.25, activate trailing after favorable +0.35%, distance0.20%, from following minute. Fallback Step20 original caps when side agrees with previous 60m move >=0.15% (SL ≤0.40%) and when side opposes previous 5m move >=0.05% (SL≤0.25%). **These two caps are recalculated against the actual proposed candidate side**; never reuse original-side stop caps for a reversed trade. All have target3% gross, 30m maximum, 1m stop-first on TP/SL collision, worse-on-gap stop fill, early close signaled only at previously completed 1m CLOSE and filled NEXT minute OPEN.
- Step15 B causal baseline early exits: if prior current-month realized equity<=0 on EVENT, adverse close<=−0.08% after10 completed minutes -> exit at next 1m OPEN. FALLBACK if current-month account return previously>=+1% then profit close>=+0.10% after10m, else if prior month return<=+0.25% then profit close +0.10% after20m, else original 30m. PnL for this state is from previously finished actual hypothetical-offer trades in same IST calendar month; resets each month.
- Cost models: 0.05% taker entry+GST18%, and a **hypothetical previously activated Delta regular Scalper Offer** waiving eligible <=30m exit fee; STANDARD comparison adds 0.05% taker exit+GST18%. 5 BTCUSD quote-point adverse slippage per side. All standard-fee results apply to EXACT same selected trades, not a separately optimized strategy. Real offer eligibility, orderbook spreads, latency, funding, liquidation, margin, intra-minute trade order unverified.

## EXACT fixed 17 fallback-direction rules (preentry only)
Changes only mandatory 21 IST fallback side, never event side or entry timestamp:
1. original Step11 direction.
2. fade previous 5m signed return if abs>=0.05%.
3. follow previous 5m if abs>=0.05%.
4. fade previous 60m if abs>=0.15%.
5. follow previous 60m if abs>=0.15%.
6. fade previous 240m if abs>=0.35%.
7. follow previous 240m if abs>=0.35%.
8. fade prior60m range edges upper/lower 20%.
9. follow prior60m range edges upper/lower 20%.
10. fade previous complete 120m Donchian break by >=0.10%, excluding last5m from channel.
11. follow 120m Donchian break by >=0.10%, excluding last5m.
12. fade prior SMA20 vs SMA60 gap >=0.03%.
13. follow prior SMA20 vs SMA60 gap >=0.03%.
14. invert previous fallback side if preentry 5m RVOL>=1.25.
15. invert side if preentry 5m RVOL<=0.90.
16. fade if previous 60m completed-close zscore>=1.0 abs relative to preceding 60m close levels.
17. fade deviation from 09:00 IST session VWAP if abs gap>=0.15%.
If a rule's threshold does not trigger, keep the ORIGINAL side. Every day still enters.

## EXACT 6 additional SL regimes
All cap only an existing stop and never widen:
1. Baseline Step20 B stop.
2. FALLBACK 5m volume ratio<=0.90 -> SL cap0.25%.
3. FALLBACK 5m volume ratio>=1.25 -> SL cap0.30%.
4. FALLBACK chosen entry side against prior 60m signed return by >=0.15% -> SL cap0.30%.
5. FALLBACK previous 60m range / preentry price >=0.50% -> SL cap0.30%.
6. FALLBACK side against previous60m range-edge when close top20% with SHORT or bottom20% with LONG -> SL cap0.25%.
When multiple caps apply, combine as min(original, historical Step20 caps, new cap) at entry.

## EXACT 8 previous-completed-month-state fallback exit regimes
No change to original EVENT early exit. Only FALLBACK can replace its Step15 B early-close choice, based exclusively on earlier settled month PnL / prior losing streak:
1. original Step15 B, unchanged.
2. if prior current-month equity return<=0, use previous completed 1m CLOSE profit>=+0.10% after10m -> next minute OPEN.
3. if prior month return<=0, profit>=+0.10% after15m -> next OPEN.
4. if prior month return<=0, adverse CLOSE<=−0.08% after5m -> next OPEN.
5. if prior month return<=0, hard timeout20m (but still stop first).
6. if prior month return<=0, stall if maximum favorable excursion<0.10% after10m -> next OPEN.
7. if previous two completed daily trades in same month were losses, adverse CLOSE<=−0.08% after10m -> next OPEN.
8. if previous two daily losses AND prior MTD<=0, profit>=+0.10% after5m -> next OPEN.

**17 directions ×6 SL choices ×8 exit choices =816 candidates, plus frozen original control, 817 strategies ×2 cost assumptions =1,634 reported results.** All must have 477 real positions. Stop and direction inputs formed before each entry; exits never use future bars to choose them. Direction and extra SL masks are settled at entry, not changed after seeing current trade price outcome; month-dependent exit choice uses earlier completed daily trades only.

## Frozen selection and reporting
- Select only from **2025 260-day, 12-month historical portion**: qualify only if 2025 has **12/12 strictly profitable months** (baseline 11/12), net 2025 compounded >= baseline, 2025 positive weekdays >= baseline, 2025 max closed DD no higher than baseline+0.0001%. Rank qualified by 2025 monthly wins, 2025 net, winning days, lower DD. If none qualify return exact original unchanged.
- Freeze the 2025-selected rule, then report Jan–Oct 2026 without selecting on 2026. 2026 is **research-exposed**, NOT independent OOS. True promotion goal 22/22 months AND total net>=+25.423847% AND DD<=2.617670% with 477 full-size trades; anything else a tradeoff, not completed goal.
- Print count of all full-history 22/22 strategies separately as **HINDSIGHT ONLY**, not automatically promote them. Also present monthly Pareto with most profitable months, best net at 21/22, worst-month severity, 2025 and 2026 splits, and standard fee sensitivity. Published artifact: every model summary, 22 monthly outcomes for selected and a few informative full-history alternatives, 477 daily trade ledger selected, exact parity of baseline to Step20 B. No other variants, thresholds or month-special-case modifications after outcomes.
- Serious false discovery / overfit risk from extensive prior mining of all 22 months. Even 22/22 in retrospect does NOT justify live trading. Real exchange offer, fills, spread, funding and latency are not validated; use forward paper trading with verified costs before deployment. No master merge.
