#!/usr/bin/env python3
"""ATR-minimum threshold neighborhood stress test (in-sample sensitivity).
Original BTCUSD 15m ST/EMA20 reclaim, original 1m price replay, fee/GST/slip.
No 1h signal. Historical 22 months heavily researched; not forward validation.
"""
import os,sys
from pathlib import Path
import pandas as pd
import research_btc15m_regime_entry_dd_20261123 as entry
base=entry.base
OUT=Path("analysis/btc15m_atr_threshold_stability_20261123")
ORIG_TIER=entry.tiered_size
ORIG_FILTER=entry.market_filter
THRESHOLDS=[.16,.165,.17,.175,.18,.185,.19,.195,.20,.205,.21,.215,.22,.225,.23,.24,.25]
SIZES=[.70,.75,.775,.80,.825,.85,.875,.90,1.0]
TIER="T65_30_10"

def stress_filter(name,side,j,ema,ind):
    if name.startswith("ATR_FINE_"):
        point=int(name.split("ATR_FINE_",1)[1])/1000.0
        return entry.CACHE["atr_pct"][j]>=point
    return ORIG_FILTER(name,side,j,ema,ind)

def stress_size(name,losses):
    factor=int(name.split("__U_",1)[1].split("__SZ_",1)[0])/1000.0
    return factor*ORIG_TIER(name,losses)

def run(i,n):
    entry.market_filter=stress_filter
    entry.tiered_size=stress_size
    sim=entry.modified_simulator()
    df,quality=base.read_source("BTCUSD")
    ema,stline,trend,valid=base.st_and_ema(df,base.TF)
    ind=base.make_indicators(df)
    entry.enrich(df,ind,ema)
    signals=base.make_signals(df,ema,trend,valid,"reclaim",4)[0]
    control="reclaim_NOFLIP_LATE825_MLOSS5__U_1000__SZ_T65_30_10_SL300_TP3R"
    cfg=(4,"ATR_FINE_200","PCT",3,3.0,"LATE:8.25:0:2:0.5")
    for path in base.PATHS:
        row,_,_=sim(df,ema,stline,trend,ind,control,cfg,signals,path)
        assert abs(row["net_return_pct"]-229.037)<.02 and abs(row["max_floating_drawdown_pct"]-14.740)<.02 and row["profitable_months"]==18 and row["trades"]==71,row
    combos=[(t,s) for t in THRESHOLDS for s in SIZES]
    rows=[];monthly=[]
    for k,(threshold,size) in enumerate(combos):
        if k%n!=i:continue
        threshold_code=int(round(threshold*1000))
        size_code=int(round(size*1000))
        name=f"reclaim_NOFLIP_LATE825_MLOSS5__U_{size_code}__SZ_{TIER}_SL300_TP3R"
        cf=(4,f"ATR_FINE_{threshold_code}","PCT",3,3.0,"LATE:8.25:0:2:0.5")
        for path in base.PATHS:
            r,m,trades=sim(df,ema,stline,trend,ind,name,cf,signals,path)
            r.update(threshold_pct=threshold,global_size=size)
            m["threshold_pct"]=threshold;m["global_size"]=size
            rows.append(r);monthly.append(m)
            print(f"{threshold:.3f} {size:.3f} {path}: return {r['net_return_pct']} dd {r['max_floating_drawdown_pct']} months {r['profitable_months']}",flush=True)
    p=OUT/f"shard_{i}"
    p.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(rows).to_csv(p/"summary.csv",index=False)
    pd.concat(monthly,ignore_index=True).to_csv(p/"months.csv",index=False)
    print("SHARD_DONE",i,len(rows),flush=True)

def aggregate(n):
    s=pd.concat([pd.read_csv(OUT/f"shard_{i}"/"summary.csv") for i in range(n)],ignore_index=True)
    m=pd.concat([pd.read_csv(OUT/f"shard_{i}"/"months.csv") for i in range(n)],ignore_index=True)
    s.to_csv(OUT/"summary.csv",index=False)
    m.to_csv(OUT/"months.csv",index=False)
    score=s.groupby(["threshold_pct","global_size"]).agg(
        worst_path_dd=("max_floating_drawdown_pct","max"),
        worst_path_profit=("net_return_pct","min"),
        min_profitable_months=("profitable_months","min"),
        ntrades=("trades","min")).reset_index()
    score["passes_target12"]= (score.worst_path_dd<12)&(score.worst_path_profit>=162.964-.01)&(score.min_profitable_months>=18)
    score["passes_original"]= (score.worst_path_dd<14.740-.001)&(score.worst_path_profit>=162.964-.01)&(score.min_profitable_months>=18)
    score.sort_values(["worst_path_dd","worst_path_profit"],ascending=[True,False]).to_csv(OUT/"ranked.csv",index=False)
    target=score[score.passes_target12].sort_values(["worst_path_dd","worst_path_profit"],ascending=[True,False])
    pass_=score[score.passes_original].sort_values(["worst_path_dd","worst_path_profit"],ascending=[True,False])
    summary=score.groupby("threshold_pct").agg(
        best_dd=("worst_path_dd","min"),
        max_net=("worst_path_profit","max"),
        best_positive_months=("min_profitable_months","max"),
        count_pass_12=("passes_target12","sum")).reset_index()
    summary.to_csv(OUT/"threshold_robustness.csv",index=False)
    lines=["# BTCUSD 15m — ATR threshold sensitivity around 0.20%",
      "",
      f"{len(score)} threshold × fractional-exposure variants; two original 1m OHLC price path assumptions; 22 IST months Jan2025–Oct2026.",
      "Source comparator verified each shard: ATR>=0.20%, +229.037% return, 14.740% max floating DD, 18 profitable months /71 trades.",
      "Current target: DD <12%, net >=+162.964%, >=18/22 positive months, never >1x position sizing.",
      "Original 15M ST/EMA20 reclaim, SL3%, TP9%, +8.25%/BE protection, five-loss month guard, tiered post-loss sizes all unchanged.",
      "Fees 0.05% taker each side+18% GST, 0.02% per-side adverse price slippage modeled; real funding, spread and liquidation unmodeled.",
      "**In-sample parameter sensitivity study, not independent validation or a forward performance expectation.**",
      "",
      f"Passing threshold-size pairs below 12% DD: {len(target)}",
      f"Passing below 14.74% DD with net >=+162.964%: {len(pass_)}",
      "",
      "## ATR threshold robustness (filter applies at completed 15M reclaim signal)",
      summary.to_markdown(index=False),
      "",
      "## Below-12% qualifying combinations",
      target.head(30).to_markdown(index=False) if len(target) else "None.",
      "",
      "## Lowest drawdown while preserving original target",
      pass_.head(30).to_markdown(index=False) if len(pass_) else "None.",
      "", "## Notes",
      "Profit/drawdown may be driven by a small number of excluded historical entries; tiny threshold changes are a critical overfit check.",
      "No claim of production readiness; test forward, include funding/order-book execution/latency before live orders."
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(lines)+"\n")
    print("\n".join(lines[:11]),flush=True)
if __name__=="__main__":
    n=int(os.environ.get("SHARD_COUNT","8"))
    if len(sys.argv)>1 and sys.argv[1]=="aggregate":aggregate(n)
    else:run(int(os.environ.get("SHARD_INDEX","0")),n)
