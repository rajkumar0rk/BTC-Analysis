# Novelty gate: BTC 1M stop-first economic path meta-label (2026-11-21)

**Decision: PARTIAL OVERLAP — approved differential correction of target mismatch.**

The user wants reliable UP/DOWN entries, not a model that earns 55–60% future-close direction accuracy but loses when stops hit first.

## Close prior evidence
- scripts/research_btc_causal_predictor_20261121.py: unconditional 3-class future 4H UP/RANGE/DOWN; the apparent 64.5% accuracy was the dominant RANGE class and no directional profit.
- scripts/research_btc_directional_diagnosis_20261121.py: explicit unconditional binary direction, 2026 accuracy 49.62%, -32.96% account after modeled costs.
- scripts/research_btc_microstructure_directional_20261121.py: OI/mark/funding context still 2026 directional accuracy 49.34%, -33.51%.
- scripts/research_btc_event_confirmed_direction_20261121.py / analysis/btc_event_confirmed_direction_20261121/RESEARCH_REPORT.md: EVENT-side 4H future-close continuation was 58.33% on 84 nonoverlapping model-accepted samples, but independently replayed account was -27.32% net, 4/22 profitable. **This is concrete evidence that future-close direction does NOT predict intrahour stop-before-target path.**
- scripts/research_btc_regime_attribution_20261121.py: original native 1M manifest audit and conservative 1M stop-first replay.
- research/stage24-monthly10, research/stage25-new-trend, codex/STRATEGY_NOVELTY_GATE.md: earlier entry patterns; not claiming the setup rules themselves are novel.

## Incremental economic question

**Does conditioning on probability of an actual after-cost profitable exit, labeled from native 1M stop/target path at first exit completion, improve results over entering every confirmed event?**

Same exact three PREVIOUSLY COMMITTED mutually exclusive 1H events and ordered priorities from the event-confirmation run:
(1) close beyond previous complete 24H channel -> breakout in that direction;
(2) sweep-and-close-inside previous 24H -> reversal against sweep; ambiguous both-side sweeps skipped;
(3) hourly displacement body >=0.75 ATR14 with 12h efficiency >= .25 closing top/bottom 20% -> continuation.
Same side, feature vector, model families, source candles, train/test split, return assumptions, costs and all-events baseline.

## Target changed BEFORE test

For *every* eligible original event hour t, create an independent hypothetical one-time entry at next native 1M open. Stop = 1.25 * current ATR14, TP = 2R, max hold 12h or IST month end. The FIRST touched barrier is exit; if both stop and TP touched in the same native 1M minute, stop first; at stop open gap use worse minute open; otherwise exit on target or last minute close. Apply 0.05% taker fee per leg, GST 18% on fees, adverse 5 USD BTC price points on both entry and exit, exactly like the frozen replay engine. Label = 1 iff resulting net price-point P&L (and thus net R) strictly positive; else label 0. No cash/equity path or concurrent-position selection in these *isolated event outcome labels*, which are used for training only. Independent exclusive-position $10k account replay is the economic evaluation.

**CRITICAL:** event label becomes known only after the exit minute closes, never earlier; a monthly predictor only trains on event outcomes fully available before the current IST month begins (all previous months). The expensive labeling data is strictly out-of-window from each month test. Excluded future labels are not backfilled into test decisions, even if their hypothetical outcome was known by repo research afterwards.

Model A: StandardScaler + LogisticRegression(C=1,max_iter=500,lbfgs,random_state=0); Model B: HistGradientBoostingClassifier(learning_rate=.04,max_iter=100,max_leaf_nodes=9,min_samples_leaf=100,l2_regularization=5,max_bins=63,early_stopping=False,random_state=0). Both fit monthly using prior completed outcomes, from Jan-Jun 2025 initial warmup, Jul 2025-Oct 2026 chronological evaluation. **Only model B generates permitted trades**, if its P(net win) >= 0.50; otherwise abstain. No hindsight selection or optimize threshold. Compare same all-event baseline, same native 1M account fills, $10k initial, 0.5% stop risk, cap 3x notional, one global active trade per account, 22 complete IST months (first six training idle), monthly net P&L, PF, drawdown and fees.

Score whether trained P(net win) improves AUC/Brier and accepted signal net-win rate vs unconditional event net-win baseline, separately 2025 Jul-Dec and 2026 Jan-Oct on non-overlapping every-fourth-hour sample origins. Use a separate event outcome label ledger and every train date-release audit.

Data integrity: manifest SHA256 and 60-second timestamp continuity on all 992,160 native 1M candles; no fabricated 2026-10-31 data. Historical funding cash transfers, real spread/orderbook, liquidation, contract quantity rounding, queue/impact still unavailable; no live deployment allowed. 2025–2026 have been seen in previous BTC research, so these calendar splits are NOT pristine untouched blind holdout. No guarantee 22/22 and no post-result parameter changes allowed.
