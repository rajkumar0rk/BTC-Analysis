# Shock-only 1H Donchian breakout — fully replayed BTCUSD account

## What is actually tested
Only enter on a **closed 1H** break of the previous 24 completed hourly bars when the fully closed signal hour is classified as **shock** by the frozen 2026-11-21 market-regime engine. Entry at the very next native 1M open. No intrabar order inference from the hourly candle.

Shock rule: (1H true range > 2.2 x ATR14) OR (ATR14 / prior-72H median ATR14 >= 1.8). It uses information available at the completed signal hour.

Stop = 1.8 x ATR14, target = 3R, maximum hold 36 hours; one position at a time; IST month-end flatten. Replays are newly generated for the filtered account; they do NOT sum the baseline's old shock-tagged trades.

Hypothetical independent initial equity $10,000; risk 0.5% of changing equity per stop and 3x notional cap; fees 0.05% taker each side + GST 18%; 5 BTC price points assumed adverse slip each side. Stop/target same 1M candle => stop first, possible stop gap filled at worse price. Funding, real spread, impact, liquidation and margin requirements are not modeled.

## Data and run quality
~~~json
{
  "data": "Delta India BTCUSD native 1M, SHA verified, no missing minutes",
  "first_utc": "2025-01-01 00:00:00+00:00",
  "last_utc": "2026-11-20 23:59:00+00:00",
  "minute_candles": 992160,
  "source_partitions": 23,
  "complete_ist_months": [
    "2025-01",
    "2025-02",
    "2025-03",
    "2025-04",
    "2025-05",
    "2025-06",
    "2025-07",
    "2025-08",
    "2025-09",
    "2025-10",
    "2025-11",
    "2025-12",
    "2026-01",
    "2026-02",
    "2026-03",
    "2026-04",
    "2026-05",
    "2026-06",
    "2026-07",
    "2026-08",
    "2026-09",
    "2026-10"
  ],
  "shock_candidate_signals": 401,
  "all_regime_candidate_signals": 1347,
  "shock_only_executed_trades": 301,
  "unfiltered_baseline_executed_trades": 573,
  "execution": "next 1M open after completely closed 1H signal; stop-first 1M; IST monthly flatten",
  "baseline_parity_verified": true,
  "selection_bias_warning": "shock gate selected after seeing original 2025-2026 subgroup result",
  "blind_out_of_sample": false
}
~~~

## Unfiltered vs independently executed shock-only account
| model                  |   trades |   wins |   losses |   win_rate_pct |   profit_factor |   net_pnl_usd |   net_return_pct |   ending_account_usd |   max_trade_close_drawdown_pct |   avg_net_R |   total_fee_gst_usd |   total_slippage_usd |   gross_before_costs_usd |
|:-----------------------|---------:|-------:|---------:|---------------:|----------------:|--------------:|-----------------:|---------------------:|-------------------------------:|------------:|--------------------:|---------------------:|-------------------------:|
| Unfiltered 1H Donchian |      573 |    187 |      386 |         32.635 |          0.931  |      -1323.02 |         -13.2302 |              8676.98 |                         18.925 |     -0.0432 |             3277.52 |               320.86 |                  2275.36 |
| Shock-only 1H Donchian |      301 |    107 |      194 |         35.548 |          1.0316 |        334.69 |           3.3469 |             10334.7  |                          9.177 |      0.0284 |             1841.47 |               184.26 |                  2360.43 |

## Calendar year returns (2026 through Oct only)
|   year |   months |   trades |   profitable_months |   losing_months |   idle_months |   year_net_return_pct |
|-------:|---------:|---------:|--------------------:|----------------:|--------------:|----------------------:|
|   2025 |       12 |      158 |                   6 |               6 |             0 |               -0.6432 |
|   2026 |       10 |      143 |                   4 |               6 |             0 |                4.016  |

