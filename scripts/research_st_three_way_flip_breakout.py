#!/usr/bin/env python3
"""BTCUSD 15m ST: line-touch, bullish flip, and new flip+green breakout.

Breakout is the green 15m candle immediately after bullish flip closing above
the bullish flip candle HIGH; enter at subsequent 15m OPEN. No lookahead.
ST(10,3), filters, all 1m SL/TP replay and ST closing exit unchanged.
"""
from pathlib import Path
import json
import pandas as pd
import numpy as np

import research_supertrend_15m_line_touch as base
import research_supertrend_15m_filter_grid as filt
import research_supertrend_15m_profit_protection as protect
import research_supertrend_15m_second_green as green
import research_second_green_percent_grid as grid
import research_second_green_percent_rr_scenarios as rr

OUT=Path("analysis/st_touch_flip_breakout_three_way_20261122")
KINDS=("after_line_touch","after_bullish_flip","flip_plus_green_breakout")
DEFAULT=("vol_ge_1p0","atrpct_ge_0p20")
OTHER=("vol_off","atrpct_ge_0p40")

def confirmed_breakout(flip_entries,bars):
    highs=bars.high.to_numpy(float)
    close=bars.close.to_numpy(float)
    result=[]
    for event in flip_entries:
        cycle,third,j,mid,line=event
        third=int(third)
        if third>=2 and close[third-1]>highs[third-2]:
            result.append(event)
    return result

def highest(table):
    result=[]
    for name in KINDS:
        a=table[table.entry_type==name]
        for scope,filters in (("same_filters",DEFAULT),
                              ("atr_high_volume_off",OTHER),
                              ("all_filters",None)):
            b=a
            if filters is not None:
                b=a[(a.vol_filter==filters[0])&(a.atr_filter==filters[1])]
            for metric,mintrades in (("max_wins",1),
                                     ("max_winrate_min20",20),
                                     ("max_winrate_min50",50),
                                     ("max_net_min20",20),
                                     ("max_net_min50",50)):
                q=b[b.trades>=mintrades]
                if not len(q):continue
                if metric=="max_wins":
                    q=q.sort_values(["wins","net_pts"],ascending=[False,False])
                elif "winrate" in metric:
                    q=q.sort_values(["win_rate_pct","net_pts"],ascending=[False,False])
                else:
                    q=q.sort_values(["net_pts","profitable_months"],ascending=[False,False])
                top=q.iloc[0]
                result.append(dict(entry_type=name,scope=scope,
                    metric=metric,vol_filter=top.vol_filter,
                    atr_filter=top.atr_filter,sl_pct=top.sl_pct,
                    tp_pct=top.tp_pct,trades=int(top.trades),
                    wins=int(top.wins),losses=int(top.trades-top.wins),
                    win_rate_pct=top.win_rate_pct,net_pts=top.net_pts,
                    profitable_months=top.profitable_months,
                    losing_months=top.losing_months,
                    max_drawdown_pts=top.max_drawdown_pts))
    return pd.DataFrame(result)

