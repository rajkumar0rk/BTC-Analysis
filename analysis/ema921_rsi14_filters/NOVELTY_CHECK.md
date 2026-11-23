# Pre-run novelty check: EMA9/21 three-timeframe entry with higher-timeframe RSI14 gate

Date: 2026-11-23.

**Decision: PARTIAL OVERLAP — approved differential: new RSI oscillator trend-strength confirmation filter layered onto unchanged completed-candle EMA crossover signals.**

## Hypothesis and exact experimental scope
- User requests adding RSI to previously losing BTCUSD EMA9/21 setup. We preserve **exact** existing 1H and 15M EMA9>EMA21 and candle close>EMA9 long context and 5M completed EMA9 cross above EMA21, next 1m entry, with exact opposite shorts; **Monday–Friday entry only** in Asia/Kolkata. Only one open position.
- Add independent *closed-candle*, 14-period Wilder RSI calculated on **1H**, **15M**, or **both** before 5M entry. RSI applies as a strength/confirmation gate, not oversold reversal:
   - LONG: RSI14 >= L; SHORT: RSI14 <= 100-L.
   - Test thresholds L=50 (50/50), L=55 (55/45), L=60 (60/40).
   - Prespecified modes: OFF baseline; BOTH_50; BOTH_55; BOTH_60; H1_55_ONLY; M15_55_ONLY; H1_60_ONLY; M15_60_ONLY; H1_55_M15_50; H1_50_M15_55.
- Test exact fixed stop/target cases (100,200) and (400,1200) BTC points from post-slip entry fill to isolate entry filter effect, instead of retuning stops. One-minute stop-first collision, gap-to-open, IST month flatten, no trailing or time exit. Entry $5 adverse slippage and exit $5, taker fee 0.05% per side with 18% GST. 1x compounded account model.
- RSI computation: Wilder(14), seed averages from the simple arithmetic mean of the first 14 price differences, then recursively update gain and loss by (13 old + new)/14. In a flat market RSI=50; pure up move RSI=100; pure down move RSI=0. Source candles from original Delta India BTCUSD 1m OHLCV.
- Data Jan2025–Oct2026 IST, all researched previously, **2026 not blind holdout**. 2025 Jan IST archive misses 330m. Results by calendar month, win rate, monthly positive count, max trade-close drawdown, 2025 vs 2026 net returns and cost. No funding or real bid/ask depth.

## Closest previous experiments
1. `scripts/research_ema921_1h15m5m_rr.py` and `analysis/ema921_1h15m5m_rr/RESEARCH_REPORT.md` from `research/ema921-1h15m5m-rr-20261122`: identical original EMA signal without RSI gate, variable swing SL, 2R/3R.
2. `scripts/research_ema921_fixed100tp200.py`, `analysis/ema921_fixed100_200/RESEARCH_REPORT.md`: identical EMA entry and fixed 100/200 exits **without RSI**.
3. `scripts/research_ema921_fixed_rr_grid.py`, `analysis/ema921_fixed_rr_grid/RESEARCH_REPORT.md`: 26 fixed stop/target pairs, **without RSI**. This experiment holds stops constant and changes only oscillator entry gating.
4. Existing RSI2 mean-reversion research in `analysis/institutional_discovery_stage19_monthly_10pct/` differs in RSI period, trade direction and trigger (oversold reversal versus RSI14 trend confirmation). Threshold-only retuning of this experiment would be duplicate; here focus on placement and sensitivity *as one finite confirmatory experiment*.

## Protection against silently changing backtest economics
- Baseline NO_RSI+100/200 must exactly match **1130 trades, 359 net winners**; baseline NO_RSI+400/1200 must match **773 trades, 208 winners** from prior completed report. Abort on mismatch.
- Test same weekday entry mask for all scenarios. Positions may exit on weekends; month boundary handling unchanged.
- No parameter optimization after examining 2026. All settings are frozen above; selecting winner within this grid would invite multiple-testing bias.
- This is research of a filter addition to a losing strategy; not independent new alpha and not production readiness.
