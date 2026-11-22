# Novelty Check — 1H EMA20 Touch next-candle green confirmation

**Date 2026-11-22. Decision: PARTIAL OVERLAP — approved incremental entry signal test per user request.** The existing ST(10,3)+EMA20 TOUCH signal was tested with a breakout of TOUCH candle HIGH+0.5 during the **next 1H candle**, without checking that next candle's full color. User requires that a **bullish** Touch setup trade only if the NEXT completed 1H candle is **GREEN**. Compare LONG-only and (as an explicitly labeled auxiliary test) symmetrical SHORT RED. This is a materially different confirmation/entry timing, not an arbitrary target parameter retest.

## Confirmed entry semantics (causal, no peek)
1. An original 1H GREEN Supertrend + EMA20 Touch signal forms at hourly index i, only after candle i closes; original setup generation is reused exactly via `setups(h, "touch")`.
2. Let candle i+1 be the next completed 1H candle. For LONG, require its Close **strictly greater than** its Open. Also require Supertrend still GREEN at i+1 close. Otherwise **do not trade this touch event**.
3. Place LONG market entry at candle i+2 **OPEN**, with 5 BTC price-point entry slippage. No entry inside i+1, because the GREEN color is not known until it closes. No new EMA, breakout or candle-body filter unless explicitly listed.
4. For the auxiliary bidirectional test, symmetrical SHORT requires ST RED and candle i+1 RED (close strictly below open), then enter i+2 open.
5. For one-per-cycle parity, each Supertrend cycle may fill one eligible confirmation; if the first touch is unconfirmed and later valid touch forms under the *existing* source setup function, permit the later confirmation. Compare separately against original TOUCH breakout baseline and original TOUCH LONG-only subset. This is a deliberately different entry pattern and entry timestamp; do not claim identical fills.
6. No new initial stop-loss, fixed target, time exit, or exit other than instant direct profit lock at ladder threshold and fallback at confirmed opposite 1H ST flip. No extrapolation beyond final ladder rung.

## Predefined comparison strategies and locks
- `original_touch_breakout_long_only` = filter source `entry_candidates(m,h,"touch")` to LONG, keep original 1m next-hour signal high breakout.
- `next_1h_green_long_only` = above confirmation at following 1h close, entry after it closes.
- `next_1h_green_red_both_sides` = LONG green / SHORT red confirmation.
- `original_touch_breakout_both_sides` = original unfiltered benchmark.

Percentage lock grids: single **0.14%, 0.50%, 0.75%, 1%, 2%, 5%**, and **0.50→1→2→5%, 1→2→5%, 2→3→5%**. Each percentage is BOTH trigger and immediately protected stop; identical source replay/fee rules: 0.001 BTC, $100 illustrative starting, taker fee per side 0.05%+18% GST, 5 points slippage per side, no funding/liquidation modeling. Model **both O-H-L-C and O-L-H-C** per 1m candle, including entry minute. 4 entry modes × 9 locks × 2 paths = **72** comparisons.

## Baselines / existing evidence
- `research/st-ema20-large-percent-profit-locks-20261122:analysis/st_ema20_large_percent_locks_1h/comparison.csv`, baseline TOUCH 253 trades, first 1M break of 1H touch signal, 0.75% lock net -$11.94 to +$5.57; 2→3→5% net -$10.03, 1→2→5% net -$2.60. Other entry modes Reclaim and Combined are distinct, not merged with the new test.
- `research/st-ema20-percent-direct-lock-grid-20261122`: 0.12–0.30% percentage locks but no next-candle-color confirmation.
- `research/st-ema20-immediate-five-lock-ladders-20261122`: fixed points and no next-candle-color confirmation.
- `research/st-ema20-reversal-only-20261122`: no profit locks, independent favorable-price reach benchmark.

## Required artifacts and controls
Validate complete Delta India BTCUSD 1-minute archive Jan 2025–2026-11-20. Emit source parity assertions, filtering/future-looking unit tests, candidate counts by LONG/SHORT, monthly by IST exit, realized drawdown and net after modeled fee and slippage, full trade ledgers, and full-month counts (22 complete months Jan2025–Oct2026). A retained trade can trigger a market stop inside a candle hypothetically; 1m OHLC does NOT establish tick order. The two path replays are uncertain, not tick-exact high/low bounds. Filter tested retrospectively on already-inspected data: no true untouched holdout. No initial stop leaves liquidation risk without a liquidation engine. No deployment.
