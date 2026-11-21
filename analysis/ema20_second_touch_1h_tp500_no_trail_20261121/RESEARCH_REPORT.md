# TP-only 1H EMA20 second touch — one entry per Supertrend cycle — 500 BTC points

1H second EMA20 touch with one trade per confirmed Supertrend cycle; ignore further touches after TP until flip. No volume/volatility filters, SL, ATR trailing, or time exit. BTC +500 point fixed TP, ETH percent equivalent.
2025-01 through 2026-10 (22 IST months), Delta India 1m. One independent 1x cash-equity trade at a time per symbol.
A TP-only win rate does not capture the risk of holding an unbounded loss; compare floating drawdown and holding time.

| Symbol | Exits | TP | Forced final close | Net return | Worst mark-to-market drawdown | Longest hold (hours) | MTM positive months |
|---|---:|---:|---:|---:|---:|---:|---:|
| BTCUSD | 73 | 72 | 1 | -19.619% | 53.835% | 9354.7 | 11/22 |
| ETHUSD | 96 | 95 | 1 | -11.031% | 56.914% | 8453.1 | 13/22 |

## Risk and methodology
- **NO stop-loss**. Supertrend changes, EMA crosses and time passage do NOT close positions.
- Fixed TP +500 BTC price points or equivalent ETH percentage at entry, frozen.
- Model marks floating equity minute by minute; worst wick adverse price and first crossing of zero equity measured.
- Positive closed trades can mask unrecoverable floating drawdown or exchange liquidation. No margin/liquidation/funding model is provided.
- Forced close at October 2026 boundary is ONLY for measuring the dataset, not a live exit rule.
- 0.05% taker each side plus 18% GST; adverse slippage 0.02% on both sides, no verified actual bid/ask spread.
- January 2025 first 330 IST minutes unavailable; 2026 not an untouched statistical validation.

Outputs: summary.csv, monthly_mark_to_market.csv, trade_ledger.csv.gz, quality.json.
