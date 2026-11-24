# BTCUSD 15M RSI switch — 20 to 21 monthly wins

113 rules/profile, 452 actual path simulations.
Jan2025–Oct2026, 22 IST months, repeated in-sample selection. No future month/date labels used.
Baseline 20-month 80%: +199.8369% / 9.846% DD; 100%: +294.9555% /12.022% DD.
Strict floors from preceding 19-month models: 80% +203.0718% /9.751%; 100% +297.7751% /12.090%.
Identical 1m OHLC path replay, taker fee 0.05% per side +18% GST, price slippage 0.02% per side. No funding, liquidation, live spread or depth.
Separate profiles, exposure never above 80% or 100% respectively.

## 80% exposure
Strict 20+ candidates: 0; strict 21+: 0; 21+ vs original floors: 0.

### Strict 20+ candidates
None.

### 21+ against original locked floors
None.

### Highest monthly consistency regardless of constraints
|   profile | rule   | kind    |   param |   tiers |   sl |   tp | lock                |     net |     dd |   winning_months |   losing_months |   worst_month |   trades |   preserved20 |   positive_month_drop | strict_floor   | original_floor   | qual20   | qual21   |
|----------:|:-------|:--------|--------:|--------:|-----:|-----:|:--------------------|--------:|-------:|-----------------:|----------------:|--------------:|---------:|--------------:|----------------------:|:---------------|:-----------------|:---------|:---------|
|        80 | A022   | losses  |       2 |     nan |  3   |    9 | LATE:4.0:2.0:1:0.25 | 270.515 | 13.075 |               21 |               1 |      -5.19106 |       73 |            17 |           2.66305     | False          | False            | False    | False    |
|        80 | A036   | losses  |       3 |     nan |  3   |    9 | LATE:4.0:2.0:1:0.25 | 260.217 | 13.075 |               21 |               1 |      -5.19106 |       74 |            18 |           0.630051    | False          | False            | False    | False    |
|        80 | A021   | losses  |       2 |     nan |  3   |    9 | LATE:4.0:1.0:1:0.25 | 257.879 | 13.283 |               21 |               1 |      -6.42806 |       72 |            18 |           0.974762    | False          | False            | False    | False    |
|        80 | A035   | losses  |       3 |     nan |  3   |    9 | LATE:4.0:1.0:1:0.25 | 257.879 | 13.283 |               21 |               1 |      -6.42806 |       72 |            18 |           0.974762    | False          | False            | False    | False    |
|        80 | A016   | losses  |       2 |     nan |  3   |   10 | LATE:8:2:1:0.25     | 200.313 |  9.846 |               20 |               2 |      -5.56468 |       70 |            20 |           6.57252e-14 | False          | True             | False    | False    |
|        80 | A030   | losses  |       3 |     nan |  3   |   10 | LATE:8:2:1:0.25     | 200.313 |  9.846 |               20 |               2 |      -5.56468 |       70 |            20 |           6.57252e-14 | False          | True             | False    | False    |
|        80 | A028   | losses  |       2 |     nan |  3   |    9 | LATE:7.0:2.0:1:0.25 | 200.046 |  9.846 |               20 |               2 |      -5.56468 |       70 |            20 |           2.13163e-14 | False          | True             | False    | False    |
|        80 | A000   | none    |       0 |     nan |  3   |    9 | LATE:8:2:1:0.25     | 199.837 |  9.846 |               20 |               2 |      -5.56468 |       70 |            20 |           0           | False          | True             | False    | False    |
|        80 | A042   | losses  |       3 |     nan |  3   |    9 | LATE:7.0:2.0:1:0.25 | 199.837 |  9.846 |               20 |               2 |      -5.56468 |       70 |            20 |           0           | False          | True             | False    | False    |
|        80 | A112   | monthdd |       3 |     nan |  3   |    9 | LATE:7.0:2.0:1:0.25 | 199.837 |  9.846 |               20 |               2 |      -5.56468 |       70 |            20 |           0           | False          | True             | False    | False    |
|        80 | A029   | losses  |       3 |     nan |  3   |    8 | LATE:8:2:1:0.25     | 199.361 |  9.846 |               20 |               2 |      -5.56468 |       70 |            19 |           0.0807125   | False          | True             | False    | False    |
|        80 | A087   | monthdd |       2 |     nan |  3.5 |    9 | LATE:8:2:1:0.25     | 199.051 |  9.846 |               20 |               2 |      -5.81228 |       70 |            20 |           2.22045e-14 | False          | True             | False    | False    |
|        80 | A101   | monthdd |       3 |     nan |  3.5 |    9 | LATE:8:2:1:0.25     | 199.051 |  9.846 |               20 |               2 |      -5.81228 |       70 |            20 |           2.22045e-14 | False          | True             | False    | False    |
|        80 | A032   | losses  |       3 |     nan |  3.5 |   10 | LATE:8:2:1:0.25     | 197.902 |  9.846 |               20 |               2 |      -5.79291 |       70 |            16 |           0.602085    | False          | True             | False    | False    |
|        80 | A031   | losses  |       3 |     nan |  3.5 |    9 | LATE:8:2:1:0.25     | 197.43  |  9.846 |               20 |               2 |      -5.79291 |       70 |            16 |           0.602085    | False          | True             | False    | False    |

