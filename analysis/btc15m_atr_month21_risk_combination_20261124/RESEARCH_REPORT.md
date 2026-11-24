# BTCUSD 15M RSI switch — 20 to 21 monthly wins

107 rules/profile, 428 actual path simulations.
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
|   profile | rule   | kind   |   param | tiers                    |   sl |   tp | lock            |     net |     dd |   winning_months |   losing_months |   worst_month |   trades |   preserved20 |   positive_month_drop | strict_floor   | original_floor   | qual20   | qual21   |
|----------:|:-------|:-------|--------:|:-------------------------|-----:|-----:|:----------------|--------:|-------:|-----------------:|----------------:|--------------:|---------:|--------------:|----------------------:|:---------------|:-----------------|:---------|:---------|
|        80 | A102   | losses |       2 | (0.6, 0.1, 0.1, 0.1)     |    3 |    9 | LATE:4:1:1:0.25 | 221.665 | 11.444 |               21 |               1 |      -4.43527 |       72 |            12 |              12.739   | False          | False            | False    | False    |
|        80 | A103   | losses |       2 | (0.6, 0.1, 0.1, 0.05)    |    3 |    9 | LATE:4:1:1:0.25 | 221.449 | 11.444 |               21 |               1 |      -4.43527 |       72 |            12 |              12.7561  | False          | False            | False    | False    |
|        80 | A104   | losses |       2 | (0.6, 0.1, 0.1, 0.025)   |    3 |    9 | LATE:4:1:1:0.25 | 221.341 | 11.444 |               21 |               1 |      -4.43527 |       72 |            12 |              12.7646  | False          | False            | False    | False    |
|        80 | A067   | losses |       2 | (0.8, 0.1, 0.1, 0.1)     |    3 |    9 | LATE:4:1:1:0.25 | 244.389 | 12.107 |               21 |               1 |      -4.92279 |       72 |            12 |               6.01635 | False          | False            | False    | False    |
|        80 | A068   | losses |       2 | (0.8, 0.1, 0.1, 0.05)    |    3 |    9 | LATE:4:1:1:0.25 | 244.157 | 12.107 |               21 |               1 |      -4.92279 |       72 |            11 |               6.00711 | False          | False            | False    | False    |
|        80 | A069   | losses |       2 | (0.8, 0.1, 0.1, 0.025)   |    3 |    9 | LATE:4:1:1:0.25 | 244.041 | 12.107 |               21 |               1 |      -4.92279 |       72 |            11 |               6.01612 | False          | False            | False    | False    |
|        80 | A070   | losses |       2 | (0.8, 0.1, 0.05, 0.05)   |    3 |    9 | LATE:4:1:1:0.25 | 243.059 | 12.154 |               21 |               1 |      -4.81547 |       72 |            12 |               6.14964 | False          | False            | False    | False    |
|        80 | A071   | losses |       2 | (0.8, 0.1, 0.05, 0.025)  |    3 |    9 | LATE:4:1:1:0.25 | 242.944 | 12.154 |               21 |               1 |      -4.81547 |       72 |            12 |               6.1128  | False          | False            | False    | False    |
|        80 | A059   | losses |       2 | (0.8, 0.15, 0.15, 0.1)   |    3 |    9 | LATE:4:1:1:0.25 | 242.704 | 12.17  |               21 |               1 |      -5.14948 |       72 |            11 |               6.11092 | False          | False            | False    | False    |
|        80 | A060   | losses |       2 | (0.8, 0.15, 0.15, 0.05)  |    3 |    9 | LATE:4:1:1:0.25 | 242.473 | 12.17  |               21 |               1 |      -5.14948 |       72 |            11 |               6.12883 | False          | False            | False    | False    |
|        80 | A061   | losses |       2 | (0.8, 0.15, 0.15, 0.025) |    3 |    9 | LATE:4:1:1:0.25 | 242.358 | 12.17  |               21 |               1 |      -5.14948 |       72 |            11 |               6.13773 | False          | False            | False    | False    |
|        80 | A062   | losses |       2 | (0.8, 0.15, 0.1, 0.1)    |    3 |    9 | LATE:4:1:1:0.25 | 241.616 | 12.217 |               21 |               1 |      -5.04252 |       72 |            11 |               6.18966 | False          | False            | False    | False    |
|        80 | A063   | losses |       2 | (0.8, 0.15, 0.1, 0.05)   |    3 |    9 | LATE:4:1:1:0.25 | 241.387 | 12.217 |               21 |               1 |      -5.04252 |       72 |            11 |               6.20769 | False          | False            | False    | False    |
|        80 | A064   | losses |       2 | (0.8, 0.15, 0.1, 0.025)  |    3 |    9 | LATE:4:1:1:0.25 | 241.272 | 12.217 |               21 |               1 |      -5.04252 |       72 |            11 |               6.21664 | False          | False            | False    | False    |
|        80 | A065   | losses |       2 | (0.8, 0.15, 0.05, 0.05)  |    3 |    9 | LATE:4:1:1:0.25 | 240.298 | 12.264 |               21 |               1 |      -4.93534 |       72 |            11 |               6.28654 | False          | False            | False    | False    |

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
|   profile | rule   | kind   |   param | tiers                    |   sl |   tp | lock            |     net |     dd |   winning_months |   losing_months |   worst_month |   trades |   preserved20 |   positive_month_drop | strict_floor   | original_floor   | qual20   | qual21   |
|----------:|:-------|:-------|--------:|:-------------------------|-----:|-----:|:----------------|--------:|-------:|-----------------:|----------------:|--------------:|---------:|--------------:|----------------------:|:---------------|:-----------------|:---------|:---------|
|       100 | A067   | losses |       2 | (0.8, 0.1, 0.1, 0.1)     |    3 |    9 | LATE:4:1:1:0.25 | 360.331 | 14.903 |               21 |               1 |      -6.13087 |       72 |            11 |               7.53926 | False          | False            | False    | False    |
|       100 | A068   | losses |       2 | (0.8, 0.1, 0.1, 0.05)    |    3 |    9 | LATE:4:1:1:0.25 | 359.944 | 14.903 |               21 |               1 |      -6.13087 |       72 |            11 |               7.56229 | False          | False            | False    | False    |
|       100 | A069   | losses |       2 | (0.8, 0.1, 0.1, 0.025)   |    3 |    9 | LATE:4:1:1:0.25 | 359.75  | 14.903 |               21 |               1 |      -6.13087 |       72 |            11 |               7.57371 | False          | False            | False    | False    |
|       100 | A070   | losses |       2 | (0.8, 0.1, 0.05, 0.05)   |    3 |    9 | LATE:4:1:1:0.25 | 358.114 | 14.96  |               21 |               1 |      -5.99846 |       72 |            11 |               7.66327 | False          | False            | False    | False    |
|       100 | A071   | losses |       2 | (0.8, 0.1, 0.05, 0.025)  |    3 |    9 | LATE:4:1:1:0.25 | 357.921 | 14.96  |               21 |               1 |      -5.99846 |       72 |            11 |               7.67478 | False          | False            | False    | False    |
|       100 | A059   | losses |       2 | (0.8, 0.15, 0.15, 0.1)   |    3 |    9 | LATE:4:1:1:0.25 | 357.507 | 14.98  |               21 |               1 |      -6.41058 |       72 |            10 |               7.86424 | False          | False            | False    | False    |
|       100 | A060   | losses |       2 | (0.8, 0.15, 0.15, 0.05)  |    3 |    9 | LATE:4:1:1:0.25 | 357.123 | 14.98  |               21 |               1 |      -6.41058 |       72 |            10 |               7.8869  | False          | False            | False    | False    |
|       100 | A061   | losses |       2 | (0.8, 0.15, 0.15, 0.025) |    3 |    9 | LATE:4:1:1:0.25 | 356.93  | 14.98  |               21 |               1 |      -6.41058 |       72 |            10 |               7.89814 | False          | False            | False    | False    |
|       100 | A062   | losses |       2 | (0.8, 0.15, 0.1, 0.1)    |    3 |    9 | LATE:4:1:1:0.25 | 355.699 | 15.037 |               21 |               1 |      -6.27873 |       72 |            10 |               7.92731 | False          | False            | False    | False    |
|       100 | A063   | losses |       2 | (0.8, 0.15, 0.1, 0.05)   |    3 |    9 | LATE:4:1:1:0.25 | 355.316 | 15.037 |               21 |               1 |      -6.27873 |       72 |            10 |               7.95016 | False          | False            | False    | False    |
|       100 | A064   | losses |       2 | (0.8, 0.15, 0.1, 0.025)  |    3 |    9 | LATE:4:1:1:0.25 | 355.124 | 15.037 |               21 |               1 |      -6.27873 |       72 |            10 |               7.96149 | False          | False            | False    | False    |
|       100 | A065   | losses |       2 | (0.8, 0.15, 0.05, 0.05)  |    3 |    9 | LATE:4:1:1:0.25 | 353.505 | 15.093 |               21 |               1 |      -6.14652 |       72 |            10 |               8.01332 | False          | False            | False    | False    |
|       100 | A066   | losses |       2 | (0.8, 0.15, 0.05, 0.025) |    3 |    9 | LATE:4:1:1:0.25 | 353.314 | 15.093 |               21 |               1 |      -6.14652 |       72 |            10 |               8.02474 | False          | False            | False    | False    |
|       100 | A048   | losses |       2 | (0.8, 0.25, 0.25, 0.1)   |    3 |    9 | LATE:4:1:1:0.25 | 351.852 | 15.135 |               21 |               1 |      -6.96773 |       72 |            11 |               9.03926 | False          | False            | False    | False    |
|       100 | A049   | losses |       2 | (0.8, 0.25, 0.25, 0.05)  |    3 |    9 | LATE:4:1:1:0.25 | 351.472 | 15.135 |               21 |               1 |      -6.96773 |       72 |            11 |               9.0612  | False          | False            | False    | False    |

### Preserving all 20 existing positive months plus strict floors
| profile   | rule   | kind   | param   | tiers   | sl   | tp   | lock   | net   | dd   | winning_months   | losing_months   | worst_month   | trades   | preserved20   | positive_month_drop   | strict_floor   | original_floor   | qual20   | qual21   |
|-----------|--------|--------|---------|---------|------|------|--------|-------|------|------------------|-----------------|---------------|----------|---------------|-----------------------|----------------|------------------|----------|----------|

