#!/usr/bin/env python3
"""Independent daily net PnL research: 1m signed-volume pressure divergence.
Not real aggressor CVD: proxy candle direction times volume. No lookahead.
Historical 2025 train, 2026 research-exposed check; no profit guarantee.
"""
from pathlib import Path
import itertools,json
import numpy as np
import pandas as pd
ROOT=Path("data/delta_india"); OUT=Path("analysis/daily_volume_pressure_20261119")
OUT.mkdir(parents=True,exist_ok=True)
FEE=.0005*1.18; SLIP=.0002; FUND=.0001
DATES=pd.date_range("2025-01-01","2026-11-17",freq="D",tz="UTC")
def load(sym):
 p=sorted((ROOT/sym/"1m").glob("20??-??.csv.gz"))
 x=pd.concat([pd.read_csv(f,compression="gzip",usecols=["time","open","high","low","close","volume"]) for f in p],ignore_index=True)
 a=int(DATES[0].timestamp());z=int(DATES[-1].timestamp())+86400
 x=x[(x.time>=a)&(x.time<z)].sort_values("time").reset_index(drop=True)
 t=x.time.to_numpy(np.int64)
 assert len(x)==len(DATES)*1440 and t[0]==a and t[-1]==z-60 and np.all(np.diff(t)==60),sym
 assert np.isfinite(x[["open","high","low","close","volume"]].to_numpy(float)).all()
 assert ((x.high>=x.low)&(x.open<=x.high)&(x.open>=x.low)&(x.close<=x.high)&(x.close>=x.low)&(x.volume>=0)).all()
 return x,dict(symbol=sym,rows=len(x),monthly_files=len(p),missing_minutes=0)