### Preserving all 20 existing positive months plus strict floors
| profile   | rule   | kind   | param   | tiers   | sl   | tp   | lock   | net   | dd   | winning_months   | losing_months   | worst_month   | trades   | preserved20   | positive_month_drop   | strict_floor   | original_floor   | qual20   | qual21   |
|-----------|--------|--------|---------|---------|------|------|--------|-------|------|------------------|-----------------|---------------|----------|---------------|-----------------------|----------------|------------------|----------|----------|

## 100% exposure
Strict 20+ candidates: 0; strict 21+: 0; 21+ vs original floors: 0.

### Strict 20+ candidates
None.

### 21+ against original locked floors
None.

### Highest monthly consistency regardless of constraints
|   profile | rule   | kind    |   param |   tiers |   sl |   tp | lock                |     net |     dd |   winning_months |   losing_months |   worst_month |   trades |   preserved20 |   positive_month_drop | strict_floor   | original_floor   | qual20   | qual21   |
|----------:|:-------|:--------|--------:|--------:|-----:|-----:|:--------------------|--------:|-------:|-----------------:|----------------:|--------------:|---------:|--------------:|----------------------:|:---------------|:-----------------|:---------|:---------|
|       100 | A022   | losses  |    2    |     nan |  3   |    9 | LATE:4.0:2.0:1:0.25 | 407.915 | 16.044 |               21 |               1 |      -6.44235 |       73 |            17 |           3.27116     | False          | False            | False    | False    |
|       100 | A036   | losses  |    3    |     nan |  3   |    9 | LATE:4.0:2.0:1:0.25 | 390.524 | 16.044 |               21 |               1 |      -6.44235 |       74 |            18 |           0.666797    | False          | False            | False    | False    |
|       100 | A021   | losses  |    2    |     nan |  3   |    9 | LATE:4.0:1.0:1:0.25 | 384.674 | 16.253 |               21 |               1 |      -7.71339 |       72 |            18 |           1.67078     | False          | False            | False    | False    |
|       100 | A035   | losses  |    3    |     nan |  3   |    9 | LATE:4.0:1.0:1:0.25 | 384.674 | 16.253 |               21 |               1 |      -7.71339 |       72 |            18 |           1.67078     | False          | False            | False    | False    |
|       100 | A016   | losses  |    2    |     nan |  3   |   10 | LATE:8:2:1:0.25     | 295.738 | 12.022 |               20 |               2 |      -6.336   |       70 |            20 |           1.56319e-13 | False          | True             | False    | False    |
|       100 | A030   | losses  |    3    |     nan |  3   |   10 | LATE:8:2:1:0.25     | 295.738 | 12.022 |               20 |               2 |      -6.336   |       70 |            20 |           1.56319e-13 | False          | True             | False    | False    |
|       100 | A028   | losses  |    2    |     nan |  3   |    9 | LATE:7.0:2.0:1:0.25 | 295.25  | 12.022 |               20 |               2 |      -6.336   |       70 |            20 |           2.22045e-14 | False          | True             | False    | False    |
|       100 | A000   | none    |    0    |     nan |  3   |    9 | LATE:8:2:1:0.25     | 294.955 | 12.022 |               20 |               2 |      -6.336   |       70 |            20 |           0           | False          | True             | False    | False    |
|       100 | A042   | losses  |    3    |     nan |  3   |    9 | LATE:7.0:2.0:1:0.25 | 294.955 | 12.022 |               20 |               2 |      -6.336   |       70 |            20 |           0           | False          | True             | False    | False    |
|       100 | A029   | losses  |    3    |     nan |  3   |    8 | LATE:8:2:1:0.25     | 294.173 | 12.022 |               20 |               2 |      -6.336   |       70 |            19 |           0.101201    | False          | True             | False    | False    |
|       100 | A101   | monthdd |    3    |     nan |  3.5 |    9 | LATE:8:2:1:0.25     | 293.86  | 12.022 |               20 |               2 |      -6.59586 |       70 |            20 |           6.83897e-14 | False          | True             | False    | False    |
|       100 | A032   | losses  |    3    |     nan |  3.5 |   10 | LATE:8:2:1:0.25     | 292.363 | 12.022 |               20 |               2 |      -6.57186 |       70 |            16 |           0.657836    | False          | True             | False    | False    |
|       100 | A087   | monthdd |    2    |     nan |  3.5 |    9 | LATE:8:2:1:0.25     | 291.828 | 12.022 |               20 |               2 |      -6.59586 |       70 |            19 |           0.548858    | False          | True             | False    | False    |
|       100 | A031   | losses  |    3    |     nan |  3.5 |    9 | LATE:8:2:1:0.25     | 291.586 | 12.022 |               20 |               2 |      -6.57186 |       70 |            16 |           0.657836    | False          | True             | False    | False    |
|       100 | A045   | monthdd |    0.25 |     nan |  3.5 |    9 | LATE:8:2:1:0.25     | 289.807 | 12.022 |               20 |               2 |      -7.07762 |       70 |            19 |           0.548858    | False          | True             | False    | False    |

### Preserving all 20 existing positive months plus strict floors
| profile   | rule   | kind   | param   | tiers   | sl   | tp   | lock   | net   | dd   | winning_months   | losing_months   | worst_month   | trades   | preserved20   | positive_month_drop   | strict_floor   | original_floor   | qual20   | qual21   |
|-----------|--------|--------|---------|---------|------|------|--------|-------|------|------------------|-----------------|---------------|----------|---------------|-----------------------|----------------|------------------|----------|----------|

