# BTC Futures 1m execution, 5m/15m/1h structure — extended discovery

**Outcome cannot be promised:** A predictable 200–500 BTC-point profit every day may not exist; zero-trade days are permitted.

## Research design
- Genuine Delta India BTCUSD perpetual 1-minute OHLCV, without inventing fills or candles.
- Only completed 5m/15m/1h candles are used. Signals on 5m close, orders at next 1m open.
- Train: Jan–Dec 2025; intermediate validation: Jan–Jun 2026; final untouched holdout: Jul–Oct 17 2026.
- Up to one event per strategy per New York day, not one event across strategies. Portfolio correlation is NOT modeled.
- 15 candidate directions/entry conditions and 9 objective exits, including bigger targets of 800–2000 price points, ATR stops, trailing stops and up to 12h holds.
- Stop wins same-minute target/stop ambiguity. Trailing stop decisions apply only after a completed 1m bar.
- Simulated taker fee 0.05% per side with 18% GST on fee, and adverse 5-point slippage per side; no funding, bid/ask or liquidation information.
- All profits are BTC price points per 1 BTC exposure, NOT account USD profit. At 0.001 BTC, a 200-point BTC move produces $0.20 gross, not $200.

## Data quality
{
  "files": 23,
  "one_minute_candles": 987840,
  "five_minute_candles": 197568,
  "fifteen_minute_candles": 65856,
  "hourly_candles": 16464,
  "first_utc": "2025-01-01 00:00:00+00:00",
  "last_utc": "2026-11-17 23:59:00+00:00",
  "zero_volume": 1887,
  "entry_events": 4271,
  "trade_simulations": 38439,
  "entries_by_setup": {
    "h1_trend_15m_reclaim": 169,
    "impulse_fade_open": 470,
    "impulse_trend_strict": 287,
    "opening_break_strict": 178,
    "opening_break_weak": 225,
    "session_vwap_reclaim": 169,
    "session_vwap_weak": 330,
    "sweep_24bar_countertrend": 262,
    "sweep_24bar_opening": 274,
    "sweep_24bar_trend": 215,
    "trend_12bar_break_strict": 249,
    "trend_12bar_break_weak": 352,
    "trend_24bar_break": 302,
    "trend_pullback_ema20": 339,
    "trend_pullback_weak": 450
  },
  "train_validation_positive_candidates": 0,
  "eligible_entry_exit_combinations": 135,
  "selection_note": "Ranking uses train and validation only; holdout not used for selection"
}

## Ranked entry/exit pairs (selection independent of final holdout)
Ranking by WORSE of train and validation average net profit; rank deliberately excludes holdout.
| setup                    | exit_policy          |   n_train |   n_validation |   n_holdout |   mean_net_train |   mean_net_validation |   mean_net_holdout |   robust_score |
|:-------------------------|:---------------------|----------:|---------------:|------------:|-----------------:|----------------------:|-------------------:|---------------:|
| opening_break_weak       | time4h_stop500       |       125 |             61 |          39 |            54.56 |                -34.8  |              14.63 |         -34.8  |
| impulse_fade_open        | fixed800_400_4h      |       250 |            125 |          95 |           -52.9  |                -58.22 |             -15.17 |         -58.22 |
| session_vwap_weak        | time8h_stop700       |       178 |             87 |          65 |           -58.68 |                -13.03 |            -222.4  |         -58.68 |
| opening_break_weak       | atr_3r_8h            |       125 |             61 |          39 |           -81.63 |                 88.41 |             -52.82 |         -81.63 |
| impulse_fade_open        | trail500_after500_8h |       250 |            125 |          95 |           -83.53 |                -41.77 |              23.2  |         -83.53 |
| opening_break_strict     | atr_3r_8h            |        99 |             48 |          31 |           -86.37 |                 73.9  |              29.88 |         -86.37 |
| trend_pullback_weak      | atr_2r_8h            |       235 |            122 |          93 |           -86.55 |                -79.74 |            -137.23 |         -86.55 |
| trend_24bar_break        | time4h_stop500       |       163 |             83 |          56 |           -47.85 |                -87.76 |             -58.69 |         -87.76 |
| trend_12bar_break_strict | atr_3r_8h            |       137 |             69 |          43 |           -89.58 |                -76.82 |             -43.65 |         -89.58 |
| session_vwap_weak        | time4h_stop500       |       178 |             87 |          65 |           -90.75 |                -22.07 |            -127.02 |         -90.75 |

