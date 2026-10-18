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
  "files": 22,
  "one_minute_candles": 943200,
  "five_minute_candles": 188640,
  "fifteen_minute_candles": 62880,
  "hourly_candles": 15720,
  "first_utc": "2025-01-01 00:00:00+00:00",
  "last_utc": "2026-10-17 23:59:00+00:00",
  "zero_volume": 1819,
  "entry_events": 4272,
  "trade_simulations": 38448,
  "entries_by_setup": {
    "h1_trend_15m_reclaim": 157,
    "impulse_fade_open": 456,
    "impulse_trend_strict": 281,
    "opening_break_strict": 189,
    "opening_break_weak": 243,
    "session_vwap_reclaim": 157,
    "session_vwap_weak": 316,
    "sweep_24bar_countertrend": 274,
    "sweep_24bar_opening": 303,
    "sweep_24bar_trend": 211,
    "trend_12bar_break_strict": 264,
    "trend_12bar_break_weak": 339,
    "trend_24bar_break": 317,
    "trend_pullback_ema20": 332,
    "trend_pullback_weak": 433
  },
  "train_validation_positive_candidates": 0,
  "eligible_entry_exit_combinations": 117,
  "selection_note": "Ranking uses train and validation only; holdout not used for selection"
}

## Ranked entry/exit pairs (selection independent of final holdout)
Ranking by WORSE of train and validation average net profit; rank deliberately excludes holdout.
| setup                | exit_policy          |   n_train |   n_validation |   n_holdout |   mean_net_train |   mean_net_validation |   mean_net_holdout |   robust_score |
|:---------------------|:---------------------|----------:|---------------:|------------:|-----------------:|----------------------:|-------------------:|---------------:|
| session_vwap_weak    | time4h_stop500       |       178 |             85 |          53 |           -35.52 |                -56.07 |            -144.98 |         -56.07 |
| opening_break_weak   | fixed1600_600_8h     |       129 |             71 |          43 |           -60.73 |                 -2.6  |             -20.63 |         -60.73 |
| trend_pullback_weak  | trail500_after500_8h |       237 |            119 |          77 |           -68.84 |                -49.77 |             -97.33 |         -68.84 |
| opening_break_weak   | atr_2r_8h            |       129 |             71 |          43 |           -77.39 |                -30.4  |             -67.72 |         -77.39 |
| opening_break_strict | fixed1600_600_8h     |       102 |             59 |          28 |           -96.89 |                  8.61 |             -14.21 |         -96.89 |
| session_vwap_weak    | fixed800_400_4h      |       178 |             85 |          53 |           -99.65 |                -89.04 |            -134.1  |         -99.65 |
| session_vwap_weak    | time8h_stop700       |       178 |             85 |          53 |            22.43 |                -99.84 |            -188.34 |         -99.84 |
| trend_pullback_weak  | time4h_stop500       |       237 |            119 |          77 |          -100.33 |                  3.56 |             -70.1  |        -100.33 |
| impulse_fade_open    | time4h_stop500       |       254 |            127 |          75 |           -37.29 |               -102.2  |              16.31 |        -102.2  |
| trend_pullback_weak  | fixed800_400_4h      |       237 |            119 |          77 |          -104.59 |                -50.95 |            -116.66 |        -104.59 |

