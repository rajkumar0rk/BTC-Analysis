# Independent Daily-Profit Hunt — 2026-11-20 02:48 IST — executable-quote feasibility calculation

Status: BLOCKED / INCONCLUSIVE for cross-venue execution hypothesis; NOT a strategy backtest. Prior vol-of-vol strategy remains REJECTED from Actions run 44558873365. This is a completed numerical feasibility test on all available authentic forward snapshots, not a profitability claim.

Source: read-only main `analysis/forward_microstructure/snapshots/2026-11-19.jsonl`, Git blob SHA `441a3bb48d97c2b328d7daeaa582d70f94a48ec5`. Three original JSONL records parsed and evaluated. Delta India BTCUSD perp is quoted USD; Binance BTCUSDT spot is quoted USDT; their notional conversion is unknown. Binance and Delta book sizes are not directly comparable. Calculation uses best quotes only, without any assumed fills.

| Sample UTC | Delta-to-Binance receive lag ms | Sell Delta bid / buy Binance ask gross bps | Sell Binance bid / buy Delta ask gross bps |
| --- | ---: | ---: | ---: |
| 2026-11-19 02:12 | 433 | -5.1570 | +5.0784 |
| 2026-11-19 10:22 | 636 | -4.5510 | +4.4732 |
| 2026-11-19 19:05 | 705 | -3.0040 | +2.9236 |

The positive reverse-direction quote differences are **not executable arbitrage**: books were received 433–705 ms apart, currency basis is unverified, exchange access/hedge shorting/spot borrow and venue fees are not established. For reference, Delta India futures taker fees alone for a complete entry+exit are assumed 0.05% per side +18% GST = 11.8 bps of notional; a two-venue hedged trade needs its own venue- and side-specific fee/cost schedule and cannot use this 11.8 bps as a complete hedge-cost estimate. Do not add the two snapshot prices as if simultaneous. Neither side's cross-venue execution is proven. The observed reverse quote gap (2.924–5.078 bps) is smaller than the Delta-only complete roundtrip taker-fee assumption, but that is merely a cost-scale comparison, NOT an executable net-profit estimate.

Falsification/feasibility decision: **INCONCLUSIVE — no 2025/2026 order-book history and only 3 unsynchronized forward samples**. No daily equity, 22-month monthly PF, ETH frozen validation, or net trade outcomes can be estimated. Funding candles are rate proxies, not settled payments; Binance funding HTTP 451; no maker fill or hedge proof. Next actionable step is collect synchronized BTC quote/trade/settled-funding and borrow/FX data, then measure a gross executable edge with a fixed latency limit, capacity and exact fee model before launching a trading backtest. If these data cannot be obtained, switch to a novel OHLCV-testable mechanism instead of inventing execution. The prior negative BTC/ETH vol-of-vol experiment is closed and must not be retuned.

No main/other branch changes, no real orders, no alert. This record is append-only within this schedule's isolated branch.
