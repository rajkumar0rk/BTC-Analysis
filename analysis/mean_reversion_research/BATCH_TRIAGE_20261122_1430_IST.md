# Mean Reversion source gate — 2026-11-22 14:30 IST

State: SOURCE SCREEN ONLY, zero new historical backtests. Existing MR002 success Actions 44911975169 and artifact 14709852576 remain prior verified evidence; not counted as new.

## Newly checked sources (distinct from 13:30 batch)
1. JusTraderZulu/VWAP_Research, https://github.com/JusTraderZulu/VWAP_Research (default branch main; repository license metadata absent when queried). Daily-reset anchored VWAP deviation event threshold, Hurst R/S regime (MR <=0.45; trend >=0.55), success defined as signed deviation crossing zero within 5/10/20 bars. **NOT A TRADING STRATEGY**: research is conditional probability/event labeling, not executable entries/stops/position sizing. Cannot invent a stop/exit to claim source-faithful replication. This is a potentially novel Hurst regime research hypothesis, not a ready backtest baseline. SKIP trade replay; separate EDA only if data supports it.
2. brucechueh/mean-reversion-backtest, https://github.com/brucechueh/mean-reversion-backtest (main; repository license metadata absent). Its BB-width/MACD BTC/ETH 5m model self-reports probable same-bar Bollinger lookahead; overlaps prior band-stretch family. Its alternative SMC sweep/SMT/OI/funding system overlaps Stage2–4/24, requires non-OHLCV historical inputs, and cannot be assumed reproducible on OHLCV. SKIP.
3. silas0700/Bitcoin-Mean-Reversion-Backtest, https://github.com/silas0700/Bitcoin-Mean-Reversion-Backtest (main; repository license metadata absent). Daily long-only n-day return extreme, enter when momentum < -threshold and exit when > +threshold; n=7..84 days, threshold=5..40%, selected on 2020–2024. No source-defined protective stop and risk can persist through BTC crash. Does not satisfy structurally capped downside; SKIP source-faithful futures adaptation until risk problem resolved.

## Independent decision
No candidate passed source licensing + exact risk + mechanism novelty simultaneously. **Do not run a backtest of an invented variant**. The Hurst-conditional anchored VWAP event study is the most economically distinct *research question*, but it is not an executable source strategy. Source commit SHA, complete historical data quality and trade rules are missing, so no candidate frozen. No new profitability, no new variant, no Actions launch.

## Cost gate
At 0.05% per side with 18% GST, two-sided trading fee is 11.8 bps of notional (before funding, spread or slippage). The anchored-VWAP event probabilities do not establish after-fee expectancy. Prior MR002 204 trades, -30.5503268% NAV, 33.5514% minute-close DD, 6/22 positive months; reject remains unchanged.

Next: find licensed complete source with stop/timeout and a materially different causal signal, pin immutable source SHA, compare against Stage19/23/24 and MR002, then execute authenticated Delta BTCUSD 1m with next-minute and stop-first fills. If no source passes, perform source-defined Hurst/VWAP EDA only and label it exploratory, not a backtest.
