# 15M first EMA20 touch: volume/volatility ON, fixed TP 1R/2R + ATR14 trailing 2x/3x

BTCUSD and ETHUSD on 15M Supertrend (Wilder ATR10 multiplier3) and EMA20; 1-minute entry and exit replay; 22 IST months Jan2025–Oct2026.
Entry: first EMA20 touch AFTER confirmed Supertrend flip, ignoring the flip candle. Only one chance per trend cycle.
Both entry filters ON: last completed 15M volume >1.2*SMA20(volume), last completed 15M Wilder ATR14 >20-bar SMA(ATR14). Failed first touch rejects the entire Supertrend cycle.
TP frozen at entry +/- (1 or 2)*R, where R = directional distance from executed entry to last completed 15M ST line.
ATR14 trailing stop: distance frozen at entry = (2 or 3)*last completed 15M Wilder ATR14; initial stop at entry +/- distance and ratchets only on favorable 1-minute price extrema.
Exits on first of FIXED TP, ATR trail hit, or next 15M OPEN after a confirmed opposite Supertrend flip.

| Asset | Fixed TP | ATR trail | Hypothetical path | Trades | Wins | Losses | TP exits | Trail exits | ST flips | Win rate | PF | Net return | Profitable months | Max floating DD |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSD | 1.0R | 2.0× | O-H-L-C | 319 | 115 | 204 | 0 | 176 | 15 | 36.05% | 0.4316 | -43.8988% | 1/22 | 44.3887% |
| BTCUSD | 1.0R | 2.0× | O-L-H-C | 319 | 114 | 205 | 0 | 178 | 15 | 35.737% | 0.4207 | -45.2553% | 1/22 | 45.7333% |
| BTCUSD | 1.0R | 3.0× | O-H-L-C | 319 | 142 | 177 | 0 | 102 | 60 | 44.514% | 0.46 | -47.702% | 1/22 | 48.057% |
| BTCUSD | 1.0R | 3.0× | O-L-H-C | 319 | 143 | 176 | 0 | 99 | 63 | 44.828% | 0.4647 | -47.509% | 1/22 | 47.8653% |
| BTCUSD | 2.0R | 2.0× | O-H-L-C | 319 | 89 | 230 | 0 | 238 | 16 | 27.9% | 0.4751 | -43.2403% | 2/22 | 43.9537% |
| BTCUSD | 2.0R | 2.0× | O-L-H-C | 319 | 90 | 229 | 0 | 236 | 16 | 28.213% | 0.4722 | -43.6323% | 2/22 | 44.3407% |
| BTCUSD | 2.0R | 3.0× | O-H-L-C | 319 | 107 | 212 | 0 | 153 | 68 | 33.542% | 0.5423 | -45.2359% | 4/22 | 45.7192% |
| BTCUSD | 2.0R | 3.0× | O-L-H-C | 319 | 108 | 211 | 0 | 148 | 71 | 33.856% | 0.558 | -43.8707% | 4/22 | 44.366% |
| ETHUSD | 1.0R | 2.0× | O-H-L-C | 268 | 123 | 145 | 0 | 129 | 12 | 45.896% | 0.6728 | -29.7455% | 5/22 | 30.6822% |
| ETHUSD | 1.0R | 2.0× | O-L-H-C | 268 | 121 | 147 | 0 | 130 | 11 | 45.149% | 0.6693 | -30.2084% | 4/22 | 30.9828% |
| ETHUSD | 1.0R | 3.0× | O-H-L-C | 268 | 146 | 122 | 0 | 71 | 48 | 54.478% | 0.7035 | -31.4256% | 5/22 | 33.1941% |
| ETHUSD | 1.0R | 3.0× | O-L-H-C | 268 | 146 | 122 | 0 | 71 | 46 | 54.478% | 0.7147 | -29.9419% | 5/22 | 31.803% |
| ETHUSD | 2.0R | 2.0× | O-H-L-C | 268 | 87 | 181 | 0 | 185 | 15 | 32.463% | 0.7611 | -25.2477% | 6/22 | 29.2655% |
| ETHUSD | 2.0R | 2.0× | O-L-H-C | 268 | 87 | 181 | 0 | 181 | 15 | 32.463% | 0.8059 | -21.1877% | 7/22 | 25.5605% |
| ETHUSD | 2.0R | 3.0× | O-H-L-C | 268 | 102 | 166 | 0 | 115 | 59 | 38.06% | 0.8068 | -25.9509% | 6/22 | 29.3761% |
| ETHUSD | 2.0R | 3.0× | O-L-H-C | 268 | 102 | 166 | 0 | 115 | 58 | 38.06% | 0.8324 | -22.9433% | 6/22 | 30.373% |

## Original reference (NO trailing stop)
- The separate prior 15M 1R and 2R reports are unchanged. This run ADDS the ATR14 trail; TP and 15M volume/volatility filters remain ON.
- Prior 1R no-trail: analysis/st_firsttouch_15m_filtered_tp1r_20261122/summary.csv
- Prior 2R no-trail: analysis/st_firsttouch_15m_vol12_atr14_filter_20261122/summary.csv

## Replay assumptions / limitations
- Replay each 1m bar as either O-H-L-C or O-L-H-C synthetic path. The actual intraminute price order is unknown.
- ATR14 for trailing distance is calculated from the last fully completed 15M candle and FROZEN at entry. It never updates during the position.
- At 1m OPEN, favorable TP gaps fill at the TP level, adverse stop gaps at the market OPEN, with adverse slippage. Price paths after entry determine whether the TP or trail occurs first.
- 0.05% taker fee each side + GST18% on fees, 0.02% adverse slippage per side, initial $1000 modeled 1× capital per independent simulation.
- 22 complete IST months, Jan2025–Oct2026; SHA256-checked Delta India BTC/ETH 1m OHLC. No funding, real orderbook spread, margin/liquidation, exchange latency or partial fills.
- 2026 previously researched; not untouched OOS. Months include MTM of open positions, final sample-end close is accounting only.

Artifacts: summary.csv, monthly_mark_to_market.csv, trades.csv.gz, quality.json, execution.log.
