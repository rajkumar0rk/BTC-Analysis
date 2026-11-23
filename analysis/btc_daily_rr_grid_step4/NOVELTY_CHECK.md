# Step 4 — BTCUSD multi-risk/reward experiment (pre-run novelty gate)

**Decision:** PARTIAL OVERLAP — approved differential. This changes the *exit hypothesis* of the already explored fixed-clock causal direction setups rather than discovering an unrelated entry.

## Why this is different
The user clarified that "+0.2% daily" was an **example**, not a mandated fixed take-profit. The previous Step 2 and 3 tests hard-coded a fee-adjusted +0.2% NET TP and only varied stops/timeouts. This test **removes the +0.2% target entirely** and measures whether broader static risk/reward combinations produce an after-cost edge and more profitable months.

## Closest prior work
- scripts/research_btc_daily_direction_step3.py and analysis/btc_daily_direction_step3/: 17 causal direction rules × 3 clock policies × 3 SL × 2 holding times × 2 cost models, **one fixed +0.2% NET TP**. Inconsistent/losing after cost.
- scripts/research_btc_daily_target_first_step2.py: unconditional fixed-clock long/short target-first with +0.2% net or 0.35/0.5% gross; limited risk/target matrix, no causal predictive direction ranking.
- scripts/research_every_candle_200.py and scripts/research_daily_200_500_points.py: fixed BTC price points rather than fixed **gross percentage stop × risk/reward** plus same causal direction rules and fee-timed offer model.
- scripts/research_monthly_10pct_stage19.py: event-driven 5m patterns, tested 2R/3R; not fixed 19/20 IST causal directions and 1x return.
- Strategy discovery Stage24 and Stage25 branches: 15m structure and 1h breakout family with different entries.
- scripts/research_btc_daily_opportunity_step1.py: oracle high-low price opportunity only, no trades.

## Fixed pre-registered matrix
- **Unchanged entries:** same 17 Step3 causal, prior-completed-candle direction predictions; fixed 19:00, 20:00, or 19:00 then 20:00 when 19:00 has no signal. One trade maximum per Mon–Fri IST calendar day; no trade allowed. Neither future outcome nor month labels may control entries. Reuse Step3's feature construction and predict function, unchanged.
- **Stop distance (percent of BTC mid entry price):** 0.10%, 0.20%, 0.30%, 0.50%, 0.75%, 1.00%.
- **Gross target-to-stop ratio:** 0.75R, 1R, 1.5R, 2R, 3R, 4R. Fixed TP = raw BTC entry midpoint × (1± R×stop distance); do not adjust TP to +0.2% NET.
- **Timeout:** 30m, 60m, 120m. Exit at next 1m OPEN when timed out. Stop hit if intrabar low/high touches, gap-aware fill, stop before target if both touched in same 1m candle. TP touched fills at target (no favorable gap improvement).
- **Fee model:** standard BTCUSD taker 0.05% per side + 18% GST on each charged fee. Alternate regular Scalper Offer **hypothetically previously activated**: opening taker fee+GST charged, closing fee+GST waived only if exit duration ≤30m. 5 BTCUSD quote points adverse slippage **per side** both models. Historical activation eligibility unverified. Funding, real order book impact, liquidation excluded; no leverage.
- **Investment exposure:** exactly 1x account notional, no capital amplification to force results.
- **Evaluation:** Jan 2, 2025 through Oct 30, 2026 — 477 completed IST weekdays, exact 1m source continuity required. 2025 training selection, fixed rule rechecked unchanged in 2026 (already exposed in older research, not clean out-of-sample). 22 monthly return table; wins, losses, no-trades, profit factor, max DD, worst day and worst month, net compounded account gain; days over +0.2/+0.5/+1.0% are supplementary rather than optimization goals.
- **Matrix count:** 17 direction rules ×3 entry clocks ×6 SLs ×6 rewards ×3 max holds ×2 costs = **11,016 fixed configurations**. No further tuning during this run.
- **2025-only selection:** require at least 80 trades in 2025; consider positive 2025 NET account return only; rank by number of positive 2025 months, then compounded 2025 account profit, then 2025 peak-to-trough DD. If none eligible positive, choose least-negative as diagnostic only. 2026 unchanged outcome always reported, and compare adjacent stop/reward parameter neighborhoods to spot isolated in-sample spikes.
- **No claim of robust strategy** from one historical best-of-11016: selection bias / repeated use of the 2026 archive remain severe.

## Source and safety
Current archive manifest regenerated 2026-11-23 shows full 2025-01..2026-10 1m continuous coverage, superseding outdated gate note on Oct 31. Runner verifies gaps/duplicates/nulls and excludes initial incomplete 2025-01-01 IST day. Existing historical 2026 data have already been used in optimization; not a pristine holdout.