## All train/validation supported setups
| setup                    | exit_policy          |   n_train |   n_validation |   n_holdout |   mean_net_train |   mean_net_validation |   mean_net_holdout |
|:-------------------------|:---------------------|----------:|---------------:|------------:|-----------------:|----------------------:|-------------------:|
| session_vwap_weak        | time4h_stop500       |       178 |             85 |          53 |           -35.52 |                -56.07 |            -144.98 |
| opening_break_weak       | fixed1600_600_8h     |       129 |             71 |          43 |           -60.73 |                 -2.6  |             -20.63 |
| trend_pullback_weak      | trail500_after500_8h |       237 |            119 |          77 |           -68.84 |                -49.77 |             -97.33 |
| opening_break_weak       | atr_2r_8h            |       129 |             71 |          43 |           -77.39 |                -30.4  |             -67.72 |
| opening_break_strict     | fixed1600_600_8h     |       102 |             59 |          28 |           -96.89 |                  8.61 |             -14.21 |
| session_vwap_weak        | fixed800_400_4h      |       178 |             85 |          53 |           -99.65 |                -89.04 |            -134.1  |
| session_vwap_weak        | time8h_stop700       |       178 |             85 |          53 |            22.43 |                -99.84 |            -188.34 |
| trend_pullback_weak      | time4h_stop500       |       237 |            119 |          77 |          -100.33 |                  3.56 |             -70.1  |
| impulse_fade_open        | time4h_stop500       |       254 |            127 |          75 |           -37.29 |               -102.2  |              16.31 |
| trend_pullback_weak      | fixed800_400_4h      |       237 |            119 |          77 |          -104.59 |                -50.95 |            -116.66 |
| impulse_fade_open        | trail500_after500_8h |       254 |            127 |          75 |           -55.57 |               -105    |             -22.53 |
| trend_pullback_weak      | atr_2r_8h            |       237 |            119 |          77 |          -106.31 |                -83.62 |            -172.41 |
| trend_pullback_ema20     | time4h_stop500       |       182 |             91 |          59 |          -107.91 |                -60.33 |            -148.22 |
| impulse_fade_open        | fixed1200_500_8h     |       254 |            127 |          75 |           -45.43 |               -108.95 |             -39    |
| opening_break_weak       | fixed1200_500_8h     |       129 |             71 |          43 |          -109.4  |                -70.11 |              -1.94 |
| trend_pullback_ema20     | trail500_after500_8h |       182 |             91 |          59 |          -110.77 |               -112.29 |            -147.99 |
| opening_break_strict     | atr_2r_8h            |       102 |             59 |          28 |          -113.81 |                -14.16 |             -96.82 |
| trend_pullback_ema20     | atr_2r_8h            |       182 |             91 |          59 |           -95.09 |               -114.1  |            -211.26 |
| sweep_24bar_countertrend | fixed800_400_4h      |       146 |             85 |          43 |           -91.29 |               -115.22 |            -191.87 |
| opening_break_weak       | atr_3r_8h            |       129 |             71 |          43 |          -116.2  |                -32.14 |            -118.47 |
| trend_12bar_break_weak   | atr_2r_8h            |       179 |             99 |          61 |          -117.31 |               -112.31 |            -137.66 |
| impulse_fade_open        | atr_3r_8h            |       254 |            127 |          75 |          -114.25 |               -119.75 |             -17.13 |
| session_vwap_weak        | trail500_after500_8h |       178 |             85 |          53 |           -47.18 |               -119.84 |            -133.48 |
| trend_pullback_ema20     | fixed800_400_4h      |       182 |             91 |          59 |          -120.81 |                -68.45 |            -198.75 |
| opening_break_weak       | time8h_stop700       |       129 |             71 |          43 |          -121.75 |                -25.76 |              53.79 |
| trend_pullback_weak      | fixed2000_800_12h    |       237 |            119 |          77 |          -121.99 |                -85.24 |            -125.05 |
| trend_pullback_weak      | atr_3r_8h            |       237 |            119 |          77 |          -126.51 |                -28.16 |            -165.79 |
| opening_break_weak       | fixed800_400_4h      |       129 |             71 |          43 |          -126.78 |                -38.21 |             -43.15 |
| sweep_24bar_countertrend | trail500_after500_8h |       146 |             85 |          43 |           -94.03 |               -126.97 |            -112.95 |
| impulse_fade_open        | fixed800_400_4h      |       254 |            127 |          75 |           -58.6  |               -127.47 |             -13.46 |
| trend_pullback_ema20     | fixed2000_800_12h    |       182 |             91 |          59 |          -128.82 |               -107.9  |            -181.37 |
| impulse_fade_open        | time8h_stop700       |       254 |            127 |          75 |           -88.21 |               -130.15 |              22.92 |
| sweep_24bar_trend        | fixed800_400_4h      |       112 |             63 |          36 |           -86.87 |               -130.42 |             -22.13 |
| trend_pullback_weak      | fixed1600_600_8h     |       237 |            119 |          77 |          -132.29 |                -72.91 |            -113.92 |
| sweep_24bar_countertrend | fixed2000_800_12h    |       146 |             85 |          43 |            -4.03 |               -133.4  |             -92.87 |
| session_vwap_weak        | atr_3r_8h            |       178 |             85 |          53 |           -20.35 |               -133.89 |            -141.15 |
| impulse_fade_open        | fixed2000_800_12h    |       254 |            127 |          75 |          -102.58 |               -134.23 |              -4.57 |
| opening_break_weak       | time4h_stop500       |       129 |             71 |          43 |          -134.56 |                 35.12 |              18.2  |
| opening_break_weak       | trail500_after500_8h |       129 |             71 |          43 |          -134.94 |                -42.21 |              -4.52 |
| impulse_fade_open        | atr_2r_8h            |       254 |            127 |          75 |           -89.32 |               -136.02 |             -10.74 |
| trend_pullback_weak      | time8h_stop700       |       237 |            119 |          77 |          -137.16 |                -56.37 |             -75.45 |
| trend_12bar_break_weak   | fixed1600_600_8h     |       179 |             99 |          61 |          -137.24 |                -68.16 |            -124.01 |
| session_vwap_weak        | fixed1200_500_8h     |       178 |             85 |          53 |           -88.18 |               -138.07 |            -144.88 |
| trend_pullback_ema20     | atr_3r_8h            |       182 |             91 |          59 |          -138.17 |                -62.22 |            -198.03 |
| trend_pullback_weak      | fixed1200_500_8h     |       237 |            119 |          77 |          -142.63 |                -95.26 |            -109.98 |
| opening_break_strict     | trail500_after500_8h |       102 |             59 |          28 |          -147.31 |                -63.37 |               0.09 |
| trend_12bar_break_strict | fixed800_400_4h      |       142 |             77 |          45 |          -147.51 |               -138.19 |            -129.9  |
| impulse_fade_open        | fixed1600_600_8h     |       254 |            127 |          75 |           -84.08 |               -148.13 |             -27.12 |
| trend_12bar_break_weak   | fixed800_400_4h      |       179 |             99 |          61 |          -148.21 |                -90.21 |            -115.76 |
| sweep_24bar_trend        | time4h_stop500       |       112 |             63 |          36 |          -103.83 |               -148.21 |               3.72 |
| sweep_24bar_countertrend | fixed1200_500_8h     |       146 |             85 |          43 |           -37.43 |               -148.23 |            -149.69 |
| impulse_trend_strict     | trail500_after500_8h |       151 |             82 |          48 |          -147.93 |               -148.56 |            -142.46 |
| trend_pullback_ema20     | fixed1600_600_8h     |       182 |             91 |          59 |          -149.4  |               -138.38 |            -180.49 |
| trend_pullback_ema20     | fixed1200_500_8h     |       182 |             91 |          59 |          -151.22 |               -123.24 |            -180.72 |
| opening_break_strict     | time8h_stop700       |       102 |             59 |          28 |          -152.09 |                -19.31 |              11.47 |
| trend_24bar_break        | fixed800_400_4h      |       170 |             92 |          55 |          -154.53 |                -83.88 |            -122.04 |
| opening_break_strict     | fixed800_400_4h      |       102 |             59 |          28 |          -154.76 |                -36.82 |             -67.69 |
| trend_12bar_break_weak   | trail500_after500_8h |       179 |             99 |          61 |          -156.08 |               -102.32 |            -106.55 |
| trend_12bar_break_weak   | atr_3r_8h            |       179 |             99 |          61 |          -157.87 |               -128.52 |            -183.55 |
| sweep_24bar_trend        | fixed1200_500_8h     |       112 |             63 |          36 |          -153.69 |               -157.94 |              -4.87 |
| trend_12bar_break_strict | fixed1600_600_8h     |       142 |             77 |          45 |          -158    |               -153.91 |            -161.88 |
| trend_12bar_break_weak   | fixed1200_500_8h     |       179 |             99 |          61 |          -159.58 |               -119.31 |            -112.91 |
| impulse_trend_strict     | fixed1600_600_8h     |       151 |             82 |          48 |          -160.65 |               -145.55 |            -172.27 |
| session_vwap_weak        | atr_2r_8h            |       178 |             85 |          53 |           -27.5  |               -162.68 |             -88.55 |
| trend_12bar_break_weak   | time8h_stop700       |       179 |             99 |          61 |          -163.44 |                -69.46 |             -69.46 |
| sweep_24bar_countertrend | atr_2r_8h            |       146 |             85 |          43 |           -45.98 |               -165.95 |            -255.68 |
| opening_break_strict     | atr_3r_8h            |       102 |             59 |          28 |          -166.68 |                -29.66 |            -177.6  |
| trend_pullback_ema20     | time8h_stop700       |       182 |             91 |          59 |          -167.88 |               -133.75 |            -115.6  |
| trend_24bar_break        | fixed1600_600_8h     |       170 |             92 |          55 |          -169.74 |                -80.72 |            -157.62 |
| impulse_trend_strict     | fixed800_400_4h      |       151 |             82 |          48 |          -173.81 |                -96.25 |            -125.59 |
| sweep_24bar_countertrend | fixed1600_600_8h     |       146 |             85 |          43 |           -65.52 |               -174.17 |            -240.58 |
| sweep_24bar_trend        | trail500_after500_8h |       112 |             63 |          36 |          -116.34 |               -175.93 |               0.05 |
| trend_24bar_break        | fixed1200_500_8h     |       170 |             92 |          55 |          -176.03 |               -130.33 |            -171.62 |
| trend_24bar_break        | trail500_after500_8h |       170 |             92 |          55 |          -176.53 |               -129.48 |            -119.7  |
| opening_break_strict     | fixed1200_500_8h     |       102 |             59 |          28 |          -176.82 |                -56.31 |             -50.61 |
| session_vwap_weak        | fixed1600_600_8h     |       178 |             85 |          53 |           -67.44 |               -178.16 |            -146.82 |
| opening_break_weak       | fixed2000_800_12h    |       129 |             71 |          43 |          -179.61 |                -18.3  |             -94.04 |
| trend_12bar_break_strict | atr_2r_8h            |       142 |             77 |          45 |          -136.32 |               -180.8  |            -167.24 |
| impulse_trend_strict     | atr_2r_8h            |       151 |             82 |          48 |          -117.75 |               -182.14 |            -162.29 |
| sweep_24bar_countertrend | time8h_stop700       |       146 |             85 |          43 |            67.34 |               -182.23 |            -297.58 |
| trend_24bar_break        | atr_2r_8h            |       170 |             92 |          55 |          -183.16 |               -104.42 |            -152.6  |
| sweep_24bar_trend        | fixed1600_600_8h     |       112 |             63 |          36 |          -175.46 |               -183.38 |             -11.12 |
| trend_12bar_break_strict | trail500_after500_8h |       142 |             77 |          45 |          -167.08 |               -184.47 |            -107.57 |
| sweep_24bar_trend        | atr_2r_8h            |       112 |             63 |          36 |           -98.21 |               -184.89 |              18.23 |
| opening_break_strict     | time4h_stop500       |       102 |             59 |          28 |          -187.84 |                 36.23 |             -10.52 |
| trend_12bar_break_strict | fixed1200_500_8h     |       142 |             77 |          45 |          -187.85 |               -186.55 |            -161.56 |
| sweep_24bar_countertrend | atr_3r_8h            |       146 |             85 |          43 |           -40.57 |               -188.39 |            -237.24 |
| impulse_trend_strict     | fixed1200_500_8h     |       151 |             82 |          48 |          -191.43 |               -164.58 |            -178.18 |
| trend_12bar_break_weak   | time4h_stop500       |       179 |             99 |          61 |          -196.87 |                -50.39 |             -86.44 |
| trend_24bar_break        | time4h_stop500       |       170 |             92 |          55 |          -198.42 |                -66.81 |            -123.1  |
| session_vwap_weak        | fixed2000_800_12h    |       178 |             85 |          53 |           -57.68 |               -199.85 |            -185.62 |
| impulse_trend_strict     | time4h_stop500       |       151 |             82 |          48 |          -206.1  |               -111.36 |            -127.22 |
| opening_break_strict     | fixed2000_800_12h    |       102 |             59 |          28 |          -209.36 |                -17.78 |            -111.02 |
| sweep_24bar_countertrend | time4h_stop500       |       146 |             85 |          43 |            35.79 |               -209.75 |            -199.7  |
| trend_12bar_break_strict | time8h_stop700       |       142 |             77 |          45 |          -210.17 |               -100.74 |            -133.55 |
| impulse_trend_strict     | time8h_stop700       |       151 |             82 |          48 |          -210.34 |               -119.14 |             -68.43 |
| trend_24bar_break        | time8h_stop700       |       170 |             92 |          55 |          -215.19 |               -123.75 |             -75.91 |
| trend_24bar_break        | atr_3r_8h            |       170 |             92 |          55 |          -216.04 |               -110.05 |            -196.86 |
| trend_12bar_break_weak   | fixed2000_800_12h    |       179 |             99 |          61 |          -217.21 |                -82.66 |            -171.64 |
| impulse_trend_strict     | atr_3r_8h            |       151 |             82 |          48 |          -218.76 |               -129.17 |            -217.35 |
| sweep_24bar_opening      | fixed800_400_4h      |       164 |             87 |          52 |           -66.33 |               -220.39 |            -127.64 |
| trend_12bar_break_strict | time4h_stop500       |       142 |             77 |          45 |          -225.05 |               -124.45 |            -145.95 |
| sweep_24bar_opening      | fixed1600_600_8h     |       164 |             87 |          52 |          -138.67 |               -225.26 |             -63.33 |
| sweep_24bar_opening      | atr_2r_8h            |       164 |             87 |          52 |          -109.02 |               -237.41 |             -48.7  |
| sweep_24bar_opening      | trail500_after500_8h |       164 |             87 |          52 |          -117.59 |               -239.39 |             -32.27 |
| trend_12bar_break_strict | atr_3r_8h            |       142 |             77 |          45 |          -239.88 |               -164.98 |            -248.14 |
| trend_24bar_break        | fixed2000_800_12h    |       170 |             92 |          55 |          -253.54 |                -63.69 |            -167.86 |
| sweep_24bar_trend        | atr_3r_8h            |       112 |             63 |          36 |           -75.56 |               -261.15 |             -95.67 |
| impulse_trend_strict     | fixed2000_800_12h    |       151 |             82 |          48 |          -265.13 |               -113.32 |            -109.19 |
| sweep_24bar_opening      | fixed1200_500_8h     |       164 |             87 |          52 |          -112.36 |               -267.34 |             -96.27 |
| trend_12bar_break_strict | fixed2000_800_12h    |       142 |             77 |          45 |          -279.33 |                -91.62 |            -178.87 |
| sweep_24bar_trend        | time8h_stop700       |       112 |             63 |          36 |           -43.06 |               -285.42 |              -6.58 |
| sweep_24bar_opening      | atr_3r_8h            |       164 |             87 |          52 |          -146.53 |               -294.71 |             -60.01 |
| sweep_24bar_trend        | fixed2000_800_12h    |       112 |             63 |          36 |          -148.01 |               -296.79 |             -69.33 |
| sweep_24bar_opening      | time8h_stop700       |       164 |             87 |          52 |          -137.51 |               -299.09 |             -80.81 |
| sweep_24bar_opening      | time4h_stop500       |       164 |             87 |          52 |           -98.44 |               -302.06 |            -135.6  |
| sweep_24bar_opening      | fixed2000_800_12h    |       164 |             87 |          52 |          -169.65 |               -324.7  |              -8.13 |

## Main interpretation
- A profitable historical train+validation combination is a candidate hypothesis, not evidence that daily income is guaranteed.
- Holdout mean and maximum drawdown must be assessed jointly and with transaction-cost sensitivity and weekly block confidence intervals.
- Repeated testing of many candidates creates selection risk; do not tune a losing holdout to make it win, then call the same dates out-of-sample.
- OHLCV does not prove resting liquidity or actual institutional execution.

See candidate_entries.csv, all_trade_replays.csv, all_summary.csv and ranked_candidates.csv.
