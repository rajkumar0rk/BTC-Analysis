# Pre-registration: weekend inventory-unwind hypothesis (BTC-first, 2026-11-19)

**Mechanism.** Crypto trading runs continuously, but traditional-market liquidity and fiat transfer rails can thin over weekends. A substantial BTC weekend move may partly reverse during Monday liquidity restoration. This is a falsifiable hypothesis, not a proven edge; no assumptions about actual dealer inventory are asserted.

**Causal signal.** Use completed BTCUSD one-minute bars. At Monday 00:00 UTC, measure Friday 00:00 UTC open to Monday 00:00 UTC open. If absolute return is at least 1.0%, trade opposite to the sign at Monday 00:00 UTC open. This is a pre-registered, fixed-threshold hypothesis, not a parameter sweep. Use a 0.45% adverse stop, 0.65% target, maximum 180 minutes, stop-first when same minute touches stop and target. Do not overlap positions. At most one trade/week. No trading on other days.

**Sizing and costs.** Model 25% account notional per position, unlevered reference equity, 0.158% round-trip fees/GST/slippage and 0.238% stressed costs; net mark-to-mid is not a true fill simulation. No compounding across trades; daily P&L is normalized to initial account equity. Funding, bid/ask and actual maker queue are not reconstructed; mark the result provisional even if positive.

**Validation.** BTC 2025 is the fixed-hypothesis research period; freeze all settings before BTC 2026 robustness check. ETH receives the same dimensionless rules as secondary validation only, and ETH results never change BTC parameters. Include every calendar day (zero-trade days too), monthly net and profit factor, worst day, drawdown and profitable/losing/no-trade counts. BTC 2026 has previously been research-exposed and is not a pristine holdout.

**Power limitation.** Only ~52 potential weekly entries/year, so this idea cannot achieve 70% profitable calendar days even if every trade wins. It can be rejected for the stated *daily-profit* goal independently of returns; it is nonetheless a distinct economic mechanism feasibility check. Reject if sparse, unprofitable or fragile. Never trade live.
