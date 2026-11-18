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
| pattern        | trend_filter   | stop_mode   |   reward_R |   hold_min |   target_trade_risk_pct |   max_notional_leverage |   trades |   months_10pct_2025 |   months_10pct_2026 |   months_positive_2025 |   months_positive_2026 |   worst_month_2025_pct |   worst_month_2026_pct |   nav_return_2025_pct |   nav_return_2026_pct |   max_trade_equity_drawdown_pct |
|:---------------|:---------------|:------------|-----------:|-----------:|------------------------:|------------------------:|---------:|--------------------:|--------------------:|-----------------------:|-----------------------:|-----------------------:|-----------------------:|----------------------:|----------------------:|--------------------------------:|
| sweep_reversal | hour_align     | structure3  |          3 |        120 |                       2 |                       5 |      579 |                   1 |                   1 |                      1 |                      1 |                -31.923 |                -25.799 |               -90.113 |               -66.949 |                          97.014 |
| sweep_reversal | hour_align     | structure3  |          3 |        120 |                       3 |                       5 |      579 |                   1 |                   1 |                      1 |                      2 |                -33.392 |                -25.726 |               -91.187 |               -68.595 |                          97.474 |
| sweep_reversal | hour_align     | structure3  |          3 |        240 |                       2 |                       5 |      577 |                   1 |                   1 |                      1 |                      3 |                -32.33  |                -18.687 |               -91.533 |               -60.252 |                          96.906 |
| sweep_reversal | hour_align     | structure3  |          3 |        120 |                       5 |                       5 |      579 |                   1 |                   1 |                      1 |                      2 |                -34.526 |                -26.073 |               -91.549 |               -68.805 |                          97.594 |
| sweep_reversal | hour_align     | structure3  |          3 |        240 |                       3 |                       5 |      577 |                   1 |                   1 |                      1 |                      3 |                -34.16  |                -20.812 |               -92.69  |               -61.803 |                          97.461 |
| sweep_reversal | hour_align     | structure3  |          3 |        240 |                       5 |                       5 |      577 |                   1 |                   1 |                      1 |                      3 |                -35.28  |                -22.653 |               -93.144 |               -62.202 |                          97.643 |
| sweep_reversal | hour_align     | atr1p5      |          2 |        120 |                       2 |                       5 |      963 |                   1 |                   0 |                      1 |                      0 |                -36.526 |                -32.845 |               -96.985 |               -92.107 |                          99.773 |
| sweep_reversal | hour_align     | atr1p5      |          2 |        120 |                       3 |                       5 |      963 |                   1 |                   0 |                      1 |                      0 |                -37.578 |                -32.979 |               -97.272 |               -92.746 |                          99.812 |
| sweep_reversal | hour_align     | atr1p5      |          2 |        120 |                       5 |                       5 |      963 |                   1 |                   0 |                      1 |                      0 |                -37.982 |                -32.878 |               -97.358 |               -92.979 |                          99.823 |
| sweep_reversal | hour_align     | atr1p5      |          2 |        240 |                       5 |                       5 |      951 |                   1 |                   0 |                      1 |                      0 |                -37.812 |                -31.51  |               -97.871 |               -91.056 |                          99.82  |
| sweep_reversal | hour_align     | structure3  |          3 |        120 |                       2 |                      10 |      579 |                   1 |                   1 |                      1 |                      1 |                -48.385 |                -42.549 |               -98.514 |               -84.121 |                          99.794 |
| sweep_reversal | hour_align     | structure3  |          2 |        120 |                       3 |                      10 |      579 |                   1 |                   0 |                      1 |                      1 |                -53.065 |                -38.129 |               -98.544 |               -89.413 |                          99.865 |
| sweep_reversal | hour_align     | structure3  |          2 |        240 |                       3 |                      10 |      578 |                   1 |                   0 |                      1 |                      2 |                -54.431 |                -34.595 |               -98.805 |               -87.633 |                          99.872 |
| sweep_reversal | hour_align     | structure3  |          3 |        120 |                       3 |                      10 |      579 |                   1 |                   1 |                      1 |                      1 |                -51.066 |                -45.828 |               -98.998 |               -88.741 |                          99.904 |
| sweep_reversal | hour_align     | structure3  |          3 |        240 |                       3 |                      10 |      577 |                   1 |                   1 |                      1 |                      2 |                -51.765 |                -36.883 |               -99.238 |               -84.227 |                          99.896 |
| sweep_reversal | hour_align     | structure3  |          3 |        120 |                       5 |                      10 |      579 |                   1 |                   1 |                      1 |                      1 |                -55.518 |                -45.044 |               -99.277 |               -90.451 |                          99.943 |
| sweep_reversal | hour_align     | structure3  |          3 |        240 |                       5 |                      10 |      577 |                   1 |                   1 |                      1 |                      3 |                -56.413 |                -36.014 |               -99.512 |               -86.153 |                          99.944 |
| sweep_reversal | hour_align     | atr1p5      |          2 |        120 |                       3 |                      10 |      963 |                   1 |                   0 |                      1 |                      0 |                -58.85  |                -54.553 |               -99.901 |               -99.33  |                          99.999 |
| sweep_reversal | hour_align     | atr1p5      |          2 |        240 |                       3 |                      10 |      951 |                   1 |                   0 |                      1 |                      0 |                -59.314 |                -52.584 |               -99.921 |               -99.068 |                          99.999 |
| sweep_reversal | hour_align     | atr1p5      |          2 |        120 |                       5 |                      10 |      963 |                   1 |                   0 |                      1 |                      0 |                -61.201 |                -55.552 |               -99.933 |               -99.496 |                         100     |

