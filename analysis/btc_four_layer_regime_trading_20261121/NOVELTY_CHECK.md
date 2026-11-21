# BTC 4-layer multi-regime executable research audit — 2026-11-21

**NOVELTY DECISION: PARTIAL OVERLAP — approved differential architecture/integration experiment, not a new entry pattern or optimization.**

## Closest prior work and what changes

- `scripts/research_btc_mtf_market_structure_audit_20261121.py`, `analysis/btc_mtf_market_structure_audit_20261121/RESEARCH_REPORT.md`: market detector recognizes current completed 1H + last closed 4H structures, 58.034% mixed, 12.44% confirmed trends, 0 historical revision errors. NO strategy entries or orders tested from its classifications.
- `scripts/research_btc_regime_attribution_20261121.py`: four existing 1H signal families, native 1M conservative execution; baselines losing. Use its unchanged 1H EMA pullback, 24H Donchian break, Bollinger reversion signals, NOT pretend they are newly invented.
- `scripts/research_btc_multiregime_audit_20261121.py`: six-month historical-positive 1H regime selector (−24%); standalone case does not do MTF regime + conditional eligible strategy + subsequent independent 15M confirmation + common 1M global account.
- `scripts/research_btc_selector_hardening_20261121.py`: fixed 1H map (−34.86%), strict selector no trades. Neither compared future 15M verification with a separate 1M fill.
- `analysis/institutional_discovery_stage13_4h_1h_15m/`, `analysis/institutional_discovery_stage24_structure_monthly10/` on `research/stage24-monthly10`, and `analysis/independent_stage25_hourly_trend/` on `research/stage25-new-trend`: similar MTF signal, pullback and breakout family already researched; we DO NOT present the rules as novel alpha. Economic differential is causal modular *integration plus ablation* (same eligible signal immediate vs first subsequent 15M confirm) with an exclusive account and full audit.
- `codex/STRATEGY_NOVELTY_GATE.md`: mandatory novelty pre-registration. Previous Stage24/25 missing-Oct-31 warning was superseded by verified newer SHA256 full 1M manifest; independently recheck.

## Four separate immutable layers (no optimization in this experiment)

1. **Market observation**: use the exact completed 1H + completed-4H `mtf.classify(one)` labels. Last closed 4H candle must satisfy `available4_utc <= decision_close_utc`. Keep MIXED_UNCERTAIN / TRANSITION / COMPRESSION explicitly named, do NOT force a trade. Additional independent 4H bias and 1H bias stored.
2. **Eligible strategy + side at 1H close, all thresholds fixed in advance**:
   - `confirmed_trend_up` / `confirmed_trend_down`: EMA20 reclaim/pullback signal from frozen `base.prepare_signals`, only in aligned trend side. Strategy `trend_pullback`.
   - `shock`: 24H Donchian close breakout from frozen base, ONLY if 4H trend bias agrees with breakout side (nonzero). Strategy `shock_breakout`.
   - `breakout_up` / `breakout_down`: 24H Donchian close breakout from frozen base matching state direction, and 4H bias not opposite (zero or agreeing). Strategy `structured_breakout`.
   - `range`: frozen 1H BB20/2 return-from-band mean reversion, only if 4H trend bias is neutral. Strategy `range_fade`.
   - `mixed_uncertain`, `compression`, `transition`, and invalid warmup: NO_TRADE. No model guessing future direction, no retrospectively optimized mapping.
   - Signal family priority is mutually exclusive because one current state per 1H. Store every candidate decision and rejection reason.
3. **Independent short-term entry confirmation**, no hourly OHLC peeking: for every eligible closed 1H signal at `t`, examine the **first NEW complete** UTC 15M candle beginning at the next 1H boundary (`signal_close=t+1h`). That bar is unknown until `t+1h+15m`. Long requires its close>open, short close<open; plus trend: close on favorable side of frozen hourly EMA20; breakout: close beyond previous 24 complete hourly channel boundary; range fade: close on favorable side of original signal 1H close. The possible actual entry is next native 1M open at `t+1h+15m`, NEVER the confirming candle's open or hypothetical intrabar fill. If confirmation fails, skip; do not chase subsequent bars.
4. **Independent 1M exit/execution**, no forced regime re-label exit: 1.6 ATR stop/2.5R target/24h timeout for trend; 1.8 ATR stop/3R target/36h for shock & structured breakouts; 1.2 ATR stop/1.5R target/12h for range. ATR fixed from closed 1H signal; risk 0.5% of current $10,000-initial account, cap 3× notional, one position globally, each model independent equity path, no overlapping positions. Gap-through stop uses adverse open; if both TP and SL reached same 1M bar exit STOP. Exit IST month-end; no fee-free magic liquidation. Assume taker 0.05% each leg plus 18% GST and $5 BTCUSD price-point adverse slippage each leg. Historical bid/ask spreads, actual funding transfers, depth, contract rounding, margin/liquidation unknown. Do NOT claim fully live-realistic.

## Locked comparators

- `no_trade` — zero trade account.
- `ungated_immediate` — fixed raw all-1H frozen signal families with deterministic priority: Donchian then EMA pullback then Bollinger reversion; next 1M open; no MTF state eligibility.
- `regime_eligible_immediate` — same regime eligibility in layer 2, enter next 1M open, no layer-3 confirmation.
- `four_layer_15m_confirmed` — exact layer 2 + layer 3 + layer 4 described above.

All comparators share **same stop/target/timeout per family**, global exclusive position, fees and risk assumptions; differences are state eligibility and 15M confirmation only. All four get separate $10,000 hypothetical accounts and all 22 COMPLETE IST months Jan 2025–Oct 2026, including no-trade months as failed positives. No training or threshold search in the run.

## Validation acceptance and outputs

- SHA256 native-1M and continuity, complete 60/15/240 underlying intervals.
- Every order's state/regime, 1H completion, completed-4H availability, subsequent 15M confirmation finish and next-1M entry; no lookahead, no trade concurrency.
- Historical-prefix invariance on at least 3 cutoffs, reuse `mtf.past_recomputation` and reject if any state revision.
- `decision_audit.csv` full all-1H state/eligible/confirmation flags, rejection reasons, timestamp.
- `trade_ledger_<comparator>.csv`, `monthly_account_returns.csv`, `comparison_summary.csv`, `yearly_returns.csv`, `execution_quality.json`, `RESEARCH_REPORT.md`.
- Reconcile trade PnL, costs and monthly returns to final compounded equity.
- Distinguish classification correctness (past-only) from predictive edge and net trading profitability.
- Evaluate positive months **22/22**, not just total return; no optimizing after seeing results, no strategy promotion to live. 2025–2026 have been repeatedly inspected and thus are not a pristine independent holdout.

This is an integrated **research** backtest on branch `research/btc-four-layer-regime-trading-20261121`, not a production deployment or merge.