# Stage 6 — Every ETHUSD 1m candle: 200 points, clean paths and executable entries

## Dataset audit
- Real 1m candles loaded: **987,840**
- Fully eligible next-open entries: **986,704** per direction
- All long+short entry paths evaluated: **1,973,408**
- Gaps: **0** missing minutes across **0** breaks; never filled
- Predeclared directional rule names: **18**
- Strict zero-loss strategies with at least 100 trades in a period: **0** cells (not a guarantee)

## Honest definitions
- 'Clean 200' means no adverse midprice movement in ANY 1m OHLC bar before or in the TP minute.
- First 200 achieved within horizon is an ex-post label, not an entry signal.
- 200 net after standard fees requires a larger dynamic price target, computed using actual entry BTC price.
- Same-bar stop and target ambiguity is ALWAYS counted as a stop.
- One trade at a time separately for each candidate model, no forced daily trades.
- Standard scenario: 0.05% taker each side + 18% GST and 5 points adverse slippage each side.
- Scalper scenario: closing fee waived only if the modeled holding time is <=30m, conditional on eligibility.
- All historical intervals including November 2026 are exploratory; do not claim an independent holdout.

## Unconditional all-candle reference (not a portfolio)
| rule               | period                      |   horizon_min |   signals |   target_200_pct |   clean_200_zero_adverse_pct |   tp_before_stop_100_pct |   target_200_net_after_fees_pct |
|:-------------------|:----------------------------|--------------:|----------:|-----------------:|-----------------------------:|-------------------------:|--------------------------------:|
| every_minute_long  | 2025_train                  |            30 |    525181 |            0.018 |                      0.0019  |                    0.016 |                           0.016 |
| every_minute_long  | 2025_train                  |            60 |    525181 |            0.038 |                      0.00209 |                    0.036 |                           0.034 |
| every_minute_long  | 2025_train                  |           240 |    525181 |            0.37  |                      0.00838 |                    0.361 |                           0.287 |
| every_minute_long  | 2026_H1_validation          |            30 |    260401 |            0     |                      0       |                    0     |                           0     |
| every_minute_long  | 2026_H1_validation          |            60 |    260401 |            0     |                      0       |                    0     |                           0     |
| every_minute_long  | 2026_H1_validation          |           240 |    260401 |            0.02  |                      0.00038 |                    0.02  |                           0.014 |
| every_minute_long  | 2026_H2_seen_recheck        |            30 |    176881 |            0.007 |                      0       |                    0.007 |                           0.004 |
| every_minute_long  | 2026_H2_seen_recheck        |            60 |    176881 |            0.024 |                      0.00113 |                    0.024 |                           0.018 |
| every_minute_long  | 2026_H2_seen_recheck        |           240 |    176881 |            0.201 |                      0.00565 |                    0.201 |                           0.127 |
| every_minute_long  | 2026_Nov_recent_exploratory |            30 |     24241 |            0     |                      0       |                    0     |                           0     |
| every_minute_long  | 2026_Nov_recent_exploratory |            60 |     24241 |            0     |                      0       |                    0     |                           0     |
| every_minute_long  | 2026_Nov_recent_exploratory |           240 |     24241 |            0     |                      0       |                    0     |                           0     |
| every_minute_short | 2025_train                  |            30 |    525181 |            0.033 |                      0.00152 |                    0.033 |                           0.025 |
| every_minute_short | 2025_train                  |            60 |    525181 |            0.071 |                      0.00343 |                    0.07  |                           0.06  |
| every_minute_short | 2025_train                  |           240 |    525181 |            0.754 |                      0.0297  |                    0.754 |                           0.571 |
| every_minute_short | 2026_H1_validation          |            30 |    260401 |            0     |                      0       |                    0     |                           0     |
| every_minute_short | 2026_H1_validation          |            60 |    260401 |            0     |                      0       |                    0     |                           0     |
| every_minute_short | 2026_H1_validation          |           240 |    260401 |            0.086 |                      0.00115 |                    0.086 |                           0.086 |
| every_minute_short | 2026_H2_seen_recheck        |            30 |    176881 |            0     |                      0       |                    0     |                           0     |
| every_minute_short | 2026_H2_seen_recheck        |            60 |    176881 |            0     |                      0       |                    0     |                           0     |
| every_minute_short | 2026_H2_seen_recheck        |           240 |    176881 |            0     |                      0       |                    0     |                           0     |
| every_minute_short | 2026_Nov_recent_exploratory |            30 |     24241 |            0     |                      0       |                    0     |                           0     |
| every_minute_short | 2026_Nov_recent_exploratory |            60 |     24241 |            0     |                      0       |                    0     |                           0     |
| every_minute_short | 2026_Nov_recent_exploratory |           240 |     24241 |            0     |                      0       |                    0     |                           0     |

