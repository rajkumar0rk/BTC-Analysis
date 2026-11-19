# BTCUSD / ETHUSD rolling spectral phase — independent historical experiment

**This does not establish a tradable cycle.** Predeclared Fourier peak-power/phase extrapolation on 96 completed 30m returns, 4 signal-strength/direction configurations.
One shared configuration chosen using 2025 **only**; 2026 not used for tuning. Full 2025/2026 research exposure is disclosed.

## 2025-only shared selection ranking

| model    |   train_2025_strong5 |   train_2025_positive |   train_2025_capped_month_sum |
|:---------|---------------------:|----------------------:|------------------------------:|
| B_fade   |                    1 |                     3 |                      -254.841 |
| B_follow |                    0 |                    10 |                      -133.953 |
| A_fade   |                    0 |                     1 |                      -375.894 |
| A_follow |                    0 |                     1 |                      -423.268 |

## Selected configuration: B_fade (both native markets)

## Each IST month, monthly PF SIDE BY SIDE with monthly NET ACCOUNT return

| month   |   BTCUSD_profit_factor |   ETHUSD_profit_factor |   BTCUSD_net_return_pct |   ETHUSD_net_return_pct |   BTCUSD_trades |   ETHUSD_trades |   BTCUSD_wins |   ETHUSD_wins |   BTCUSD_losses |   ETHUSD_losses |   BTCUSD_net_exit_pnl_usd |   ETHUSD_net_exit_pnl_usd |   BTCUSD_month_drawdown_sampled_pct |   ETHUSD_month_drawdown_sampled_pct |
|:--------|-----------------------:|-----------------------:|------------------------:|------------------------:|----------------:|----------------:|--------------:|--------------:|----------------:|----------------:|--------------------------:|--------------------------:|------------------------------------:|------------------------------------:|
| 2025-01 |               1.7851   |               0.971069 |               12.1588   |               -0.799645 |              29 |              44 |            16 |            18 |              13 |              26 |                 121.588   |                 -7.99645  |                            -3.25946 |                            -7.64403 |
| 2025-02 |               1.01469  |               0.929626 |                0.439624 |               -1.99746  |              49 |              34 |            22 |            13 |              27 |              21 |                   4.93076 |                -16.4092   |                            -7.7877  |                           -10.3161  |
| 2025-03 |               0.920942 |               1.02952  |               -2.97132  |                1.02758  |              59 |              47 |            25 |            19 |              34 |              28 |                 -33.4725  |                  7.87342  |                           -12.2391  |                            -7.15365 |
| 2025-04 |               0.596698 |               0.952918 |              -15.2779   |               -1.38183  |              53 |              50 |            17 |            19 |              36 |              31 |                -166.995   |                -14.8612   |                           -18.2565  |                            -8.37007 |
| 2025-05 |               0.759957 |               0.76019  |               -9.47413  |              -10.1954   |              57 |              67 |            21 |            24 |              36 |              43 |                 -87.7353  |                -98.7529   |                           -13.0128  |                           -13.609   |
| 2025-06 |               0.441284 |               0.631312 |              -27.0934   |              -15.6574   |              67 |              58 |            19 |            19 |              48 |              39 |                -222.235   |               -136.197    |                           -28.1723  |                           -20.1568  |
| 2025-07 |               0.405635 |               0.606965 |              -24.4779   |              -19.7531   |              57 |              76 |            16 |            24 |              41 |              52 |                -154.5     |               -144.92     |                           -25.6428  |                           -21.7548  |
| 2025-08 |               0.239494 |               0.394878 |              -18.1786   |              -14.9336   |              27 |              32 |             5 |             7 |              22 |              25 |                 -83.9092  |                -87.5259   |                           -18.1786  |                           -15.4957  |
| 2025-09 |               0.519678 |               0.704513 |              -22.1261   |              -12.0296   |              59 |              57 |            17 |            19 |              42 |              38 |                 -80.9761  |                -60.9239   |                           -22.9255  |                           -20.8613  |
| 2025-10 |               0.736504 |               0.818194 |              -11.1182   |               -6.48729  |              67 |              53 |            22 |            18 |              45 |              35 |                 -35.2875  |                -28.2978   |                           -16.0728  |                           -10.622   |
| 2025-11 |               0.564493 |               0.648743 |              -15.931    |              -13.1584   |              53 |              53 |            17 |            17 |              36 |              36 |                 -41.645   |                -53.3525   |                           -16.8748  |                           -16.1139  |
| 2025-12 |               0.467421 |               0.313431 |              -19.1222   |              -20.6937   |              50 |              37 |            13 |             6 |              37 |              31 |                 -42.0237  |                -74.8966   |                           -19.5853  |                           -21.4172  |
| 2026-01 |               0.974784 |               0.684868 |               -0.686601 |              -10.2439   |              44 |              47 |            19 |            15 |              25 |              32 |                  -1.22036 |                -29.0662   |                           -15.5324  |                           -12.4422  |
| 2026-02 |               0.521693 |               0.954723 |              -10.5654   |               -1.28867  |              33 |              46 |            10 |            17 |              23 |              29 |                 -18.9925  |                 -3.2819   |                           -10.7594  |                           -12.0644  |
| 2026-03 |               0.474863 |               0.883664 |              -15.4538   |               -2.87176  |              41 |              41 |            13 |            15 |              28 |              26 |                 -24.0544  |                 -7.2194   |                           -18.7105  |                            -8.28711 |
| 2026-04 |               1.09834  |               0.951256 |                3.35965  |               -1.29982  |              57 |              43 |            26 |            18 |              31 |              25 |                   4.48421 |                 -3.17381  |                            -7.23989 |                            -7.28261 |
| 2026-05 |               0.473258 |               0.485191 |              -19.4172   |              -19.7965   |              50 |              48 |            17 |            16 |              33 |              32 |                 -26.429   |                -47.7095   |                           -19.8569  |                           -19.7965  |
| 2026-06 |               0.29924  |               0.603192 |              -32.4712   |              -15.4106   |              62 |              55 |            14 |            15 |              48 |              40 |                 -36.4565  |                -29.7872   |                           -34.2168  |                           -16.915   |
| 2026-07 |               0.667855 |               0.743631 |              -14.3031   |              -10.748    |              64 |              59 |            22 |            21 |              42 |              38 |                 -10.7376  |                -17.5733   |                           -16.2975  |                           -16.4517  |
| 2026-08 |               0.429362 |               0.305337 |              -17.6204   |              -22.7499   |              46 |              45 |            16 |            11 |              30 |              34 |                 -11.3359  |                -33.1988   |                           -21.847   |                           -24.9497  |
| 2026-09 |               0.804753 |               0.974613 |               -4.43408  |               -0.599321 |              34 |              36 |            14 |            17 |              20 |              19 |                  -2.41857 |                 -0.675618 |                            -5.06634 |                            -7.60126 |
| 2026-10 |               0.899443 |               1.21389  |               -3.46937  |                4.70691  |              53 |              39 |            21 |            19 |              32 |              20 |                  -1.68857 |                  5.27432  |                           -12.4729  |                            -5.88707 |

