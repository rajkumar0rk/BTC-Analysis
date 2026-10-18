# BTC Futures 30-Minute Data — Institutional-Style Review

**Archive:** 5-minute BTC OHLCV aggregated into 30-minute completed candles. **Research dates:** January 1–July 31, 2026 UTC (10,176 candles). Predefined chronological partitions: January–April (train), May (validation), June–July (out-of-sample check). This is a research exercise, **not proof of executable trading edge**.

## Time definitions and scope

- Source timestamps are treated as **candle-close labels**. For example, a source 30-minute row stamped 10:00 AM New York covers the candle opening 9:30 AM and closing 10:00 AM New York time (DST handled using America/New_York).
- An outcome following a signal is measured by a **hypothetical entry at the next 30-minute candle's open**, exiting at the close of the fourth 30-minute candle after the signal, approximately two hours after the signal. This is an OHLCV proxy without real bid/ask, slippage, fees, funding or liquidation margin.
- Premarket reference is 00:00–09:29:59 New York: previous 19 completed 30-minute candles, with 09:30–10:00 as the US cash-opening candle. The dataset is BTC futures OHLCV, **not** a feed of stock market transactions, order book, liquidations or institutional holdings.

## What the market reveals about the US opening

For June–July (45 weekdays), the first 09:30–10:00 NY candle had a **median high-low range of 88.1 basis points** versus **37.8 bp** for other weekday 30-minute bars. After that bar, the next **two-hour closing-price change** was 0.5% or more (absolute value) in **27/45 cases (60.0%)** versus **29.0%** across all 30-minute bars in the test period. This suggests **volatility timing** rather than directional predictability.

Blindly continuing in the opening candle's direction was profitable (before costs, next-bar-open to two-hour close) in only **19/45 cases (42.2%)** in June–July, with average **-7.3 bp**. In January–April, it was 54.7% with average +1.7 bp. Thus the opening candle's color alone **did not generalize**.

## Most interesting exploratory level-interaction condition

**Rule observed at 10:00 AM New York:** The 09:30–10:00 opening candle trades **below the 00:00–09:30 premarket low** and **closes below that low**. Evaluate a short from the **next candle's open**, exit at 12:00 NY (two hours after signal close).

| Period | Cases | Positive shorts | Mean signed return | Median signed return |
|---|---:|---:|---:|---:|
| Jan–Apr (train) | 14 | 10 (71.4%) | +23.0 bp | +21.0 bp |
| May (validation) | 5 | 3 (60.0%) | +22.4 bp | +16.6 bp |
| Jun–Jul (test) | 10 | 6 (60.0%) | +21.2 bp | +28.9 bp |

This was more stable *on a fixed two-hour close-to-close outcome* than most other directional effects. On June–July, **a bearish US opening candle that did NOT close below the premarket low** had a mean short outcome of **-34.7 bp** (9 cases). This illustrates why location relative to a price level may be more relevant than color alone.

However: just **10 out-of-sample cases** (6 wins) produce a huge 95% exact binomial interval for win probability (about **26%–88%**). In test, worst two-hour result was **-219 bp** and best +220 bp. The pattern is **not a validated trade**: a stop/target replay using a stop at the opening candle's range and 1.5× range take-profit yielded a mere **+0.3 bp per trade on average in the test set before costs**, and tighter stops performed worse. This illustrates how a positive timed-exit average can vanish with stop constraints. Intrabar stop/target order is unknown and we conservatively assign stop first on collisions.

## Negative findings that matter

Taking the previous New York day's high and closing back below did not consistently forecast declines. Out-of-sample, 31 such first-crossing events delivered only **51.6%** positive short trades, with average **+2.0 bp**, too small relative to costs. A prior-day low sweep and reclaim was *negative* in June–July (24 events, only **41.7%** positive longs, average **-21.1 bp**). Therefore "liquidity sweep = reversal" is **not** a reliable universal rule in this archive.

The 09:30 opening bar is high-volatility, and Sunday 18:00–18:30 New York also shows unusually large relative candle ranges. Neither establishes a bullish/bearish bias by itself.

## Institutional-style research process

1. Identify a **map** of previous New York day high/low, completed 00:00–09:30 overnight high/low, and the cash-open 09:30–10:00 range. These are *observable reference levels*, not evidence of actual stop orders.
2. Separate **acceptance** (close beyond a level) from **rejection** (cross then close back inside). Calculate future signed price change and path risk for each, conditioned on session clock and trend/volatility regime.
3. Before allowing entries, require sufficient repeated examples and verify **out of sample**, avoiding rule tweaks after viewing Jun–Jul.
4. Execute only after the candle that establishes the condition has closed. Calculate fees, spread, slippage, depth, funding and liquidation risk; backtest realistic stop/target handling, including gaps.
5. Use a session volatility alert for 09:30 NY and the overnight-low acceptance pattern as **research hypotheses**—not live orders—until newer months confirm edge net of costs.

## Limits

The file has OHLCV only. We cannot know where institutions placed limit orders, who initiated trades, actual stop clusters, order-book imbalance, liquidation events, open interest, or market news. Any claim that institutions “hunted stops” would be speculation. Confidence intervals and historical periods are not guarantees, and many exploratory rules were screened, adding selection bias.

## Supporting files

- `btc_30m_institutional_event_tests.csv`: prior-day high/low and overnight breakout/rejection results by period.
- `btc_30m_institutional_time_baselines.csv`: 09:30 NY opening volatility versus other hours.
- `btc_30m_ny_open_conditions.csv`: opening bar placement/volume/structure tests by period.
- `btc_30m_ny_lowbreak_stoptarget_sensitivity.csv`: stop/target stress test, deliberately conservative.
- `btc_30m_ny_open_features.csv`: daily reference levels for reproducing opening-bar tests.