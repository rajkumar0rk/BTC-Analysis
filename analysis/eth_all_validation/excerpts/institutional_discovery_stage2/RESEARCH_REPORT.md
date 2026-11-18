# Finding actual BTC futures market behavior: non-directional predictive regimes

## Research question
Before trying BUY/SELL rules, can market-structure, participation, open interest, basis, funding, and time context forecast the NEXT hour's price movement RANGE? A future hourly HIGH-LOW is a volatility observation, not an executable trading profit.

All 1-hour samples are nonoverlapping, and all features use completed current/prior hourly candles. 2025=training; Jan-Jun 2026=validation; July-Oct 2026=chronological recheck (NOT globally untouched after earlier analyses).
The baseline controls for next-hour New York clock hour and weekday/weekend, so trivial clock effects are reduced. Regime signal rates are measured against matched baseline rates within each chronological period.

## Source/quality
~~~json
{
  "futures_1m": 987840,
  "mark_1m": 987840,
  "OI_5m": 197568,
  "funding_1h": 16464,
  "available_hourly_events": 16283,
  "first": "2025-01-08 12:00:00+00:00",
  "last": "2026-11-17 22:00:00+00:00",
  "oi_changes_pct_p01_p50_p99": [
    -16.926,
    0.359,
    14.877
  ],
  "hourly_range_points_p01_p50_p99": [
    3.85,
    19.55,
    107.29
  ],
  "funding_distinct_values": 818,
  "funding_fraction_exact_point01": 0.603,
  "total_predeclared_conditions": 34,
  "eligible_metric_tests": 145,
  "candidate_regimes": [
    "after_OI_fall_and_range_expand",
    "after_hourly_range_expansion_2x",
    "after_price_down_and_OI_fall",
    "after_OI_rise_and_range_expand",
    "after_OI_fall_zm1p5",
    "after_hourly_range_expansion_1p5",
    "after_big_down_hour",
    "after_range_expansion_and_volume"
  ],
  "notes": [
    "Hourly next-period outcomes do not overlap",
    "Clock-matched means by NY next-hour and weekend/weekday",
    "The chronological holdout was previously seen by other studies; independent new forward data remains needed",
    "These are price-point ranges, NOT executable trade profits",
    "Gross future high-low is NOT a profitable tradable strategy"
  ]
}
~~~

