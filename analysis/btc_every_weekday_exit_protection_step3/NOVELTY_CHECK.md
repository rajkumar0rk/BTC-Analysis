# Mandatory-daily BTCUSD Step 3 — exit protection study (pre-run)

**Novelty gate:** PARTIAL OVERLAP — approved differential. Entry logic is **frozen** from earlier work; the new variable is within-trade, predeclared dynamic exit behavior, not another entry/backtest claim.

## Existing closest work
- `scripts/research_btc_every_weekday_reset_step1.py` and `analysis/btc_every_weekday_reset_step1/`: 51,840 full-weekday fixed-entry models; static stop, TP or timeout only. Best 2025-only selected fixed19 5m fade gave +1.12% 2025, −2.25% 2026, 241 winning / 477 weekdays after hypothetical Scalper Offer.
- `scripts/research_btc_every_weekday_adaptive_step2.py` and `analysis/btc_every_weekday_adaptive_step2/`: 85 full-weekday entry policies, fixed exits. The retrospectively interesting `vol5_fade__us_only__follow60` had 477 trades (219 winning days), +2.61% 2025 and +5.47% 2026 with SL 1% / TP 3% / 30 minute timeout, but is not validated due to selection on full history.
- Other `scripts/research_btc_daily_target_first_step2.py`, `research_btc_daily_rr_grid_step4.py`, and `research_one_trade_every_day_200.py`: first TP vs static SL and fixed-ratio exits, not *causal ratcheting* profit stop under the exact 477 trade adaptive signal.
- Stage19/23/24/25 exits include some ATR/trailing variants on unrelated event-driven entries; they do not establish this daily-exposure trade path's fee-adjusted protected-exit comparison.

## Strict user constraints
- Exactly **ONE trade every Monday–Friday IST**, 2025-01-02 through 2026-10-30: 477 weekdays, 260 in 2025 and 217 in 2026. Never skip a day (even if signal weak), never weekend entries, never a second daily position.
- **Freeze two entries**: `fixed19_fade5` at 19 IST; and `vol5_fade__us_only__follow60` with first pre-entry 5m volume>=1.5 at 18/19/20 IST, FADE 5m, otherwise 21 IST FOLLOW 1h. Their past-only 5m/1h signal logic must match Step2 exactly.
- Full 1min contiguous Delta India BTCUSD feed, one-minute OPEN fills, 1m OHLC stop-first if SL+TP touched same bar, gap-worse stops, favorable high/low intrabar only **updates profit protection AFTER** processing the current minute. Cannot move stop and claim filled during the bar that enabled the update.
- Entry / SL / target always in mid BTCUSD price, 5 quote-price points adverse per side. 100% account notional, 1× exposure without leverage. Standard 0.05% taker per side plus 18% GST, hypothetical regular Scalper Offer fee waiver closing leg for eligible ≤30m exits (prior activation assumed). Funding/orderbook/live fill quality excluded.

## Frozen exits
Test all two entry signals against:
- **Unchanged baselines:** fixed19: SL1%, gross TP1%, hold30; vol5_fade: SL1%, gross TP3%, hold30.
- **Static exits:** SL 0.15 / 0.30 / 0.50 / 0.75 / 1.00%; gross TP 0.25 / 0.50 / 1.00 / 2.00 / 3.00%; hard timeout 10/20/30 minutes. This grid is independent of the old RR-based setup.
- **Step profit lock:** same SL grid, gross TP 1% or 3% (ceil), 30m hold; activation price movement 0.15 / 0.25 / 0.40 / 0.60%, lock in gross 0.05 / 0.10 / 0.20% (lock must be strictly smaller than activation). When favorable excursion achieved in completed minute, raise stop to entry±lock for the **next** minute; never loosen. No activation before first completed minute.
- **Trailing stop:** SL grid and gross TP 1% or 3%, hard hold 30m; activate after completed-minute high/low favorable move of 0.20 / 0.35 / 0.50 / 0.75%; use trailing distance 0.10 / 0.20 / 0.30 / 0.50% of entry price (positive); trail from max/min favorable price seen **through completed bars**, with stop updates valid on NEXT bar only, no retroactive same-bar fills.
- **Step-up profit lock:** same 30m and SL grid, gross TP 1/3%; activation 0.20 / 0.35%, step 0.20 / 0.30%, lock 0.05 / 0.10% on activation, step lock increases by each completed favorable step, never decreases. Only valid following minute.
- For all dynamic exits, stop checked first, then TP; if neither hit, **raise stop for next minute** using price extreme in current completed minute; timeout fills at 1m open 10/20/30m (or earlier stop/TP). No auto-intrabar perfect high/low trailing.
- Test 2 entries × above frozen exit sets × two cost cases. 2025-only model choice prioritizes **positive 2025 compounded NET account return**, then highest 2025 positive-day count, then 2025 return, then lower 2025 DD. Otherwise mark the attempt as failed. Compare unchanged 2026 results; 2026 has already been extensively examined so it is NOT independent blind OOS.
- Report all 477 net daily returns and full 22-month table for selected candidates; 2025 vs 2026 winning days, account return, max closed-trade DD, worst day/month, 30m eligibility, frequency of stop vs timed exits, fee+GST and slippage. Count variants positive in both years retrospectively, but do not select them on 2026 outcomes.

## Limitations
Market data are 1-minute OHLC; actual intrabar stop/TP sequence unknown, assume stop first. Real fills, funding, liquidation, historical offer opt-in and orderbook not confirmed. Many exit variants create multiple-testing and selection bias; do not claim a durable trading edge without forward paper-trading.
