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
| compression_break | hour_align     | atr1p5      |          3 |        240 |                       3 |                       5 |      562 |                   3 |                   0 |                      4 |                      1 |                -23.806 |                -39.74  |               -62.561 |               -86.31  |                          95.678 |
| compression_break | hour_align     | atr1p5      |          3 |        240 |                       5 |                      10 |      562 |                   3 |                   1 |                      4 |                      1 |                -41.683 |                -62.802 |               -89.329 |               -98.244 |                          99.868 |
| compression_break | hour_align     | atr1p5      |          3 |        240 |                       3 |                      20 |      562 |                   3 |                   1 |                      4 |                      1 |                -45.519 |                -64.725 |               -91.213 |               -98.253 |                          99.9   |
| compression_break | hour_align     | atr1p5      |          3 |        120 |                       5 |                      10 |      574 |                   3 |                   0 |                      4 |                      1 |                -54.989 |                -64.511 |               -92.827 |               -98.792 |                          99.94  |
| compression_break | hour_align     | atr1p5      |          3 |        240 |                       5 |                      20 |      562 |                   3 |                   1 |                      4 |                      1 |                -60.72  |                -77.104 |               -98.068 |               -99.806 |                          99.998 |
| compression_break | hour_align     | atr1p5      |          3 |        240 |                       5 |                       5 |      562 |                   3 |                   0 |                      3 |                      1 |                -24.595 |                -40.646 |               -60.515 |               -87.647 |                          95.887 |
| compression_break | hour_align     | structure3  |          2 |        240 |                       5 |                      10 |      503 |                   3 |                   1 |                      3 |                      2 |                -47.518 |                -49.247 |               -91.181 |               -93.665 |                          99.601 |
| compression_break | hour_align     | atr1p5      |          3 |        240 |                       2 |                       5 |      562 |                   2 |                   0 |                      4 |                      1 |                -23.076 |                -36.453 |               -61.704 |               -83.396 |                          94.675 |
| compression_break | hour_align     | atr1p5      |          3 |        120 |                       2 |                       5 |      574 |                   2 |                   0 |                      4 |                      1 |                -31.123 |                -37.976 |               -67.99  |               -86.194 |                          96.324 |
| compression_break | hour_align     | atr1p5      |          3 |        120 |                       3 |                       5 |      574 |                   2 |                   0 |                      4 |                      1 |                -32.803 |                -41.076 |               -70.534 |               -88.751 |                          97.238 |
| compression_break | hour_align     | structure3  |          3 |        240 |                       5 |                       5 |      493 |                   2 |                   1 |                      4 |                      1 |                -37.886 |                -32.651 |               -72.541 |               -80.811 |                          95.784 |
| compression_break | hour_align     | atr1p5      |          3 |        240 |                       2 |                      10 |      562 |                   2 |                   1 |                      4 |                      1 |                -31.939 |                -45.392 |               -77.065 |               -91.408 |                          98.511 |
| compression_break | hour_align     | atr1p5      |          3 |        240 |                       2 |                      20 |      562 |                   2 |                   1 |                      4 |                      1 |                -33.181 |                -50.692 |               -78.525 |               -92.829 |                          98.839 |
| compression_break | hour_align     | atr1p5      |          3 |        120 |                       2 |                      10 |      574 |                   2 |                   0 |                      4 |                      1 |                -40.007 |                -47.508 |               -81.076 |               -93.662 |                          99.077 |
| compression_break | hour_align     | atr1p5      |          3 |        120 |                       2 |                      20 |      574 |                   2 |                   0 |                      4 |                      1 |                -42.923 |                -53.081 |               -82.281 |               -94.825 |                          99.295 |
| compression_break | hour_align     | atr1p5      |          3 |        240 |                       3 |                      10 |      562 |                   2 |                   1 |                      4 |                      1 |                -39.304 |                -55.021 |               -85.448 |               -96.183 |                          99.612 |
| compression_break | hour_align     | atr1p5      |          3 |        120 |                       3 |                      10 |      574 |                   2 |                   0 |                      4 |                      1 |                -49.007 |                -57.138 |               -88.915 |               -97.278 |                          99.788 |
| compression_break | hour_align     | atr1p5      |          3 |        120 |                       3 |                      20 |      574 |                   2 |                   0 |                      4 |                      1 |                -56.943 |                -67.155 |               -93.35  |               -98.916 |                          99.952 |
| compression_break | hour_align     | structure3  |          3 |        120 |                       2 |                       5 |      513 |                   2 |                   1 |                      3 |                      2 |                -37.193 |                -23.414 |               -64.563 |               -74.471 |                          92.265 |
| compression_break | hour_align     | structure3  |          2 |        240 |                       3 |                       5 |      503 |                   2 |                   1 |                      3 |                      2 |                -26.689 |                -30.025 |               -68.26  |               -75.472 |                          93.488 |

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
| compression_break | hour_align     | atr1p5      |          3 |        240 |                       3 |                       5 | 2025-11     |       26 |                 -23.176  | Loss        |
| compression_break | hour_align     | atr1p5      |          3 |        240 |                       3 |                       5 | 2025-12     |       30 |                 -21.3037 | Loss        |
| compression_break | hour_align     | atr1p5      |          3 |        240 |                       3 |                       5 | 2026-01     |       38 |                 -39.7404 | Loss        |
| compression_break | hour_align     | atr1p5      |          3 |        240 |                       3 |                       5 | 2026-02     |       27 |                 -17.9593 | Loss        |
| compression_break | hour_align     | atr1p5      |          3 |        240 |                       3 |                       5 | 2026-03     |       23 |                 -14.2808 | Loss        |
| compression_break | hour_align     | atr1p5      |          3 |        240 |                       3 |                       5 | 2026-04     |       27 |                  -5.9521 | Loss        |
| compression_break | hour_align     | atr1p5      |          3 |        240 |                       3 |                       5 | 2026-05     |       29 |                 -19.757  | Loss        |
| compression_break | hour_align     | atr1p5      |          3 |        240 |                       3 |                       5 | 2026-06     |       30 |                 -31.2673 | Loss        |
| compression_break | hour_align     | atr1p5      |          3 |        240 |                       3 |                       5 | 2026-07     |       28 |                   6.8379 | Profit <10% |
| compression_break | hour_align     | atr1p5      |          3 |        240 |                       3 |                       5 | 2026-08     |       32 |                 -20.9882 | Loss        |
| compression_break | hour_align     | atr1p5      |          3 |        240 |                       3 |                       5 | 2026-09     |       26 |                 -10.7342 | Loss        |
| compression_break | hour_align     | atr1p5      |          3 |        240 |                       3 |                       5 | 2026-10     |       25 |                 -17.3511 | Loss        |
| compression_break | hour_align     | atr1p5      |          3 |        240 |                       3 |                       5 | 2026-11     |       14 |                 -12.3366 | Loss        |

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
