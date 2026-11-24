# Frozen X180 BTCUSD 2024 validation

Frozen from research/btc15m-dynamic-management-refine-20261124, rule X180; original risk rules and fees/slippage, no optimization on 2024.

## Data coverage
| month   |   expected |   observed |   missing | complete   |
|:--------|-----------:|-----------:|----------:|:-----------|
| 2023-12 |      44640 |        544 |     44096 | False      |
| 2024-01 |      44640 |       7514 |     37126 | False      |
| 2024-02 |      41760 |      40121 |      1639 | False      |
| 2024-03 |      44640 |      44635 |         5 | False      |
| 2024-04 |      43200 |      43200 |         0 | True       |
| 2024-05 |      44640 |      44640 |         0 | True       |
| 2024-06 |      43200 |      43196 |         4 | False      |
| 2024-07 |      44640 |      44639 |         1 | False      |
| 2024-08 |      44640 |      44640 |         0 | True       |
| 2024-09 |      43200 |      43200 |         0 | True       |
| 2024-10 |      44640 |      44640 |         0 | True       |
| 2024-11 |      43200 |      43200 |         0 | True       |
| 2024-12 |      44640 |      44640 |         0 | True       |

## Scored period: 2024-09 to 2024-12 (4/12 complete IST months)
Warmup: 2024-08; no trades during warmup. Full-year coverage: False.

Both intraminute paths, starting equity $1000. Fee 0.05% per side plus GST18%; slippage 0.02% per side. Funding and actual exchange fills not modeled.

|   profile | path_assumption   |   trades |   wins |   losses |   net_return_pct |   max_floating_drawdown_pct |   profitable_months |   fees_gst_usd |
|----------:|:------------------|---------:|-------:|---------:|-----------------:|----------------------------:|--------------------:|---------------:|
|        80 | O-H-L-C           |       14 |      2 |       12 |          -8.3596 |                       9.705 |                   0 |         4.8856 |
|        80 | O-L-H-C           |       14 |      2 |       12 |          -8.3596 |                       9.705 |                   0 |         4.8856 |
|       100 | O-H-L-C           |       14 |      2 |       12 |         -10.2609 |                      11.9   |                   0 |         5.9871 |
|       100 | O-L-H-C           |       14 |      2 |       12 |         -10.2609 |                      11.9   |                   0 |         5.9871 |

## Monthly returns
| month_ist   |   ('80', 'O-H-L-C') |   ('80', 'O-L-H-C') |   ('100', 'O-H-L-C') |   ('100', 'O-L-H-C') |
|:------------|--------------------:|--------------------:|---------------------:|---------------------:|
| 2024-09     |          -6.4275    |          -6.4275    |           -7.98643   |           -7.98643   |
| 2024-10     |          -2.00343   |          -2.00343   |           -2.40082   |           -2.40082   |
| 2024-11     |          -0.0626689 |          -0.0626689 |           -0.0728224 |           -0.0728224 |
| 2024-12     |           0         |           0         |            0         |            0         |

