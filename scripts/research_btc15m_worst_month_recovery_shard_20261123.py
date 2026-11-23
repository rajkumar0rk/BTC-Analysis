#!/usr/bin/env python3
"""Parallel group of causal loss-pausing rules on unchanged BTCUSD Reclaim."""
from pathlib import Path
import os,sys,json
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parent))
import research_btc15m_worst_month_recovery_aware_20261123 as research
OUT=Path("analysis/btc15m_worst_month_recovery_aware_20261123")
def main():
    index=int(os.environ["SHARD_INDEX"]);total=int(os.environ.get("SHARD_COUNT","8"))
    assert total==8 and 0<=index<total
    selected=[(name,cfg) for i,(name,cfg) in enumerate(research.CONFIGS.items()) if i%total==index]
    assert selected
    out=OUT/f"shard_{index}"
    out.mkdir(parents=True,exist_ok=True)
    df,quality=research.read_source("BTCUSD")
    ema,stline,trend,valid=research.st_and_ema(df,research.TF)
    indicators=research.make_indicators(df)
    signals=research.make_signals(df,ema,trend,valid,"reclaim",4)[0]
    summary=[];monthly=[];trades=[]
    for name,cfg in selected:
        for path in research.PATHS:
            print("RUN",name,path,flush=True)
            row,mo,ledger=research.simulate(df,ema,stline,trend,indicators,name,cfg,signals,path)
            assert row["flip_exits"]==0 and not row["supertrend_flip_exit_enabled"]
            summary.append(row);monthly.append(mo);trades.append(ledger)
            print("RESULT",json.dumps(row,sort_keys=True),flush=True)
    pd.DataFrame(summary).to_csv(out/"summary.csv",index=False)
    pd.concat(monthly,ignore_index=True).to_csv(out/"monthly.csv",index=False)
    pd.concat(trades,ignore_index=True).to_csv(out/"trades.csv.gz",index=False,compression="gzip")
    (out/"quality.json").write_text(json.dumps({"shard":index,"count":len(summary),
        "config_names":[a for a,b in selected],"quality":quality},indent=2,default=str))
    print("SHARD_DONE",index,len(summary),flush=True)
if __name__=="__main__":main()