## Paired summary including exact 2025 FULL YEAR and 2026 Jan-Oct YTD returns

| market   | model   |   total_net_pf |   months_both_pf1p5_net10 |   months_both_pf1p5_net5 |   positive_months |   negative_months |   zero_months |   year2025_full_net_pct | year2025_above500   |   year2026_jan_oct_net_pct | year2026_jan_oct_above500   |   net_return_22m_pct |   max_sampled_equity_drawdown_pct |   trades |   wins |   losses |
|:---------|:--------|---------------:|--------------------------:|-------------------------:|------------------:|------------------:|--------------:|------------------------:|:--------------------|---------------------------:|:----------------------------|---------------------:|----------------------------------:|---------:|-------:|---------:|
| BTCUSD   | B_fade  |       0.711934 |                         1 |                        1 |                 3 |                19 |             0 |                -82.226  | False               |                   -72.4931 | False                       |             -95.1109 |                          -96.1948 |     1111 |    382 |      729 |
| ETHUSD   | B_fade  |       0.75728  |                         0 |                        0 |                 2 |                20 |             0 |                -71.6259 | False               |                   -58.6491 | False                       |             -88.2671 |                          -90.0705 |     1067 |    367 |      700 |

## All candidate summaries (including rejected variants)

| market   | model    |   total_net_pf |   months_both_pf1p5_net10 |   months_both_pf1p5_net5 |   positive_months |   negative_months |   zero_months |   year2025_full_net_pct | year2025_above500   |   year2026_jan_oct_net_pct | year2026_jan_oct_above500   |   net_return_22m_pct |   max_sampled_equity_drawdown_pct |   trades |   wins |   losses |
|:---------|:---------|---------------:|--------------------------:|-------------------------:|------------------:|------------------:|--------------:|------------------------:|:--------------------|---------------------------:|:----------------------------|---------------------:|----------------------------------:|---------:|-------:|---------:|
| BTCUSD   | A_follow |       0.698404 |                         0 |                        0 |                 0 |                22 |             0 |                -98.294  | False               |                   -95.4553 | False                       |             -99.9225 |                          -99.9292 |     2888 |    997 |     1891 |
| BTCUSD   | A_fade   |       0.760665 |                         0 |                        0 |                 0 |                22 |             0 |                -97.3845 | False               |                   -96.5572 | False                       |             -99.91   |                          -99.9182 |     2866 |   1018 |     1848 |
| BTCUSD   | B_follow |       0.781055 |                         0 |                        0 |                 6 |                16 |             0 |                -43.2122 | False               |                   -72.531  | False                       |             -84.401  |                          -84.6656 |     1045 |    394 |      651 |
| BTCUSD   | B_fade   |       0.711934 |                         1 |                        1 |                 3 |                19 |             0 |                -82.226  | False               |                   -72.4931 | False                       |             -95.1109 |                          -96.1948 |     1111 |    382 |      729 |
| ETHUSD   | A_follow |       0.67202  |                         0 |                        0 |                 1 |                21 |             0 |                -96.5594 | False               |                   -96.6819 | False                       |             -99.8858 |                          -99.8929 |     2813 |    951 |     1862 |
| ETHUSD   | A_fade   |       0.815698 |                         0 |                        0 |                 1 |                21 |             0 |                -95.0836 | False               |                   -93.4411 | False                       |             -99.6775 |                          -99.7157 |     2855 |   1009 |     1846 |
| ETHUSD   | B_follow |       0.758849 |                         0 |                        0 |                 6 |                16 |             0 |                -59.4542 | False               |                   -62.5284 | False                       |             -84.8068 |                          -84.8068 |     1006 |    356 |      650 |
| ETHUSD   | B_fade   |       0.75728  |                         0 |                        0 |                 2 |                20 |             0 |                -71.6259 | False               |                   -58.6491 | False                       |             -88.2671 |                          -90.0705 |     1067 |    367 |      700 |

