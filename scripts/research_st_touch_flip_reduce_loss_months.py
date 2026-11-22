#!/usr/bin/env python3
"""BTCUSD 15m: reduce losing months for fixed ST Touch+Flip strategy.

Uses EXACT existing 0.75% SL / 1.5% TP Line Touch and 3% SL / 0.5% TP
Bullish Flip, after verified original signal volume/ATR filters, 1m
stop-first fill, fee+GST+slippage, ST close exit, one position at once,
one trade per ST bullish cycle. Tests only entry filters based on last
COMPLETED 15m/1h/4h OHLC values.

All past months incl 2026 have been observed in conversation: results
cannot be treated as independent out-of-sample. Separate rankings:
(A) train using 2025 ONLY, (B) explicitly labeled exploratory across
all seen months. No calendar-month-specific hindsight exclusion.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd

import research_supertrend_15m_line_touch as base
import research_supertrend_15m_filter_grid as filt
import research_st_three_best_combined_portfolio as portfolio
import research_st_touch075_flip_lowvol_combination as original
import research_st_touch_flip_causal_regime_filters as htf
import research_second_green_percent_rr_scenarios as rr

OUT=Path("analysis/st_touch_flip_reduce_losing_months_20261122")
MONTHS=tuple(base.MONTHS)
YEAR_2025=MONTHS[:12]
YEAR_2026=MONTHS[12:22]
PRIORITY=("line_touch","bullish_flip")

TOUCH_FILTERS=(
  "1h_bull_di_4h_ema20",   # preexisting 17/22
  "1h_4h_above_ema20",     # preexisting 17/22
  "1h_above_ema20",
  "1h_above_ema50",
  "1h_rsi50",
  "1h_rsi55",
  "1h_bull_di",
  "1h_bull_di_and_adx20",
  "1h_above_ema20_and_adx20",
  "1h_above_ema20_and_rising",
  "1h_above_ema20_weekday",
  "1h_above_ema20_age4",
  "4h_above_ema20",
  "4h_above_ema50",
  "4h_above_ema20_and_rising",
  "4h_ema20_rising",
  "4h_adx20",
  "4h_adx25",
  "4h_rsi50",
  "4h_rsi55",
  "1h_adx20",
  "1h_adx25",
  "1h_bull_di_and_4h_bull_di",
  "weekday",
  "off"
)
FLIP_FILTERS=(
  "off",
  "1h_above_ema20",
  "1h_above_ema50",
  "1h_ema20_rising",
  "1h_rsi50",
  "1h_rsi55",
  "1h_bull_di",
  "1h_adx20",
  "1h_adx25",
  "1h_bull_di_and_adx20",
  "1h_above_ema20_and_adx20",
  "1h_above_ema20_and_rising",
  "1h_above_ema20_weekday",
  "4h_above_ema20",
  "4h_above_ema50",
  "4h_ema20_rising",
  "4h_above_ema20_and_rising",
  "4h_bull_di",
  "4h_adx20",
  "4h_adx25",
  "4h_rsi50",
  "4h_rsi55",
  "1h_4h_above_ema20",
  "1h_bull_di_4h_ema20",
  "1h_bull_di_and_4h_bull_di",
  "weekday",
  "tue_thu",
  "session_9_21"
)
assert len(TOUCH_FILTERS)==len(set(TOUCH_FILTERS))
assert len(FLIP_FILTERS)==len(set(FLIP_FILTERS))

def evaluate(trades):
    mon=trades.groupby("exit_month_ist").net_pts.sum()
    out={}
    for label,years in (
      ("y2025",YEAR_2025),
      ("y2026",YEAR_2026),
      ("all22",MONTHS),
      ("y2025_first",YEAR_2025[:6]),
      ("y2025_second",YEAR_2025[6:]),
      ("y2026_first",YEAR_2026[:6]),
      ("y2026_late",YEAR_2026[6:])):
        z=trades[trades.exit_month_ist.isin(years)]
        xs=np.array([float(mon.get(m,0.)) for m in years],dtype=float)
        out[label+"_net_pts"]=round(float(z.net_pts.sum()),2)
        out[label+"_trade_count"]=len(z)
        out[label+"_winning_months"]=int(np.sum(xs>0))
        out[label+"_losing_months"]=int(np.sum(xs<0))
        out[label+"_flat_months"]=int(np.sum(xs==0))
        out[label+"_winning_trades"]=int(z.win.sum())
        loss=float(z.loc[z.net_pts<0,"net_pts"].sum())
        profit=float(z.loc[z.net_pts>0,"net_pts"].sum())
        out[label+"_profit_factor"]=round(profit/-loss,3) if loss<0 else None
        out[label+"_worst_month"]=round(float(xs.min()),2)
    ordered=trades.sort_values("exit_idx")
    eq=np.r_[0.,np.cumsum(ordered.net_pts.to_numpy(float))]
    out["max_closed_trade_drawdown_pts"]=round(float(
      (np.maximum.accumulate(eq)-eq).max()),2)
    return out

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    rr.configure_grid()
    portfolio.SPECS=original.COHORTS
    minute,bars,files=base.load()
    super_line,super_dir=base.supertrend(bars)
    vol,atrpct,atrrel=filt.build_features(bars)
    events,stops=filt.candidate_touch_events(
        minute,bars,super_line,super_dir,vol,atrpct,atrrel)
    signal_sets=portfolio.decode_signals(
        minute,bars,super_dir,vol,atrpct,atrrel,events,stops)
    all_entries=portfolio.compute_candidates(
        minute,super_dir,stops,signal_sets)
    assert len(all_entries)==150
    flags=htf.features(bars,super_dir)
    for col in set(TOUCH_FILTERS)|set(FLIP_FILTERS):
        assert col=="off" or col in flags.columns,col
    barids=all_entries.entry_bar.to_numpy(int)
    mask={"off":np.ones(len(all_entries),dtype=bool)}
    for col in set(TOUCH_FILTERS)|set(FLIP_FILTERS):
        if col=="off":continue
        mask[col]=flags[col].to_numpy(bool)[barids]
    touch=(all_entries.strategy=="line_touch").to_numpy()
    flip=~touch
    labels={
      "original_no_new_gate":("off","off"),
      "previous_best_17mo_dmi4h":("1h_bull_di_4h_ema20","off"),
      "previous_best_17mo_1h4h":("1h_4h_above_ema20","off"),
    }
    grid=[]
    for t in TOUCH_FILTERS:
        for f in FLIP_FILTERS:
            name="t__"+t+"__f__"+f
            labels[name]=(t,f)
    rows=[]
    for name,(touchgate,flipgate) in labels.items():
        eligible=(touch&mask[touchgate])|(flip&mask[flipgate])
        sample=all_entries[eligible]
        selected,blocked=portfolio.portfolio(
            sample,("line_touch","bullish_flip"),
            PRIORITY,global_cycle_cap=True)
        row=dict(profile=name,touch_gate=touchgate,flip_gate=flipgate,
                 candidate_signals=int(len(sample)),
                 rejected_overlap=int(blocked["blocked_overlaps"]),
                 rejected_per_cycle=int(blocked["blocked_one_cycle"]),
                 **evaluate(selected))
        rows.append(row)
    tab=pd.DataFrame(rows)
    assert len(tab)==3+len(TOUCH_FILTERS)*len(FLIP_FILTERS)
    base_row=tab[tab.profile=="original_no_new_gate"].iloc[0]
    assert (base_row.y2025_net_pts,base_row.y2026_net_pts)==(10060.42,548.16)
    for p,y25,y26,m25,m26 in (
      ("previous_best_17mo_dmi4h",8176.19,4280.81,9,8),
      ("previous_best_17mo_1h4h",9560.31,3887.15,9,8)):
        v=tab.loc[tab.profile==p].iloc[0]
        assert (v.y2025_net_pts,v.y2026_net_pts,
                v.y2025_winning_months,v.y2026_winning_months)==(
                y25,y26,m25,m26),p
    tab["passes_2025_development"] = (
       (tab.y2025_net_pts>0)&
       (tab.y2025_trade_count>=30)&
       (tab.y2025_winning_months>=7)&
       (tab.y2025_first_net_pts>0)&
       (tab.y2025_second_net_pts>0))
    tab["positive_both_years"]=(
       (tab.y2025_net_pts>0)&(tab.y2026_net_pts>0))
    tab["months_positive_total"]=(
       tab.y2025_winning_months+tab.y2026_winning_months)
    tab["months_losing_total"]=(
       tab.y2025_losing_months+tab.y2026_losing_months)
    # Avoid selection of trivially inactive (flat) months as "consistency".
    tab["sufficient_activity"]=(
       (tab.y2025_trade_count>=25)&(tab.y2026_trade_count>=15)&
       (tab.y2025_winning_months+tab.y2025_losing_months>=10)&
       (tab.y2026_winning_months+tab.y2026_losing_months>=8))
    tab.to_csv(OUT/"all_gate_pair_results.csv",index=False)
    # 2025-only ranking, does not inspect 2026.
    developed=tab[tab.passes_2025_development].sort_values(
       ["y2025_winning_months","y2025_net_pts","y2025_trade_count"],
       ascending=[False,False,False])
    developed.to_csv(OUT/"ranked_2025_only_development.csv",index=False)
    # The retrospective cross-year scoreboard is deliberately LABELED
    # exploratory; this is NOT forward validated since all 22 months were
    # examined repeatedly in past research.
    explore=tab[(tab.positive_both_years)&(tab.sufficient_activity)].sort_values(
       ["months_positive_total","y2026_winning_months",
        "y2026_net_pts","y2025_net_pts"],
       ascending=[False,False,False,False])
    explore.to_csv(OUT/"retrospective_rankings_NOT_independent.csv",index=False)
    # Score candidates with adequate samples and 2026 profit on both halves
    bothhalves=tab[(tab.positive_both_years)&tab.sufficient_activity&
       (tab.y2026_first_net_pts>0)&(tab.y2026_late_net_pts>0)&
       (tab.y2025_first_net_pts>0)&(tab.y2025_second_net_pts>0)].sort_values(
       ["months_positive_total","y2026_net_pts","y2025_net_pts"],
       ascending=[False,False,False])
    bothhalves.to_csv(OUT/"profitable_all_four_time_blocks_EXPLORATORY.csv",index=False)
    focus=explore.head(5).profile.tolist()
    focus=list(dict.fromkeys(
      ["original_no_new_gate","previous_best_17mo_dmi4h",
       "previous_best_17mo_1h4h"]+focus))
    focus_rows=tab[tab.profile.isin(focus)]
    candm=[];candtr=[]
    for name in focus:
        v=labels[name]
        available=all_entries[(touch&mask[v[0]])|(flip&mask[v[1]])]
        selected,_=portfolio.portfolio(
            available,("line_touch","bullish_flip"),
            PRIORITY,global_cycle_cap=True)
        mm=portfolio.month_table(selected,minute,name)
        cc=selected.copy()
        cc["profile"]=name
        candm.append(mm)
        candtr.append(cc)
    pd.concat(candm,ignore_index=True).to_csv(
        OUT/"focus_profiles_actual_exit_monthly.csv",index=False)
    pd.concat(candtr,ignore_index=True).to_csv(
        OUT/"focus_profiles_trade_ledgers.csv.gz",index=False,compression="gzip")
    cols=["profile","touch_gate","flip_gate",
          "y2025_net_pts","y2026_net_pts",
          "y2025_winning_months","y2026_winning_months",
          "y2025_losing_months","y2026_losing_months",
          "y2025_flat_months","y2026_flat_months",
          "y2025_trade_count","y2026_trade_count",
          "y2026_first_net_pts","y2026_late_net_pts",
          "all22_net_pts","all22_trade_count",
          "max_closed_trade_drawdown_pts"]
    report=[
     "# BTCUSD ST Touch+Flip: systematic study of losing-month reduction",
     "",
     "Base: 15m ST(10,3); Line Touch SL 0.75% TP 1.5% and Flip SL",
     "3% TP 0.5%, each with its preexisting volume and ATR settings.",
     "Fixed exits and 1m OHLC stop-first replay, net after estimated",
     "trading fees GST slippage. One open position and one per ST bullish",
     "cycle. Extra entry gates use only completed higher TF candles.",
     "",
     "## Replayed baseline and strongest exploratory candidates",
     focus_rows[cols].to_markdown(index=False),
     "",
     "## 2025-only candidate selection, 2026 displayed but NEVER",
     "## consulted to select development ranking",
     developed[cols].head(20).to_markdown(index=False),
     "",
     "## Most consistent across historical 22 months, explicitly hindsight",
     explore[cols].head(30).to_markdown(index=False),
     "",
     "## Positive in both halves of both years — exploratory diagnostic",
     bothhalves[cols].head(20).to_markdown(index=False),
     "",
     "## Interpretation",
     "2026 has been repeatedly inspected (including by user) and",
     "baseline settings were chosen retrospectively. NEVER label any",
     "2026 score here as untouched out-of-sample. The pair grid tries",
     "many correlated variants, so picking the highest monthly outcome",
     "risks multiple-comparisons/data-mining bias. Independent paper",
     "trading and economic execution modeling are required.",
     "No leverage, margin liquidation, funding, order depth/latency.",
     "Points per 1 BTC-equivalent, not leveraged account PnL."
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    (OUT/"quality.json").write_text(json.dumps({
      "tested_pair_combinations":len(tab),
      "2025_dev_qualified":len(developed),
      "exploratory_positive_both_sufficient":len(explore),
      "exploratory_both_halves_positive":len(bothhalves),
      "tested_retrospective_2026_already_seen":True,
      "source_1m_archive_files":len(files),
      "same_baseline_parity":True,
      "original_stop_tp_and_ST_exit_unchanged":True,
      "entry_filters_from_last_closed_15m_1h_4h":True,
      "same_cost_model_and_one_position":True,
      "not_forward_tested":True,
      "candidate_focus":focus},indent=2)+"\n")
    print("BASELINE_PARITY_PASS",flush=True)
    print("TOTAL_FILTER_PROFILES",len(tab),flush=True)
    print("2025_SELECTED_TOP\n"+developed[cols].head(6).to_string(index=False),flush=True)
    print("EXPLORATORY_TOP\n"+explore[cols].head(12).to_string(index=False),flush=True)
    print("FOUR_BLOCKS_TOP\n"+bothhalves[cols].head(8).to_string(index=False),flush=True)
    print("SUCCESS_RETROSPECTIVE_MONTH_LOSS_STUDY",flush=True)

if __name__=="__main__":
    main()
