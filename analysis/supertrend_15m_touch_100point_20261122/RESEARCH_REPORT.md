# BTCUSD 15m Supertrend: how many first-touch entries reach +100?

Delta India BTCUSD perpetual; 1m OHLC, 22 completed IST months Jan2025-Oct2026.
Gross price excursion **before 15m closing stop**; NO fixed 100-point hard SL.
One entry per bullish Supertrend(10,3) cycle.

## Unfiltered +100, +200, +500 and +1,000 comparison
|   target_pts | volume_filter   | volatility_filter   |   trades |   reached_before_close_stop |   pct_reached |   reached_after_entry_slippage |   not_reached |
|-------------:|:----------------|:--------------------|---------:|----------------------------:|--------------:|-------------------------------:|--------------:|
|          100 | vol_off         | atr_off             |      782 |                         430 |         54.99 |                            419 |           352 |
|          200 | vol_off         | atr_off             |      782 |                         299 |         38.24 |                            296 |           483 |
|          500 | vol_off         | atr_off             |      782 |                         171 |         21.87 |                            169 |           611 |
|         1000 | vol_off         | atr_off             |      782 |                          92 |         11.76 |                             92 |           690 |

## +100 with representative prior-closed-bar volume/ATR filters
|   target_pts | volume_filter   | volatility_filter   |   trades |   reached_before_close_stop |   pct_reached |   reached_after_entry_slippage |   not_reached |
|-------------:|:----------------|:--------------------|---------:|----------------------------:|--------------:|-------------------------------:|--------------:|
|          100 | vol_off         | atr_off             |      782 |                         430 |         54.99 |                            419 |           352 |
|          100 | vol_ge_1p25     | atrpct_ge_0p30      |      173 |                         120 |         69.36 |                            117 |            53 |
|          100 | vol_ge_1p5      | atrpct_ge_0p30      |      146 |                         104 |         71.23 |                            100 |            42 |
|          100 | vol_ge_1p5      | atrpct_ge_0p40      |       64 |                          49 |         76.56 |                             47 |            15 |
|          100 | vol_ge_2p0      | atrpct_ge_0p30      |      100 |                          76 |         76    |                             74 |            24 |
|          100 | vol_ge_2p0      | atrpct_ge_0p40      |       44 |                          36 |         81.82 |                             35 |             8 |

## 42 combinations at +100, ranked by hit rate (>=50 trades)
|   target_pts | volume_filter   | volatility_filter   |   trades |   reached_before_close_stop |   pct_reached |   reached_after_entry_slippage |   not_reached |
|-------------:|:----------------|:--------------------|---------:|----------------------------:|--------------:|-------------------------------:|--------------:|
|          100 | vol_ge_1p5      | atrpct_ge_0p40      |       64 |                          49 |         76.56 |                             47 |            15 |
|          100 | vol_ge_2p0      | atrpct_ge_0p30      |      100 |                          76 |         76    |                             74 |            24 |
|          100 | vol_ge_1p25     | atrpct_ge_0p40      |       73 |                          53 |         72.6  |                             52 |            20 |
|          100 | vol_ge_1p5      | atrpct_ge_0p30      |      146 |                         104 |         71.23 |                            100 |            42 |
|          100 | vol_ge_1p25     | atrpct_ge_0p30      |      173 |                         120 |         69.36 |                            117 |            53 |
|          100 | vol_ge_1p0      | atrpct_ge_0p40      |       94 |                          65 |         69.15 |                             63 |            29 |
|          100 | vol_ge_2p0      | atrpct_ge_0p20      |      193 |                         133 |         68.91 |                            130 |            60 |
|          100 | vol_ge_1p0      | atrpct_ge_0p30      |      209 |                         143 |         68.42 |                            139 |            66 |
|          100 | vol_off         | atrpct_ge_0p30      |      288 |                         188 |         65.28 |                            184 |           100 |
|          100 | vol_ge_1p5      | atrpct_ge_0p20      |      279 |                         181 |         64.87 |                            176 |            98 |
|          100 | vol_ge_2p0      | atrrel_ge_1p25      |       65 |                          42 |         64.62 |                             42 |            23 |
|          100 | vol_off         | atrpct_ge_0p40      |      134 |                          86 |         64.18 |                             85 |            48 |
|          100 | vol_ge_2p0      | atrpct_ge_0p10      |      269 |                         170 |         63.2  |                            167 |            99 |
|          100 | vol_ge_2p0      | atr_off             |      278 |                         174 |         62.59 |                            171 |           104 |
|          100 | vol_ge_1p25     | atrpct_ge_0p20      |      348 |                         212 |         60.92 |                            208 |           136 |
|          100 | vol_ge_1p5      | atrpct_ge_0p10      |      396 |                         241 |         60.86 |                            235 |           155 |
|          100 | vol_ge_1p0      | atrpct_ge_0p20      |      413 |                         251 |         60.77 |                            244 |           162 |
|          100 | vol_ge_1p5      | atrrel_ge_1p25      |       99 |                          60 |         60.61 |                             59 |            39 |
|          100 | vol_ge_1p0      | atrrel_ge_1p25      |      139 |                          84 |         60.43 |                             80 |            55 |
|          100 | vol_off         | atrpct_ge_0p20      |      550 |                         329 |         59.82 |                            322 |           221 |

## Reconciliation
- Unfiltered +200 = 299, +500 = 171, +1000 = 92 — all passed prior report parity.
- +100 hit count is a gross move; not net +100 profit.
- The separate 1:1 RR study reported 325 target exits from 782 entries
  with a 100-point **hard SL**. Hard-stop-first vs Supertrend-stop-only
  are different questions; don't compare or conflate counts.
- Excludes price highs in the entry minute, because OHLC ordering is unknown.
- Volume/volatility data is last fully closed 15m bar (no lookahead).
- 2025/2026 dates have already been researched; not new OOS.
