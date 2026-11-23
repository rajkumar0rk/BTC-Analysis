#!/usr/bin/env python3
"""Parallel shard of BTCUSD 15M no-ST-flip-exit percentage SL backtest.
Every configuration is assigned to one shard deterministically and both 1m
price-path assumptions are replayed. Same simulator as full source script."""
import os,json
from pathlib import Path
import pandas as pd
import research_btc15m_no_st_flip_exit_pct_sl_20261123 as lab

def main():
    sid=int(os.environ["SHARD_INDEX"]);nshards=int(os.environ["SHARD_COUNT"])
    assert nshards>=1 and 0<=sid<nshards
    ordered=list(lab.CONFIGS.items())
    selected=[(name,cfg) for i,(name,cfg) in enumerate(ordered) if i%nshards==sid]
    assert selected
    out=Path(f"analysis/btc15m_no_st_flip_exit_percent_sl_20261123/shard_{sid}")
    out.mkdir(parents=True,exist_ok=True)
    df,quality=lab.read_source("BTCUSD")
    ema,stline,trend,valid=lab.st_and_ema(df,lab.TF)
    ind=lab.make_indicators(df)
    sigcache={}
    results=[];monthly=[];trades=[]
    for name,cfg in selected:
        key=(name.split("_")[0],cfg[0])
        if key not in sigcache:sigcache[key]=lab.make_signals(df,ema,trend,valid,*key)[0]
        for path in lab.PATHS:
            print("RUN",name,path,flush=True)
            rr,mon,ledger=lab.simulate(df,ema,stline,trend,ind,name,cfg,sigcache[key],path)
            assert rr["supertrend_flip_exit_enabled"]==("_BASE_ST3R" in name or "_FLIPON_" in name)
            if "_NOFLIP_" in name:assert rr["flip_exits"]==0
            results.append(rr);monthly.append(mon);trades.append(ledger)
            print("RESULT",json.dumps(rr,sort_keys=True),flush=True)
    pd.DataFrame(results).to_csv(out/"summary_part.csv",index=False)
    pd.concat(monthly,ignore_index=True).to_csv(out/"monthly_part.csv",index=False)
    pd.concat(trades,ignore_index=True).to_csv(out/"trades_part.csv.gz",index=False,compression="gzip")
    (out/"quality_part.json").write_text(json.dumps({"shard":sid,"nshards":nshards,
        "configs":[k for k,v in selected],"model_count":len(results),"data_quality":quality},default=str,indent=2))
    print("SHARD_DONE",sid,len(selected),len(results),flush=True)
if __name__=="__main__":main()
