# ETHUSD EMA20/Supertrend 1h — screenshot settings (27m Scalper Offer model)

Source: 963,360 SHA256-verified Delta India ETHUSD one-minute candles; 16,056 1h bars, 22 UTC months.
Main test: ATR10 Supertrend3, EMA20 pullback, ATR14x2 stop, original 100/50 ETH price-point trailing, master entry filter Off.
ETH normalized sensitivity: 0.125% price activation; 0.0625% price trailing distance, rounded to 0.05.
Size: 1 ETHUSD lot = 0.01 ETH; 0.05% taker entry and exit, 18% GST, 27m offer modeled, funding=0, slippage=0 main.

| Configuration / fee model | Trades | Net USD | Win rate | Profit factor | Positive months | Offer-eligible modeled |
|---|---:|---:|---:|---:|---:|---:|
| Original fixed ETH 100/50; 27min_conservative_zero_slippage | 504 | -6.81 | 34.72% | 0.9578 | 8/22 | 0 |
| Original fixed ETH 100/50; 27min_optimistic_fee_waiver_upper_bound | 504 | -6.68 | 34.72% | 0.9586 | 8/22 | 9 |
| Original fixed ETH 100/50; 27min_conservative_plus_0p5_point_slippage_per_fill | 504 | -11.85 | 34.33% | 0.9281 | 7/22 | 0 |
| Original fixed ETH 100/50; hypothetical_unlimited_exit_fee_waiver | 504 | +1.47 | 35.12% | 1.0094 | 9/22 | 504 |
| ETH percentage-scaled comparison; 27min_conservative_zero_slippage | 1571 | +115.43 | 79.31% | 3.1773 | 22/22 | 0 |
| ETH percentage-scaled comparison; 27min_optimistic_fee_waiver_upper_bound | 1571 | +134.28 | 89.56% | 3.6037 | 22/22 | 1176 |
| ETH percentage-scaled comparison; 27min_conservative_plus_0p5_point_slippage_per_fill | 1571 | +99.72 | 72.18% | 2.7544 | 22/22 | 0 |
| ETH percentage-scaled comparison; hypothetical_unlimited_exit_fee_waiver | 1571 | +140.47 | 92.81% | 3.8302 | 22/22 | 1571 |

## 22-month primary fixed 100/50 (27-minute conservative)

| month_utc   |   trades |   net_wins |   net_losses |   gross_points |   net_points |   net_usd |   fees_usd |   gst_usd |   profit_factor |
|:------------|---------:|-----------:|-------------:|---------------:|-------------:|----------:|-----------:|----------:|----------------:|
| 2025-01     |       29 |         12 |           17 |         415.5  |     302.099  |    3.021  |     0.961  |    0.173  |          1.2809 |
| 2025-02     |       25 |         10 |           15 |          23    |     -56.354  |   -0.5635 |     0.6725 |    0.121  |          0.9302 |
| 2025-03     |       24 |          5 |           19 |        -142.2  |    -201.278  |   -2.0128 |     0.5007 |    0.0901 |          0.7874 |
| 2025-04     |       27 |          1 |           26 |        -860.4  |    -913.987  |   -9.1399 |     0.4541 |    0.0817 |          0.1745 |
| 2025-05     |       23 |          8 |           15 |        -334.3  |    -399.713  |   -3.9971 |     0.5543 |    0.0998 |          0.4994 |
| 2025-06     |       20 |          6 |           14 |         311.95 |     252.543  |    2.5254 |     0.5034 |    0.0906 |          1.4639 |
| 2025-07     |       26 |         12 |           14 |         202.85 |     101.454  |    1.0145 |     0.8593 |    0.1547 |          1.1129 |
| 2025-08     |       30 |         16 |           14 |         851.4  |     697.656  |    6.9766 |     1.3029 |    0.2345 |          1.5434 |
| 2025-09     |       24 |         11 |           13 |         334.55 |     211.215  |    2.1122 |     1.0452 |    0.1881 |          1.2554 |
| 2025-10     |       29 |         17 |           12 |        1007.2  |     866.687  |    8.6669 |     1.1908 |    0.2143 |          1.8949 |
| 2025-11     |       24 |          8 |           16 |        -450.1  |    -540.935  |   -5.4094 |     0.7698 |    0.1386 |          0.5627 |
| 2025-12     |       23 |          7 |           16 |          76.3  |      -6.2687 |   -0.0627 |     0.6997 |    0.126  |          0.9911 |
| 2026-01     |       24 |          9 |           15 |         -48.35 |    -135.806  |   -1.3581 |     0.7412 |    0.1334 |          0.8058 |
| 2026-02     |       24 |          8 |           16 |        -154.15 |    -211.614  |   -2.1161 |     0.487  |    0.0877 |          0.7576 |
| 2026-03     |       21 |          7 |           14 |        -117.55 |    -168.742  |   -1.6874 |     0.4338 |    0.0781 |          0.7549 |
| 2026-04     |       20 |          5 |           15 |        -141.75 |    -195.156  |   -1.9516 |     0.4526 |    0.0815 |          0.6244 |
| 2026-05     |       18 |          7 |           11 |          -0.25 |     -47.1816 |   -0.4718 |     0.3977 |    0.0716 |          0.8535 |
| 2026-06     |       16 |          8 |            8 |         221.8  |     189.354  |    1.8935 |     0.275  |    0.0495 |          1.7805 |
| 2026-07     |       20 |          5 |           15 |         -39.8  |     -82.7029 |   -0.827  |     0.3636 |    0.0654 |          0.7582 |
| 2026-08     |       16 |          4 |           12 |          45.95 |       6.1177 |    0.0612 |     0.3376 |    0.0608 |          1.0209 |
| 2026-09     |       21 |          4 |           17 |         -43.8  |    -107.52   |   -1.0752 |     0.54   |    0.0972 |          0.7891 |
| 2026-10     |       20 |          5 |           15 |        -183.05 |    -241.067  |   -2.4107 |     0.4917 |    0.0885 |          0.4711 |

