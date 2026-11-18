#!/usr/bin/env python3
"""Independent daily time-window conditional drift around UTC funding clocks.
No funding cashflow claim: close before boundary, or use post-boundary window.
2025-only selection, 2026 research-exposed unchanged check. One trade/day.
Entry at minute OPEN after completed 15m pre-window direction or inverse.
Exit fixed stop/target or max hold; conservative stop-first OHLC, next minute.
Fee 0.05% taker each side +18% GST, 2bp adverse slippage each fill.
"""
from pathlib import Path
import itertools,json
import numpy as np
import pandas as pd
ROOT=Path("data/delta_india");OUT=Path("analysis/daily_funding_window_drift_20261119");OUT.mkdir(parents=True,exist_ok=True)
START=1735689600;END=1794960000
FEE=.00059;SLIP=.0002;FUND=.0001
START_MIN=(15,30,60,120,240,360,480,600,720,840,960,1080,1200,1320)
SIGNAL=("long","short","momentum","contrarian")
TP=(.003,.006);SL=(.002,.004);HOLD=(30,90)
CAP=1000.;RISK=.005;LEV=2.
def load(sym):
 p=sorted((ROOT/sym/"1m").glob("20??-??.csv.gz"))
 if len(p)<22:raise RuntimeError("source missing")
 x=pd.concat((pd.read_csv(f,compression="gzip",usecols=["time","open","high","low","close","volume"]) for f in p),ignore_index=True)
 x=x[(x.time>=START)&(x.time<END)].sort_values("time").reset_index(drop=True)
 t=x.time.to_numpy(np.int64)
 if len(t)%1440 or len(t)<950000 or t[0]!=START or t[-1]!=END-60 or not np.all(np.diff(t)==60):raise RuntimeError("source incomplete")
 if not np.isfinite(x[["open","high","low","close","volume"]].to_numpy(float)).all():raise RuntimeError("nonfinite")
 if (x.high<x.low).any() or (x.open<x.low).any() or (x.close<x.low).any():raise RuntimeError("OHLC invalid")
 return x,dict(symbol=sym,rows=len(x),source_files=len(p),missing_minutes=0,first_utc=str(pd.to_datetime(t[0],unit="s",utc=True)),last_utc=str(pd.to_datetime(t[-1],unit="s",utc=True)))
