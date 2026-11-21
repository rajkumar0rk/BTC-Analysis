# BTC multi-regime selector hardening (2026-11-21)

Decision: PARTIAL OVERLAP — approved causal validation differential, NOT a new alpha search.

## Older research and incremental issue
- scripts/research_btc_regime_attribution_20261121.py: eight 1H regimes, four frozen 1M-replayed strategies (all 22-month standalone returns negative).
- scripts/research_btc_multiregime_audit_20261121.py plus analysis/btc_multiregime_audit_20261121/: classifier history-prefix invariance passed; six-month moving selector made 221 trades, net -24.00%, 2 profitable months.
- scripts/research_btc_shock_only_donchian_20261121.py on branch research/btc-shock-only-donchian-20261121: shock-only Donchian made 301 trades, net +3.35%, 10/22 months positive.
- analysis/institutional_discovery_stage14_monthly_regimes/ and analysis/institutional_discovery_stage20_three_sleeve/, plus research/stage25-new-trend: regime switches and hourly strategy signals already researched.
- codex/STRATEGY_NOVELTY_GATE.md.

Differential: compare a predeclared strict statistical selector (lower-bound profitability gate), a fixed logic-based state map, prior 6-month selector with asserted parity, shock-only with asserted parity, and a no-trade benchmark on identical single-account 1M execution. Also audit yearly forward regime persistence/predictive directional uncertainty and incremental hypothetical spread sensitivities. This is diagnostic NOT threshold optimization.

## Frozen implementation

- Delta India native BTCUSD 1M archive Jan 2025–Oct 2026 complete IST months. Verify SHA, exact continuous timestamps and valid 1H aggregation.
- Regimes and candidates unchanged: eight states and four EMA pullback / Donchian breakout / Bollinger reversion / failed-break reversal models from previous scripts, signals only on completed hourly candles and fill at following minute open.
- Same initial 10,000 USD hypothetical account; stop risk 0.5% changing equity, 3x notional cap, global exclusive position, IST month-end flatten; original ATR stops, R targets and timeouts. Simulated taker fee 0.05% per side and 18% GST, adverse 5 price points each side. Native 1M bar stop-before-TP, stop gaps filled at adverse open. Historical order-book spread, realized funding, exchange margin/liquidation/rounding NOT reconstructed. FUNDING:BTCUSD hourly candles are rate observations not cash-payment ledger.
- NO_TRADE: no trades all 22 months.
- FIXED_MAP (all months): shock, breakout up/down -> Donchian; trend up/down -> EMA pullback; range -> Bollinger; compression and mixed -> no trade. No optimization.
- PRIOR_SELECTOR: load pre-existing selector_decisions.csv and replay. Must reproduce 221 trades, -24.0037% (+/-0.02).
- SHOCK_ONLY: only closed-hour shock -> Donchian, all months. Must reproduce 301 trades, +3.3469% (+/-0.02).
- STRICT_LOWER_BOUND: each new IST month starting July 2025, examine prior 6 COMPLETE months' exited trades, per regime/strategy, before current month start only. Require >=30 trades, >=4 active training months, positive sum of net R in last 3 months, and one-sided 95% conservative lower bound of mean after-cost net-R: mean(R) - 1.645 * sample_std(R) / sqrt(n) > 0. If multiple qualify, max lower bound then largest n then lexical strategy name. Otherwise NO_TRADE. Six warmup months must count as 6 non-profitable months in 22-month target. iid assumption is optimistic and noted.
- For all comparators recalculate single-account equity and one-position concurrency with 1M execution. Do not concatenate old trade ledgers.
- Incremental unobserved spread-like roundtrip cost stress: extra 0/2/5/10 basis points of entry notional, recalc each model's sequential equity and equity-proportional quantities. Costs are hypothetical, NOT observed. No parameter selection from this result.
- Hourly regime diagnostics: past-label history invariance from earlier run; one-hour persistence and 4H future direction/volatility by state and year on non-overlapping starts with Wilson 95% intervals. Label classification is technically causal but lacks externally labeled ground truth.

## Required output
New dedicated analysis/btc_selector_hardening_20261121 directory, comparison summary, all 22 months per model, selected trades and decisions, regime diagnostics, cost sensitivity, full report and reproducible workflow. Fail if parity, month-end, concurrency, no-lookahead, risk or equity reconciliation checks fail. This archive already influenced strategy ideas, so comparisons are NOT pristine independent validation; never claim guaranteed or live-ready profit.
