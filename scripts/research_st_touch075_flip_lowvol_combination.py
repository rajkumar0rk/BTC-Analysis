#!/usr/bin/env python3
"""Causal, one-position BTCUSD 15m portfolio: touch .75/1.5 + flip 3/.5.

Exact previously selected entry cohorts and filters (no fresh optimization):
 Line Touch is SECOND GREEN after Supertrend line touch, 0.75% SL / 1.5% TP,
    volume ratio>=1.00x, 15m ATR%>=0.20%.
 Bullish Flip is NEXT GREEN after bullish ST flip, 3% SL / 0.5% TP,
    volume ratio<=0.80x, 15m ATR%>=0.20%.
 ST 10/3 closing exit ON in both, 1m stop-first sl/tp replay.
 Compare independent summed, one-position with priority variations and
 optional global one trade per bullish ST cycle. Year by actual exit month.
 PnL is BTC price points per 1 BTC not account return or funded backtest.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd

import research_st_three_best_combined_portfolio as portfolio
import research_supertrend_15m_line_touch as base
import research_supertrend_15m_filter_grid as feat
import research_second_green_percent_rr_scenarios as rr

ROOT=Path("analysis/st_075pct_touch_plus_lowvol_flip_20261122")
COHORTS={
 "line_touch":{
  "sl":0.75,"tp":1.5,"volume":"vol_ge_1p0","atr":"atrpct_ge_0p20",
  "expected_n":108,"expected_w":36,"expected_net":7928.77,
  "expected_pos":12,"expected_loss":10},
 "bullish_flip":{
  "sl":3.0,"tp":0.5,"volume":"vol_le_0p8","atr":"atrpct_ge_0p20",
  "expected_n":42,"expected_w":33,"expected_net":3401.08,
  "expected_pos":14,"expected_loss":5},
}
PRIORITIES={
 "combined_touch_priority":("line_touch","bullish_flip"),
 "combined_flip_priority":("bullish_flip","line_touch")
}
def period_summary(policy,ledger,months,period,valid_months):
    sub=ledger[ledger.exit_month_ist.isin(valid_months)]
    mon=months[months.month_ist.isin(valid_months)]
    return dict(
     policy=policy,period=period,
     trades=int(len(sub)),wins=int(sub.win.sum()),
     losses=int(len(sub)-sub.win.sum()),
     win_rate_pct=round(100*int(sub.win.sum())/len(sub),2) if len(sub) else 0,
     net_pts=round(float(sub.net_pts.sum()),2),
     profitable_months=int((mon.exit_month_realized_net_pts>0).sum()),
     losing_months=int((mon.exit_month_realized_net_pts<0).sum()),
     flat_months=int((mon.exit_month_realized_net_pts==0).sum()),
     max_monthly_loss_pts=round(float(mon.exit_month_realized_net_pts.min()),2),
     max_monthly_gain_pts=round(float(mon.exit_month_realized_net_pts.max()),2))
def main():
    rr.configure_grid()
    portfolio.SPECS=COHORTS
    ROOT.mkdir(parents=True,exist_ok=True)
    minute,bars,files=base.load()
    st,trend=base.supertrend(bars)
    volume,atpct,atrel=feat.build_features(bars)
    events,stops=feat.candidate_touch_events(
       minute,bars,st,trend,volume,atpct,atrel)
    signals=portfolio.decode_signals(
       minute,bars,trend,volume,atpct,atrel,events,stops)
    candidates=portfolio.compute_candidates(minute,trend,stops,signals)
    assert set(candidates.strategy)==set(COHORTS)
    prior_years={
      "line_touch":{"2025_full":7039.37,"2026_JanOct":889.40},
      "bullish_flip":{"2025_full":3394.93,"2026_JanOct":6.15}
    }
    parity=[]
    policies={}
    for name,s in COHORTS.items():
        df=candidates[candidates.strategy==name].copy()
        mon=df.groupby("exit_month_ist").net_pts.sum()
        assert len(df)==s["expected_n"],(name,len(df))
        assert int(df.win.sum())==s["expected_w"],(name,int(df.win.sum()))
        assert abs(float(df.net_pts.sum())-s["expected_net"])<.03,(
               name,"P&L parity",df.net_pts.sum())
        assert int((mon>0).sum())==s["expected_pos"],(name,"months positive")
        assert int((mon<0).sum())==s["expected_loss"],(name,"months negative")
        for label,bounds in (
           ("2025_full",("2025-01","2025-12")),
           ("2026_JanOct",("2026-01","2026-10"))):
            val=float(df[df.exit_month_ist.between(*bounds)].net_pts.sum())
            assert abs(val-prior_years[name][label])<.03,(
                  name,label,val,prior_years[name][label])
        parity.append(dict(strategy=name,trade_count=len(df),
                  winning_trades=int(df.win.sum()),
                  net_pts=round(float(df.net_pts.sum()),2),
                  positive_months=int((mon>0).sum()),
                  profit_2025=prior_years[name]["2025_full"],
                  profit_2026_JanOct=prior_years[name]["2026_JanOct"]))
        policies["standalone_"+name]=(df,dict(
            blocked_overlaps=0,blocked_one_cycle=0,
            input_signals=len(df),accepted=len(df)))
    print("STANDALONE_PARITY_PASS",json.dumps(parity),flush=True)
    independent=candidates.copy()
    policies["parallel_both_not_one_position"]=(independent,dict(
      blocked_overlaps=0,blocked_one_cycle=0,
      input_signals=len(independent),accepted=len(independent)))
    for label,priority in PRIORITIES.items():
        policies[label]=portfolio.portfolio(candidates,tuple(COHORTS),
                                            priority,global_cycle_cap=True)
        policies[label+"_no_cycle_cap"]=portfolio.portfolio(
             candidates,tuple(COHORTS),priority,global_cycle_cap=False)
    metrics=[];months=[];yearly=[];ledgers=[]
    periods={
      "2025_full":base.MONTHS[:12],
      "2025_JanOct":base.MONTHS[:10],
      "2026_JanOct":base.MONTHS[12:22],
      "22_months":base.MONTHS
    }
    for name,(trades,blocked) in policies.items():
        ledger=trades.copy()
        ledger["policy"]=name
        monthly=portfolio.month_table(trades,minute,name)
        assert len(monthly)==22,(name,len(monthly))
        monthly["policy"]=name
        metrics.append(portfolio.summarize(trades,monthly,name,blocked))
        for label,months_in_period in periods.items():
            yearly.append(period_summary(name,trades,monthly,
                          label,months_in_period))
        months.append(monthly)
        ledgers.append(ledger)
    met=pd.DataFrame(metrics)
    year=pd.DataFrame(yearly)
    monthly=pd.concat(months,ignore_index=True)
    allledger=pd.concat(ledgers,ignore_index=True)
    met.to_csv(ROOT/"policy_comparison_summary.csv",index=False)
    year.to_csv(ROOT/"2025_vs_2026_by_policy.csv",index=False)
    monthly.to_csv(ROOT/"actual_exit_monthly_pnl.csv",index=False)
    allledger.to_csv(ROOT/"trade_ledger_per_policy.csv.gz",
                     index=False,compression="gzip")
    # Portfolio cannot duplicate a live position; isolated paths remain
    # independent reference only. Ensure chronology and no duplicate cycles.
    for label,priority in PRIORITIES.items():
        ledger=policies[label][0].sort_values("entry_idx")
        assert (ledger.entry_idx.iloc[1:].to_numpy() >
                ledger.exit_idx.iloc[:-1].to_numpy()).all()
        assert ledger.st_cycle.is_unique
        assert len(ledger)<len(independent)
    raw_sum=sum(s["expected_net"] for s in COHORTS.values())
    assert abs(float(met[met.policy=="parallel_both_not_one_position"].net_pts.iloc[0])-
               raw_sum)<.05,("independent net",raw_sum)
    years=year[year.period!="2025_JanOct"]
    detail=year[year.policy.isin(PRIORITIES)]
    narrative=[
       "# BTCUSD 15M: 0.75% / 1.5% Touch + 3% / 0.5% Flip combined",
       "",
       "Two exact user-selected previously profitable in BOTH calendar 2025",
       "and January-October 2026 strategies, no retuning; 1m historical data.",
       "15m ST 10/3 closing exit retained, actual 1m stops/targets;",
       "one concurrent open position in exclusive portfolios.",
       "",
       "## One-position portfolio policies vs standalone",
       met[["policy","trades","wins","losses","win_rate_pct",
            "net_pts","profitable_realized_exit_months",
            "losing_realized_exit_months","flat_realized_exit_months",
            "max_realized_trade_equity_drawdown_pts",
            "blocked_overlaps","blocked_one_cycle"]].to_markdown(index=False),
       "",
       "## Yearly results by actual exit month",
       years[["policy","period","trades","wins","losses",
              "net_pts","profitable_months","losing_months",
              "flat_months","max_monthly_loss_pts"]].to_markdown(index=False),
       "",
       "## 2025 full vs Jan-Oct 2025 vs Jan-Oct 2026",
       year[year.policy.isin(PRIORITIES)][[
          "policy","period","net_pts","profitable_months",
          "losing_months","flat_months"]].to_markdown(index=False),
       "",
       "## Every actual-exit month: two priority choices",
       monthly[monthly.policy.isin(PRIORITIES)][[
          "policy","month_ist","realized_closed_trades",
          "exit_month_realized_net_pts","month_to_month_mtm_change_pts",
          "month_end_open_positions"]].to_markdown(index=False),
       "",
       "## Caveats",
       "- Historical results use the SAME 22 months used to choose settings.",
       "- 2025 has 12 months and 2026 Jan-Oct has 10; compare Jan-Oct windows.",
       "- Parallel sum DOUBLE COUNTS overlapping positions; not executable",
       "  with one open position and fixed capital per trade.",
       "- Trading fee model: taker 0.05% per side plus 18% GST, 5 BTC",
       "  points adverse slippage at each fill.",
       "- Net points per 1 BTC-equivalent, not dollar account P&L;",
       "  margin, leverage, liquidation, funding, real bid-ask and",
       "  live order latency NOT modeled.",
    ]
    (ROOT/"RESEARCH_REPORT.md").write_text("\n".join(narrative)+"\n")
    (ROOT/"quality.json").write_text(json.dumps(dict(
      source_repo="rajkumar0rk/BTC-Analysis",
      executed_status="passed_standalone_parity_and_exclusive_portfolio_checks",
      specs=COHORTS,
      standalone_parity=parity,
      time_period="2025Jan through 2026Oct IST",
      signal_rule="third 15m candle long entry; original ST close exit",
      strategy_filters_distinct_and_preserved=True,
      priority_modes={k:list(v) for k,v in PRIORITIES.items()},
      original_supertrend_exit=True,
      portfolio_exclusive=True,one_trade_per_ST_bull_cycle=True,
      2025_and_2026_actual_exit_month_used=True,
      pnl_units="BTC price points per 1 BTC equivalent",
      liquidation_and_funding_not_modeled=True,
      forward_tested=False),indent=2)+"\n")
    print("YEARLY_AND_MONTHLY_RESULTS\n"+year.to_string(index=False),
          flush=True)
    print("POLICY_SUMMARY\n"+met.to_string(index=False),flush=True)
    print("SUCCESS_TOUCH075_FLIP_COMBINATION",flush=True)

if __name__=="__main__":
    main()
