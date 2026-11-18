# ETHUSD fixed-point correction — mandatory before profitability scoring

The historical ETH cross-market batch originally created by
`eth_all_prior_strategy_runner.py` made a **literal text substitution**:
BTCUSD->ETHUSD but kept BTC absolute price-point targets, stops and slippage.
This is **NOT** a comparable ETH trading strategy backtest.

**Treat the original batch as DIAGNOSTIC ONLY.**
Do not rank, select, trade, or claim +10% monthly profitability from its
fixed-point strategies, even if a Python script exited successfully.
Automatic workflow push triggering was disabled after recognizing this issue.

## Correct normalization

For a BTC original rule with price-point distance `D_BTC`, use the
**last completed BTCUSD reference price** known at the ETH signal time:

`relative_distance = D_BTC / BTC_reference_price`

Then compute:

`D_ETH = ETH_entry_reference_price * relative_distance`

Example, not a market quote: BTC=$100,000, ETH=$3,000.
BTC 200 points = 0.20% -> ETH 6.00 points.
BTC 100-point stop = 0.10% -> ETH 3.00 points.

Convert BTC 5-point execution slippage analogously, or use a separate
validated ETH spread/slippage model. As an illustrative price-ratio conversion,
5 BTC points at those prices correspond to 0.15 ETH points.
Do not mistake this for an actual executable fill estimate.

ATR-based multipliers and genuinely percentage-based thresholds are
already scale-aware: preserve them without changing their ATR multipliers.
Lookback candle counts and duration windows are not monetary points and
must never be rescaled.

Validate that any BTC reference price comes from data **available before
the ETH decision**, and that all October 2026 BTCUSD 1-minute data are
complete using `research/oct31-raw-repair`. No post-entry data, no
interpolated candles, and no future-month selection.

## Scope

1. Original fixed-point rule/exit/stop/fee parameters must be normalized
   explicitly at each ETH signal, not by blindly scaling arbitrary source
   numeric constants or by using one constant price ratio for all dates.
2. Review each original script's actual entry/exit/equity logic and
   classification: explanatory statistics are not executable strategies.
3. Run isolated ETH backtests with after-fee+GST realistic ETH slippage;
   report every complete IST month, wins/losses/trades, drawdown and assumptions.
4. The Stage26 ETH audit in `research/eth-stage26-crossmarket` uses ATR
   stops (scale-aware) and has additional 1, 0.5, and 0.25 ETH-point
   slippage sensitivity cases. Even its least severe tested case did
   **not** achieve 22/22 months profitable.
5. Existing BTC research and all scheduled automations must remain untouched.
