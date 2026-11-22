# 15M first EMA20 touch + volume and volatility: fixed 1R TP, Supertrend-flip loss exit

BTCUSD and ETHUSD, signal 15M, first touch only after Supertrend(ATR10, multiplier3) flip, entry monitored on 1m.
Volume of last completed 15M candle > 1.2× its SMA20; completed Wilder ATR(14) > its SMA20. Both required at first touch; reject cycle if they fail.
REFERENCE R = directional distance from executed EMA20 entry to last completed Supertrend line, frozen at entry.
Fixed TP = entry + direction × **1R**. NO fixed 1R stop loss: losing exit waits for confirmed opposite 15M Supertrend flip and happens next 15M opening; there is no trailing or profit lock.

| Asset | Assumed 1m path | Trades | Wins | Losses | TP 1R exits | ST flip exits | Win% | Profit factor | Net return | Profitable months | Max floating drawdown |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSD | O-H-L-C | 319 | 161 | 158 | 177 | 142 | 50.47% | 0.5531 | -42.7095% | 2/22 | 43.0984% |
| BTCUSD | O-L-H-C | 319 | 163 | 156 | 178 | 141 | 51.097% | 0.562 | -41.6251% | 2/22 | 42.5445% |
| ETHUSD | O-H-L-C | 268 | 151 | 117 | 154 | 113 | 56.343% | 0.7192 | -31.5953% | 6/22 | 33.7047% |
| ETHUSD | O-L-H-C | 268 | 150 | 118 | 155 | 112 | 55.97% | 0.7128 | -32.1204% | 6/22 | 34.2136% |

## Filter gate and 2R comparison
- Rejected first touches do NOT roll to second touch; one entry maximum per trend flip.
- Direct 2R control, otherwise same strategy: analysis/st_firsttouch_15m_vol12_atr14_filter_20261122/
- This 1R test changes ONLY the TP distance, not the losing exit.

## Limitations
- 1m OHLC is not tick-level: assumed Open-High-Low-Close and Open-Low-High-Close paths cannot establish actual order of prices within a minute.
- SHA256-verified Delta India 1-minute data Jan 2025-Oct 2026, 22 IST months; $1000 initial equity per asset, 1x evolving model notional.
- Assumed 0.05% taker fee each side plus 18% GST on fees, 0.02% adverse slippage each side.
- No funding, exchange margin/liquidation, real order-book fills, spread or execution latency. 2026 extensively researched previously; not untouched OOS.
- Supertrend flip remains the stop; actual losing trade can exceed reference 1R. Ratio is not actual fixed 1:1 risk/reward.
- All months marked to market including open positions; final forced close is accounting only.

Artifacts: summary.csv, monthly_mark_to_market.csv, trades.csv.gz, quality.json.
