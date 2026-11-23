# Step 20 — Independent replay of overlooked Step 18 risk candidate and frozen stop-condition combinations

**Novelty gate: PARTIAL OVERLAP; audit and limited preregistered combinations only.** Earlier Step18 ran 540 volatility-based stop caps. Its official 2025-only selection rejected every change because no candidate in hindsight-selected family B made 2025 **12/12** positive months. However, examining the *published full-period candidate table* reveals a substantial **unreported Pareto improvement WITH THE SAME 21/22 monthly win count**:
- Step15 B family original: 477 trades, 21/22 positive months (2025 11/12, 2026 10/10), +22.480405% compounded 1x account return, 293 profitable weekdays, max closed DD2.715507%, worst month Jan2025 −1.450594%, worst weekday −0.824025%.
- **Step18 B / with60 / fallback / min(original SL,0.40%) / preentry previous completed 60m signed trend aligned with chosen side by ≥0.15%:** 21/22 positive months, +24.421194%, 292 positive weekdays, max DD2.617670%, worst Jan2025 −1.047101%, worst weekday −0.636900%, 117 fallback initial stops narrowed. 2025 +8.429309%, 153/260 winning days and 11/12 months; 2026 +14.748674%, 139/217 winning and 10/10 months. **Identified by searching 2025+2026 results, NOT forward validated.**
- Step18 A / tight_range60 / both / SL cap0.40% / previous completed 60m range <=0.50%: 21/22 positive months, +25.973352%, max DD2.715507%, 292 winning days, 2025 11/12, 2026 10/10, but still worst month Jan2025 −1.450594%. Also hindsight.
- Step18 B + normal taker fees remains net negative. Historical Scalper offer prior activation is hypothetically assumed, not audited.

**Rationale:** Auditing per-day 1m execution and monthly account compounding ensures candidate-row summary not hiding a mismatch. A fixed small set of simple, causal OR-composed stop masks probes whether the improvement is isolated and fragile. This does **not** erase selection bias from having seen years 2025–2026 already.

## Frozen 477-day execution contract
- BTCUSD Delta India 1m OHLCV Jan2025–Oct2026. 477 complete IST Mon–Fri weekdays, one trade EVERY day, original Step11 frozen entry clock and original chosen side, full 1× account-notional exposure, no skipped/zero-sized days or extra orders, no weekends.
- Same Step13 and Step15 A/B fallback/event month-to-date early exit logic, TP3%, event initial SL0.50% and next-bar profit lock activates0.25% locks0.10%; fallback SL0.50/0.75% by completed RVOL≥1.25, trail activation0.35% distance0.20% next-bar, 30m max hold.
- Stop first if same 1m bar hits SL/TP, gap adverse handling, 5 BTC quote-point adverse slippage each side; standard taker 0.05% per leg+GST18%; hypothetical preactivated regular Scalper fee waiver only closes eligible positions<=30m. Real fills, spread, funding, L2, margin and actual historic offer opt-in unverified.
- Every trigger uses **ONLY pre-entry fully completed 1m candles and 5m volume**; do not use current day's or future actual return to change its stop or entry.
- A stop cap uses `min(original initial SL percentage, cap)`, NEVER widens. Two simultaneously triggered caps combine as `min(original, cap1, cap2)`. All original SL/TP/trailing/next-bar early-exit state retained.

## Exactly frozen audit model list
A and B are separate earlier hindsight-selected base families. Six new B candidates and one A replay, plus two original baselines:
1. `B_baseline` unchanged.
2. `B_with60_only` — fallback & signed 60m return aligned with entry ≥0.15%, cap0.40% (from Step18).
3. `A_baseline` unchanged.
4. `A_tight60_only` — event/fallback & previous 60m high-low normalized range≤0.50%, cap0.40% (from Step18).
5. `B_with60_plus_highvol` — B_with60, plus fallback with completed5m RVOL≥1.75x prior20 cap0.25%.
6. `B_with60_plus_counter5` — B_with60, plus fallback against completed prior5m move by≥0.05% cap0.25%.
7. `B_with60_plus_rangeedge` — B_with60, plus fallback with last close high in top20% of prior60m range while SHORT or bottom20% while LONG cap0.25%.
8. `B_with60_plus_tight60` — B_with60, plus event/fallback in prior60m range≤0.50% cap0.40%.
9. `B_with60_plus_wide60` — B_with60, plus fallback with prior60m range≥0.50% cap0.25%.
10. `B_with60_plus_highvol_event` — B_with60, plus EVENT with completed5m RVOL≥1.75x cap0.30%.

These 10 model names, rules, cap values and scopes are preregistered **before execution**. Do not add other variants on seeing results. All at 1x notional and 477 real positions, both fee models. Explicitly assert original B/A complete per-day 1m parity, and exact Step18 B_with60/A_tight60 aggregate statistics as above. Publish a 477-trade daily ledger and 22 monthly results for EVERY candidate and both fee models, costs, drawdown, winning days, worst month/day and year-by-year monthly counts.

**Selection constraint:** The eight nonbaseline candidates are **hindsight exploratory** because B/A identity and stop trigger families were already selected by examining all 22 months. Do NOT promote any 22/22 or >+X% discovered here as validated. Mark any result with 22/22 as in-sample, and do not claim a genuinely independent Jan–Oct2026 holdout. To qualify under a nominal prospective 2025-only monthly screen would require **12/12 profitable months in 2025** and at least base family 2025 net and no worse DD; this is a retrospective check only, NOT full independence. Only subsequent unseen forward paper fills can validate.