## All train/validation supported setups
| setup                    | exit_policy          |   n_train |   n_validation |   n_holdout |   mean_net_train |   mean_net_validation |   mean_net_holdout |
|:-------------------------|:---------------------|----------:|---------------:|------------:|-----------------:|----------------------:|-------------------:|
| opening_break_weak       | time4h_stop500       |       125 |             61 |          39 |            54.56 |                -34.8  |              14.63 |
| impulse_fade_open        | fixed800_400_4h      |       250 |            125 |          95 |           -52.9  |                -58.22 |             -15.17 |
| session_vwap_weak        | time8h_stop700       |       178 |             87 |          65 |           -58.68 |                -13.03 |            -222.4  |
| opening_break_weak       | atr_3r_8h            |       125 |             61 |          39 |           -81.63 |                 88.41 |             -52.82 |
| impulse_fade_open        | trail500_after500_8h |       250 |            125 |          95 |           -83.53 |                -41.77 |              23.2  |
| opening_break_strict     | atr_3r_8h            |        99 |             48 |          31 |           -86.37 |                 73.9  |              29.88 |
| trend_pullback_weak      | atr_2r_8h            |       235 |            122 |          93 |           -86.55 |                -79.74 |            -137.23 |
| trend_24bar_break        | time4h_stop500       |       163 |             83 |          56 |           -47.85 |                -87.76 |             -58.69 |
| trend_12bar_break_strict | atr_3r_8h            |       137 |             69 |          43 |           -89.58 |                -76.82 |             -43.65 |
| session_vwap_weak        | time4h_stop500       |       178 |             87 |          65 |           -90.75 |                -22.07 |            -127.02 |
| sweep_24bar_trend        | time4h_stop500       |       119 |             57 |          39 |           -74.8  |                -92.88 |            -176.38 |
| trend_pullback_weak      | atr_3r_8h            |       235 |            122 |          93 |           -93.86 |                -82.81 |            -158.28 |
| impulse_fade_open        | fixed1200_500_8h     |       250 |            125 |          95 |          -100.39 |                 -7.87 |              21.03 |
| trend_12bar_break_weak   | time4h_stop500       |       192 |             95 |          65 |          -101.67 |                -65.18 |             -49.46 |
| trend_pullback_weak      | fixed1200_500_8h     |       235 |            122 |          93 |          -103.17 |                -82.71 |            -134.97 |
| opening_break_weak       | time8h_stop700       |       125 |             61 |          39 |           115.92 |               -104.19 |             139.23 |
| sweep_24bar_countertrend | trail500_after500_8h |       138 |             72 |          52 |          -106.58 |                -85.22 |            -126.52 |
| sweep_24bar_opening      | trail500_after500_8h |       147 |             75 |          52 |           -74.92 |               -107.55 |             -56.58 |
| session_vwap_weak        | atr_3r_8h            |       178 |             87 |          65 |          -110.99 |                 11.79 |            -205.6  |
| impulse_fade_open        | atr_2r_8h            |       250 |            125 |          95 |          -113.22 |                -73.21 |              62.67 |
| trend_pullback_ema20     | trail500_after500_8h |       179 |             93 |          67 |          -113.28 |               -100.03 |            -147.88 |
| trend_pullback_weak      | time8h_stop700       |       235 |            122 |          93 |          -113.74 |                -83.35 |             -69.02 |
| opening_break_strict     | fixed2000_800_12h    |        99 |             48 |          31 |          -115.85 |                 40.76 |              88.15 |
| sweep_24bar_countertrend | time8h_stop700       |       138 |             72 |          52 |          -110.45 |               -115.85 |              15.92 |
| trend_pullback_weak      | fixed1600_600_8h     |       235 |            122 |          93 |          -115.88 |                -88.13 |            -158.34 |
| trend_pullback_ema20     | time8h_stop700       |       179 |             93 |          67 |          -103.79 |               -118.47 |              11    |
| impulse_fade_open        | fixed2000_800_12h    |       250 |            125 |          95 |          -118.68 |                -64.94 |              73.17 |
| trend_24bar_break        | atr_3r_8h            |       163 |             83 |          56 |          -119.87 |                -27.34 |            -128.12 |
| trend_24bar_break        | atr_2r_8h            |       163 |             83 |          56 |          -122.01 |                -52.62 |             -95.32 |
| trend_12bar_break_strict | fixed2000_800_12h    |       137 |             69 |          43 |          -103.57 |               -122.23 |             -49.87 |
| opening_break_weak       | fixed2000_800_12h    |       125 |             61 |          39 |          -122.41 |                 22.73 |             -21.74 |
| trend_pullback_weak      | fixed800_400_4h      |       235 |            122 |          93 |           -62.86 |               -123.19 |            -157.12 |
| trend_12bar_break_strict | atr_2r_8h            |       137 |             69 |          43 |          -125.28 |                -63.16 |             -54.68 |
| impulse_fade_open        | fixed1600_600_8h     |       250 |            125 |          95 |          -125.32 |                -17.27 |               9.78 |
| trend_pullback_weak      | trail500_after500_8h |       235 |            122 |          93 |          -125.5  |                -79.57 |            -111.52 |
| opening_break_weak       | fixed1200_500_8h     |       125 |             61 |          39 |          -125.87 |                -67.74 |             -32.8  |
| sweep_24bar_trend        | fixed800_400_4h      |       119 |             57 |          39 |          -127.25 |               -120.72 |             -53.62 |
| opening_break_weak       | fixed1600_600_8h     |       125 |             61 |          39 |          -127.48 |                 42.27 |              -5.3  |
| sweep_24bar_countertrend | fixed1600_600_8h     |       138 |             72 |          52 |          -129.19 |                -64.64 |               9.2  |
| session_vwap_weak        | atr_2r_8h            |       178 |             87 |          65 |          -131.29 |                -29.78 |            -208.28 |
| trend_24bar_break        | fixed2000_800_12h    |       163 |             83 |          56 |          -131.76 |                -83.35 |            -120.8  |
| trend_24bar_break        | fixed1600_600_8h     |       163 |             83 |          56 |          -133.94 |                -56.74 |             -94.43 |
| trend_24bar_break        | fixed1200_500_8h     |       163 |             83 |          56 |          -134.7  |               -115.01 |             -93.21 |
| trend_pullback_weak      | time4h_stop500       |       235 |            122 |          93 |          -136.56 |                -83.72 |            -111.14 |
| impulse_trend_strict     | time8h_stop700       |       151 |             81 |          55 |           -38.42 |               -136.6  |             -54.12 |
| trend_24bar_break        | time8h_stop700       |       163 |             83 |          56 |            50.6  |               -137.79 |              -4.44 |
| trend_pullback_ema20     | fixed800_400_4h      |       179 |             93 |          67 |           -92.04 |               -141.3  |            -216.99 |
| sweep_24bar_countertrend | fixed2000_800_12h    |       138 |             72 |          52 |          -141.51 |               -112.73 |               5.67 |
| sweep_24bar_countertrend | atr_2r_8h            |       138 |             72 |          52 |          -142.43 |                -69.69 |             -30.88 |
| impulse_trend_strict     | time4h_stop500       |       151 |             81 |          55 |          -117.81 |               -142.45 |             -93.58 |
| impulse_fade_open        | time4h_stop500       |       250 |            125 |          95 |          -142.93 |                -21    |              78.22 |
| trend_24bar_break        | fixed800_400_4h      |       163 |             83 |          56 |          -143.58 |                -38.3  |             -90.8  |
| session_vwap_weak        | fixed800_400_4h      |       178 |             87 |          65 |          -144.08 |                -72.66 |            -157.99 |
| opening_break_strict     | time4h_stop500       |        99 |             48 |          31 |            20.5  |               -145.68 |             106.33 |
| sweep_24bar_countertrend | fixed800_400_4h      |       138 |             72 |          52 |          -146.11 |               -100.15 |             -67.6  |
| sweep_24bar_opening      | fixed1200_500_8h     |       147 |             75 |          52 |          -110.13 |               -146.78 |             -64.88 |
| trend_24bar_break        | trail500_after500_8h |       163 |             83 |          56 |          -149.74 |                -64.47 |             -59.12 |
| trend_pullback_ema20     | atr_3r_8h            |       179 |             93 |          67 |          -149.78 |               -115.29 |            -116.72 |
| trend_12bar_break_strict | fixed800_400_4h      |       137 |             69 |          43 |          -150.49 |               -140.38 |            -126.14 |
| sweep_24bar_trend        | atr_3r_8h            |       119 |             57 |          39 |          -150.58 |               -111.02 |            -217.71 |
| sweep_24bar_trend        | fixed2000_800_12h    |       119 |             57 |          39 |          -143.15 |               -152.37 |            -221.49 |
| impulse_fade_open        | atr_3r_8h            |       250 |            125 |          95 |          -152.95 |                -54.72 |              53.4  |
| opening_break_strict     | fixed1200_500_8h     |        99 |             48 |          31 |          -153.61 |                -82    |              36.94 |
| opening_break_weak       | atr_2r_8h            |       125 |             61 |          39 |          -153.62 |                 20.02 |             -83.61 |
| trend_pullback_weak      | fixed2000_800_12h    |       235 |            122 |          93 |           -86.07 |               -154.66 |            -166.66 |
| sweep_24bar_trend        | atr_2r_8h            |       119 |             57 |          39 |          -155.47 |                -81.37 |            -166.93 |
| sweep_24bar_countertrend | fixed1200_500_8h     |       138 |             72 |          52 |          -155.56 |                -79.49 |             -97.49 |
| trend_12bar_break_strict | fixed1600_600_8h     |       137 |             69 |          43 |          -155.71 |               -100.27 |             -82.7  |
| trend_pullback_ema20     | fixed1200_500_8h     |       179 |             93 |          67 |          -157.25 |               -104.47 |            -151.03 |
| trend_pullback_ema20     | fixed2000_800_12h    |       179 |             93 |          67 |          -158.34 |               -142.28 |            -105.89 |
| sweep_24bar_opening      | time4h_stop500       |       147 |             75 |          52 |          -119.03 |               -158.63 |             -25.72 |
| trend_12bar_break_weak   | fixed800_400_4h      |       192 |             95 |          65 |          -159.51 |                -41.96 |            -133.12 |
| trend_12bar_break_strict | trail500_after500_8h |       137 |             69 |          43 |          -160.71 |               -154.82 |             -46.36 |
| trend_pullback_ema20     | time4h_stop500       |       179 |             93 |          67 |          -149.03 |               -161.06 |             -94.28 |
| trend_12bar_break_weak   | time8h_stop700       |       192 |             95 |          65 |           -30.21 |               -162.1  |             -34.27 |
| trend_12bar_break_weak   | fixed1200_500_8h     |       192 |             95 |          65 |          -162.69 |                -99.47 |            -122.1  |
| opening_break_strict     | time8h_stop700       |        99 |             48 |          31 |            60.9  |               -162.9  |             253.59 |
| sweep_24bar_opening      | atr_2r_8h            |       147 |             75 |          52 |          -115.66 |               -163.45 |             -33.37 |
| trend_12bar_break_weak   | atr_2r_8h            |       192 |             95 |          65 |          -163.82 |                -39.91 |            -131.79 |
| trend_12bar_break_strict | fixed1200_500_8h     |       137 |             69 |          43 |          -164.55 |               -141.24 |            -104.28 |
| trend_12bar_break_weak   | fixed1600_600_8h     |       192 |             95 |          65 |          -165.77 |                -52.95 |            -124.56 |
| trend_12bar_break_weak   | atr_3r_8h            |       192 |             95 |          65 |          -165.95 |                -22.14 |            -129.93 |
| opening_break_strict     | trail500_after500_8h |        99 |             48 |          31 |          -167.75 |                -61.09 |               0.9  |
| opening_break_weak       | fixed800_400_4h      |       125 |             61 |          39 |          -168.84 |                -53.01 |             -90.53 |
| opening_break_weak       | trail500_after500_8h |       125 |             61 |          39 |          -169.01 |                -22.09 |             -74.01 |
| sweep_24bar_trend        | fixed1600_600_8h     |       119 |             57 |          39 |          -160.81 |               -169.73 |            -261.62 |
| opening_break_strict     | fixed1600_600_8h     |        99 |             48 |          31 |          -171.79 |                 45.29 |              77.97 |
| sweep_24bar_opening      | fixed1600_600_8h     |       147 |             75 |          52 |          -152.04 |               -172.35 |             -57.87 |
| session_vwap_reclaim     | fixed800_400_4h      |        94 |             45 |          30 |          -174.01 |               -160.64 |            -271.62 |
| h1_trend_15m_reclaim     | fixed800_400_4h      |        94 |             45 |          30 |          -174.01 |               -160.64 |            -271.62 |
| sweep_24bar_opening      | fixed800_400_4h      |       147 |             75 |          52 |           -92.69 |               -175.36 |              -9.18 |
| trend_12bar_break_weak   | trail500_after500_8h |       192 |             95 |          65 |          -175.44 |                -82.12 |             -82.49 |
| sweep_24bar_opening      | atr_3r_8h            |       147 |             75 |          52 |          -116.52 |               -175.52 |             -66.74 |
| impulse_trend_strict     | fixed800_400_4h      |       151 |             81 |          55 |          -175.76 |               -110.05 |            -228.61 |
| trend_12bar_break_weak   | fixed2000_800_12h    |       192 |             95 |          65 |          -175.85 |                -74.16 |            -100.87 |
| trend_12bar_break_strict | time4h_stop500       |       137 |             69 |          43 |           -66.18 |               -177.54 |              24.16 |
| impulse_trend_strict     | atr_3r_8h            |       151 |             81 |          55 |          -178.34 |               -121.77 |             -94.58 |
| session_vwap_weak        | trail500_after500_8h |       178 |             87 |          65 |          -180.25 |                -98.38 |            -166.42 |
| session_vwap_reclaim     | time4h_stop500       |        94 |             45 |          30 |          -167.18 |               -181.43 |            -242.01 |
| h1_trend_15m_reclaim     | time4h_stop500       |        94 |             45 |          30 |          -167.18 |               -181.43 |            -242.01 |
| opening_break_strict     | atr_2r_8h            |        99 |             48 |          31 |          -184.19 |                 24.41 |               7.07 |
| impulse_fade_open        | time8h_stop700       |       250 |            125 |          95 |          -185.42 |                -27.83 |             146.99 |
| session_vwap_weak        | fixed2000_800_12h    |       178 |             87 |          65 |          -187.51 |                -52.75 |            -175.6  |
| session_vwap_weak        | fixed1600_600_8h     |       178 |             87 |          65 |          -187.65 |                -33.42 |            -227.21 |
| session_vwap_weak        | fixed1200_500_8h     |       178 |             87 |          65 |          -189.01 |               -110.08 |            -170.13 |
| sweep_24bar_trend        | trail500_after500_8h |       119 |             57 |          39 |          -163.24 |               -189.35 |            -119.35 |
| trend_pullback_ema20     | fixed1600_600_8h     |       179 |             93 |          67 |          -189.59 |               -104.06 |            -158.83 |
| h1_trend_15m_reclaim     | atr_2r_8h            |        94 |             45 |          30 |          -189.6  |               -163.37 |            -277.06 |
| session_vwap_reclaim     | atr_2r_8h            |        94 |             45 |          30 |          -189.6  |               -163.37 |            -277.06 |
| impulse_trend_strict     | fixed1200_500_8h     |       151 |             81 |          55 |          -191.93 |                -80.63 |            -192.91 |
| sweep_24bar_countertrend | atr_3r_8h            |       138 |             72 |          52 |          -195.3  |                -49.36 |             -21.94 |
| sweep_24bar_opening      | fixed2000_800_12h    |       147 |             75 |          52 |          -124.47 |               -195.61 |             -25.29 |
| opening_break_strict     | fixed800_400_4h      |        99 |             48 |          31 |          -198.67 |               -110.05 |             -41.5  |
| impulse_trend_strict     | fixed1600_600_8h     |       151 |             81 |          55 |          -199.53 |                -66.4  |            -156.05 |
| trend_pullback_ema20     | atr_2r_8h            |       179 |             93 |          67 |          -199.76 |               -104.85 |             -96.6  |
| impulse_trend_strict     | trail500_after500_8h |       151 |             81 |          55 |          -203.72 |               -126.02 |            -121.3  |
| sweep_24bar_trend        | fixed1200_500_8h     |       119 |             57 |          39 |          -143.27 |               -209.18 |            -218.01 |
| session_vwap_reclaim     | fixed1600_600_8h     |        94 |             45 |          30 |          -209.19 |               -166.92 |            -341.24 |
| h1_trend_15m_reclaim     | fixed1600_600_8h     |        94 |             45 |          30 |          -209.19 |               -166.92 |            -341.24 |
| trend_12bar_break_strict | time8h_stop700       |       137 |             69 |          43 |            20.25 |               -209.82 |              41.09 |
| sweep_24bar_opening      | time8h_stop700       |       147 |             75 |          52 |          -154.59 |               -211.96 |             -28.09 |
| sweep_24bar_trend        | time8h_stop700       |       119 |             57 |          39 |          -210.18 |               -213.68 |            -276.25 |
| impulse_trend_strict     | fixed2000_800_12h    |       151 |             81 |          55 |          -216.07 |                -86.34 |            -155.23 |
| sweep_24bar_countertrend | time4h_stop500       |       138 |             72 |          52 |          -219.55 |                -71.47 |             -76.89 |
| session_vwap_reclaim     | trail500_after500_8h |        94 |             45 |          30 |          -188.66 |               -228.36 |            -265.82 |
| h1_trend_15m_reclaim     | trail500_after500_8h |        94 |             45 |          30 |          -188.66 |               -228.36 |            -265.82 |
| h1_trend_15m_reclaim     | atr_3r_8h            |        94 |             45 |          30 |          -232.98 |               -126.64 |            -257.1  |
| session_vwap_reclaim     | atr_3r_8h            |        94 |             45 |          30 |          -232.98 |               -126.64 |            -257.1  |
| impulse_trend_strict     | atr_2r_8h            |       151 |             81 |          55 |          -233.03 |                -52.3  |            -127.11 |
| session_vwap_reclaim     | fixed1200_500_8h     |        94 |             45 |          30 |          -192.9  |               -247.77 |            -301.23 |
| h1_trend_15m_reclaim     | fixed1200_500_8h     |        94 |             45 |          30 |          -192.9  |               -247.77 |            -301.23 |
| session_vwap_reclaim     | time8h_stop700       |        94 |             45 |          30 |          -261.91 |               -129.2  |            -370.58 |
| h1_trend_15m_reclaim     | time8h_stop700       |        94 |             45 |          30 |          -261.91 |               -129.2  |            -370.58 |
| h1_trend_15m_reclaim     | fixed2000_800_12h    |        94 |             45 |          30 |          -293.47 |                -47.14 |            -252.24 |
| session_vwap_reclaim     | fixed2000_800_12h    |        94 |             45 |          30 |          -293.47 |                -47.14 |            -252.24 |

## Main interpretation
- A profitable historical train+validation combination is a candidate hypothesis, not evidence that daily income is guaranteed.
- Holdout mean and maximum drawdown must be assessed jointly and with transaction-cost sensitivity and weekly block confidence intervals.
- Repeated testing of many candidates creates selection risk; do not tune a losing holdout to make it win, then call the same dates out-of-sample.
- OHLCV does not prove resting liquidity or actual institutional execution.

See candidate_entries.csv, all_trade_replays.csv, all_summary.csv and ranked_candidates.csv.
