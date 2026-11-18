# Stage19 — Find at least +10% net BTC account return EVERY calendar month

## Hard target
At least 10% account NAV return after taker fees/GST/slippage in
every COMPLETE month of 2025 and Jan–Oct 2026. Zero-trade and
negative months never pass. No requirement of limited trades/day.

## Methods
6 fully specified 5m intraday price action patterns, 1H confirm
optional, structure or volatility stops, 2R/3R targets, 2h/4h max
holds, every 1m candle checks exits, one open position at once.
Account leverage cap: 5x/10x/20x; risk budget: 0.5/1/2/3/5 percent.

**Strategies achieving 10% in every complete month: 0 / 1440**

## Best ranked on 2025 only, then 2026 comparison
| pattern           | trend_filter   | stop_mode   |   reward_R |   hold_min |   target_trade_risk_pct |   max_notional_leverage |   trades |   months_10pct_2025 |   months_10pct_2026 |   months_positive_2025 |   months_positive_2026 |   worst_month_2025_pct |   worst_month_2026_pct |   nav_return_2025_pct |   nav_return_2026_pct |   max_trade_equity_drawdown_pct |
|:------------------|:---------------|:------------|-----------:|-----------:|------------------------:|------------------------:|---------:|--------------------:|--------------------:|-----------------------:|-----------------------:|-----------------------:|-----------------------:|----------------------:|----------------------:|--------------------------------:|
| compression_break | hour_align     | atr1p5      |          3 |        240 |                       3 |                       5 |      549 |                   3 |                   0 |                      4 |                      1 |                -24.452 |                -40.55  |               -62.258 |               -86.494 |                          95.097 |
| compression_break | hour_align     | atr1p5      |          3 |        240 |                       5 |                      10 |      549 |                   3 |                   1 |                      4 |                      1 |                -43.621 |                -63.802 |               -89.152 |               -98.291 |                          99.828 |
| compression_break | hour_align     | atr1p5      |          3 |        240 |                       3 |                      20 |      549 |                   3 |                   1 |                      4 |                      1 |                -44.974 |                -66.62  |               -91.29  |               -98.347 |                          99.866 |
| compression_break | hour_align     | atr1p5      |          3 |        120 |                       5 |                      10 |      560 |                   3 |                   0 |                      4 |                      1 |                -52.67  |                -64.674 |               -92.708 |               -98.798 |                          99.919 |
| compression_break | hour_align     | atr1p5      |          3 |        240 |                       5 |                      20 |      549 |                   3 |                   1 |                      4 |                      1 |                -60.72  |                -78.335 |               -98.065 |               -99.817 |                          99.997 |
| compression_break | hour_align     | atr1p5      |          3 |        240 |                       5 |                       5 |      549 |                   3 |                   0 |                      3 |                      1 |                -24.595 |                -41.443 |               -60.196 |               -87.813 |                          95.334 |
| compression_break | hour_align     | structure3  |          2 |        240 |                       5 |                      10 |      493 |                   3 |                   1 |                      3 |                      2 |                -47.518 |                -49.247 |               -90.963 |               -93.676 |                          99.499 |
| compression_break | hour_align     | atr1p5      |          3 |        240 |                       2 |                       5 |      549 |                   2 |                   0 |                      4 |                      1 |                -23.076 |                -37.307 |               -61.395 |               -83.619 |                          93.917 |
| compression_break | hour_align     | atr1p5      |          3 |        120 |                       2 |                       5 |      560 |                   2 |                   0 |                      4 |                      1 |                -29.394 |                -38.117 |               -67.732 |               -86.225 |                          95.724 |
| compression_break | hour_align     | atr1p5      |          3 |        120 |                       3 |                       5 |      560 |                   2 |                   0 |                      4 |                      1 |                -31.115 |                -41.21  |               -70.296 |               -88.777 |                          96.793 |
| compression_break | hour_align     | structure3  |          3 |        240 |                       5 |                       5 |      483 |                   2 |                   1 |                      4 |                      1 |                -35.545 |                -32.651 |               -72.044 |               -80.829 |                          95.114 |
| compression_break | hour_align     | atr1p5      |          3 |        240 |                       2 |                      10 |      549 |                   2 |                   1 |                      4 |                      1 |                -31.939 |                -46.859 |               -77.196 |               -91.639 |                          98.187 |
| compression_break | hour_align     | atr1p5      |          3 |        240 |                       2 |                      20 |      549 |                   2 |                   1 |                      4 |                      1 |                -32.121 |                -52.598 |               -78.648 |               -93.106 |                          98.6   |
| compression_break | hour_align     | atr1p5      |          3 |        120 |                       2 |                      10 |      560 |                   2 |                   0 |                      4 |                      1 |                -38.328 |                -47.75  |               -81.184 |               -93.691 |                          98.871 |
| compression_break | hour_align     | atr1p5      |          3 |        120 |                       2 |                      20 |      560 |                   2 |                   0 |                      4 |                      1 |                -41.325 |                -53.392 |               -82.382 |               -94.859 |                          99.139 |
| compression_break | hour_align     | atr1p5      |          3 |        240 |                       3 |                      10 |      549 |                   2 |                   1 |                      4 |                      1 |                -39.304 |                -56.229 |               -85.333 |               -96.285 |                          99.494 |
| compression_break | hour_align     | atr1p5      |          3 |        120 |                       3 |                      10 |      560 |                   2 |                   0 |                      4 |                      1 |                -46.835 |                -57.336 |               -88.827 |               -97.291 |                          99.719 |
| compression_break | hour_align     | atr1p5      |          3 |        120 |                       3 |                      20 |      560 |                   2 |                   0 |                      4 |                      1 |                -55.109 |                -67.464 |               -93.408 |               -98.926 |                          99.934 |
| compression_break | hour_align     | structure3  |          3 |        120 |                       2 |                       5 |      503 |                   2 |                   1 |                      3 |                      2 |                -36.284 |                -23.781 |               -64.729 |               -74.594 |                          91.54  |
| compression_break | hour_align     | structure3  |          2 |        240 |                       3 |                       5 |      493 |                   2 |                   1 |                      3 |                      2 |                -26.689 |                -30.025 |               -67.685 |               -75.495 |                          92.687 |

