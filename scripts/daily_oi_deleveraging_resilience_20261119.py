#!/usr/bin/env python3
"""Pre-registered BTC-first OI deleveraging/price resilience experiment.
OI declines >1.5% over completed 60m while price retains directional displacement >0.15%.
Interpretation: liquidation/position-unwind inventory transfer may permit next 3h continuation.
OI candles are aggregate proxy, NOT actual liquidation tape. ETH only frozen validation.
"""
import glob,gzip,json,hashlib
from pathlib import Path
import numpy as np,pandas as pd
OUT=Path("analysis/daily_oi_deleveraging_resilience_20261119");OUT.mkdir(parents=True,exist_ok=True)
STOP=.0045;TARGET=.0065;HOLD=36;OI_DROP=.015;PRICE_MOVE=.0015;COST=.00158;STRESS=.00238;ALLOCATION=.25
def load(sym):
 def get(path):
  files=sorted(glob.glob(path))
  if len(files)<20:raise RuntimeError("insufficient partitions "+path)
  frames=[]
  for f in files:
   with gzip.open(f,"rt") as z:frames.append(pd.read_csv(z,usecols=["time","open","high","low","close"]))
  a=pd.concat(frames,ignore_index=True).sort_values("time")
  if a.time.duplicated().any():raise RuntimeError("duplicate timestamps "+path)
  a.index=pd.to_datetime(a.time,unit="s",utc=True)
  return a
 px=get(f"data/delta_india/{sym}/1m/20??-??.csv.gz")
 oi=get(f"data/delta_india/{sym}/institutional/history/open_interest_5m/20??-??.csv.gz")
 bars=px.resample("5min").agg({"open":"first","high":"max","low":"min","close":"last"})
 count=px.close.resample("5min").count()
 bars=bars[count==5]
 oi=oi[["close"]].rename(columns={"close":"oi"})
 b=bars.join(oi,how="inner")
 b=b[(b.oi>0)&(b.open>0)]
 return b
def evaluate(sym,cost):
 b=load(sym); idx=b.index; n=len(b)
 # Signal at 5m bar close, enter next complete 5m bar open.
 o=b.open.to_numpy();h=b.high.to_numpy();l=b.low.to_numpy();c=b.close.to_numpy();oi=b.oi.to_numpy()
 day=idx.tz_convert("Asia/Kolkata").strftime("%Y-%m-%d")
 eligible=np.zeros(n,dtype=bool);direction=np.zeros(n,dtype=int)
 for i in range(12,n-1):
  if idx[i]-idx[i-12]!=pd.Timedelta(minutes=60) or idx[i+1]-idx[i]!=pd.Timedelta(minutes=5):continue
  if oi[i]/oi[i-12]-1> -OI_DROP:continue
  ret=c[i]/c[i-12]-1
  if abs(ret)<PRICE_MOVE:continue
  eligible[i+1]=True;direction[i+1]=1 if ret>0 else -1
 trades=[];busy=-1;used=set()
 for i in range(n):
  if i<busy or not eligible[i] or day[i] in used:continue
  side=direction[i];entry=o[i];stop=entry*(1-side*STOP);target=entry*(1+side*TARGET)
  used.add(day[i]);last=min(n-1,i+HOLD);exit_i=last;reason="time";fill=c[last]
  for j in range(i,last+1):
   if j>i and idx[j]-idx[j-1]!=pd.Timedelta(minutes=5):
    exit_i=j-1;fill=c[j-1];reason="gap";break
   stop_hit=l[j]<=stop if side==1 else h[j]>=stop
   target_hit=h[j]>=target if side==1 else l[j]<=target
   if stop_hit:
    fill=min(o[j],stop) if side==1 else max(o[j],stop);exit_i=j;reason="stop_first";break
   if target_hit:fill=target;exit_i=j;reason="target";break
  gross=side*(fill/entry-1)
  trades.append({"entry":str(idx[i]),"exit":str(idx[exit_i]),"entry_day_ist":day[i],"exit_day_ist":day[exit_i],"side":int(side),"gross":float(gross),"fee_gst_slippage":cost,"net":float(gross-cost),"reason":reason})
  busy=exit_i+1
 tr=pd.DataFrame(trades);tr.to_csv(OUT/f"{sym}_{'stress' if cost==STRESS else 'base'}_trades.csv",index=False)
 days=pd.date_range(idx[0].tz_convert("Asia/Kolkata").normalize(),idx[-1].tz_convert("Asia/Kolkata").normalize(),freq="D",tz="Asia/Kolkata")
 ledger=pd.DataFrame({"date":days.strftime("%Y-%m-%d")})
 if len(tr):
  daily=tr.groupby("exit_day_ist").net.agg(["sum","count"]).rename(columns={"sum":"net","count":"trades"})
  ledger=ledger.join(daily,on="date")
 ledger["net"]=ledger.net.fillna(0);ledger["trades"]=ledger.trades.fillna(0).astype(int)
 ledger["equity_return"]=ledger.net*ALLOCATION
 ledger.to_csv(OUT/f"{sym}_{'stress' if cost==STRESS else 'base'}_daily.csv",index=False)
 annual=[];monthly=[]
 for label,group in ledger.groupby(ledger.date.str.slice(0,4)):
  v=group.equity_return.to_numpy();w=v[v>0].sum();loss=-v[v<0].sum()
  annual.append({"year":label,"calendar_days":len(group),"positive":int((v>0).sum()),"negative":int((v<0).sum()),"no_trade":int((group.trades==0).sum()),"trades":int(group.trades.sum()),"net_return_pct":float((np.prod(1+v)-1)*100),"net_pf":float(w/loss) if loss else None,"median_daily_pct":float(np.median(v)*100),"mean_daily_pct":float(v.mean()*100),"worst_day_pct":float(v.min()*100)})
 for label,g in ledger.groupby(ledger.date.str.slice(0,7)):
  v=g.equity_return.to_numpy();w=v[v>0].sum();loss=-v[v<0].sum()
  monthly.append({"month":label,"net_return_pct":float((np.prod(1+v)-1)*100),"net_pf":float(w/loss) if loss else None,"positive_days":int((v>0).sum()),"negative_days":int((v<0).sum()),"no_trade_days":int((g.trades==0).sum())})
 v=ledger.equity_return.to_numpy();eq=np.cumprod(1+v);dd=1-eq/np.maximum.accumulate(np.r_[1,eq])[1:]
 streak=0;maxstreak=0
 for x in v:
  streak=streak+1 if x<0 else 0;maxstreak=max(maxstreak,streak)
 return {"symbol":sym,"cost_roundtrip":cost,"trades":len(tr),"annual":annual,"monthly":monthly,"max_close_to_close_drawdown_pct":float(dd.max()*100),"max_losing_calendar_day_streak":maxstreak,"gross_sum":float(tr.gross.sum()) if len(tr) else 0,"cost_sum":float(len(tr)*cost),"limitations":"OI snapshots are NOT actual liquidations; OHLC bar fills not bid/ask; funding cashflows omitted; no lot/margin verification; 2026 previously exposed; intrabar drawdown unmeasured"}
def main():
 result=[]
 for sym in ["BTCUSD","ETHUSD"]:
  for cost in [COST,STRESS]:result.append(evaluate(sym,cost))
 (OUT/"results.json").write_text(json.dumps(result,indent=2))
 print("RESULTS",json.dumps([{k:v for k,v in x.items() if k!="monthly"} for x in result],indent=2))
 print("MONTHLY",json.dumps([{x["symbol"]+"_"+str(x["cost_roundtrip"]):x["monthly"]} for x in result]))
if __name__=="__main__":main()
