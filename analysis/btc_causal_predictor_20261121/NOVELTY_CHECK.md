# Novelty gate — fully chronological BTC next-4H market-state predictor (2026-11-21)

Decision: PARTIAL OVERLAP — approved differential directional prediction test, NOT parameter search.

## Exact prior overlap
- scripts/research_btc_regime_attribution_20261121.py and analysis/btc_regime_attribution_20261121/: causal hourly descriptive regimes and four losing baseline strategies, no direct tested forward-state probabilistic model.
- scripts/research_btc_multiregime_audit_20261121.py and analysis/btc_multiregime_audit_20261121/: causal selector lost 24%, noisy 4H conditional diagnostic.
- scripts/research_btc_selector_hardening_20261121.py and analysis/btc_selector_hardening_20261121/: conservative eligibility rejected all; intuition mapping lost 34.86%; dynamic volatility-shock Donchian earned +3.35% but with zero room for spread.
- scripts/research_independent_hourly_trend_stage25.py on branch research/stage25-new-trend: broad 1H signal search, not historical-prefix-invariant prior-month-only probabilistic three-class future state predictor.
- codex/STRATEGY_NOVELTY_GATE.md: no duplicate optimization.

## Changed hypothesis
Frozen deterministic 1H regime indicators *describe the just-closed hour*, not reliably forecast the next move; can a **past-only monthly retrained, calibrated-probability 3-class model** forecast next-four-hour direction vs no-skill baseline and yield a tradable risk/reward edge without future leakage? This is a direct reliability test of prospective regime detection; no optimizer/hyperparameter sweep is allowed. A future direction label is a measurable ex-post outcome, not a physically true market-regime ontology.

## Precommitted design

- Delta Exchange India BTCUSD native 1M, 2025-01-01 UTC to 2026-11-20 UTC, 992,160 expected bars. Verify original SHA256 and one-minute time continuity. Aggregate only exact complete UTC 1H bars; all features computed on **completed** hours; features will be known when next 1M open occurs.
- Target class at time t: 4h-ahead difference (close at completed UTC hour t+4 minus close of completed hour t) / ATR14 known at t. UP if > +1 ATR, DOWN if < -1 ATR, otherwise RANGE. Target label used for fitting only after the t+4 completed candle has closed; embargo recent 5h before each new IST month training boundary.
- Features (all strictly past-only): EMA20 vs EMA50 / ATR, close vs EMA20 / ATR, ADX14, signed DI spread, 12H efficiency ratio, ATR ratio vs prior 72H ATR median, previous-24H channel location, 1H close-open body / ATR, 1H close - prev close / ATR, 4H and 12H past close returns / ATR, hour-of-day cyclic UTC, realized 1H candle range / ATR. No OI/funding/mark data and no future price used for model inputs.
- Each complete IST month starting July 2025, fit a **new** StandardScaler + multinomial regularized logistic regression using all prior fully labeled examples with label release strictly before month start. Fixed L2 regularization C=1, max_iter=500, lbfgs, no class weighting, no tuning, deterministic random_state 0. Preserve 2025-Jan to June as initial training-only months, show them as six idle months for 22/22 goal. 2026 previously studied; test is chronological but not globally novel/blind.
- Predict each subsequent *completed* 1H bar once. Evaluate on nonoverlapping every-fourth-UTC-hour starts; compare accuracy, macro F1 and log-loss with a **month-start training-majority class baseline** and reference model training prior only. Report 2025 Jul–Dec separately from 2026 Jan–Oct, by-month and confusion matrices.
- Frozen high-confidence trade rule: trade LONG at next 1M open if P(UP)>=0.55 and P(UP)>=P(DOWN)+0.15 and P(UP)>=P(RANGE)+0.15; SHORT symmetrically for DOWN. Otherwise no trade. 1H features and probabilities fully finalized before entry. No selecting on realized label.
- Stop = 1 ATR14, target = 2x initial stop, timeout 4H. Native 1M OHLC stop-first, conservative gap rule, single account one global position, month-end IST flatten; initial $10,000 hypothetical, 0.5% stop risk each trade capped at 3x notional. Fees: taker 0.05% per side + GST 18%; assumed adverse 5 BTC points each side, hypothetical not L1 spread. Missing real historical bid/ask, settlement funding, liquidation, contract rounding and queue handling; NOT live ready.
- Required: model audit log of training max available target close UTC, complete 22-month portfolio returns, 2025 vs 2026 accuracy, baseline comparison, 1M trade ledger, data-quality report. Assert no same-month training and historical prefix validity via existing prior audit.
- No tweaks after seeing results without new signed novelty check and untouched holdout. Never imply 22/22 profitability or model truth from a 22-month post-hoc score.