def signals(x):
 c=x.close.to_numpy(float);o=x.open.to_numpy(float);v=x.volume.to_numpy(float)
 # Candle-volume imbalance proxy, normalized by trailing volume, and price return.
 pressure=np.sign(c-o)*v
 by={}
 for w,level,mode in itertools.product((15,30,60),(.2,.4,.6),("divergence","continuation")):
  cum=np.r_[0.,np.cumsum(pressure)];vol=np.r_[0.,np.cumsum(v)]
  signed=np.full(len(c),np.nan);pr=np.full(len(c),np.nan)
  signed[w-1:]=(cum[w:]-cum[:-w])/np.maximum(vol[w:]-vol[:-w],1e-12)
  pr[w-1:]=np.log(c[w-1:]/o[:len(c)-w+1])
  # Reversal: strong signed volume against realized price move.
  # Continuation: strong volume and price same direction.
  if mode=="divergence":side=np.where((signed>level)&(pr<-.0005),1,np.where((signed<-level)&(pr>.0005),-1,0))
  else:side=np.where((signed>level)&(pr>.0005),1,np.where((signed<-level)&(pr<-.0005),-1,0))
  # Only signal when completed minute k-1 and enter k open, max one per UTC day.
  ev={}
  for i in np.flatnonzero(side):
   k=int(i+1);minute=k%1440
   if k<len(c) and 180<=minute<1200:ev.setdefault(k//1440,(k,int(side[i])))
  by[(w,level,mode)]=ev
 return by
def replay(x,ev,tp,sl,hold):
 o=x.open.to_numpy(float);h=x.high.to_numpy(float);l=x.low.to_numpy(float);c=x.close.to_numpy(float);t=x.time.to_numpy(np.int64)
 eq=1000.;rows=[]
 for day in range(len(DATES)):
  prior=eq;net=0.;fees=0.;fund=0.;did=0
  if day in ev and eq>0:
   k,side=ev[day];did=1
   entry=o[k]*(1+side*SLIP);qty=min(eq*.005/(sl*entry),eq*2/entry)
   stop=entry*(1-side*sl);target=entry*(1+side*tp)
   end=min(k+hold,(day+1)*1440);j=end-1;exitprice=c[j]
   for n in range(k,end):
    if side==1:
     if l[n]<=stop:j=n;exitprice=min(o[n],stop);break
     if h[n]>=target:j=n;exitprice=target;break
    else:
     if h[n]>=stop:j=n;exitprice=max(o[n],stop);break
     if l[n]<=target:j=n;exitprice=target;break
   fill=exitprice*(1-side*SLIP)
   fees=qty*FEE*(entry+fill)
   fund=qty*FUND*fill*sum(t[q]%28800==0 for q in range(k,j+1))
   net=qty*side*(fill-entry)-fees-fund;eq+=net
  rows.append((prior,eq,net,fees,fund,did))
 return np.asarray(rows)
def stats(a,sym,cfg,year):
 z=a[:365] if year==2025 else a[365:];p=z[:,2];w=p[p>1e-8];loss=p[p<-1e-8]
 eq=np.r_[z[0,0],z[:,1]];streak=0;mx=0
 for v in p:
  streak=streak+1 if v<-1e-8 else 0;mx=max(mx,streak)
 return dict(symbol=sym,year=year,window=cfg[0],pressure_threshold=cfg[1],mode=cfg[2],target=cfg[3],stop=cfg[4],hold_min=cfg[5],
   calendar_days=len(z),trades=int(z[:,5].sum()),profitable_days=len(w),losing_days=len(loss),no_trade_days=int((z[:,5]==0).sum()),
   profitable_calendar_days_pct=round(100*len(w)/len(z),3),
   profit_factor=round(float(w.sum()/-loss.sum()),4) if len(loss) else None,
   net_return_pct=round(100*(z[-1,1]/z[0,0]-1),4),
   median_daily_net_usd=round(float(np.median(p)),4),mean_daily_net_usd=round(float(np.mean(p)),4),
   worst_day_usd=round(float(p.min()),4),max_losing_day_streak=mx,
   max_dayclose_drawdown_pct=round(float(100*np.min(eq/np.maximum.accumulate(eq)-1)),4),
   fees_usd=round(float(z[:,3].sum()),4),funding_debit_usd=round(float(z[:,4].sum()),4))
def main():
 summary=[];selected=[];monthly=[];quality=[]
 for sym in ("BTCUSD","ETHUSD"):
  print("LOADING",sym,flush=True);x,q=load(sym);quality.append(q);evs=signals(x);runs={}
  for key,ev in evs.items():
   for tp,sl,hold in itertools.product((.003,.006),(.003,.005),(30,90)):
    cfg=(*key,tp,sl,hold);a=replay(x,ev,tp,sl,hold)
    r25=stats(a,sym,cfg,2025);r26=stats(a,sym,cfg,2026)
    summary.extend((r25,r26));runs[cfg]=(a,r25,r26)
  viable=[(k,v) for k,v in runs.items() if v[1]["trades"]>=50 and v[1]["net_return_pct"]>0 and (v[1]["profit_factor"] or 0)>1]
  passed=bool(viable)
  chosen=max(viable if passed else runs.items(),key=lambda kv:(kv[1][1]["profitable_calendar_days_pct"],kv[1][1]["net_return_pct"]) if passed else (kv[1][1]["net_return_pct"],kv[1][1]["profitable_calendar_days_pct"]))
  cfg,(a,r25,r26)=chosen
  selected.extend([{**r25,"passes_2025_minimum":passed},{**r26,"passes_2025_minimum":passed}])
  for m in pd.unique(DATES.strftime("%Y-%m")):
   z=a[DATES.strftime("%Y-%m")==m];p=z[:,2]
   monthly.append(dict(symbol=sym,month_utc=m,net_return_pct=round(100*(z[-1,1]/z[0,0]-1),4),
    trades=int(z[:,5].sum()),profitable_days=int((p>1e-8).sum()),losing_days=int((p<-1e-8).sum()),no_trade_days=int((z[:,5]==0).sum())))
  print("SELECTED",sym,cfg,r25,r26,flush=True)
 pd.DataFrame(summary).to_csv(OUT/"summary.csv",index=False)
 pd.DataFrame(selected).to_csv(OUT/"selected.csv",index=False)
 pd.DataFrame(monthly).to_csv(OUT/"selected_monthly.csv",index=False)
 meta=dict(hypothesis="Candle-direction signed volume pressure versus same-window price direction",novelty="1-minute candle-volume pressure divergence/continuation, distinct from prior wick, VWAP, cross-asset and breakout tests",
   models_per_market=len(runs),data_quality=quality,period="2025-01-01 through 2026-11-17 UTC",selection="2025 PF>1, net return>0, trades>=50 then highest positive calendar day fraction; otherwise best net 2025. 2026 unchanged.",
   costs=dict(taker_fee_plus_GST_per_side=FEE,adverse_slippage_per_side=SLIP,conservative_funding_debit_per_8h_boundary=FUND),
   risk=dict(stop_equity_risk=.005,leverage_cap=2),
   limitations=["Candle signed volume is not true taker aggressor volume or order-book imbalance",
    "2026 was previously exposed in earlier research; not a pristine out-of-sample",
    "No tick/lot, queue position, margin liquidation, real funding rate, depth or spread snapshots",
    "Intraminute OHLC stops always precede targets; overnight not allowed","No strategy can guarantee daily profit"])
 (OUT/"quality.json").write_text(json.dumps(meta,indent=2)+"\n")
 (OUT/"REPORT.md").write_text("# Independent signed-volume pressure daily-net backtest\n\n"+pd.DataFrame(selected).to_string(index=False)+"\n\n"+json.dumps(meta,indent=2)+"\n")
 print("COMPLETE",len(summary),flush=True)
if __name__=="__main__":main()
