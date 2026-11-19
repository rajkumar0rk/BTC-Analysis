#!/usr/bin/env python3
"""Independent preregistered funding-crowding exhaustion falsification.
Hypothesis: an extreme positive funding observation represents expensive crowded longs
and forecasts a downside convex move; negative funding forecasts an upside move.
Control: identical trades with direction inverted. No parameter optimization.
Funding observations are not verified cash settlements. Causal signal only after
completed funding hour; enter following hour open, with adverse execution.
"""
import csv,gzip,glob,json
from pathlib import Path
import numpy as np
import pandas as pd
OUT=Path("analysis/independent_funding_crowding_20261119");OUT.mkdir(parents=True,exist_ok=True)
FEE=.0005*1.18;SLIP=.0005;RISK=.008;TRAIL=.08;MAXH=96
def read(sym,kind):
    base=f"data/delta_india/{sym}/1m" if kind=="trade" else f"data/delta_india/{sym}/institutional/history/funding_1h"
    files=sorted(glob.glob(base+"/20??-??.csv.gz"))
    if len(files)<20:raise RuntimeError(f"Missing {kind} {sym}: {len(files)}")
    a=[]
    for f in files:
        with gzip.open(f,"rt") as z:a.append(pd.read_csv(z,usecols=["time","open","high","low","close"]))
    d=pd.concat(a,ignore_index=True)
    d["time"]=pd.to_datetime(d.time.astype("int64"),unit="s",utc=True)
    d=d.drop_duplicates("time").set_index("time").sort_index()
    for c in ["open","high","low","close"]:d[c]=pd.to_numeric(d[c],errors="raise")
    return d
def backtest(sym,invert=False):
    raw=read(sym,"trade")
    d=raw.resample("1h",label="left",closed="left").agg({"open":"first","high":"max","low":"min","close":"last"})
    cnt=raw.close.resample("1h",label="left",closed="left").count()
    d=d[cnt==60]
    funding=read(sym,"funding")
    d=d.join(funding[["close"]].rename(columns={"close":"fund"}),how="inner")
    if len(d)<15000:raise RuntimeError(f"Missing hourly observations: {sym} {len(d)}")
    # percentile of previous 90 days, excluding current funding observation
    qlo=d.fund.rolling(24*90,min_periods=24*90).quantile(.025).shift(1)
    qhi=d.fund.rolling(24*90,min_periods=24*90).quantile(.975).shift(1)
    signal=np.where(d.fund>qhi,-1,np.where(d.fund<qlo,1,0))
    if invert:signal=-signal
    bars=d[["open","high","low","close"]].to_numpy()
    fr=d.fund.to_numpy();ts=d.index
    pos=0;entry=0;stop=0;extreme=0;start=0;equity=1.;peak=1.;maxdd=0.;rows=[]
    for i in range(24*90+2,len(bars)):
        op,hi,lo,cl=bars[i]
        if pos:
            # Proxy funding charge at end of each hour. Not real settlement.
            funding_cost=pos*fr[i-1] if np.isfinite(fr[i-1]) else 0.
            if i>start:equity*=max(.01,1-funding_cost)
            hit=(lo<=stop if pos==1 else hi>=stop)
            timeout=i-start>=MAXH
            if hit or timeout:
                px=(min(op,stop) if pos==1 else max(op,stop)) if hit else op
                px*=1-SLIP*pos
                gross=pos*(px/entry-1)
                net=gross-2*FEE
                equity*=max(.01,1+net)
                rows.append({"symbol":sym,"entry_utc":str(ts[start]),"exit_utc":str(ts[i]),"side":pos,"gross":gross,"net":net,"R":net/RISK,"reason":"stop" if hit else "timeout"})
                pos=0
            else:
                extreme=max(extreme,hi) if pos==1 else min(extreme,lo)
                candidate=extreme*(1-TRAIL) if pos==1 else extreme*(1+TRAIL)
                stop=max(stop,candidate) if pos==1 else min(stop,candidate)
        # Signal uses completed previous hour; require new crossing, not persistent crowding
        if not pos and signal[i-1] and signal[i-2]==0:
            pos=int(signal[i-1]);entry=op*(1+SLIP*pos);start=i
            extreme=entry;stop=entry*(1-RISK*pos)
        mark=equity*(max(.01,1+pos*(cl/entry-1)-2*FEE) if pos else 1.)
        peak=max(peak,mark);maxdd=max(maxdd,1-mark/peak)
    if pos:
        cl=bars[-1][3];net=pos*(cl*(1-SLIP*pos)/entry-1)-2*FEE
        equity*=max(.01,1+net)
        rows.append({"symbol":sym,"entry_utc":str(ts[start]),"exit_utc":str(ts[-1]),"side":pos,"gross":net+2*FEE,"net":net,"R":net/RISK,"reason":"forced_end"})
    tr=pd.DataFrame(rows)
    suffix="control" if invert else "hypothesis"
    tr.to_csv(OUT/f"{sym}_{suffix}_trades.csv",index=False)
    if tr.empty:return {"symbol":sym,"variant":suffix,"trades":0,"rejected":True}
    tr["month"]=pd.to_datetime(tr.exit_utc,utc=True).dt.tz_convert("Asia/Kolkata").dt.strftime("%Y-%m")
    tr["year"]=pd.to_datetime(tr.exit_utc,utc=True).dt.year
    win=tr[tr.net>0].net;loss=tr[tr.net<0].net
    monthly=[]
    for month,g in tr.groupby("month"):
        monthly.append({"month":month,"trades":len(g),"net_compounded":float(np.prod(1+g.net)-1),"pf":float(g[g.net>0].net.sum()/-g[g.net<0].net.sum()) if (g.net<0).any() else None})
    (OUT/f"{sym}_{suffix}_monthly.json").write_text(json.dumps(monthly,indent=2))
    return {"symbol":sym,"variant":suffix,"bars":len(d),"trades":len(tr),"wins":len(win),"losses":len(loss),"win_rate":len(win)/len(tr),"win_loss_ratio":float(win.mean()/-loss.mean()) if len(win) and len(loss) else None,"pf":float(win.sum()/-loss.sum()) if len(loss) else None,"max_R":float(tr.R.max()),"max_dd_marked":maxdd,"net_total":equity-1,"annual_realized_ex_funding_proxy":{str(y):float(np.prod(1+g.net)-1) for y,g in tr.groupby("year")},"monthly_positive":sum(m["net_compounded"]>0 for m in monthly),"months":len(monthly),"caveat":"funding proxy applied hourly, not settlement-accurate; no historical L2; hourly OHLC cannot prove intrabar ordering; 2026 incomplete"}
def main():
    result=[]
    for sym in ("BTCUSD","ETHUSD"):
        for control in (False,True):result.append(backtest(sym,control))
    (OUT/"results.json").write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
if __name__=="__main__":main()
