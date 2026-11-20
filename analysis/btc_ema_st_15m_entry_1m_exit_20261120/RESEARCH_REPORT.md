# Original BTC 15M EMA20+Supertrend: 1M OHLC stop/trailing validation
Original script recomputed and +$828.4954 regression-verified from identical archived data.
The only material execution change is 15M OHLC to 1M OHLC, plus consequent exact-minute timing.

| Model | Net USD | Trades | Profit factor | Profitable complete months |
|---|---:|---:|---:|---:|
| Old 15M OHLC (assumed offer) | +828.50 | 1000 | 1.6139 | 19/22 |
| New 1M OHLC assumed_30m_offer | -91.46 | 415 | 0.8113 | 2/22 |
| New 1M OHLC no_offer | -96.59 | 232 | 0.652 | 1/22 |

## Model limitations
- 1M candle OHLC still infers intraminute high/low order, not real ticks, quotes or fills.
- No actual historical mark-price liquidation, spread, slippage, funding or latency.
- Offer active all-history is an optimistic assumption; compare the no-offer scenario.
- No pre-entry trading from unclosed 15-minute bars; 15M indicators unchanged.
- No VPS live bot or main branch modified.
- The previous +$828.50 includes partial Nov 2026; 22 complete months end Oct 2026.
- Fixed $10 margin per position, no replenishment or position size compounding.
