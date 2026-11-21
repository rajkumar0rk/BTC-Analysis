#!/usr/bin/env python3
"""600 TP/300 SL first-touch audit on the original 1H-OHLC trade ledger.

Reuses the exact 2405 BTC / 2421 ETH original reported trades and their
1-hour stamped exit windows. First touching archived Delta 1m OHLC decides.
No simulated 1-hour OHLC path. Same-minute dual hits remain ambiguous.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from numba import njit
import backtest_ema_st_1h_trail_1_0p1_20261120 as prior
import backtest_tv_ema_st_1h_27min_20261120 as btc
import backtest_eth_ema_st_1h_27min_20261120 as eth

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"analysis"/"ema_st_1h_all_stops_hourly_1_0p1_20261120"
OUT=ROOT/"analysis"/"original_1h_first_touch_600_300"
OUT.mkdir(parents=True,exist_ok=True)
SUMMARY=json.loads((BASE/"summary.json").read_text())

@njit(cache=True)
def first_touch_asym(times,op,hi,lo,entry_t,exit_t,entry,side,TP,SL):
    i=int(np.searchsorted(times,entry_t))
    j=int(np.searchsorted(times,exit_t))
    if i>=len(times) or times[i]!=entry_t or j<=i:
        return -2
    target=entry+side*TP
    stop=entry-side*SL
    for k in range(i,j):
        if side==1:
            if op[k]>=target:return 1
            if op[k]<=stop:return 0
            tp=hi[k]>=target;sl=lo[k]<=stop
        else:
            if op[k]<=target:return 1
            if op[k]>=stop:return 0
            tp=lo[k]<=target;sl=hi[k]>=stop
        if tp and sl:return 2
        if tp:return 1
        if sl:return 0
    return -1

def execute(asset,module):
    expected=SUMMARY["assets"][asset]["hourly_results"]["inferred"]
    ledger=pd.read_csv(BASE/f"{asset.lower()}_1h_inferred_trades.csv.gz")
    minute,source=prior.read_minutes(module)
    assert len(ledger)==expected["trade_count"]
    assert len(minute)==963360
    t=minute.time.to_numpy(np.int64)
    assert np.all(np.diff(t)==60)
    o=minute.open.to_numpy(np.float64)
    hi=minute.high.to_numpy(np.float64)
    lo=minute.low.to_numpy(np.float64)
    n=len(ledger)
    enters=ledger.entry_epoch.to_numpy(np.int64)
    exits=ledger.exit_epoch.to_numpy(np.int64)
    entries=ledger.entry.to_numpy(np.float64)
    sides=np.where(ledger.side=="LONG",1,-1).astype(np.int8)
    results={}
    for pair,btc_tp,btc_sl in (("200_200",200,200),("400_200",400,200),("600_300",600,300)):
        tpdist=np.full(n,float(btc_tp)) if asset=="BTC" else entries*(btc_tp/80000.)
        sldist=np.full(n,float(btc_sl)) if asset=="BTC" else entries*(btc_sl/80000.)
        statuses=np.empty(n,np.int8)
        for i in range(n):
            statuses[i]=first_touch_asym(t,o,hi,lo,int(enters[i]),int(exits[i]),float(entries[i]),int(sides[i]),float(tpdist[i]),float(sldist[i]))
        assert not np.any(statuses==-2)
        tp=int(np.sum(statuses==1)); sl=int(np.sum(statuses==0))
        tie=int(np.sum(statuses==2)); neither=int(np.sum(statuses==-1))
        resolved=tp+sl
        row={"asset":asset,"pair":pair,"signals":n,
             "TP_first":tp,"SL_first":sl,"ambiguous_same_minute":tie,"neither_before_original_exit":neither,
             "resolved":resolved,"TP_pct_resolved":round(100*tp/resolved,2) if resolved else None,
             "SL_pct_resolved":round(100*sl/resolved,2) if resolved else None,
             "TP_pct_all":round(100*tp/n,2),"SL_pct_all":round(100*sl/n,2),
             "tp_native":"+"+str(btc_tp)+" points" if asset=="BTC" else "+"+str(100*btc_tp/80000)+"%",
             "sl_native":"-"+str(btc_sl)+" points" if asset=="BTC" else "-"+str(100*btc_sl/80000)+"%"}
        assert tp+sl+tie+neither==n
        print("ORIGINAL_LEDGER_FIRST_TOUCH",json.dumps(row),flush=True)
        results[pair]=row
    return {"ledger_net_usd":expected["net_usd"],"source":source,"comparisons":results}

def main():
    r={"method":"Actual archived 1m candle first touches over original reported 1H OHLC trade windows, original trade-entry ledger and timestamps",
       "important":"NOT an independent fixed-exit portfolio backtest; each 1H end time overstates actual end-time precision, so intrahour exit mismatch remains possible. Same-minute ties are ambiguous, not silently given to either side.",
       "assets":{}}
    for asset,module in (("BTC",btc),("ETH",eth)):
        r["assets"][asset]=execute(asset,module)
    (OUT/"results.json").write_text(json.dumps(r,indent=2)+"\n")
    print("ORIGINAL_LEDGER_600_300_COMPLETE",flush=True)
if __name__=="__main__":
    main()
