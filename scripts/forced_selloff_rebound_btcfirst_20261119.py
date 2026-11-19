#!/usr/bin/env python3
"""BTC-first preregistered extreme selloff with volume surge: forced-selling proxy.
Economic premise: concentrated deleveraging and transient inventory pressure cause price rebound.
No actual liquidation tape exists. 2025 is exploratory; 2026 is later robustness, never tuned.
ETH is frozen secondary validation, not parameter selection. Placebo trades continuation short.
"""
import glob,gzip,json
from pathlib import Path
import numpy as np,pandas as pd
OUT=Path("analysis/forced_selloff_rebound_btcfirst_20261119");OUT.mkdir(parents=True,exist_ok=True)
FEE=.0005*1.18;SLIP=.0005;STOP=.015;TRAIL=.05;HOLD=72;ALLOCATION=.25
def load(sym):
 files=sorted(glob.glob(f"data/delta_india/{sym}/1m/20??-??.csv.gz"))
 if len(files)<20:raise RuntimeError(f"missing {sym} partitions {len(files)}")
 parts=[]
 for f in files:
  with gzip.open(f,"rt") as z:parts.append(pd.read_csv(z,usecols=["time","open","high","low","close","volume"]))
 d=pd.concat(parts,ignore_index=True).drop_duplicates("time").sort_values("time")
 d.index=pd.to_datetime(d.time,unit="s",utc=True)
 if d.index.has_duplicates or d[["open","high","low","close"]].isna().any().any():raise RuntimeError("bad OHLC")
 h=d.resample("1h").agg({"open":"first","high":"max","low":"min","close":"last","volume":"sum"})
 h=h[d.close.resample("1h").count()==60]
 return h
def run(sym,invert=False):
 h=load(sym);t=h.index;a=h[["open","high","low","close"]].to_numpy()
 # An hourly crash plus extreme volume proxies temporary forced-selling pressure.
 # Prior rolling 30-day volume baseline is shifted one full hour: causal at signal close.
 median_volume=h.volume.rolling(720,min_periods=480).median().shift(1)
 ret=h.close/h.open-1
 event=(ret<=-.025)&(h.volume>=3*median_volume)
 signal={}
 for idx in np.flatnonzero(event.to_numpy()):
  if idx+1>=len(t):continue
  if t[idx+1]-t[idx]!=pd.Timedelta(hours=1):continue
  signal[t[idx+1]]=-1 if invert else 1
 pos=0;entry=stop=extreme=0.;start=0;equity=1.;peak=1.;dd=0.;trades=[];curve=[]
 for i,(tm,bar) in enumerate(zip(t,a)):
  op,hi,lo,cl=bar
  if pos:
   hit=lo<=stop if pos==1 else hi>=stop
   expiry=i-start>=HOLD
   if hit or expiry:
    fill=(min(op,stop) if pos==1 else max(op,stop)) if hit else op
    fill*=1-SLIP*pos
    net=pos*(fill/entry-1)-2*FEE
    equity*=max(.01,1+ALLOCATION*net)
    trades.append(dict(entry=str(t[start]),exit=str(tm),side=pos,net=float(net),R=float(net/STOP),reason="stop" if hit else "time"))
    pos=0
   else:
    extreme=max(extreme,hi) if pos==1 else min(extreme,lo)
    candidate=extreme*(1-TRAIL) if pos==1 else extreme*(1+TRAIL)
    stop=max(stop,candidate) if pos==1 else min(stop,candidate)
  if not pos and tm in signal:
   pos=signal[tm];entry=op*(1+SLIP*pos);start=i;extreme=entry;stop=entry*(1-STOP*pos)
  marked=equity*max(.01,1+ALLOCATION*(pos*(cl/entry-1)-2*FEE)) if pos else equity
  peak=max(peak,marked);dd=max(dd,1-marked/peak)
  curve.append((tm.tz_convert("Asia/Kolkata").strftime("%Y-%m"),float(marked)))
 if pos:
  net=pos*(a[-1][3]*(1-SLIP*pos)/entry-1)-2*FEE
  equity*=max(.01,1+ALLOCATION*net)
  trades.append(dict(entry=str(t[start]),exit=str(t[-1]),side=pos,net=float(net),R=float(net/STOP),reason="forced"))
 tag=sym+("_continuation_placebo" if invert else "_rebound")
 tr=pd.DataFrame(trades);tr.to_csv(OUT/(tag+"_trades.csv"),index=False)
 if tr.empty:return dict(symbol=sym,variant=tag,trades=0)
 tr["month"]=pd.to_datetime(tr.exit,utc=True).dt.tz_convert("Asia/Kolkata").dt.strftime("%Y-%m")
 tr["year"]=pd.to_datetime(tr.exit,utc=True).dt.year
 monthly=[]
 for month,g in tr.groupby("month"):
  w=g[g.net>0].net.sum();l=-g[g.net<0].net.sum()
  monthly.append(dict(month=month,trades=len(g),net_return=float(np.prod(1+ALLOCATION*g.net)-1),pf=float(w/l) if l else None))
 (OUT/(tag+"_monthly.json")).write_text(json.dumps(monthly,indent=2))
 w=tr[tr.net>0].net;l=tr[tr.net<0].net
 return dict(symbol=sym,variant=tag,trades=len(tr),win_rate=float(len(w)/len(tr)),avg_win_loss=float(w.mean()/-l.mean()) if len(w) and len(l) else None,pf=float(w.sum()/-l.sum()) if len(l) else None,max_R=float(tr.R.max()),max_drawdown=float(dd),net_return=float(equity-1),annual_exit_compounded={str(y):float(np.prod(1+ALLOCATION*g.net)-1) for y,g in tr.groupby("year")},positive_months=sum(m["net_return"]>0 for m in monthly),months=len(monthly),biggest_winner_removed_net=float(np.prod(1+ALLOCATION*tr.sort_values("net").iloc[:-1].net)-1),caveat="Hourly stop simulation; crash volume is a proxy not observed liquidations; gap/slippage uncertainty, funding omitted, no historical L2; 2026 partial")
if __name__=="__main__":
 results=[run("BTCUSD",False),run("BTCUSD",True),run("ETHUSD",False),run("ETHUSD",True)]
 (OUT/"results.json").write_text(json.dumps(results,indent=2))
 print(json.dumps(results,indent=2))
