# Novelty gate — FIRST EMA9/21 crossover, maximum ONE entry per Supertrend regime

Date: 2026-11-22. Status: **PARTIAL OVERLAP, NEW STRICT PER-REGIME GATE**. No claim of new independent indicator or out-of-sample validation.

## User request, precise preregistered entry logic

- Preserve the previously completed **second-crossover** research unchanged at `analysis/supertrend_second_ema_cross/`; create a distinct study at `analysis/supertrend_first_cross_once/`.
- Independently for each 5-minute, 15-minute and 1-hour timeframe, compute standard closed-bar Supertrend Wilder ATR10 × 3 and EMA9/EMA21.
- **LONG**: once Supertrend has flipped into GREEN, enter on the **FIRST bullish EMA9 crossover ABOVE EMA21** (EMA9 preceding <= EMA21 preceding and EMA9 current > EMA21 current), provided Supertrend was already GREEN on the previous completed bar and remains GREEN on the crossover bar. Entry at the next actual 1m candle OPEN. A Supertrend flip by itself is NOT an entry.
- **SHORT**: once Supertrend has flipped into RED, enter on the **FIRST bearish EMA9 crossover BELOW EMA21**, provided Supertrend already RED on prior and current completed bar, entry next 1m OPEN.
- Reset crossover eligibility whenever Supertrend changes color. A cross on the same bar as the Supertrend color flip does not count. If the trend flips before the first eligible EMA crossover, no trade for that trend. If no crossover, no trade.
- **Maximum one signal / one entry attempt per entire Supertrend color regime**, even when SL or TP exits early. No re-entry on subsequent EMA crossovers in the SAME regime. A second or third EMA crossover in the same regime is ignored. If signal happens while position still active, it is consumed, not queued, and cannot re-enter within the regime.
- If a position lasts beyond Supertrend flip, do not close it just because the Supertrend flips; fixed TP/SL or month flatten only. Signals on subsequent regimes while in a trade are skipped/consumed.
- Warmup first 100 fully completed strategy-timeframe candles; ignore incomplete candles; no repaint, no future high/low used to enter.

## Contrast with prior repo research

- `research/supertrend-first-ema-cross-20261122` / `analysis/supertrend_first_ema_cross/` permits **EVERY** eligible first-style EMA cross during the same ST color regime. THIS study only permits one crossover/attempt per regime; prior statistics cannot be reused.
- `research/supertrend-second-ema-cross-20261122` / `analysis/supertrend_second_ema_cross/` waits until the **SECOND** qualified EMA crossover. Here first qualified crossover triggers and subsequent crosses are ignored.
- `research/supertrend-ema921-20261122` and fixed/grid follow-ups count entry on newly combined alignment, including an ST flip when EMAs already above/below, not this first-cross event.
- EMA-only MTF confirmation studies in `analysis/ema921_fixed100_200/` use a different signal. Thus this is a user-specified *signal gate* research comparison, not a new profitable discovery by moving stop/target levels.

## Frozen exit grid and research protocol

- Authentic Delta India BTCUSD perpetual 1m OHLCV from `data/delta_india/BTCUSD/1m/`, Jan 2025 to Oct 2026 IST inclusive. First 330 minutes of Jan 2025 IST unavailable, remaining data continuous; reject other gaps.
- Single open position, both directions, 24×7. Entry next real 1m open after signal candle closes. Strict 1m OHLC first-touch stop/target with stop-first ties, stop gaps at next 1m OPEN. Ignore indicator flip as exit. Position flattened IST month end for monthly attribution.
- 20 exact fixed pairs, all carried unchanged from second-cross study:
  - 1:3: (100/300),(150/450),(200/600),(300/900),(400/1200),(500/1500),(600/1800),(800/2400),(1000/3000).
  - 1:4: (100/400),(200/800),(300/1200),(400/1600),(500/2000),(600/2400),(800/3200),(1000/4000).
  - Other references (100/200),(200/2000),(1000/2000). **60 scenarios total**.
- 1× exposure compounded per actual trade. Per-side 0.05% taker fee plus 18% GST, $5 BTC price-point adverse slippage per side. No maker spread/orderbook funding/liquidation/margin modeling.
- Report 60 combinations with 22 IST monthly returns each; wins, losses, win rate, total return, PF, drawdown (trade-close only), positive months, 2025 and 2026 changes. Save full trade ledger and quality stats. Compare to second crossover under identical assumptions. No performance optimization after results.
- 2025/2026 data already repeatedly studied; research-exposed, not blind forward validation. No recommendation for real money trading based on any cherry-picked winning configuration.

## Tests that must pass

1. First eligible cross during green triggers exactly one LONG and ignores second/third in same green.
2. First eligible cross during red triggers exactly one SHORT and ignores next red bearish cross.
3. No EMA crossover means no trade even if Supertrend green/red.
4. EMA crossover exactly simultaneous with ST flip does not trigger or consume chance; next later qualified crossover is first.
5. ST flip before an EMA crossover resets regime; cross from old trend not carried forward.
6. After first-crossover signal has fired, a second crossover after early TP/SL does not generate a second trade in same ST regime.

All work stays on isolated branch `research/supertrend-first-cross-once-20261122`, and the previous second-crossover version is kept unchanged.