## Selected preliminary regimes and chronological rechecks
Selection uses only 2025 and Jan-Jun 2026; holdout is not used for ranking.
| rule                             | metric           |   n_train |   observed_train |   matched_train |   uplift_train |   n_validation |   uplift_validation |   n_holdout |   uplift_holdout |   rank_score |
|:---------------------------------|:-----------------|----------:|-----------------:|----------------:|---------------:|---------------:|--------------------:|------------:|-----------------:|-------------:|
| after_OI_fall_and_range_expand   | normalized_range |       407 |          1.98237 |         1.38416 |        0.59821 |            230 |             0.58637 |         173 |          0.8032  |      0.58637 |
| after_hourly_range_expansion_2x  | normalized_range |      1032 |          2.01795 |         1.39838 |        0.61957 |            611 |             0.55643 |         503 |          0.71375 |      0.55643 |
| after_price_down_and_OI_fall     | normalized_range |       294 |          1.88856 |         1.37705 |        0.51152 |            177 |             0.51587 |         133 |          0.28226 |      0.51152 |
| after_OI_rise_and_range_expand   | normalized_range |       122 |          1.89032 |         1.39379 |        0.49653 |             61 |             0.47072 |          55 |          0.31838 |      0.47072 |
| after_OI_fall_zm1p5              | normalized_range |       523 |          1.80678 |         1.37122 |        0.43556 |            293 |             0.4342  |         221 |          0.6073  |      0.4342  |
| after_hourly_range_expansion_1p5 | normalized_range |      2019 |          1.78039 |         1.37293 |        0.40746 |           1112 |             0.4214  |         861 |          0.48175 |      0.40746 |
| after_big_down_hour              | normalized_range |      1059 |          1.8181  |         1.38139 |        0.43671 |            570 |             0.40292 |         424 |          0.41207 |      0.40292 |
| after_range_expansion_and_volume | normalized_range |      1222 |          1.88864 |         1.46482 |        0.42382 |            703 |             0.39479 |         565 |          0.57146 |      0.39479 |
| after_hourly_range_expansion_2x  | p_regime_expand  |      1032 |          0.58333 |         0.32294 |        0.26039 |            611 |             0.22943 |         503 |          0.26603 |      0.22943 |
| after_OI_fall_and_range_expand   | p_regime_expand  |       407 |          0.54791 |         0.31195 |        0.23596 |            230 |             0.20024 |         173 |          0.24029 |      0.20024 |
| after_big_down_hour              | p_regime_expand  |      1059 |          0.49764 |         0.31521 |        0.18242 |            570 |             0.17682 |         424 |          0.19042 |      0.17682 |
| after_range_expansion_and_volume | p_regime_expand  |      1222 |          0.53928 |         0.36778 |        0.1715  |            703 |             0.16393 |         565 |          0.19719 |      0.16393 |
| after_hourly_range_expansion_1p5 | p_regime_expand  |      2019 |          0.47301 |         0.31008 |        0.16293 |           1112 |             0.17072 |         861 |          0.1865  |      0.16293 |
| after_price_down_and_OI_fall     | p_regime_expand  |       294 |          0.5034  |         0.30771 |        0.19569 |            177 |             0.14801 |         133 |          0.10041 |      0.14801 |
| after_OI_fall_zm1p5              | p_regime_expand  |       523 |          0.47419 |         0.30462 |        0.16957 |            293 |             0.14077 |         221 |          0.17673 |      0.14077 |
| after_OI_rise_and_range_expand   | p_regime_expand  |       122 |          0.46721 |         0.3292  |        0.13801 |             61 |             0.15982 |          55 |          0.17864 |      0.13801 |
| after_OI_fall_zm1p5              | p500             |       523 |          0.00191 |         0.00019 |        0.00173 |            293 |             0       |         221 |          0       |      0       |
| after_range_expansion_and_volume | p500             |      1222 |          0.00082 |         3e-05   |        0.00079 |            703 |             0       |         565 |          0       |      0       |
| after_big_down_hour              | p500             |      1059 |          0.00094 |         9e-05   |        0.00086 |            570 |             0       |         424 |          0       |      0       |
| after_OI_fall_and_range_expand   | p500             |       407 |          0.00246 |         0.00019 |        0.00227 |            230 |             0       |         173 |          0       |      0       |
| after_hourly_range_expansion_2x  | p500             |      1032 |          0.00097 |         0.00011 |        0.00086 |            611 |             0       |         503 |          0       |      0       |
| after_hourly_range_expansion_1p5 | p500             |      2019 |          0.0005  |         0.00011 |        0.00038 |           1112 |             0       |         861 |          0       |      0       |
| after_price_down_and_OI_fall     | p500             |       294 |          0.0034  |         0.00021 |        0.00319 |            177 |             0       |         133 |          0       |      0       |
| after_OI_rise_and_range_expand   | p500             |       122 |          0       |         3e-05   |       -3e-05   |             61 |             0       |          55 |          0       |     -3e-05   |

