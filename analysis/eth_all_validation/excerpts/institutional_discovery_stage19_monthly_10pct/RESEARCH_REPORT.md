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

**Strategies achieving 10% in every complete month: 0 / 1080**

## Best ranked on 2025 only, then 2026 comparison
| pattern        | trend_filter   | stop_mode   |   reward_R |   hold_min |   target_trade_risk_pct |   max_notional_leverage |   trades |   months_10pct_2025 |   months_10pct_2026 |   months_positive_2025 |   months_positive_2026 |   worst_month_2025_pct |   worst_month_2026_pct |   nav_return_2025_pct |   nav_return_2026_pct |   max_trade_equity_drawdown_pct |
|:---------------|:---------------|:------------|-----------:|-----------:|------------------------:|------------------------:|---------:|--------------------:|--------------------:|-----------------------:|-----------------------:|-----------------------:|-----------------------:|----------------------:|----------------------:|--------------------------------:|
| range_breakout | any            | structure3  |          3 |        240 |                       5 |                       5 |       14 |                   2 |                   0 |                      5 |                      1 |                 -5.559 |                 -3.165 |                35.929 |                -3.169 |                          11.271 |
| range_breakout | any            | structure3  |          3 |        240 |                       5 |                      10 |       14 |                   2 |                   0 |                      5 |                      1 |                 -5.559 |                 -3.165 |                35.929 |                -3.169 |                          11.271 |
| range_breakout | any            | structure3  |          3 |        240 |                       5 |                      20 |       14 |                   2 |                   0 |                      5 |                      1 |                 -5.559 |                 -3.165 |                35.929 |                -3.169 |                          11.271 |
| range_breakout | hour_align     | structure3  |          3 |        240 |                       5 |                       5 |        6 |                   2 |                   0 |                      3 |                      0 |                  0     |                 -3.165 |                32.622 |                -3.517 |                           3.517 |
| range_breakout | hour_align     | structure3  |          3 |        240 |                       5 |                      10 |        6 |                   2 |                   0 |                      3 |                      0 |                  0     |                 -3.165 |                32.622 |                -3.517 |                           3.517 |
| range_breakout | hour_align     | structure3  |          3 |        240 |                       5 |                      20 |        6 |                   2 |                   0 |                      3 |                      0 |                  0     |                 -3.165 |                32.622 |                -3.517 |                           3.517 |
| range_breakout | any            | structure3  |          2 |        240 |                       5 |                       5 |       15 |                   1 |                   0 |                      5 |                      1 |                 -5.559 |                 -3.165 |                32.498 |                -3.169 |                          11.271 |
| range_breakout | any            | structure3  |          2 |        240 |                       5 |                      10 |       15 |                   1 |                   0 |                      5 |                      1 |                 -5.559 |                 -3.165 |                32.498 |                -3.169 |                          11.271 |
| range_breakout | any            | structure3  |          2 |        240 |                       5 |                      20 |       15 |                   1 |                   0 |                      5 |                      1 |                 -5.559 |                 -3.165 |                32.498 |                -3.169 |                          11.271 |
| range_breakout | any            | structure3  |          3 |        120 |                       5 |                       5 |       14 |                   1 |                   0 |                      5 |                      0 |                 -5.559 |                 -3.444 |                17.389 |                -5.417 |                          13.333 |
| range_breakout | any            | structure3  |          3 |        120 |                       5 |                      10 |       14 |                   1 |                   0 |                      5 |                      0 |                 -5.559 |                 -3.444 |                17.389 |                -5.417 |                          13.333 |
| range_breakout | any            | structure3  |          3 |        120 |                       5 |                      20 |       14 |                   1 |                   0 |                      5 |                      0 |                 -5.559 |                 -3.444 |                17.389 |                -5.417 |                          13.333 |
| range_breakout | hour_align     | structure3  |          3 |        120 |                       5 |                       5 |        6 |                   1 |                   0 |                      2 |                      0 |                 -0.946 |                 -3.444 |                20.676 |                -4.32  |                           5.225 |
| range_breakout | hour_align     | structure3  |          3 |        120 |                       5 |                      10 |        6 |                   1 |                   0 |                      2 |                      0 |                 -0.946 |                 -3.444 |                20.676 |                -4.32  |                           5.225 |
| range_breakout | hour_align     | structure3  |          3 |        120 |                       5 |                      20 |        6 |                   1 |                   0 |                      2 |                      0 |                 -0.946 |                 -3.444 |                20.676 |                -4.32  |                           5.225 |
| trend_engulf   | hour_align     | structure3  |          3 |        240 |                       5 |                       5 |        2 |                   1 |                   0 |                      2 |                      0 |                  0     |                  0     |                15.521 |                 0     |                           0     |
| trend_engulf   | hour_align     | structure3  |          3 |        240 |                       5 |                      10 |        2 |                   1 |                   0 |                      2 |                      0 |                  0     |                  0     |                15.521 |                 0     |                           0     |
| trend_engulf   | hour_align     | structure3  |          3 |        240 |                       5 |                      20 |        2 |                   1 |                   0 |                      2 |                      0 |                  0     |                  0     |                15.521 |                 0     |                           0     |
| trend_engulf   | any            | structure3  |          3 |        240 |                       5 |                       5 |        3 |                   1 |                   0 |                      2 |                      0 |                  0     |                  0     |                12.086 |                 0     |                           2.974 |
| trend_engulf   | any            | structure3  |          3 |        240 |                       5 |                      10 |        3 |                   1 |                   0 |                      2 |                      0 |                  0     |                  0     |                12.086 |                 0     |                           2.974 |

