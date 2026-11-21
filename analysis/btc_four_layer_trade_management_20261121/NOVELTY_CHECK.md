# BTC four-layer position management differential (2026-11-21)

**NOVELTY GATE: PARTIAL OVERLAP — permitted isolated exit-management ablation, NOT discovery of an unrelated new strategy.**

## Relevant earlier work

- `scripts/research_btc_four_layer_regime_trading_20261121.py`: completed 1H/4H regime → frozen eligible strategy → first subsequent 15M closed-candle confirmation → native 1M conservative stop-first execution; original -22.1561%, 9/22 months profitable.
- `scripts/research_btc_four_layer_past_only_edge_20261121.py` and `analysis/btc_four_layer_past_only_edge_20261121/RESEARCH_REPORT.md`: 6-month past-only shadow-trade evidence filter +3.9621% (55 trades), 12-month past-only shadow-trade evidence filter +8.9446% (51 trades), 7/22 positive months each; 12m model trades only Jan–Oct 2026. Prior model costs include taker 0.05% per leg plus 18% GST, and BTC 5-price-point slippage each side. The 12m filtered account's occasional large Donchian breakouts compensate losers, motivating an *exit-only* study.
- `analysis/btc_four_layer_past_only_edge_20261121/RELEASE_VALIDATION.md`: all 264 monthly decisions verified as past-only; simulated extra 2–10 bps cost sensitivity and no-go for live trading.
- Previous trading-research projects have explored ATR trailing and breakeven controls; no novelty asserted for those stop methods themselves.
- `codex/STRATEGY_NOVELTY_GATE.md` prohibits duplicate optimization: this is a small, frozen comparison of trade-management mechanisms without any parameter sweep or cherry-picked selection.

## Frozen experiment

**The market classifier, candidate entry, eligibility and 15M confirmation never change.** Reuse pre-existing historical 6m and 12m monthly eligibility decision files, verify them against prior evidence and the exact 1M baseline. For each predeclared model, take the full original list of 513 15M-confirmed events, filter by month/regime eligibility as set at the beginning of that month, independently run a new one-position account with $10,000 starting cash. Do NOT concatenate published trade ledgers, remove trades after seeing results, or alter the old monthly gates to suit a changed exit. Historical shadow-trade eligibility was estimated using the **original 3R exits**, so its quality may not transfer to trailing; explicitly disclose this training-model mismatch.

Unchanged: stop price = entry minus/plus `stop_atr * original 1H ATR14` (shock / breakout: 1.8 ATR14); equity-risk 0.5% per stop, leverage cap 3×; one position globally; next 1M open after 15M confirmation, Delta modeled taker fees 0.05% per side plus GST 18%, and adverse $5 BTC price-points each side; original max hold 36h for breakout and IST-month-end flatten. If stop and take-profit touched in same 1M bar, stop wins; adverse stop gaps fill at minute open; all trailing edits activate only **after** the current 1M candle closes and take effect in the **next minute**, never at the unknown same-minute extreme.

Five independent hypothetical accounts (not a parameter sweep):
1. `past12_original`: primary 12-month gate + unmodified 3R target, original stop. Full replay MUST reproduce 51 trades, net +8.9446% and identical trade entries/exits and per-trade net cash.
2. `past12_protected`: same 12m gate and original 3R TP; after a breakout position's favorable completed native 1M high/low reaches +1.5R at any point and did NOT stop/target in that minute, **on the NEXT minute** tighten stop to entry +0.15R for long or entry -0.15R for short (never loosen); no further trailing. A 0.15R lock is an assumed price buffer, not guaranteed net fee breakeven.
3. `past12_runner`: same 12m gate, breakout TP removed; initial 1.8 ATR stop. After favorable completed 1M high/low reaches +1.5R, starting **next minute** ratchet stop to prior completed high water minus 1.8 ATR (long) or low water plus 1.8 ATR (short); update on subsequent completed minutes only. Original 36h maximum and IST-month-end flatten unchanged. No future candle high/low known early; stop-first on previous minute's active stop. Other nonbreakout strategies (if any selected by gate) retain fixed TP and stop.
4. `past6_original`: 6m prior gate with unchanged fixed exits; MUST reproduce 55 trades and +3.9621% net.
5. `past6_protected`: a robustness check of the same +1.5R activation/+0.15R protected stop using 6m gate, retaining its 3R TP. This checks whether an outcome depends entirely on which evidence window was used.

Do NOT optimize to the best 2025–2026 result. All five results reported, including negative. Drawdown measured at trade close, no true L1 spread or funding cash ledger, liquidation/contract rounding not modeled. No external truly unresearched holdout, no live approval. Months with no trades count as NOT profitable toward 22/22. Initial 6m/12m warmup requires zero trades in those months. Do not describe 22/22 as achieved unless every one of the 22 complete months is positive after ALL modeled costs.

## Audits and required files

Native 992,160 continuous Delta BTCUSD 1M candles with manifest SHA256 integrity; original 15M confirmation and 4H completed-regime evidence unchanged; original entry/exit parity; stop monotonicity, no exit before entry, no overlapping positions, no same-minute newly raised stop triggering, fee/GST/slippage gross-net cash, account equity reconciliation and monthly IST boundary; disallow any unapproved unknown strategy. All-month CSV, 2025/2026 report, individual trade ledgers (with stop update count/reason), win rate/PF/drawdown, additional hypothetical 2/5/10 bps round-trip execution cost stress for *all* models with equity-dependent sizing. 2026 was researched before this experiment, so results are in-sample from a broader research-selection perspective, even if the code obeys time causality.

Research branch `research/btc-four-layer-trade-management-20261121`, main unmodified, no live trading.