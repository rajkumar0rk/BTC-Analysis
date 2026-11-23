# Step 25 — Net profit optimization with frozen 477 BTC weekday entries

**Novelty classification: PARTIAL OVERLAP / factorial integration.** Previous Steps 20, 22 and 24 individually examined stop caps, supervised fallback direction, and 816 direction×stop×fallback exit combinations. Step 25 combines **the exact causal Ridge 120-day fallback model** from Step22 with candidate risk and month-to-date event/fallback exits to optimize **net after modeled fee/GST/slippage**, not raw BTC points. No new signal family or independently demonstrated market edge is claimed. Prior data mining makes full-period peaks subject to heavy selection bias.

## Frozen control cases and economics
- Dataset: authentic Delta India BTCUSD futures 1m archive, exactly 477 full Asia/Kolkata MON–FRI days 2025-01-02 through 2026-10-30, 260 in 2025 and 217 in Jan–Oct2026. **One actual full 1× account-notional trade on every weekday, no skips, zero trades, size adjustments, weekend orders, or additional positions.** Entry time 18:00/19:00/20:00 IST first volume>=1.5× previous20 completed 5m bars or mandatory 21:00 fallback. Event direction unchanged, fallback side selected using original Step11 prev-day structural learner or Step22 causal Ridge model trained on only previous finished same-type days (last120, features basic, minimum40 old trades, confidence0.30). Never peek current outcome.
- **BASE Step20 B**: after-cost **+25.423847%**, 21/22 profitable months (11/12 2025,10/10 2026), 292/477 winning days, **max closed DD 2.617670%**, standard taker fee version −5.332682%.
- **Ridge Step22**: +**26.468595%**, same 21/22 months, **294/477** winning, DD2.617670%, 4 fallback side flips, full normal taker fee version **−4.544%** (exact check from Step22 reproducible grid).
- Original stops: event0.50% gross, TP3%, activate+0.10% lock after favorable+0.25% completed1m, fallback0.50%/0.75% by preentry RVOL >=1.25, activate 0.20%-distance trail on favorable+0.35%; 30m max; 1m TP/SL collision STOP FIRST, gap-worse stop fills, extra exits from previous closed 1m signal at next 1m OPEN only. Original Step20 B fallback **two original caps**: prior 60m trend aligned chosen side>=0.15% => SL min(original,0.40%), previous 5m move counter to chosen side>=0.05% => SL min(original,0.25%), recomputed for each proposed side.
- Costs: adverse **5 BTCUSD quote points per leg**, entry taker0.05% and GST18%, hypothetical previously activated regular Delta Scalper <=30m closing fee waived versus standard0.05% taker on BOTH entry and closing + GST18%. Same selected trades repriced standard vs offer, not separate model selection. Historical offer status and real spread, depth, funding, latency, margin and tick path NOT verified.

## Precommitted 672 model factorial, plus two control baselines
Exactly TWO frozen fallback-side families: original Step20 B and Step22 `ridge__120__basic__0.3__fallback` (the Ridge history learner uses only previous settled fallback cases and prior completed OHLC).
Eight additional initial-stop policies, only STOP NARROWING by preentry completed OHLCV, leaving original Step20 B two fallback caps:
1. baseline (no new cap);
2. fallback when selected side against previous60m upper/lower range edge top20% SHORT / bottom20% LONG => cap0.25%;
3. fallback against previous60m signed return >=0.15% => cap0.30%;
4. fallback preentry completed 5m RVOL >=1.25 => cap0.30%;
5. fallback preentry RVOL <=0.90 => cap0.25%;
6. fallback completed prior60m range>=0.50% => cap0.30%;
7. BOTH event+fallback completed60m range<=0.50% => cap0.40%;
8. EVENT ONLY previous5m RVOL>=1.75 => cap0.30%.
For each candidate, base caps AND additional cap evaluate on its ACTUAL selected side. SL NEVER widens.

Six event early-close policies, condition ONLY on earlier FINISHED current-month account return:
1. baseline B: when prior MTD<=0 adverse previous 1m close<=−0.08% after10min, fill next open;
2. if prior MTD<=0 adverse close<=−0.08% after5min;
3. if prior MTD<=0 adverse close<=−0.08% after15min;
4. if prior MTD<=0 adverse close<=−0.12% after10min;
5. if prior MTD>=+0.50%, profit CLOSE>=+0.15% after20min, next open (else B baseline);
6. if prior MTD>=+0.50%, hard timeout20min (else B baseline).

Seven fallback early-close policies, based ONLY on earlier completed current-month actual returns:
1. original B / Step13 logic: when prior MTD >=+1% exit profit CLOSE>=+0.10% after10min; otherwise if prior MTD<=+0.25%, exit profit>=+0.10% after20min; else normal stop/TP/30m.
2. if prior MTD<=0, exit profit>=+0.10% after10min, else original;
3. if prior MTD<=0, exit profit>=+0.10% after15min, else original;
4. if prior MTD<=0, exit profit>=+0.10% after5min, else original;
5. if prior MTD<=0, exit adverse CLOSE<=−0.08% after5min, else original;
6. if prior MTD>=+1.0%, disable extra early exit to let original stop/TP/30m run, else original;
7. if prior MTD>=+1.0%, delay extra profit CLOSE>=+0.10% to20min, else original.

**2 direction choices ×8 stop additions ×6 event exits ×7 fallback exits = 672 unique policies** (two unchanged family controls already included); with both fee schedules exactly **1,344 policy/fee results**. Each 477 actual full-size weekday positions. No post hoc extra thresholds. At every entry, direction and risk computed from earlier fully closed bars; the month-to-date exit rule is picked from prior fully COMPLETED actual trades. Today's exit outcome changes only tomorrow's month equity state. All 1m entry/exits use prior stop-first / gap conservative behavior.

## Precommitted selection and promotion
- **Select using ONLY 2025 history**: require >=11/12 strictly positive months, 2025 compounded net>=BASE original +8.882867%, 2025 positive weekdays>=original 2025 153, and 2025 closed DD<=2.617670% +0.0001 percentage points. Rank eligible by **highest 2025 NET return**, then profitable months, positive weekdays, and lower DD. Do not use Jan–Oct2026 to select rule. If no alternative qualifies, retain unchanged BASE.
- Freeze 2025-selected settings and inspect 2026 (has been previously exposed in substantial prior research so **NOT true blind OOS**). An improved all-history *monthly-preserving* profit result must have >=21/22 positive months, 2026 >=10/10, overall modeled offer net > **+26.468595%** previous strongest same-DD candidate, max DD<=2.617670%, exactly477 positions. If any dimension fails, don't claim comprehensive improvement. Standard-fee result must be stated separately, even if negative.
- Report strict 2025-selected, and separately best all-period 21+/22 monthly-profit constrained NET *HINDSIGHT ONLY*, and maximum standard-fee net, if all negative disclose. Report worst month/day, annual results, returns by each of22 complete calendar months, yearly winning days, all 1,344 rows, complete 477 daily ledgers for selected and top hindsight candidate. Provide historical regression checks for BASE/Ridge control figures and standard-fee same fills.
- No merging master / deploying live. Huge cumulative selection bias and unknown actual historical scalper offer eligibility mean even +X% historical net is not evidence of reliable live profit. No future performance guarantee. No commission rebate assumed when >30min and no leverage margin model.

This preregistration must be committed BEFORE Step25 executable code or historical result is inspected.
