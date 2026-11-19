# Novelty gate — rolling spectral-phase forecast (2026-11-19)

**Decision: NEW, with partial overlap in generic follow/fade execution; spectral frequency-and-phase signal itself not found in main or listed research branches.** A pre-run code-search for `spectral`, `fourier`, `periodogram` and `cycle` returned no prior scripts in main, and branch-name search returned no earlier spectral branch. This is a novel **hypothesis**, not evidence of edge.

## Predeclared deterministic rules

For each symbol separately on its own original Delta India 1m data:

1. Aggregate COMPLETE 30-minute UTC OHLC bars (minimum 30 source candles each). For every just-completed 30m close, take the last **96** log-close returns, demean them, compute real DFT `rfft`, and examine frequency bins 3–16, representing 3–16-hour historical cycle lengths (96/k bars * 30m).
2. Identify the bin with greatest power, compute its fraction of total power within bins 3–16, and extrapolate that harmonic exactly one 30m bar ahead using the **phase known at signal time**. Normalize absolute forecast by trailing RMS of the same 96 completed returns.
3. Predeclared signal-strength thresholds: **A:** peak share >=0.16 and forecast/RMS >=0.20; **B:** peak share >=0.22 and forecast/RMS >=0.35. Both tested for **follow predicted sign** and **fade predicted sign** (four configurations). No lookahead or fit of frequencies to subsequent returns.
4. Enter at next native 1m OPEN when signal true; one position only; max hold 12 hours; stop first at 1.5 * completed 30m ATR(14), target at 2R; stop-first for 1m dual touches and gap-aware stop; slip adverse per side; no forced IST month-end liquidation.
5. Initial capital USD $1000 **per market**, 1% equity risk per trade with 3x notional cap; no compounding trick, martingale, leverage tuning or separate ETH/BTC parameter tuning.
6. Fee 0.05% taker EACH side plus GST 18% on fee; BTC slip 5 USD points each side, ETH 0.02% each side with extra sensitivity run 0.04%. Funding, actual spread/impact, margin/liquidation and lot-size feasibility reported as omitted. All results report what can be validated, with no claims of live attainability.
7. Select one SHARED fixed configuration based on Jan–Dec **2025 BTC+ETH** joint consistency only, then report that identical configuration unchanged on Jan–Oct 2026. No 2026 or month-label tuning. Strategy family known to be research-exposed (not pristine OOS).

## Closest prior work and material differences

- `research/btc-eth-hourly-return-autocorr-20261118`: autocorrelation/entropy of past hourly returns; this test estimates a **specific narrow-band Fourier frequency, power concentration and its extrapolated phase**, not lag correlation or hour-to-hour sign frequency.
- `research/independent-stage27-variance-ratio`: 4-bar/1-bar variance ratio, choosing follow or fade from realized 4-bar return. No selected spectral peak or phase forecast.
- `research/independent-bipower-jump-fade-20261118-v1`: hourly realized versus bipower variation jump fraction, shock-size fade. No cyclic-phase hypothesis.
- `analysis/institutional_discovery_stage19_monthly_10pct/`, `analysis/institutional_discovery_stage23_broad_5m_monthly/`: RSI, EMA, candle patterns, breakouts, sweeps and compression; no frequency-domain signal forecast.
- `research/independent-crossasset-confirmation-pf-20261118`, `research/independent-crossasset-dispersion-pf-20261118`: cross-market confirmation/leadership; spectral hypothesis is independently computed per native coin with EXACT same rules.
- `research/independent-stage26-semivariance`: signed return-squared asymmetry; not frequency-domain phase.

Generic directional trend/fade overlap is disclosed; assess against baseline rather than misleadingly treating the generic direction trade as new.

## Data, inference and audit scope

Use only original `data/delta_india/{BTCUSD,ETHUSD}/1m/2025-01.csv.gz` through `2026-10.csv.gz`; verify each compressed partition's SHA256 against its original manifest and strict chronological 60-second increments. Both October 2026 manifests now report all 44,640 UTC candles including Oct 31; verify *file hashes*, do not trust stale novelty gate's old gap note. **Jan 2025 IST first 5.5 hours missing** (sources start Jan 1 00:00 UTC). All 22 IST calendar periods Jan 2025–Oct 2026 including losses, no November. Require sequential per-market trade ledgers, monthly **exit-PF** from net USD PnL versus monthly account-NAV returns with live open-trade month-end mark (after estimated liquidation costs), monthly PnL and counts, annual actual 2025 and Jan–Oct 2026 compounding and >500% flags. If any quality check fails, reject rather than improvise/fill missing prices.

Stop-first one-minute data cannot reveal tick order. Real funding, spreads, order-book depth, margin, liquidation, lot constraints unverified. Avoid claiming live profitability on a backtest.
