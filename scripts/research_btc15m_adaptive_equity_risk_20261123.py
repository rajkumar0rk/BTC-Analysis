#!/usr/bin/env python3
"""Faithful BTCUSD 15m Reclaim equity-risk sensitivity, 2025-01 through 2026-10.

Uses the verified original research simulator with a research-only replacement of
the single position-sizing expression. Signal generation, entry timing, fee/GST,
slippage, monthly loss-pause, 3% SL, 9% TP and 8.25% protection are unchanged.
Risk multipliers > 1 represent LEVERAGE and are separately labeled.
All 22 months are highly in-sample; no claims of out-of-sample success.
"""
import os,inspect,sys
from pathlib import Path
import pandas as pd
import numpy as np
import research_btc15m_worst_month_loss_pause_20261123 as base

OUT=Path("analysis/btc15m_adaptive_equity_risk_20261123")
REFERENCE="reclaim_NOFLIP_LATE825_MLOSS5_SL300_TP3R"
BASECFG=(4,"any","PCT",3,3.0,"LATE:8.25:0:2:0.5")
# Each mode is (kind, threshold, floor_size, cap_size): cap >1 = leverage.
MODELS=[
 ("DD03H",("dd",3,.5,1.)),("DD05H",("dd",5,.5,1.)),
 ("DD08H",("dd",8,.5,1.)),("DD10H",("dd",10,.5,1.)),
 ("DD12H",("dd",12,.5,1.)),("DD15H",("dd",15,.5,1.)),
 ("DD03Q",("dd",3,.75,1.)),("DD05Q",("dd",5,.75,1.)),
 ("DD08Q",("dd",8,.75,1.)),("DD10Q",("dd",10,.75,1.)),
 ("DD05F",("dd",5,.25,1.)),("DD08F",("dd",8,.25,1.)),
 ("ML02H",("loss",2,.5,1.)),("ML03H",("loss",3,.5,1.)),
 ("ML04H",("loss",4,.5,1.)),("ML02Q",("loss",2,.75,1.)),
 ("MM03H",("month",3,.5,1.)),("MM05H",("month",5,.5,1.)),
 ("MM07H",("month",7,.5,1.)),
 ("ATR03H",("atr",.3,.5,1.)),("ATR04H",("atr",.4,.5,1.)),
 ("ATR05H",("atr",.5,.5,1.)),
 ("DD05B12",("boost",5,.5,1.2)),("DD08B12",("boost",8,.5,1.2)),
 ("DD05B15",("boost",5,.5,1.5)),("DD08B15",("boost",8,.5,1.5)),
 ("DD10B15",("boost",10,.5,1.5)),("DD05B20",("boost",5,.5,2.0)),
 ("ATR03B15",("atr",.3,.5,1.5)),("ATR04B15",("atr",.4,.5,1.5)),
 ("MLOSS3B15",("lossboost",3,.5,1.5)),("MLOSS4B15",("lossboost",4,.5,1.5)),
 ("DD05B13",("boost",5,.75,1.3)),("DD08B13",("boost",8,.75,1.3)),
 ("DD05B18",("boost",5,.75,1.8)),("DD08B18",("boost",8,.75,1.8)),
 ("DD05B12Q",("boost",5,.75,1.2)),("DD08B12Q",("boost",8,.75,1.2))
]
MODEL_DICT=dict(MODELS)

def size_multiplier(name,cash,peak,losses,month_ref,ind,j,consec):
    if "__SZ_" not in name: return 1.0
    key=name.split("__SZ_",1)[1].split("_SL300",1)[0]
    kind,trigger,low,high=MODEL_DICT[key]
    high=max(low,high)
    dd=100*max(0,peak-cash)/max(peak,1e-9)
    month_dd=100*max(0,month_ref-cash)/max(month_ref,1e-9)
    if kind=="dd": return low if dd>=trigger else 1.
    if kind=="loss": return low if losses>=trigger else 1.
    if kind=="month": return low if month_dd>=trigger else 1.
    if kind=="atr":
        bar_atr_pct=100*float(ind["ATR"][j])/float(ind["C"][j])
        return float(np.clip(trigger/max(1e-10,bar_atr_pct),low,high))
    if kind=="boost": return low if dd>=trigger else high
    if kind=="lossboost": return low if losses>=trigger else high
    raise RuntimeError(kind)

def verify_baseline(x):
    if not (int(x["trades"])==72 and abs(float(x["net_return_pct"])-151.787)<.02 and
            abs(float(x["max_floating_drawdown_pct"])-19.948)<.02 and
            int(x["profitable_months"])==18):
        raise RuntimeError(f"ORIGINAL SIMULATOR NOT REPRODUCED: {x!r}")

def make_size_sim():
    source=inspect.getsource(base.simulate)
    old="qty=cash/entry"
    if source.count(old)!=1:
        raise RuntimeError("Cannot verify single original sizing operation")
    source=source.replace(old, """qty=(cash/entry)*size_multiplier(name,cash,eq_high,losses_this_month,month_reference,ind,j,consecutive_losses)""")
    namespace=dict(base.__dict__)
    namespace["size_multiplier"]=size_multiplier
    exec(compile(source,"<faithful-sim-with-risk-weight>","exec"),namespace)
    return namespace["simulate"]