## Best drawdown-bounded 2025 candidate monthly account returns
| pattern        | trend_filter   | stop_mode   |   reward_R |   hold_min |   target_trade_risk_pct |   max_notional_leverage | month_ist   |   trades |   net_account_return_pct | status   |
|:---------------|:---------------|:------------|-----------:|-----------:|------------------------:|------------------------:|:------------|---------:|-------------------------:|:---------|
| sweep_reversal | hour_align     | structure3  |          3 |        120 |                       2 |                       5 | 2025-01     |       27 |                 -17.4216 | Loss     |
| sweep_reversal | hour_align     | structure3  |          3 |        120 |                       2 |                       5 | 2025-02     |       19 |                 -21.827  | Loss     |
| sweep_reversal | hour_align     | structure3  |          3 |        120 |                       2 |                       5 | 2025-03     |       28 |                 -21.3125 | Loss     |
| sweep_reversal | hour_align     | structure3  |          3 |        120 |                       2 |                       5 | 2025-04     |       33 |                 -13.1902 | Loss     |
| sweep_reversal | hour_align     | structure3  |          3 |        120 |                       2 |                       5 | 2025-05     |       39 |                 -31.923  | Loss     |
| sweep_reversal | hour_align     | structure3  |          3 |        120 |                       2 |                       5 | 2025-06     |       21 |                 -18.8074 | Loss     |
| sweep_reversal | hour_align     | structure3  |          3 |        120 |                       2 |                       5 | 2025-07     |       41 |                 -29.4219 | Loss     |
| sweep_reversal | hour_align     | structure3  |          3 |        120 |                       2 |                       5 | 2025-08     |       38 |                 -12.8297 | Loss     |
| sweep_reversal | hour_align     | structure3  |          3 |        120 |                       2 |                       5 | 2025-09     |       28 |                 -18.5641 | Loss     |
| sweep_reversal | hour_align     | structure3  |          3 |        120 |                       2 |                       5 | 2025-10     |       34 |                 -11.5378 | Loss     |
| sweep_reversal | hour_align     | structure3  |          3 |        120 |                       2 |                       5 | 2025-11     |       29 |                  14.6515 | >=10%    |
| sweep_reversal | hour_align     | structure3  |          3 |        120 |                       2 |                       5 | 2025-12     |       29 |                 -20.1677 | Loss     |
| sweep_reversal | hour_align     | structure3  |          3 |        120 |                       2 |                       5 | 2026-01     |       38 |                 -25.7993 | Loss     |
| sweep_reversal | hour_align     | structure3  |          3 |        120 |                       2 |                       5 | 2026-02     |       21 |                  -4.4599 | Loss     |
| sweep_reversal | hour_align     | structure3  |          3 |        120 |                       2 |                       5 | 2026-03     |       25 |                 -15.7832 | Loss     |
| sweep_reversal | hour_align     | structure3  |          3 |        120 |                       2 |                       5 | 2026-04     |       19 |                 -17.2607 | Loss     |
| sweep_reversal | hour_align     | structure3  |          3 |        120 |                       2 |                       5 | 2026-05     |       19 |                  10.8775 | >=10%    |
| sweep_reversal | hour_align     | structure3  |          3 |        120 |                       2 |                       5 | 2026-06     |       26 |                 -18.8631 | Loss     |
| sweep_reversal | hour_align     | structure3  |          3 |        120 |                       2 |                       5 | 2026-07     |       15 |                  -8.0206 | Loss     |
| sweep_reversal | hour_align     | structure3  |          3 |        120 |                       2 |                       5 | 2026-08     |       10 |                  -1.3462 | Loss     |
| sweep_reversal | hour_align     | structure3  |          3 |        120 |                       2 |                       5 | 2026-09     |       19 |                 -16.2879 | Loss     |
| sweep_reversal | hour_align     | structure3  |          3 |        120 |                       2 |                       5 | 2026-10     |       15 |                  -2.0891 | Loss     |
| sweep_reversal | hour_align     | structure3  |          3 |        120 |                       2 |                       5 | 2026-11     |        6 |                  -6.5847 | Loss     |

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
