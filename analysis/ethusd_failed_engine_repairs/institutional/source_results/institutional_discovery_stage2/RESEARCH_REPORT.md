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
    107.94,
    548.13,
    3008.03
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
| after_hourly_range_expansion_2x  | normalized_range |      1033 |          2.01806 |         1.3981  |        0.61995 |            610 |             0.55653 |         504 |          0.7117  |      0.55653 |
| after_price_down_and_OI_fall     | normalized_range |       294 |          1.88856 |         1.37705 |        0.51152 |            177 |             0.51587 |         133 |          0.28226 |      0.51152 |
| after_OI_rise_and_range_expand   | normalized_range |       122 |          1.89032 |         1.39379 |        0.49653 |             61 |             0.47072 |          55 |          0.31838 |      0.47072 |
| after_OI_fall_zm1p5              | normalized_range |       523 |          1.80678 |         1.37122 |        0.43556 |            293 |             0.4342  |         221 |          0.6073  |      0.4342  |
| after_hourly_range_expansion_1p5 | normalized_range |      2019 |          1.78039 |         1.37293 |        0.40746 |           1113 |             0.42274 |         861 |          0.48175 |      0.40746 |
| after_big_down_hour              | normalized_range |      1059 |          1.8181  |         1.38139 |        0.43671 |            570 |             0.40292 |         424 |          0.41207 |      0.40292 |
| after_range_expansion_and_volume | normalized_range |      1222 |          1.88864 |         1.46482 |        0.42382 |            703 |             0.39479 |         565 |          0.57146 |      0.39479 |
| after_hourly_range_expansion_2x  | p_regime_expand  |      1033 |          0.58374 |         0.32279 |        0.26095 |            610 |             0.22873 |         504 |          0.26526 |      0.22873 |
| after_OI_fall_and_range_expand   | p_regime_expand  |       407 |          0.54791 |         0.31195 |        0.23596 |            230 |             0.20044 |         173 |          0.24035 |      0.20044 |
| after_big_down_hour              | p_regime_expand  |      1059 |          0.49764 |         0.31521 |        0.18242 |            570 |             0.17696 |         424 |          0.19068 |      0.17696 |
| after_range_expansion_and_volume | p_regime_expand  |      1222 |          0.53928 |         0.36778 |        0.1715  |            703 |             0.16393 |         565 |          0.19732 |      0.16393 |
| after_hourly_range_expansion_1p5 | p_regime_expand  |      2019 |          0.47301 |         0.31008 |        0.16293 |           1113 |             0.1714  |         861 |          0.18673 |      0.16293 |
| after_price_down_and_OI_fall     | p_regime_expand  |       294 |          0.5034  |         0.30771 |        0.19569 |            177 |             0.14827 |         133 |          0.10049 |      0.14827 |
| after_OI_fall_zm1p5              | p_regime_expand  |       523 |          0.47419 |         0.30462 |        0.16957 |            293 |             0.14096 |         221 |          0.17678 |      0.14096 |
| after_OI_rise_and_range_expand   | p_regime_expand  |       122 |          0.46721 |         0.3292  |        0.13801 |             61 |             0.15982 |          55 |          0.179   |      0.13801 |
| after_hourly_range_expansion_2x  | p500             |      1033 |          0.89545 |         0.76896 |        0.12649 |            610 |             0.16299 |         504 |          0.16239 |      0.12649 |
| after_price_down_and_OI_fall     | p500             |       294 |          0.89116 |         0.765   |        0.12616 |            177 |             0.17555 |         133 |          0.12202 |      0.12616 |
| after_OI_fall_and_range_expand   | p500             |       407 |          0.89681 |         0.77254 |        0.12427 |            230 |             0.18737 |         173 |          0.18843 |      0.12427 |
| after_hourly_range_expansion_1p5 | p500             |      2019 |          0.8633  |         0.76738 |        0.09592 |           1113 |             0.13608 |         861 |          0.11836 |      0.09592 |
| after_OI_fall_zm1p5              | p500             |       523 |          0.86424 |         0.76843 |        0.09582 |            293 |             0.16396 |         221 |          0.1566  |      0.09582 |
| after_big_down_hour              | p500             |      1059 |          0.86591 |         0.77143 |        0.09448 |            570 |             0.14046 |         424 |          0.13095 |      0.09448 |
| after_OI_rise_and_range_expand   | p500             |       122 |          0.89344 |         0.78982 |        0.10362 |             61 |             0.09044 |          55 |          0.125   |      0.09044 |
| after_range_expansion_and_volume | p500             |      1222 |          0.88871 |         0.80898 |        0.07973 |            703 |             0.10542 |         565 |          0.1043  |      0.07973 |

