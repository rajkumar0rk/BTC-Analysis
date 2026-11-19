#!/usr/bin/env python3
"""Preregistered cross-asset propagation falsification: BTC hourly tail shock -> ETH follow-through.
Only completed hourly BTC candles trigger next-hour ETH entries; placebo trades reverse side.
Fixed 2025/2026 rules, no optimization. Historical OHLC cannot establish bid/ask liquidity.
"""
import glob,gzip,json
from pathlib import Path
import numpy as np,pandas as pd
OUT=Path("analysis/cross_asset_shock_20261119");OUT.mkdir(parents=True,exist_ok=True)
FEE=.0005*1.18; SLIP=.0005; STOP=.012; TRAIL=.06; HOLD=168; ALLOCATION=.25
def load(sym):
 files=sorted(glob.glob(f"data/delta_india/{sym}/1m/20??-??.csv.gz"))
 if len(files)<20:raise RuntimeError(f"Insufficient genuine {sym} data: {len(files)} partitions")
 pieces=[]
 for file in files:
  with gzip.open(file,"rt") as stream:pieces.append(pd.read_csv(stream,usecols=["time","open","high","low","close"]))
 d=pd.concat(pieces,ignore_index=True).drop_duplicates("time").sort_values("time")
 d.index=pd.to_datetime(d.time,unit="s",utc=True)
 if d.index.has_duplicates:raise RuntimeError("duplicate timestamps")
 if d[["open","high","low","close"]].isna().any().any():raise RuntimeError("NaN prices")
 hourly=d.resample("1h").agg({"open":"first","high":"max","low":"min","close":"last"})
 count=d.close.resample("1h").count()
 hourly=hourly[count==60]
 return hourly
def run(invert):
 btc=load("BTCUSD");eth=load("ETHUSD")
 d=eth.join(btc[["open","close"]].rename(columns={"open":"btc_open","close":"btc_close"}),how="inner")
 if len(d)<15000:raise RuntimeError(f"Too few synchronized hours {len(d)}")
 # Rolling threshold is determined exclusively by PRIOR 60 days of BTC hourly returns.
 ret=np.log(d.btc_close/d.btc_open)
 threshold=ret.abs().rolling(1440,min_periods=1440).quantile(.995).shift(1)
 shock=np.where((ret.abs()>threshold)&(ret.abs()>.007),np.sign(ret),0)
 if invert:shock=-shock
 # Only signal from previous fully closed BTC hour; execute at next ETH hour open.
 a=d[["open","high","low","close"]].to_numpy();t=d.index
 pos=0;entry=0;stop=0;extreme=0;start=0;equity=1.;peak=1.;dd=0.;trades=[];curve=[]
 for i in range(1442,len(a)):
  op,hi,lo,cl=a[i]
  if pos:
   hit=(lo<=stop if pos==1 else hi>=stop)
   expiry=(i-start>=HOLD)
   if hit or expiry:
    fill=(min(op,stop) if pos==1 else max(op,stop)) if hit else op
    fill*=1-SLIP*pos
    net=pos*(fill/entry-1)-2*FEE
    equity*=max(.01,1+ALLOCATION*net)
    trades.append(dict(entry=str(t[start]),exit=str(t[i]),side=pos,net=float(net),R=float(net/STOP),reason="stop" if hit else "time"))
    pos=0
   else:
    extreme=max(extreme,hi) if pos==1 else min(extreme,lo)
    candidate=extreme*(1-TRAIL) if pos==1 else extreme*(1+TRAIL)
    stop=max(stop,candidate) if pos==1 else min(stop,candidate)
  if not pos and shock[i-1] and shock[i-2]==0:
   pos=int(shock[i-1]);entry=op*(1+SLIP*pos);start=i;extreme=entry;stop=entry*(1-STOP*pos)
  marked=equity*(max(.01,1+ALLOCATION*(pos*(cl/entry-1)-2*FEE)) if pos else 1.)
  peak=max(peak,marked);dd=max(dd,1-marked/peak)
  curve.append((t[i].tz_convert("Asia/Kolkata").strftime("%Y-%m"),marked))
 if pos:
  net=pos*(a[-1][3]*(1-SLIP*pos)/entry-1)-2*FEE
  equity*=max(.01,1+ALLOCATION*net)
  trades.append(dict(entry=str(t[start]),exit=str(t[-1]),side=pos,net=float(net),R=float(net/STOP),reason="forced"))
 variant="placebo_reverse" if invert else "btc_shock_follow"
 tr=pd.DataFrame(trades);tr.to_csv(OUT/f"{variant}_trades.csv",index=False)
 if tr.empty:return {"variant":variant,"trades":0}
 tr["month"]=pd.to_datetime(tr["exit"],utc=True).dt.tz_convert("Asia/Kolkata").dt.strftime("%Y-%m")
 tr["year"]=pd.to_datetime(tr["exit"],utc=True).dt.year
 monthly=[]
 for m,g in tr.groupby("month"):
  wins=g[g.net>0].net.sum();loss=-g[g.net<0].net.sum()
  monthly.append(dict(month=m,closed_trades=len(g),return_on_equity=float(np.prod(1+ALLOCATION*g.net)-1),pf=float(wins/loss) if loss else None))
 (OUT/f"{variant}_monthly.json").write_text(json.dumps(monthly,indent=2))
 w=tr[tr.net>0].net;l=tr[tr.net<0].net
 return dict(variant=variant,source="ETHUSD traded OHLC + BTCUSD traded OHLC",trades=len(tr),win_rate=float(len(w)/len(tr)),avg_win_loss=float(w.mean()/-l.mean()) if len(w) and len(l) else None,pf=float(w.sum()/-l.sum()) if len(l) else None,max_R=float(tr.R.max()),max_drawdown=float(dd),net_return=float(equity-1),annual_exit_compounded={str(y):float(np.prod(1+ALLOCATION*g.net)-1) for y,g in tr.groupby("year")},positive_months=sum(x["return_on_equity"]>0 for x in monthly),months=len(monthly),biggest_winner_removed_net=float(np.prod(1+ALLOCATION*tr.sort_values("net").iloc[:-1].net)-1),caveat="ETH execution is hourly OHLC approximation; stop priority conservative; funding omitted (unverified), no L2, 2026 partial, signal overlap/correlation risk")
if __name__=="__main__":
 results=[run(False),run(True)]
 (OUT/"results.json").write_text(json.dumps(results,indent=2))
 print(json.dumps(results,indent=2))
