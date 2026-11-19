#!/usr/bin/env python3
"""Preregistered BTC-first weekend liquidity reversion; fixed parameters, no optimization."""
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path("data/delta_india")
OUT=Path("analysis/daily_weekend_inventory_20261119")
OUT.mkdir(parents=True,exist_ok=True)
COSTS={"base":0.00158,"stress":0.00238}
STOP=0.0045; TARGET=0.0065; MAX_HOLD=180; ALLOC=0.25
def load(sym):
    paths=sorted((ROOT/sym/"1m").glob("20??-??.csv.gz"))
    if not paths: raise RuntimeError("missing genuine archive "+sym)
    frames=[pd.read_csv(p,compression="gzip",usecols=["time","open","high","low","close"]) for p in paths]
    d=pd.concat(frames,ignore_index=True)
    d["time"]=pd.to_datetime(d.time.astype("int64"),unit="s",utc=True)
    d=d.set_index("time").sort_index()
    if d.index.has_duplicates: raise RuntimeError("duplicate timestamp "+sym)
    return d
def run(sym,scenario,cost):
    d=load(sym); op=d.open.to_numpy(float); hi=d.high.to_numpy(float); lo=d.low.to_numpy(float)
    ix=d.index; pos={t:i for i,t in enumerate(ix)}
    start=ix.min().floor("D"); end=ix.max().floor("D")
    days=pd.date_range(start,end,freq="D",tz="UTC")
    ledger={day:{"date":str(day.date()),"net_account_pct":0.0,"trades":0,"status":"no_trade"} for day in days}
    trades=[]
    for day in days:
        if day.weekday()!=0 or day.year not in (2025,2026):continue
        fri=day-pd.Timedelta(days=3)
        if day not in pos or fri not in pos: continue
        k=pos[day]; f=pos[fri]
        if k-f!=3*1440 or k+MAX_HOLD>=len(ix) or ix[k+MAX_HOLD]!=day+pd.Timedelta(minutes=MAX_HOLD):continue
        move=op[k]/op[f]-1
        if abs(move)<0.01:continue
        side=-1 if move>0 else 1
        entry=op[k]; stop=entry*(1-side*STOP); target=entry*(1+side*TARGET)
        exit_price=op[k+MAX_HOLD]; reason="timeout"; end_k=k+MAX_HOLD
        for j in range(k,k+MAX_HOLD):
            stop_hit=lo[j]<=stop if side==1 else hi[j]>=stop
            target_hit=hi[j]>=target if side==1 else lo[j]<=target
            if stop_hit:exit_price=stop;reason="stop";end_k=j;break
            if target_hit:exit_price=target;reason="target";end_k=j;break
        gross=side*(exit_price/entry-1)
        net=(gross-cost)*ALLOC*100
        ledger[day]["net_account_pct"]=round(net,8)
        ledger[day]["trades"]=1
        ledger[day]["status"]="profitable" if net>0 else ("losing" if net<0 else "flat")
        trades.append({"symbol":sym,"scenario":scenario,"entry_utc":str(day),"exit_utc":str(ix[end_k]),"weekend_move":move,"side":side,"exit_reason":reason,"gross_return":gross,"net_account_pct":net})
    df=pd.DataFrame(list(ledger.values()))
    df["year"]=pd.to_datetime(df.date).dt.year
    df["month"]=pd.to_datetime(df.date).dt.to_period("M").astype(str)
    df.to_csv(OUT/f"{sym}_{scenario}_daily.csv",index=False)
    pd.DataFrame(trades,columns=["symbol","scenario","entry_utc","exit_utc","weekend_move","side","exit_reason","gross_return","net_account_pct"]).to_csv(OUT/f"{sym}_{scenario}_trades.csv",index=False)
    summaries=[]
    for (year,month),g in df.groupby(["year","month"]):
        vals=g.net_account_pct.to_numpy(float);gain=vals[vals>0].sum();loss=-vals[vals<0].sum()
        summaries.append({"symbol":sym,"scenario":scenario,"year":int(year),"month":month,"net_account_pct":round(float(vals.sum()),6),"profit_factor":round(float(gain/loss),5) if loss else None,"profitable_days":int((vals>0).sum()),"losing_days":int((vals<0).sum()),"no_trade_days":int((g.trades==0).sum()),"worst_day_pct":round(float(vals.min()),6),"median_day_pct":round(float(np.median(vals)),6)})
    pd.DataFrame(summaries).to_csv(OUT/f"{sym}_{scenario}_monthly.csv",index=False)
    totals={}
    for year,g in df.groupby("year"):
        if year not in (2025,2026):continue
        v=g.net_account_pct.to_numpy(float);equity=np.r_[0,v.cumsum()]
        totals[str(year)]={"net_account_pct":round(float(v.sum()),6),"profitable_days":int((v>0).sum()),"losing_days":int((v<0).sum()),"no_trade_days":int((g.trades==0).sum()),"max_drawdown_account_pct":round(float((np.maximum.accumulate(equity)-equity).max()),6),"trades":int(g.trades.sum())}
    return totals
def main():
    results={}
    for scenario,cost in COSTS.items():
        # BTC is evaluated first, ETH with unchanged settings only.
        results[scenario]={"BTCUSD":run("BTCUSD",scenario,cost),"ETHUSD":run("ETHUSD",scenario,cost)}
    (OUT/"RESULTS.json").write_text(json.dumps({"settings":{"stop":STOP,"target":TARGET,"max_hold_minutes":MAX_HOLD,"account_notional_fraction":ALLOC,"roundtrip_costs":COSTS},"results":results,"limitations":"OHLC proxy, not verified executable fills, financing/funding excluded; 2026 not pristine holdout; sparse weekly trades cannot satisfy 70% profitable calendar days"},indent=2)+"\n")
    print(json.dumps(results,indent=2))
if __name__=="__main__":main()