## Predeclared executable strategies at 200 gross TP / 100 stop / 30m max
| rule                         | period                      |   trades |   win_pct |   avg_net_pts |   profit_factor |   max_drawdown_pts |   worst_net_trade_pts |   losses_or_flat |
|:-----------------------------|:----------------------------|---------:|----------:|--------------:|----------------:|-------------------:|----------------------:|-----------------:|
| 15min_close_breakout_long    | 2025_train                  |      650 |     17.23 |       -13.994 |           0.181 |            9096.06 |               -115.36 |              538 |
| 15min_close_breakout_long    | 2026_H1_validation          |      254 |      9.06 |       -13.402 |           0.06  |            3406.77 |                -65.44 |              231 |
| 15min_close_breakout_long    | 2026_H2_seen_recheck        |      218 |      6.42 |       -13.3   |           0.078 |            2899.46 |                -68.6  |              204 |
| 15min_close_breakout_long    | 2026_Nov_recent_exploratory |       17 |     11.76 |        -7.395 |           0.41  |             131.98 |                -25.12 |               15 |
| 15min_close_breakout_short   | 2025_train                  |      657 |     16.59 |       -13.283 |           0.204 |            8727.04 |                -99.76 |              548 |
| 15min_close_breakout_short   | 2026_H1_validation          |      310 |     11.94 |       -12.254 |           0.126 |            3798.84 |               -112.14 |              273 |
| 15min_close_breakout_short   | 2026_H2_seen_recheck        |      208 |      9.62 |       -12.594 |           0.066 |            2619.6  |                -45.19 |              188 |
| 15min_close_breakout_short   | 2026_Nov_recent_exploratory |       33 |     15.15 |       -10.394 |           0.33  |             343    |                -75.06 |               28 |
| 20m_accepted_breakout_long   | 2025_train                  |     5958 |     11.97 |       -13.769 |           0.11  |           82037    |               -115.34 |             5245 |
| 20m_accepted_breakout_long   | 2026_H1_validation          |     2780 |      6.22 |       -13.117 |           0.054 |           36466.1  |               -113.05 |             2607 |
| 20m_accepted_breakout_long   | 2026_H2_seen_recheck        |     1995 |      4.21 |       -12.596 |           0.033 |           25128.7  |                -90.13 |             1911 |
| 20m_accepted_breakout_long   | 2026_Nov_recent_exploratory |      266 |      4.51 |       -13.536 |           0.042 |            3600.69 |                -72.35 |              254 |
| 20m_accepted_breakout_short  | 2025_train                  |     5790 |     13.28 |       -13.693 |           0.131 |           79280.5  |               -115.52 |             5021 |
| 20m_accepted_breakout_short  | 2026_H1_validation          |     2918 |      7.78 |       -12.632 |           0.068 |           36861.4  |               -113.5  |             2691 |
| 20m_accepted_breakout_short  | 2026_H2_seen_recheck        |     2021 |      4.16 |       -13.028 |           0.032 |           26330.3  |               -113    |             1937 |
| 20m_accepted_breakout_short  | 2026_Nov_recent_exploratory |      307 |      5.86 |       -12.173 |           0.065 |            3737.19 |                -46.42 |              289 |
| 20m_rejected_sweep_long      | 2025_train                  |     4853 |     12.73 |       -13.897 |           0.096 |           67440.3  |               -115.58 |             4235 |
| 20m_rejected_sweep_long      | 2026_H1_validation          |     2435 |      5.75 |       -12.942 |           0.036 |           31513.3  |               -112.86 |             2295 |
| 20m_rejected_sweep_long      | 2026_H2_seen_recheck        |     1729 |      4.63 |       -12.54  |           0.025 |           21685.3  |               -112.91 |             1649 |
| 20m_rejected_sweep_long      | 2026_Nov_recent_exploratory |      204 |      5.88 |       -13.435 |           0.038 |            2740.68 |               -112.56 |              192 |
| 20m_rejected_sweep_short     | 2025_train                  |     4847 |     12.05 |       -13.653 |           0.091 |           66175.2  |               -115.35 |             4263 |
| 20m_rejected_sweep_short     | 2026_H1_validation          |     2432 |      6.41 |       -12.564 |           0.044 |           30556.3  |               -113.85 |             2276 |
| 20m_rejected_sweep_short     | 2026_H2_seen_recheck        |     1710 |      3.45 |       -12.864 |           0.016 |           21996.9  |               -112.56 |             1651 |
| 20m_rejected_sweep_short     | 2026_Nov_recent_exploratory |      188 |      5.32 |       -11.053 |           0.028 |            2082.64 |                -90.69 |              178 |
| 5min_close_breakout_long     | 2025_train                  |     1915 |     14.05 |       -13.714 |           0.15  |           26262.4  |               -115.52 |             1646 |
| 5min_close_breakout_long     | 2026_H1_validation          |      848 |      9.43 |       -12.939 |           0.076 |           10971.9  |                -68    |              768 |
| 5min_close_breakout_long     | 2026_H2_seen_recheck        |      713 |      4.77 |       -12.896 |           0.051 |            9194.84 |                -91.94 |              679 |
| 5min_close_breakout_long     | 2026_Nov_recent_exploratory |       84 |      4.76 |       -12.966 |           0.099 |            1089.16 |                -30    |               80 |
| 5min_close_breakout_short    | 2025_train                  |     1867 |     15.21 |       -13.498 |           0.165 |           25200.8  |               -114.71 |             1583 |
| 5min_close_breakout_short    | 2026_H1_validation          |     1016 |     10.63 |       -12.991 |           0.089 |           13198.7  |               -112.12 |              908 |
| 5min_close_breakout_short    | 2026_H2_seen_recheck        |      691 |      4.78 |       -13.728 |           0.039 |            9486.38 |                -64.66 |              658 |
| 5min_close_breakout_short    | 2026_Nov_recent_exploratory |      106 |      6.6  |       -11.846 |           0.125 |            1255.64 |                -36.74 |               99 |
| 60m_rejected_sweep_long      | 2025_train                  |     1848 |     14.88 |       -14.466 |           0.106 |           26733.2  |               -115.58 |             1573 |
| 60m_rejected_sweep_long      | 2026_H1_validation          |      995 |      6.73 |       -13.413 |           0.037 |           13352.3  |               -112.86 |              928 |
| 60m_rejected_sweep_long      | 2026_H2_seen_recheck        |      759 |      3.82 |       -12.578 |           0.023 |            9551.07 |                -83.72 |              730 |
| 60m_rejected_sweep_long      | 2026_Nov_recent_exploratory |       76 |      5.26 |       -13.547 |           0.026 |            1039.84 |                -93.59 |               72 |
| 60m_rejected_sweep_short     | 2025_train                  |     1711 |     12.04 |       -13.876 |           0.099 |           23747.3  |               -115.35 |             1505 |
| 60m_rejected_sweep_short     | 2026_H1_validation          |      914 |      5.91 |       -13.041 |           0.037 |           11919.5  |               -113.85 |              860 |
| 60m_rejected_sweep_short     | 2026_H2_seen_recheck        |      739 |      5.55 |       -12.439 |           0.028 |            9192.62 |                -57.85 |              698 |
| 60m_rejected_sweep_short     | 2026_Nov_recent_exploratory |       58 |      8.62 |       -10.375 |           0.063 |             614.53 |                -90.69 |               53 |
| compression_break_long       | 2025_train                  |      395 |     12.15 |       -14.08  |           0.097 |            5561.71 |               -263.7  |              347 |
| compression_break_long       | 2026_H1_validation          |      196 |      3.57 |       -13.215 |           0.04  |            2590.17 |                -68.25 |              189 |
| compression_break_long       | 2026_H2_seen_recheck        |      220 |      3.18 |       -12.479 |           0.029 |            2745.48 |                -29.27 |              213 |
| compression_break_long       | 2026_Nov_recent_exploratory |       25 |      0    |       -17.452 |           0     |             436.31 |                -35.79 |               25 |
| compression_break_short      | 2025_train                  |      373 |      9.65 |       -14.549 |           0.068 |            5426.75 |                -83.98 |              337 |
| compression_break_short      | 2026_H1_validation          |      229 |      4.8  |       -12.861 |           0.044 |            2945.13 |                -50.53 |              218 |
| compression_break_short      | 2026_H2_seen_recheck        |      222 |      2.7  |       -13.856 |           0.008 |            3076.08 |                -44.11 |              216 |
| compression_break_short      | 2026_Nov_recent_exploratory |       33 |      3.03 |       -13.139 |           0.003 |             435.01 |                -27.72 |               32 |
| every_minute_long            | 2025_train                  |    17535 |     12.18 |       -13.681 |           0.1   |          239894    |               -263.7  |            15400 |
| every_minute_long            | 2026_H1_validation          |     8683 |      6.14 |       -12.798 |           0.048 |          111125    |               -113.81 |             8150 |
| every_minute_long            | 2026_H2_seen_recheck        |     5897 |      3.95 |       -12.524 |           0.025 |           73855.7  |               -112.91 |             5664 |
| every_minute_long            | 2026_Nov_recent_exploratory |      809 |      5.44 |       -13.019 |           0.035 |           10532.7  |               -112.56 |              765 |
| every_minute_short           | 2025_train                  |    17525 |     12.13 |       -13.589 |           0.106 |          238155    |               -115.54 |            15400 |
| every_minute_short           | 2026_H1_validation          |     8682 |      6.63 |       -12.459 |           0.051 |          108169    |               -113.85 |             8106 |
| every_minute_short           | 2026_H2_seen_recheck        |     5898 |      3.46 |       -12.752 |           0.022 |           75209.3  |               -113.01 |             5694 |
| every_minute_short           | 2026_Nov_recent_exploratory |      809 |      5.81 |       -11.946 |           0.053 |            9664.28 |                -85.78 |              762 |
| strong_burst_long            | 2025_train                  |     4147 |     13.02 |       -14.009 |           0.126 |           58095.7  |               -115.52 |             3607 |
| strong_burst_long            | 2026_H1_validation          |     2184 |      7.65 |       -12.972 |           0.067 |           28331.9  |               -113.25 |             2017 |
| strong_burst_long            | 2026_H2_seen_recheck        |     1612 |      4.84 |       -12.359 |           0.035 |           19923.2  |                -60.73 |             1534 |
| strong_burst_long            | 2026_Nov_recent_exploratory |      194 |      4.12 |       -14.667 |           0.041 |            2845.45 |                -98.8  |              186 |
| strong_burst_short           | 2025_train                  |     4154 |     13.26 |       -13.675 |           0.135 |           56805.5  |               -115.5  |             3603 |
| strong_burst_short           | 2026_H1_validation          |     2324 |      8.73 |       -12.372 |           0.076 |           28752.7  |                -81.42 |             2121 |
| strong_burst_short           | 2026_H2_seen_recheck        |     1628 |      4.55 |       -12.986 |           0.036 |           21141.7  |               -113    |             1554 |
| strong_burst_short           | 2026_Nov_recent_exploratory |      210 |      8.1  |       -10.941 |           0.099 |            2297.64 |                -46.42 |              193 |
| trend_pullback_reclaim_long  | 2025_train                  |     4890 |     11.39 |       -13.714 |           0.106 |           67060.1  |               -115.78 |             4333 |
| trend_pullback_reclaim_long  | 2026_H1_validation          |     2292 |      6.02 |       -12.922 |           0.048 |           29617.7  |               -112.68 |             2154 |
| trend_pullback_reclaim_long  | 2026_H2_seen_recheck        |     1698 |      4.59 |       -12.44  |           0.039 |           21122.9  |                -79.75 |             1620 |
| trend_pullback_reclaim_long  | 2026_Nov_recent_exploratory |      192 |      4.69 |       -13.425 |           0.049 |            2577.59 |                -56.86 |              183 |
| trend_pullback_reclaim_short | 2025_train                  |     4640 |     13.97 |       -13.54  |           0.139 |           62825.5  |               -115.26 |             3992 |
| trend_pullback_reclaim_short | 2026_H1_validation          |     2511 |      7.85 |       -12.421 |           0.07  |           31189    |               -112.14 |             2314 |
| trend_pullback_reclaim_short | 2026_H2_seen_recheck        |     1642 |      3.9  |       -13.057 |           0.028 |           21440.3  |                -75.36 |             1578 |
| trend_pullback_reclaim_short | 2026_Nov_recent_exploratory |      255 |      9.41 |       -11.729 |           0.089 |            2990.89 |                -54.91 |              231 |

