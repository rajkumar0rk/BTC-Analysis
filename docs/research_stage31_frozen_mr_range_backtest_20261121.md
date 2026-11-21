# Stage31 — BTCUSD Mean Reversion + Range: frozen 1-minute independent verification

**Verified successful replay:** https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44914300686  
**Source:** `scripts/research_stage31_frozen_mr_range_audit_20261121.py`  
**Mode:** BACKTEST_ONLY / both strategies disabled

## Critical selection honesty

Both promising configurations were **chosen after examining 2026 outcomes** among previously tested models. They are **hindsight research findings, not validated 2025-selected forward winners**. The previous objectively 2025-selected alternatives in Stage28/Stage30 both had negative Jan–Oct 2026 performance. The November 2026 data are through November 18 only and one trade per strategy, so are not a sufficient test.

## Complete backtest rules

- Data: 989,280 consecutive BTCUSD 1-minute candles Jan 1, 2025–Nov 18, 2026; main sample is 22 complete IST months Jan 2025–Oct 2026.
- Entries: all signal indicators from completed 1H/4H bars. Market entry at next 1-minute OPEN; stop-first if stop and target are reached within same 1-minute candle. Exits can happen within a 1H or 4H source candle.
- Fees: model 0.05% futures taker per leg; 18% GST on trading fees; 5 BTC price-point adverse slip per leg; additional adverse 0/2/5/10bps per leg stressed.
- Per-strategy fixed theoretical risk 0.5% of strategy equity per initial R, maximum 5x notional. NOT full exchange order-book, funding, shared futures margin, precise contract sizing or liquidation simulation.

### Mean Reversion

1H LONG after previous close outside lower Bollinger20×2 band with RSI(2) oversold, then a fully completed bullish re-entry bar. Target the known-at-signal 1H SMA20. Initial stop 3× 1H ATR(14) from actual entry. Max holding 1,920 minutes (32 h). Only when completed 4H ADX ≤45, 8-bar directional efficiency ≤0.70 and absolute 3-bar 4H drift ≤1.5× 4H ATR.

### Range Trading

1H LONG/SHORT reversal on contact with a known 48×1H high/low boundary, directional close back inside, profit target at known prior 48h range midpoint. Initial stop 3× 1H ATR(14). Max holding 1,920 minutes. Only when completed 4H ADX ≤45, directional efficiency ≤0.70, and completed 4H close is inside the **middle 50%** of the previous 48×4H price channel; this rejects very directional 4H regimes.

## Independent Stage31 1-minute replay — reproduced Stage30 totals exactly

| Metric | Mean Reversion | Range Trading | Equal 50/50 monthly synthetic blend |
|---|---:|---:|---:|
| 2025 with +5bps/leg | **+1.0733%** | **+4.0562%** | **+2.5674%** |
| Jan–Oct 2026 with +5bps/leg | **+1.5714%** | **+4.0430%** | **+2.8061%** |
| **22m net with +5bps/leg** | **+2.6615%** | **+8.2632%** | **+5.4455%** |
| 22m profitable / losing / flat | 11 / 6 / 5 | 15 / 6 / 1 | **16 / 5 / 1** |
| Full 22m +10bps/leg | +1.3292% | +6.5566% | Not computed |
| Completed trades | 36 | 51 | Overlap/margin unmodeled |
| Available Nov 1–18 partial month +5bps/leg | **+0.2787% (1 trade)** | **−0.5532% (1 trade)** | Not a complete month |

The November MR trade was LONG entered November 10 UTC and exited November 11 UTC at the SMA target. The November Range trade was SHORT entered November 4 UTC and exited November 4 UTC at its stop. **This current partial-November loss in Range is a useful warning against assuming the earlier 22-month edge persists.** There are no significant recent samples here; avoid any claim of true forward validation.

The weighted monthly 50/50 portfolio is a synthetic comparison; this project has not jointly simulated margin, simultaneous positions, netting, funding and live lot precision.

## Result, decision and implementation status

- **Historical profitability is established only on the searched sample** and is subject to multiple-testing/data-snooping. 2025-only selection did not find a consistently profitable subsequent 2026 variant.
- **Forward profitable strategy status remains unproven**; no strategy live deployment and no change to existing Core/Donchian trading.
- Both candidate configurations stored in `config/strategies/stage31_frozen_historical_profitable_mr_range_research.json` as **BACKTEST_ONLY, disabled**.
- Next legitimate test: new BTC minute data beyond the searched interval with frozen rules, measured spreads/funding and independent broker-style execution, with meaningful sample size before contemplating live use.

## Evidence

GitHub Actions artifact `btc-stage31-frozen-meanreversion-range-trade-audit` contains:

- `mean_reversion_trade_ledger.csv`: every 1-minute entry/exit and modeled stop/target, side, R PnL and costs
- `range_trading_trade_ledger.csv`: same
- `strategy_22_months_and_partial_november.csv`: all month-level returns at 0/2/5/10bps extra adverse slip
- `frozen_verification_summary.json`: independently computed aggregate and stage30 parity assertions

Source runs: Stage30 44914001236 (gate study), Stage31 44914300686 (frozen exact replay).