## Stress ETH slippage 0.04% per side

{
  "market": "ETHUSD",
  "model": "eth_slip_0p04pct",
  "total_net_pf": 0.721364517262405,
  "months_both_pf1p5_net10": 0,
  "months_both_pf1p5_net5": 0,
  "positive_months": 1,
  "negative_months": 21,
  "zero_months": 0,
  "year2025_full_net_pct": -77.99429288524856,
  "year2025_above500": false,
  "year2026_jan_oct_net_pct": -70.73348787655821,
  "year2026_jan_oct_above500": false,
  "net_return_22m_pct": -93.55969705941219,
  "max_sampled_equity_drawdown_pct": -94.49291361536456,
  "trades": 1072,
  "wins": 358,
  "losses": 714
}

## Quality and missing execution costs

{
  "source": "Original Delta India BTCUSD ETHUSD 1m original manifest hash verified per partition",
  "source_sha256_file": "source_partition_sha256.csv",
  "months": 22,
  "calendar": "IST Jan2025 to Oct2026",
  "missing_2025_Jan_IST_first_hours": 5.5,
  "original_2026_Oct31_complete_both": true,
  "November_2026_excluded": true,
  "native_candles_per_market": {
    "BTCUSD": 963360,
    "ETHUSD": 963360
  },
  "timeframes": "30m completed spectral signals, next original 1m open and 1m stop-first replay",
  "selection": "one identical config for BTC ETH selected using 2025 both-coin monthly scores; 2026 retrospective check only",
  "initial_equity_usd_per_market": 1000.0,
  "risk_per_stop_equity_pct": 1.0,
  "max_leverage": 3.0,
  "standard_taker_fee_each_side": 0.0005,
  "fee_GST": 0.18,
  "BTC_adverse_slippage_usd_points_each_side": 5.0,
  "ETH_adverse_slippage_fraction_each_side": 0.0002,
  "ETH_stress_slippage_fraction_each_side": 0.0004,
  "months_NAV": "Month end mark-to-market using exit fee and slip estimate; positions persist",
  "months_PF": "winning closed net-USD trade sums / abs(losing closed net-USD trade sums) by IST exit month",
  "end_scope_note": "Open position at final October IST boundary marked in NAV, not forced flat; any November exit excluded from reported 22-month PF",
  "sampled_drawdown_not_tick_path": true,
  "costs_not_verified": [
    "settled funding",
    "bid/ask spread",
    "market impact",
    "margin/liquidation",
    "lot-size constraints",
    "actual execution latency"
  ],
  "historical_2026_not_pristine_OOS": true,
  "previously_tested_comparators": [
    "hourly autocorr",
    "variance ratio",
    "bipower variation",
    "time-day volume",
    "breakout/squeeze",
    "return dispersion"
  ]
}

Exit-month PF sums only closed trade net PnL, including modeled entry/exit taker fees, GST and slippage. 
Account monthly NAV return uses equity plus estimated liquidation net value of any carried open position. 
This distinction means exit-month net PnL need not equal NAV change. 
Drawdowns are based on closed trade equity plus month-end marks, not full intraminute equity lows. 
Historical backtests can overstate live performance; no orders were placed.
