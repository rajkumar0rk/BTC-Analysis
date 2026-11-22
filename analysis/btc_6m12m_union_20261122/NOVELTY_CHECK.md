# BTC four-layer 6M + 12M combined single-account monthly backtest

Date: 2026-11-22. **Novelty gate: PARTIAL OVERLAP / portfolio-combination audit only.** This study is not an alpha strategy search or a filter optimization. User requested the **combined monthly result** of the previously tested 6-month and 12-month *profit-protected* BTCUSD four-layer strategies.

## Existing research

- `scripts/research_btc_four_layer_trade_management_20261121.py` and `analysis/btc_four_layer_trade_management_20261121/RESEARCH_REPORT.md`: existing fixed protected stops on 1M (stop at entry ± 0.15R activated after favorable 1M +1.5R, effective next 1M), 12m +9.207% / 51 trades, 6m +4.8154% / 55 trades. Both 7/22 profitable.
- `scripts/research_btc_four_layer_past_only_edge_20261121.py`: month-start past 6/12 complete month shadow trade net R and PF gates (original 3R exit training), no lookahead.
- `scripts/research_btc_four_layer_regime_trading_20261121.py`: market regime 1H+last completed 4H -> strategy gate -> first subsequent completed 15M confirmation -> native 1M order and conservative exit.
- `codex/STRATEGY_NOVELTY_GATE.md`: no duplicate tuning.

## Primary frozen combined-account rule

**Union portfolio**: at the start of each IST month, an existing 15M-confirmed event is eligible if **either** the original 6m or 12m as-of month-start (strategy, state) eligibility gate qualifies. Do NOT use any historical net result from that month to decide. Take the union of their eligible events by exact `signal_j`, `entry_utc`, `strategy`, `state`, `side`. Shared signals are executed **once**, never duplicated. One combined hypothetical $10,000 account, 0.5% of current balance risk per stop, 3x notional cap, one open BTCUSD position at a time, same event-time order priority as prior scripts. No requirement to make separate 6m and 12m positions simultaneously. All exits use the existing protected exit at +1.5R activation with +0.15R price lock beginning the NEXT completed minute, original 3R target, ATR initial stop, 36h timeout for breakout, IST month end flatten, adverse gap stop-first. Existing modeled taker 0.05% per side plus 18% GST, $5 price-point adverse slippage per side.

**Secondary no-optimization comparator**: intersection of both already-qualified rules (only when both 6m and 12m agree). Do not select the best based on test results. Independently replay `six_only` and `twelve_only` accounts and assert exact entry, exit and per-trade PnL parity to prior published *protected* runs. Additional cost stresses 2/5/10 round-trip bps for every account.

## Evidence requirements

- Source 992,160 SHA256-verified continuous Delta India BTCUSD futures 1M observations, 22 IST complete months 2025-01 through 2026-10.
- No 4H incomplete candle use, entry only after 15M confirmation, trailing stop only updated on completed 1M and effective next minute; no overlapping positions or cash reconciliation issues.
- Report for **every** 22 months separate 6m / 12m / actual UNION / intersection net monthly account returns and trades, wins, losses, PnL, ending equity.
- Explicit shared qualified signal count, union eligible signals, actual executed signals, skipped due to occupied position. Demonstrate combined != simple sum or combination of independently compounded returns.
- Validate standalone protected portfolio parity to the original saved 6m and 12m reports at individual-trade precision.
- Full year/combined net after fee/GST/slippage and extra bps stress; zero-trade months fail 22/22 target.
- 2025-2026 previously researched, no untouched external holdout. Real exchange bid/ask historical spread, settlement funding cashflows, contract sizing, liquidation absent. Real-money deployment BLOCKED; research branch only, no main merge.

The primary union vs intersection is specified BEFORE running. No hindsight per-month winner switch and no modified profit targets or ATR thresholds.