## 22-month ETH percentage-scaled sensitivity (27-minute conservative)

| month_utc   |   trades |   net_wins |   net_losses |   gross_points |   net_points |   net_usd |   fees_usd |   gst_usd |   profit_factor |
|:------------|---------:|-----------:|-------------:|---------------:|-------------:|----------:|-----------:|----------:|----------------:|
| 2025-01     |       71 |         57 |           14 |         759.15 |     477.393  |    4.7739 |     2.3878 |    0.4298 |          1.9957 |
| 2025-02     |       60 |         50 |           10 |         810.65 |     619.299  |    6.193  |     1.6216 |    0.2919 |          3.287  |
| 2025-03     |       76 |         58 |           18 |         730.4  |     551.274  |    5.5127 |     1.518  |    0.2732 |          2.3529 |
| 2025-04     |       70 |         52 |           18 |         236.2  |      95.7192 |    0.9572 |     1.1905 |    0.2143 |          1.3656 |
| 2025-05     |       61 |         51 |           10 |         565.05 |     395.438  |    3.9544 |     1.4374 |    0.2587 |          2.8141 |
| 2025-06     |       64 |         50 |           14 |         671.9  |     481.963  |    4.8196 |     1.6096 |    0.2897 |          6.7309 |
| 2025-07     |       68 |         57 |           11 |         958.55 |     700.003  |    7      |     2.1911 |    0.3944 |          2.7751 |
| 2025-08     |       67 |         55 |           12 |        1928    |    1586.83   |   15.8683 |     2.8913 |    0.5204 |         13.4355 |
| 2025-09     |       77 |         60 |           17 |         982.15 |     586.669  |    5.8667 |     3.3515 |    0.6033 |          2.5382 |
| 2025-10     |       81 |         67 |           14 |        1458.1  |    1064.21   |   10.6421 |     3.338  |    0.6008 |          5.8086 |
| 2025-11     |       74 |         60 |           14 |         934.25 |     657.388  |    6.5739 |     2.3463 |    0.4223 |          3.0517 |
| 2025-12     |       75 |         58 |           17 |         747.5  |     479.708  |    4.7971 |     2.2694 |    0.4085 |          2.0109 |
| 2026-01     |       71 |         60 |           11 |        1011.3  |     751.32   |    7.5132 |     2.2032 |    0.3966 |          7.7558 |
| 2026-02     |       68 |         57 |           11 |         803.25 |     639.981  |    6.3998 |     1.3836 |    0.2491 |          3.1504 |
| 2026-03     |       81 |         68 |           13 |         809.95 |     610.634  |    6.1063 |     1.6891 |    0.304  |          5.6593 |
| 2026-04     |       79 |         62 |           17 |         418.95 |     210.125  |    2.1012 |     1.7697 |    0.3185 |          1.7188 |
| 2026-05     |       78 |         61 |           17 |         608.9  |     407.25   |    4.0725 |     1.7089 |    0.3076 |          5.9434 |
| 2026-06     |       67 |         54 |           13 |         312.9  |     178.126  |    1.7813 |     1.1422 |    0.2056 |          1.8288 |
| 2026-07     |       61 |         50 |           11 |         420.35 |     288.073  |    2.8807 |     1.121  |    0.2018 |          4.7876 |
| 2026-08     |       77 |         55 |           22 |         338.65 |     147.618  |    1.4762 |     1.6189 |    0.2914 |          1.7142 |
| 2026-09     |       81 |         60 |           21 |         690.5  |     445.102  |    4.451  |     2.0796 |    0.3743 |          4.9701 |
| 2026-10     |       64 |         44 |           20 |         355.85 |     168.429  |    1.6843 |     1.5883 |    0.2859 |          2.2395 |

## Caveats

- One ETHUSD contract is modeled as 0.01 ETH; unlike BTCUSD one contract, dollar notional is not equal.
- Core 100-point activation/50-point trailing setting is unchanged for main test; optional comparison uses ETH entry*100/80000 and ETH entry*50/80000.
- 27-minute exit-fee waiver is assumed on historical ETH trades but actual ETH eligibility must be verified with exchange; do not treat as granted.
- 1h OHLC bar replay only; conservative fee model assumes no 27-minute eligible intrabar exits. Optimistic upper bound assumes all first-hour intrabar stops qualify. Neither supplies exact timestamps.
- This is a reconstructed TradingView broker-emulator approximation, not a broker trade-history replay.
- No order book spread, funding charges, mark-price liquidation, variable leverage, margin restrictions, or live slippage. 0.5 price points adversely on each fill is an optional stress case.
- Only 22 fully completed UTC calendar months Jan 2025 through Oct 2026 are included; no November partial month.
- Profit factor is computed after modeled fees and GST. Net USD is for fixed 0.01 ETH contract, with no reinvestment or account sizing.
- OHLC path inference can differ from real 1-minute prices and TradingView's strategy engine.
