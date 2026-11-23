# Trend family source audit — 2026-11-23 23:56 IST

Status: SOURCE-LEVEL SCREEN ONLY. Zero new historical executions, zero verified BTC P&L. No source code executed.

## 1. Aksee123 AlphaTrend strategy
- Immutable code: https://github.com/Aksee123/Trend_strategy/blob/ebe98fcfc3eb0f1ae9f1e380df220a4d3fdb5317/Trend.pine ; author Aksee123 / README attributes Rao Aksee Nasir; Pine v5; README permits educational/personal use with attribution but does not establish a standard OSI license.
- Original market/timeframe: TradingView chart-dependent, not a specified BTC or 1H market. No trustworthy published period, trades, PF, NAV, DD or costs in source.
- Defaults: ATR SMA(TR,14), RSI14, multiplier 1, crosses of price versus AlphaTrend; 10-bar swing stop, 1R target, optional fixed 1% SL/TP. Default order sizing inherited from TradingView, not risk-matched.
- **Critical source bug:** expression `(ta.rsi(src,AP)>=50 ? upT : downT > nz(AlphaTrend[1]) ? nz(AlphaTrend[1]) : downT)` does NOT implement the normal bullish trailing clamp; bullish branch sets `upT` directly. This can create a different path than published AlphaTrend descriptions. **Critical short risk bug:** `fixedSL=close*(1-slPerc/100)` is used for shorts, placing short stop below entry when fixed mode enabled. Also exits use signal-bar close-derived stops before next-bar entry, creating fill-dependent R divergence. No fee model. Reproducing code verbatim is possible but economically unsafe and the central ATR+RSI trend thesis overlaps SuperTrend variants. Gate: SKIP unsafe/overlap; do not silently fix and call it original.

## 2. Viprasol EMA Cross Confluence Edition
- Immutable source: https://github.com/Viprasol-Tech/pine-script-strategy/blob/5b333426745a8fa2a78ae924e9baa31e52fc0da4/src/viprasol_ma_cross_strategy.pine ; Viprasol Tech, Pine v6; license not verified here.
- Default 12/26 EMA crossover, daily EMA50 trend filter, ATR14 2x stop and 3x target; RSI/ADX/volume/session filters disabled by default. Chart timeframe unspecified. Original `process_orders_on_close=true`, 100% equity size, commission 0.04% and one tick slippage; NOT equal to causal next-minute Delta execution.
- Trend regime/crossover with ATR exit duplicates existing EMA/HTF/ATR family research (Stage13/Stage25, 1H/15M EMA and SuperTrend). Gate: DUPLICATE; skip. Publisher PF/trades/period/return/DD not verified.

## 3. Freqtrade TrendRider
- Immutable source: https://github.com/freqtrade/freqtrade-strategies/blob/a892f504b556abed4c22053a09a8a4f0035d4e39/user_data/strategies/TrendRiderStrategy.py ; Freqtrade community; repository license requires separate verification before code reuse.
- Original 1H, long-only, 1x, 210-candle warmup, 4H/1D and BTC informative inputs; multiple EMA/RSI/ADX/BB/MACD pullback/bounce entries. 6% default stop, custom stop disabled, +5% activation then 3% trailing, time-tiered ROI (22.9% immediate; 13.6% after 124m; 4.4% after 290m; zero after 764m), cooldown/stoploss guards. Buy params are explicitly hyperoptimized on five pairs dated 2026-03-23; in-sample selection and transfer risk. No reliable BTC2025 after-cost results supplied; do not infer them.
- Freqtrade informative pairs include BTC/USDT perpetual on a distinct venue and 4H/1D data; cannot claim exact Delta India BTCUSD-only source fidelity without resolving that dependency. Original mixes many existing EMA/RSI/ADX pullback signals; novelty unclear, likely overlap. Gate: PENDING dependency and license audit; no BTC backtest.

## Economics and integrity
- 0.05% fee * 1.18 GST = 0.059% per side; equal-notional round trip = 0.118%, before funding/spread/slippage.
- A proposed source-faithful reproduction must preserve original signal logic in an immutable baseline, disclose separate causal execution adaptation, avoid same-bar favorable fills, compute next eligible 1m open, stop-first on touched bars, and independently reconcile monthly IST NAV/trades/realized PF.
- All three leads currently fail the novelty/source-execution gate. No new historical workflow was launched. The previously completed Kali-Uga workflow 45131335895 remains the latest branch run in the 30-run branch query. No modifications to main, other families, VPS or trading.
- Next: locate a genuinely distinct *complete* persistence source, pin license/settings, preregister differential novelty and launch the existing authentic 1m runner. Avoid repeated screens of EMA+ATR variations.