## Calendar-day bootstrap confidence intervals (exploratory)
Lower > 0 in multiple periods indicates consistent evidence for a volatility-regime uplift, NOT guaranteed returns. These are NOT multiplicity-adjusted.
| rule                             | period     | metric                |    n |   days |   uplift_lower |   uplift_median |   uplift_upper |
|:---------------------------------|:-----------|:----------------------|-----:|-------:|---------------:|----------------:|---------------:|
| after_OI_fall_and_range_expand   | train      | future_range_500      |  407 |    234 |        0.08637 |         0.1247  |        0.15779 |
| after_OI_fall_and_range_expand   | train      | future_vol_expansion  |  407 |    234 |        0.1791  |         0.23831 |        0.29404 |
| after_OI_fall_and_range_expand   | train      | future_vol_normalized |  407 |    234 |        0.41697 |         0.60026 |        0.79374 |
| after_OI_fall_and_range_expand   | validation | future_range_500      |  230 |    130 |        0.11468 |         0.1871  |        0.26088 |
| after_OI_fall_and_range_expand   | validation | future_vol_expansion  |  230 |    130 |        0.1344  |         0.19866 |        0.26482 |
| after_OI_fall_and_range_expand   | validation | future_vol_normalized |  230 |    130 |        0.39009 |         0.58802 |        0.78531 |
| after_OI_fall_and_range_expand   | holdout    | future_range_500      |  173 |     98 |        0.10888 |         0.1851  |        0.26847 |
| after_OI_fall_and_range_expand   | holdout    | future_vol_expansion  |  173 |     98 |        0.16074 |         0.2374  |        0.31269 |
| after_OI_fall_and_range_expand   | holdout    | future_vol_normalized |  173 |     98 |        0.39513 |         0.76543 |        1.29828 |
| after_hourly_range_expansion_2x  | train      | future_range_500      | 1033 |    298 |        0.10136 |         0.12695 |        0.15207 |
| after_hourly_range_expansion_2x  | train      | future_vol_expansion  | 1033 |    298 |        0.22225 |         0.26089 |        0.29871 |
| after_hourly_range_expansion_2x  | train      | future_vol_normalized | 1033 |    298 |        0.50217 |         0.61685 |        0.73672 |
| after_hourly_range_expansion_2x  | validation | future_range_500      |  610 |    162 |        0.10878 |         0.1623  |        0.21606 |
| after_hourly_range_expansion_2x  | validation | future_vol_expansion  |  610 |    162 |        0.18118 |         0.22718 |        0.27298 |
| after_hourly_range_expansion_2x  | validation | future_vol_normalized |  610 |    162 |        0.42144 |         0.55438 |        0.67343 |
| after_hourly_range_expansion_2x  | holdout    | future_range_500      |  504 |    125 |        0.09763 |         0.16286 |        0.22774 |
| after_hourly_range_expansion_2x  | holdout    | future_vol_expansion  |  504 |    125 |        0.20908 |         0.26632 |        0.31334 |
| after_hourly_range_expansion_2x  | holdout    | future_vol_normalized |  504 |    125 |        0.44144 |         0.70649 |        1.08879 |
| after_price_down_and_OI_fall     | train      | future_range_500      |  294 |    195 |        0.08148 |         0.12548 |        0.16438 |
| after_price_down_and_OI_fall     | train      | future_vol_expansion  |  294 |    195 |        0.13016 |         0.19474 |        0.26136 |
| after_price_down_and_OI_fall     | train      | future_vol_normalized |  294 |    195 |        0.3034  |         0.49483 |        0.72996 |
| after_price_down_and_OI_fall     | validation | future_range_500      |  177 |    114 |        0.10011 |         0.17573 |        0.25551 |
| after_price_down_and_OI_fall     | validation | future_vol_expansion  |  177 |    114 |        0.0675  |         0.14418 |        0.22854 |
| after_price_down_and_OI_fall     | validation | future_vol_normalized |  177 |    114 |        0.27732 |         0.50402 |        0.77715 |
| after_price_down_and_OI_fall     | holdout    | future_range_500      |  133 |     88 |        0.02973 |         0.12196 |        0.21078 |
| after_price_down_and_OI_fall     | holdout    | future_vol_expansion  |  133 |     88 |        0.01225 |         0.1034  |        0.20169 |
| after_price_down_and_OI_fall     | holdout    | future_vol_normalized |  133 |     88 |        0.06201 |         0.28239 |        0.50414 |
| after_OI_rise_and_range_expand   | train      | future_range_500      |  122 |     99 |        0.04385 |         0.1048  |        0.15978 |
| after_OI_rise_and_range_expand   | train      | future_vol_expansion  |  122 |     99 |        0.06148 |         0.13732 |        0.2214  |
| after_OI_rise_and_range_expand   | train      | future_vol_normalized |  122 |     99 |        0.3011  |         0.486   |        0.71396 |
| after_OI_rise_and_range_expand   | validation | future_range_500      |   61 |     48 |       -0.03513 |         0.08744 |        0.19579 |
| after_OI_rise_and_range_expand   | validation | future_vol_expansion  |   61 |     48 |        0.03618 |         0.15428 |        0.26346 |
| after_OI_rise_and_range_expand   | validation | future_vol_normalized |   61 |     48 |        0.09513 |         0.4499  |        0.86657 |
| after_OI_rise_and_range_expand   | holdout    | future_range_500      |   55 |     40 |       -0.00966 |         0.12302 |        0.26189 |
| after_OI_rise_and_range_expand   | holdout    | future_vol_expansion  |   55 |     40 |        0.06064 |         0.17619 |        0.29827 |
| after_OI_rise_and_range_expand   | holdout    | future_vol_normalized |   55 |     40 |        0.04423 |         0.31255 |        0.57888 |
| after_OI_fall_zm1p5              | train      | future_range_500      |  523 |    272 |        0.05876 |         0.09667 |        0.13052 |
| after_OI_fall_zm1p5              | train      | future_vol_expansion  |  523 |    272 |        0.12126 |         0.17025 |        0.21907 |
| after_OI_fall_zm1p5              | train      | future_vol_normalized |  523 |    272 |        0.29921 |         0.43627 |        0.60267 |
| after_OI_fall_zm1p5              | validation | future_range_500      |  293 |    146 |        0.09034 |         0.16655 |        0.22555 |
| after_OI_fall_zm1p5              | validation | future_vol_expansion  |  293 |    146 |        0.07564 |         0.14022 |        0.20617 |
| after_OI_fall_zm1p5              | validation | future_vol_normalized |  293 |    146 |        0.24846 |         0.43011 |        0.62194 |
| after_OI_fall_zm1p5              | holdout    | future_range_500      |  221 |    111 |        0.08033 |         0.15264 |        0.23136 |
| after_OI_fall_zm1p5              | holdout    | future_vol_expansion  |  221 |    111 |        0.1036  |         0.173   |        0.24475 |
| after_OI_fall_zm1p5              | holdout    | future_vol_normalized |  221 |    111 |        0.26694 |         0.56981 |        1.02228 |
| after_hourly_range_expansion_1p5 | train      | future_range_500      | 2019 |    339 |        0.07122 |         0.09565 |        0.11942 |
| after_hourly_range_expansion_1p5 | train      | future_vol_expansion  | 2019 |    339 |        0.13275 |         0.16229 |        0.19208 |
| after_hourly_range_expansion_1p5 | train      | future_vol_normalized | 2019 |    339 |        0.32018 |         0.4036  |        0.49544 |
| after_hourly_range_expansion_1p5 | validation | future_range_500      | 1113 |    178 |        0.09475 |         0.1352  |        0.18184 |
| after_hourly_range_expansion_1p5 | validation | future_vol_expansion  | 1113 |    178 |        0.12963 |         0.17056 |        0.20989 |
| after_hourly_range_expansion_1p5 | validation | future_vol_normalized | 1113 |    178 |        0.32357 |         0.42102 |        0.51919 |
| after_hourly_range_expansion_1p5 | holdout    | future_range_500      |  861 |    133 |        0.06624 |         0.11999 |        0.17134 |
| after_hourly_range_expansion_1p5 | holdout    | future_vol_expansion  |  861 |    133 |        0.14042 |         0.18579 |        0.2303  |
| after_hourly_range_expansion_1p5 | holdout    | future_vol_normalized |  861 |    133 |        0.28886 |         0.47502 |        0.69793 |
| after_big_down_hour              | train      | future_range_500      | 1059 |    312 |        0.06451 |         0.09578 |        0.12165 |
| after_big_down_hour              | train      | future_vol_expansion  | 1059 |    312 |        0.14509 |         0.18338 |        0.22048 |
| after_big_down_hour              | train      | future_vol_normalized | 1059 |    312 |        0.32592 |         0.43775 |        0.55061 |
| after_big_down_hour              | validation | future_range_500      |  570 |    162 |        0.08898 |         0.13801 |        0.18883 |
| after_big_down_hour              | validation | future_vol_expansion  |  570 |    162 |        0.12573 |         0.17665 |        0.21765 |
| after_big_down_hour              | validation | future_vol_normalized |  570 |    162 |        0.28352 |         0.40001 |        0.51986 |
| after_big_down_hour              | holdout    | future_range_500      |  424 |    123 |        0.06511 |         0.13141 |        0.19534 |
| after_big_down_hour              | holdout    | future_vol_expansion  |  424 |    123 |        0.12507 |         0.19032 |        0.24943 |
| after_big_down_hour              | holdout    | future_vol_normalized |  424 |    123 |        0.25742 |         0.40909 |        0.57814 |
| after_range_expansion_and_volume | train      | future_range_500      | 1222 |    318 |        0.05423 |         0.08055 |        0.10588 |
| after_range_expansion_and_volume | train      | future_vol_expansion  | 1222 |    318 |        0.13426 |         0.17221 |        0.20715 |
| after_range_expansion_and_volume | train      | future_vol_normalized | 1222 |    318 |        0.33209 |         0.42258 |        0.52259 |
| after_range_expansion_and_volume | validation | future_range_500      |  703 |    168 |        0.05751 |         0.10549 |        0.15031 |
| after_range_expansion_and_volume | validation | future_vol_expansion  |  703 |    168 |        0.11255 |         0.16413 |        0.20912 |
| after_range_expansion_and_volume | validation | future_vol_normalized |  703 |    168 |        0.27488 |         0.3967  |        0.51268 |
| after_range_expansion_and_volume | holdout    | future_range_500      |  565 |    126 |        0.04812 |         0.10531 |        0.15302 |
| after_range_expansion_and_volume | holdout    | future_vol_expansion  |  565 |    126 |        0.14767 |         0.19717 |        0.24076 |
| after_range_expansion_and_volume | holdout    | future_vol_normalized |  565 |    126 |        0.34012 |         0.56009 |        0.87636 |

