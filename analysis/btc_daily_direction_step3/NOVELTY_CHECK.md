# Step 3 — causal BTCUSD pre-entry direction signals (pre-run novelty gate)

**Decision:** PARTIAL OVERLAP — approved *diagnostic incremental hypothesis*, not a claim of new alpha or an investment recommendation.

## Closest previous experiments
- scripts/research_btc_daily_opportunity_step1.py and analysis/btc_daily_opportunity_step1/RESEARCH_REPORT.md: 477 complete IST weekdays; **7/8 PM** historically high **hindsight either-side** price opportunity, no predictor.
- scripts/research_btc_daily_target_first_step2.py and analysis/btc_daily_target_first_step2/RESEARCH_REPORT.md: fixed-clock unconditional LONG/SHORT, 1-minute target-first versus stop-first at +0.2% net after offer; none of 288 unconditional fixed direction cases profitable in 2025.
- scripts/research_every_candle_200.py, analysis/institutional_discovery_stage6_every_candle_200/ and stage7_time_volume: BTC fixed *point* outcomes for multiple completed-candle filters; not fixed 19:00 / 20:00 IST net 0.2% **account** direction selector with measured no-trade days.
- scripts/research_one_trade_every_day_200.py: forced NY trading day entry + fixed point target, not selective IST direction.
- scripts/research_monthly_10pct_stage19.py and newer 15m compression strategy: very different event-driven pattern and 5m entry times; no fully causally gated 19/20 fixed-clock direction signal tested with this cost and target.

## New measurable hypothesis
At 19:00 / 20:00 IST BTC often travels far enough in **one** direction; can *pre-entry* 15m/1h/4h momentum, trend, reversal, range-position and 5m-volume select that direction well enough that small wins outweigh losing days?

## Fixed setup BEFORE backtest
- BTCUSD 1m authentic archive from 2025-01 through 2026-10 inclusive. Test 2025-01-02..2026-10-30, exactly 477 complete IST Mon–Fri sessions, no Saturdays or Sundays. Source gap/duplicate/null/OHLC checks inherited from Step1.
- Entry at the 1-minute OPEN at **19:00**, **20:00**, or first eligible 19:00 then 20:00 fallback, maximum ONE position/day. Features use only 1m candles **strictly prior** to entry and last *completed* 5m, 15m, and 1h candles. No direction selection from future.
- Prior lookback returns: (previous 1m close / 15-, 60-, 240-minute-ago open) - 1. Prior 1-hour/4-hour high-low position (prior 240 bars); completed 5m volume ratio = last completed 5m volume / preceding 20 completed 5m average.
- Signals, each authoritatively distinct and frozen: always long; always short; 15m, 60m, 240m return direction; 15m and 60m same sign; 60m and 240m same sign; hourly EMA20/EMA50 regime (close versus EMA20 too); completed 15m EMA9/EMA21; 15m + 1h alignment; 15m reverse on +/-0.15% move; 60m reverse on +/-0.30% move; 15m retrace against 60m direction; 240m range-position extreme >=0.8 / <=0.2; 15m momentum + prior 5m volume ratio >=1.5; hourly trend + 15m return agree + 5m volume >=1.25. All signs are symmetric long and short. Weak/no agreement => no trade. No model can see 2026 before selection.
- Static STOP 0.2%, 0.3%, 0.5% price move adverse from entry mid; TP = **+0.20% NET ACCOUNT** at 1x notional after actual fee assumptions and slippage. 1m replay, stop-first on double touch, gap-aware stop fill, maximum hold 30 or 120 minutes. Fully overnight-free.
- Primary economic model: hypothetical **regular Scalper Offer** activated in advance: opening taker 0.05% +18% GST, closing fee zero only when within 30m, otherwise 0.05% taker + GST. 5 BTCUSD quote-point adverse slippage on entry AND exit. Also reprice identical trades under standard double-sided taker fee. No leverage or liquidations/funding.
- For each candidate × entry rule × stop × hold, report 2025 and Jan-Oct 2026 NET compounded account return at 1x, +0.2% weekdays, net win/loss/no-trade days, coverage, max drawdown, worst day, 22 monthly returns, TP before stop rate. No-trade weekdays contribute 0%.
- **Pre-committed selection**: rank 2025 variants first among those with >=45 trades in 2025 and positive 2025 NET compounded return; maximize 2025 +0.2% account-goal days, tie with higher 2025 account return, lower drawdown. If no positive 2025 variants, choose least negative for diagnosis only, mark invalid. Freeze 2025-selected rule, check 2026 without retuning. Also show 2026 performance across all rules separately to flag selection bias.
- No artificial win-rate guarantee: 2025 already studied, and 2026 previously exposed through related BTC research, so this is an imperfect recheck, **not a pristine blind holdout**.
