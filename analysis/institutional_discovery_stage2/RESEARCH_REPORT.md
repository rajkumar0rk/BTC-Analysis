# Finding actual BTC futures market behavior: non-directional predictive regimes

## Research question
Before trying BUY/SELL rules, can market-structure, participation, open interest, basis, funding, and time context forecast the NEXT hour's price movement RANGE? A future hourly HIGH-LOW is a volatility observation, not an executable trading profit.

All 1-hour samples are nonoverlapping, and all features use completed current/prior hourly candles. 2025=training; Jan-Jun 2026=validation; July-Oct 2026=chronological recheck (NOT globally untouched after earlier analyses).
The baseline controls for next-hour New York clock hour and weekday/weekend, so trivial clock effects are reduced. Regime signal rates are measured against matched baseline rates within each chronological period.

## Source/quality
~~~json
{
  "futures_1m": 943200,
  "mark_1m": 943200,
  "OI_5m": 188640,
  "funding_1h": 15720,
  "available_hourly_events": 15539,
  "first": "2025-01-08 12:00:00+00:00",
  "last": "2026-10-17 22:00:00+00:00",
  "oi_changes_pct_p01_p50_p99": [
    -17.531,
    0.33,
    16.207
  ],
  "hourly_range_points_p01_p50_p99": [
    84.0,
    433.0,
    2175.0
  ],
  "funding_distinct_values": 755,
  "funding_fraction_exact_point01": 0.6163,
  "total_predeclared_conditions": 34,
  "eligible_metric_tests": 145,
  "candidate_regimes": [
    "after_OI_fall_and_range_expand",
    "after_hourly_range_expansion_2x",
    "after_big_down_hour",
    "after_OI_fall_zm1p5",
    "after_hourly_range_expansion_1p5",
    "after_price_down_and_OI_fall",
    "after_price_up_and_OI_fall",
    "after_OI_rise_and_range_expand"
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
| after_OI_fall_and_range_expand   | normalized_range |       364 |          2.20972 |         1.49741 |        0.71232 |            203 |             0.57337 |         133 |          0.42788 |      0.57337 |
| after_hourly_range_expansion_2x  | normalized_range |      1153 |          2.19984 |         1.49966 |        0.70018 |            593 |             0.55495 |         391 |          0.77344 |      0.55495 |
| after_big_down_hour              | normalized_range |      1074 |          1.99847 |         1.46919 |        0.52928 |            562 |             0.44211 |         335 |          0.38125 |      0.44211 |
| after_OI_fall_zm1p5              | normalized_range |       496 |          1.89543 |         1.4371  |        0.45832 |            273 |             0.38096 |         161 |          0.2883  |      0.38096 |
| after_hourly_range_expansion_1p5 | normalized_range |      2169 |          1.93219 |         1.45656 |        0.47563 |           1099 |             0.37964 |         688 |          0.4877  |      0.37964 |
| after_price_down_and_OI_fall     | normalized_range |       281 |          1.97219 |         1.43924 |        0.53295 |            149 |             0.37449 |          74 |          0.05695 |      0.37449 |
| after_price_up_and_OI_fall       | normalized_range |       215 |          1.79509 |         1.43431 |        0.36078 |            124 |             0.38874 |          87 |          0.48508 |      0.36078 |
| after_OI_rise_and_range_expand   | normalized_range |       138 |          1.8854  |         1.45747 |        0.42794 |             68 |             0.3455  |          46 |          0.74518 |      0.3455  |
| after_OI_fall_and_range_expand   | p_regime_expand  |       364 |          0.6511  |         0.37742 |        0.27368 |            203 |             0.25209 |         133 |          0.22343 |      0.25209 |
| after_hourly_range_expansion_2x  | p_regime_expand  |      1153 |          0.68257 |         0.37944 |        0.30313 |            593 |             0.24675 |         391 |          0.2997  |      0.24675 |
| after_OI_fall_and_range_expand   | p500             |       364 |          0.83242 |         0.63469 |        0.19773 |            203 |             0.2248  |         133 |          0.13818 |      0.19773 |
| after_big_down_hour              | p_regime_expand  |      1074 |          0.59497 |         0.36444 |        0.23053 |            562 |             0.18917 |         335 |          0.18818 |      0.18917 |
| after_price_down_and_OI_fall     | p_regime_expand  |       281 |          0.51601 |         0.34598 |        0.17003 |            149 |             0.20094 |          74 |          0.08482 |      0.17003 |
| after_OI_fall_zm1p5              | p_regime_expand  |       496 |          0.51613 |         0.34432 |        0.17181 |            273 |             0.16388 |         161 |          0.16251 |      0.16388 |
| after_hourly_range_expansion_1p5 | p_regime_expand  |      2169 |          0.56754 |         0.35763 |        0.20991 |           1099 |             0.1636  |         688 |          0.19557 |      0.1636  |
| after_hourly_range_expansion_2x  | p500             |      1153 |          0.80225 |         0.61796 |        0.1843  |            593 |             0.15813 |         391 |          0.12166 |      0.15813 |
| after_price_down_and_OI_fall     | p500             |       281 |          0.75801 |         0.6045  |        0.15351 |            149 |             0.20547 |          74 |          0.10509 |      0.15351 |
| after_OI_fall_zm1p5              | p500             |       496 |          0.74395 |         0.60831 |        0.13564 |            273 |             0.19671 |         161 |          0.109   |      0.13564 |
| after_big_down_hour              | p500             |      1074 |          0.78492 |         0.61736 |        0.16755 |            562 |             0.12806 |         335 |          0.06643 |      0.12806 |
| after_price_up_and_OI_fall       | p_regime_expand  |       215 |          0.51628 |         0.34214 |        0.17414 |            124 |             0.11936 |          87 |          0.22858 |      0.11936 |
| after_price_up_and_OI_fall       | p500             |       215 |          0.72558 |         0.61329 |        0.11229 |            124 |             0.18618 |          87 |          0.11232 |      0.11229 |
| after_hourly_range_expansion_1p5 | p500             |      2169 |          0.76072 |         0.60846 |        0.15226 |           1099 |             0.11068 |         688 |          0.0747  |      0.11068 |
| after_OI_rise_and_range_expand   | p_regime_expand  |       138 |          0.60145 |         0.3692  |        0.23225 |             68 |             0.07264 |          46 |          0.14997 |      0.07264 |
| after_OI_rise_and_range_expand   | p500             |       138 |          0.78986 |         0.63313 |        0.15672 |             68 |             0.06956 |          46 |         -0.00036 |      0.06956 |

## Calendar-day bootstrap confidence intervals (exploratory)
Lower > 0 in multiple periods indicates consistent evidence for a volatility-regime uplift, NOT guaranteed returns. These are NOT multiplicity-adjusted.
| rule                             | period     | metric                |    n |   days |   uplift_lower |   uplift_median |   uplift_upper |
|:---------------------------------|:-----------|:----------------------|-----:|-------:|---------------:|----------------:|---------------:|
| after_OI_fall_and_range_expand   | train      | future_range_500      |  364 |    217 |        0.15191 |         0.19649 |        0.24138 |
| after_OI_fall_and_range_expand   | train      | future_vol_expansion  |  364 |    217 |        0.22134 |         0.27416 |        0.3282  |
| after_OI_fall_and_range_expand   | train      | future_vol_normalized |  364 |    217 |        0.5028  |         0.70047 |        0.94733 |
| after_OI_fall_and_range_expand   | validation | future_range_500      |  203 |    122 |        0.15226 |         0.22395 |        0.29001 |
| after_OI_fall_and_range_expand   | validation | future_vol_expansion  |  203 |    122 |        0.17722 |         0.25245 |        0.32455 |
| after_OI_fall_and_range_expand   | validation | future_vol_normalized |  203 |    122 |        0.36239 |         0.57188 |        0.78291 |
| after_OI_fall_and_range_expand   | holdout    | future_range_500      |  133 |     84 |        0.04399 |         0.14075 |        0.22409 |
| after_OI_fall_and_range_expand   | holdout    | future_vol_expansion  |  133 |     84 |        0.14954 |         0.22529 |        0.29171 |
| after_OI_fall_and_range_expand   | holdout    | future_vol_normalized |  133 |     84 |        0.23637 |         0.42269 |        0.63526 |
| after_hourly_range_expansion_2x  | train      | future_range_500      | 1153 |    286 |        0.14599 |         0.18408 |        0.2179  |
| after_hourly_range_expansion_2x  | train      | future_vol_expansion  | 1153 |    286 |        0.2625  |         0.30203 |        0.33433 |
| after_hourly_range_expansion_2x  | train      | future_vol_normalized | 1153 |    286 |        0.57188 |         0.69685 |        0.81071 |
| after_hourly_range_expansion_2x  | validation | future_range_500      |  593 |    156 |        0.11288 |         0.15642 |        0.20304 |
| after_hourly_range_expansion_2x  | validation | future_vol_expansion  |  593 |    156 |        0.20391 |         0.24558 |        0.28558 |
| after_hourly_range_expansion_2x  | validation | future_vol_normalized |  593 |    156 |        0.42082 |         0.55163 |        0.68289 |
| after_hourly_range_expansion_2x  | holdout    | future_range_500      |  391 |     95 |        0.04592 |         0.12279 |        0.19681 |
| after_hourly_range_expansion_2x  | holdout    | future_vol_expansion  |  391 |     95 |        0.23546 |         0.29934 |        0.35328 |
| after_hourly_range_expansion_2x  | holdout    | future_vol_normalized |  391 |     95 |        0.51323 |         0.76694 |        1.04028 |
| after_big_down_hour              | train      | future_range_500      | 1074 |    306 |        0.12989 |         0.16812 |        0.19729 |
| after_big_down_hour              | train      | future_vol_expansion  | 1074 |    306 |        0.19426 |         0.22812 |        0.26739 |
| after_big_down_hour              | train      | future_vol_normalized | 1074 |    306 |        0.4111  |         0.52149 |        0.64105 |
| after_big_down_hour              | validation | future_range_500      |  562 |    161 |        0.07404 |         0.12773 |        0.17699 |
| after_big_down_hour              | validation | future_vol_expansion  |  562 |    161 |        0.13658 |         0.18672 |        0.23768 |
| after_big_down_hour              | validation | future_vol_normalized |  562 |    161 |        0.30438 |         0.43171 |        0.56973 |
| after_big_down_hour              | holdout    | future_range_500      |  335 |     95 |        0.00774 |         0.06675 |        0.1265  |
| after_big_down_hour              | holdout    | future_vol_expansion  |  335 |     95 |        0.11746 |         0.18832 |        0.2509  |
| after_big_down_hour              | holdout    | future_vol_normalized |  335 |     95 |        0.2183  |         0.3767  |        0.5295  |
| after_OI_fall_zm1p5              | train      | future_range_500      |  496 |    271 |        0.09548 |         0.13553 |        0.17604 |
| after_OI_fall_zm1p5              | train      | future_vol_expansion  |  496 |    271 |        0.12472 |         0.17212 |        0.22042 |
| after_OI_fall_zm1p5              | train      | future_vol_normalized |  496 |    271 |        0.29187 |         0.45648 |        0.66382 |
| after_OI_fall_zm1p5              | validation | future_range_500      |  273 |    143 |        0.135   |         0.19594 |        0.25666 |
| after_OI_fall_zm1p5              | validation | future_vol_expansion  |  273 |    143 |        0.0983  |         0.16266 |        0.22882 |
| after_OI_fall_zm1p5              | validation | future_vol_normalized |  273 |    143 |        0.19927 |         0.37715 |        0.56433 |
| after_OI_fall_zm1p5              | holdout    | future_range_500      |  161 |     92 |        0.03158 |         0.1101  |        0.18973 |
| after_OI_fall_zm1p5              | holdout    | future_vol_expansion  |  161 |     92 |        0.08974 |         0.16306 |        0.23103 |
| after_OI_fall_zm1p5              | holdout    | future_vol_normalized |  161 |     92 |        0.09538 |         0.28931 |        0.47328 |
| after_hourly_range_expansion_1p5 | train      | future_range_500      | 2169 |    321 |        0.12317 |         0.15222 |        0.1818  |
| after_hourly_range_expansion_1p5 | train      | future_vol_expansion  | 2169 |    321 |        0.17903 |         0.20898 |        0.24111 |
| after_hourly_range_expansion_1p5 | train      | future_vol_normalized | 2169 |    321 |        0.39127 |         0.47169 |        0.55783 |
| after_hourly_range_expansion_1p5 | validation | future_range_500      | 1099 |    175 |        0.06868 |         0.10898 |        0.15282 |
| after_hourly_range_expansion_1p5 | validation | future_vol_expansion  | 1099 |    175 |        0.12635 |         0.16273 |        0.19678 |
| after_hourly_range_expansion_1p5 | validation | future_vol_normalized | 1099 |    175 |        0.27178 |         0.37344 |        0.47054 |
| after_hourly_range_expansion_1p5 | holdout    | future_range_500      |  688 |    103 |        0.01959 |         0.07489 |        0.13838 |
| after_hourly_range_expansion_1p5 | holdout    | future_vol_expansion  |  688 |    103 |        0.14025 |         0.19519 |        0.24102 |
| after_hourly_range_expansion_1p5 | holdout    | future_vol_normalized |  688 |    103 |        0.30585 |         0.48304 |        0.67629 |
| after_price_down_and_OI_fall     | train      | future_range_500      |  281 |    197 |        0.1023  |         0.15291 |        0.20532 |
| after_price_down_and_OI_fall     | train      | future_vol_expansion  |  281 |    197 |        0.10776 |         0.17101 |        0.2293  |
| after_price_down_and_OI_fall     | train      | future_vol_normalized |  281 |    197 |        0.27697 |         0.53113 |        0.85238 |
| after_price_down_and_OI_fall     | validation | future_range_500      |  149 |    103 |        0.12557 |         0.20546 |        0.28435 |
| after_price_down_and_OI_fall     | validation | future_vol_expansion  |  149 |    103 |        0.11557 |         0.19868 |        0.28565 |
| after_price_down_and_OI_fall     | validation | future_vol_normalized |  149 |    103 |        0.15521 |         0.36673 |        0.62372 |
| after_price_down_and_OI_fall     | holdout    | future_range_500      |   74 |     60 |       -0.00709 |         0.10037 |        0.20592 |
| after_price_down_and_OI_fall     | holdout    | future_vol_expansion  |   74 |     60 |       -0.02303 |         0.08425 |        0.17077 |
| after_price_down_and_OI_fall     | holdout    | future_vol_normalized |   74 |     60 |       -0.13629 |         0.05567 |        0.23332 |
| after_price_up_and_OI_fall       | train      | future_range_500      |  215 |    150 |        0.05394 |         0.10755 |        0.16997 |
| after_price_up_and_OI_fall       | train      | future_vol_expansion  |  215 |    150 |        0.10498 |         0.17413 |        0.24031 |
| after_price_up_and_OI_fall       | train      | future_vol_normalized |  215 |    150 |        0.21469 |         0.35884 |        0.51634 |
| after_price_up_and_OI_fall       | validation | future_range_500      |  124 |     86 |        0.09822 |         0.18483 |        0.27456 |
| after_price_up_and_OI_fall       | validation | future_vol_expansion  |  124 |     86 |        0.02925 |         0.11746 |        0.20621 |
| after_price_up_and_OI_fall       | validation | future_vol_normalized |  124 |     86 |        0.14965 |         0.37394 |        0.63017 |
| after_price_up_and_OI_fall       | holdout    | future_range_500      |   87 |     58 |        0.00953 |         0.10702 |        0.21652 |
| after_price_up_and_OI_fall       | holdout    | future_vol_expansion  |   87 |     58 |        0.12255 |         0.22695 |        0.32376 |
| after_price_up_and_OI_fall       | holdout    | future_vol_normalized |   87 |     58 |        0.21184 |         0.47935 |        0.76433 |
| after_OI_rise_and_range_expand   | train      | future_range_500      |  138 |    104 |        0.079   |         0.153   |        0.2259  |
| after_OI_rise_and_range_expand   | train      | future_vol_expansion  |  138 |    104 |        0.14544 |         0.23242 |        0.32156 |
| after_OI_rise_and_range_expand   | train      | future_vol_normalized |  138 |    104 |        0.26695 |         0.42457 |        0.62073 |
| after_OI_rise_and_range_expand   | validation | future_range_500      |   68 |     54 |       -0.05217 |         0.06746 |        0.19969 |
| after_OI_rise_and_range_expand   | validation | future_vol_expansion  |   68 |     54 |       -0.03872 |         0.0747  |        0.18475 |
| after_OI_rise_and_range_expand   | validation | future_vol_normalized |   68 |     54 |        0.06543 |         0.32841 |        0.63837 |
| after_OI_rise_and_range_expand   | holdout    | future_range_500      |   46 |     35 |       -0.14219 |        -0.00472 |        0.12089 |
| after_OI_rise_and_range_expand   | holdout    | future_vol_expansion  |   46 |     35 |       -0.00882 |         0.14986 |        0.28705 |
| after_OI_rise_and_range_expand   | holdout    | future_vol_normalized |   46 |     35 |       -0.17225 |         0.67961 |        1.89793 |

## Execution realism
Optional directional follow/fade simulation uses next hourly OPEN, next 60 individual minutes with stop-first ambiguous fills, taker fee each side 0.05% plus 18% GST, and 5 BTC-point adverse slippage per side.
One trade per NY day per rule, restricted to days with condition; +300/-250, +500/-350, +800/-500, one-hour timeout.
Directional simulated results are separate from non-directional range findings. Do not conflate forecastable volatility with forecastable direction.
| rule                             | mode   |   target |   stop | period     |   trades |   mean_net |   win_pct |
|:---------------------------------|:-------|---------:|-------:|:-----------|---------:|-----------:|----------:|
| after_OI_fall_and_range_expand   | fade   |      300 |    250 | holdout    |       83 |     -95.97 |     37.35 |
| after_OI_fall_and_range_expand   | fade   |      300 |    250 | train      |      217 |    -130.08 |     41.47 |
| after_OI_fall_and_range_expand   | fade   |      300 |    250 | validation |      122 |    -149.92 |     31.97 |
| after_OI_fall_and_range_expand   | fade   |      500 |    350 | holdout    |       83 |     -82.03 |     37.35 |
| after_OI_fall_and_range_expand   | fade   |      500 |    350 | train      |      217 |     -92.13 |     41.47 |
| after_OI_fall_and_range_expand   | fade   |      500 |    350 | validation |      122 |    -158.93 |     29.51 |
| after_OI_fall_and_range_expand   | fade   |      800 |    500 | holdout    |       83 |     -89.53 |     34.94 |
| after_OI_fall_and_range_expand   | fade   |      800 |    500 | train      |      217 |     -82.69 |     41.01 |
| after_OI_fall_and_range_expand   | fade   |      800 |    500 | validation |      122 |    -167.93 |     30.33 |
| after_OI_fall_and_range_expand   | follow |      300 |    250 | holdout    |       83 |     -99.89 |     33.73 |
| after_OI_fall_and_range_expand   | follow |      300 |    250 | train      |      217 |    -151.67 |     38.71 |
| after_OI_fall_and_range_expand   | follow |      300 |    250 | validation |      122 |     -34.68 |     52.46 |
| after_OI_fall_and_range_expand   | follow |      500 |    350 | holdout    |       83 |    -111.71 |     28.92 |
| after_OI_fall_and_range_expand   | follow |      500 |    350 | train      |      217 |    -177.69 |     32.72 |
| after_OI_fall_and_range_expand   | follow |      500 |    350 | validation |      122 |     -30.84 |     45.08 |
| after_OI_fall_and_range_expand   | follow |      800 |    500 | holdout    |       83 |    -118.75 |     27.71 |
| after_OI_fall_and_range_expand   | follow |      800 |    500 | train      |      217 |    -172.95 |     34.56 |
| after_OI_fall_and_range_expand   | follow |      800 |    500 | validation |      122 |     -40.06 |     44.26 |
| after_OI_fall_zm1p5              | fade   |      300 |    250 | holdout    |       91 |     -87.96 |     39.56 |
| after_OI_fall_zm1p5              | fade   |      300 |    250 | train      |      271 |    -139.57 |     38.38 |
| after_OI_fall_zm1p5              | fade   |      300 |    250 | validation |      143 |    -138.21 |     31.47 |
| after_OI_fall_zm1p5              | fade   |      500 |    350 | holdout    |       91 |     -67.1  |     40.66 |
| after_OI_fall_zm1p5              | fade   |      500 |    350 | train      |      271 |    -118.92 |     36.9  |
| after_OI_fall_zm1p5              | fade   |      500 |    350 | validation |      143 |    -134.36 |     30.07 |
| after_OI_fall_zm1p5              | fade   |      800 |    500 | holdout    |       91 |     -66.2  |     38.46 |
| after_OI_fall_zm1p5              | fade   |      800 |    500 | train      |      271 |    -109.75 |     37.27 |
| after_OI_fall_zm1p5              | fade   |      800 |    500 | validation |      143 |    -150.75 |     30.07 |
| after_OI_fall_zm1p5              | follow |      300 |    250 | holdout    |       91 |    -105.36 |     30.77 |
| after_OI_fall_zm1p5              | follow |      300 |    250 | train      |      271 |    -142.68 |     37.27 |
| after_OI_fall_zm1p5              | follow |      300 |    250 | validation |      143 |     -54.9  |     47.55 |
| after_OI_fall_zm1p5              | follow |      500 |    350 | holdout    |       91 |    -124.35 |     25.27 |
| after_OI_fall_zm1p5              | follow |      500 |    350 | train      |      271 |    -152.95 |     31.37 |
| after_OI_fall_zm1p5              | follow |      500 |    350 | validation |      143 |     -46.09 |     42.66 |
| after_OI_fall_zm1p5              | follow |      800 |    500 | holdout    |       91 |    -134.08 |     24.18 |
| after_OI_fall_zm1p5              | follow |      800 |    500 | train      |      271 |    -142.69 |     32.84 |
| after_OI_fall_zm1p5              | follow |      800 |    500 | validation |      143 |     -70.34 |     40.56 |
| after_OI_rise_and_range_expand   | fade   |      300 |    250 | holdout    |       35 |    -129.14 |     31.43 |
| after_OI_rise_and_range_expand   | fade   |      300 |    250 | train      |      104 |    -160.41 |     37.5  |
| after_OI_rise_and_range_expand   | fade   |      300 |    250 | validation |       54 |     -69.87 |     44.44 |
| after_OI_rise_and_range_expand   | fade   |      500 |    350 | holdout    |       35 |    -120.01 |     31.43 |
| after_OI_rise_and_range_expand   | fade   |      500 |    350 | train      |      104 |    -162.9  |     34.62 |
| after_OI_rise_and_range_expand   | fade   |      500 |    350 | validation |       54 |    -100.34 |     33.33 |
| after_OI_rise_and_range_expand   | fade   |      800 |    500 | holdout    |       35 |    -110.29 |     28.57 |
| after_OI_rise_and_range_expand   | fade   |      800 |    500 | train      |      104 |    -173.54 |     38.46 |
| after_OI_rise_and_range_expand   | fade   |      800 |    500 | validation |       54 |     -97.95 |     37.04 |
| after_OI_rise_and_range_expand   | follow |      300 |    250 | holdout    |       35 |     -72.25 |     40    |
| after_OI_rise_and_range_expand   | follow |      300 |    250 | train      |      104 |    -107.52 |     48.08 |
| after_OI_rise_and_range_expand   | follow |      300 |    250 | validation |       54 |    -133.52 |     35.19 |
| after_OI_rise_and_range_expand   | follow |      500 |    350 | holdout    |       35 |    -111.26 |     34.29 |
| after_OI_rise_and_range_expand   | follow |      500 |    350 | train      |      104 |    -100.16 |     41.35 |
| after_OI_rise_and_range_expand   | follow |      500 |    350 | validation |       54 |    -121.32 |     31.48 |
| after_OI_rise_and_range_expand   | follow |      800 |    500 | holdout    |       35 |     -77.9  |     37.14 |
| after_OI_rise_and_range_expand   | follow |      800 |    500 | train      |      104 |     -85.51 |     41.35 |
| after_OI_rise_and_range_expand   | follow |      800 |    500 | validation |       54 |    -124.7  |     27.78 |
| after_big_down_hour              | fade   |      300 |    250 | holdout    |       95 |     -93.87 |     38.95 |
| after_big_down_hour              | fade   |      300 |    250 | train      |      306 |    -102.53 |     47.06 |
| after_big_down_hour              | fade   |      300 |    250 | validation |      161 |    -122.6  |     35.4  |
| after_big_down_hour              | fade   |      500 |    350 | holdout    |       95 |     -85.55 |     38.95 |
| after_big_down_hour              | fade   |      500 |    350 | train      |      306 |     -93.38 |     42.16 |
| after_big_down_hour              | fade   |      500 |    350 | validation |      161 |    -118.94 |     34.78 |
| after_big_down_hour              | fade   |      800 |    500 | holdout    |       95 |     -88.73 |     40    |
| after_big_down_hour              | fade   |      800 |    500 | train      |      306 |     -66.83 |     42.48 |
| after_big_down_hour              | fade   |      800 |    500 | validation |      161 |    -114.28 |     37.89 |
| after_big_down_hour              | follow |      300 |    250 | holdout    |       95 |    -112.88 |     31.58 |
| after_big_down_hour              | follow |      300 |    250 | train      |      306 |    -150.46 |     38.89 |
| after_big_down_hour              | follow |      300 |    250 | validation |      161 |     -87.95 |     40.99 |
| after_big_down_hour              | follow |      500 |    350 | holdout    |       95 |    -121.77 |     27.37 |
| after_big_down_hour              | follow |      500 |    350 | train      |      306 |    -162.36 |     32.35 |
| after_big_down_hour              | follow |      500 |    350 | validation |      161 |     -93.07 |     37.27 |
| after_big_down_hour              | follow |      800 |    500 | holdout    |       95 |    -115.52 |     26.32 |
| after_big_down_hour              | follow |      800 |    500 | train      |      306 |    -165.12 |     32.03 |
| after_big_down_hour              | follow |      800 |    500 | validation |      161 |     -94.93 |     37.27 |
| after_hourly_range_expansion_1p5 | fade   |      300 |    250 | holdout    |      101 |     -51.99 |     43.56 |
| after_hourly_range_expansion_1p5 | fade   |      300 |    250 | train      |      321 |    -134.58 |     39.88 |
| after_hourly_range_expansion_1p5 | fade   |      300 |    250 | validation |      175 |    -127.35 |     31.43 |
| after_hourly_range_expansion_1p5 | fade   |      500 |    350 | holdout    |      101 |     -65.49 |     38.61 |
| after_hourly_range_expansion_1p5 | fade   |      500 |    350 | train      |      321 |    -124.03 |     36.76 |
| after_hourly_range_expansion_1p5 | fade   |      500 |    350 | validation |      175 |    -132.31 |     30.29 |
| after_hourly_range_expansion_1p5 | fade   |      800 |    500 | holdout    |      101 |     -79.63 |     36.63 |
| after_hourly_range_expansion_1p5 | fade   |      800 |    500 | train      |      321 |     -96.9  |     38.94 |
| after_hourly_range_expansion_1p5 | fade   |      800 |    500 | validation |      175 |    -120.52 |     32.57 |
| after_hourly_range_expansion_1p5 | follow |      300 |    250 | holdout    |      101 |    -131.57 |     24.75 |
| after_hourly_range_expansion_1p5 | follow |      300 |    250 | train      |      321 |    -121.11 |     43.93 |
| after_hourly_range_expansion_1p5 | follow |      300 |    250 | validation |      175 |     -63.77 |     42.86 |
| after_hourly_range_expansion_1p5 | follow |      500 |    350 | holdout    |      101 |    -149.96 |     21.78 |
| after_hourly_range_expansion_1p5 | follow |      500 |    350 | train      |      321 |    -137.72 |     37.07 |
| after_hourly_range_expansion_1p5 | follow |      500 |    350 | validation |      175 |     -66.85 |     38.86 |
| after_hourly_range_expansion_1p5 | follow |      800 |    500 | holdout    |      101 |    -136.38 |     22.77 |
| after_hourly_range_expansion_1p5 | follow |      800 |    500 | train      |      321 |    -148.62 |     36.45 |
| after_hourly_range_expansion_1p5 | follow |      800 |    500 | validation |      175 |     -84.32 |     36    |
| after_hourly_range_expansion_2x  | fade   |      300 |    250 | holdout    |       94 |     -96.47 |     40.43 |
| after_hourly_range_expansion_2x  | fade   |      300 |    250 | train      |      286 |    -152.58 |     37.41 |
| after_hourly_range_expansion_2x  | fade   |      300 |    250 | validation |      156 |    -137.89 |     32.05 |
| after_hourly_range_expansion_2x  | fade   |      500 |    350 | holdout    |       94 |    -106.5  |     37.23 |
| after_hourly_range_expansion_2x  | fade   |      500 |    350 | train      |      286 |    -142.51 |     33.92 |
| after_hourly_range_expansion_2x  | fade   |      500 |    350 | validation |      156 |    -152.77 |     30.77 |
| after_hourly_range_expansion_2x  | fade   |      800 |    500 | holdout    |       94 |    -103.37 |     37.23 |
| after_hourly_range_expansion_2x  | fade   |      800 |    500 | train      |      286 |    -126.51 |     33.57 |
| after_hourly_range_expansion_2x  | fade   |      800 |    500 | validation |      156 |    -154.9  |     33.33 |
| after_hourly_range_expansion_2x  | follow |      300 |    250 | holdout    |       94 |     -98.18 |     35.11 |
| after_hourly_range_expansion_2x  | follow |      300 |    250 | train      |      286 |    -131.6  |     42.31 |
| after_hourly_range_expansion_2x  | follow |      300 |    250 | validation |      156 |     -61.76 |     45.51 |
| after_hourly_range_expansion_2x  | follow |      500 |    350 | holdout    |       94 |    -109.24 |     29.79 |
| after_hourly_range_expansion_2x  | follow |      500 |    350 | train      |      286 |    -112.5  |     39.16 |
| after_hourly_range_expansion_2x  | follow |      500 |    350 | validation |      156 |     -53.16 |     41.67 |
| after_hourly_range_expansion_2x  | follow |      800 |    500 | holdout    |       94 |     -88.46 |     31.91 |
| after_hourly_range_expansion_2x  | follow |      800 |    500 | train      |      286 |    -125.34 |     38.46 |
| after_hourly_range_expansion_2x  | follow |      800 |    500 | validation |      156 |     -60.47 |     39.1  |
| after_price_down_and_OI_fall     | fade   |      300 |    250 | holdout    |       60 |     -99.03 |     36.67 |
| after_price_down_and_OI_fall     | fade   |      300 |    250 | train      |      197 |    -125.99 |     41.12 |
| after_price_down_and_OI_fall     | fade   |      300 |    250 | validation |      103 |    -157.11 |     28.16 |
| after_price_down_and_OI_fall     | fade   |      500 |    350 | holdout    |       60 |     -98.64 |     36.67 |
| after_price_down_and_OI_fall     | fade   |      500 |    350 | train      |      197 |    -111.47 |     38.07 |
| after_price_down_and_OI_fall     | fade   |      500 |    350 | validation |      103 |    -158.18 |     28.16 |
| after_price_down_and_OI_fall     | fade   |      800 |    500 | holdout    |       60 |     -80.58 |     38.33 |
| after_price_down_and_OI_fall     | fade   |      800 |    500 | train      |      197 |     -93.3  |     39.09 |
| after_price_down_and_OI_fall     | fade   |      800 |    500 | validation |      103 |    -181.07 |     28.16 |
| after_price_down_and_OI_fall     | follow |      300 |    250 | holdout    |       60 |     -97.49 |     33.33 |
| after_price_down_and_OI_fall     | follow |      300 |    250 | train      |      197 |    -145.57 |     37.06 |
| after_price_down_and_OI_fall     | follow |      300 |    250 | validation |      103 |     -37.01 |     52.43 |
| after_price_down_and_OI_fall     | follow |      500 |    350 | holdout    |       60 |    -111.89 |     26.67 |
| after_price_down_and_OI_fall     | follow |      500 |    350 | train      |      197 |    -162.01 |     29.95 |
| after_price_down_and_OI_fall     | follow |      500 |    350 | validation |      103 |     -14.61 |     48.54 |
| after_price_down_and_OI_fall     | follow |      800 |    500 | holdout    |       60 |     -91.72 |     28.33 |
| after_price_down_and_OI_fall     | follow |      800 |    500 | train      |      197 |    -132.82 |     31.47 |
| after_price_down_and_OI_fall     | follow |      800 |    500 | validation |      103 |     -44.08 |     43.69 |
| after_price_up_and_OI_fall       | fade   |      300 |    250 | holdout    |       58 |    -104.82 |     37.93 |
| after_price_up_and_OI_fall       | fade   |      300 |    250 | train      |      150 |    -159.1  |     34.67 |
| after_price_up_and_OI_fall       | fade   |      300 |    250 | validation |       86 |    -103.74 |     38.37 |
| after_price_up_and_OI_fall       | fade   |      500 |    350 | holdout    |       58 |     -89.77 |     37.93 |
| after_price_up_and_OI_fall       | fade   |      500 |    350 | train      |      150 |    -159.49 |     31.33 |
| after_price_up_and_OI_fall       | fade   |      500 |    350 | validation |       86 |    -108.91 |     33.72 |
| after_price_up_and_OI_fall       | fade   |      800 |    500 | holdout    |       58 |    -117.14 |     32.76 |
| after_price_up_and_OI_fall       | fade   |      800 |    500 | train      |      150 |    -159.81 |     30.67 |
| after_price_up_and_OI_fall       | fade   |      800 |    500 | validation |       86 |    -111.54 |     33.72 |
| after_price_up_and_OI_fall       | follow |      300 |    250 | holdout    |       58 |     -72.64 |     37.93 |
| after_price_up_and_OI_fall       | follow |      300 |    250 | train      |      150 |    -123.89 |     40.67 |
| after_price_up_and_OI_fall       | follow |      300 |    250 | validation |       86 |     -95.07 |     39.53 |
| after_price_up_and_OI_fall       | follow |      500 |    350 | holdout    |       58 |     -74.63 |     36.21 |
| after_price_up_and_OI_fall       | follow |      500 |    350 | train      |      150 |    -104.78 |     39.33 |
| after_price_up_and_OI_fall       | follow |      500 |    350 | validation |       86 |     -86.72 |     33.72 |
| after_price_up_and_OI_fall       | follow |      800 |    500 | holdout    |       58 |    -107.42 |     32.76 |
| after_price_up_and_OI_fall       | follow |      800 |    500 | train      |      150 |     -99.72 |     40.67 |
| after_price_up_and_OI_fall       | follow |      800 |    500 | validation |       86 |     -81.47 |     37.21 |

## Limitations
- OHLCV/OI/funding/mark do not identify trading firms or record historical liquidation and full depth.
- Percentile uncertainty is a within-period calendar-day bootstrap, without multiple-testing correction.
- Prior analyses used some of the same final dates; future live data is the only genuinely fresh test.
- Price-index regime thresholds are normalized to trailing range; fixed $500 threshold is also shown but is regime dependent.
- Fees, funding charges, actual quotes and market impact might further worsen directional P&L.

## Saved research files
all_conditional_findings.csv, ranked_early_periods.csv, day_block_intervals.csv, directional_trade_ledger.csv, directional_trade_results.csv, six_hourly_feature_samples.csv.
