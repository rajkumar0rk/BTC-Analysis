# Institutional Stage 4A — pre-registered market-neutral funding carry feasibility

**Question:** Can a calendar-driven, direction-neutral LONG Binance BTCUSDT spot / SHORT Delta India BTCUSD perpetual pair earn positive net USD/USDT-proxy cash flow from actual observed funding and changes in the cross-venue basis, after two-leg fees, financing, and slippage?

This is **not** a BTC direction predictor. The paired position deliberately cancels most BTC USD delta, with residual cross-venue and USD/USDT basis risk.

## Predeclared research design (fixed before results)

- Study source: authentic Delta BTCUSD one-minute futures archive and hourly FUNDING:BTCUSD series, and public Binance BTCUSDT hourly spot candles from Binance's official data.binance.vision archive (downloaded in GitHub Actions). No fabricated spot observations. The Binance spot is **not** Delta's index and quotes BTC/USDT; parity USDT=USD is a strong unverified approximation. No full order books at either venue; executed returns remain unknown.
- Study starts 2025-10-01 01:00 UTC, to avoid the Delta India 8 September 2025 funding-payment change. Post-change BTCUSD snapshots expected at 00/08/16 UTC (05:30/13:30/21:30 IST). The archive's FUNDING:BTCUSD **hourly candle is a rate observation and not an actual settled payment**. Use its *prior completed hourly close* at settlement timestamps as a proxy, explicitly reported as such.
- Rates from the API are represented as percentages: 0.01 means **0.01%**, not 1%. Convert percentage to fraction by /100. Preserve negative rates as payments by shorts.
- Fixed entry calendar: first study date 2025-10-01 01:00 UTC and then every holding duration, nonoverlapping **within a test scenario**. Holding durations 8h, 24h, 7d, 14d, 30d; independent scenarios overlap *each other* and must never have their returns added together. Entry at hour OPEN for both instruments, exit at hour OPEN for both instruments. Credit funding only at snapshots strictly *inside* the holding window; do not count ambiguous entry/exit-boundary snapshots.
- Equal fixed 0.001 BTC spot long and 0.001 BTC futures short; report results in indicative USD/USDT equivalents and percentages of spot notional, **not guaranteed P&L**. Futures BTCUSD lot size 0.001 BTC (verify and disclose).
- Gross pair price P&L = quantity times [spot exit - spot entry - (perpetual exit - perpetual entry)]. Funding credit to perpetual short = rate in fraction times quote-based spot notional at each snapshot.
- Baseline costs: Delta futures taker 0.05% per side plus 18% GST on these fees; illustrative Binance spot fee 0.10% per side; adverse 5 BTC price-point slippage **per leg per side**; zero financing baseline and additional annual spot capital carry scenarios of 5% and 10%. Binance spot fees are not claimed to be verified personal account fees.
- Optimistic envelope: Delta maker 0.02% per side + GST, zero spot fees and zero slippage and financing; explicitly a **non-executable upper-bound-like** scenario, not evidence of fill ability. Stress scenarios: 15-point per-leg-per-side slippage and 5% spot financing; 10% financing.
- Strict source alignment and no candles interpolated. Require complete paired OHLC intervals, and funding proxy observations for every internal scheduled settlement. Missing settlement rates exclude the trial; no zero-filling.
- Report all durations and chronological slices 2025-Q4, 2026-H1, and 2026-Q3; no claim that any slice is an untouched statistical holdout (prior research has examined historical data). Include sample size, net-return mean, median, positive fraction, profit factor, max realized cumulative drawdown, breakdown of funding vs basis changes vs fees, and missing-event counts.
- Every negative/null experiment is persisted alongside positive results.
- No leverage, futures margin/liquidation mechanics, live spreads, financing availability, INR conversion, exchange transfer/access risk, actual paid funding logs, spot inventory lending, market impact, or USDT depeg correction are reconstructed. Consequently a positive result is **only a potential research lead** and cannot qualify as a real executable edge.

Exchange reference: https://www.delta.exchange/support/solutions?articleId=80001199725 and https://prod-mobile-india.delta.exchange/contracts
Binance source/time precision: https://github.com/binance/binance-public-data/blob/master/README.md
