# Step 5 — BTC mandatory-daily causal regime switching, preregistered

**Novelty decision: PARTIAL OVERLAP — new conditional-exit comparison on established daily signal.**

## Closest work and reason for study
- `scripts/research_btc_every_weekday_reset_step1.py`: 51,840 models forced one entry on each 477 full Mon-Fri IST days; static stops/TP, 24 clocks, 10 directional rules, 2025-2026.
- `scripts/research_btc_every_weekday_adaptive_step2.py`: 18,360 first-event signal/fallback entries with static exit.
- `scripts/research_btc_every_weekday_exit_protection_step3.py`: 425 exit designs with next-1m causal stop update, fixed per strategy, historical protected 265/477 net +6.79%, drawdown 6.87%.
- `scripts/research_btc_daily_fallback_regime_step4.py`: 8,064 fallback-direction × separate event/fallback exit designs; hindsight candidate **B** 271/477 winning, +15.52%, max closed DD 6.71%, 16/22 profitable months, 477 trades; option **A** 274/477, +14.43%, DD 6.63%, 15/22 months. **Both were selected using full period and are NOT validated.**
- `scripts/audit_btc_daily_fallback_regime_november_2026.py`: B yielded +0.019% on only 15 later November weekdays with hypothetical Scalper Offer, effectively flat. Historical cost sensitivity remains high.

## Unchanged mandatory daily contract
- Exactly ONE BTCUSD futures trade on EVERY full IST Monday–Friday date 2025-01-02 through 2026-10-30, 477/477 days, including 260 in 2025 and 217 in 2026; no skipped signals and no weekend trades.
- Frozen EVENT entry: earliest 18/19/20 IST checkpoint where previous complete 5m volume >/=1.5 times mean previous 20 completed 5m bars, then FADE preceding 5m return. Price fill at entry 1m open. If no event, forced FALLBACK at 21:00 or 22:00 IST with a causal direction determined at that exact time from strictly earlier complete 1m bars.
- Predefined fallback directions: follow5, fade5, follow15, follow60, follow5 if |past5m return|>=0.10% else fade5, follow5 if 5m/60m directions agree else fade5, follow5 if prior 5m volume>=1.25x else follow60, follow60 if |prior 60m return|>=0.30% else follow5, fade5 if past 5m return >=0.15% magnitude else follow5, follow5 if 5m/15m agree else follow60, fade60 if 60m price position >=0.85 or <=0.15 else follow5. All use only candles preceding entry; tie signs deterministic long.
- Available complete-preentry context for dynamic exit regime: last 60m high-low range relative entry mid, absolute 5m return, last 5m volume ratio to prior 20 bars, alignment of signed 5m/60m momentum. Trigger each day at time of entry. Choose a predeclared HIGH- or LOW-regime exit recipe, NEVER optimize intraday by future.
- Predeclared regime rules: always-high (control); preentry 60m range >=0.45%, >=0.80%; |5m return| >=0.12%; previous-completed 5m volume >=1.25x; 5m and 60m directions agree. Total 6.
- EVENT exit choices: (1) lock: SL0.5%, activate +0.25% favorable, protect +0.10% gross, 3% gross TP; (2) same lock with SL0.75%; (3) same lock with SL1%; (4) trailing: SL0.5%, activate +0.35%, distance0.20%. FALLBACK low/high exit choices: lock0.5, lock0.75, trailing0.5, trailing0.75, static0.75 (all gross TP3%, 30m max).
- Apply 11 fallback side policies ×2 mandatory fallback entry hours ×4 event exits ×5 low-regime fallback exits ×5 high-regime fallback exits ×6 regime tests ×2 cost models = **26,400 configurations**. No new trade filters, no reductions in trade count. Include exact B, A and previous protected 265 baselines and assert parity.
- Stop-first if SL and TP both touched in 1m candle, gap-worse stops; favorable high-low of a minute cannot tighten stop during that minute (updates only valid NEXT 1m). No unrealistic fills at future extrema. Force out at next 1m OPEN after 30m maximum. All positions completed same weekday.
- 1× account notional, unleveraged. 0.05% standard taker fee each side +18% GST on each charged fee, 5 BTC quote-price points adverse slippage per side; hypothetical eligible regular Scalper Offer = closing fee/GST waived only if exit <=30m (preactivation assumed, not verified historically). No true bid/ask depth, funding or latency modeling.

## Selection and measures
- Select using ONLY 2025 (260 sessions), first require 2025 net compounded account profit >0 and <=8% 2025 max closed DD; maximize 2025 profitable-day count then 2025 net return then lower DD. Freeze 2025 chosen model and measure 2026 separately without adjustment. 2026 is RESEARCH-EXPOSED, not independent blind OOS.
- Explicitly compare hindsight Pareto to B (271 profitable days, +15.522%, 6.7068% DD, 16/22 profitable months), A (274 profitable days, +14.434%, 6.6325% DD, 15/22 months), previous protected (265 winning, +6.7867%, 6.86685% DD); never promote full-period cherry-picked winners as independently validated.
- Preserve daily loss/win, year-by-year compounded returns, 22 individual months, max DD, worst day/month, maximum consecutive loss streak, fees/slippage, frequency of fallback trigger, same-trade 477 count. Show no improvement if test fails. Requiring every weekday trade is a user constraint, not an assurance of daily gains.
- November already used as a later audit; do not re-use it to select new variants. Future forward paper trading would still be needed before real deployment.
