#!/usr/bin/env python3
"""Follow-up audit: do alternative initial stops repair EMA20 Reclaim losing months?

Previously selected signal filters, three validated profit-lock ladders, two
intrabar path models, 11 different initial SL levels. Preserve each exact
Reclaim entry signal and complete next-hour 1m trigger. All signal gates
causal (completed H1 candle); stop amendments modeled immediately on 1m path.
2026 used for analysis earlier: results exploratory, not pristine OOS.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from research_st_ema20_initial_sl_grid_20261122 import eng,prepare_entries,run,summarize,PATHS
from research_st_ema20_reclaim_loss_months_20261122 import (
  indicator_features,signal_table,LADDERS,MONTHS
)

OUT=Path("analysis/st_ema20_reclaim_loss_month_stop_sweep_20261122")
STOPS=(0.75,1.,1.25,1.5,1.75,2.,2.25,2.5,2.75,3.,4.)
CASES={
 "baseline":lambda f: np.ones(len(f),bool),
 "ema_gap_le_0p75":lambda f: np.asarray(f.ema_gap_pct<=.75,bool),
 "hourly_range_le_2atr":lambda f: np.asarray(f.hourly_range_atr<=2,bool),
 "ema_gap_le_0p75__slope_ge_minus0p2":lambda f: np.asarray(
    (f.ema_gap_pct<=.75)&(f.ema_slope_pct>=-.2),bool),
 "adx_ge_15__slope_le_0p1":lambda f: np.asarray(
    (f.adx14>=15)&(f.ema_slope_pct<=.1),bool),
 "adx_le_30__rsi_le_60__slope_ge_minus0p2":lambda f: np.asarray(
    (f.adx14<=30)&(f.dir_rsi14<=60)&(f.ema_slope_pct>=-.2),bool),
 "adx_le_30__slope_ge_minus0p2__volume_le_4":lambda f: np.asarray(
    (f.adx14<=30)&(f.ema_slope_pct>=-.2)&(f.volume_ratio<=4.),bool),
 "ema_gap_le_0p75__slope_ge_minus0p2__range_le_2atr":lambda f: np.asarray(
    (f.ema_gap_pct<=.75)&(f.ema_slope_pct>=-.2)&(f.hourly_range_atr<=2.),bool)
}

def max_point_adverse(t):
    if t.empty:return 0.
    return round(float(t.max_adverse_points.max()),2)

def main():
    engine=eng()
    m,h,files=engine.load()
    h=indicator_features(engine.features(h))
    entries=prepare_entries(engine,m,h,"reclaim")
    assert len(entries)==62
    f=signal_table(entries,h)
    masks={k:func(f) for k,func in CASES.items()}
    assert masks["baseline"].sum()==62
    stats=[];months=[];selected_trades=[]
    for stop in STOPS:
        for ladder_id,levels in LADDERS.items():
            for path in PATHS:
                t=run(engine,m,h,entries,"reclaim",path,"initial stop","pct",stop,
                      ladder_override=levels)
                assert len(t)==62
                for name,mask in masks.items():
                    v=t.loc[mask].copy()
                    score,mon=summarize(v,"reclaim",f"{stop:g}%",path)
                    score.update(filter_name=name,ladder=ladder_id,
                        initial_sl_pct=stop,selected_signals=int(mask.sum()),
                        max_trade_adverse_points=max_point_adverse(v))
                    mon["filter_name"]=name;mon["ladder"]=ladder_id
                    mon["initial_sl_pct"]=stop
                    stats.append(score)
                    months.append(mon)
                    if (name=="baseline" and stop==2 and ladder_id=="L235") or (
                        stop==2 and (name,ladder_id) in (
                         ("ema_gap_le_0p75","L235"),
                         ("adx_ge_15__slope_le_0p1","L175235"),
                         ("adx_le_30__rsi_le_60__slope_ge_minus0p2","L235"))):
                        v["filter_name"]=name;v["ladder"]=ladder_id
                        v["initial_sl_pct"]=stop;selected_trades.append(v)
                if stop==2 and ladder_id=="L235" and masks["baseline"].all():
                    expected={"open_high_low_close":(14,13.522615),
                              "open_low_high_close":(15,13.746743)}[path]
                    row=stats[-len(masks)]
                    assert row["profitable_months"]==expected[0],(path,row)
                    assert abs(row["total_net_usd"]-expected[1])<.00001,(path,row)
        print("Finished initial stop",stop,flush=True)

    df=pd.DataFrame(stats);mth=pd.concat(months,ignore_index=True)
    pairs=[]
    for (name,ladder,stop),group in df.groupby(["filter_name","ladder","initial_sl_pct"]):
        assert len(group)==2,(name,ladder,stop)
        pairs.append(dict(filter_name=name,ladder=ladder,initial_sl_pct=stop,
           selected_signals=int(group.selected_signals.min()),
           profitable_months_min=int(group.profitable_months.min()),
           profitable_months_max=int(group.profitable_months.max()),
           profitable2025_min=int(group.profitable_2025.min()),
           profitable2026_min=int(group.profitable_2026.min()),
           losing_months_max=int(group.losing_months.max()),
           flat_months_max=int(group.flat_months.max()),
           net_min_usd=float(group.total_net_usd.min()),
           net_max_usd=float(group.total_net_usd.max()),
           net25_min=float(group.net_2025.min()),
           net25_max=float(group.net_2025.max()),
           net26_min=float(group.net_2026.min()),
           net26_max=float(group.net_2026.max()),
           trades_min=int(group.trades.min()),
           stop_exits_max=int(group.stopped_trades.max()),
           closed_equity_dd_pct_worst=float(group.max_realized_dd_pct.max()),
           max_trade_adverse_points=float(group.max_trade_adverse_points.max()),
           positive_both_years=bool((group.net_2025>0).all() and (group.net_2026>0).all())))
    pp=pd.DataFrame(pairs)
    pp=pp.sort_values(["positive_both_years","profitable_months_min","net_min_usd"],
                      ascending=[False,False,False])
    best=pp[(pp.positive_both_years)&(pp.net_min_usd>0)]
    top=best.sort_values(["profitable_months_min","net_min_usd"],ascending=False).head(30)
    chrono=pp[(pp.trades_min>=22)].sort_values(
       ["profitable2025_min","net25_min"],ascending=False).head(25)
    previous=pp[(pp.initial_sl_pct==2)&
      (((pp.filter_name=="baseline")&(pp.ladder=="L235"))|
       ((pp.filter_name=="ema_gap_le_0p75")&(pp.ladder=="L235"))|
       ((pp.filter_name=="adx_ge_15__slope_le_0p1")&(pp.ladder=="L175235")))]
    OUT.mkdir(parents=True,exist_ok=True)
    df.to_csv(OUT/"path_results.csv",index=False)
    pp.to_csv(OUT/"paired_comparison.csv",index=False)
    top.to_csv(OUT/"top_30_both_years.csv",index=False)
    chrono.to_csv(OUT/"top_2025_ranked_2026_diagnostic.csv",index=False)
    mth.to_csv(OUT/"monthly_all_configs.csv",index=False)
    pd.concat(selected_trades,ignore_index=True).to_csv(
        OUT/"reference_trade_audit.csv",index=False)
    # Compact monthly view for prior controls plus current all-history winner.
    take=list(zip(previous.filter_name,previous.ladder,previous.initial_sl_pct))
    if len(top):
        winner=top.iloc[0]
        take.append((winner.filter_name,winner.ladder,winner.initial_sl_pct))
    view=pd.concat([mth[(mth.filter_name==a)&(mth.ladder==b)&
                       (mth.initial_sl_pct==c)] for a,b,c in take],ignore_index=True)
    view.to_csv(OUT/"selected_monthly.csv",index=False)
    report=(
        "# EMA20 Reclaim initial-SL and loss-month robustness\n\n"
        f"Tested {len(STOPS)} entry-relative initial stops, {len(LADDERS)} stepped profit locks, "
        f"{len(CASES)} causal filter conditions and 2 simulated intraminute 1m OHLC paths "
        f"({len(df)} path-level scenarios). 22 completed months 2025-01 to 2026-10.\n\n"
        "## Previously identified filters at 2% initial SL\n\n"
        +previous.to_markdown(index=False)+"\n\n"
        "## Best two-year-positive historical results, ALL scenarios\n\n"
        +top.to_markdown(index=False)+"\n\n"
        "## Highest 2025-only training scores (2026 columns are diagnostic)\n\n"
        +chrono.to_markdown(index=False)+"\n\n"
        "## Risks\n\n"
        "All combinations are historical/in-sample explorations. 2026 was used in prior research, "
        "so it is NOT a pristine untouched holdout. "
        "Closed-equity DD excludes floating exposure. "
        "No funding, liquidation, exchange stop amendment delay, or precise tick-level intraminute ordering.\n")
    (OUT/"RESEARCH_REPORT.md").write_text(report)
    (OUT/"quality.json").write_text(json.dumps({
       "source":"Delta Exchange India BTCUSD 1m OHLC",
       "month_range":[MONTHS[0],MONTHS[-1]],
       "initial_sl_grid_pct":STOPS,
       "profit_lock_ladders":LADDERS,
       "causal_filter_names":list(CASES),
       "total_scenarios":len(df),
       "entry_count":62,
       "validated_baseline":"2% SL, 2-3-5 profit lock exactly matched",
       "limit":"historical optimization, not true forward testing"
    },indent=2)+"\n")
    print("SUCCESS",OUT,flush=True)
    print("BEST",top.head(10).to_string(index=False),flush=True)
    print("BASELINES",previous.to_string(index=False),flush=True)

if __name__=="__main__":
    main()
