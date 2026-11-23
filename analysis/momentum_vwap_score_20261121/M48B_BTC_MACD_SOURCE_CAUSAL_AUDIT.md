# M48B — Apache-licensed BTC MACD source-code causal audit (2026-11-24 IST)

Source: https://github.com/iamrichardD/tradingview/blob/9d20d513dcc3348024f82a0ffac6b2d90f6891a2/production/5m-scalping-strategy/strategy.pine ; blob SHA e383ce23a06c43d2ae2076c283fb75ec5b38b35a. Repo LICENSE Apache-2.0; source header separately says MIT, an attribution/license inconsistency to retain and review. Original stated BTC futures 5m. Publisher README claims 21 trades, 85.71% win rate and PF2.687; source header instead says 58.70% win rate. Dates, DD and funding/cost parity unestablished. No local Delta performance.

**Actual defaults:** MACD(8,21,5); prior-bar MACD zero and signal-line crosses; 1.5x volume/SMA20; price above SMA20; long-only (short disabled); 1% equity; 1.8% SL; 2.7% TP; 0.5% activation and 0.3% trailing distance; 12 max daily trades; 0.05%/side commission; 1 tick slippage; process_orders_on_close=true and calc_on_every_tick=true. Early momentum/histogram acceleration is OFF by default.

**Critical causal and fidelity defects:**
1. Entry signals use MACD[1]/MACD[2] crosses, but contemporaneous volume and trend filters; therefore source combines a lagged crossing event with current-bar filters.
2. On entry it sets `entryPrice := open`, while orders are sent with `process_orders_on_close=true`. SL/TP are anchored to candle OPEN, not the actual entry fill at CLOSE. An apparently favorable or unfavorable 5m candle changes real risk and reward. This is not a 1m next-open source-equivalent fill.
3. Trailing updates highestPrice using the current bar HIGH and then submits an exit using that HIGH-derived stop. The 5m OHLC path cannot establish whether the high preceded the low/stop. Any Delta replay must conservatively process preexisting stop first and only activate new trail at the next eligible minute.
4. `calc_on_every_tick=true` can produce live intrabar signals from current volume/close, whereas historical bars lack matching tick feed. No source-faithful live/historical parity is established.
5. `dailyTrades` increments only on CLOSED trades, not entries; the label Max Daily Trades does not strictly cap daily entries. `ta.change(dayofweek)` resets by weekday change, not a specified IST trading session.

**Novelty:** default is MACD crossover with trend/volume filter, not histogram acceleration. Earlier M14 MACD/RSI and momentum-score screens overlap; optional early signals would be a different configuration but need a separate novelty gate and source-faithful risk semantics. Decision SKIP unchanged as acceleration candidate. No replay, variant or profit claim.

Source inspection is a static audit, not a completed fix. To test a corrected execution model, explicitly label it a derived adaptation, preserve the original and run authentic Delta BTC2025 historical replay before claiming results.
