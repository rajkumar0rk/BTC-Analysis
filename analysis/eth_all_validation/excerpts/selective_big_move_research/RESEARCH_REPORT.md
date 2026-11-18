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
| setup                  | exit_policy       |   n_train |   n_validation |   n_holdout |   mean_net_train |   mean_net_validation |   mean_net_holdout |   robust_score |
|:-----------------------|:------------------|----------:|---------------:|------------:|-----------------:|----------------------:|-------------------:|---------------:|
| trend_24bar_break      | fixed800_400_4h   |       163 |             83 |          56 |            -5.47 |                 -9.47 |             -15.14 |          -9.47 |
| trend_24bar_break      | time4h_stop500    |       163 |             83 |          56 |            -5.47 |                 -9.47 |             -15.14 |          -9.47 |
| opening_break_weak     | fixed800_400_4h   |       125 |             61 |          39 |            -9.98 |                 -7.41 |             -16.52 |          -9.98 |
| opening_break_weak     | time4h_stop500    |       125 |             61 |          39 |            -9.98 |                 -7.41 |             -16.52 |          -9.98 |
| trend_12bar_break_weak | fixed800_400_4h   |       192 |             95 |          65 |           -10.27 |                -10.31 |             -14.94 |         -10.31 |
| trend_12bar_break_weak | time4h_stop500    |       192 |             95 |          65 |           -10.27 |                -10.31 |             -14.94 |         -10.31 |
| opening_break_weak     | fixed2000_800_12h |       125 |             61 |          39 |           -10.39 |                 -7.9  |              -9.34 |         -10.39 |
| trend_24bar_break      | fixed2000_800_12h |       163 |             83 |          56 |            -8.15 |                -10.58 |             -13.26 |         -10.58 |
| opening_break_weak     | atr_3r_8h         |       125 |             61 |          39 |           -10.63 |                 -6.65 |             -11.34 |         -10.63 |
| trend_24bar_break      | atr_2r_8h         |       163 |             83 |          56 |            -6.79 |                -10.76 |             -12.86 |         -10.76 |