## Every complete IST month's actual account net return, no-trade months included
| month_ist   |   trades |   wins |   losses |   net_return_pct |   net_pnl_usd |   gross_before_costs_usd |   fees_gst_usd |   slippage_usd | status   |
|:------------|---------:|-------:|---------:|-----------------:|--------------:|-------------------------:|---------------:|---------------:|:---------|
| 2025-01     |       16 |      4 |       12 |         -2.11107 |       -211.11 |                  -141.76 |          63.89 |           5.46 | Loss     |
| 2025-02     |       13 |      4 |        9 |         -1.01643 |        -99.5  |                   -35.31 |          58.93 |           5.26 | Loss     |
| 2025-03     |       12 |      3 |        9 |         -0.04637 |         -4.49 |                    63.18 |          61.59 |           6.08 | Loss     |
| 2025-04     |       11 |      3 |        8 |          0.17244 |         16.7  |                    74.24 |          52.42 |           5.12 | Profit   |
| 2025-05     |       13 |      5 |        8 |          1.32437 |        128.48 |                   212.46 |          77.59 |           6.39 | Profit   |
| 2025-06     |       11 |      3 |        8 |         -2.63504 |       -259.03 |                  -185.58 |          67.99 |           5.45 | Loss     |
| 2025-07     |       12 |      3 |        9 |         -3.33038 |       -318.75 |                  -226.04 |          86.28 |           6.44 | Loss     |
| 2025-08     |       13 |      5 |        8 |          0.18272 |         16.91 |                    99.16 |          76.62 |           5.63 | Profit   |
| 2025-09     |       13 |      7 |        6 |          2.84455 |        263.67 |                   370.87 |          99.7  |           7.5  | Profit   |
| 2025-10     |       12 |      9 |        3 |         10.1034  |        963.15 |                  1037.46 |          69.22 |           5.09 | Profit   |
| 2025-11     |       12 |      5 |        7 |          0.48682 |         51.1  |                   104.44 |          49.08 |           4.26 | Profit   |
| 2025-12     |       20 |      3 |       17 |         -5.7973  |       -611.45 |                  -468.92 |         130.11 |          12.42 | Loss     |
| 2026-01     |       20 |      9 |       11 |          4.73765 |        470.72 |                   608.86 |         126.28 |          11.87 | Profit   |
| 2026-02     |       10 |      5 |        5 |          2.50142 |        260.31 |                   302.2  |          37.2  |           4.69 | Profit   |
| 2026-03     |       11 |      4 |        7 |         -0.22666 |        -24.18 |                    28.8  |          47.22 |           5.76 | Loss     |
| 2026-04     |       15 |      5 |       10 |         -0.68218 |        -72.6  |                    20.83 |          83.74 |           9.7  | Loss     |
| 2026-05     |       14 |      5 |        9 |         -0.47418 |        -50.12 |                    66.45 |         105.16 |          11.41 | Loss     |
| 2026-06     |       11 |      4 |        7 |          1.64213 |        172.75 |                   235.01 |          54.87 |           7.39 | Profit   |
| 2026-07     |       13 |      5 |        8 |         -0.30596 |        -32.72 |                    66.38 |          87.44 |          11.66 | Loss     |
| 2026-08     |       19 |      7 |       12 |          0.58922 |         62.81 |                   272.11 |         185.6  |          23.69 | Profit   |
| 2026-09     |       14 |      4 |       10 |         -2.3776  |       -254.94 |                  -145.35 |          99.07 |          10.53 | Loss     |
| 2026-10     |       16 |      5 |       11 |         -1.27069 |       -133.01 |                     0.92 |         121.46 |          12.47 | Loss     |

## Read before interpreting
- This gate was chosen *after inspecting the same full history*, where the baseline's shock-tagged subset had PF > 1. Ex-post selection bias applies. 2026 has already been researched; this is not a pristine untouched holdout.
- Unlike attribution on the old baseline ledger, the shock-only account has its own entries, position concurrency, fees, sizing, cash and equity progression.
- No claim of real-trading profitability until forward test and realistic historical spreads, actual funding, liquidation and fills are incorporated.
- Equity drawdown is sampled on trade closes; intratrade max drawdown may be much worse.
- The returns are for a hypothetical equity account, NOT BTC price-point movement and NOT a margin/contract feasibility estimate.
- Zero-trade months count as **not profitable**. November 2026 excluded because incomplete.
- \`shock\` is a price volatility definition, not proof of liquidations.

## Execution audit
- Original eligible all-regime Donchian signal hours: 1347
- Eligible shock Donchian signal hours: 401
- Actual executed shock-only trades, with independent concurrency: 301
