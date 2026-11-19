# BTCUSD / ETHUSD rolling spectral phase — independent historical experiment

**This does not establish a tradable cycle.** Predeclared Fourier peak-power/phase extrapolation on 96 completed 30m returns, 4 signal-strength/direction configurations.
One shared configuration chosen using 2025 **only**; 2026 not used for tuning. Full 2025/2026 research exposure is disclosed.

## 2025-only shared selection ranking

| model    |   train_2025_strong5 |   train_2025_positive |   train_2025_capped_month_sum |   train_2025_consistency_score |
|:---------|---------------------:|----------------------:|------------------------------:|-------------------------------:|
| B_follow |                    0 |                    10 |                      -133.953 |                        8.66047 |
| B_fade   |                    1 |                     3 |                      -254.841 |                        4.45159 |
| A_fade   |                    0 |                     1 |                      -375.894 |                       -2.75894 |
| A_follow |                    0 |                     1 |                      -423.268 |                       -3.23268 |

## Selected configuration: B_follow (both native markets)

## Each IST month, monthly PF SIDE BY SIDE with monthly NET ACCOUNT return

| month   |   BTCUSD_profit_factor |   ETHUSD_profit_factor |   BTCUSD_net_return_pct |   ETHUSD_net_return_pct |   BTCUSD_trades |   ETHUSD_trades |   BTCUSD_wins |   ETHUSD_wins |   BTCUSD_losses |   ETHUSD_losses |   BTCUSD_net_exit_pnl_usd |   ETHUSD_net_exit_pnl_usd |   BTCUSD_month_drawdown_sampled_pct |   ETHUSD_month_drawdown_sampled_pct |
|:--------|-----------------------:|-----------------------:|------------------------:|------------------------:|----------------:|----------------:|--------------:|--------------:|----------------:|----------------:|--------------------------:|--------------------------:|------------------------------------:|------------------------------------:|
| 2025-01 |               0.349324 |               0.551643 |              -17.6472   |              -14.9627   |              32 |              43 |             6 |            11 |              26 |              32 |                -176.472   |                -149.627   |                           -19.4632  |                           -16.4777  |
| 2025-02 |               0.608684 |               1.02296  |              -15.0951   |                1.43516  |              54 |              35 |            19 |            14 |              35 |              21 |                -124.313   |                   4.33914 |                           -18.942   |                            -5.44977 |
| 2025-03 |               1.02291  |               0.538115 |                0.6937   |              -16.7486   |              50 |              48 |            22 |            13 |              28 |              35 |                   4.85046 |                -135.985   |                            -5.65986 |                           -19.1661  |
| 2025-04 |               1.02498  |               1.01201  |                0.689249 |                0.466697 |              42 |              49 |            18 |            20 |              24 |              29 |                   4.85277 |                   2.73165 |                            -7.47889 |                            -8.87681 |
| 2025-05 |               0.987265 |               1.08355  |               -0.406123 |                3.53274  |              47 |              66 |            21 |            28 |              26 |              38 |                  -2.87908 |                  25.4873  |                            -7.43012 |                            -6.77827 |
| 2025-06 |               0.743371 |               0.944584 |              -10.2721   |               -0.923421 |              61 |              54 |            25 |            22 |              36 |              32 |                 -74.2934  |                 -14.7937  |                           -15.0502  |                           -10.3865  |
| 2025-07 |               1.01722  |               0.585475 |                0.278929 |              -20.3978   |              50 |              72 |            23 |            23 |              27 |              49 |                   3.5353  |                -143.057   |                            -7.05082 |                           -26.2248  |
| 2025-08 |               0.761072 |               0.598513 |               -4.64152  |               -8.9788   |              26 |              30 |            10 |             9 |              16 |              21 |                 -29.4867  |                 -50.7919  |                            -8.21675 |                            -8.9788  |
| 2025-09 |               1.13806  |               0.983235 |                4.15871  |                0.110668 |              54 |              50 |            26 |            22 |              28 |              28 |                  29.3746  |                  -2.94458 |                            -9.68802 |                           -10.08    |
| 2025-10 |               0.967059 |               0.509547 |               -0.686461 |              -17.3719   |              64 |              50 |            27 |            12 |              37 |              38 |                  -8.51287 |                 -94.3661  |                            -6.81325 |                           -19.7882  |
| 2025-11 |               1.04679  |               0.666787 |                1.32389  |              -10.6182   |              48 |              46 |            21 |            17 |              27 |              29 |                   8.29622 |                 -43.7058  |                            -5.76104 |                           -12.4302  |
| 2025-12 |               0.688891 |               1.09561  |              -10.5637   |                2.27288  |              53 |              31 |            21 |            15 |              32 |              16 |                 -67.0743  |                   8.17133 |                           -19.1239  |                           -11.4565  |
| 2026-01 |               0.496454 |               0.944159 |              -15.1007   |               -1.58356  |              44 |              44 |            16 |            19 |              28 |              25 |                 -85.7533  |                  -6.42066 |                           -16.6357  |                            -8.1049  |
| 2026-02 |               0.793157 |               0.614728 |               -5.39107  |              -11.9493   |              38 |              44 |            13 |            15 |              25 |              29 |                 -23.9668  |                 -47.6824  |                            -9.01576 |                           -14.2171  |
| 2026-03 |               1.19338  |               1.08171  |                4.90619  |                2.152    |              36 |              42 |            15 |            18 |              21 |              24 |                  20.3539  |                   7.56118 |                            -5.07535 |                            -9.84236 |
| 2026-04 |               0.591006 |               0.484965 |              -14.2884   |              -16.8294   |              52 |              41 |            18 |            10 |              34 |              31 |                 -68.3714  |                 -60.4033  |                           -14.2884  |                           -20.11    |
| 2026-05 |               0.493618 |               0.536597 |              -20.4734   |              -14.7143   |              53 |              42 |            16 |            13 |              37 |              29 |                 -83.8259  |                 -43.9241  |                           -23.2492  |                           -17.5768  |
| 2026-06 |               0.589864 |               0.542028 |              -16.7244   |              -14.4488   |              57 |              48 |            17 |            16 |              40 |              32 |                 -54.694   |                 -36.7849  |                           -17.6842  |                           -17.4568  |
| 2026-07 |               0.76341  |               0.624743 |               -8.53944  |              -13.6545   |              54 |              54 |            19 |            17 |              35 |              37 |                 -23.1948  |                 -29.7401  |                           -14.0666  |                           -15.0165  |
| 2026-08 |               0.462933 |               0.826431 |              -14.7516   |               -4.78376  |              42 |              41 |            13 |            16 |              29 |              25 |                 -36.6467  |                  -8.99652 |                           -15.6362  |                           -15.7637  |
| 2026-09 |               0.648974 |               0.575493 |               -6.86418  |              -10.7171   |              30 |              34 |            11 |             9 |              19 |              25 |                 -16.201   |                 -19.1908  |                           -11.4332  |                           -13.1535  |
| 2026-10 |               0.515855 |               0.818842 |              -20.9143   |               -4.96947  |              58 |              42 |            17 |            17 |              41 |              25 |                 -39.5876  |                  -7.94502 |                           -21.3693  |                            -7.57971 |

