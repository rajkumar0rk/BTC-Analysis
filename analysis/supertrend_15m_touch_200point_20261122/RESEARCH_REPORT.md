# 15m Supertrend line-touch: how many touch entries reach +200 points first?

Delta Exchange India BTCUSD perpetual, archived 1m candles resampled to
15m; Supertrend(10,3); stop **only after completed 15m closing breach**.
Count +200 from executed midprice using 1m highs strictly **after**
entry minute, before the next 15m closing-stop execution.
Monthly inclusion by **IST entry month** January 2025 to October 2026;
November 2026 partial month excluded. No shorts, one entry per bullish ST cycle.

## Unfiltered and representative configurations
| volume_filter   | volatility_filter   |   trades |   reached_200_before_close_stop |   reached_200_pct |   reached_200_after_entry_slip |   estimated_net_pts |
|:----------------|:--------------------|---------:|--------------------------------:|------------------:|-------------------------------:|--------------------:|
| vol_off         | atr_off             |      782 |                             299 |             38.24 |                            296 |           -94266.2  |
| vol_ge_1p25     | atrpct_ge_0p40      |       73 |                              43 |             58.9  |                             43 |            -7296.34 |
| vol_ge_2p0      | atrpct_ge_0p40      |       44 |                              29 |             65.91 |                             29 |            -3811.14 |
| vol_le_0p8      | atrrel_ge_1p25      |       56 |                              21 |             37.5  |                             21 |            -7222.74 |

## Highest hit COUNTS (filters overlap; NEVER sum across configurations)
| volume_filter   | volatility_filter   |   trades |   reached_200_before_close_stop |   reached_200_pct |   reached_200_after_entry_slip |   estimated_net_pts |
|:----------------|:--------------------|---------:|--------------------------------:|------------------:|-------------------------------:|--------------------:|
| vol_off         | atr_off             |      782 |                             299 |             38.24 |                            296 |            -94266.2 |
| vol_off         | atrpct_ge_0p10      |      747 |                             298 |             39.89 |                            295 |            -89103.1 |
| vol_off         | atrpct_ge_0p20      |      550 |                             238 |             43.27 |                            235 |            -69412.6 |
| vol_ge_1p0      | atr_off             |      587 |                             230 |             39.18 |                            227 |            -74725   |
| vol_ge_1p0      | atrpct_ge_0p10      |      567 |                             229 |             40.39 |                            226 |            -72075.2 |
| vol_ge_1p25     | atr_off             |      499 |                             199 |             39.88 |                            196 |            -63326.7 |
| vol_ge_1p25     | atrpct_ge_0p10      |      483 |                             198 |             40.99 |                            195 |            -61192   |
| vol_ge_1p0      | atrpct_ge_0p20      |      413 |                             176 |             42.62 |                            173 |            -58798.2 |
| vol_ge_1p5      | atr_off             |      409 |                             171 |             41.81 |                            168 |            -50021.9 |
| vol_ge_1p5      | atrpct_ge_0p10      |      396 |                             169 |             42.68 |                            166 |            -48503.9 |
| vol_ge_1p25     | atrpct_ge_0p20      |      348 |                             148 |             42.53 |                            145 |            -50166   |
| vol_off         | atrpct_ge_0p30      |      288 |                             140 |             48.61 |                            139 |            -33955.7 |
| vol_ge_2p0      | atr_off             |      278 |                             130 |             46.76 |                            127 |            -32772.4 |
| vol_ge_2p0      | atrpct_ge_0p10      |      269 |                             127 |             47.21 |                            124 |            -32124.8 |
| vol_ge_1p5      | atrpct_ge_0p20      |      279 |                             125 |             44.8  |                            122 |            -39570.7 |

## Highest hit PERCENTAGES with at least 50 entries
| volume_filter   | volatility_filter   |   trades |   reached_200_before_close_stop |   reached_200_pct |   reached_200_after_entry_slip |   estimated_net_pts |
|:----------------|:--------------------|---------:|--------------------------------:|------------------:|-------------------------------:|--------------------:|
| vol_ge_1p5      | atrpct_ge_0p40      |       64 |                              38 |             59.38 |                             38 |            -6521.8  |
| vol_ge_1p25     | atrpct_ge_0p40      |       73 |                              43 |             58.9  |                             43 |            -7296.34 |
| vol_ge_2p0      | atrpct_ge_0p30      |      100 |                              58 |             58    |                             58 |           -10572.4  |
| vol_ge_1p0      | atrpct_ge_0p40      |       94 |                              53 |             56.38 |                             52 |           -10852.2  |
| vol_ge_1p0      | atrpct_ge_0p30      |      209 |                             110 |             52.63 |                            109 |           -24378.1  |
| vol_off         | atrpct_ge_0p40      |      134 |                              70 |             52.24 |                             69 |           -16114.5  |
| vol_ge_1p5      | atrpct_ge_0p30      |      146 |                              76 |             52.05 |                             76 |           -17062.5  |
| vol_ge_1p25     | atrpct_ge_0p30      |      173 |                              89 |             51.45 |                             89 |           -19780.8  |
| vol_ge_2p0      | atrpct_ge_0p20      |      193 |                              97 |             50.26 |                             94 |           -25551.4  |
| vol_ge_2p0      | atrrel_ge_1p25      |       65 |                              32 |             49.23 |                             31 |            -9563.2  |
| vol_off         | atrpct_ge_0p30      |      288 |                             140 |             48.61 |                            139 |           -33955.7  |
| vol_ge_2p0      | atrpct_ge_0p10      |      269 |                             127 |             47.21 |                            124 |           -32124.8  |
| vol_ge_2p0      | atr_off             |      278 |                             130 |             46.76 |                            127 |           -32772.4  |
| vol_ge_1p5      | atrpct_ge_0p20      |      279 |                             125 |             44.8  |                            122 |           -39570.7  |
| vol_off         | atrrel_ge_1p25      |      185 |                              81 |             43.78 |                             80 |           -26574.2  |

## Integrity and limitations
- All filters evaluated using the most recent completed 15m candle only.
- A 200-point hit is a gross PRICE EXCURSION, not a net $200 profit.
- Net illustration assumes target limit at entry-mid +200, 0.05% taker each
  side plus 18% GST, and 5 adverse points each side; funding excluded.
- The stricter column **after_entry_slip** requires high >= entry-mid +205.
- Same 1m entry candle's high is deliberately excluded (unknown event order).
- Historical price data lacks bid/ask spreads and limit order fill certainty.
- Later historical dates have already been used in research, not fresh OOS.