## Rankings from 2025 training only (not evidence of future profitability)
| rule                         |   trades |   avg_net_pts |   win_pct |   losses_or_flat |
|:-----------------------------|---------:|--------------:|----------:|-----------------:|
| 15min_close_breakout_short   |      657 |       -13.283 |     16.59 |              548 |
| 5min_close_breakout_short    |     1867 |       -13.498 |     15.21 |             1583 |
| trend_pullback_reclaim_short |     4640 |       -13.54  |     13.97 |             3992 |
| every_minute_short           |    17525 |       -13.589 |     12.13 |            15400 |
| 20m_rejected_sweep_short     |     4847 |       -13.653 |     12.05 |             4263 |
| strong_burst_short           |     4154 |       -13.675 |     13.26 |             3603 |
| every_minute_long            |    17535 |       -13.681 |     12.18 |            15400 |
| 20m_accepted_breakout_short  |     5790 |       -13.693 |     13.28 |             5021 |
| trend_pullback_reclaim_long  |     4890 |       -13.714 |     11.39 |             4333 |
| 5min_close_breakout_long     |     1915 |       -13.714 |     14.05 |             1646 |
| 20m_accepted_breakout_long   |     5958 |       -13.769 |     11.97 |             5245 |
| 60m_rejected_sweep_short     |     1711 |       -13.876 |     12.04 |             1505 |
| 20m_rejected_sweep_long      |     4853 |       -13.897 |     12.73 |             4235 |
| 15min_close_breakout_long    |      650 |       -13.994 |     17.23 |              538 |
| strong_burst_long            |     4147 |       -14.009 |     13.02 |             3607 |
| compression_break_long       |      395 |       -14.08  |     12.15 |              347 |

## Reproducible audit artifacts
- every_candle_directional_labels.csv.gz (one entry time per long/short case)
- all_candle_conditional_rates.csv
- new_york_hour_profile.csv
- trade_ledger.csv.gz (one open trade at a time per independently measured setup)
- trade_summary.csv
- zero_loss_candidates.csv (may contain header only)
- quality.json (archive gaps, fees, exact sample counts)

## Safeguards / limitations
- No historical bid/ask quote, order-book depth or intraminute tick path
- Favorable target may be unfillable at modeled high/low
- Missing source minutes not fabricated; skip signals spanning gaps
- All four historical splits are used for exploratory research, not pristine forward testing
- Overlapping minute labels produce severely correlated observations
- Fee voucher credits are not counted as cash; historical Scalper Offer unknown
- Funding, market impact, liquidation, capital and margin not reconstructed
- No ability to guarantee a 200-point move without losses
- Only rule-based subset scanned; many possible rules not tested
- 200 BTC points represents quote-price move, not dollar account P&L

Conclusions must come from the actual table, not from choosing perfect historical candles.
