# Trend family experiment ledger — append only

## 2026-11-21 — TF-ICH-001 — launched, awaiting GitHub execution

- Candidate: 4H causal Ichimoku TK cross with 9/26/52/26 cloud and 26-period historical close confirmation, from https://github.com/sakshamverma2030/Algorithmic-Trading-Framework-in-Crypto-Python
- Original published implementation has NOT been copied. Source commit and license still need pinning; this is an independently written first-screen approximation, NOT yet certified source-faithful reproduction.
- Novelty: cloud displacement plus TK crossover and Chikou past-price filter is materially different from Stage13 EMA pullback and Stage17 Donchian. Compare source-level against Stage25 before treating as qualifying.
- Hypothesis: confirmation of multi-week directional persistence can offset frequent whipsaw losses. Disproof: negative BTC2025 fee-inclusive expectancy or too few trades.
- Execution: closed 4H bar at timestamp t, next eligible 1m open t; 2ATR initial stop is an independently disclosed risk overlay, not a claim about source's original stop.
- First-screen costs: 0 slippage; 0.05% notional fee each side and 18% GST; no funding data; capped 1x notional, 0.5% initial-stop risk.
- BTC2025 only. Workflow: .github/workflows/trend-family-ichimoku-screen.yml. Script: scripts/trend_family_ichimoku_first_screen.py.
- Script commit: 0a06063f50c2f2e60cdf5a55ffc92c07db103863; workflow commit eb46fed06fee802dd85a9f77f1a84ca5c22055c6.
- Status: workflow committed; no registered GitHub run observed immediately after push. DO NOT report profit or completed historical test until run/job/artifact verified.
- Next: verify workflow registration, repair any failure, pin source commit/license, audit output NAV reconciliation, archive source/data hashes and freeze baseline before 2026/ETH.
