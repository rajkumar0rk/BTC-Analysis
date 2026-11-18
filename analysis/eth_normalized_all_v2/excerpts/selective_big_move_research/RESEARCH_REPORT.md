# BTC Futures 1m execution, 5m/15m/1h structure — extended discovery

**Outcome cannot be promised:** A predictable 200–500 BTC-point profit every day may not exist; zero-trade days are permitted.

## Research design
- Genuine Delta India ETHUSD perpetual 1-minute OHLCV, without inventing fills or candles.
- Only completed 5m/15m/1h candles are used. Signals on 5m close, orders at next 1m open.
- Train: Jan–Dec 2025; intermediate validation: Jan–Jun 2026; final untouched holdout: Jul–Oct 17 2026.
- Up to one event per strategy per New York day, not one event across strategies. Portfolio correlation is NOT modeled.
- 15 candidate directions/entry conditions and 9 objective exits, including bigger targets of 800–2000 price points, ATR stops, trailing stops and up to 12h holds.
- Stop wins same-minute target/stop ambiguity. Trailing stop decisions apply only after a completed 1m bar.
- Simulated taker fee 0.05% per side with 18% GST on fee, and adverse 5-point slippage per side; no funding, bid/ask or liquidation information.
- All profits are BTC price points per 1 BTC exposure, NOT account USD profit. At 0.001 BTC, a 200-point BTC move produces $0.20 gross, not $200.

## Data quality
{
  "files": 22,
  "one_minute_candles": 963360,
  "five_minute_candles": 192672,
  "fifteen_minute_candles": 64224,
  "hourly_candles": 16056,
  "first_utc": "2025-01-01 00:00:00+00:00",
  "last_utc": "2026-10-31 23:59:00+00:00",
  "zero_volume": 1887,
  "entry_events": 4178,
  "trade_simulations": 37602,
  "entries_by_setup": {
    "h1_trend_15m_reclaim": 164,
    "impulse_fade_open": 459,
    "impulse_trend_strict": 280,
    "opening_break_strict": 173,
    "opening_break_weak": 220,
    "session_vwap_reclaim": 164,
    "session_vwap_weak": 323,
    "sweep_24bar_countertrend": 257,
    "sweep_24bar_opening": 271,
    "sweep_24bar_trend": 212,
    "trend_12bar_break_strict": 243,
    "trend_12bar_break_weak": 345,
    "trend_24bar_break": 297,
    "trend_pullback_ema20": 331,
    "trend_pullback_weak": 439
  },
  "train_validation_positive_candidates": 0,
  "eligible_entry_exit_combinations": 135,
  "selection_note": "Ranking uses train and validation only; holdout not used for selection"
}

## Ranked entry/exit pairs (selection independent of final holdout)
Ranking by WORSE of train and validation average net profit; rank deliberately excludes holdout.
| setup                    | exit_policy          |   n_train |   n_validation |   n_holdout |   mean_net_train |   mean_net_validation |   mean_net_holdout |   robust_score |
|:-------------------------|:---------------------|----------:|---------------:|------------:|-----------------:|----------------------:|-------------------:|---------------:|
| opening_break_weak       | time4h_stop500       |       125 |             61 |          34 |            54.56 |                -34.8  |              -2.95 |         -34.8  |
| impulse_fade_open        | fixed800_400_4h      |       250 |            125 |          84 |           -52.9  |                -58.22 |              15.72 |         -58.22 |
| session_vwap_weak        | time8h_stop700       |       178 |             87 |          58 |           -58.68 |                -13.03 |            -201.85 |         -58.68 |
| opening_break_weak       | atr_3r_8h            |       125 |             61 |          34 |           -81.63 |                 88.41 |             -89.31 |         -81.63 |
| impulse_fade_open        | trail500_after500_8h |       250 |            125 |          84 |           -83.53 |                -41.77 |              57.48 |         -83.53 |
| opening_break_strict     | atr_3r_8h            |        99 |             48 |          26 |           -86.37 |                 73.9  |              -1.93 |         -86.37 |
| trend_pullback_weak      | atr_2r_8h            |       235 |            122 |          82 |           -86.55 |                -79.74 |            -151.39 |         -86.55 |
| trend_24bar_break        | time4h_stop500       |       163 |             83 |          51 |           -47.85 |                -87.76 |             -69.94 |         -87.76 |
| trend_12bar_break_strict | atr_3r_8h            |       137 |             69 |          37 |           -89.58 |                -76.82 |             -53.43 |         -89.58 |
| session_vwap_weak        | time4h_stop500       |       178 |             87 |          58 |           -90.75 |                -22.07 |             -97.74 |         -90.75 |

