# One-change experiment: BTC +100-step profit lock, 1H Supertrend flip exit
Preregistered 2026-11-21.

## Exact change versus prior test
Baseline: scripts/research_ema20_second_touch_1h_step200_flip_exit_paths.py and analysis/ema20_second_touch_1h_step200_flip_exit_20261121/ with 200 point milestone step and exit on confirmed Supertrend flip.

**Only change: BTC milestone activation and incremental step size 200 -> 100 price points** (equivalent percentage for ETH). Leave strict post-milestone 1-BTC-point breach rule unchanged; this breach tick is NOT the trailing distance. Example entry 80000 LONG: price 80099 no lock; 80100 lock 80100; 80150 still lock 80100; 80200 lock 80200; a subsequent 80199 crossing exits. Shorts symmetric.

Keep previous 1H Supertrend(10,3) second 1H EMA20 touch post-flip entry, one trade per cycle; confirmed 1H Supertrend reversal always exits at next 1H open, even before activation; no fixed TP, separate SL, or ATR exit.

## Data and costing
Both BTCUSD and ETHUSD use SHA-verified original 1m Delta India OHLC through 2026-10-31, 22 IST months 2025-01 through 2026-10; 1x evolving $1000 equity per asset, 0.05% taker each side +18% GST, adverse 0.02% slippage each side, ETH step = 100*ETH entry/previous completed 1m BTC close. Synthetic O-H-L-C and O-L-H-C paths can only show exploratory OHLC assumptions; the true intraminute 1-point reversal, actual transaction prices, margin/liquidation, funding, and latency cannot be validated. Report both assumptions and full monthly series, wins/losses, reason-specific exits, max drawdown and insolvency.

## Novelty gate
PARTIAL OVERLAP: exact one-parameter 100-vs-200 threshold counterfactual explicitly requested; not a new independent strategy. Must not mistake 100 profit-lock step for +200 activation with 100 trail distance. No cherry-picking 2026 previously studied months.
