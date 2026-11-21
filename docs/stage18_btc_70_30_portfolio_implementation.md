# Stage 18 — BTC Futures 70/30 Research Portfolio Implementation

## Status
**BACKTEST ONLY — NOT LIVE READY.** This implementation reproduces the
22-month historical 70% core / 30% Donchian candidate using independently
replayed BTCUSD 1-minute candles. It does not send orders or touch live positions.

## Frozen components
| Sleeve | Allocation | Entry | Exit |
|---|---:|---|---|
| Core | 70% | 4H trend, 1H pullback, 15M breakout; ADX<=18, prior-month efficiency<=0.25, H1 VR<=1.2, initial stop 150–700 points | Structural stop, 5R target, maximum 240 minutes |
| Donchian | 30% | Completed daily close beyond prior 55 complete daily highs/lows, EMA50 alignment | 2 ATR initial stop, 3 ATR daily trailing stop, opposite breakout or 30-day maximum hold |

*Data feeds use 1-minute BTCUSD futures OHLCV; entries are on the next available 1-minute open. Both sleeves allow long/short independently, one open position per sleeve.*

## Risk and costs
- Each standalone engine sizes around 0.5% hypothetical risk per trade using its **own** equity; core is capped by its pre-existing 3x notional risk formula.
- Taker fees 0.05% per side, plus 18% GST on fees; 5 BTC price points adverse slippage per side.
- Additional **0, 2 and 5 basis points per side** are tested independently. Funding, real bid/ask spreads, maintenance margin, liquidation, fill uncertainty, and fractional contract sizing are **not** modeled.
- Core positions are attributed to the IST **exit month**; Donchian positions are marked to market at IST month-end. These differing accounting conventions are inherited from the original studies.

## How to reproduce
Run the independent script from the repository root, after installing `numpy pandas numba tabulate` and providing original Stage14 archived signals at the `STAGE14_EVENTS` environment path:

```bash
export STAGE14_EVENTS=/path/to/event_states.csv.gz
PYTHONPATH=scripts python -m unittest discover -s tests -p 'test_stage18_70_30_portfolio_20261121.py'
PYTHONPATH=scripts python scripts/research_stage18_70_30_portfolio_20261121.py
```

The workflow `.github/workflows/research-stage18-70-30-portfolio-20261121.yml`
runs this using the preserved Stage14 GitHub Actions artifact and saves the output:
`analysis/stage18_btc_70core_30donchian_implementation/`.

The `--config` argument loads
`config/strategies/stage18_btc_70core_30donchian_research.json`.
Unknown execution modes or mismatched cost/risk settings fail validation rather
than silently running inconsistent trading assumptions.

## Synthetic monthly portfolio math
For month `t`, with independent per-sleeve return **in percentage points**:

```
monthly_portfolio_return_pct[t] =
    0.70 * core_return_pct[t] + 0.30 * donchian_return_pct[t]

portfolio_equity_end[t] =
    portfolio_equity_start[t] * (1 + monthly_portfolio_return_pct[t] / 100)
```

At each new month, the *theoretical* weights reset to 70/30. The Donchian sleeve
might already have an open 30-day trade when a new calendar month starts.
The model **does not implement the necessary partial buy/sell orders** to
reweight such a position. This mathematical blend is therefore **not equivalent
to an executable jointly margined trading account**.

## Expected historical regression
January 2025–October 2026, already-researched data:

| Cost stress | Return | Profitable months | Losing months | Flat |
|---|---:|---:|---:|---:|
| Baseline costs | ~+14.44% | 19 | 2 | 1 |
| Extra 2 bps each side | ~+11.86% | 18 | 3 | 1 |
| Extra 5 bps each side | ~+8.10% | 16 | 5 | 1 |

The source 75/25 Stage18 benchmark must also reconcile to ~+13.88%, 18
profitable, three losing, one flat month. The run **fails closed** if these
results drift, rather than silently producing unsupported figures.

## No live use
- Never merge this directly into a live Delta Exchange execution service.
- Before any real-money deployment, implement a *unified 1-minute position
  and margin simulator*, with both strategies' positions, crossed exposure,
  funding, liquidation rules, contract sizes, actual spreads, and exchange-level
  order/stop/reconciliation behavior.
- Historical choice of 70/30 and 30-day maximum hold was informed by
  previously inspected 2026 results: **there is no untouched forward holdout**.
- No basis to claim 19 profitable months will recur in the future.
