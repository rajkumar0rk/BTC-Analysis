# TP-only 15M EMA20 second touch — BTC/ETH

Same 15M completed-candle volume and volatility gates as the prior fixed 200/100 model. SL removed entirely.
2025-01 through 2026-10 (22 IST months), Delta India 1m. One independent 1x cash-equity trade at a time per symbol.
A TP-only win rate does not capture the risk of holding an unbounded loss; compare floating drawdown and holding time.

| Symbol | Exits | TP | Forced final close | Net return | Worst mark-to-market drawdown | Longest hold (hours) | MTM positive months |
|---|---:|---:|---:|---:|---:|---:|---:|
| BTCUSD | 63 | 62 | 1 | -15.195% | 39.622% | 6915.9 | 9/22 |
| ETHUSD | 167 | 166 | 1 | -34.995% | 102.996% | 5115.9 | 12/22 |

## Risk and methodology
- **NO stop-loss**. Supertrend changes, EMA crosses and time passage do NOT close positions.
- Fixed TP +200 BTC price points or equivalent ETH percentage at entry, frozen.
- Model marks floating equity minute by minute; worst wick adverse price and first crossing of zero equity measured.
- Positive closed trades can mask unrecoverable floating drawdown or exchange liquidation. No margin/liquidation/funding model is provided.
- Forced close at October 2026 boundary is ONLY for measuring the dataset, not a live exit rule.
- 0.05% taker each side plus 18% GST; adverse slippage 0.02% on both sides, no verified actual bid/ask spread.
- January 2025 first 330 IST minutes unavailable; 2026 not an untouched statistical validation.

Outputs: summary.csv, monthly_mark_to_market.csv, trade_ledger.csv.gz, quality.json.