def main():
    rr.configure_grid()
    OUT.mkdir(parents=True,exist_ok=True)
    minute,bars,files=base.load()
    st,trend=base.supertrend(bars)
    vol,atrpct,atrrel=filt.build_features(bars)
    all_touch,stops=filt.candidate_touch_events(
        minute,bars,st,trend,vol,atrpct,atrrel)
    op=minute.open.to_numpy(float)
    months=minute.index.tz_convert("Asia/Kolkata").strftime("%Y-%m").to_numpy()
    records=[]
    refcounts={}
    for vn,vs in filt.VOLUME.items():
        for an,ats in filt.VOLATILITY.items():
            touching=protect.select_events(all_touch,vs,ats)
            first=green.after_touch_green(touching,bars,trend,stops,op)
            flip=green.after_flip_green(bars,trend,vol,atrpct,
                                        atrrel,vs,ats,stops,op)
            breakout=confirmed_breakout(flip,bars)
            cases={"after_line_touch":first,
                   "after_bullish_flip":flip,
                   "flip_plus_green_breakout":breakout}
            if (vn,an)==DEFAULT:
                refcounts={k:sum(months[event[2]] in base.MONTHS
                                 for event in cohort)
                           for k,cohort in cases.items()}
                assert refcounts["after_line_touch"]==108,refcounts
                assert refcounts["after_bullish_flip"]==197,refcounts
            for name,entries in cases.items():
                x,_=grid.run_grid(entries,stops,minute,months,vn,an,name)
                records.extend(x)
            print("FILTER_DONE",vn,an,"rows",len(records),flush=True)

    result=pd.DataFrame(records)
    assert len(result)==3*42*len(rr.STOP_PCT)*len(rr.TARGET_PCT),len(result)
    same=result[(result.vol_filter==DEFAULT[0])&
                (result.atr_filter==DEFAULT[1])]
    previous=same[(same.sl_pct==1.0)&(same.tp_pct==1.0)]
    t=previous[previous.entry_type=="after_line_touch"].iloc[0]
    f=previous[previous.entry_type=="after_bullish_flip"].iloc[0]
    assert (int(t.wins),int(t.trades),float(t.net_pts))==(45,108,5457.49),tuple(t.values)
    assert (int(f.wins),int(f.trades),float(f.net_pts))==(83,197,-27747.24),tuple(f.values)
    top=highest(result)
    top.to_csv(OUT/"max_wins_winrate_and_profit_three_strategies.csv",index=False)
    req=pd.DataFrame(rr.ASKED,columns=["sl_pct","tp_pct"])
    comparisons=same.merge(req,on=["sl_pct","tp_pct"],validate="many_to_one")
    comparisons.to_csv(OUT/"same_filters_requested_ratios.csv",index=False)
    result.to_csv(OUT/"all_36036_fixed_percent_combinations.csv.gz",
                  compression="gzip",index=False)
    examples=comparisons[
        comparisons[["sl_pct","tp_pct"]].apply(tuple,axis=1).isin(
        [(1.,1.),(.5,1.),(.5,1.5),(.75,1.5),(1.,2.),(1.,3.),
         (2.,4.),(3.,6.)])]
    tab=top[top.scope=="same_filters"]
    columns=["entry_type","metric","sl_pct","tp_pct","trades",
             "wins","losses","win_rate_pct","net_pts",
             "profitable_months","losing_months","max_drawdown_pts"]
    lines=[
      "# BTCUSD 15M Supertrend Line Touch vs Bullish Flip vs Flip + Breakout",
      "",
      "New third variant: a bullish flip and next 15m GREEN candle with CLOSE",
      "above flip candle HIGH; market enter at third 15m candle OPEN.",
      "Same Supertrend(10,3) closing exit for all three; fixed % SL & TP",
      "on 1m, conservative stop-first OHLC ties. No profit-lock experiment",
      "in this three-way fixed risk/reward comparison. Original filters and",
      "fee model: taker 0.05% each side + GST18 and 5 BTC pts slip per side.",
      "",
      "## Same volume>=1 ATR>=0.20 filters, highest win count and rates",
      tab[columns].to_markdown(index=False),
      "",
      "## Selected ratios, same filters",
      examples[["entry_type","sl_pct","tp_pct","trades","wins",
        "win_rate_pct","net_pts","profitable_months",
        "losing_months"]].to_markdown(index=False),
      "",
      "## Other filters and highest wins",
      top[columns+["scope","vol_filter","atr_filter"]].to_markdown(index=False),
      "",
      "## Limitations",
      "No independent untouched future sample. In-sample optimized results.",
      "No model for leverage, funding, bid/ask depth or liquidation.",
      "1-BTC equivalent price points, not percent account returns.",
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(lines)+"\n")
    quality=dict(
       status="completed",original_entry_cohort_counts=refcounts,
       breakout_confirmation="next 15m GREEN close > preceding bullish flip HIGH",
       entry="open of subsequent third 15m bar",
       ST_original_exit_unchanged=True,ST_period=10,ST_mult=3,
       percent_fixed_SL_TP=True,profit_lock=False,
       full_configurations=len(result),filter_pairs=42,
       months="2025Jan to 2026Oct, entry month IST",
       fill_model="1m stop-first, 0.05% fee each side with 18% GST, 5 pt slip each side",
       liquidation_not_modeled=True)
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2)+"\n")
    print("THREE_WAY_COUNTS",refcounts,"CASES",len(result),flush=True)
    print("HIGH_WINS_SAME_FILTERS\n"+tab[columns].to_string(index=False),flush=True)
    print("EXAMPLE_RATIOS\n"+examples[["entry_type","sl_pct",
        "tp_pct","trades","wins","net_pts"]].to_string(index=False),flush=True)

if __name__=="__main__":
    main()
