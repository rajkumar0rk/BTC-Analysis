# Novelty check — Shock-only Donchian account replay

**Decision:** PARTIAL OVERLAP — approved differential diagnostic, not a genuinely new alpha hypothesis.

## Prior evidence and selection bias

- `analysis/btc_regime_attribution_20261121/RESEARCH_REPORT.md` on `research/btc-regime-attribution-20261121`: full 1H regime census and four separately replayed strategies. The unfiltered Donchian baseline had 573 trades and -13.23% net account return; the **subset of its 233 trades classified as `shock`** had profit factor 1.13 and 14 positive / 8 negative months in conditional subgroup sums. **That subset was not an independently executed strategy.**
- `scripts/research_btc_regime_attribution_20261121.py`: source of frozen 1H indicator definitions, priority-based shock regime, signal generation, and 1M fills.
- `analysis/institutional_discovery_stage14_monthly_regimes/RESEARCH_REPORT.md`: earlier broader regime-based tests, 0/428 passed.
- `analysis/independent_stage25_hourly_trend/RESEARCH_REPORT.md` on `research/stage25-new-trend`: earlier 1H momentum/trend search.
- `analysis/institutional_discovery_stage24_structure_monthly10/RESEARCH_REPORT.md` on `research/stage24-monthly10`: earlier 15M structure search.
- `codex/STRATEGY_NOVELTY_GATE.md`: mandatory gate.

**Economic differential:** Restrict permitted entries to `shock` hours and replay the filtered signal sequence *from scratch*, with independent one-position-at-a-time handling, independent floating account equity, position sizing, fees, slippage, time exit and IST month-end exit. This can (and likely will) give a different trade list and dollar returns than summing the original strategy's shock-tagged trades. Rules and parameters are **not** optimized.

## Fully frozen signal and execution rules

- Source: Delta India BTCUSD perpetual futures native 1M files, 2025-01-01 UTC through 2026-11-20 UTC. Read native manifest, verify SHA-256, completeness and no timestamp gaps. Use complete IST months Jan 2025 through Oct 2026; exclude partial Nov 2026.
- Hourly signal only at **completed** 1H candle close; 1M open of the following hour as earliest possible entry.
- Long when closed 1H close > highest high of previous 24 **complete** 1H candles; short when close < previous 24 complete 1H lowest low. Do not enter if both triggered simultaneously.
- `shock` gate: use **same precommitted** hourly classifier and precedence as source script: `1H TrueRange > 2.2 * ATR14` **OR** `ATR14 / prior 72H median ATR14 >= 1.8`. All features computed only with candles closed at entry decision.
- Stop loss initial distance: `1.8 * ATR14` from unadjusted entry 1M open, TP `3 * initial stop distance`, timeout 36 hours. Bar-by-bar native 1M high/low; conservative stop when stop and target in same minute; adverse stop-gap open fill.
- One trade maximum at a time. Entry first minute after signal. No new position while prior one remains open. IST month-end flatten.
- Hypothetical account $10,000 initial, 0.5% of current account equity initial stop-risk per trade, maximum 3x notional; equity rolls across months and is **not reset monthly**.
- Assumed taker 0.05% fee each side; 18% GST on fees; 5 USD BTCUSD price-point adverse slippage per leg. **Funding, real spread, order book impact, liquidity and liquidation NOT modeled**.
- Publish: per-month net account percentage, trades/wins/losses/idle, gross and modeled cost breakdown, max trade-close equity drawdown, yearly and 22-month returns, profit factor, trade ledger. Include original unfiltered baseline for comparability.

## Validation / expectation management

This gate is an **ex-post trade filter chosen because the same 2025–2026 sample showed a promising shock-tagged subgroup**. It is not an independent holdout; 2026 was previously researched. A positive filtered result does not prove future profitability. An independent later period and prospective paper trading, with true trading costs, remain required. No 10% monthly or all-positive-month assertion is permitted without actual account-level proof. October 31, 2026 was missing in older Stage24/25 runs; the newer 2026-11-21 1M manifest reports zero gaps and must be checked on read.
