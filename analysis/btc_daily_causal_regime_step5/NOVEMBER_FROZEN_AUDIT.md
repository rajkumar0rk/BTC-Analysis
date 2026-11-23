# Freeze C, D, E before November follow-on check

This is a later chronological audit only, **not** independent discovery. The 15 November weekdays and outcomes for earlier baselines had already been examined in prior studies; no selection using this new audit is permitted.

All 477-day historical grid values for 2025-01-02 to 2026-10-30 are model outputs and have severe best-of-26,400 bias. The following four unchanged variants must be audited, whether the result is positive or negative:

| Model | Entry | Event exit | 21h forced fallback direction | Fallback exit | Preentry regime | Historical 2025-Oct2026 |
|---|---|---|---|---|---|---|
| B previous baseline | volume5 fade at first 18/19/20 >1.5x, else 21h | lock SL0.50 TP3 activate0.25 lock0.10 | follow completed prior5m | trail SL0.50 TP3 activate0.35 distance0.20 | none | 271 winning days, +15.522477%, 16/22 profitable months, 6.70682% DD |
| C | same | lock SL0.75 TP3 activate0.25 lock0.10 | follow5 | LOW: trail SL0.50; HIGH: trail SL0.75, both activate0.35 distance0.20 | HIGH iff preceding completed 5m volume / preceding 20x5m volume >=1.25 at entry | 276 winning days, +16.849616%, 14/22 profitable months, 6.530684% DD |
| D | same | lock SL0.50 TP3 activate0.25 lock0.10 | follow5 | LOW: trail SL0.50 activate0.35 distance0.20; HIGH: lock SL0.75 activate0.25 lock0.10 | same 1.25 volume | 275 winning, +16.230389%, 15/22 months, 6.291612% DD |
| E | same | lock SL0.50 TP3 activate0.25 lock0.10 | follow5 | LOW: trail SL0.50; HIGH: trail SL0.75, both activate0.35 distance0.20 | same 1.25 volume | 273 winning, +17.215989%, 15/22 months, 5.737444% DD |

Every exit capped at 30 minutes, stop-first if both 1m levels touch, trailing updates only next 1m, 5 BTC price points adverse slippage per leg, 0.05% taker+GST on opening, closing fee waived **only hypothetically** on pre-activated regular Scalper Offer if <=30m. Also report standard fees. Account notional 1×, no leverage.

**Future-period sample:** exactly 15 complete IST Mon–Fri dates November 2–20, 2026, each independently entered once. Do NOT skip loss days or tune the setup. The November OHLC file spans through Nov 22 UTC and is complete for these dates. Short 15-day check is not a forward live paper-trade test. No funding, real bid-ask spreads, orderbook depth or actual offer activation verified.

Selection decision: do not pick November's best variant post hoc. Present all four equally and retain November as a warning/confirmation only. Historical 2026 remains research-exposed.
