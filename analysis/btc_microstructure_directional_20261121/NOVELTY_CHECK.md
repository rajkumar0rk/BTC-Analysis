# Novelty gate — BTCUSD OI / mark-basis / funding RATE features for directional forecast

Decision: PARTIAL OVERLAP — approved DIFFERENTIAL RESEARCH, not a new or untested market regime invention.

## Prior work

- scripts/research_btc_causal_predictor_20261121.py: prior 3-class majority-RANGE model, 64.515% accuracy vs 64.583% prior baseline, no useful direction.
- scripts/research_btc_directional_diagnosis_20261121.py and analysis/btc_directional_diagnosis_20261121/RESEARCH_REPORT.md: explicit binary future-4H UP/DOWN classifier with 1H OHLC-only features; nonoverlapping 2025H2 direction accuracy 55.344% and 2026 direction accuracy 49.616%; pooled 51.776%, after-cost trade result -32.96%. Separate expansion classifier (absolute next 4H >= ATR14) AUC 0.6649 pooled.
- scripts/collect_delta_institutional_data.py and data/delta_india/BTCUSD/institutional/history_manifest.json: MARK BTCUSD 1M (basis indicator, NOT tradeable bid/ask), OI BTCUSD 5M (OI proxy), FUNDING BTCUSD 1H (observed rate series, NOT settled cash payments); separate live snapshots are not historical books.
- scripts/analyze_institutional_regimes.py and analysis/institutional_regime_research/: OI/funding/mark proxies previously studied in conjunction with structure strategies; no claim those input categories are novel by themselves.
- research/stage25-new-trend, codex/STRATEGY_NOVELTY_GATE.md: existing hourly strategy and no-duplicate gate.

## Hypothesis and difference

Use time-aligned exchange-native **OI, mark/perpetual basis, and funding-rate observations at the just-completed 1H bar close** to test if adding genuine position/mark-proxy information increases next-4H **binary direction** skill and market-expansion skill over a frozen otherwise identical OHLC-only model. Do NOT use the result to cherry-pick model/parameters or trade retroactively. Evaluate whole 2025H2 and 2026 chronological blocks with identical thresholds and models; report weakness honestly.

## Frozen study design

- Parent script price-only directional predictor retained unchanged on earlier branch, all features/labels, train-only monthly fitting and 1M execution rules preserved.
- New script copies frozen parent script, adds 1H-complete indicator columns only from exchange native MARK:BTCUSD 1m, OI:BTCUSD 5m, FUNDING:BTCUSD 1h archives. Validate each native series timestamp continuity and per-1H count, avoid future-timestamp row and incomplete candle; no ffill of missing OI/funding/mark. Data is historically available until 2026-11-17, through Oct 2026.
- At 1H hour t, mark close from the minute candle t+59m, OI close from 5M t+55m, and funding rate from hour t (known after hour ends). Features at hour index t: futures-mark basis in bps, change in basis over previous 1H/4H, mark 4H momentum /ATR14, 1H/4H/24H OI percent changes, OI1H change x futures past1H return /ATR14, funding current rate (in raw API units), 8H average funding, 8H funding change, funding times past OI change. If any raw bar missing, exclude affected hours, never fill forward to fake real time data. Data are observations, not proof of executed positions or funding cash transfer.
- Same prediction target: future four completed hour close movement UP versus DOWN binary; separate abs future move >= 1 ATR14, label release t+5H.
- Same two predeclared models exactly: StandardScaler LogisticRegression(C=1,solver=lbfgs,max_iter=500,random_state=0), HistGradientBoostingClassifier(learning_rate=.04,max_iter=100,max_leaf_nodes=9,min_samples_leaf=100,l2_regularization=5,max_bins=63,early_stopping=False,random_state=0). Fit models separately each month beginning 2025-07 through 2026-10, with only released pre-month labels.
- Same nonoverlapping UTC 4H score, probability calibration, directional accuracy, AUC, Brier/log-loss, expansion AUC, and previous 4H momentum / past training-only majority benchmark. Compare BOTH overall and year-specific performance with price-only report. No grid-search or parameter selection.
- Same trade-only nonlinear model forecast: P(up)>=.62 AND P(expansion)>=.35 LONG, P(up)<=.38 AND P(expansion)>=.35 SHORT; 1 ATR stop, 2R target, 4H timeout, single exclusive position, next native 1M open, stop before TP in same 1M, monthly IST flatten, hypothetical $10,000 initial, 0.5% current-equity stop risk, max 3x notional, assumed taker fee .05%/side plus 18% GST and adverse five price points/side.
- Complete 22 IST month report (6 initial training-only idle months), quality and trade ledger, comparing against exact price-only results without refitting them to 2026.
- Funding paid/received is NOT modeled from rate candles. Real spread, orderbook, queue, liquidation and contract rounding unavailable. Ex-post research on prior seen data is NOT blind independent holdout. No live promotion, no 22/22 guarantee.

No further threshold tuning on these 22 months is authorized by this diagnostic.
