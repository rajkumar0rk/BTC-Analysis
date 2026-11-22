#!/usr/bin/env python3
"""Independent replay audit of two 17/22 positive-month causal ST filters.

These were identified by exploratory evaluation of 2026 data.
Audit is still IN-SAMPLE diagnostic, not independently validated alpha.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd

import research_supertrend_15m_line_touch as base
import research_supertrend_15m_filter_grid as filt
import research_st_three_best_combined_portfolio as portfolio
import research_st_touch075_flip_lowvol_combination as baseline
import research_st_touch_flip_causal_regime_filters as study
import research_second_green_percent_rr_scenarios as rr

OUT=Path("analysis/st_touch_flip_17month_candidate_audit_20261122")
CHOICES={
 "baseline":("off","off"),
 "touch_1h_bull_di_4h_ema20":("1h_bull_di_4h_ema20","off"),
 "touch_1h_4h_above_ema20":("1h_4h_above_ema20","off"),
 "both_1h_above_ema20":("1h_above_ema20","1h_above_ema20"),
 "both_1h_above_ema50":("1h_above_ema50","1h_above_ema50"),
 "both_1h_above_ema20_weekday":(
    "1h_above_ema20_weekday","1h_above_ema20_weekday")}
EXPECTED={
 "baseline":(10060.42,548.16,8,5),
 "touch_1h_bull_di_4h_ema20":(8176.19,4280.81,9,8),
 "touch_1h_4h_above_ema20":(9560.31,3887.15,9,8),
 "both_1h_above_ema20":(13323.02,3799.70,9,7),
 "both_1h_above_ema50":(11075.61,4347.83,9,7),
 "both_1h_above_ema20_weekday":(14763.67,2615.88,9,7)}

def main():
    rr.configure_grid()
    portfolio.SPECS=baseline.COHORTS
    OUT.mkdir(parents=True,exist_ok=True)
    minute,bars,files=base.load()
    st,trend=base.supertrend(bars)
    vol,apct,arel=filt.build_features(bars)
    events,stops=filt.candidate_touch_events(
        minute,bars,st,trend,vol,apct,arel)
    signals=portfolio.decode_signals(
        minute,bars,trend,vol,apct,arel,events,stops)
    allc=portfolio.compute_candidates(minute,trend,stops,signals)
    f=study.features(bars,trend)
    m15=f.reset_index(drop=True)
    indices=allc.entry_bar.to_numpy(int)
    is_touch=(allc.strategy=="line_touch").to_numpy()
    profiles=[];monthly=[];trades=[]
    for name,(touch,flip) in CHOICES.items():
        at=np.ones(len(allc),bool) if touch=="off" else m15[touch].to_numpy(bool)[indices]
        af=np.ones(len(allc),bool) if flip=="off" else m15[flip].to_numpy(bool)[indices]
        eligible=allc[(is_touch&at)|(~is_touch&af)]
        used,blocking=portfolio.portfolio(
            eligible,tuple(baseline.COHORTS),
            ("line_touch","bullish_flip"),global_cycle_cap=True)
        mm=portfolio.month_table(used,minute,name)
        stats=study.evaluate(used)
        expected=EXPECTED[name]
        assert abs(stats["2025_full_net"]-expected[0])<.02,(name,stats)
        assert abs(stats["2026_JanOct_net"]-expected[1])<.02,(name,stats)
        assert stats["2025_full_win_months"]==expected[2],name
        assert stats["2026_JanOct_win_months"]==expected[3],name
        assert (used.entry_idx.iloc[1:].to_numpy() >
                used.exit_idx.iloc[:-1].to_numpy()).all()
        assert used.st_cycle.is_unique
        periods={}
        for label,months in (
           ("2025_H1",base.MONTHS[:6]),
           ("2025_H2",base.MONTHS[6:12]),
           ("2025_full",base.MONTHS[:12]),
           ("2026_H1",base.MONTHS[12:18]),
           ("2026_JulOct",base.MONTHS[18:22]),
           ("2026_JanOct",base.MONTHS[12:22])):
            x=used[used.exit_month_ist.isin(months)]
            losses=x[x.net_pts<=0]
            wins=x[x.net_pts>0]
            periods[label+"_pf"]=round(float(
                wins.net_pts.sum()/-losses.net_pts.sum()),3) if len(losses) else None
            periods[label+"_win_rate"]=round(
                100*len(wins)/len(x),2) if len(x) else None
        profiles.append(dict(
            name=name,touch_gate=touch,flip_gate=flip,
            blocked_overlap=blocking["blocked_overlaps"],
            blocked_cycle=blocking["blocked_one_cycle"],
            **stats,**periods))
        xx=used.copy()
        xx["policy"]=name
        mm["policy"]=name
        trades.append(xx)
        monthly.append(mm)
    summary=pd.DataFrame(profiles)
    m=pd.concat(monthly,ignore_index=True)
    alltr=pd.concat(trades,ignore_index=True)
    summary.to_csv(OUT/"verified_17month_comparison.csv",index=False)
    m.to_csv(OUT/"verified_monthly_2025_2026.csv",index=False)
    alltr.to_csv(OUT/"selected_trade_ledgers.csv.gz",
                 index=False,compression="gzip")
    negative=m[(m.policy== "touch_1h_bull_di_4h_ema20")&
               (m.exit_month_realized_net_pts<0)]
    columns=[
        "name","total_trades","total_net_pts","closed_equity_max_drawdown_pts",
        "2025_full_net","2025_full_win_months","2025_full_loss_months",
        "2025_full_trades","2025_full_win_trades","2025_full_pf",
        "2026_JanOct_net","2026_JanOct_win_months","2026_JanOct_loss_months",
        "2026_JanOct_trades","2026_JanOct_win_trades","2026_JanOct_pf",
        "2026_H1_net","2026_JulOct_net"]
    diag=m[m.policy=="touch_1h_bull_di_4h_ema20"]
    report=[
      "# Two BTC ST Touch+Flip variants with 17/22 profitable months",
      "",
      "Historical exploratory candidates: 2026 outcomes were viewed during",
      "hypothesis selection. This confirms exact replay parity, NOT OOS.",
      "Only entry filters change; fees, original ST closing exit and",
      "conservative 1m fixed % stops/targets remain unchanged.",
      "",
      "## Yearly trades, profit factor, max drawdown and win months",
      summary[columns].to_markdown(index=False),
      "",
      "## Top consistency setup: 1H DMI direction + 4H EMA20 for TOUCH only",
      "For Line Touch, require +DI > -DI on the last completed 1H",
      "candle AND close above EMA20 on the last completed 4H candle.",
      "Bullish Flip (3% SL/0.5% TP) retains existing low-volume criteria.",
      "",
      diag[["month_ist","newly_entered_trades","realized_closed_trades",
            "exit_month_realized_net_pts","month_end_equity_mtm_pts"
           ]].to_markdown(index=False),
      "",
      "## Negative months remaining in top consistency configuration",
      negative[["month_ist","exit_month_realized_net_pts",
                "newly_entered_trades"]].to_markdown(index=False),
      "",
      "## Risk warnings",
      "- BTC point profit is 1 BTC equivalent, not account ROI.",
      "- Estimated 0.05% taker each side, 18% GST and 5 point slip each side.",
      "- ST close and minute stops are honored; no leverage/funding/liquidation.",
      "- 121 related filter tests increase the chance of hindsight overfit.",
      "- Genuine validation requires forward paper trading on unseen data.",
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    (OUT/"quality.json").write_text(json.dumps(dict(
      independently_replayed_settings=len(CHOICES),
      source_2025_selected_study=str(study.OUT),
      year_2026_was_examined_before_selection=True,
      full_period="Jan 2025 to Oct 2026 IST",
      original_trade_exit_rules_preserved=True,
      per_strategy_filters_retained=True,
      exclusive_one_position=True,
      selected_by_2026_backtest_diagnostics=True),indent=2)+"\n")
    print("17MONTH_AUDIT_PARITY_PASS",flush=True)
    print(summary[columns].to_string(index=False),flush=True)
    print("BEST_MONTHLY\n"+diag[["month_ist","exit_month_realized_net_pts"]].to_string(index=False),flush=True)

if __name__=="__main__":
    main()
