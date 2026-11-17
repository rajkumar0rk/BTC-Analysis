# Stage 6 — Every BTCUSD 1m candle: 200 points, clean paths and executable entries

## Dataset audit
- Real 1m candles loaded: **984,960**
- Fully eligible next-open entries: **984,122** per direction
- All long+short entry paths evaluated: **1,968,244**
- Gaps: **1,440** missing minutes across **1** breaks; never filled
- Predeclared directional rule names: **18**
- Strict zero-loss strategies with at least 100 trades in a period: **0** cells (not a guarantee)

## Honest definitions
- 'Clean 200' means no adverse midprice movement in ANY 1m OHLC bar before or in the TP minute.
- First 200 achieved within horizon is an ex-post label, not an entry signal.
- 200 net after standard fees requires a larger dynamic price target, computed using actual entry BTC price.
- Same-bar stop and target ambiguity is ALWAYS counted as a stop.
- One trade at a time separately for each candidate model, no forced daily trades.
- Standard scenario: 0.05% taker each side + 18% GST and 5 points adverse slippage each side.
- Scalper scenario: closing fee waived only if the modeled holding time is <=30m, conditional on eligibility.
- All historical intervals including November 2026 are exploratory; do not claim an independent holdout.

## Unconditional all-candle reference (not a portfolio)
| rule               | period     |   horizon_min |   signals |   target_200_pct |   clean_200_zero_adverse_pct |   tp_before_stop_100_pct |   target_200_net_after_fees_pct |
|:-------------------|:-----------|--------------:|----------:|-----------------:|-----------------------------:|-------------------------:|--------------------------------:|
| every_minute_long  | 2025_train |            30 |    984122 |           31.717 |                      2.91488 |                   22.69  |                          16.868 |
| every_minute_long  | 2025_train |            60 |    984122 |           45.117 |                      3.19503 |                   28.281 |                          28.112 |
| every_minute_long  | 2025_train |           240 |    984122 |           69.76  |                      3.35324 |                   33.172 |                          55.269 |
| every_minute_short | 2025_train |            30 |    984122 |           32.105 |                      3.02412 |                   23.195 |                          17.289 |
| every_minute_short | 2025_train |            60 |    984122 |           45.598 |                      3.30396 |                   28.898 |                          28.883 |
| every_minute_short | 2025_train |           240 |    984122 |           70.124 |                      3.43626 |                   33.434 |                          56.599 |

## Predeclared executable strategies at 200 gross TP / 100 stop / 30m max
| rule                         | period     |   trades |   win_pct |   avg_net_pts |   profit_factor |   max_drawdown_pts |   worst_net_trade_pts |   losses_or_flat |
|:-----------------------------|:-----------|---------:|----------:|--------------:|----------------:|-------------------:|----------------------:|-----------------:|
| 15min_close_breakout_long    | 2025_train |     1561 |     26.33 |      -126.352 |           0.139 |   197235           |               -258.19 |             1150 |
| 15min_close_breakout_short   | 2025_train |     1801 |     27.48 |      -122.227 |           0.156 |   220208           |               -256.52 |             1306 |
| 20m_accepted_breakout_long   | 2025_train |    16422 |     26    |      -119.619 |           0.145 |        1.96439e+06 |               -275.92 |            12152 |
| 20m_accepted_breakout_short  | 2025_train |    17396 |     26.55 |      -118.881 |           0.15  |        2.06818e+06 |               -263.88 |            12777 |
| 20m_rejected_sweep_long      | 2025_train |    12091 |     27.83 |      -112.84  |           0.16  |        1.36435e+06 |               -259.97 |             8726 |
| 20m_rejected_sweep_short     | 2025_train |    11622 |     26.85 |      -112.289 |           0.154 |        1.30504e+06 |               -257.75 |             8501 |
| 5min_close_breakout_long     | 2025_train |     5027 |     25.24 |      -123.614 |           0.137 |   621407           |               -258.34 |             3758 |
| 5min_close_breakout_short    | 2025_train |     5454 |     26.51 |      -120.513 |           0.151 |   657278           |               -264.33 |             4008 |
| 60m_rejected_sweep_long      | 2025_train |     4614 |     27.39 |      -113.648 |           0.157 |   524373           |               -258.42 |             3350 |
| 60m_rejected_sweep_short     | 2025_train |     4272 |     26.54 |      -111.318 |           0.153 |   475663           |               -257.75 |             3138 |
| compression_break_long       | 2025_train |     1577 |     21.62 |      -121.225 |           0.112 |   191171           |               -257.48 |             1236 |
| compression_break_short      | 2025_train |     1692 |     21.57 |      -118.62  |           0.117 |   201043           |               -263.88 |             1327 |
| every_minute_long            | 2025_train |   108487 |     30.68 |      -115.124 |           0.175 |        1.24895e+07 |               -856.69 |            75206 |
| every_minute_short           | 2025_train |   108445 |     30.94 |      -114.146 |           0.177 |        1.23786e+07 |              -1725.2  |            74894 |
| strong_burst_long            | 2025_train |    12670 |     25.82 |      -117.207 |           0.145 |        1.48502e+06 |               -264.4  |             9399 |
| strong_burst_short           | 2025_train |    13203 |     25.66 |      -117.802 |           0.143 |        1.55541e+06 |               -282.04 |             9815 |
| trend_pullback_reclaim_long  | 2025_train |    14623 |     26.88 |      -116.841 |           0.151 |        1.70857e+06 |               -281.74 |            10692 |
| trend_pullback_reclaim_short | 2025_train |    15537 |     28.6  |      -112.661 |           0.168 |        1.75043e+06 |               -265.25 |            11093 |