## Paired summary including exact 2025 FULL YEAR and 2026 Jan-Oct YTD returns

| market   | model    |   total_net_pf |   months_both_pf1p5_net10 |   months_both_pf1p5_net5 |   positive_months |   negative_months |   zero_months |   year2025_full_net_pct | year2025_above500   |   year2026_jan_oct_net_pct | year2026_jan_oct_above500   |   net_return_22m_pct |   max_sampled_equity_drawdown_pct |   trades |   wins |   losses |
|:---------|:---------|---------------:|--------------------------:|-------------------------:|------------------:|------------------:|--------------:|------------------------:|:--------------------|---------------------------:|:----------------------------|---------------------:|----------------------------------:|---------:|-------:|---------:|
| BTCUSD   | B_follow |       0.781055 |                         0 |                        0 |                 6 |                16 |             0 |                -43.2122 | False               |                   -72.531  | False                       |             -84.401  |                          -84.6656 |     1045 |    394 |      651 |
| ETHUSD   | B_follow |       0.758849 |                         0 |                        0 |                 6 |                16 |             0 |                -59.4542 | False               |                   -62.5284 | False                       |             -84.8068 |                          -84.8068 |     1006 |    356 |      650 |

## All candidate summaries (including rejected variants)

| market   | model    |   total_net_pf |   months_both_pf1p5_net10 |   months_both_pf1p5_net5 |   positive_months |   negative_months |   zero_months |   year2025_full_net_pct | year2025_above500   |   year2026_jan_oct_net_pct | year2026_jan_oct_above500   |   net_return_22m_pct |   max_sampled_equity_drawdown_pct |   trades |   wins |   losses |
|:---------|:---------|---------------:|--------------------------:|-------------------------:|------------------:|------------------:|--------------:|------------------------:|:--------------------|---------------------------:|:----------------------------|---------------------:|----------------------------------:|---------:|-------:|---------:|
| BTCUSD   | A_follow |       0.698404 |                         0 |                        0 |                 0 |                22 |             0 |                -98.294  | False               |                   -95.4553 | False                       |             -99.9225 |                          -99.9288 |     2888 |    997 |     1891 |
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
  "total_net_pf": 0.7306889248127737,
  "months_both_pf1p5_net10": 0,
  "months_both_pf1p5_net5": 0,
  "positive_months": 2,
  "negative_months": 20,
  "zero_months": 0,
  "year2025_full_net_pct": -64.6896714353802,
  "year2025_above500": false,
  "year2026_jan_oct_net_pct": -71.11047228935932,
  "year2026_jan_oct_above500": false,
  "net_return_22m_pct": -89.79901284460588,
  "max_sampled_equity_drawdown_pct": -89.79901284460601,
  "trades": 1016,
  "wins": 354,
  "losses": 662
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
