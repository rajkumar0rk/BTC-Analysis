#!/usr/bin/env python3
"""Preregistered trade-vs-mark premium exhaustion hypothesis; exploratory only.
Signal: trade close / mark close premium z-score, causal 48h history.
At 5m close, extreme premium is faded at next 5m open. 0.6% stop;
large moves allowed by 4% trailing reversal, 48h maximum hold.
Prices are actual traded OHLC, NOT mark prices. Assumes 5m open fills
plus 5bps slippage and 5bps taker fee each side, 18% GST on fees.
Funding is excluded (explicit missing-cost limitation).
"""
import csv,gzip,glob,json,os
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path("analysis/independent_mark_premium_20261119")
ROOT.mkdir(parents=True,exist_ok=True)
def load(sym,kind):
    folder=f"data/delta_india/{sym}/1m" if kind=="trade" else f"data/delta_india/{sym}/institutional/history/mark_1m"
    paths=sorted(glob.glob(folder+"/20??-??.csv.gz"))
    if len(paths)<20:raise RuntimeError(f"missing partitions {folder}: {len(paths)}")
    frames=[]
    for path in paths:
        with gzip.open(path,"rt") as f:
            d=pd.read_csv(f,usecols=["time","open","high","low","close"])
        frames.append(d)
    d=pd.concat(frames,ignore_index=True)
    d["time"]=pd.to_datetime(d["time"].astype("int64"),unit="s",utc=True)
    d=d.drop_duplicates("time").set_index("time").sort_index()
    if not d.index.is_monotonic_increasing:raise RuntimeError("bad index")
    for k in ("open","high","low","close"):d[k]=pd.to_numeric(d[k],errors="raise")
    return d
def aggregate(d):
    z=d.resample("5min",label="left",closed="left").agg({"open":"first","high":"max","low":"min","close":"last"})
    n=d["close"].resample("5min",label="left",closed="left").count()
    return z[n==5]
def test(sym):
    t=aggregate(load(sym,"trade"));m=aggregate(load(sym,"mark"))
    d=t.join(m[["close"]].rename(columns={"close":"mark"}),how="inner")
    if len(d)<150000:raise RuntimeError("insufficient complete bars")
    prem=(d["close"]/d["mark"]-1)*10000
    mu=prem.rolling(576,min_periods=576).mean().shift(1)
    sd=prem.rolling(576,min_periods=576).std().shift(1)
    z=(prem-mu)/sd.replace(0,np.nan)
    # fixed threshold: extreme premium implies crowded long/short
    signal=np.where(z>=3,-1,np.where(z<=-3,1,0))
    rows=[];position=0;entry=0;stop=0;extreme=0;start=0
    equity=1.;peak=1.;maxdd=0.
    fee=0.0005*1.18;slip=0.0005
    times=d.index; a=d[["open","high","low","close"]].to_numpy()
    # 1x notional, one position, no leverage; no reinvested leverage
    for i in range(577,len(a)):
        op,hi,lo,cl=a[i]
        if position:
            # stop uses prior completed bar's trailing level; adverse stop gap at open
            hit=(lo<=stop) if position==1 else (hi>=stop)
            timeout=i-start>=576
            if hit or timeout:
                px=min(op,stop) if position==1 and hit else max(op,stop) if position==-1 and hit else op
                px=px*(1-slip*position)
                gross=position*(px/entry-1)
                net=gross-2*fee
                equity*=max(0.01,1+net)
                rows.append({"symbol":sym,"entry_utc":str(times[start]),"exit_utc":str(times[i]),"direction":position,"gross_return":gross,"net_return":net,"R":net/0.006,"exit_reason":"stop" if hit else "timeout"})
                position=0
            else:
                # update trailing only AFTER evaluating this bar stop
                extreme=max(extreme,hi) if position==1 else min(extreme,lo)
                trail=extreme*(1-0.04) if position==1 else extreme*(1+0.04)
                stop=max(stop,trail) if position==1 else min(stop,trail)
        if not position and i>578 and signal[i-1] and not signal[i-2]:
            position=int(signal[i-1]);entry=op*(1+slip*position)
            start=i;extreme=entry;stop=entry*(1-0.006*position)
        if position:
            mark_net=position*(cl/entry-1)-2*fee
            marked=equity*max(.01,1+mark_net)
        else:marked=equity
        peak=max(peak,marked);maxdd=max(maxdd,1-marked/peak)
    trades=pd.DataFrame(rows)
    trades.to_csv(ROOT/f"{sym}_trades.csv",index=False)
    if trades.empty:return {"symbol":sym,"error":"no trades"}
    trades["month"]=pd.to_datetime(trades.exit_utc,utc=True).dt.tz_convert("Asia/Kolkata").dt.strftime("%Y-%m")
    monthly=trades.groupby("month").agg(trades=("net_return","size"),wins=("net_return",lambda x:int((x>0).sum())),gross_wins=("net_return",lambda x:float(x[x>0].sum())),gross_losses=("net_return",lambda x:float(-x[x<0].sum())))
    monthly["pf"]=monthly.gross_wins/monthly.gross_losses.replace(0,np.nan)
    monthly["compounded_return"]=trades.groupby("month").net_return.apply(lambda x:float(np.prod(1+x)-1))
    monthly.to_csv(ROOT/f"{sym}_monthly.csv")
    win=trades[trades.net_return>0].net_return;loss=trades[trades.net_return<0].net_return
    byyear={str(year):float(np.prod(1+g.net_return)-1) for year,g in trades.groupby(pd.to_datetime(trades.exit_utc,utc=True).dt.year)}
    return {"symbol":sym,"bars":len(d),"trades":len(trades),"wins":len(win),"losses":len(loss),"win_rate":len(win)/len(trades),"avg_win_loss_ratio":float(win.mean()/-loss.mean()) if len(win) and len(loss) else None,"pf":float(win.sum()/-loss.sum()) if len(loss) else None,"max_R":float(trades.R.max()),"max_dd_marked":maxdd,"net_total":float(np.prod(1+trades.net_return)-1),"calendar_years_realized":byyear,"funding_included":False,"caveat":"5m OHLC stop ordering, 5m opening fills, no bid ask/orderbook or actual funding; exploratory only"}
def main():
    result=[]
    for s in ("BTCUSD","ETHUSD"):
        result.append(test(s))
    (ROOT/"results.json").write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
if __name__=="__main__":main()
