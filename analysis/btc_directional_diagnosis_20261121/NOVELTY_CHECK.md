# Novelty gate — separate true direction from "range" and assess BTCUSD next-4H forecasts

Decision: PARTIAL OVERLAP — APPROVED DIFFERENTIAL DIAGNOSTIC, not a new claim of alpha.

## Existing work

- scripts/research_btc_causal_predictor_20261121.py and analysis/btc_causal_predictor_20261121/RESEARCH_REPORT.md (research/btc-causal-4h-predictor-20261121): 3-class next-4H UP/RANGE/DOWN logistic regression; on nonoverlapping forward 4H samples 64.515% accuracy against 64.583% majority baseline, macro-F1 0.2655, 2 losing trades. RANGE was approximately 65% of labels, making the seemingly good top-line accuracy meaningless for direction.
- scripts/research_btc_regime_attribution_20261121.py and analysis/btc_regime_attribution_20261121/RESEARCH_REPORT.md: original 1H 8-state heuristic, 1M trade execution (four baseline systems).
- scripts/research_btc_multiregime_audit_20261121.py and analysis/btc_multiregime_audit_20261121/: label no-repainting passed; directional continuation rates weak.
- scripts/research_btc_selector_hardening_20261121.py and analysis/btc_selector_hardening_20261121/: regime selectors negative or no trade; cost stress.
- research/stage25-new-trend and codex/STRATEGY_NOVELTY_GATE.md: earlier 1H momentum studies and novelty procedure.

## Economic and prediction DIFFERENTIAL

**Fix measured failure**: stop using three-class top-line accuracy to infer future direction. Fit and evaluate binary next-four-hour close sign (UP vs DOWN) explicitly, independently estimate probability of an absolute 4H move >= 1x current ATR14. The latter is a separate event, not a majority "RANGE" prediction. Evaluate two frozen, distinct forecast model families and simple prior-only/last-four-hour-momentum baselines. Trade only predeclared sufficiently confident predictions. No parameter/grid search, no model choice based on the generated test returns.

## Pre-registered labels and timing

Native Delta India BTCUSD futures 1M SHA256 and 60s continuity validated 2025-01-01 UTC to 2026-11-20 23:59 UTC. Completed UTC 1H only. At complete 1H index t, feature values may use data through t+1h and prior only. Future 4H target: completed 1H close at t+4 minus completed 1H close at t, both scaled by ATR14 at t. Binary direction UP iff future delta >0, DOWN iff <0; exactly zero removed from binary training/score, and no forced current outcome. Move target 1 iff absolute delta >= 1 ATR14, else 0. Label only available after t+5 hours, so monthly training excludes yet-unreleased outcomes. Jan-Jun 2025 warm-up, evaluation July 2025-Oct 2026, no prior-month test fit leakage. Training expands monthly using all available completed labels before month IST start.

Causal features: EMA20 vs EMA50 / ATR; current price vs EMA20, SMA200 / ATR; ADX14, DMI difference, efficiency12, ATR/current previous72h median, Donchian24 previous channel location and breakout distance; OHLC candle body, range and upper/lower wicks / ATR; close return lags 1/2/4/8/12/24/48 / ATR; rolling 24h close-return volatility / ATR; RSI14, UTC cyclic hour-of-day, weekday cyclic. All features calculated on completed bars, no future leads. Raw close level NOT a feature.

Model A: StandardScaler + LogisticRegression(C=1.0, solver lbfgs, max_iter=500, random_state=0), fit binary direction and separately move target.
Model B: HistGradientBoostingClassifier(learning_rate=0.04, max_iter=100, max_leaf_nodes=9, min_samples_leaf=100, l2_regularization=5, max_bins=63, early_stopping=False, random_state=0), fit binary direction and separately move target. Both frozen a priori. No training on any July 2025-Oct 2026 future label before its monthly release date.

Evaluation: nonoverlapping (1H UTC index multiple of 4) 4H outcome windows, 2025 Jul-Dec vs 2026 Jan-Oct, accuracy, balanced accuracy, AUC, Brier, log-loss, high-confidence coverage, probability calibration; compare with train-only majority and immediate trailing 4H momentum sign. Scored future extreme-move-conditioned accuracy is **diagnostic** not a tradable filter. Reject any "edge" if it fails directional baseline, probability skill or after-cost trading.

Frozen trade rule applies **only Model B (nonlinear)**, to avoid ex-post model selection: completed-hour P(up)>=0.62 and P(abs move >=1ATR)>=0.35 => LONG; P(up)<=0.38 and same P(move)>=0.35 => SHORT; otherwise NO_TRADE. Use original 1M execution engine with frozen new SPEC stop 1x ATR14, TP 2R, timeout 4H, one exclusive position, next 1M open, stop-first if same-minute TP/SL, IST month-end flatten, 0.5% current-equity initial stop risk with 3x notional cap, $10,000 hypothetical starting equity. Simulated fee 0.05% each side plus GST 18% plus adverse 5 BTC points each side. Funding settlements, historical order book spreads, market impact and liquidation NOT reconstructed.

Report full monthly returns including six idle training months, entry and execution counts, missing data, prefix history audit, training audit, all scored predictions and confusion/calibration, separate model comparisons and provisional 22/22 success/failure. Hypothetical observed sample does NOT establish live performance. Historical 2026 previously examined, so chronological but NOT externally blind OOS. No post-hoc threshold changes based on performance in this run.
