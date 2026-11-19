# Novelty gate: risk-guarded fixed $10 per trade replay

Decision: PARTIAL OVERLAP, approved incremental execution-safety comparison. Original full history in `analysis/btc_ema_st_fixed_10_margin_20261119/` already tested the exact 15m signal with $100 account, fixed $10 isolated margin, 100x and optimistic/pessimistic liquidation fills.

This run changes **only one entry guard** to represent the VPS forward runner: skip if the 2xATR14 initial stop is farther than `1/100 - 0.0025 maintenance - 0.0025 extra buffer` (0.5% of entry). All other entry, exit, 15m intrabar OHLC assumption, 100x position size, fees, and funding assumptions remain identical to prior replay. Therefore this is a risk-control ablation, NOT a new strategy search, and must be compared with original results.

Limitations: uses traded 15m OHLC price as a **proxy** for liquidation, not Delta mark price; does not reproduce REST trailing updates, actual order book fills or historical Scalper Offer entitlement. A zero modeled liquidation count does not guarantee zero live liquidations. No chronological holdout is created; the entire period has been research-exposed. Never promote results as expected live returns. Original strategy parity remains unvalidated.
