# Trend-family turnover failure postmortem — 2026-11-23 15:00 IST

Status: **POST-REPLAY COST DIAGNOSIS; NO NEW BACKTEST**. Isolated trend-family research only.

## Verified evidence
- Authentic Delta India BTC2025 1m replay: https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/45131335895 (completed SUCCESS, SHA 371e2917f93817ecd7aa7a05ba39b6cf70d720b3).
- Original output artifact: https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/45131335895/artifacts/14797817980 .
- Original Kali-Uga source anchor: period 263, scale 0.01, completed 5m signal, continuous notional exposure rebalancing. Publisher NQ research is not BTC evidence.
- Reported BTC2025 replay: starting NAV $100, ending NAV $29.08, net return -70.92%, max DD 70.93%, 0/12 positive months, 104366 orders, $75.01 modeled fees+GST. Zero assumed slippage; funding unmodeled.

## Cost arithmetic (diagnostic, NOT independently rerun)
- Assumed fee per executed side 0.05% notional + 18% GST = **0.059%** of executed notional.
- Implied aggregate transacted notional from $75.01 cost = **$127,135.59**, provided every execution incurred exactly this rate. This is an inference, not an independent ledger sum.
- Implied mean notional change per order = **$1.21816** across 104366 orders.
- If the reported account P&L and fees reconcile additively, gross pre-fee dollar P&L = **+$4.09**, compared with **-$70.92** net. This is a diagnostic identity, NOT an independently verified trade-ledger gross result; cashflows/rounding must be checked against artifact.
- With zero assumed slippage already, simply reducing slippage cannot rescue this baseline. Fee sensitivity is dominant; no justification to run more favorable execution assumptions.
- Rebalancing a continuous target every completed 5m bar can accumulate enormous turnover even when directional forecast has a small positive gross edge. Future candidates must have an economically explicit trade-frequency/holding-period mechanism; arbitrary deadbands on this rejected baseline are parameter retuning, not a new strategy.

## Novelty / next-candidate gates
1. **Time-filtered trend persistence with a source-defined long holding period and volatility-managed exposure**: check against TSMOM 30/90-day components and their failed 2026 recheck; reject if equivalent. No invented parameters.
2. **Source-defined trend persistence estimator (e.g. causal Hurst/efficiency gate) with trailing exits**: requires exact source code, license, source commit, full entry/exit rules and proof it differs from Stage25/Stage13 and prior trend acceleration. Indicator-only repositories are not strategies.
3. **Chandelier or ATR trailing persistence**: reject ordinary EMA/SuperTrend + ATR exit as already tested unless a published distinct regime mechanism is recovered.

## Research integrity
No new strategy implemented, no new historical job launched, no new P&L verified in this audit. Do not count a postmortem as a baseline or a fix. Next execution must be a DIFFERENT source-faithful low-turnover strategy, predeclared novelty, archived original source and actual authentic 1m historical workflow, then completed artifact reconciliation. BTC2026 is research-exposed and October 2026 has a documented 1440-minute gap. Do not change other families or deploy.
