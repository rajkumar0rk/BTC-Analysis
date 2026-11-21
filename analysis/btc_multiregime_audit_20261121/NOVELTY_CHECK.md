# Novelty decision — BTC 1H market-state and causal strategy-selector audit (2026-11-21)

**Decision: PARTIAL OVERLAP — approved DIFFERENTIAL VALIDATION; no new strategy alpha or optimization.**

User goal: before any 22/22 monthly portfolio search, determine whether the existing regime classifier is causally correct and whether the system *selects strategies using only information known before their trades*. This project is audit/replay, not a parameter search. Thresholds listed below are frozen before seeing the test output.

## Existing work and overlap reviewed

- `scripts/research_btc_regime_attribution_20261121.py`, `analysis/btc_regime_attribution_20261121/RESEARCH_REPORT.md` (branch `research/btc-regime-attribution-20261121`): 8 primary 1H regimes; four standalone 1M-executed baselines, per-regime attribution. Previous hours: 47.2% mixed; four baselines had negative 22-month returns.
- `analysis/btc_shock_only_donchian_20261121/RESEARCH_REPORT.md` (branch `research/btc-shock-only-donchian-20261121`): independently replayed shock-only Donchian, +3.35% net over 22 complete months but only 10/22 profitable; shock subgroup chosen ex post.
- `analysis/institutional_discovery_stage14_monthly_regimes/RESEARCH_REPORT.md`: regime-conditioned entry rule search; 0/428 passed prior gate.
- `analysis/institutional_discovery_stage20_three_sleeve/RESEARCH_REPORT.md`: static portfolio combination, not causal regime-aware online selection.
- `analysis/independent_stage25_hourly_trend/RESEARCH_REPORT.md` (research/stage25-new-trend): hourly momentum and trend, 0/2880 all-month.
- `codex/STRATEGY_NOVELTY_GATE.md`: mandatory gate.

## Differential question, not equivalent entry family

The earlier market-state study **did not** audit history-prefix invariance, report non-overlapping forward-state diagnostics, or operate a single-account month-by-month past-trained selector where strategy choice is unknown until the month's beginning. This test adds precisely those missing correctness checks. All market features and four strategies are reused without changing their numerical thresholds.

## Classifier audit

1. Read Delta India BTCUSD original native one-minute futures bars, check SHA-256 against partition manifest and 60-second contiguity, no fabricated prices. Hours are aggregated in UTC from exactly 60 complete 1M candles. Warmup hours remain unclassified and ineligible.
2. Use original frozen completed-hour labels, **mutually exclusive by priority**: shock, breakout_up, breakout_down, trend_up, trend_down, compression, range, mixed. Verify one label per eligible hour, no disallowed label and no missing or duplicated 1H data.
3. Test past-label invariance under multiple historical prefixes (compare full-sample classifier against recomputation on truncated 1M input; final complete hours must match bit-for-bit). Pass = 0 history-revision mismatches.
4. Calculate percentages of non-actionable mixed hours and one-hour transition frequency; many mixed hours are *uncertain, not recognized reliably*. Do not claim that technical-regime labels are objective ground truth.
5. Calculate **diagnostic, NOT accuracy**: 4H forward close direction for up/down trend; after-signal volatility and future range for shock/compression, using independent non-overlapping 4-hour start times. Future prices NEVER enter a live regime label or strategy choice.

## Fixed strategy selector, all rules selected before run

At the beginning of each IST month from **2025-07** to **2026-10** (16 months), rank four frozen candidate strategies separately per regime using **only previous six complete IST months of their already-closed trades**, each from full one-strategy historical replay. January–June 2025 are training-only months; count them as idle/non-profitable if evaluating all 22 months.

Eligible strategy/regime pairs must have >=15 completed trades in prior six complete months, >=3 distinct months with trading, profit factor calculated on normalized net risk R >=1.15, mean normalized net R >0.05, and total normalized R >0 in the most recent three complete months. No eligible strategy = NO TRADE in that regime. Pick highest mean net R; tie-break highest PF then lexicographic strategy ID, chosen at month open.

The four candidate strategies and their stops, targets, timeouts, fees are **unchanged** from `scripts/research_btc_regime_attribution_20261121.py`. Each candidate's historical ledger for selecting strategies is independent; but actual selected live-like account is a **fresh single-account, exclusive-position replay**, not a concatenation of ledgers. Candidate signals on the current completed 1H must match the selected model at the monthly decision and the actually known regime. Entry next native 1M open, exits on 1M stop/target/timeout or IST month boundary; same-minute ambiguity => stop; adverse gap open. One portfolio position globally. Fixed hypothetical $10,000 initial equity, stop-risk 0.5% of current equity, maximum notional leverage 3x; modeled Delta India 0.05% taker per side + 18% GST, 5 BTC price points adverse slip per side.

## Required outputs

- `classifier_audit.json`: no-lookahead history-prefix tests, bar integrity, mutually exclusive labels, mixed share, regime stability, forward-only diagnostic.
- `selector_decisions.csv`: month/regime choice or explicit no-trade reason, sample size, normalized PF and mean net R used (NO same-month trades).
- `selected_trade_ledger.csv` and `monthly_portfolio_returns.csv`: exclusive 1M replay, all months including 6 training idle months.
- `strategy_selector_summary.json` and `RESEARCH_REPORT.md`: 22/22 pass/fail, performance, costs, drawdown, candid limitations.
- Preserve negative findings and ensure strategy selection never reads incomplete or future-month outcomes.

## Validity limits

Historical regime classification is a deterministic proxy, not ground-truth proof that BTC will continue moving in that regime. Four available strategies are not necessarily adequate to cover each regime. 2025-2026 history and especially the shock idea have already been explored, so these 16 evaluated months are **walk-forward in process but not a globally untouched external holdout**. Historical bid/ask spread, realized funding, impact, liquidation and exchange order handling are absent. Neither a 22/22 fit nor positive PF can be declared live-ready without independent prospective evaluation.
