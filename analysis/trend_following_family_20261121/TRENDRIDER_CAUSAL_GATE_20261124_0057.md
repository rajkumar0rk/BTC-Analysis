# Trend family — TrendRider exact-source causal gate (2026-11-24 00:57 IST)

Status: STATIC SOURCE AUDIT ONLY. No new historical replay or verified BTC P&L.

Immutable upstream: https://github.com/freqtrade/freqtrade-strategies/blob/a892f504b556abed4c22053a09a8a4f0035d4e39/user_data/strategies/TrendRiderStrategy.py . Community Freqtrade code; exact reuse license must be verified. Source is 1h long-only, 1x, with six independent OR entry tags, four exit tags, -6% stop, +5% activation/+3% trailing and time-tiered ROI. Hyperopt settings explicitly fitted to five pairs on 2026-03-23; no source-proven BTC2025 after-cost PF/return/DD/trades.

## Three additional executable-fidelity findings

1. The source sets `startup_candle_count = 210` on 1h bars while its 1d informative feed calculates EMA200. 210 hours (~8.75 days) cannot warm up a 200-DAY EMA; daily data history and informative pair warmup must be independently confirmed. The 1d EMA200 check is applied to **only** the `trend_pullback` entry, not all six entries.
2. The `bb_bounce` entry has no EMA200 bull-regime condition at all; it checks close near lower BB, bullish candle, RSI<45, ADX>18 and other conditions. The `rsi_bounce` and `ema_crossover` branches also do not enforce daily EMA200. Calling the combined model a uniformly D1-confirmed trend-following system is factually wrong.
3. In the data-provider-unavailable branch, `btc_is_bull_1h` defaults to 1 and `btc_rsi_1h` to 50; missing sentiment data can therefore make the filter permissive, not conservative. `funding_rate`, `oi_change`, and fear/greed are hard-coded neutral; no historical funding modeling is present. The source's BTC/USDT:USDT informative pair is a separate instrument/venue and cannot be silently replaced with Delta BTCUSD while claiming exact fidelity.

## Decision and next action

Novelty gate: SKIP for this source in the BTCUSD trend hunt. The six-entry OR system is predominantly EMA/RSI/ADX/BB/MACD pullback or bounce with overlap against Stage13 and Stage25; its daily trend-persistence claim is not enforced across entries, and exact market-dependent reproduction would require another venue's informative series. No rules invented, no execution scripts installed. A modified D1-gated variant would be a NEW independently defined hypothesis, not the original source and would require its own novelty approval before historical replay.

Fees remain 0.05% per executed side plus 18% GST; 0.059% each side, 0.118% round trip at equal notional, before slippage, spread, funding. Historical 1m runner is available via isolated GitHub Actions; this audit does not count as a historical backtest. The latest verified historical run in branch Actions list remains Kali-Uga 45131335895 (completed/success), which is an existing rejected model. No main/other-family/VPS/trading changes.
