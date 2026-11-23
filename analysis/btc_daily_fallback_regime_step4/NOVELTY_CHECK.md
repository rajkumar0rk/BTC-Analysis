# Step 4 — Fix the 9 PM daily fallback without reducing 477 trades

**Novelty gate:** PARTIAL OVERLAP (incremental conditional fallback and exits). This is NOT a novel broad price-action signal or proven profitable strategy.

## Previous research and differential hypothesis
- `scripts/research_btc_every_weekday_reset_step1.py`: exactly 477 IST weekday entries using fixed clocks; none of 51,840 models was profitable in both 2025 and 2026.
- `scripts/research_btc_every_weekday_adaptive_step2.py`: volume-reversal US-session entry with fallback 21 IST follow60. One trade/day. The full-period hindsight historical model (1% stop, 3% target, 30m) returned +8.22% with hypothetical Scalper Offer (219 winning days, 7.90% closed DD).
- `scripts/research_btc_every_weekday_exit_protection_step3.py`: same entries, 1m next-bar profit lock; model chosen using 2025 (0.50% SL, 3% TP, activate 0.25%, lock 0.10%, hold30) produced 265/477 winning weekdays, +6.79% modeled net and 6.87% closed DD. In that 477-day ledger, **260 volume-triggered days** had sum of daily net account returns +17.37 percentage points, **217 forced 21:00 fallback days** had sum −10.32. The planned experiment varies fallback-side selection and exit-by-entry-type while preserving **every entry**.
- Scripts research_btc_daily_direction_step3.py and research_every_candle_200.py examined static-time direction or fixed-point moves. This test is a precommitted limited combination of **causal 21/22 IST fallback direction with conditional exits**, not identical to those tests. Stage19/23/24/25 primarily evaluate selective trade entries and do not ensure daily coverage.

## Exact user constraints
- **Exactly 1 BTCUSD futures trade every full Monday–Friday IST day**, Jan 2 2025–Oct 30 2026 (477 distinct weekdays, 260 in 2025, 217 in Jan–Oct 2026). Never skip a weekday; never weekend entry.
- Freeze primary strategy: at 18:00, 19:00, 20:00 IST check last *completed* 5-minute volume >=1.5× preceding 20 complete 5m bars; enter immediately at the next 1m OPEN in the opposite direction from the completed last 5m price change, taking earliest signal. First event day remains exactly as the prior Step3 entry policy. If no event, MUST enter a fallback trade at **21:00 or 22:00 IST**, as fixed per variant.
- Fallback direction must be computed using strictly preceding 1m data; no future outcome, no discretionary exclusions. Frozen candidate rules (14):
  1. follow5; 2. fade5; 3. follow15; 4. fade15; 5. follow60 (old baseline); 6. fade60; 7. follow240; 8. fade240;
  9. follow15 if 15m and 60m agree, otherwise fade5;
  10. follow60 if 15m and 60m oppose, otherwise fade5;
  11. fade5 if 5m and 60m agree, otherwise follow60;
  12. follow60 if 60m return magnitude >=0.25%, else fade5;
  13. fade5 if last completed 5m volume ratio >=1.25, else follow60;
  14. fade60 when 60m range position extreme (>=0.85 or <=0.15), otherwise follow60.
- Frozen fallback clock at 21:00 or 22:00 IST (hourly checkpoint), 14*2=28 fallback policies. No other entries or rolling optimization.

## Frozen exit combinations
- Use previously verified **1-minute causal stop-first exit engine** `scripts/research_btc_every_weekday_exit_protection_step3.py` unchanged. Stops tightened only after the minute closes, never retroactively. Gap-worse stop fills, TP at target, forced timeout at max30m. No overnight exposures.
- Choose separate predefined exit recipes for event and fallback (12 in total):
  - static: SL1%/TP3%/hold30; SL0.75%/TP3%/hold30; SL0.50%/TP3%/hold30.
  - 1-step lock: SL0.50% or 0.75% or 1%/TP3%/hold30, activate +0.25% and lock +0.10%; SL0.75%/TP3% activate +0.35% lock +0.10%; SL1%/TP3% activate +0.40% lock +0.10%; SL1%/TP3% activate +0.60% lock +0.20%.
  - trailing: SL0.75%/TP3% activate +0.35%, trail distance 0.20% from best favorable after bar close.
  - stepped lock: SL0.50%/TP3%, activate +0.35%, 0.20% step, +0.10% initial lock.
  - keep 30m hold and 3% gross target for all, the original 1%/3% static and new protected 0.5%/3% locked baseline are included and asserted equal to historical net results (8.222995%, 6.786696%) to detect replay regressions.
- Matrix = 14 fallback side rules × 2 fallback clock hours × 12 event exit recipes × 12 fallback exit recipes × 2 fee schedules = **8064 configurations** (actual count asserted). Entry count per variation EXACTLY 477.
- Account notional 1× equity, no leverage. Regular taker 0.05% each side + 18% GST, adverse 5 BTC price points slippage each leg. Hypothetical eligible regular Scalper Offer waives closing taker/GST only for holding <=30m, assuming opt-in before trade (historical status unverified). Funding, bid/ask depth, exchange order latency and liquidation excluded.

## Evaluation and selection
- Primary metrics: profitable weekday count in each year, compounded net account return 2025/2026/all, max closed DD, max losing streak, 22 monthly returns and worst loss month. Compare **strictly** against 265 profitable days / +6.79% net / 6.87% DD protected baseline, and original higher-profit +8.22%/219 winning days. Require absolutely no reduction in **477 total entries**.
- **2025-only model selection** among variants with 2025 net return >0 AND 2025 closed DD <=8%; maximize 2025 profitable days, tie higher 2025 net return then lower 2025 DD. 2026 outcome is a historical robustness check but has already been researched (NOT pristine blind out-of-sample).
- Report whether any chosen candidate improves BOTH profitable-day count and total net return relative to old protected baseline while preserving 477 trades. Also report Pareto improvements across both years as **hindsight-only** (never used for 2025 selection). Dynamic exit and side-rule interactions subject to massive multiple-testing overfit.
- Include exact 477-row selected daily trades, 22-row monthly net returns, all 8064 configurations and the pre-registered rules. No further tuning on 2026 results within this run.

## Historical limitations
No tick-level order sequence; stop-first within 1m double-touch and next-bar trailing controls are conservative. Past-data 2026 already exposed; neither +6.79% nor any improvement is forward validated. No guarantee of daily profits.
