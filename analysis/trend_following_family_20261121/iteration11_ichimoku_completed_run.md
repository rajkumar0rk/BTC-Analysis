# TF-ICH-001 iteration 11 — completed first-screen evidence (2026-11-21)

GitHub Actions historical run: https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44914091290
Job: 136875873525, completed success; actual execution step completed success.
Artifact: https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44914091290/artifacts/14710589580 (3 files, archive SHA256 42cea3119e1e7a5089babe8983ee4098cb6b22e3d7fa155285ff9098caeb85e5).
Code HEAD: 0e833c973a34e2369ff325e84297a44c8b9110b8; input candle frame SHA256 c6d8aa094646c66b17c092fd68d49ca35d30ff1385cc2b0deb1246d8a4ed9af2.

Exact stdout summary: 28 trades, PF 1.2387453630546115, ending NAV 101.69975209984057 (starting 100 assumed by code), maximum drawdown 4.211306785463211%, six positive and six losing IST months, zero flat, 12 months. Source missing minutes reported 0. First-screen assumptions: zero slippage; fee 0.05% per executed side plus 18% GST; funding unmodeled; 0.5% initial-stop nominal risk, 1x notional cap, 2ATR research stop overlay. BTC 2025 only.

This is an independently implemented Ichimoku research variant, NOT source-faithful until original publisher rules, commit and license are verified. PF below 1.5 and only 28 trades; weak, inconclusive signal. No BTC2026/ETH selection or slippage sensitivity justified yet. Full monthly table/trade-ledger contents remain to be inspected from artifact; do not claim their independent reconciliation based solely on stdout. No live readiness.

Next: inspect actual artifact ledger/monthly NAV, verify reconciliation and stop-first path, pin original source; then reject or preserve baseline before a distinct trend-family candidate. Do not optimize 2026.