def shard(index,count):
    assert 0<=index<count
    OUT.mkdir(parents=True,exist_ok=True)
    sim=make_size_sim()
    df,quality=base.read_source("BTCUSD")
    ema,stline,trend,valid=base.st_and_ema(df,base.TF)
    ind=base.make_indicators(df)
    signals=base.make_signals(df,ema,trend,valid,"reclaim",4)[0]
    controls=[]
    for path in base.PATHS:
        row,monthly,ledger=sim(df,ema,stline,trend,ind,REFERENCE,BASECFG,signals,path)
        verify_baseline(row)
        controls.append(row)
    rows=[];months=[]
    for i,(key,cfg) in enumerate(MODELS):
        if i%count!=index: continue
        name=f"reclaim_NOFLIP_LATE825_MLOSS5__SZ_{key}_SL300_TP3R"
        for path in base.PATHS:
            row,mon,trades=sim(df,ema,stline,trend,ind,name,BASECFG,signals,path)
            row["size_mode"]=key;row["max_size_multiplier"]=cfg[3]
            row["risk_family"]=cfg[0]
            rows.append(row)
            mon["size_mode"]=key
            mon["max_size_multiplier"]=cfg[3]
            months.append(mon)
            print("RESULT",key,path,row["net_return_pct"],row["max_floating_drawdown_pct"],row["profitable_months"],flush=True)
    p=OUT/f"shard_{index}"
    p.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(rows).to_csv(p/"summary.csv",index=False)
    pd.concat(months,ignore_index=True).to_csv(p/"monthly.csv",index=False)
    (p/"status.txt").write_text(f"baseline verified in two OHLC paths; {len(rows)} model/path runs.\n")
    print("SHARD COMPLETED",index,len(rows),flush=True)

def aggregate(count):
    sums=[];months=[]
    for j in range(count):
        p=OUT/f"shard_{j}"
        sums.append(pd.read_csv(p/"summary.csv"))
        months.append(pd.read_csv(p/"monthly.csv"))
    s=pd.concat(sums,ignore_index=True)
    m=pd.concat(months,ignore_index=True)
    s.to_csv(OUT/"summary.csv",index=False)
    m.to_csv(OUT/"monthly.csv",index=False)
    # Conservative O-H-L-C and O-L-H-C each must qualify.
    grouped=s.groupby("size_mode").agg(
        worst_dd=("max_floating_drawdown_pct","max"),
        min_profit=("net_return_pct","min"),
        min_positive_months=("profitable_months","min"),
        max_size=("max_size_multiplier","max"),
        min_trades=("trades","min"),max_trades=("trades","max")
    ).reset_index()
    grouped["qualifies_profit_and_months"]=(grouped.min_profit>=151.787-.01)&(grouped.min_positive_months>=18)
    grouped["drawdown_better"]=grouped.worst_dd<19.948-.001
    grouped["reaches_target_12pct"]=grouped.worst_dd<12.
    grouped["reaches_target_10pct"]=grouped.worst_dd<10.
    grouped["all_criteria"]=grouped.qualifies_profit_and_months & grouped.drawdown_better
    grouped.sort_values(["worst_dd","min_profit"],ascending=[True,False]).to_csv(OUT/"ranked.csv",index=False)
    fair=grouped.loc[grouped.max_size<=1.]
    leverage=grouped.loc[grouped.max_size>1.]
    qualified=grouped.loc[grouped.all_criteria]
    lines=[
      "# BTCUSD 15M Reclaim — adaptive sizing / drawdown search",
      "",
      "This research varies **position sizing only** in the original proven engine, not signals/exits.",
      "Original 5-losses-per-month pause, +8.25% activation / 0% lock, 3% SL/9% TP remain.",
      "Jan2025–Oct2026, 22 IST calendar months, 1-minute price-path test; net includes taker fees +18% GST and 0.02% slippage per side; funding excluded.",
      "**History is thoroughly in-sample; optimizing thresholds across it is not prospective evidence.**",
      "IMPORTANT: models with size multiplier > 1 use additional leverage; they should NOT be directly considered a same-risk replacement.",
      "",
      "## Baseline (re-verified in each shard and path)",
      "72 trades, +151.787% net, 18/22 profitable months, maximum floating DD 19.948%.",
      "",
      f"## Counts: {len(grouped)} models",
      f"Qualified strictly (net >=151.787%, >=18 profitable months, DD <19.948%): {len(qualified)}.",
      f"Of those with <=1x position sizing: {len(qualified.loc[qualified.max_size<=1.])}.",
      f"Of those reaching <=12% DD: {int(((grouped.worst_dd<=12)&grouped.qualifies_profit_and_months).sum())}.",
      "",
      "## Strict 1x-max sizing models (best DD first)",
      fair.sort_values(["worst_dd","min_profit"],ascending=[True,False]).head(15).to_markdown(index=False),
      "",
      "## Up to 2x leveraged profiles (separate risk category)",
      leverage.sort_values(["worst_dd","min_profit"],ascending=[True,False]).head(15).to_markdown(index=False),
      "",
      "## Qualified on all three conditions",
      qualified.sort_values(["worst_dd","min_profit"],ascending=[True,False]).to_markdown(index=False) if len(qualified) else "No qualifying model found.",
      "",
      "## Audit notes",
      "All strict comparisons are on *max intratrade/floating equity drawdown*, not just closed-trade peaks.",
      "Stop execution modeled via 1-minute OHLC path alternatives; real fill/gap/funding effects can be worse.",
      "None of the results implies future performance."
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(lines)+"\n")
    print("\n".join(lines[:17]),flush=True)

if __name__=="__main__":
    if len(sys.argv)>1 and sys.argv[1]=="aggregate":
        aggregate(int(os.environ.get("SHARD_COUNT","8")))
    else:
        shard(int(os.environ.get("SHARD_INDEX","0")),int(os.environ.get("SHARD_COUNT","8")))
