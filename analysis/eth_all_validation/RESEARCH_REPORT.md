# ETHUSD — cross-market replay of existing BTC strategy code

**This test is independent of the BTC results and scheduled research tasks.**
ETH 1-minute files from main were SHA-256 checked. The runner translated
original source market paths and report paths while keeping signal logic
and absolute numeric parameters unchanged. The original BTC-to-ETH 5-point
slippage and price-point thresholds **may not be economically suitable for ETH**.

**Main-branch research scripts attempted: 50. Completed successfully: 39. Not completed: 11.**

Success here means the script executed, not that it achieved positive monthly returns.
Do not assume every script produces a 22-row after-cost compounded account-return series.

## Script execution audit

| Script | Group | Execution | Notes |
|:--|:--|:--|:--|
| research_selective_big_moves.py | institutional | success |   open_window=(ny.dayofweek<5)&(tod>=570)&(tod<720) |
| research_behavioral_discovery.py | institutional | success |   h["ny_weekday"]=ny.dayofweek.astype(int) |
| research_adaptive_anytime_entries_stage9.py | institutional | success |  |
| research_directional_acceptance.py | institutional | success |  |
| research_retest_reclaim_stage4.py | institutional | success |  |
| research_volatility_scaled_exits_stage5.py | institutional | success |  |
| analyze_institutional_regimes.py | institutional | success |  |
| research_intraday_spread.py | institutional | success |  |
| research_daily_200_500_points.py | intraday | success |   cand=b5[(z.dayofweek<5)&(z.hour>=9)&(z.hour<16)] |
| research_one_trade_every_day_200.py | intraday | success |  |
| research_every_candle_200.py | intraday | success |   n_weekday=np.asarray(ny.dayofweek,dtype=np.int8) |
| research_anytime_volume_volatility_patterns.py | intraday | success |  |
| research_time_day_volume_200.py | intraday | success |   weekday = np.asarray(india.dayofweek, dtype=np.int8) |
| research_price_action_time_day.py | intraday | success |   b["dow"] = ny.dayofweek |
| research_time_day_strategies.py | intraday | success |   selected_stop=after[after.target_points==0][after.stop_points==500] |
| research_swing_donchian_stage17.py | later | success |  |
| research_new_1h_patterns_stage19.py | later | failed | AssertionError: Some new model has 0 trades |
| research_monthly_10pct_stage19.py | later | success |  |
| research_signal_inversion_stage20.py | later | failed | RuntimeError: No account models |
| research_stage24_failed_auction.py | later | success |  |
| research_failed_auction_stage24.py | later | success |  |
| research_trade_counts_stage22.py | later | failed | research_trade_counts_stage22.py: error: the following arguments are required: --stage15, --stage17, --stage19 |
| research_v7_1_retest_2025.py | legacy | success |  |
| research_v7_2_daily_4h_2025.py | legacy | success |  |
| research_v8_1_2025_exits.py | legacy | success |  |
| research_v8_2025_big_moves.py | legacy | success |  |
| analyze_1m_exit_methods.py | legacy | success |   session=(ny.dayofweek<5)&(clock>=570)&(clock<720) |
| analyze_delta_mtf_institutional.py | legacy | success |   a["dow"]=local.dayofweek |
| research_july_drawdown_stage15.py | legacy | failed | research_july_drawdown_stage15.py: error: the following arguments are required: --original-artifact |
| research_monthly_portfolio_stage18.py | portfolio | failed | research_monthly_portfolio_stage18.py: error: the following arguments are required: --stage15-ledger |
| research_three_sleeve_stage20.py | portfolio | failed | FileNotFoundError: [Errno 2] No such file or directory: 'analysis/eth_all_original_rules/institutional_discovery_stage18_monthly_dual_strate |
| research_monthly_fixed_weight_stage21.py | portfolio | failed | FileNotFoundError: [Errno 2] No such file or directory: 'analysis/eth_all_original_rules/institutional_discovery_stage18_monthly_dual_strate |
| research_wide_monthly_stage23.py | portfolio | failed | FileNotFoundError: [Errno 2] No such file or directory: 'analysis/eth_all_original_rules/institutional_discovery_stage18_monthly_dual_strate |
| eth_transfer_stage24.py | research_branches | success |  |
| eth_transfer_stage25.py | research_branches | success |  |
| research_dynamic_exit_stage10.py | signals | success |  |
| research_structure_rr_stage11.py | signals | failed | AttributeError: 'DataFrame' object has no attribute 'consistent_positive' |
| research_pretrend_market_state_stage12.py | signals | success |  |
| research_stage12_monthly.py | signals | failed | research_stage12_monthly.py: error: the following arguments are required: --ledger |
| research_trend_pullback_breakout_stage13.py | signals | success |  |
| research_monthly_regime_stage14.py | signals | success |  |
| research_monthly_regime_switch_stage16.py | signals | failed | research_monthly_regime_switch_stage16.py: error: the following arguments are required: --original-artifact |
| research_big_trend_stage1.py | structure | success |   return np.asarray((x.dayofweek<5)&(m>=start)&(m<end)) |
| research_previous_day_range_swing.py | structure | success |   return np.asarray((x.dayofweek<5)&(minute>=start)&(minute<end)) |
| research_mtf_swing_range_long.py | structure | success |   return (x.dayofweek<5)&(minute>=start)&(minute<end) |
| research_mtf_swing_range_fixed3r.py | structure | success |   return (x.dayofweek<5)&(minute>=start)&(minute<end) |
| research_mtf_swing_range_long_fixed2r.py | structure | success |   return (x.dayofweek<5)&(minute>=start)&(minute<end) |
| research_mtf_swing_range_short_fixed2r.py | structure | success |   return (x.dayofweek<5)&(minute>=start)&(minute<end) |
| research_mtf_swing_range_short_fixed3r.py | structure | success |   return (x.dayofweek<5)&(minute>=start)&(minute<end) |
| research_mtf_uptrend_short_fixed3r.py | structure | success |   return (x.dayofweek<5)&(minute>=start)&(minute<end) |

## Method and limitations

- Entirely new ETH market data, not BTC trade ledgers or BTC fitted monthly results.
- Original absolute stops and profit points were left alone. Their scale may be inappropriate for ETH.
- Market scans, distribution reports, and audits are not automatically executable trading strategies.
- Scripts with data dependencies may fail rather than silently consume old BTC strategy result files.
- All 22 target months are Jan 2025–Oct 2026; incomplete November 2026 is excluded.
- Funding, actual bid/ask, contract precision, liquidation, and spread are not independently verified.
- Until independently audited 22-month net account returns are available, never claim 22/22 profitability.
- Stage24/25 research-branch strategies and Stage26 are handled in additional independent cross-market evaluations.

## Detailed outputs

Small report excerpts and source checks are inside analysis/eth_all_validation/excerpts/.
Original full trade ledgers are generated ephemerally by GitHub Actions; use the exact script and
original ETH market data to reproduce them. GitHub Actions artifact retention is not permanent.
