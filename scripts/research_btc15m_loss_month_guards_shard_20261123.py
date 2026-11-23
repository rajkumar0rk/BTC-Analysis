#!/usr/bin/env python3
"""Shard a read-only replay of fixed BTC 15m loss-month overlays."""
import os,json,sys
from pathlib import Path
import pandas as pd
sys.path.insert(0,str(Path(__file__).parent))
import research_btc15m_loss_month_guards_20261123 as lab
OUT=Path("analysis/btc15m_loss_month_guards_parallel_20261123")
def main():
    shard=int(os.environ["SHARD_INDEX"])
    total=int(os.environ.get("SHARD_COUNT","7"))
    assert 0<=shard<total
    cfgs=[(name,cfg) for i,(name,cfg) in enumerate(lab.CONFIGS.items()) if i%total==shard]
    assert cfgs
    out=OUT/f"shard_{shard}"
    out.mkdir(parents=True,exist_ok=True)
    df,quality=lab.read_source("BTCUSD")
    ema,stline,trend,valid=lab.st_and_ema(df,lab.TF)
    ind=lab.make_indicators(df)
    signals=lab.make_signals(df,ema,trend,valid,"reclaim",4)[0]
    results=[];monthly=[];trades=[]
    for name,cfg in cfgs:
        for path in lab.PATHS:
            print("RUN",name,path,flush=True)
            r,mon,ledger=lab.simulate(df,ema,stline,trend,ind,name,cfg,signals,path)
            assert r["flip_exits"]==0 and not r["supertrend_flip_exit_enabled"]
            results.append(r);monthly.append(mon);trades.append(ledger)
            print("RESULT",json.dumps(r,sort_keys=True),flush=True)
    pd.DataFrame(results).to_csv(out/"summary.csv",index=False)
    pd.concat(monthly,ignore_index=True).to_csv(out/"monthly.csv",index=False)
    pd.concat(trades,ignore_index=True).to_csv(out/"trades.csv.gz",index=False,compression="gzip")
    (out/"quality.json").write_text(json.dumps(dict(shard=shard,shard_count=total,
       models=len(cfgs),results=len(results),configs=[x[0] for x in cfgs],BTCUSD=quality),default=str,indent=2))
    print("SHARD_DONE",shard,len(results),flush=True)
if __name__=="__main__":main()