## Rankings from 2025 training only (not evidence of future profitability)
| rule                         |   trades |   avg_net_pts |   win_pct |   losses_or_flat |
|:-----------------------------|---------:|--------------:|----------:|-----------------:|
| 60m_rejected_sweep_short     |     4272 |      -111.318 |     26.54 |             3138 |
| 20m_rejected_sweep_short     |    11622 |      -112.289 |     26.85 |             8501 |
| trend_pullback_reclaim_short |    15537 |      -112.661 |     28.6  |            11093 |
| 20m_rejected_sweep_long      |    12091 |      -112.84  |     27.83 |             8726 |
| 60m_rejected_sweep_long      |     4614 |      -113.648 |     27.39 |             3350 |
| every_minute_short           |   108445 |      -114.146 |     30.94 |            74894 |
| every_minute_long            |   108487 |      -115.124 |     30.68 |            75206 |
| trend_pullback_reclaim_long  |    14623 |      -116.841 |     26.88 |            10692 |
| strong_burst_long            |    12670 |      -117.207 |     25.82 |             9399 |
| strong_burst_short           |    13203 |      -117.802 |     25.66 |             9815 |
| compression_break_short      |     1692 |      -118.62  |     21.57 |             1327 |
| 20m_accepted_breakout_short  |    17396 |      -118.881 |     26.55 |            12777 |
| 20m_accepted_breakout_long   |    16422 |      -119.619 |     26    |            12152 |
| 5min_close_breakout_short    |     5454 |      -120.513 |     26.51 |             4008 |
| compression_break_long       |     1577 |      -121.225 |     21.62 |             1236 |
| 15min_close_breakout_short   |     1801 |      -122.227 |     27.48 |             1306 |

## Reproducible audit artifacts
- every_candle_directional_labels.csv.gz (one entry time per long/short case)
- all_candle_conditional_rates.csv
- new_york_hour_profile.csv
- trade_ledger.csv.gz (one open trade at a time per independently measured setup)
- trade_summary.csv
- zero_loss_candidates.csv (may contain header only)
- quality.json (archive gaps, fees, exact sample counts)

## Safeguards / limitations
- No historical bid/ask quote, order-book depth or intraminute tick path
- Favorable target may be unfillable at modeled high/low
- Missing source minutes not fabricated; skip signals spanning gaps
- All four historical splits are used for exploratory research, not pristine forward testing
- Overlapping minute labels produce severely correlated observations
- Fee voucher credits are not counted as cash; historical Scalper Offer unknown
- Funding, market impact, liquidation, capital and margin not reconstructed
- No ability to guarantee a 200-point move without losses
- Only rule-based subset scanned; many possible rules not tested
- 200 BTC points represents quote-price move, not dollar account P&L

Conclusions must come from the actual table, not from choosing perfect historical candles.