## Execution realism
Optional directional follow/fade simulation uses next hourly OPEN, next 60 individual minutes with stop-first ambiguous fills, taker fee each side 0.05% plus 18% GST, and 5 BTC-point adverse slippage per side.
One trade per NY day per rule, restricted to days with condition; +300/-250, +500/-350, +800/-500, one-hour timeout.
Directional simulated results are separate from non-directional range findings. Do not conflate forecastable volatility with forecastable direction.
| rule                             | mode   |   target |   stop | period     |   trades |   mean_net |   win_pct |
|:---------------------------------|:-------|---------:|-------:|:-----------|---------:|-----------:|----------:|
| after_OI_fall_and_range_expand   | fade   |      300 |    250 | holdout    |       98 |    -109.01 |     38.78 |
| after_OI_fall_and_range_expand   | fade   |      300 |    250 | train      |      234 |    -101.42 |     45.73 |
| after_OI_fall_and_range_expand   | fade   |      300 |    250 | validation |      130 |    -103.23 |     37.69 |
| after_OI_fall_and_range_expand   | fade   |      500 |    350 | holdout    |       98 |    -107.59 |     40.82 |
| after_OI_fall_and_range_expand   | fade   |      500 |    350 | train      |      234 |    -106.23 |     39.32 |
| after_OI_fall_and_range_expand   | fade   |      500 |    350 | validation |      130 |    -139.86 |     31.54 |
| after_OI_fall_and_range_expand   | fade   |      800 |    500 | holdout    |       98 |    -103.94 |     42.86 |
| after_OI_fall_and_range_expand   | fade   |      800 |    500 | train      |      234 |    -101.82 |     39.32 |
| after_OI_fall_and_range_expand   | fade   |      800 |    500 | validation |      130 |    -155.97 |     31.54 |
| after_OI_fall_and_range_expand   | follow |      300 |    250 | holdout    |       98 |     -57.54 |     47.96 |
| after_OI_fall_and_range_expand   | follow |      300 |    250 | train      |      234 |    -123.93 |     41.88 |
| after_OI_fall_and_range_expand   | follow |      300 |    250 | validation |      130 |     -76.64 |     40    |
| after_OI_fall_and_range_expand   | follow |      500 |    350 | holdout    |       98 |     -63.79 |     39.8  |
| after_OI_fall_and_range_expand   | follow |      500 |    350 | train      |      234 |    -113    |     38.89 |
| after_OI_fall_and_range_expand   | follow |      500 |    350 | validation |      130 |     -27.3  |     40.77 |
| after_OI_fall_and_range_expand   | follow |      800 |    500 | holdout    |       98 |     -53.62 |     37.76 |
| after_OI_fall_and_range_expand   | follow |      800 |    500 | train      |      234 |    -136.82 |     35.04 |
| after_OI_fall_and_range_expand   | follow |      800 |    500 | validation |      130 |     -41.48 |     37.69 |
| after_OI_fall_zm1p5              | fade   |      300 |    250 | holdout    |      111 |     -91.07 |     40.54 |
| after_OI_fall_zm1p5              | fade   |      300 |    250 | train      |      272 |    -105.37 |     44.85 |
| after_OI_fall_zm1p5              | fade   |      300 |    250 | validation |      146 |     -89.05 |     38.36 |
| after_OI_fall_zm1p5              | fade   |      500 |    350 | holdout    |      111 |     -99.22 |     40.54 |
| after_OI_fall_zm1p5              | fade   |      500 |    350 | train      |      272 |    -114.62 |     38.24 |
| after_OI_fall_zm1p5              | fade   |      500 |    350 | validation |      146 |    -102.38 |     35.62 |
| after_OI_fall_zm1p5              | fade   |      800 |    500 | holdout    |      111 |    -104.26 |     41.44 |
| after_OI_fall_zm1p5              | fade   |      800 |    500 | train      |      272 |    -106.36 |     39.34 |
| after_OI_fall_zm1p5              | fade   |      800 |    500 | validation |      146 |     -99.58 |     36.3  |
| after_OI_fall_zm1p5              | follow |      300 |    250 | holdout    |      111 |     -61.44 |     45.05 |
| after_OI_fall_zm1p5              | follow |      300 |    250 | train      |      272 |    -115.5  |     42.65 |
| after_OI_fall_zm1p5              | follow |      300 |    250 | validation |      146 |     -87.04 |     36.99 |
| after_OI_fall_zm1p5              | follow |      500 |    350 | holdout    |      111 |     -66.27 |     37.84 |
| after_OI_fall_zm1p5              | follow |      500 |    350 | train      |      272 |    -111.01 |     38.97 |
| after_OI_fall_zm1p5              | follow |      500 |    350 | validation |      146 |     -59.1  |     36.3  |
| after_OI_fall_zm1p5              | follow |      800 |    500 | holdout    |      111 |     -64.75 |     34.23 |
| after_OI_fall_zm1p5              | follow |      800 |    500 | train      |      272 |    -126.97 |     34.93 |
| after_OI_fall_zm1p5              | follow |      800 |    500 | validation |      146 |     -73.12 |     33.56 |
| after_OI_rise_and_range_expand   | fade   |      300 |    250 | holdout    |       40 |     -82.72 |     42.5  |
| after_OI_rise_and_range_expand   | fade   |      300 |    250 | train      |       99 |     -73.1  |     50.51 |
| after_OI_rise_and_range_expand   | fade   |      300 |    250 | validation |       48 |     -86.2  |     37.5  |
| after_OI_rise_and_range_expand   | fade   |      500 |    350 | holdout    |       40 |     -69.9  |     37.5  |
| after_OI_rise_and_range_expand   | fade   |      500 |    350 | train      |       99 |    -103.4  |     41.41 |
| after_OI_rise_and_range_expand   | fade   |      500 |    350 | validation |       48 |     -98.23 |     33.33 |
| after_OI_rise_and_range_expand   | fade   |      800 |    500 | holdout    |       40 |     -89.6  |     35    |
| after_OI_rise_and_range_expand   | fade   |      800 |    500 | train      |       99 |    -122.23 |     40.4  |
| after_OI_rise_and_range_expand   | fade   |      800 |    500 | validation |       48 |     -90.91 |     35.42 |
| after_OI_rise_and_range_expand   | follow |      300 |    250 | holdout    |       40 |     -86.27 |     42.5  |
| after_OI_rise_and_range_expand   | follow |      300 |    250 | train      |       99 |    -123.55 |     42.42 |
| after_OI_rise_and_range_expand   | follow |      300 |    250 | validation |       48 |    -120.3  |     33.33 |
| after_OI_rise_and_range_expand   | follow |      500 |    350 | holdout    |       40 |    -102.05 |     37.5  |
| after_OI_rise_and_range_expand   | follow |      500 |    350 | train      |       99 |    -141.68 |     35.35 |
| after_OI_rise_and_range_expand   | follow |      500 |    350 | validation |       48 |    -108.64 |     31.25 |
| after_OI_rise_and_range_expand   | follow |      800 |    500 | holdout    |       40 |    -102.78 |     40    |
| after_OI_rise_and_range_expand   | follow |      800 |    500 | train      |       99 |     -72.3  |     41.41 |
| after_OI_rise_and_range_expand   | follow |      800 |    500 | validation |       48 |     -56.41 |     33.33 |
| after_big_down_hour              | fade   |      300 |    250 | holdout    |      123 |     -99.91 |     40.65 |
| after_big_down_hour              | fade   |      300 |    250 | train      |      312 |     -95.16 |     46.15 |
| after_big_down_hour              | fade   |      300 |    250 | validation |      162 |     -95.12 |     36.42 |
| after_big_down_hour              | fade   |      500 |    350 | holdout    |      123 |     -82.87 |     43.09 |
| after_big_down_hour              | fade   |      500 |    350 | train      |      312 |     -84.61 |     43.91 |
| after_big_down_hour              | fade   |      500 |    350 | validation |      162 |    -119.33 |     32.1  |
| after_big_down_hour              | fade   |      800 |    500 | holdout    |      123 |     -81.55 |     43.9  |
| after_big_down_hour              | fade   |      800 |    500 | train      |      312 |     -83.53 |     43.59 |
| after_big_down_hour              | fade   |      800 |    500 | validation |      162 |     -72.45 |     39.51 |
| after_big_down_hour              | follow |      300 |    250 | holdout    |      123 |     -78.4  |     38.21 |
| after_big_down_hour              | follow |      300 |    250 | train      |      312 |    -117.87 |     42.31 |
| after_big_down_hour              | follow |      300 |    250 | validation |      162 |     -65.81 |     42.59 |
| after_big_down_hour              | follow |      500 |    350 | holdout    |      123 |     -87.53 |     32.52 |
| after_big_down_hour              | follow |      500 |    350 | train      |      312 |    -132.32 |     35.9  |
| after_big_down_hour              | follow |      500 |    350 | validation |      162 |     -81.99 |     33.95 |
| after_big_down_hour              | follow |      800 |    500 | holdout    |      123 |     -92.45 |     28.46 |
| after_big_down_hour              | follow |      800 |    500 | train      |      312 |    -143.61 |     33.33 |
| after_big_down_hour              | follow |      800 |    500 | validation |      162 |     -76.21 |     33.33 |
| after_hourly_range_expansion_1p5 | fade   |      300 |    250 | holdout    |      132 |     -90.06 |     42.42 |
| after_hourly_range_expansion_1p5 | fade   |      300 |    250 | train      |      339 |     -92.07 |     46.02 |
| after_hourly_range_expansion_1p5 | fade   |      300 |    250 | validation |      178 |    -118.78 |     30.9  |
| after_hourly_range_expansion_1p5 | fade   |      500 |    350 | holdout    |      132 |     -91.57 |     40.91 |
| after_hourly_range_expansion_1p5 | fade   |      500 |    350 | train      |      339 |     -93.99 |     41.3  |
| after_hourly_range_expansion_1p5 | fade   |      500 |    350 | validation |      178 |    -147.24 |     28.09 |
| after_hourly_range_expansion_1p5 | fade   |      800 |    500 | holdout    |      132 |    -110.62 |     38.64 |
| after_hourly_range_expansion_1p5 | fade   |      800 |    500 | train      |      339 |    -102.2  |     40.12 |
| after_hourly_range_expansion_1p5 | fade   |      800 |    500 | validation |      178 |    -136.27 |     32.02 |
| after_hourly_range_expansion_1p5 | follow |      300 |    250 | holdout    |      132 |     -73.56 |     39.39 |
| after_hourly_range_expansion_1p5 | follow |      300 |    250 | train      |      339 |    -121.28 |     40.71 |
| after_hourly_range_expansion_1p5 | follow |      300 |    250 | validation |      178 |     -39.07 |     44.38 |
| after_hourly_range_expansion_1p5 | follow |      500 |    350 | holdout    |      132 |     -66.91 |     37.88 |
| after_hourly_range_expansion_1p5 | follow |      500 |    350 | train      |      339 |    -123.6  |     35.99 |
| after_hourly_range_expansion_1p5 | follow |      500 |    350 | validation |      178 |     -21.36 |     39.89 |
| after_hourly_range_expansion_1p5 | follow |      800 |    500 | holdout    |      132 |     -75.32 |     34.85 |
| after_hourly_range_expansion_1p5 | follow |      800 |    500 | train      |      339 |    -151.93 |     33.04 |
| after_hourly_range_expansion_1p5 | follow |      800 |    500 | validation |      178 |     -23.07 |     36.52 |
| after_hourly_range_expansion_2x  | fade   |      300 |    250 | holdout    |      124 |     -98.01 |     38.71 |
| after_hourly_range_expansion_2x  | fade   |      300 |    250 | train      |      298 |    -120.2  |     42.28 |
| after_hourly_range_expansion_2x  | fade   |      300 |    250 | validation |      162 |     -98.74 |     38.27 |
| after_hourly_range_expansion_2x  | fade   |      500 |    350 | holdout    |      124 |     -86.62 |     39.52 |
| after_hourly_range_expansion_2x  | fade   |      500 |    350 | train      |      298 |    -114.8  |     39.93 |
| after_hourly_range_expansion_2x  | fade   |      500 |    350 | validation |      162 |    -126.59 |     35.19 |
| after_hourly_range_expansion_2x  | fade   |      800 |    500 | holdout    |      124 |    -106.55 |     39.52 |
| after_hourly_range_expansion_2x  | fade   |      800 |    500 | train      |      298 |    -147.17 |     37.58 |
| after_hourly_range_expansion_2x  | fade   |      800 |    500 | validation |      162 |    -101.77 |     38.27 |
| after_hourly_range_expansion_2x  | follow |      300 |    250 | holdout    |      124 |     -76.16 |     41.13 |
| after_hourly_range_expansion_2x  | follow |      300 |    250 | train      |      298 |     -93.9  |     46.98 |
| after_hourly_range_expansion_2x  | follow |      300 |    250 | validation |      162 |     -61.05 |     43.21 |
| after_hourly_range_expansion_2x  | follow |      500 |    350 | holdout    |      124 |     -58.08 |     38.71 |
| after_hourly_range_expansion_2x  | follow |      500 |    350 | train      |      298 |     -91.99 |     41.28 |
| after_hourly_range_expansion_2x  | follow |      500 |    350 | validation |      162 |     -61.93 |     37.65 |
| after_hourly_range_expansion_2x  | follow |      800 |    500 | holdout    |      124 |     -83.76 |     35.48 |
| after_hourly_range_expansion_2x  | follow |      800 |    500 | train      |      298 |    -124.09 |     36.58 |
| after_hourly_range_expansion_2x  | follow |      800 |    500 | validation |      162 |     -49.87 |     37.04 |
| after_price_down_and_OI_fall     | fade   |      300 |    250 | holdout    |       88 |     -94.97 |     37.5  |
| after_price_down_and_OI_fall     | fade   |      300 |    250 | train      |      195 |    -105.12 |     46.15 |
| after_price_down_and_OI_fall     | fade   |      300 |    250 | validation |      114 |    -101.17 |     35.96 |
| after_price_down_and_OI_fall     | fade   |      500 |    350 | holdout    |       88 |     -99.62 |     38.64 |
| after_price_down_and_OI_fall     | fade   |      500 |    350 | train      |      195 |     -76.99 |     45.13 |
| after_price_down_and_OI_fall     | fade   |      500 |    350 | validation |      114 |    -104.06 |     35.09 |
| after_price_down_and_OI_fall     | fade   |      800 |    500 | holdout    |       88 |     -94.69 |     40.91 |
| after_price_down_and_OI_fall     | fade   |      800 |    500 | train      |      195 |     -57.88 |     46.67 |
| after_price_down_and_OI_fall     | fade   |      800 |    500 | validation |      114 |     -66.75 |     39.47 |
| after_price_down_and_OI_fall     | follow |      300 |    250 | holdout    |       88 |     -68.87 |     38.64 |
| after_price_down_and_OI_fall     | follow |      300 |    250 | train      |      195 |    -121.08 |     42.56 |
| after_price_down_and_OI_fall     | follow |      300 |    250 | validation |      114 |     -68.56 |     40.35 |
| after_price_down_and_OI_fall     | follow |      500 |    350 | holdout    |       88 |     -81.5  |     30.68 |
| after_price_down_and_OI_fall     | follow |      500 |    350 | train      |      195 |    -145.73 |     35.9  |
| after_price_down_and_OI_fall     | follow |      500 |    350 | validation |      114 |     -74.87 |     33.33 |
| after_price_down_and_OI_fall     | follow |      800 |    500 | holdout    |       88 |     -66.37 |     28.41 |
| after_price_down_and_OI_fall     | follow |      800 |    500 | train      |      195 |    -181.45 |     30.77 |
| after_price_down_and_OI_fall     | follow |      800 |    500 | validation |      114 |     -83.49 |     31.58 |
| after_range_expansion_and_volume | fade   |      300 |    250 | holdout    |      126 |     -91.63 |     42.06 |
| after_range_expansion_and_volume | fade   |      300 |    250 | train      |      318 |    -107.83 |     44.34 |
| after_range_expansion_and_volume | fade   |      300 |    250 | validation |      168 |    -128.03 |     30.36 |
| after_range_expansion_and_volume | fade   |      500 |    350 | holdout    |      126 |     -86.15 |     42.06 |
| after_range_expansion_and_volume | fade   |      500 |    350 | train      |      318 |    -117.63 |     40.25 |
| after_range_expansion_and_volume | fade   |      500 |    350 | validation |      168 |    -151.36 |     27.98 |
| after_range_expansion_and_volume | fade   |      800 |    500 | holdout    |      126 |    -105.15 |     41.27 |
| after_range_expansion_and_volume | fade   |      800 |    500 | train      |      318 |    -111.32 |     41.19 |
| after_range_expansion_and_volume | fade   |      800 |    500 | validation |      168 |    -141.67 |     31.55 |
| after_range_expansion_and_volume | follow |      300 |    250 | holdout    |      126 |     -77.5  |     38.89 |
| after_range_expansion_and_volume | follow |      300 |    250 | train      |      318 |    -111.2  |     43.4  |
| after_range_expansion_and_volume | follow |      300 |    250 | validation |      168 |     -45.07 |     44.64 |
| after_range_expansion_and_volume | follow |      500 |    350 | holdout    |      126 |     -67.11 |     37.3  |
| after_range_expansion_and_volume | follow |      500 |    350 | train      |      318 |     -98.25 |     40.25 |
| after_range_expansion_and_volume | follow |      500 |    350 | validation |      168 |     -16.91 |     42.26 |
| after_range_expansion_and_volume | follow |      800 |    500 | holdout    |      126 |     -60.32 |     34.92 |
| after_range_expansion_and_volume | follow |      800 |    500 | train      |      318 |    -127.3  |     36.16 |
| after_range_expansion_and_volume | follow |      800 |    500 | validation |      168 |     -39.38 |     37.5  |

## Limitations
- OHLCV/OI/funding/mark do not identify trading firms or record historical liquidation and full depth.
- Percentile uncertainty is a within-period calendar-day bootstrap, without multiple-testing correction.
- Prior analyses used some of the same final dates; future live data is the only genuinely fresh test.
- Price-index regime thresholds are normalized to trailing range; fixed $500 threshold is also shown but is regime dependent.
- Fees, funding charges, actual quotes and market impact might further worsen directional P&L.

## Saved research files
all_conditional_findings.csv, ranked_early_periods.csv, day_block_intervals.csv, directional_trade_ledger.csv, directional_trade_results.csv, six_hourly_feature_samples.csv.
