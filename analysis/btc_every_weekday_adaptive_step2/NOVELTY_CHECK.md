# Restarted Step 2 — Causally adaptive daily entry, exactly one trade every IST weekday

**Novelty gate: PARTIAL OVERLAP — approved incremental study**. This is a conditional clock/side selection experiment using existing fee and execution replay, NOT an untested strategy recommendation.

## The non-negotiable goal

One **and only one BTCUSD futures trade on every full Monday–Friday IST calendar day**, maximizing **the frequency of profitable daily account returns** subject to after-cost positive expectancy and tolerable drawdown. The previous +0.2% example is NOT used as a fixed target, selection metric, or threshold. Negative days count even when a trade loses less than 0.2%, and every day must have exactly one trade.

## Closest existing work

- scripts/research_btc_every_weekday_reset_step1.py and analysis/btc_every_weekday_reset_step1/: 51,840 full-coverage models with FIXED entry hour, 10 momentum/fade sides, 6 stops, 6 gross R:R values, 3 holds and standard/scalper costs. Best Scalper Offer member chosen on 2025 gained +1.12% in 2025, lost -2.25% in 2026, with 52.31% and 48.39% winning days respectively.
- scripts/research_one_trade_every_day_200.py and analysis/one_daily_trade_200_points/: all NY days including weekends, forced daily fallback, fixed BTC-point target. Not the same IST adaptive timing logic or broad percentage R:R matrix.
- scripts/research_btc_daily_direction_step3.py / research_btc_daily_rr_grid_step4.py: 19:00/20:00 optional signals skip many days. Cannot answer the strict one-entry-every-weekday question.
- scripts/research_every_candle_200.py and Stage7, Stage19/23 and Stage24/25: time/volume/momentum/structure studies have overlapping signals, but differ in full IST daily coverage, tested exchange fees, and multi-R grid.

## New hypothesis

Selecting the **earliest causally observed intraday momentum/volume/range event** from a locked list of UTC-to-IST-correct clock checkpoints, with a mandatory later fallback trade if no qualifying event occurs, may outperform a fixed-hour entry because it can act when volatility is already expanding. No rule can choose an earlier entry using a later price.

## Pre-registered entries

- Authentic Delta India BTCUSD 1m archive 2025-01 through 2026-10; strict no gaps, duplicate/null/invalid OHLC. **477 full IST weekdays**, from 2025-01-02 through 2026-10-30, 260 days 2025 and 217 days 2026. All entry prices at 1m OPEN at selected clock checkpoint, so all features at 1m close strictly BEFORE entry.
- Candidate checkpoint policies:
  1. Asia/EU/US checkpoints at 09, 12, 15, 18, 19, 20 IST;
  2. EU/US checkpoints at 15, 18, 19, 20 IST;
  3. US checkpoints at 18, 19, 20 IST.
  Each tries checkpoints from EARLIEST to LATEST. First qualifying condition enters immediately. If NONE qualifies, **MUST enter at 21:00 IST**. This guarantees one trade every weekday without using future data. No weekend entry. A separately tested 19:00 fixed-entry/5m fade baseline anchors prior Step1 results.
- At every checkpoint calculate only: preceding completed **5m, 15m, 60m, 240m price returns**; previous completed 5m volume / average of the prior twenty complete 5m volumes; previous 60m high-low range position; preceding 15m price range / median of six prior 15m ranges; current last close relative to high/low of 120-to-30 minutes ago. No current partial bars and no forward signals.
- Fourteen frozen trigger rules: 15m impulse follow/fade (abs return >=0.15%); 1h impulse follow/fade (abs return >=0.40%); past 5m relative volume >=1.5 follow/fade 5m return; 15m and 60m agree follow/fade (15m abs >=0.08%, 60m abs >=0.25%); 15m/60m pullback (opposing signs, same thresholds, follow 60m); 60m range position >0.85 or <0.15 follow or fade; 120-to-30m range breakout with volume>=1.25 follow; 15m range expansion >=1.5× median six prior 15m candle ranges follow/fade. All directions deterministic, no future information.
- Mandatory 21:00 fallback side = (a) FADE last completed 5m return or (b) FOLLOW last completed 60m return, tie goes LONG before inversion. The fallback side is independent of whether the chosen trigger rule is bullish/bearish.
- Total daily entry policies: **14 × 3 checkpoint windows × 2 fallback directions + 1 fixed 19:00 baseline = 85**. All have exactly 477 trades.

## Frozen exit/fee scenarios

- 6 BTC price stop %: **0.10 / 0.20 / 0.30 / 0.50 / 0.75 / 1.00**.
- 6 gross price target R multipliers **0.75 / 1 / 1.5 / 2 / 3 / 4**, so target price percentage = SL % × R. Do NOT use +0.2% net target.
- 3 maximum holds: **30 / 60 / 120 minutes**, 1-minute stop-first execution. Stop worse-than-open in price gaps; target touched at target; timeout at exact 1m OPEN; no trade holds after 23:59 IST.
- Two fee models: standard taker 0.05%/side + 18% GST, hypothetical regular Scalper Offer zero closing fee only if held ≤30 minutes, assumed opted in in advance, with 5 BTC price-point adverse slippage on EACH side.
- **85 × 6 × 6 × 3 × 2 = 18,360 configurations**, each with 477 trades, at **100% account notional and 1x unleveraged exposure**, no other leverage.
- NO trading Sat/Sun, NO missing daily trades, NO unlimited trade count. Funding and live orderbook/real spread not modeled; cannot assume offer terms were active in all historical months.

## Validation and reporting

- Main metric = **profitable-days fraction** separately in 2025 and 2026, with **net 2025 and 2026 compounded account return**, 22 monthly results, worst month, worst day, max drawdown, consecutive losing weekdays, profit factor, total fees, TP/SL/timeout breakdown and fallback frequency.
- Choose using 2025 only: require strictly POSITIVE 2025 net return AND max 2025 drawdown <=15%; among those maximize winning weekdays in 2025, then 2025 net return, then smaller 2025 DD. If none pass, choose least-loss version solely for diagnosis and say no validated candidate.
- Recheck selected rule untouched against 2026, which is **not a pristine holdout** because earlier research already investigated 2026. Also count models net profitable in both years and with >=60/70% positive days in BOTH years, explicitly hindsight only. Do not select based on them.
- Compare Step 1 fixed19 5m fade baseline under the SAME replay engine for verification. Report neighbor robustness (adjacent stops/target ratios), 2025-selected daily and 22-month ledgers, cost model effects.
- This is Step 2 ONLY; do not optimize a second batch after seeing 2026 results in the same experiment.

## Source caveats

2026-11-23 manifest reports complete October UTC archive (previous stale novelty gate said a missing day). Runner verifies actual 1m continuity. Intrabar stop/TP ordering is unknowable from OHLC1m; ties stop first. 18,360 trials and prior exposure create severe overfitting risk even with 2025 selection.