## All train/validation supported setups
| setup                    | exit_policy          |   n_train |   n_validation |   n_holdout |   mean_net_train |   mean_net_validation |   mean_net_holdout |
|:-------------------------|:---------------------|----------:|---------------:|------------:|-----------------:|----------------------:|-------------------:|
| opening_break_weak       | time4h_stop500       |       125 |             61 |          34 |            54.56 |                -34.8  |              -2.95 |
| impulse_fade_open        | fixed800_400_4h      |       250 |            125 |          84 |           -52.9  |                -58.22 |              15.72 |
| session_vwap_weak        | time8h_stop700       |       178 |             87 |          58 |           -58.68 |                -13.03 |            -201.85 |
| opening_break_weak       | atr_3r_8h            |       125 |             61 |          34 |           -81.63 |                 88.41 |             -89.31 |
| impulse_fade_open        | trail500_after500_8h |       250 |            125 |          84 |           -83.53 |                -41.77 |              57.48 |
| opening_break_strict     | atr_3r_8h            |        99 |             48 |          26 |           -86.37 |                 73.9  |              -1.93 |
| trend_pullback_weak      | atr_2r_8h            |       235 |            122 |          82 |           -86.55 |                -79.74 |            -151.39 |
| trend_24bar_break        | time4h_stop500       |       163 |             83 |          51 |           -47.85 |                -87.76 |             -69.94 |
| trend_12bar_break_strict | atr_3r_8h            |       137 |             69 |          37 |           -89.58 |                -76.82 |             -53.43 |
| session_vwap_weak        | time4h_stop500       |       178 |             87 |          58 |           -90.75 |                -22.07 |             -97.74 |
| sweep_24bar_trend        | time4h_stop500       |       119 |             57 |          36 |           -74.8  |                -92.88 |            -161.21 |
| trend_pullback_weak      | atr_3r_8h            |       235 |            122 |          82 |           -93.86 |                -82.81 |            -157.39 |
| impulse_fade_open        | fixed1200_500_8h     |       250 |            125 |          84 |          -100.39 |                 -7.87 |              46.06 |
| trend_12bar_break_weak   | time4h_stop500       |       192 |             95 |          58 |          -101.67 |                -65.18 |             -64.53 |
| trend_pullback_weak      | fixed1200_500_8h     |       235 |            122 |          82 |          -103.17 |                -82.71 |            -151.27 |
| opening_break_weak       | time8h_stop700       |       125 |             61 |          34 |           115.92 |               -104.19 |             119.52 |
| sweep_24bar_countertrend | trail500_after500_8h |       138 |             72 |          47 |          -106.58 |                -85.22 |            -118.56 |
| sweep_24bar_opening      | trail500_after500_8h |       147 |             75 |          49 |           -74.92 |               -107.55 |             -60.49 |
| session_vwap_weak        | atr_3r_8h            |       178 |             87 |          58 |          -110.99 |                 11.79 |            -191.26 |
| impulse_fade_open        | atr_2r_8h            |       250 |            125 |          84 |          -113.22 |                -73.21 |              78.32 |
| trend_pullback_ema20     | trail500_after500_8h |       179 |             93 |          59 |          -113.28 |               -100.03 |            -133.13 |
| trend_pullback_weak      | time8h_stop700       |       235 |            122 |          82 |          -113.74 |                -83.35 |             -50.19 |
| opening_break_strict     | fixed2000_800_12h    |        99 |             48 |          26 |          -115.85 |                 40.76 |              70.6  |
| sweep_24bar_countertrend | time8h_stop700       |       138 |             72 |          47 |          -110.45 |               -115.85 |              22.63 |
| trend_pullback_weak      | fixed1600_600_8h     |       235 |            122 |          82 |          -115.88 |                -88.13 |            -163.61 |
| trend_pullback_ema20     | time8h_stop700       |       179 |             93 |          59 |          -103.79 |               -118.47 |              74.31 |
| impulse_fade_open        | fixed2000_800_12h    |       250 |            125 |          84 |          -118.68 |                -64.94 |              79.52 |
| trend_24bar_break        | atr_3r_8h            |       163 |             83 |          51 |          -119.87 |                -27.34 |            -147.37 |
| trend_24bar_break        | atr_2r_8h            |       163 |             83 |          51 |          -122.01 |                -52.62 |             -96.18 |
| trend_12bar_break_strict | fixed2000_800_12h    |       137 |             69 |          37 |          -103.57 |               -122.23 |             -58.51 |
| opening_break_weak       | fixed2000_800_12h    |       125 |             61 |          34 |          -122.41 |                 22.73 |             -51.31 |
| trend_pullback_weak      | fixed800_400_4h      |       235 |            122 |          82 |           -62.86 |               -123.19 |            -164.54 |
| trend_12bar_break_strict | atr_2r_8h            |       137 |             69 |          37 |          -125.28 |                -63.16 |             -45.33 |
| impulse_fade_open        | fixed1600_600_8h     |       250 |            125 |          84 |          -125.32 |                -17.27 |              25.16 |
| trend_pullback_weak      | trail500_after500_8h |       235 |            122 |          82 |          -125.5  |                -79.57 |            -116.05 |
| opening_break_weak       | fixed1200_500_8h     |       125 |             61 |          34 |          -125.87 |                -67.74 |             -50.96 |
| sweep_24bar_trend        | fixed800_400_4h      |       119 |             57 |          36 |          -127.25 |               -120.72 |             -30.99 |
| opening_break_weak       | fixed1600_600_8h     |       125 |             61 |          34 |          -127.48 |                 42.27 |             -25.29 |
| sweep_24bar_countertrend | fixed1600_600_8h     |       138 |             72 |          47 |          -129.19 |                -64.64 |              13.07 |
| session_vwap_weak        | atr_2r_8h            |       178 |             87 |          58 |          -131.29 |                -29.78 |            -194.26 |
| trend_24bar_break        | fixed2000_800_12h    |       163 |             83 |          51 |          -131.76 |                -83.35 |            -145.42 |
| trend_24bar_break        | fixed1600_600_8h     |       163 |             83 |          51 |          -133.94 |                -56.74 |            -105.17 |
| trend_24bar_break        | fixed1200_500_8h     |       163 |             83 |          51 |          -134.7  |               -115.01 |            -101.88 |
| trend_pullback_weak      | time4h_stop500       |       235 |            122 |          82 |          -136.56 |                -83.72 |            -100.5  |
| impulse_trend_strict     | time8h_stop700       |       151 |             81 |          48 |           -38.42 |               -136.6  |             -58.08 |
| trend_24bar_break        | time8h_stop700       |       163 |             83 |          51 |            50.6  |               -137.79 |             -28.09 |
| trend_pullback_ema20     | fixed800_400_4h      |       179 |             93 |          59 |           -92.04 |               -141.3  |            -201.82 |
| sweep_24bar_countertrend | fixed2000_800_12h    |       138 |             72 |          47 |          -141.51 |               -112.73 |              21.06 |
| sweep_24bar_countertrend | atr_2r_8h            |       138 |             72 |          47 |          -142.43 |                -69.69 |             -32.99 |
| impulse_trend_strict     | time4h_stop500       |       151 |             81 |          48 |          -117.81 |               -142.45 |            -110.68 |
| impulse_fade_open        | time4h_stop500       |       250 |            125 |          84 |          -142.93 |                -21    |             115.13 |
| trend_24bar_break        | fixed800_400_4h      |       163 |             83 |          51 |          -143.58 |                -38.3  |             -99.64 |
| session_vwap_weak        | fixed800_400_4h      |       178 |             87 |          58 |          -144.08 |                -72.66 |            -144.81 |
| opening_break_strict     | time4h_stop500       |        99 |             48 |          26 |            20.5  |               -145.68 |             100.97 |
| sweep_24bar_countertrend | fixed800_400_4h      |       138 |             72 |          47 |          -146.11 |               -100.15 |             -76.72 |
| sweep_24bar_opening      | fixed1200_500_8h     |       147 |             75 |          49 |          -110.13 |               -146.78 |             -83.25 |
| trend_24bar_break        | trail500_after500_8h |       163 |             83 |          51 |          -149.74 |                -64.47 |             -58.87 |
| trend_pullback_ema20     | atr_3r_8h            |       179 |             93 |          59 |          -149.78 |               -115.29 |             -90.64 |
| trend_12bar_break_strict | fixed800_400_4h      |       137 |             69 |          37 |          -150.49 |               -140.38 |            -133.63 |
| sweep_24bar_trend        | atr_3r_8h            |       119 |             57 |          36 |          -150.58 |               -111.02 |            -194.95 |
| sweep_24bar_trend        | fixed2000_800_12h    |       119 |             57 |          36 |          -143.15 |               -152.37 |            -180.18 |
| impulse_fade_open        | atr_3r_8h            |       250 |            125 |          84 |          -152.95 |                -54.72 |              68.62 |
| opening_break_strict     | fixed1200_500_8h     |        99 |             48 |          26 |          -153.61 |                -82    |              26.59 |
| opening_break_weak       | atr_2r_8h            |       125 |             61 |          34 |          -153.62 |                 20.02 |            -101.85 |
| trend_pullback_weak      | fixed2000_800_12h    |       235 |            122 |          82 |           -86.07 |               -154.66 |            -157.89 |
| sweep_24bar_trend        | atr_2r_8h            |       119 |             57 |          36 |          -155.47 |                -81.37 |            -139.94 |
| sweep_24bar_countertrend | fixed1200_500_8h     |       138 |             72 |          47 |          -155.56 |                -79.49 |             -89    |
| trend_12bar_break_strict | fixed1600_600_8h     |       137 |             69 |          37 |          -155.71 |               -100.27 |             -95.48 |
| trend_pullback_ema20     | fixed1200_500_8h     |       179 |             93 |          59 |          -157.25 |               -104.47 |            -129.93 |
| trend_pullback_ema20     | fixed2000_800_12h    |       179 |             93 |          59 |          -158.34 |               -142.28 |             -81.59 |
| sweep_24bar_opening      | time4h_stop500       |       147 |             75 |          49 |          -119.03 |               -158.63 |             -33.9  |
| trend_12bar_break_weak   | fixed800_400_4h      |       192 |             95 |          58 |          -159.51 |                -41.96 |            -148.38 |
| trend_12bar_break_strict | trail500_after500_8h |       137 |             69 |          37 |          -160.71 |               -154.82 |             -42.87 |
| trend_pullback_ema20     | time4h_stop500       |       179 |             93 |          59 |          -149.03 |               -161.06 |             -57.83 |
| trend_12bar_break_weak   | time8h_stop700       |       192 |             95 |          58 |           -30.21 |               -162.1  |             -56.37 |
| trend_12bar_break_weak   | fixed1200_500_8h     |       192 |             95 |          58 |          -162.69 |                -99.47 |            -142.5  |
| opening_break_strict     | time8h_stop700       |        99 |             48 |          26 |            60.9  |               -162.9  |             249.81 |
| sweep_24bar_opening      | atr_2r_8h            |       147 |             75 |          49 |          -115.66 |               -163.45 |             -49.82 |
| trend_12bar_break_weak   | atr_2r_8h            |       192 |             95 |          58 |          -163.82 |                -39.91 |            -153.95 |
| trend_12bar_break_strict | fixed1200_500_8h     |       137 |             69 |          37 |          -164.55 |               -141.24 |            -117.87 |
| trend_12bar_break_weak   | fixed1600_600_8h     |       192 |             95 |          58 |          -165.77 |                -52.95 |            -146.98 |
| trend_12bar_break_weak   | atr_3r_8h            |       192 |             95 |          58 |          -165.95 |                -22.14 |            -155.13 |
| opening_break_strict     | trail500_after500_8h |        99 |             48 |          26 |          -167.75 |                -61.09 |              -5.44 |
| opening_break_weak       | fixed800_400_4h      |       125 |             61 |          34 |          -168.84 |                -53.01 |            -103.73 |
| opening_break_weak       | trail500_after500_8h |       125 |             61 |          34 |          -169.01 |                -22.09 |             -89.87 |
| sweep_24bar_trend        | fixed1600_600_8h     |       119 |             57 |          36 |          -160.81 |               -169.73 |            -236.6  |
| opening_break_strict     | fixed1600_600_8h     |        99 |             48 |          26 |          -171.79 |                 45.29 |              67.84 |
| sweep_24bar_opening      | fixed1600_600_8h     |       147 |             75 |          49 |          -152.04 |               -172.35 |             -75.82 |
| session_vwap_reclaim     | fixed800_400_4h      |        94 |             45 |          25 |          -174.01 |               -160.64 |            -278.48 |
| h1_trend_15m_reclaim     | fixed800_400_4h      |        94 |             45 |          25 |          -174.01 |               -160.64 |            -278.48 |
| sweep_24bar_opening      | fixed800_400_4h      |       147 |             75 |          49 |           -92.69 |               -175.36 |             -16.34 |
| trend_12bar_break_weak   | trail500_after500_8h |       192 |             95 |          58 |          -175.44 |                -82.12 |             -95.83 |
| sweep_24bar_opening      | atr_3r_8h            |       147 |             75 |          49 |          -116.52 |               -175.52 |             -85.23 |
| impulse_trend_strict     | fixed800_400_4h      |       151 |             81 |          48 |          -175.76 |               -110.05 |            -241.98 |
| trend_12bar_break_weak   | fixed2000_800_12h    |       192 |             95 |          58 |          -175.85 |                -74.16 |            -125.96 |
| trend_12bar_break_strict | time4h_stop500       |       137 |             69 |          37 |           -66.18 |               -177.54 |              25.52 |
| impulse_trend_strict     | atr_3r_8h            |       151 |             81 |          48 |          -178.34 |               -121.77 |            -101.41 |
| session_vwap_weak        | trail500_after500_8h |       178 |             87 |          58 |          -180.25 |                -98.38 |            -147.89 |
| session_vwap_reclaim     | time4h_stop500       |        94 |             45 |          25 |          -167.18 |               -181.43 |            -218.3  |
| h1_trend_15m_reclaim     | time4h_stop500       |        94 |             45 |          25 |          -167.18 |               -181.43 |            -218.3  |
| opening_break_strict     | atr_2r_8h            |        99 |             48 |          26 |          -184.19 |                 24.41 |               0.65 |
| impulse_fade_open        | time8h_stop700       |       250 |            125 |          84 |          -185.42 |                -27.83 |             191.42 |
| session_vwap_weak        | fixed2000_800_12h    |       178 |             87 |          58 |          -187.51 |                -52.75 |            -192.2  |
| session_vwap_weak        | fixed1600_600_8h     |       178 |             87 |          58 |          -187.65 |                -33.42 |            -204.76 |
| session_vwap_weak        | fixed1200_500_8h     |       178 |             87 |          58 |          -189.01 |               -110.08 |            -149.41 |
| sweep_24bar_trend        | trail500_after500_8h |       119 |             57 |          36 |          -163.24 |               -189.35 |             -80.63 |
| trend_pullback_ema20     | fixed1600_600_8h     |       179 |             93 |          59 |          -189.59 |               -104.06 |            -135.4  |
| h1_trend_15m_reclaim     | atr_2r_8h            |        94 |             45 |          25 |          -189.6  |               -163.37 |            -267.47 |
| session_vwap_reclaim     | atr_2r_8h            |        94 |             45 |          25 |          -189.6  |               -163.37 |            -267.47 |
| impulse_trend_strict     | fixed1200_500_8h     |       151 |             81 |          48 |          -191.93 |                -80.63 |            -206.43 |
| sweep_24bar_countertrend | atr_3r_8h            |       138 |             72 |          47 |          -195.3  |                -49.36 |             -23.11 |
| sweep_24bar_opening      | fixed2000_800_12h    |       147 |             75 |          49 |          -124.47 |               -195.61 |             -34.74 |
| opening_break_strict     | fixed800_400_4h      |        99 |             48 |          26 |          -198.67 |               -110.05 |             -49.34 |
| impulse_trend_strict     | fixed1600_600_8h     |       151 |             81 |          48 |          -199.53 |                -66.4  |            -164.2  |
| trend_pullback_ema20     | atr_2r_8h            |       179 |             93 |          59 |          -199.76 |               -104.85 |             -85.38 |
| impulse_trend_strict     | trail500_after500_8h |       151 |             81 |          48 |          -203.72 |               -126.02 |            -129.27 |
| sweep_24bar_trend        | fixed1200_500_8h     |       119 |             57 |          36 |          -143.27 |               -209.18 |            -187.51 |
| session_vwap_reclaim     | fixed1600_600_8h     |        94 |             45 |          25 |          -209.19 |               -166.92 |            -325.21 |
| h1_trend_15m_reclaim     | fixed1600_600_8h     |        94 |             45 |          25 |          -209.19 |               -166.92 |            -325.21 |
| trend_12bar_break_strict | time8h_stop700       |       137 |             69 |          37 |            20.25 |               -209.82 |              31.81 |
| sweep_24bar_opening      | time8h_stop700       |       147 |             75 |          49 |          -154.59 |               -211.96 |             -44.21 |
| sweep_24bar_trend        | time8h_stop700       |       119 |             57 |          36 |          -210.18 |               -213.68 |            -246.89 |
| impulse_trend_strict     | fixed2000_800_12h    |       151 |             81 |          48 |          -216.07 |                -86.34 |            -165.71 |
| sweep_24bar_countertrend | time4h_stop500       |       138 |             72 |          47 |          -219.55 |                -71.47 |             -84.87 |
| session_vwap_reclaim     | trail500_after500_8h |        94 |             45 |          25 |          -188.66 |               -228.36 |            -256.85 |
| h1_trend_15m_reclaim     | trail500_after500_8h |        94 |             45 |          25 |          -188.66 |               -228.36 |            -256.85 |
| h1_trend_15m_reclaim     | atr_3r_8h            |        94 |             45 |          25 |          -232.98 |               -126.64 |            -243.52 |
| session_vwap_reclaim     | atr_3r_8h            |        94 |             45 |          25 |          -232.98 |               -126.64 |            -243.52 |
| impulse_trend_strict     | atr_2r_8h            |       151 |             81 |          48 |          -233.03 |                -52.3  |            -122.55 |
| session_vwap_reclaim     | fixed1200_500_8h     |        94 |             45 |          25 |          -192.9  |               -247.77 |            -293.2  |
| h1_trend_15m_reclaim     | fixed1200_500_8h     |        94 |             45 |          25 |          -192.9  |               -247.77 |            -293.2  |
| session_vwap_reclaim     | time8h_stop700       |        94 |             45 |          25 |          -261.91 |               -129.2  |            -370.18 |
| h1_trend_15m_reclaim     | time8h_stop700       |        94 |             45 |          25 |          -261.91 |               -129.2  |            -370.18 |
| h1_trend_15m_reclaim     | fixed2000_800_12h    |        94 |             45 |          25 |          -293.47 |                -47.14 |            -250.46 |
| session_vwap_reclaim     | fixed2000_800_12h    |        94 |             45 |          25 |          -293.47 |                -47.14 |            -250.46 |

## Main interpretation
- A profitable historical train+validation combination is a candidate hypothesis, not evidence that daily income is guaranteed.
- Holdout mean and maximum drawdown must be assessed jointly and with transaction-cost sensitivity and weekly block confidence intervals.
- Repeated testing of many candidates creates selection risk; do not tune a losing holdout to make it win, then call the same dates out-of-sample.
- OHLCV does not prove resting liquidity or actual institutional execution.

See candidate_entries.csv, all_trade_replays.csv, all_summary.csv and ranked_candidates.csv.