def run(px,minutes,mode,tp,sl,hold):
 o,h,l,c,t=px;n=len(o);eq=CAP;rows=[]
 for day in range(n//1440):
  k=day*1440+minutes
  prev=eq
  side=1 if mode=="long" else -1 if mode=="short" else (1 if c[k-1]>c[k-16] else -1)
  if mode=="contrarian":side=-side
  entry=o[k]*(1+side*SLIP)
  qty=min(eq*RISK/(sl*entry),eq*LEV/entry)
  stop=entry*(1-side*sl);target=entry*(1+side*tp)
  end=min(k+hold,(day+1)*1440);j=end-1;pxexit=c[j]
  for v in range(k,end):
   if side==1:
    if l[v]<=stop:j=v;pxexit=min(o[v],stop);break
    if h[v]>=target:j=v;pxexit=target;break
   else:
    if h[v]>=stop:j=v;pxexit=max(o[v],stop);break
    if l[v]<=target:j=v;pxexit=target;break
  fill=pxexit*(1-side*SLIP)
  fee=FEE*qty*(entry+fill)
  funding=FUND*qty*fill*sum(1 for z in range(k,j+1) if t[z]%28800==0)
  pnl=side*qty*(fill-entry)-fee-funding
  eq+=pnl
  rows.append((int(t[day*1440]),prev,eq,pnl,fee,funding,j-k+1))
 return np.array(rows)
def summary(sym,cfg,rows,year):
 a=rows[:365] if year==2025 else rows[365:]
 p=a[:,3];pos=p[p>1e-9];neg=p[p<-1e-9]
 nav=np.r_[a[0,1],a[:,2]];peak=np.maximum.accumulate(nav)
 streak=0;maxstreak=0
 for z in p:
  streak=streak+1 if z<-1e-9 else 0;maxstreak=max(maxstreak,streak)
 return dict(symbol=sym,year=year,start_minute=cfg[0],mode=cfg[1],tp=cfg[2],sl=cfg[3],hold=cfg[4],
  days=len(a),trades=len(a),profitable_days=len(pos),losing_days=len(neg),no_trade_days=0,
  profitable_calendar_day_pct=round(100*len(pos)/len(a),3),profit_factor=round(float(pos.sum()/-neg.sum()),4) if len(neg) else None,
  net_return_pct=round(100*(a[-1,2]/a[0,1]-1),4),median_daily_net_usd=round(float(np.median(p)),4),
  mean_daily_net_usd=round(float(p.mean()),4),worst_day_usd=round(float(p.min()),4),
  max_losing_streak=maxstreak,max_dayclose_drawdown_pct=round(float(np.min(nav/peak-1)*100),4),
  fees_usd=round(float(a[:,4].sum()),4),funding_proxy_debit_usd=round(float(a[:,5].sum()),4),
  avg_hold_min=round(float(a[:,6].mean()),2))
def main():
 allrows=[];selected=[];monthly=[];quality=[]
 for sym in ("BTCUSD","ETHUSD"):
  print("LOAD",sym,flush=True);d,q=load(sym);quality.append(q)
  px=tuple(d[z].to_numpy(float) if z!="time" else d[z].to_numpy(np.int64) for z in ("open","high","low","close","time"))
  models={}
  for cfg in itertools.product(START_MIN,SIGNAL,TP,SL,HOLD):
   rows=run(px,*cfg);a=summary(sym,cfg,rows,2025);b=summary(sym,cfg,rows,2026)
   allrows.extend((a,b));models[cfg]=(rows,a,b)
  valid=[(k,v) for k,v in models.items() if v[1]["net_return_pct"]>0 and (v[1]["profit_factor"] or 0)>1]
  eligible=bool(valid)
  candidates=valid if eligible else list(models.items())
  cfg,(r,a,b)=max(candidates,key=lambda kv:(kv[1][1]["profitable_calendar_day_pct"],kv[1][1]["net_return_pct"]) if eligible else (kv[1][1]["net_return_pct"],kv[1][1]["profitable_calendar_day_pct"]))
  selected.extend([{**a,"train_positive":eligible},{**b,"train_positive":eligible}])
  months=pd.to_datetime(r[:,0].astype(np.int64),unit="s",utc=True).strftime("%Y-%m")
  for m in pd.unique(months):
   x=r[months==m];monthly.append(dict(symbol=sym,month_utc=m,net_return_pct=round(100*(x[-1,2]/x[0,1]-1),4),
    positive_days=int(np.sum(x[:,3]>1e-9)),negative_days=int(np.sum(x[:,3]<-1e-9)),trades=len(x)))
  print("SELECTED",sym,cfg,eligible,a,b,flush=True)
 pd.DataFrame(allrows).to_csv(OUT/"summary.csv",index=False)
 pd.DataFrame(selected).to_csv(OUT/"selected.csv",index=False)
 pd.DataFrame(monthly).to_csv(OUT/"selected_monthly.csv",index=False)
 meta=dict(hypothesis="Calendar-fixed intraday drift around UTC funding boundary windows, conditional or unconditional direction",
  distinct_from=["VWAP exhaustion","wick reversals","cross-asset 1m lead lag","market neutral carry","4H cross asset confirmation"],
  source_quality=quality,models_per_symbol=14*4*2*2*2,
  cost_model=dict(fee_with_GST_each_side=FEE,adverse_slippage_each_side=SLIP,funding_boundary_debit=FUND),
  execution="one position per UTC day, fixed minute OPEN, momentum from 15 previously completed minutes, stop-first intraminute, flat before day end",
  equity="1000 USD starting, risk 0.5% nominal stop, 2x max notional",
  selection="Only 2025: profitable PF>1; choose highest calendar profitable-day fraction, otherwise least negative net return. 2026 unchanged",
  caveats=["2026 historically exposed, not pristine out-of-sample","No guaranteed daily return",
  "No order book, lot sizes, margin liquidation, actual funding settlements","Simplified 2bp per-side adverse slippage","Every calendar day has a trade even if edge absent"])
 (OUT/"quality.json").write_text(json.dumps(meta,indent=2)+"\n")
 (OUT/"REPORT.md").write_text("# New independent intraday calendar drift research\n\n"+
 "## 2025 selected and 2026 unchanged\n\n"+pd.DataFrame(selected).to_string(index=False)+"\n\n"+
 "## Monthly\n\n"+pd.DataFrame(monthly).to_string(index=False)+"\n\n"+
 "## Assumptions\n\n"+json.dumps(meta,indent=2)+"\n")
 print("DONE",len(allrows),flush=True)
if __name__=="__main__":main()