## All train/validation supported setups
| setup                    | exit_policy          |   n_train |   n_validation |   n_holdout |   mean_net_train |   mean_net_validation |   mean_net_holdout |
|:-------------------------|:---------------------|----------:|---------------:|------------:|-----------------:|----------------------:|-------------------:|
| trend_24bar_break        | fixed800_400_4h      |       163 |             83 |          56 |            -5.47 |                 -9.47 |             -15.14 |
| trend_24bar_break        | time4h_stop500       |       163 |             83 |          56 |            -5.47 |                 -9.47 |             -15.14 |
| opening_break_weak       | fixed800_400_4h      |       125 |             61 |          39 |            -9.98 |                 -7.41 |             -16.52 |
| opening_break_weak       | time4h_stop500       |       125 |             61 |          39 |            -9.98 |                 -7.41 |             -16.52 |
| trend_12bar_break_weak   | fixed800_400_4h      |       192 |             95 |          65 |           -10.27 |                -10.31 |             -14.94 |
| trend_12bar_break_weak   | time4h_stop500       |       192 |             95 |          65 |           -10.27 |                -10.31 |             -14.94 |
| opening_break_weak       | fixed2000_800_12h    |       125 |             61 |          39 |           -10.39 |                 -7.9  |              -9.34 |
| trend_24bar_break        | fixed2000_800_12h    |       163 |             83 |          56 |            -8.15 |                -10.58 |             -13.26 |
| opening_break_weak       | atr_3r_8h            |       125 |             61 |          39 |           -10.63 |                 -6.65 |             -11.34 |
| trend_24bar_break        | atr_2r_8h            |       163 |             83 |          56 |            -6.79 |                -10.76 |             -12.86 |
| trend_24bar_break        | atr_3r_8h            |       163 |             83 |          56 |            -5.26 |                -10.76 |             -12.86 |
| trend_24bar_break        | fixed1600_600_8h     |       163 |             83 |          56 |            -6.11 |                -10.76 |             -12.86 |
| trend_24bar_break        | time8h_stop700       |       163 |             83 |          56 |            -6.11 |                -10.76 |             -12.86 |
| trend_24bar_break        | trail500_after500_8h |       163 |             83 |          56 |            -6.26 |                -10.76 |             -12.86 |
| trend_24bar_break        | fixed1200_500_8h     |       163 |             83 |          56 |            -6.11 |                -10.76 |             -12.86 |
| trend_12bar_break_weak   | atr_3r_8h            |       192 |             95 |          65 |           -10.9  |                -11.04 |             -13.19 |
| trend_12bar_break_weak   | fixed1200_500_8h     |       192 |             95 |          65 |           -11.62 |                -11.04 |             -13.19 |
| trend_12bar_break_weak   | time8h_stop700       |       192 |             95 |          65 |           -11.62 |                -11.04 |             -13.19 |
| trend_12bar_break_weak   | fixed1600_600_8h     |       192 |             95 |          65 |           -11.62 |                -11.04 |             -13.19 |
| opening_break_weak       | time8h_stop700       |       125 |             61 |          39 |           -11.73 |                 -6.65 |             -11.34 |
| opening_break_weak       | fixed1200_500_8h     |       125 |             61 |          39 |           -11.73 |                 -6.65 |             -11.34 |
| opening_break_weak       | fixed1600_600_8h     |       125 |             61 |          39 |           -11.73 |                 -6.65 |             -11.34 |
| trend_12bar_break_weak   | trail500_after500_8h |       192 |             95 |          65 |           -11.74 |                -11.04 |             -13.19 |
| trend_12bar_break_strict | fixed800_400_4h      |       137 |             69 |          43 |            -9.97 |                -11.75 |              -9.37 |
| trend_12bar_break_strict | time4h_stop500       |       137 |             69 |          43 |            -9.97 |                -11.75 |              -9.37 |
| trend_pullback_weak      | time4h_stop500       |       235 |            122 |          93 |           -11.82 |                -10.6  |             -14.33 |
| trend_pullback_weak      | fixed800_400_4h      |       235 |            122 |          93 |           -11.82 |                -10.6  |             -14.33 |
| opening_break_strict     | fixed2000_800_12h    |        99 |             48 |          31 |           -11.85 |                -10.94 |               0.4  |
| opening_break_weak       | trail500_after500_8h |       125 |             61 |          39 |           -11.93 |                 -6.65 |             -11.34 |
| trend_12bar_break_weak   | atr_2r_8h            |       192 |             95 |          65 |           -12.21 |                -11.04 |             -13.19 |
| opening_break_weak       | atr_2r_8h            |       125 |             61 |          39 |           -12.64 |                 -6.65 |             -11.34 |
| trend_12bar_break_strict | atr_3r_8h            |       137 |             69 |          43 |           -13.18 |                 -9.45 |              -6.53 |
| trend_12bar_break_weak   | fixed2000_800_12h    |       192 |             95 |          65 |           -13.31 |                -11.94 |             -12.95 |
| opening_break_strict     | time4h_stop500       |        99 |             48 |          31 |           -13.74 |                -11.2  |             -10.37 |
| opening_break_strict     | fixed800_400_4h      |        99 |             48 |          31 |           -13.74 |                -11.2  |             -10.37 |
| impulse_trend_strict     | fixed800_400_4h      |       151 |             81 |          55 |           -14.01 |                -13.67 |             -15.33 |
| impulse_trend_strict     | time4h_stop500       |       151 |             81 |          55 |           -14.01 |                -13.67 |             -15.33 |
| trend_12bar_break_strict | time8h_stop700       |       137 |             69 |          43 |           -14.37 |                 -9.45 |              -6.53 |
| trend_12bar_break_strict | fixed1200_500_8h     |       137 |             69 |          43 |           -14.37 |                 -9.45 |              -6.53 |
| trend_12bar_break_strict | fixed1600_600_8h     |       137 |             69 |          43 |           -14.37 |                 -9.45 |              -6.53 |
| session_vwap_weak        | atr_3r_8h            |       178 |             87 |          65 |           -14.45 |                -10.57 |             -17.59 |
| trend_12bar_break_strict | fixed2000_800_12h    |       137 |             69 |          43 |           -14.5  |                -12.23 |             -10.18 |
| trend_12bar_break_strict | trail500_after500_8h |       137 |             69 |          43 |           -14.75 |                 -9.45 |              -6.53 |
| session_vwap_weak        | time4h_stop500       |       178 |             87 |          65 |           -15    |                -12.47 |             -15.14 |
| session_vwap_weak        | fixed800_400_4h      |       178 |             87 |          65 |           -15    |                -12.47 |             -15.14 |
| trend_12bar_break_strict | atr_2r_8h            |       137 |             69 |          43 |           -15    |                 -9.45 |              -6.53 |
| sweep_24bar_countertrend | atr_3r_8h            |       138 |             72 |          52 |           -15.4  |                -13.09 |             -12.06 |
| sweep_24bar_countertrend | atr_2r_8h            |       138 |             72 |          52 |           -15.4  |                -13.09 |             -12.06 |
| trend_pullback_weak      | atr_2r_8h            |       235 |            122 |          93 |           -15.62 |                 -9.8  |             -12.84 |
| trend_pullback_weak      | atr_3r_8h            |       235 |            122 |          93 |           -15.62 |                 -9.8  |             -12.84 |
| trend_pullback_ema20     | time4h_stop500       |       179 |             93 |          67 |           -14.48 |                -15.73 |             -13.8  |
| trend_pullback_ema20     | fixed800_400_4h      |       179 |             93 |          67 |           -14.48 |                -15.73 |             -13.8  |
| trend_pullback_weak      | fixed1600_600_8h     |       235 |            122 |          93 |           -15.76 |                 -9.8  |             -12.84 |
| trend_pullback_weak      | trail500_after500_8h |       235 |            122 |          93 |           -15.76 |                 -9.8  |             -12.84 |
| trend_pullback_weak      | fixed1200_500_8h     |       235 |            122 |          93 |           -15.76 |                 -9.8  |             -12.84 |
| trend_pullback_weak      | time8h_stop700       |       235 |            122 |          93 |           -15.76 |                 -9.8  |             -12.84 |
| sweep_24bar_trend        | fixed800_400_4h      |       119 |             57 |          39 |           -15.83 |                -11.29 |             -20.4  |
| sweep_24bar_trend        | time4h_stop500       |       119 |             57 |          39 |           -15.83 |                -11.29 |             -20.4  |
| impulse_trend_strict     | atr_3r_8h            |       151 |             81 |          55 |           -15.84 |                -10.12 |             -12.05 |
| session_vwap_weak        | atr_2r_8h            |       178 |             87 |          65 |           -15.86 |                -10.57 |             -17.59 |
| sweep_24bar_countertrend | time8h_stop700       |       138 |             72 |          52 |           -16.13 |                -13.09 |             -12.06 |
| session_vwap_weak        | time8h_stop700       |       178 |             87 |          65 |           -16.13 |                -10.57 |             -17.59 |
| session_vwap_weak        | fixed1600_600_8h     |       178 |             87 |          65 |           -16.13 |                -10.57 |             -17.59 |
| session_vwap_weak        | fixed1200_500_8h     |       178 |             87 |          65 |           -16.13 |                -10.57 |             -17.59 |
| session_vwap_weak        | trail500_after500_8h |       178 |             87 |          65 |           -16.27 |                -10.57 |             -17.59 |
| opening_break_strict     | atr_3r_8h            |        99 |             48 |          31 |           -16.44 |                 -8.84 |              -1.45 |
| trend_pullback_weak      | fixed2000_800_12h    |       235 |            122 |          93 |           -16.83 |                -12.71 |             -13.39 |
| impulse_trend_strict     | fixed1200_500_8h     |       151 |             81 |          55 |           -17.12 |                -10.12 |             -12.05 |
| impulse_trend_strict     | time8h_stop700       |       151 |             81 |          55 |           -17.12 |                -10.12 |             -12.05 |
| impulse_trend_strict     | fixed1600_600_8h     |       151 |             81 |          55 |           -17.12 |                -10.12 |             -12.05 |
| sweep_24bar_trend        | atr_2r_8h            |       119 |             57 |          39 |           -13.07 |                -17.19 |             -21.78 |
| sweep_24bar_trend        | fixed1600_600_8h     |       119 |             57 |          39 |           -11.31 |                -17.19 |             -21.78 |
| sweep_24bar_trend        | fixed1200_500_8h     |       119 |             57 |          39 |           -11.31 |                -17.19 |             -21.78 |
| sweep_24bar_trend        | atr_3r_8h            |       119 |             57 |          39 |           -10.97 |                -17.19 |             -21.78 |
| sweep_24bar_trend        | trail500_after500_8h |       119 |             57 |          39 |           -11.31 |                -17.19 |             -21.78 |
| sweep_24bar_trend        | time8h_stop700       |       119 |             57 |          39 |           -11.31 |                -17.19 |             -21.78 |
| sweep_24bar_countertrend | trail500_after500_8h |       138 |             72 |          52 |           -17.25 |                -13.09 |             -12.06 |
| sweep_24bar_countertrend | fixed1200_500_8h     |       138 |             72 |          52 |           -17.25 |                -13.09 |             -12.06 |
| trend_pullback_ema20     | fixed2000_800_12h    |       179 |             93 |          67 |           -17.33 |                -13.53 |             -11.67 |
| impulse_trend_strict     | trail500_after500_8h |       151 |             81 |          55 |           -17.46 |                -10.12 |             -12.05 |
| impulse_trend_strict     | atr_2r_8h            |       151 |             81 |          55 |           -17.49 |                -10.12 |             -12.05 |
| opening_break_strict     | fixed1200_500_8h     |        99 |             48 |          31 |           -17.82 |                 -8.84 |              -1.45 |
| opening_break_strict     | time8h_stop700       |        99 |             48 |          31 |           -17.82 |                 -8.84 |              -1.45 |
| opening_break_strict     | fixed1600_600_8h     |        99 |             48 |          31 |           -17.82 |                 -8.84 |              -1.45 |
| sweep_24bar_countertrend | fixed2000_800_12h    |       138 |             72 |          52 |           -17.96 |                -16.87 |             -10.93 |
| sweep_24bar_countertrend | fixed1600_600_8h     |       138 |             72 |          52 |           -17.97 |                -13.09 |             -12.06 |
| opening_break_strict     | trail500_after500_8h |        99 |             48 |          31 |           -18.07 |                 -8.84 |              -1.45 |
| trend_pullback_ema20     | atr_2r_8h            |       179 |             93 |          67 |           -18.08 |                -11.07 |              -9.43 |
| trend_pullback_ema20     | atr_3r_8h            |       179 |             93 |          67 |           -18.08 |                -11.07 |              -9.43 |
| impulse_trend_strict     | fixed2000_800_12h    |       151 |             81 |          55 |           -18.23 |                -12.77 |             -13.19 |
| trend_pullback_ema20     | trail500_after500_8h |       179 |             93 |          67 |           -18.26 |                -11.07 |              -9.43 |
| trend_pullback_ema20     | fixed1600_600_8h     |       179 |             93 |          67 |           -18.26 |                -11.07 |              -9.43 |
| trend_pullback_ema20     | fixed1200_500_8h     |       179 |             93 |          67 |           -18.26 |                -11.07 |              -9.43 |
| trend_pullback_ema20     | time8h_stop700       |       179 |             93 |          67 |           -18.26 |                -11.07 |              -9.43 |
| sweep_24bar_opening      | fixed2000_800_12h    |       147 |             75 |          52 |           -18.22 |                -18.6  |              -8.49 |
| opening_break_strict     | atr_2r_8h            |        99 |             48 |          31 |           -18.96 |                 -8.84 |              -1.45 |
| sweep_24bar_opening      | time8h_stop700       |       147 |             75 |          52 |           -19.34 |                -16.43 |             -12.87 |
| sweep_24bar_opening      | trail500_after500_8h |       147 |             75 |          52 |           -19.34 |                -16.43 |             -12.87 |
| sweep_24bar_opening      | fixed1200_500_8h     |       147 |             75 |          52 |           -19.34 |                -16.43 |             -12.87 |
| sweep_24bar_opening      | fixed1600_600_8h     |       147 |             75 |          52 |           -19.34 |                -16.43 |             -12.87 |
| sweep_24bar_opening      | atr_2r_8h            |       147 |             75 |          52 |           -19.91 |                -16.43 |             -12.87 |
| sweep_24bar_opening      | atr_3r_8h            |       147 |             75 |          52 |           -19.91 |                -16.43 |             -12.87 |
| sweep_24bar_opening      | time4h_stop500       |       147 |             75 |          52 |           -20.13 |                -16.26 |             -10.61 |
| sweep_24bar_opening      | fixed800_400_4h      |       147 |             75 |          52 |           -20.13 |                -16.26 |             -10.61 |
| session_vwap_reclaim     | fixed800_400_4h      |        94 |             45 |          30 |           -20.62 |                -13.78 |             -16.87 |
| h1_trend_15m_reclaim     | time4h_stop500       |        94 |             45 |          30 |           -20.62 |                -13.78 |             -16.87 |
| session_vwap_reclaim     | time4h_stop500       |        94 |             45 |          30 |           -20.62 |                -13.78 |             -16.87 |
| h1_trend_15m_reclaim     | fixed800_400_4h      |        94 |             45 |          30 |           -20.62 |                -13.78 |             -16.87 |
| sweep_24bar_trend        | fixed2000_800_12h    |       119 |             57 |          39 |           -14.42 |                -20.64 |             -16.85 |
| session_vwap_weak        | fixed2000_800_12h    |       178 |             87 |          65 |           -20.66 |                -13.43 |             -14.74 |
| sweep_24bar_countertrend | fixed800_400_4h      |       138 |             72 |          52 |           -21.94 |                -13.82 |             -12.36 |
| h1_trend_15m_reclaim     | atr_2r_8h            |        94 |             45 |          30 |           -22.55 |                -12.79 |             -19.94 |
| session_vwap_reclaim     | atr_2r_8h            |        94 |             45 |          30 |           -22.55 |                -12.79 |             -19.94 |
| session_vwap_reclaim     | atr_3r_8h            |        94 |             45 |          30 |           -22.55 |                -12.79 |             -19.94 |
| h1_trend_15m_reclaim     | atr_3r_8h            |        94 |             45 |          30 |           -22.55 |                -12.79 |             -19.94 |
| sweep_24bar_countertrend | time4h_stop500       |       138 |             72 |          52 |           -22.67 |                -13.82 |             -12.36 |
| session_vwap_reclaim     | fixed1200_500_8h     |        94 |             45 |          30 |           -22.88 |                -12.79 |             -19.94 |
| h1_trend_15m_reclaim     | fixed1200_500_8h     |        94 |             45 |          30 |           -22.88 |                -12.79 |             -19.94 |
| h1_trend_15m_reclaim     | fixed1600_600_8h     |        94 |             45 |          30 |           -22.88 |                -12.79 |             -19.94 |
| h1_trend_15m_reclaim     | trail500_after500_8h |        94 |             45 |          30 |           -22.88 |                -12.79 |             -19.94 |
| h1_trend_15m_reclaim     | time8h_stop700       |        94 |             45 |          30 |           -22.88 |                -12.79 |             -19.94 |
| session_vwap_reclaim     | trail500_after500_8h |        94 |             45 |          30 |           -22.88 |                -12.79 |             -19.94 |
| session_vwap_reclaim     | time8h_stop700       |        94 |             45 |          30 |           -22.88 |                -12.79 |             -19.94 |
| session_vwap_reclaim     | fixed1600_600_8h     |        94 |             45 |          30 |           -22.88 |                -12.79 |             -19.94 |
| impulse_fade_open        | fixed800_400_4h      |       250 |            125 |          95 |           -23.81 |                -12.61 |              -6.61 |
| impulse_fade_open        | time4h_stop500       |       250 |            125 |          95 |           -24.21 |                -12.61 |              -6.61 |
| impulse_fade_open        | atr_3r_8h            |       250 |            125 |          95 |           -26.36 |                -13.68 |              -6.39 |
| impulse_fade_open        | atr_2r_8h            |       250 |            125 |          95 |           -26.36 |                -13.68 |              -6.39 |
| h1_trend_15m_reclaim     | fixed2000_800_12h    |        94 |             45 |          30 |           -27.71 |                 -9.97 |             -18.14 |
| impulse_fade_open        | trail500_after500_8h |       250 |            125 |          95 |           -27.71 |                -13.68 |              -6.39 |
| impulse_fade_open        | fixed1200_500_8h     |       250 |            125 |          95 |           -27.71 |                -13.68 |              -6.39 |
| session_vwap_reclaim     | fixed2000_800_12h    |        94 |             45 |          30 |           -27.71 |                 -9.97 |             -18.14 |
| impulse_fade_open        | fixed1600_600_8h     |       250 |            125 |          95 |           -28.41 |                -13.68 |              -6.39 |
| impulse_fade_open        | time8h_stop700       |       250 |            125 |          95 |           -28.81 |                -13.68 |              -6.39 |
| impulse_fade_open        | fixed2000_800_12h    |       250 |            125 |          95 |           -30.03 |                -14.27 |              -5.87 |

## Main interpretation
- A profitable historical train+validation combination is a candidate hypothesis, not evidence that daily income is guaranteed.
- Holdout mean and maximum drawdown must be assessed jointly and with transaction-cost sensitivity and weekly block confidence intervals.
- Repeated testing of many candidates creates selection risk; do not tune a losing holdout to make it win, then call the same dates out-of-sample.
- OHLCV does not prove resting liquidity or actual institutional execution.

See candidate_entries.csv, all_trade_replays.csv, all_summary.csv and ranked_candidates.csv.