## Calendar-day bootstrap confidence intervals (exploratory)
Lower > 0 in multiple periods indicates consistent evidence for a volatility-regime uplift, NOT guaranteed returns. These are NOT multiplicity-adjusted.
| rule                             | period     | metric                |    n |   days |   uplift_lower |   uplift_median |   uplift_upper |
|:---------------------------------|:-----------|:----------------------|-----:|-------:|---------------:|----------------:|---------------:|
| after_OI_fall_and_range_expand   | train      | future_range_500      |  407 |    234 |       -0.00025 |         0.00225 |        0.00719 |
| after_OI_fall_and_range_expand   | train      | future_vol_expansion  |  407 |    234 |        0.1791  |         0.23831 |        0.29404 |
| after_OI_fall_and_range_expand   | train      | future_vol_normalized |  407 |    234 |        0.41697 |         0.60026 |        0.79374 |
| after_OI_fall_and_range_expand   | validation | future_range_500      |  230 |    130 |        0       |         0       |        0       |
| after_OI_fall_and_range_expand   | validation | future_vol_expansion  |  230 |    130 |        0.13427 |         0.19845 |        0.26468 |
| after_OI_fall_and_range_expand   | validation | future_vol_normalized |  230 |    130 |        0.39009 |         0.58802 |        0.78531 |
| after_OI_fall_and_range_expand   | holdout    | future_range_500      |  173 |     98 |        0       |         0       |        0       |
| after_OI_fall_and_range_expand   | holdout    | future_vol_expansion  |  173 |     98 |        0.16069 |         0.23728 |        0.31255 |
| after_OI_fall_and_range_expand   | holdout    | future_vol_normalized |  173 |     98 |        0.39513 |         0.76543 |        1.29828 |
| after_hourly_range_expansion_2x  | train      | future_range_500      | 1032 |    298 |       -0.00014 |         0.00084 |        0.00282 |
| after_hourly_range_expansion_2x  | train      | future_vol_expansion  | 1032 |    298 |        0.22225 |         0.2602  |        0.2979  |
| after_hourly_range_expansion_2x  | train      | future_vol_normalized | 1032 |    298 |        0.50124 |         0.61646 |        0.73605 |
| after_hourly_range_expansion_2x  | validation | future_range_500      |  611 |    162 |        0       |         0       |        0       |
| after_hourly_range_expansion_2x  | validation | future_vol_expansion  |  611 |    162 |        0.18126 |         0.22777 |        0.2743  |
| after_hourly_range_expansion_2x  | validation | future_vol_normalized |  611 |    162 |        0.42153 |         0.55428 |        0.67308 |
| after_hourly_range_expansion_2x  | holdout    | future_range_500      |  503 |    125 |        0       |         0       |        0       |
| after_hourly_range_expansion_2x  | holdout    | future_vol_expansion  |  503 |    125 |        0.20967 |         0.26669 |        0.31304 |
| after_hourly_range_expansion_2x  | holdout    | future_vol_normalized |  503 |    125 |        0.44144 |         0.70967 |        1.09357 |
| after_price_down_and_OI_fall     | train      | future_range_500      |  294 |    195 |       -0.00028 |         0.00316 |        0.00995 |
| after_price_down_and_OI_fall     | train      | future_vol_expansion  |  294 |    195 |        0.13016 |         0.19474 |        0.26136 |
| after_price_down_and_OI_fall     | train      | future_vol_normalized |  294 |    195 |        0.3034  |         0.49483 |        0.72996 |
| after_price_down_and_OI_fall     | validation | future_range_500      |  177 |    114 |        0       |         0       |        0       |
| after_price_down_and_OI_fall     | validation | future_vol_expansion  |  177 |    114 |        0.06722 |         0.14388 |        0.2282  |
| after_price_down_and_OI_fall     | validation | future_vol_normalized |  177 |    114 |        0.27732 |         0.50402 |        0.77715 |
| after_price_down_and_OI_fall     | holdout    | future_range_500      |  133 |     88 |        0       |         0       |        0       |
| after_price_down_and_OI_fall     | holdout    | future_vol_expansion  |  133 |     88 |        0.01223 |         0.10326 |        0.20163 |
| after_price_down_and_OI_fall     | holdout    | future_vol_normalized |  133 |     88 |        0.06201 |         0.28239 |        0.50414 |
| after_OI_rise_and_range_expand   | train      | future_range_500      |  122 |     99 |       -0.0001  |        -3e-05   |        0       |
| after_OI_rise_and_range_expand   | train      | future_vol_expansion  |  122 |     99 |        0.06148 |         0.13732 |        0.2214  |
| after_OI_rise_and_range_expand   | train      | future_vol_normalized |  122 |     99 |        0.3011  |         0.486   |        0.71396 |
| after_OI_rise_and_range_expand   | validation | future_range_500      |   61 |     48 |        0       |         0       |        0       |
| after_OI_rise_and_range_expand   | validation | future_vol_expansion  |   61 |     48 |        0.03618 |         0.15428 |        0.26346 |
| after_OI_rise_and_range_expand   | validation | future_vol_normalized |   61 |     48 |        0.09513 |         0.4499  |        0.86657 |
| after_OI_rise_and_range_expand   | holdout    | future_range_500      |   55 |     40 |        0       |         0       |        0       |
| after_OI_rise_and_range_expand   | holdout    | future_vol_expansion  |   55 |     40 |        0.06    |         0.17583 |        0.29781 |
| after_OI_rise_and_range_expand   | holdout    | future_vol_normalized |   55 |     40 |        0.04423 |         0.31255 |        0.57888 |
| after_OI_fall_zm1p5              | train      | future_range_500      |  523 |    272 |       -0.00023 |         0.00173 |        0.00704 |
| after_OI_fall_zm1p5              | train      | future_vol_expansion  |  523 |    272 |        0.12126 |         0.17025 |        0.21907 |
| after_OI_fall_zm1p5              | train      | future_vol_normalized |  523 |    272 |        0.29921 |         0.43627 |        0.60267 |
| after_OI_fall_zm1p5              | validation | future_range_500      |  293 |    146 |        0       |         0       |        0       |
| after_OI_fall_zm1p5              | validation | future_vol_expansion  |  293 |    146 |        0.07551 |         0.13999 |        0.206   |
| after_OI_fall_zm1p5              | validation | future_vol_normalized |  293 |    146 |        0.24846 |         0.43011 |        0.62194 |
| after_OI_fall_zm1p5              | holdout    | future_range_500      |  221 |    111 |        0       |         0       |        0       |
| after_OI_fall_zm1p5              | holdout    | future_vol_expansion  |  221 |    111 |        0.10359 |         0.17295 |        0.24472 |
| after_OI_fall_zm1p5              | holdout    | future_vol_normalized |  221 |    111 |        0.26694 |         0.56981 |        1.02228 |
| after_hourly_range_expansion_1p5 | train      | future_range_500      | 2019 |    339 |       -0.00013 |         0.00037 |        0.00146 |
| after_hourly_range_expansion_1p5 | train      | future_vol_expansion  | 2019 |    339 |        0.13275 |         0.16229 |        0.19208 |
| after_hourly_range_expansion_1p5 | train      | future_vol_normalized | 2019 |    339 |        0.32018 |         0.4036  |        0.49544 |
| after_hourly_range_expansion_1p5 | validation | future_range_500      | 1112 |    178 |        0       |         0       |        0       |
| after_hourly_range_expansion_1p5 | validation | future_vol_expansion  | 1112 |    178 |        0.12907 |         0.17008 |        0.20943 |
| after_hourly_range_expansion_1p5 | validation | future_vol_normalized | 1112 |    178 |        0.32087 |         0.42004 |        0.51842 |
| after_hourly_range_expansion_1p5 | holdout    | future_range_500      |  861 |    133 |        0       |         0       |        0       |
| after_hourly_range_expansion_1p5 | holdout    | future_vol_expansion  |  861 |    133 |        0.1402  |         0.18559 |        0.23007 |
| after_hourly_range_expansion_1p5 | holdout    | future_vol_normalized |  861 |    133 |        0.28886 |         0.47502 |        0.69793 |
| after_big_down_hour              | train      | future_range_500      | 1059 |    312 |       -0.00011 |         0.00084 |        0.00353 |
| after_big_down_hour              | train      | future_vol_expansion  | 1059 |    312 |        0.14509 |         0.18338 |        0.22048 |
| after_big_down_hour              | train      | future_vol_normalized | 1059 |    312 |        0.32592 |         0.43775 |        0.55061 |
| after_big_down_hour              | validation | future_range_500      |  570 |    162 |        0       |         0       |        0       |
| after_big_down_hour              | validation | future_vol_expansion  |  570 |    162 |        0.12563 |         0.17653 |        0.21748 |
| after_big_down_hour              | validation | future_vol_normalized |  570 |    162 |        0.28352 |         0.40001 |        0.51986 |
| after_big_down_hour              | holdout    | future_range_500      |  424 |    123 |        0       |         0       |        0       |
| after_big_down_hour              | holdout    | future_vol_expansion  |  424 |    123 |        0.12473 |         0.19002 |        0.24923 |
| after_big_down_hour              | holdout    | future_vol_normalized |  424 |    123 |        0.25742 |         0.40909 |        0.57814 |
| after_range_expansion_and_volume | train      | future_range_500      | 1222 |    318 |       -5e-05   |         0.00078 |        0.0025  |
| after_range_expansion_and_volume | train      | future_vol_expansion  | 1222 |    318 |        0.13426 |         0.17221 |        0.20715 |
| after_range_expansion_and_volume | train      | future_vol_normalized | 1222 |    318 |        0.33209 |         0.42258 |        0.52259 |
| after_range_expansion_and_volume | validation | future_range_500      |  703 |    168 |        0       |         0       |        0       |
| after_range_expansion_and_volume | validation | future_vol_expansion  |  703 |    168 |        0.11255 |         0.16413 |        0.20912 |
| after_range_expansion_and_volume | validation | future_vol_normalized |  703 |    168 |        0.27488 |         0.3967  |        0.51268 |
| after_range_expansion_and_volume | holdout    | future_range_500      |  565 |    126 |        0       |         0       |        0       |
| after_range_expansion_and_volume | holdout    | future_vol_expansion  |  565 |    126 |        0.14758 |         0.19702 |        0.24066 |
| after_range_expansion_and_volume | holdout    | future_vol_normalized |  565 |    126 |        0.34012 |         0.56009 |        0.87636 |

