#!/usr/bin/env python3
"""Two- and three-tier causal monthly loss sizing on verified BTC 15m Reclaim.
Historical research only; no increased leverage, look-ahead, or altered entry/exit.
"""
import os,sys
from pathlib import Path
import numpy as np
import pandas as pd
import research_btc15m_adaptive_equity_risk_20261123 as risk
base=risk.base
OUT=Path("analysis/btc15m_tiered_loss_risk_20261123")
CONFIGS=[]
for s2 in (.45,.55,.65,.75,.85,.95):
    for s3 in (.10,.20,.30,.40,.50):
        if s3>s2: continue
        for s4 in (s3, min(.10,s3)):
            # The two modes coincide when s3=0.10.
            if s3==s4 and s3==.10 and len([1 for q in (s3,min(.10,s3)) if q==s3])>1 and False: pass
            key=f"T{int(s2*100):02d}_{int(s3*100):02d}_{int(s4*100):02d}"
            if key not in dict(CONFIGS): CONFIGS.append((key,(s2,s3,s4)))
CONFIG_MAP=dict(CONFIGS)

def layered_size(name,cash,eq_high,losses,month_ref,ind,j,consec):
    if "__SZ_" not in name: return 1.0
    key=name.split("__SZ_",1)[1].split("_SL300",1)[0]
    s2,s3,s4=CONFIG_MAP[key]
    if losses>=4: return s4
    if losses>=3: return s3
    if losses>=2: return s2
    return 1.0

def run(index,count):
    assert 0<=index<count
    risk.size_multiplier=layered_size
    sim=risk.make_size_sim()
    df,quality=base.read_source("BTCUSD")
    ema,stline,trend,valid=base.st_and_ema(df,base.TF)
    ind=base.make_indicators(df)
    signals=base.make_signals(df,ema,trend,valid,"reclaim",4)[0]
    for path in base.PATHS:
        row,monthly,ledger=sim(df,ema,stline,trend,ind,risk.REFERENCE,risk.BASECFG,signals,path)
        risk.verify_baseline(row)
    summary=[];months=[]
    for idx,(key,(s2,s3,s4)) in enumerate(CONFIGS):
        if idx%count!=index: continue
        name=f"reclaim_NOFLIP_LATE825_MLOSS5__SZ_{key}_SL300_TP3R"
        for path in base.PATHS:
            row,mon,trades=sim(df,ema,stline,trend,ind,name,risk.BASECFG,signals,path)
            row.update(size_mode=key,loss2_size=s2,loss3_size=s3,loss4_size=s4)
            summary.append(row);mon["size_mode"]=key;months.append(mon)
            print(key,path,"net",row["net_return_pct"],"dd",row["max_floating_drawdown_pct"],"months",row["profitable_months"],flush=True)
    p=OUT/f"shard_{index}"
    p.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(summary).to_csv(p/"summary.csv",index=False)
    pd.concat(months,ignore_index=True).to_csv(p/"monthly.csv",index=False)
    print("COMPLETE",index,len(summary),flush=True)

def aggregate(n):
    ss=[];mm=[]
    for j in range(n):
        ss.append(pd.read_csv(OUT/f"shard_{j}"/"summary.csv"))
        mm.append(pd.read_csv(OUT/f"shard_{j}"/"monthly.csv"))
    s=pd.concat(ss,ignore_index=True)
    m=pd.concat(mm,ignore_index=True)
    s.to_csv(OUT/"summary.csv",index=False)
    m.to_csv(OUT/"monthly.csv",index=False)
    score=s.groupby("size_mode").agg(
        s2=("loss2_size","first"),s3=("loss3_size","first"),s4=("loss4_size","first"),
        worst_path_drawdown=("max_floating_drawdown_pct","max"),
        worst_path_return=("net_return_pct","min"),
        min_winning_months=("profitable_months","min"),
        ntrades=("trades","min")).reset_index()
    score["vs_original"]=(score.worst_path_drawdown<19.948)&(score.worst_path_return>=151.787-.01)&(score.min_winning_months>=18)
    score["vs_172_16"]=(score.worst_path_drawdown<16.662)&(score.worst_path_return>=172.101-.01)&(score.min_winning_months>=18)
    score["target_12"]=(score.worst_path_drawdown<12)&(score.worst_path_return>=151.787-.01)&(score.min_winning_months>=18)
    score["target_10"]=(score.worst_path_drawdown<10)&(score.worst_path_return>=151.787-.01)&(score.min_winning_months>=18)
    score.sort_values(["worst_path_drawdown","worst_path_return"],ascending=[True,False]).to_csv(OUT/"ranked.csv",index=False)
    qualified=score[score.vs_original].sort_values(["worst_path_drawdown","worst_path_return"],ascending=[True,False])
    strict=score[score.vs_172_16].sort_values(["worst_path_drawdown","worst_path_return"],ascending=[True,False])
    lines=["# BTCUSD 15M Reclaim — tiered loss-streak sizing",
      "",f"Tested {len(score)} loss2/loss3/loss4 sizing schedules, both 1-minute OHLC paths, Jan 2025–Oct 2026.",
      "Original 15M ST10/3 + EMA20 reclaim, one trade per cycle, 3% SL, 9% TP, +8.25% profit trigger/0% lock, five losses monthly pause; source baseline reconciled exactly.",
      "Fees and 18% GST plus 0.02% slippage per side included; funding, live spread and actual execution NOT included.",
      "All size multipliers <= 1, so no extra leverage. History is heavily in-sample (do not interpret selected configurations as out-of-sample performance).",
      "",f"Models with lower than 19.948% DD, >=151.787% return, and >=18 positive months: {len(qualified)}",
      f"Models beating both +172.101% profit and 16.662% drawdown: {len(strict)}",
      f"Models with DD <12% preserving original return/months: {int(score.target_12.sum())}; <10%: {int(score.target_10.sum())}",
      "", "## Strongest drawdown reduction preserving original net profit/month count",
      qualified.head(30).to_markdown(index=False) if len(qualified) else "None.",
      "","## Strictly better than +172.101%/16.662%",
      strict.head(25).to_markdown(index=False) if len(strict) else "None.",
      "","## Lowest drawdown regardless of profit preservation",
      score.sort_values(["worst_path_drawdown","worst_path_return"],ascending=[True,False]).head(20).to_markdown(index=False),
      "", "## Limitations", "Floating peak-to-trough drawdown includes intratrade marks. Requires prospective validation, funding and real order execution stress test."]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(lines)+"\n")
    print("\n".join(lines[:11]),flush=True)

if __name__=="__main__":
    if len(sys.argv)>1 and sys.argv[1]=="aggregate": aggregate(int(os.environ.get("SHARD_COUNT","8")))
    else: run(int(os.environ.get("SHARD_INDEX","0")),int(os.environ.get("SHARD_COUNT","8")))
