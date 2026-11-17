# V8.1 — BTC 2025 Exit Comparisons

**Historical model, not a proven profitable trading system. No 2026 candles.**

## Fixed entry across EVERY exit comparison

- On each completed hourly candle, daily and 4h trend EMAs must BOTH align.
- Daily/4h up: Close > EMA20 > EMA50 for LONG; inverse for SHORT.
- Enter at next 1-minute OPEN, weekdays IST only, whenever no position is open.
- Only one open position per variant, no daily trade limit.
- 1,000 BTC-point initial stop, monitored 1-minute, gap-aware, stop-first if ambiguous.
- Compare fixed +500/+750/+1000/+1500/+2000/+3000/+5000 point targets,
  +2000 with 24h max, and 1,000/500 or 1,500/750 activation/trailing.
- All other variants have a 48-hour maximum hold; remaining trades closed at 2025 year-end.
- Taker fees: 0.05% per side +18% GST, plus 5 BTC-point adverse slippage per side.
- No funding or margin/liquidation modeling. Price-points are 1-BTC-equivalent, NOT USD account returns.

## Exclusive trade backtests

| Exit | Trades | Win % | Net points | Profit factor | Profitable months | Drawdown pts |
|---|---:|---:|---:|---:|---:|---:|
| fixed_500 | 722 | 64.96 | -108463.36 | 0.619 | 0/10 | 110219.81 |
| fixed_750 | 572 | 55.77 | -84525.41 | 0.702 | 1/10 | 86462.7 |
| fixed_1000 | 481 | 49.9 | -60268.97 | 0.777 | 2/10 | 61647.46 |
| fixed_1500 | 348 | 39.94 | -44697.71 | 0.808 | 2/10 | 53292.99 |
| fixed_2000 | 269 | 33.09 | -40131.46 | 0.799 | 2/10 | 53443.44 |
| fixed_3000 | 204 | 27.45 | -33140.2 | 0.797 | 3/10 | 42052.06 |
| fixed_5000 | 165 | 21.82 | -37956.64 | 0.734 | 3/10 | 44326.89 |
| fixed_2000_24h | 293 | 35.15 | -44180.5 | 0.784 | 2/10 | 60162.54 |
| trail_1000_500 | 428 | 50.93 | -48534.26 | 0.793 | 1/10 | 52825.16 |
| trail_1500_750 | 317 | 40.06 | -45923.69 | 0.782 | 3/10 | 54436.95 |

## Monthly net points (exit month)

| Month | fixed_500 | fixed_750 | fixed_1000 | fixed_1500 | fixed_2000 | fixed_3000 | fixed_5000 | fixed_2000_24h | trail_1000_500 | trail_1500_750 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2025-03 | -15538.96 | -16273.89 | -15503.0 | -17388.39 | -17267.6 | -16669.01 | -14947.18 | -17082.88 | -12635.3 | -15809.41 |
| 2025-04 | -11705.27 | -9794.15 | -11003.01 | -8823.55 | -9571.39 | -9880.13 | -8591.57 | -9189.33 | -6495.64 | -10769.65 |
| 2025-05 | -11616.54 | -6680.26 | 971.51 | 1029.96 | 760.96 | 5988.65 | 1.86 | 839.25 | -4396.31 | 3402.99 |
| 2025-06 | -3260.88 | -3280.09 | -1094.2 | -887.11 | -1376.09 | 66.63 | -689.1 | -2377.85 | -1686.24 | -2042.4 |
| 2025-07 | -23128.77 | -22748.32 | -15399.46 | -10987.78 | -6734.11 | -5886.13 | -6966.8 | -8841.69 | -13782.5 | -12109.31 |
| 2025-08 | -4042.1 | -2415.14 | -928.41 | -854.44 | -3136.53 | -139.85 | 1372.47 | -4859.25 | -2007.25 | 195.91 |
| 2025-09 | -6263.29 | -4204.46 | -3263.81 | -5486.41 | -5190.32 | -5190.32 | -5190.32 | -4670.51 | -2424.88 | -6573.06 |
| 2025-10 | -13503.6 | -11452.01 | -11704.25 | -7682.42 | -8302.39 | -7446.83 | -8838.19 | -11354.31 | -8310.66 | -7738.51 |
| 2025-11 | -3626.64 | 2921.67 | 9284.54 | 17024.98 | 19184.4 | 15107.08 | 14847.62 | 20403.62 | 11729.86 | 14771.14 |
| 2025-12 | -15777.31 | -10598.76 | -11628.88 | -10642.55 | -8498.39 | -9090.29 | -8955.43 | -7047.55 | -8525.34 | -9251.39 |

## Split stability — net points

| Exit | Mar–Aug | Sep–Dec |
|---|---:|---:|
| fixed_500 | -69292.52 | -39170.84 |
| fixed_750 | -61191.85 | -23333.56 |
| fixed_1000 | -42956.57 | -17312.4 |
| fixed_1500 | -37911.31 | -6786.4 |
| fixed_2000 | -37324.76 | -2806.7 |
| fixed_3000 | -26519.84 | -6620.36 |
| fixed_5000 | -29820.32 | -8136.32 |
| fixed_2000_24h | -41511.75 | -2668.75 |
| trail_1000_500 | -41003.24 | -7531.02 |
| trail_1500_750 | -37131.87 | -8791.82 |

## Limitations

- This changes only the exit; entry remains V8 Daily+4H aligned, a condition not previously profitable.
- Candidate trades are exclusive per variant; trade populations diverge after exits (realistic path dependence).
- Trailing is conservatively stop-first on an ambiguous 1-minute candle.
- No 2026 test, no unseen holdout, no live market impact, actual fees or funding.
- Do not select a strategy solely because one of many exits wins on 2025.