## Best drawdown-bounded 2025 candidate monthly account returns
| pattern        | trend_filter   | stop_mode   |   reward_R |   hold_min |   target_trade_risk_pct |   max_notional_leverage | month_ist   |   trades |   net_account_return_pct | status      |
|:---------------|:---------------|:------------|-----------:|-----------:|------------------------:|------------------------:|:------------|---------:|-------------------------:|:------------|
| range_breakout | any            | structure3  |          3 |        240 |                       5 |                       5 | 2025-01     |        2 |                   5.1343 | Profit <10% |
| range_breakout | any            | structure3  |          3 |        240 |                       5 |                       5 | 2025-02     |        1 |                  14.5634 | >=10%       |
| range_breakout | any            | structure3  |          3 |        240 |                       5 |                       5 | 2025-03     |        1 |                   0.8696 | Profit <10% |
| range_breakout | any            | structure3  |          3 |        240 |                       5 |                       5 | 2025-04     |        0 |                   0      | No trades   |
| range_breakout | any            | structure3  |          3 |        240 |                       5 |                       5 | 2025-05     |        0 |                   0      | No trades   |
| range_breakout | any            | structure3  |          3 |        240 |                       5 |                       5 | 2025-06     |        0 |                   0      | No trades   |
| range_breakout | any            | structure3  |          3 |        240 |                       5 |                       5 | 2025-07     |        0 |                   0      | No trades   |
| range_breakout | any            | structure3  |          3 |        240 |                       5 |                       5 | 2025-08     |        2 |                  10.9226 | >=10%       |
| range_breakout | any            | structure3  |          3 |        240 |                       5 |                       5 | 2025-09     |        0 |                   0      | No trades   |
| range_breakout | any            | structure3  |          3 |        240 |                       5 |                       5 | 2025-10     |        4 |                   6.8018 | Profit <10% |
| range_breakout | any            | structure3  |          3 |        240 |                       5 |                       5 | 2025-11     |        0 |                   0      | No trades   |
| range_breakout | any            | structure3  |          3 |        240 |                       5 |                       5 | 2025-12     |        1 |                  -5.5588 | Loss        |
| range_breakout | any            | structure3  |          3 |        240 |                       5 |                       5 | 2026-01     |        0 |                   0      | No trades   |
| range_breakout | any            | structure3  |          3 |        240 |                       5 |                       5 | 2026-02     |        0 |                   0      | No trades   |
| range_breakout | any            | structure3  |          3 |        240 |                       5 |                       5 | 2026-03     |        1 |                   0.3608 | Profit <10% |
| range_breakout | any            | structure3  |          3 |        240 |                       5 |                       5 | 2026-04     |        0 |                   0      | No trades   |
| range_breakout | any            | structure3  |          3 |        240 |                       5 |                       5 | 2026-05     |        0 |                   0      | No trades   |
| range_breakout | any            | structure3  |          3 |        240 |                       5 |                       5 | 2026-06     |        0 |                   0      | No trades   |
| range_breakout | any            | structure3  |          3 |        240 |                       5 |                       5 | 2026-07     |        0 |                   0      | No trades   |
| range_breakout | any            | structure3  |          3 |        240 |                       5 |                       5 | 2026-08     |        1 |                  -0.3629 | Loss        |
| range_breakout | any            | structure3  |          3 |        240 |                       5 |                       5 | 2026-09     |        1 |                  -3.1654 | Loss        |
| range_breakout | any            | structure3  |          3 |        240 |                       5 |                       5 | 2026-10     |        0 |                   0      | No trades   |
| range_breakout | any            | structure3  |          3 |        240 |                       5 |                       5 | 2026-11     |        0 |                   0      | No trades   |

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
