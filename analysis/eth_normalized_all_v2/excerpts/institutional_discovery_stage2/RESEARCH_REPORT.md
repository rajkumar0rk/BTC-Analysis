# Finding actual BTC futures market behavior: non-directional predictive regimes

## Research question
Before trying BUY/SELL rules, can market-structure, participation, open interest, basis, funding, and time context forecast the NEXT hour's price movement RANGE? A future hourly HIGH-LOW is a volatility observation, not an executable trading profit.

All 1-hour samples are nonoverlapping, and all features use completed current/prior hourly candles. 2025=training; Jan-Jun 2026=validation; July-Oct 2026=chronological recheck (NOT globally untouched after earlier analyses).
The baseline controls for next-hour New York clock hour and weekday/weekend, so trivial clock effects are reduced. Regime signal rates are measured against matched baseline rates within each chronological period.

## Source/quality
~~~json
{
  "futures_1m": 963360,
  "mark_1m": 963360,
  "OI_5m": 192672,
  "funding_1h": 16056,
  "available_hourly_events": 15875,
  "first": "2025-01-08 12:00:00+00:00",
  "last": "2026-10-31 22:00:00+00:00",
  "oi_changes_pct_p01_p50_p99": [
    -17.01,
    0.357,
    15.011
  ],
  "hourly_range_points_p01_p50_p99": [
    107.94,
    552.34,
    3015.49
  ],
  "funding_distinct_values": 776,
  "funding_fraction_exact_point01": 0.6139,
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
| after_OI_fall_and_range_expand   | normalized_range |       408 |          1.97907 |         1.38356 |        0.59551 |            230 |             0.58637 |         154 |          0.84682 |      0.58637 |
| after_hourly_range_expansion_2x  | normalized_range |      1032 |          2.01668 |         1.39785 |        0.61883 |            610 |             0.55653 |         433 |          0.71819 |      0.55653 |
| after_price_down_and_OI_fall     | normalized_range |       294 |          1.88856 |         1.37705 |        0.51152 |            177 |             0.51587 |         114 |          0.2804  |      0.51152 |
| after_OI_rise_and_range_expand   | normalized_range |       122 |          1.89032 |         1.39379 |        0.49653 |             61 |             0.47072 |          51 |          0.31015 |      0.47072 |
| after_OI_fall_zm1p5              | normalized_range |       523 |          1.80678 |         1.37122 |        0.43556 |            293 |             0.4342  |         199 |          0.63811 |      0.4342  |
| after_hourly_range_expansion_1p5 | normalized_range |      2020 |          1.77982 |         1.37282 |        0.40701 |           1112 |             0.4214  |         747 |          0.48184 |      0.40701 |
| after_big_down_hour              | normalized_range |      1060 |          1.81699 |         1.38117 |        0.43582 |            570 |             0.40292 |         356 |          0.37631 |      0.40292 |
| after_range_expansion_and_volume | normalized_range |      1222 |          1.88864 |         1.46482 |        0.42382 |            703 |             0.39479 |         481 |          0.56125 |      0.39479 |
| after_hourly_range_expansion_2x  | p_regime_expand  |      1032 |          0.58333 |         0.32271 |        0.26062 |            610 |             0.22873 |         433 |          0.26545 |      0.22873 |
| after_OI_fall_and_range_expand   | p_regime_expand  |       408 |          0.54657 |         0.31172 |        0.23485 |            230 |             0.20044 |         154 |          0.2453  |      0.20044 |
| after_big_down_hour              | p_regime_expand  |      1060 |          0.49717 |         0.31517 |        0.182   |            570 |             0.17696 |         356 |          0.1762  |      0.17696 |
| after_range_expansion_and_volume | p_regime_expand  |      1222 |          0.53928 |         0.36785 |        0.17143 |            703 |             0.16393 |         481 |          0.19548 |      0.16393 |
| after_hourly_range_expansion_1p5 | p_regime_expand  |      2020 |          0.47277 |         0.31009 |        0.16268 |           1112 |             0.17085 |         747 |          0.18548 |      0.16268 |
| after_price_down_and_OI_fall     | p_regime_expand  |       294 |          0.5034  |         0.30781 |        0.1956  |            177 |             0.14827 |         114 |          0.09312 |      0.14827 |
| after_OI_fall_zm1p5              | p_regime_expand  |       523 |          0.47419 |         0.3047  |        0.16949 |            293 |             0.14096 |         199 |          0.18147 |      0.14096 |
| after_OI_rise_and_range_expand   | p_regime_expand  |       122 |          0.46721 |         0.32923 |        0.13798 |             61 |             0.15982 |          51 |          0.16651 |      0.13798 |
| after_hourly_range_expansion_2x  | p500             |      1032 |          0.89535 |         0.76883 |        0.12652 |            610 |             0.16299 |         433 |          0.15419 |      0.12652 |
| after_price_down_and_OI_fall     | p500             |       294 |          0.89116 |         0.765   |        0.12616 |            177 |             0.17555 |         114 |          0.10236 |      0.12616 |
| after_OI_fall_and_range_expand   | p500             |       408 |          0.89461 |         0.77241 |        0.12219 |            230 |             0.18737 |         154 |          0.18537 |      0.12219 |
| after_OI_fall_zm1p5              | p500             |       523 |          0.86424 |         0.76843 |        0.09582 |            293 |             0.16396 |         199 |          0.15372 |      0.09582 |
| after_hourly_range_expansion_1p5 | p500             |      2020 |          0.86287 |         0.76735 |        0.09552 |           1112 |             0.13555 |         747 |          0.11503 |      0.09552 |
| after_big_down_hour              | p500             |      1060 |          0.86509 |         0.77139 |        0.09371 |            570 |             0.14046 |         356 |          0.10579 |      0.09371 |
| after_OI_rise_and_range_expand   | p500             |       122 |          0.89344 |         0.78982 |        0.10362 |             61 |             0.09044 |          51 |          0.10469 |      0.09044 |
| after_range_expansion_and_volume | p500             |      1222 |          0.88871 |         0.80898 |        0.07973 |            703 |             0.10542 |         481 |          0.09764 |      0.07973 |

## Calendar-day bootstrap confidence intervals (exploratory)
Lower > 0 in multiple periods indicates consistent evidence for a volatility-regime uplift, NOT guaranteed returns. These are NOT multiplicity-adjusted.
| rule                             | period     | metric                |    n |   days |   uplift_lower |   uplift_median |   uplift_upper |
|:---------------------------------|:-----------|:----------------------|-----:|-------:|---------------:|----------------:|---------------:|
| after_OI_fall_and_range_expand   | train      | future_range_500      |  408 |    235 |        0.0855  |         0.12245 |        0.15503 |
| after_OI_fall_and_range_expand   | train      | future_vol_expansion  |  408 |    235 |        0.17761 |         0.23583 |        0.28969 |
| after_OI_fall_and_range_expand   | train      | future_vol_normalized |  408 |    235 |        0.43787 |         0.59664 |        0.77328 |
| after_OI_fall_and_range_expand   | validation | future_range_500      |  230 |    130 |        0.11468 |         0.1871  |        0.26088 |
| after_OI_fall_and_range_expand   | validation | future_vol_expansion  |  230 |    130 |        0.1344  |         0.19866 |        0.26482 |
| after_OI_fall_and_range_expand   | validation | future_vol_normalized |  230 |    130 |        0.39009 |         0.58802 |        0.78531 |
| after_OI_fall_and_range_expand   | holdout    | future_range_500      |  154 |     87 |        0.10067 |         0.18396 |        0.26906 |
| after_OI_fall_and_range_expand   | holdout    | future_vol_expansion  |  154 |     87 |        0.16674 |         0.24377 |        0.31672 |
| after_OI_fall_and_range_expand   | holdout    | future_vol_normalized |  154 |     87 |        0.41999 |         0.83559 |        1.335   |
| after_hourly_range_expansion_2x  | train      | future_range_500      | 1032 |    298 |        0.10137 |         0.12698 |        0.15209 |
| after_hourly_range_expansion_2x  | train      | future_vol_expansion  | 1032 |    298 |        0.22158 |         0.26054 |        0.29816 |
| after_hourly_range_expansion_2x  | train      | future_vol_normalized | 1032 |    298 |        0.50211 |         0.61589 |        0.73619 |
| after_hourly_range_expansion_2x  | validation | future_range_500      |  610 |    162 |        0.10878 |         0.1623  |        0.21606 |
| after_hourly_range_expansion_2x  | validation | future_vol_expansion  |  610 |    162 |        0.18118 |         0.22718 |        0.27298 |
| after_hourly_range_expansion_2x  | validation | future_vol_normalized |  610 |    162 |        0.42144 |         0.55438 |        0.67343 |
| after_hourly_range_expansion_2x  | holdout    | future_range_500      |  433 |    111 |        0.07767 |         0.154   |        0.22874 |
| after_hourly_range_expansion_2x  | holdout    | future_vol_expansion  |  433 |    111 |        0.20499 |         0.26488 |        0.31911 |
| after_hourly_range_expansion_2x  | holdout    | future_vol_normalized |  433 |    111 |        0.41033 |         0.69266 |        1.084   |
| after_price_down_and_OI_fall     | train      | future_range_500      |  294 |    195 |        0.08148 |         0.12548 |        0.16438 |
| after_price_down_and_OI_fall     | train      | future_vol_expansion  |  294 |    195 |        0.13007 |         0.19463 |        0.26127 |
| after_price_down_and_OI_fall     | train      | future_vol_normalized |  294 |    195 |        0.3034  |         0.49483 |        0.72996 |
| after_price_down_and_OI_fall     | validation | future_range_500      |  177 |    114 |        0.10011 |         0.17573 |        0.25551 |
| after_price_down_and_OI_fall     | validation | future_vol_expansion  |  177 |    114 |        0.0675  |         0.14418 |        0.22854 |
| after_price_down_and_OI_fall     | validation | future_vol_normalized |  177 |    114 |        0.27732 |         0.50402 |        0.77715 |
| after_price_down_and_OI_fall     | holdout    | future_range_500      |  114 |     77 |       -0.01231 |         0.10273 |        0.20488 |
| after_price_down_and_OI_fall     | holdout    | future_vol_expansion  |  114 |     77 |       -0.00286 |         0.09504 |        0.19251 |
| after_price_down_and_OI_fall     | holdout    | future_vol_normalized |  114 |     77 |        0.04922 |         0.28952 |        0.52398 |
| after_OI_rise_and_range_expand   | train      | future_range_500      |  122 |     99 |        0.04385 |         0.1048  |        0.15978 |
| after_OI_rise_and_range_expand   | train      | future_vol_expansion  |  122 |     99 |        0.06147 |         0.1373  |        0.22137 |
| after_OI_rise_and_range_expand   | train      | future_vol_normalized |  122 |     99 |        0.3011  |         0.486   |        0.71396 |
| after_OI_rise_and_range_expand   | validation | future_range_500      |   61 |     48 |       -0.03513 |         0.08744 |        0.19579 |
| after_OI_rise_and_range_expand   | validation | future_vol_expansion  |   61 |     48 |        0.03618 |         0.15428 |        0.26346 |
| after_OI_rise_and_range_expand   | validation | future_vol_normalized |   61 |     48 |        0.09513 |         0.4499  |        0.86657 |
| after_OI_rise_and_range_expand   | holdout    | future_range_500      |   51 |     36 |       -0.04538 |         0.10643 |        0.24274 |
| after_OI_rise_and_range_expand   | holdout    | future_vol_expansion  |   51 |     36 |        0.04916 |         0.16804 |        0.29367 |
| after_OI_rise_and_range_expand   | holdout    | future_vol_normalized |   51 |     36 |        0.03451 |         0.31161 |        0.59122 |
| after_OI_fall_zm1p5              | train      | future_range_500      |  523 |    272 |        0.05876 |         0.09667 |        0.13052 |
| after_OI_fall_zm1p5              | train      | future_vol_expansion  |  523 |    272 |        0.12117 |         0.17016 |        0.21899 |
| after_OI_fall_zm1p5              | train      | future_vol_normalized |  523 |    272 |        0.29921 |         0.43627 |        0.60267 |
| after_OI_fall_zm1p5              | validation | future_range_500      |  293 |    146 |        0.09034 |         0.16655 |        0.22555 |
| after_OI_fall_zm1p5              | validation | future_vol_expansion  |  293 |    146 |        0.07564 |         0.14022 |        0.20617 |
| after_OI_fall_zm1p5              | validation | future_vol_normalized |  293 |    146 |        0.24846 |         0.43011 |        0.62194 |
| after_OI_fall_zm1p5              | holdout    | future_range_500      |  199 |    100 |        0.07424 |         0.15546 |        0.23144 |
| after_OI_fall_zm1p5              | holdout    | future_vol_expansion  |  199 |    100 |        0.0985  |         0.18186 |        0.25211 |
| after_OI_fall_zm1p5              | holdout    | future_vol_normalized |  199 |    100 |        0.28638 |         0.61837 |        1.09078 |
| after_hourly_range_expansion_1p5 | train      | future_range_500      | 2020 |    339 |        0.07064 |         0.09494 |        0.11889 |
| after_hourly_range_expansion_1p5 | train      | future_vol_expansion  | 2020 |    339 |        0.13239 |         0.16198 |        0.19195 |
| after_hourly_range_expansion_1p5 | train      | future_vol_normalized | 2020 |    339 |        0.31965 |         0.40319 |        0.49496 |
| after_hourly_range_expansion_1p5 | validation | future_range_500      | 1112 |    178 |        0.09442 |         0.13486 |        0.18096 |
| after_hourly_range_expansion_1p5 | validation | future_vol_expansion  | 1112 |    178 |        0.12919 |         0.17017 |        0.20952 |
| after_hourly_range_expansion_1p5 | validation | future_vol_normalized | 1112 |    178 |        0.32087 |         0.42004 |        0.51842 |
| after_hourly_range_expansion_1p5 | holdout    | future_range_500      |  747 |    117 |        0.05562 |         0.11347 |        0.17268 |
| after_hourly_range_expansion_1p5 | holdout    | future_vol_expansion  |  747 |    117 |        0.13526 |         0.18591 |        0.23126 |
| after_hourly_range_expansion_1p5 | holdout    | future_vol_normalized |  747 |    117 |        0.26549 |         0.47439 |        0.72934 |
| after_big_down_hour              | train      | future_range_500      | 1060 |    312 |        0.06328 |         0.09506 |        0.12165 |
| after_big_down_hour              | train      | future_vol_expansion  | 1060 |    312 |        0.14501 |         0.18299 |        0.22038 |
| after_big_down_hour              | train      | future_vol_normalized | 1060 |    312 |        0.32496 |         0.4369  |        0.5506  |
| after_big_down_hour              | validation | future_range_500      |  570 |    162 |        0.08898 |         0.13801 |        0.18883 |
| after_big_down_hour              | validation | future_vol_expansion  |  570 |    162 |        0.12573 |         0.17665 |        0.21765 |
| after_big_down_hour              | validation | future_vol_normalized |  570 |    162 |        0.28352 |         0.40001 |        0.51986 |
| after_big_down_hour              | holdout    | future_range_500      |  356 |    107 |        0.03477 |         0.10398 |        0.17353 |
| after_big_down_hour              | holdout    | future_vol_expansion  |  356 |    107 |        0.1051  |         0.17305 |        0.23425 |
| after_big_down_hour              | holdout    | future_vol_normalized |  356 |    107 |        0.19798 |         0.36397 |        0.55004 |
| after_range_expansion_and_volume | train      | future_range_500      | 1222 |    318 |        0.05423 |         0.08055 |        0.10588 |
| after_range_expansion_and_volume | train      | future_vol_expansion  | 1222 |    318 |        0.1342  |         0.17215 |        0.20708 |
| after_range_expansion_and_volume | train      | future_vol_normalized | 1222 |    318 |        0.33209 |         0.42258 |        0.52259 |
| after_range_expansion_and_volume | validation | future_range_500      |  703 |    168 |        0.05751 |         0.10549 |        0.15031 |
| after_range_expansion_and_volume | validation | future_vol_expansion  |  703 |    168 |        0.11255 |         0.16413 |        0.20912 |
| after_range_expansion_and_volume | validation | future_vol_normalized |  703 |    168 |        0.27488 |         0.3967  |        0.51268 |
| after_range_expansion_and_volume | holdout    | future_range_500      |  481 |    110 |        0.04102 |         0.09823 |        0.15577 |
| after_range_expansion_and_volume | holdout    | future_vol_expansion  |  481 |    110 |        0.14236 |         0.19498 |        0.23979 |
| after_range_expansion_and_volume | holdout    | future_vol_normalized |  481 |    110 |        0.30774 |         0.54686 |        0.90088 |

## Execution realism
Optional directional follow/fade simulation uses next hourly OPEN, next 60 individual minutes with stop-first ambiguous fills, taker fee each side 0.05% plus 18% GST, and 5 BTC-point adverse slippage per side.
One trade per NY day per rule, restricted to days with condition; +300/-250, +500/-350, +800/-500, one-hour timeout.
Directional simulated results are separate from non-directional range findings. Do not conflate forecastable volatility with forecastable direction.
| rule                             | mode   |   target |   stop | period     |   trades |   mean_net |   win_pct |
|:---------------------------------|:-------|---------:|-------:|:-----------|---------:|-----------:|----------:|
| after_OI_fall_and_range_expand   | fade   |      300 |    250 | holdout    |       87 |    -102.85 |     39.08 |
| after_OI_fall_and_range_expand   | fade   |      300 |    250 | train      |      235 |    -102.32 |     45.53 |
| after_OI_fall_and_range_expand   | fade   |      300 |    250 | validation |      130 |    -103.23 |     37.69 |
| after_OI_fall_and_range_expand   | fade   |      500 |    350 | holdout    |       87 |     -99.62 |     41.38 |
| after_OI_fall_and_range_expand   | fade   |      500 |    350 | train      |      235 |    -107.53 |     39.15 |
| after_OI_fall_and_range_expand   | fade   |      500 |    350 | validation |      130 |    -139.86 |     31.54 |
| after_OI_fall_and_range_expand   | fade   |      800 |    500 | holdout    |       87 |     -86.67 |     43.68 |
| after_OI_fall_and_range_expand   | fade   |      800 |    500 | train      |      235 |    -102.03 |     39.15 |
| after_OI_fall_and_range_expand   | fade   |      800 |    500 | validation |      130 |    -155.97 |     31.54 |
| after_OI_fall_and_range_expand   | follow |      300 |    250 | holdout    |       87 |     -60.01 |     47.13 |
| after_OI_fall_and_range_expand   | follow |      300 |    250 | train      |      235 |    -122.39 |     42.13 |
| after_OI_fall_and_range_expand   | follow |      300 |    250 | validation |      130 |     -76.64 |     40    |
| after_OI_fall_and_range_expand   | follow |      500 |    350 | holdout    |       87 |     -82.57 |     36.78 |
| after_OI_fall_and_range_expand   | follow |      500 |    350 | train      |      235 |    -112.41 |     39.15 |
| after_OI_fall_and_range_expand   | follow |      500 |    350 | validation |      130 |     -27.3  |     40.77 |
| after_OI_fall_and_range_expand   | follow |      800 |    500 | holdout    |       87 |     -78.77 |     35.63 |
| after_OI_fall_and_range_expand   | follow |      800 |    500 | train      |      235 |    -136.13 |     35.32 |
| after_OI_fall_and_range_expand   | follow |      800 |    500 | validation |      130 |     -41.48 |     37.69 |
| after_OI_fall_zm1p5              | fade   |      300 |    250 | holdout    |      100 |     -83.77 |     41    |
| after_OI_fall_zm1p5              | fade   |      300 |    250 | train      |      272 |    -105.37 |     44.85 |
| after_OI_fall_zm1p5              | fade   |      300 |    250 | validation |      146 |     -89.05 |     38.36 |
| after_OI_fall_zm1p5              | fade   |      500 |    350 | holdout    |      100 |     -92.07 |     41    |
| after_OI_fall_zm1p5              | fade   |      500 |    350 | train      |      272 |    -114.62 |     38.24 |
| after_OI_fall_zm1p5              | fade   |      500 |    350 | validation |      146 |    -102.38 |     35.62 |
| after_OI_fall_zm1p5              | fade   |      800 |    500 | holdout    |      100 |     -89.97 |     42    |
| after_OI_fall_zm1p5              | fade   |      800 |    500 | train      |      272 |    -106.36 |     39.34 |
| after_OI_fall_zm1p5              | fade   |      800 |    500 | validation |      146 |     -99.58 |     36.3  |
| after_OI_fall_zm1p5              | follow |      300 |    250 | holdout    |      100 |     -64.05 |     44    |
| after_OI_fall_zm1p5              | follow |      300 |    250 | train      |      272 |    -115.5  |     42.65 |
| after_OI_fall_zm1p5              | follow |      300 |    250 | validation |      146 |     -87.04 |     36.99 |
| after_OI_fall_zm1p5              | follow |      500 |    350 | holdout    |      100 |     -82.92 |     35    |
| after_OI_fall_zm1p5              | follow |      500 |    350 | train      |      272 |    -111.01 |     38.97 |
| after_OI_fall_zm1p5              | follow |      500 |    350 | validation |      146 |     -59.1  |     36.3  |
| after_OI_fall_zm1p5              | follow |      800 |    500 | holdout    |      100 |     -83.11 |     32    |
| after_OI_fall_zm1p5              | follow |      800 |    500 | train      |      272 |    -126.97 |     34.93 |
| after_OI_fall_zm1p5              | follow |      800 |    500 | validation |      146 |     -73.12 |     33.56 |
| after_OI_rise_and_range_expand   | fade   |      300 |    250 | holdout    |       36 |     -86.06 |     41.67 |
| after_OI_rise_and_range_expand   | fade   |      300 |    250 | train      |       99 |     -73.1  |     50.51 |
| after_OI_rise_and_range_expand   | fade   |      300 |    250 | validation |       48 |     -86.2  |     37.5  |
| after_OI_rise_and_range_expand   | fade   |      500 |    350 | holdout    |       36 |     -71.74 |     36.11 |
| after_OI_rise_and_range_expand   | fade   |      500 |    350 | train      |       99 |    -103.4  |     41.41 |
| after_OI_rise_and_range_expand   | fade   |      500 |    350 | validation |       48 |     -98.23 |     33.33 |
| after_OI_rise_and_range_expand   | fade   |      800 |    500 | holdout    |       36 |     -93.64 |     33.33 |
| after_OI_rise_and_range_expand   | fade   |      800 |    500 | train      |       99 |    -122.23 |     40.4  |
| after_OI_rise_and_range_expand   | fade   |      800 |    500 | validation |       48 |     -90.91 |     35.42 |
| after_OI_rise_and_range_expand   | follow |      300 |    250 | holdout    |       36 |     -90    |     41.67 |
| after_OI_rise_and_range_expand   | follow |      300 |    250 | train      |       99 |    -123.55 |     42.42 |
| after_OI_rise_and_range_expand   | follow |      300 |    250 | validation |       48 |    -120.3  |     33.33 |
| after_OI_rise_and_range_expand   | follow |      500 |    350 | holdout    |       36 |    -113.09 |     36.11 |
| after_OI_rise_and_range_expand   | follow |      500 |    350 | train      |       99 |    -141.68 |     35.35 |
| after_OI_rise_and_range_expand   | follow |      500 |    350 | validation |       48 |    -108.64 |     31.25 |
| after_OI_rise_and_range_expand   | follow |      800 |    500 | holdout    |       36 |    -113.39 |     38.89 |
| after_OI_rise_and_range_expand   | follow |      800 |    500 | train      |       99 |     -72.3  |     41.41 |
| after_OI_rise_and_range_expand   | follow |      800 |    500 | validation |       48 |     -56.41 |     33.33 |
| after_big_down_hour              | fade   |      300 |    250 | holdout    |      107 |    -100.51 |     40.19 |
| after_big_down_hour              | fade   |      300 |    250 | train      |      312 |     -95.16 |     46.15 |
| after_big_down_hour              | fade   |      300 |    250 | validation |      162 |     -95.12 |     36.42 |
| after_big_down_hour              | fade   |      500 |    350 | holdout    |      107 |     -81.09 |     42.99 |
| after_big_down_hour              | fade   |      500 |    350 | train      |      312 |     -84.61 |     43.91 |
| after_big_down_hour              | fade   |      500 |    350 | validation |      162 |    -119.33 |     32.1  |
| after_big_down_hour              | fade   |      800 |    500 | holdout    |      107 |     -80.57 |     43.93 |
| after_big_down_hour              | fade   |      800 |    500 | train      |      312 |     -82.21 |     43.59 |
| after_big_down_hour              | fade   |      800 |    500 | validation |      162 |     -72.45 |     39.51 |
| after_big_down_hour              | follow |      300 |    250 | holdout    |      107 |     -84.64 |     36.45 |
| after_big_down_hour              | follow |      300 |    250 | train      |      312 |    -117.87 |     42.31 |
| after_big_down_hour              | follow |      300 |    250 | validation |      162 |     -65.81 |     42.59 |
| after_big_down_hour              | follow |      500 |    350 | holdout    |      107 |     -97.98 |     30.84 |
| after_big_down_hour              | follow |      500 |    350 | train      |      312 |    -133.64 |     35.9  |
| after_big_down_hour              | follow |      500 |    350 | validation |      162 |     -81.99 |     33.95 |
| after_big_down_hour              | follow |      800 |    500 | holdout    |      107 |     -91.65 |     28.04 |
| after_big_down_hour              | follow |      800 |    500 | train      |      312 |    -145.89 |     33.33 |
| after_big_down_hour              | follow |      800 |    500 | validation |      162 |     -76.21 |     33.33 |
| after_hourly_range_expansion_1p5 | fade   |      300 |    250 | holdout    |      116 |     -89.95 |     42.24 |
| after_hourly_range_expansion_1p5 | fade   |      300 |    250 | train      |      339 |     -92.07 |     46.02 |
| after_hourly_range_expansion_1p5 | fade   |      300 |    250 | validation |      178 |    -118.78 |     30.9  |
| after_hourly_range_expansion_1p5 | fade   |      500 |    350 | holdout    |      116 |     -93.22 |     40.52 |
| after_hourly_range_expansion_1p5 | fade   |      500 |    350 | train      |      339 |     -93.99 |     41.3  |
| after_hourly_range_expansion_1p5 | fade   |      500 |    350 | validation |      178 |    -147.24 |     28.09 |
| after_hourly_range_expansion_1p5 | fade   |      800 |    500 | holdout    |      116 |    -116.18 |     37.93 |
| after_hourly_range_expansion_1p5 | fade   |      800 |    500 | train      |      339 |    -100.98 |     40.12 |
| after_hourly_range_expansion_1p5 | fade   |      800 |    500 | validation |      178 |    -136.27 |     32.02 |
| after_hourly_range_expansion_1p5 | follow |      300 |    250 | holdout    |      116 |     -76.55 |     38.79 |
| after_hourly_range_expansion_1p5 | follow |      300 |    250 | train      |      339 |    -121.28 |     40.71 |
| after_hourly_range_expansion_1p5 | follow |      300 |    250 | validation |      178 |     -39.07 |     44.38 |
| after_hourly_range_expansion_1p5 | follow |      500 |    350 | holdout    |      116 |     -75.56 |     37.07 |
| after_hourly_range_expansion_1p5 | follow |      500 |    350 | train      |      339 |    -124.81 |     35.99 |
| after_hourly_range_expansion_1p5 | follow |      500 |    350 | validation |      178 |     -21.36 |     39.89 |
| after_hourly_range_expansion_1p5 | follow |      800 |    500 | holdout    |      116 |     -73.88 |     34.48 |
| after_hourly_range_expansion_1p5 | follow |      800 |    500 | train      |      339 |    -154.03 |     33.04 |
| after_hourly_range_expansion_1p5 | follow |      800 |    500 | validation |      178 |     -23.07 |     36.52 |
| after_hourly_range_expansion_2x  | fade   |      300 |    250 | holdout    |      110 |     -99    |     40    |
| after_hourly_range_expansion_2x  | fade   |      300 |    250 | train      |      298 |    -122.03 |     41.95 |
| after_hourly_range_expansion_2x  | fade   |      300 |    250 | validation |      162 |     -98.74 |     38.27 |
| after_hourly_range_expansion_2x  | fade   |      500 |    350 | holdout    |      110 |     -89.62 |     40.91 |
| after_hourly_range_expansion_2x  | fade   |      500 |    350 | train      |      298 |    -117.65 |     39.6  |
| after_hourly_range_expansion_2x  | fade   |      500 |    350 | validation |      162 |    -126.59 |     35.19 |
| after_hourly_range_expansion_2x  | fade   |      800 |    500 | holdout    |      110 |    -112.78 |     40.91 |
| after_hourly_range_expansion_2x  | fade   |      800 |    500 | train      |      298 |    -151.52 |     37.25 |
| after_hourly_range_expansion_2x  | fade   |      800 |    500 | validation |      162 |    -101.77 |     38.27 |
| after_hourly_range_expansion_2x  | follow |      300 |    250 | holdout    |      110 |     -73.39 |     41.82 |
| after_hourly_range_expansion_2x  | follow |      300 |    250 | train      |      298 |     -92.05 |     47.32 |
| after_hourly_range_expansion_2x  | follow |      300 |    250 | validation |      162 |     -61.05 |     43.21 |
| after_hourly_range_expansion_2x  | follow |      500 |    350 | holdout    |      110 |     -61.4  |     39.09 |
| after_hourly_range_expansion_2x  | follow |      500 |    350 | train      |      298 |     -89.12 |     41.61 |
| after_hourly_range_expansion_2x  | follow |      500 |    350 | validation |      162 |     -61.93 |     37.65 |
| after_hourly_range_expansion_2x  | follow |      800 |    500 | holdout    |      110 |     -87.28 |     35.45 |
| after_hourly_range_expansion_2x  | follow |      800 |    500 | train      |      298 |    -122.51 |     36.58 |
| after_hourly_range_expansion_2x  | follow |      800 |    500 | validation |      162 |     -49.87 |     37.04 |
| after_price_down_and_OI_fall     | fade   |      300 |    250 | holdout    |       77 |     -86.04 |     37.66 |
| after_price_down_and_OI_fall     | fade   |      300 |    250 | train      |      195 |    -105.12 |     46.15 |
| after_price_down_and_OI_fall     | fade   |      300 |    250 | validation |      114 |    -101.17 |     35.96 |
| after_price_down_and_OI_fall     | fade   |      500 |    350 | holdout    |       77 |     -90.39 |     38.96 |
| after_price_down_and_OI_fall     | fade   |      500 |    350 | train      |      195 |     -76.99 |     45.13 |
| after_price_down_and_OI_fall     | fade   |      500 |    350 | validation |      114 |    -104.06 |     35.09 |
| after_price_down_and_OI_fall     | fade   |      800 |    500 | holdout    |       77 |     -74.77 |     41.56 |
| after_price_down_and_OI_fall     | fade   |      800 |    500 | train      |      195 |     -57.88 |     46.67 |
| after_price_down_and_OI_fall     | fade   |      800 |    500 | validation |      114 |     -66.75 |     39.47 |
| after_price_down_and_OI_fall     | follow |      300 |    250 | holdout    |       77 |     -73.31 |     36.36 |
| after_price_down_and_OI_fall     | follow |      300 |    250 | train      |      195 |    -121.08 |     42.56 |
| after_price_down_and_OI_fall     | follow |      300 |    250 | validation |      114 |     -68.56 |     40.35 |
| after_price_down_and_OI_fall     | follow |      500 |    350 | holdout    |       77 |    -105.29 |     25.97 |
| after_price_down_and_OI_fall     | follow |      500 |    350 | train      |      195 |    -145.73 |     35.9  |
| after_price_down_and_OI_fall     | follow |      500 |    350 | validation |      114 |     -74.87 |     33.33 |
| after_price_down_and_OI_fall     | follow |      800 |    500 | holdout    |       77 |     -90.44 |     24.68 |
| after_price_down_and_OI_fall     | follow |      800 |    500 | train      |      195 |    -181.45 |     30.77 |
| after_price_down_and_OI_fall     | follow |      800 |    500 | validation |      114 |     -83.49 |     31.58 |
| after_range_expansion_and_volume | fade   |      300 |    250 | holdout    |      110 |     -88.4  |     42.73 |
| after_range_expansion_and_volume | fade   |      300 |    250 | train      |      318 |    -107.83 |     44.34 |
| after_range_expansion_and_volume | fade   |      300 |    250 | validation |      168 |    -128.03 |     30.36 |
| after_range_expansion_and_volume | fade   |      500 |    350 | holdout    |      110 |     -82.85 |     42.73 |
| after_range_expansion_and_volume | fade   |      500 |    350 | train      |      318 |    -117.63 |     40.25 |
| after_range_expansion_and_volume | fade   |      500 |    350 | validation |      168 |    -151.36 |     27.98 |
| after_range_expansion_and_volume | fade   |      800 |    500 | holdout    |      110 |    -104.61 |     41.82 |
| after_range_expansion_and_volume | fade   |      800 |    500 | train      |      318 |    -111.32 |     41.19 |
| after_range_expansion_and_volume | fade   |      800 |    500 | validation |      168 |    -141.67 |     31.55 |
| after_range_expansion_and_volume | follow |      300 |    250 | holdout    |      110 |     -85.06 |     37.27 |
| after_range_expansion_and_volume | follow |      300 |    250 | train      |      318 |    -111.2  |     43.4  |
| after_range_expansion_and_volume | follow |      300 |    250 | validation |      168 |     -45.07 |     44.64 |
| after_range_expansion_and_volume | follow |      500 |    350 | holdout    |      110 |     -81.91 |     35.45 |
| after_range_expansion_and_volume | follow |      500 |    350 | train      |      318 |     -98.25 |     40.25 |
| after_range_expansion_and_volume | follow |      500 |    350 | validation |      168 |     -16.91 |     42.26 |
| after_range_expansion_and_volume | follow |      800 |    500 | holdout    |      110 |     -65.01 |     33.64 |
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
