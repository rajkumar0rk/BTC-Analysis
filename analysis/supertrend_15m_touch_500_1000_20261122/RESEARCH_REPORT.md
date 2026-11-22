# BTCUSD 15m Supertrend first-touch: 500 and 1,000 BTC-point first passage

Delta India BTCUSD perpetual, Jan 2025–Oct 2026 complete IST months.
Same 15m close stop, one long per bullish cycle, 1m execution.
The same-entry minute is excluded because OHLC cannot resolve ordering.

## Unfiltered (all eligible touches)
- 782 trades.
- +500 reached BEFORE closing stop: **171** (21.87%).
- +1,000 reached BEFORE closing stop: **92** (11.76%).
- +1,000 counts are a subset of +500; do not add them.

## Representative volume/volatility combinations
| volume_filter   | volatility_filter   |   trades |   hit_500 |   rate_500_pct |   hit_1000 |   rate_1000_pct |
|:----------------|:--------------------|---------:|----------:|---------------:|-----------:|----------------:|
| vol_off         | atr_off             |      782 |       171 |          21.87 |         92 |           11.76 |
| vol_ge_1p25     | atrpct_ge_0p30      |      173 |        48 |          27.75 |         30 |           17.34 |
| vol_ge_1p5      | atrpct_ge_0p30      |      146 |        41 |          28.08 |         27 |           18.49 |
| vol_ge_1p5      | atrpct_ge_0p40      |       64 |        20 |          31.25 |         12 |           18.75 |
| vol_ge_2p0      | atrpct_ge_0p30      |      100 |        32 |          32    |         21 |           21    |
| vol_ge_2p0      | atrpct_ge_0p40      |       44 |        16 |          36.36 |         10 |           22.73 |

## Highest +500 hit rates (at least 50 trades)
| volume_filter   | volatility_filter   |   trades |   hit_500 |   rate_500_pct |   hit_1000 |   rate_1000_pct |
|:----------------|:--------------------|---------:|----------:|---------------:|-----------:|----------------:|
| vol_off         | atrpct_ge_0p40      |      134 |        43 |          32.09 |         22 |           16.42 |
| vol_ge_2p0      | atrpct_ge_0p30      |      100 |        32 |          32    |         21 |           21    |
| vol_ge_1p0      | atrpct_ge_0p40      |       94 |        30 |          31.91 |         17 |           18.09 |
| vol_ge_1p25     | atrpct_ge_0p40      |       73 |        23 |          31.51 |         13 |           17.81 |
| vol_ge_1p5      | atrpct_ge_0p40      |       64 |        20 |          31.25 |         12 |           18.75 |
| vol_ge_1p0      | atrpct_ge_0p30      |      209 |        63 |          30.14 |         39 |           18.66 |
| vol_ge_1p5      | atrpct_ge_0p30      |      146 |        41 |          28.08 |         27 |           18.49 |
| vol_off         | atrpct_ge_0p30      |      288 |        80 |          27.78 |         45 |           15.62 |
| vol_ge_1p25     | atrpct_ge_0p30      |      173 |        48 |          27.75 |         30 |           17.34 |
| vol_ge_2p0      | atrpct_ge_0p20      |      193 |        49 |          25.39 |         29 |           15.03 |
| vol_ge_2p0      | atrpct_ge_0p10      |      269 |        67 |          24.91 |         35 |           13.01 |
| vol_ge_2p0      | atr_off             |      278 |        69 |          24.82 |         35 |           12.59 |

## Highest +1,000 hit rates (at least 50 trades)
| volume_filter   | volatility_filter   |   trades |   hit_500 |   rate_500_pct |   hit_1000 |   rate_1000_pct |
|:----------------|:--------------------|---------:|----------:|---------------:|-----------:|----------------:|
| vol_ge_2p0      | atrpct_ge_0p30      |      100 |        32 |          32    |         21 |           21    |
| vol_ge_1p5      | atrpct_ge_0p40      |       64 |        20 |          31.25 |         12 |           18.75 |
| vol_ge_1p0      | atrpct_ge_0p30      |      209 |        63 |          30.14 |         39 |           18.66 |
| vol_ge_1p5      | atrpct_ge_0p30      |      146 |        41 |          28.08 |         27 |           18.49 |
| vol_ge_1p0      | atrpct_ge_0p40      |       94 |        30 |          31.91 |         17 |           18.09 |
| vol_ge_1p25     | atrpct_ge_0p40      |       73 |        23 |          31.51 |         13 |           17.81 |
| vol_ge_1p25     | atrpct_ge_0p30      |      173 |        48 |          27.75 |         30 |           17.34 |
| vol_off         | atrpct_ge_0p40      |      134 |        43 |          32.09 |         22 |           16.42 |
| vol_off         | atrpct_ge_0p30      |      288 |        80 |          27.78 |         45 |           15.62 |
| vol_ge_2p0      | atrpct_ge_0p20      |      193 |        49 |          25.39 |         29 |           15.03 |
| vol_ge_1p0      | atrpct_ge_0p20      |      413 |       100 |          24.21 |         62 |           15.01 |
| vol_ge_1p5      | atrpct_ge_0p20      |      279 |        66 |          23.66 |         41 |           14.7  |

## Definitions
- Volume factor: last closed 15m volume / mean of preceding 20 fully closed 15m volumes.
- ATR percentage: 15m Wilder ATR14 / last closed price × 100.
- All support lines and filters known before the candidate 15m candle.
- +500/1,000 are **gross price movement**, NOT 500/1000 net profit.
- Individual results and estimated net target-TP replay in CSV; costs assumed.
- The 42 variants overlap, so summed hit counts are meaningless.
- All previously researched months; not an untouched out-of-sample test.