## Best drawdown-bounded 2025 candidate monthly account returns
| pattern           | trend_filter   | stop_mode   |   reward_R |   hold_min |   target_trade_risk_pct |   max_notional_leverage | month_ist   |   trades |   net_account_return_pct | status      |
|:------------------|:---------------|:------------|-----------:|-----------:|------------------------:|------------------------:|:------------|---------:|-------------------------:|:------------|
| compression_break | hour_align     | atr1p5      |          3 |        240 |                       3 |                       5 | 2025-01     |       23 |                 -23.8057 | Loss        |
| compression_break | hour_align     | atr1p5      |          3 |        240 |                       3 |                       5 | 2025-02     |       12 |                   0.969  | Profit <10% |
| compression_break | hour_align     | atr1p5      |          3 |        240 |                       3 |                       5 | 2025-03     |       12 |                 -12.0327 | Loss        |
| compression_break | hour_align     | atr1p5      |          3 |        240 |                       3 |                       5 | 2025-04     |       22 |                 -10.05   | Loss        |
| compression_break | hour_align     | atr1p5      |          3 |        240 |                       3 |                       5 | 2025-05     |       29 |                  22.6089 | >=10%       |
| compression_break | hour_align     | atr1p5      |          3 |        240 |                       3 |                       5 | 2025-06     |       16 |                 -12.5501 | Loss        |
| compression_break | hour_align     | atr1p5      |          3 |        240 |                       3 |                       5 | 2025-07     |       30 |                 -11.2081 | Loss        |
| compression_break | hour_align     | atr1p5      |          3 |        240 |                       3 |                       5 | 2025-08     |       23 |                  17.4493 | >=10%       |
| compression_break | hour_align     | atr1p5      |          3 |        240 |                       3 |                       5 | 2025-09     |       18 |                 -21.8688 | Loss        |
| compression_break | hour_align     | atr1p5      |          3 |        240 |                       3 |                       5 | 2025-10     |       22 |                  16.4432 | >=10%       |
| compression_break | hour_align     | atr1p5      |          3 |        240 |                       3 |                       5 | 2025-11     |       27 |                 -24.4523 | Loss        |
| compression_break | hour_align     | atr1p5      |          3 |        240 |                       3 |                       5 | 2025-12     |       29 |                 -19.3277 | Loss        |
| compression_break | hour_align     | atr1p5      |          3 |        240 |                       3 |                       5 | 2026-01     |       39 |                 -40.5499 | Loss        |
| compression_break | hour_align     | atr1p5      |          3 |        240 |                       3 |                       5 | 2026-02     |       27 |                 -17.9593 | Loss        |
| compression_break | hour_align     | atr1p5      |          3 |        240 |                       3 |                       5 | 2026-03     |       23 |                 -14.2808 | Loss        |
| compression_break | hour_align     | atr1p5      |          3 |        240 |                       3 |                       5 | 2026-04     |       27 |                  -5.9521 | Loss        |
| compression_break | hour_align     | atr1p5      |          3 |        240 |                       3 |                       5 | 2026-05     |       29 |                 -19.757  | Loss        |
| compression_break | hour_align     | atr1p5      |          3 |        240 |                       3 |                       5 | 2026-06     |       30 |                 -31.2673 | Loss        |
| compression_break | hour_align     | atr1p5      |          3 |        240 |                       3 |                       5 | 2026-07     |       28 |                   6.8379 | Profit <10% |
| compression_break | hour_align     | atr1p5      |          3 |        240 |                       3 |                       5 | 2026-08     |       32 |                 -20.9882 | Loss        |
| compression_break | hour_align     | atr1p5      |          3 |        240 |                       3 |                       5 | 2026-09     |       26 |                 -10.7342 | Loss        |
| compression_break | hour_align     | atr1p5      |          3 |        240 |                       3 |                       5 | 2026-10     |       25 |                 -17.3511 | Loss        |
| compression_break | hour_align     | atr1p5      |          3 |        240 |                       3 |                       5 | 2026-11     |        0 |                   0      | No trades   |

## Limitations
- All historical months have been examined during prior research; NOT a blind OOS test
- No guarantee every future month will gain >=10%; target is extremely aggressive
- Real contracts have discrete lot sizes, minimum margin, exchange risk limits and liquidation
- No funding, actual bid-ask spread, market impact or forced liquidation modeled
- 1m OHLC stop-first, adverse gap stops, trades enter only AFTER 5m completion
- One position open at a time per independent setting, no fixed trade/day limit
- Trade risk 3% or 5% can produce large drawdowns and is not recommended
- Maximum leverage cap is an assumption, not confirmation actual position can open
- 2026-10-31 entire UTC day missing, November 2026 ends on 16th
- Realized PNL is counted in the actual IST EXIT month
- No-trade months count as misses of the 10% target
- Every scenario's monthly return is AFTER modeled taker/GST/slippage costs
- Equity drawdown sampled on each trade close; OPEN position drawdowns may be worse

All result files committed. Raw trade and entry ledgers stored as GitHub Actions artifacts.