## Execution realism
Optional directional follow/fade simulation uses next hourly OPEN, next 60 individual minutes with stop-first ambiguous fills, taker fee each side 0.05% plus 18% GST, and 5 BTC-point adverse slippage per side.
One trade per NY day per rule, restricted to days with condition; +300/-250, +500/-350, +800/-500, one-hour timeout.
Directional simulated results are separate from non-directional range findings. Do not conflate forecastable volatility with forecastable direction.
| rule                             | mode   |   target |   stop | period     |   trades |   mean_net |   win_pct |
|:---------------------------------|:-------|---------:|-------:|:-----------|---------:|-----------:|----------:|
| after_OI_fall_and_range_expand   | fade   |      300 |    250 | holdout    |       98 |     -14.63 |     11.22 |
| after_OI_fall_and_range_expand   | fade   |      300 |    250 | train      |      234 |     -14.71 |     26.5  |
| after_OI_fall_and_range_expand   | fade   |      300 |    250 | validation |      130 |     -14.58 |     13.85 |
| after_OI_fall_and_range_expand   | fade   |      500 |    350 | holdout    |       98 |     -14.63 |     11.22 |
| after_OI_fall_and_range_expand   | fade   |      500 |    350 | train      |      234 |     -14.71 |     26.5  |
| after_OI_fall_and_range_expand   | fade   |      500 |    350 | validation |      130 |     -14.58 |     13.85 |
| after_OI_fall_and_range_expand   | fade   |      800 |    500 | holdout    |       98 |     -14.63 |     11.22 |
| after_OI_fall_and_range_expand   | fade   |      800 |    500 | train      |      234 |     -14.71 |     26.5  |
| after_OI_fall_and_range_expand   | fade   |      800 |    500 | validation |      130 |     -14.58 |     13.85 |
| after_OI_fall_and_range_expand   | follow |      300 |    250 | holdout    |       98 |     -10.61 |     15.31 |
| after_OI_fall_and_range_expand   | follow |      300 |    250 | train      |      234 |     -12.57 |     25.21 |
| after_OI_fall_and_range_expand   | follow |      300 |    250 | validation |      130 |     -10.7  |     18.46 |
| after_OI_fall_and_range_expand   | follow |      500 |    350 | holdout    |       98 |     -10.61 |     15.31 |
| after_OI_fall_and_range_expand   | follow |      500 |    350 | train      |      234 |     -12.57 |     25.21 |
| after_OI_fall_and_range_expand   | follow |      500 |    350 | validation |      130 |     -10.7  |     18.46 |
| after_OI_fall_and_range_expand   | follow |      800 |    500 | holdout    |       98 |     -10.61 |     15.31 |
| after_OI_fall_and_range_expand   | follow |      800 |    500 | train      |      234 |     -12.57 |     25.21 |
| after_OI_fall_and_range_expand   | follow |      800 |    500 | validation |      130 |     -10.7  |     18.46 |
| after_OI_fall_zm1p5              | fade   |      300 |    250 | holdout    |      111 |     -13.89 |     10.81 |
| after_OI_fall_zm1p5              | fade   |      300 |    250 | train      |      272 |     -14.29 |     23.9  |
| after_OI_fall_zm1p5              | fade   |      300 |    250 | validation |      146 |     -13.12 |     15.75 |
| after_OI_fall_zm1p5              | fade   |      500 |    350 | holdout    |      111 |     -13.89 |     10.81 |
| after_OI_fall_zm1p5              | fade   |      500 |    350 | train      |      272 |     -14.29 |     23.9  |
| after_OI_fall_zm1p5              | fade   |      500 |    350 | validation |      146 |     -13.12 |     15.75 |
| after_OI_fall_zm1p5              | fade   |      800 |    500 | holdout    |      111 |     -13.89 |     10.81 |
| after_OI_fall_zm1p5              | fade   |      800 |    500 | train      |      272 |     -14.29 |     23.9  |
| after_OI_fall_zm1p5              | fade   |      800 |    500 | validation |      146 |     -13.12 |     15.75 |
| after_OI_fall_zm1p5              | follow |      300 |    250 | holdout    |      111 |     -11.34 |     14.41 |
| after_OI_fall_zm1p5              | follow |      300 |    250 | train      |      272 |     -12.9  |     23.53 |
| after_OI_fall_zm1p5              | follow |      300 |    250 | validation |      146 |     -12.1  |     14.38 |
| after_OI_fall_zm1p5              | follow |      500 |    350 | holdout    |      111 |     -11.34 |     14.41 |
| after_OI_fall_zm1p5              | follow |      500 |    350 | train      |      272 |     -12.9  |     23.53 |
| after_OI_fall_zm1p5              | follow |      500 |    350 | validation |      146 |     -12.1  |     14.38 |
| after_OI_fall_zm1p5              | follow |      800 |    500 | holdout    |      111 |     -11.34 |     14.41 |
| after_OI_fall_zm1p5              | follow |      800 |    500 | train      |      272 |     -12.9  |     23.53 |
| after_OI_fall_zm1p5              | follow |      800 |    500 | validation |      146 |     -12.1  |     14.38 |
| after_OI_rise_and_range_expand   | fade   |      300 |    250 | holdout    |       40 |     -12.85 |     15    |
| after_OI_rise_and_range_expand   | fade   |      300 |    250 | train      |       99 |     -14.37 |     24.24 |
| after_OI_rise_and_range_expand   | fade   |      300 |    250 | validation |       48 |     -14.07 |     14.58 |
| after_OI_rise_and_range_expand   | fade   |      500 |    350 | holdout    |       40 |     -12.85 |     15    |
| after_OI_rise_and_range_expand   | fade   |      500 |    350 | train      |       99 |     -14.37 |     24.24 |
| after_OI_rise_and_range_expand   | fade   |      500 |    350 | validation |       48 |     -14.07 |     14.58 |
| after_OI_rise_and_range_expand   | fade   |      800 |    500 | holdout    |       40 |     -12.85 |     15    |
| after_OI_rise_and_range_expand   | fade   |      800 |    500 | train      |       99 |     -14.37 |     24.24 |
| after_OI_rise_and_range_expand   | fade   |      800 |    500 | validation |       48 |     -14.07 |     14.58 |
| after_OI_rise_and_range_expand   | follow |      300 |    250 | holdout    |       40 |     -12.7  |      7.5  |
| after_OI_rise_and_range_expand   | follow |      300 |    250 | train      |       99 |     -12.71 |     24.24 |
| after_OI_rise_and_range_expand   | follow |      300 |    250 | validation |       48 |     -11.56 |     18.75 |
| after_OI_rise_and_range_expand   | follow |      500 |    350 | holdout    |       40 |     -12.7  |      7.5  |
| after_OI_rise_and_range_expand   | follow |      500 |    350 | train      |       99 |     -12.71 |     24.24 |
| after_OI_rise_and_range_expand   | follow |      500 |    350 | validation |       48 |     -11.56 |     18.75 |
| after_OI_rise_and_range_expand   | follow |      800 |    500 | holdout    |       40 |     -12.7  |      7.5  |
| after_OI_rise_and_range_expand   | follow |      800 |    500 | train      |       99 |     -12.71 |     24.24 |
| after_OI_rise_and_range_expand   | follow |      800 |    500 | validation |       48 |     -11.56 |     18.75 |
| after_big_down_hour              | fade   |      300 |    250 | holdout    |      123 |     -12.35 |      8.94 |
| after_big_down_hour              | fade   |      300 |    250 | train      |      312 |     -14.73 |     25.32 |
| after_big_down_hour              | fade   |      300 |    250 | validation |      162 |     -11.92 |     16.67 |
| after_big_down_hour              | fade   |      500 |    350 | holdout    |      123 |     -12.35 |      8.94 |
| after_big_down_hour              | fade   |      500 |    350 | train      |      312 |     -14.73 |     25.32 |
| after_big_down_hour              | fade   |      500 |    350 | validation |      162 |     -11.92 |     16.67 |
| after_big_down_hour              | fade   |      800 |    500 | holdout    |      123 |     -12.35 |      8.94 |
| after_big_down_hour              | fade   |      800 |    500 | train      |      312 |     -14.73 |     25.32 |
| after_big_down_hour              | fade   |      800 |    500 | validation |      162 |     -11.92 |     16.67 |
| after_big_down_hour              | follow |      300 |    250 | holdout    |      123 |     -12.94 |     13.01 |
| after_big_down_hour              | follow |      300 |    250 | train      |      312 |     -12.45 |     21.47 |
| after_big_down_hour              | follow |      300 |    250 | validation |      162 |     -13.32 |     15.43 |
| after_big_down_hour              | follow |      500 |    350 | holdout    |      123 |     -12.94 |     13.01 |
| after_big_down_hour              | follow |      500 |    350 | train      |      312 |     -12.45 |     21.47 |
| after_big_down_hour              | follow |      500 |    350 | validation |      162 |     -13.32 |     15.43 |
| after_big_down_hour              | follow |      800 |    500 | holdout    |      123 |     -12.94 |     13.01 |
| after_big_down_hour              | follow |      800 |    500 | train      |      312 |     -12.45 |     21.47 |
| after_big_down_hour              | follow |      800 |    500 | validation |      162 |     -13.32 |     15.43 |
| after_hourly_range_expansion_1p5 | fade   |      300 |    250 | holdout    |      132 |     -13.96 |      8.33 |
| after_hourly_range_expansion_1p5 | fade   |      300 |    250 | train      |      339 |     -14.11 |     24.19 |
| after_hourly_range_expansion_1p5 | fade   |      300 |    250 | validation |      178 |     -14.62 |     13.48 |
| after_hourly_range_expansion_1p5 | fade   |      500 |    350 | holdout    |      132 |     -13.96 |      8.33 |
| after_hourly_range_expansion_1p5 | fade   |      500 |    350 | train      |      339 |     -14.11 |     24.19 |
| after_hourly_range_expansion_1p5 | fade   |      500 |    350 | validation |      178 |     -14.62 |     13.48 |
| after_hourly_range_expansion_1p5 | fade   |      800 |    500 | holdout    |      132 |     -13.96 |      8.33 |
| after_hourly_range_expansion_1p5 | fade   |      800 |    500 | train      |      339 |     -14.11 |     24.19 |
| after_hourly_range_expansion_1p5 | fade   |      800 |    500 | validation |      178 |     -14.62 |     13.48 |
| after_hourly_range_expansion_1p5 | follow |      300 |    250 | holdout    |      132 |     -11.29 |     12.88 |
| after_hourly_range_expansion_1p5 | follow |      300 |    250 | train      |      339 |     -13.11 |     19.47 |
| after_hourly_range_expansion_1p5 | follow |      300 |    250 | validation |      178 |     -10.61 |     19.66 |
| after_hourly_range_expansion_1p5 | follow |      500 |    350 | holdout    |      132 |     -11.29 |     12.88 |
| after_hourly_range_expansion_1p5 | follow |      500 |    350 | train      |      339 |     -13.11 |     19.47 |
| after_hourly_range_expansion_1p5 | follow |      500 |    350 | validation |      178 |     -10.61 |     19.66 |
| after_hourly_range_expansion_1p5 | follow |      800 |    500 | holdout    |      132 |     -11.29 |     12.88 |
| after_hourly_range_expansion_1p5 | follow |      800 |    500 | train      |      339 |     -13.11 |     19.47 |
| after_hourly_range_expansion_1p5 | follow |      800 |    500 | validation |      178 |     -10.61 |     19.66 |
| after_hourly_range_expansion_2x  | fade   |      300 |    250 | holdout    |      124 |     -13.61 |     12.1  |
| after_hourly_range_expansion_2x  | fade   |      300 |    250 | train      |      298 |     -14.82 |     25.84 |
| after_hourly_range_expansion_2x  | fade   |      300 |    250 | validation |      162 |     -12.83 |     15.43 |
| after_hourly_range_expansion_2x  | fade   |      500 |    350 | holdout    |      124 |     -13.61 |     12.1  |
| after_hourly_range_expansion_2x  | fade   |      500 |    350 | train      |      298 |     -15.03 |     25.84 |
| after_hourly_range_expansion_2x  | fade   |      500 |    350 | validation |      162 |     -12.83 |     15.43 |
| after_hourly_range_expansion_2x  | fade   |      800 |    500 | holdout    |      124 |     -13.61 |     12.1  |
| after_hourly_range_expansion_2x  | fade   |      800 |    500 | train      |      298 |     -14.94 |     25.84 |
| after_hourly_range_expansion_2x  | fade   |      800 |    500 | validation |      162 |     -12.83 |     15.43 |
| after_hourly_range_expansion_2x  | follow |      300 |    250 | holdout    |      124 |     -11.66 |     15.32 |
| after_hourly_range_expansion_2x  | follow |      300 |    250 | train      |      298 |     -12.39 |     23.49 |
| after_hourly_range_expansion_2x  | follow |      300 |    250 | validation |      162 |     -12.42 |     19.14 |
| after_hourly_range_expansion_2x  | follow |      500 |    350 | holdout    |      124 |     -11.66 |     15.32 |
| after_hourly_range_expansion_2x  | follow |      500 |    350 | train      |      298 |     -12.31 |     23.49 |
| after_hourly_range_expansion_2x  | follow |      500 |    350 | validation |      162 |     -12.42 |     19.14 |
| after_hourly_range_expansion_2x  | follow |      800 |    500 | holdout    |      124 |     -11.66 |     15.32 |
| after_hourly_range_expansion_2x  | follow |      800 |    500 | train      |      298 |     -12.31 |     23.49 |
| after_hourly_range_expansion_2x  | follow |      800 |    500 | validation |      162 |     -12.42 |     19.14 |
| after_price_down_and_OI_fall     | fade   |      300 |    250 | holdout    |       88 |     -13.19 |      6.82 |
| after_price_down_and_OI_fall     | fade   |      300 |    250 | train      |      195 |     -12.6  |     31.79 |
| after_price_down_and_OI_fall     | fade   |      300 |    250 | validation |      114 |     -12.17 |     16.67 |
| after_price_down_and_OI_fall     | fade   |      500 |    350 | holdout    |       88 |     -13.19 |      6.82 |
| after_price_down_and_OI_fall     | fade   |      500 |    350 | train      |      195 |     -12.6  |     31.79 |
| after_price_down_and_OI_fall     | fade   |      500 |    350 | validation |      114 |     -12.17 |     16.67 |
| after_price_down_and_OI_fall     | fade   |      800 |    500 | holdout    |       88 |     -13.19 |      6.82 |
| after_price_down_and_OI_fall     | fade   |      800 |    500 | train      |      195 |     -12.6  |     31.79 |
| after_price_down_and_OI_fall     | fade   |      800 |    500 | validation |      114 |     -12.17 |     16.67 |
| after_price_down_and_OI_fall     | follow |      300 |    250 | holdout    |       88 |     -12.01 |     11.36 |
| after_price_down_and_OI_fall     | follow |      300 |    250 | train      |      195 |     -14.51 |     24.62 |
| after_price_down_and_OI_fall     | follow |      300 |    250 | validation |      114 |     -12.99 |     13.16 |
| after_price_down_and_OI_fall     | follow |      500 |    350 | holdout    |       88 |     -12.01 |     11.36 |
| after_price_down_and_OI_fall     | follow |      500 |    350 | train      |      195 |     -14.51 |     24.62 |
| after_price_down_and_OI_fall     | follow |      500 |    350 | validation |      114 |     -12.99 |     13.16 |
| after_price_down_and_OI_fall     | follow |      800 |    500 | holdout    |       88 |     -12.01 |     11.36 |
| after_price_down_and_OI_fall     | follow |      800 |    500 | train      |      195 |     -14.51 |     24.62 |
| after_price_down_and_OI_fall     | follow |      800 |    500 | validation |      114 |     -12.99 |     13.16 |
| after_range_expansion_and_volume | fade   |      300 |    250 | holdout    |      126 |     -14.09 |     12.7  |
| after_range_expansion_and_volume | fade   |      300 |    250 | train      |      318 |     -14.65 |     27.36 |
| after_range_expansion_and_volume | fade   |      300 |    250 | validation |      168 |     -13.84 |     14.29 |
| after_range_expansion_and_volume | fade   |      500 |    350 | holdout    |      126 |     -14.09 |     12.7  |
| after_range_expansion_and_volume | fade   |      500 |    350 | train      |      318 |     -14.65 |     27.36 |
| after_range_expansion_and_volume | fade   |      500 |    350 | validation |      168 |     -13.84 |     14.29 |
| after_range_expansion_and_volume | fade   |      800 |    500 | holdout    |      126 |     -14.09 |     12.7  |
| after_range_expansion_and_volume | fade   |      800 |    500 | train      |      318 |     -14.65 |     27.36 |
| after_range_expansion_and_volume | fade   |      800 |    500 | validation |      168 |     -13.84 |     14.29 |
| after_range_expansion_and_volume | follow |      300 |    250 | holdout    |      126 |     -11.16 |     17.46 |
| after_range_expansion_and_volume | follow |      300 |    250 | train      |      318 |     -12.56 |     25.16 |
| after_range_expansion_and_volume | follow |      300 |    250 | validation |      168 |     -11.43 |     19.05 |
| after_range_expansion_and_volume | follow |      500 |    350 | holdout    |      126 |     -11.16 |     17.46 |
| after_range_expansion_and_volume | follow |      500 |    350 | train      |      318 |     -12.56 |     25.16 |
| after_range_expansion_and_volume | follow |      500 |    350 | validation |      168 |     -11.43 |     19.05 |
| after_range_expansion_and_volume | follow |      800 |    500 | holdout    |      126 |     -11.16 |     17.46 |
| after_range_expansion_and_volume | follow |      800 |    500 | train      |      318 |     -12.56 |     25.16 |
| after_range_expansion_and_volume | follow |      800 |    500 | validation |      168 |     -11.43 |     19.05 |

## Limitations
- OHLCV/OI/funding/mark do not identify trading firms or record historical liquidation and full depth.
- Percentile uncertainty is a within-period calendar-day bootstrap, without multiple-testing correction.
- Prior analyses used some of the same final dates; future live data is the only genuinely fresh test.
- Price-index regime thresholds are normalized to trailing range; fixed $500 threshold is also shown but is regime dependent.
- Fees, funding charges, actual quotes and market impact might further worsen directional P&L.

## Saved research files
all_conditional_findings.csv, ranked_early_periods.csv, day_block_intervals.csv, directional_trade_ledger.csv, directional_trade_results.csv, six_hourly_feature_samples.csv.
