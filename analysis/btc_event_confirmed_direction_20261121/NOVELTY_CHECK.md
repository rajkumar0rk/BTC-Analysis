# BTC event-confirmed direction — novelty/validation gate (2026-11-21)

**Decision: PARTIAL OVERLAP — approved differential conditional-forecast test, NOT a new guaranteed direction oracle.**

User asks to fix failed UP/DOWN prediction. Existing BTC-Analysis research has extensively backtested breakouts, sweeps and momentum, so simply renaming patterns or shifting ATR thresholds is prohibited. This experiment tests a **different, measurable question**: after a causal 1H entry event has already established a candidate side, can a monthly past-only model decide whether that side is likely to remain correct over the NEXT 4H, and abstain when weak, instead of forcing UP/DOWN predictions on every hourly candle?

## Reviewed overlapping research

- scripts/research_btc_causal_predictor_20261121.py / analysis/btc_causal_predictor_20261121/: dominant 3-class RANGE model had ~64.5% headline classification accuracy but essentially no direction edge.
- scripts/research_btc_directional_diagnosis_20261121.py / analysis/btc_directional_diagnosis_20261121/: unconditional binary 4H direction model; 2025 Jul-Dec 55.34%, 2026 Jan-Oct 49.62%; ~-33% trading return.
- scripts/research_btc_microstructure_directional_20261121.py (branch research/btc-microstructure-directional-20261121): adding OI, funding-rate proxy and mark basis did not help out-of-sample direction, ~-33.5% trading simulation.
- scripts/research_btc_regime_attribution_20261121.py: native 1M BTCUSD data integrity, 1H features and exclusive-position 1M stop-first backtest.
- analysis/institutional_discovery_stage24_structure_monthly10/ (research/stage24-monthly10): 15M structure entry/fade signal search, 1M execution. This study **does not** claim novel break or fade patterns; it asks if a past-only probability conditional on a known event has differential value.
- analysis/independent_stage25_hourly_trend/ (research/stage25-new-trend): broad 1H momentum pattern search; distinct from explicit conditional probability evaluation and abstention with independent baseline account.
- analysis/institutional_discovery_stage14_monthly_regimes/, analysis/institutional_discovery_stage20_three_sleeve/, codex/STRATEGY_NOVELTY_GATE.md.

## Frozen, explicitly causal event rules (all complete 1H candles)

Three mutually exclusive event *families*, assigned in fixed priority:

1. **24H close breakout**: completed 1H close > previous 24 complete 1H highs => long; close < previous 24 complete lows => short.
2. **Failed 24H sweep**: completed 1H high > previous 24 highs and close back below high => short; completed low < previous 24 lows and close back above low => long. Ambiguous two-sided sweeps skipped.
3. **Displacement continuation**: absolute 1H candle body >= 0.75 ATR14, 12H directional efficiency >=0.25; bullish body closes in upper 20% of hourly candle span => long; bearish body closes in lowest 20% => short.

No signals on hourly bars failing 1H feature warmup or finite price checks. Breakout/sweep families overlap existing studies, and the research novelty is solely in conditioning on forecast of event-side success.

## Predeclared target, training and models

Event label at completed hour index t is 1 iff **event_side * (close[t+4] - close[t]) > 0**, else 0. Do not include zero or missing future observations. This is a measurable 4H event-side directional outcome, not a claim about exact stochastic market regime. Its label is released only at t+5h UTC and never included in training before release.

Event-side features: exact causal features in scripts/research_btc_directional_diagnosis_20261121.py, plus event side, one-hot family, side-adjusted EMA spread/price momentum, event candle body over ATR and past 24H channel position. No future information in model features.

At *every IST month start*, training uses ALL prior events whose 4H outcome was fully observed before month start. Initial Jan-Jun 2025 are training-only, evaluation Jul 2025–Oct 2026, all 22 complete IST calendar months shown. Fixed model A: StandardScaler + LogisticRegression(C=1, max_iter=500, lbfgs, random_state=0); fixed model B: HistGradientBoostingClassifier(learning_rate=.04,max_iter=100,max_leaf_nodes=9,min_samples_leaf=100,l2_regularization=5,max_bins=63,early_stopping=False,random_state=0). Models predict event-side 4H continuation probability. No tuning of candidates/thresholds based on output.

Precommitted trade selector is **ONLY model B and P(event-side next4H continuation)>=0.60**; else abstain. Compare all-event baseline with the same execution model, and NO_TRADE control. Do NOT reverse side based on hindsight. Report accepted-event directional hit accuracy on nonoverlapping four-hour UTC origin subsamples vs all-event side baseline, model A/B AUC, Brier and calibration, 2025/2026 splits, and all 22 monthly account returns. Overlapping hourly labels make iid confidence optimistic; no causal advantage asserted without temporal stability and independent future holdout.

## Execution for filtered and all-events comparators

Same 1H signal close -> next native 1M open; stop = 1.25 * current ATR14, target = 2R, max hold=12 hours, 1M high/low stop-first on both touched and adverse open gap; no bar-close TP assumptions. All-events comparator starts Jul 2025 to match the selected model, with six Jan-Jun training-only months idle. ONE exclusive position/account per comparator, compounded hypothetical 10,000 USD initial, risk = 0.5% changing equity stop risk, max 3x notional, IST calendar month-end flatten, assumed Delta India taker 0.05% per leg plus 18% GST and $5 per BTC price-point adverse slippage per leg. Real historical spreads, funding cash transfers, exact contract sizing, liquidation/market impact not reconstructed.

Data: original SHA256-verified BTCUSD 1M 992,160 bars 2025-01-01 through 2026-11-20 UTC and 60 complete 1M per 1H, 22 complete IST months Jan2025-Oct2026. No 1M gap or 2026-10-31 omission. 2026 *previously researched*, not a globally fresh blind holdout. Reproducible new scripts/report on independent branch; no unreported tuning after results.

**Exit criteria:** Independent account 22/22 positive after costs needed for the user's full goal, but since first six months are training-only, this research alone cannot prove 22/22. Never claim directional reliability merely from greater-than-50% accuracy: compare tradeable side-confirmation coverage, past-only baselines, yearly stability, and net expectancy. Skip if model fails; do not force trades.
