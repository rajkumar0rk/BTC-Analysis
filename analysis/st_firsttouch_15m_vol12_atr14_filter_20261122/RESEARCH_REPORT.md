# 15M first EMA20 touch: Volume > 1.2 SMA20 and ATR14 > SMA20(ATR14), TP=2R and ST-flip exit

BTCUSD and ETHUSD, signal timeframe 15M, 22 IST months Jan2025-Oct2026.
First EMA20 touch after ST(ATR10, factor3) flips, flip candle excluded. Both filters use last COMPLETED 15M bar. If either filter fails at first touch, no trade in that ST cycle.
TP = fixed 2 x entry-to-ST-line distance; exit loss only at next 15M open following confirmed opposite ST flip. No fixed hard SL or profit lock.

| Asset | Hypothetical 1m path | First touches | Rejected by either filter | Passed both | Trades | Net wins | Net losses | TP 2R exits | ST flip exits | Win% | PF | Net return | Profitable months | Max floating DD |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSD | O-H-L-C | 1559 | 1236 | 323 | 319 | 123 | 196 | 117 | 202 | 38.558% | 0.6246 | -41.9081% | 3/22 | 42.4207% |
| BTCUSD | O-L-H-C | 1559 | 1236 | 323 | 319 | 123 | 196 | 118 | 201 | 38.558% | 0.6262 | -41.7124% | 3/22 | 42.2267% |
| ETHUSD | O-H-L-C | 1425 | 1155 | 270 | 268 | 109 | 159 | 105 | 162 | 40.672% | 0.8002 | -29.5738% | 8/22 | 32.3464% |
| ETHUSD | O-L-H-C | 1425 | 1155 | 270 | 268 | 108 | 160 | 104 | 163 | 40.299% | 0.7923 | -30.7509% | 8/22 | 33.4771% |

## Volume and volatility settings
- Last completed 15M volume strictly > 1.2 * 20-bar SMA(volume); average includes last completed bar, excludes current in-progress bar.
- Last completed Wilder ATR(14) strictly > 20-bar SMA(ATR14); ATR14 uses SMA14 initialization, Wilder recursive smoothing.
- Filters both required. Individual reject counts overlap when both fail. One chance per Supertrend flip at first EMA20 touch only.

## Methodology and limitations
- Original Delta India 1m data Jan2025-Oct2026 verified by SHA256; zero missing 1m observations.
- 1m O-H-L-C and O-L-H-C synthetic path assumptions are NOT real historical ticks or rigorous bounds.
- Supertrend uses ATR10 factor3, NOT the ATR14 used for the volatility filter.
- Fixed TP 2R is calculated from current Supertrend line but real loss is not capped at 1R because stop only occurs after confirmed ST flip.
- Cost: taker fee 0.05% each side + GST18%; adverse slip 0.02% each side, capital $1000, 1x notional, evolving equity.
- No exchange margin/liquidation, real spread, funding, depth or latency; backtested history not pristine holdout.
- Monthly return is mark-to-market including open positions; final forced close is accounting only.

Artifacts: summary.csv, monthly_mark_to_market.csv, trades.csv.gz, quality.json.
