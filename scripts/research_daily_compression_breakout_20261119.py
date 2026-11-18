#!/usr/bin/env python3
"""Independent DAILY compression-breakout: a quiet 30/60/120m rolling range,
followed by a completed 1m close beyond that range; next 1m OPEN entry.
Not VWAP, wick reversal, lead-lag, or two-leg pairs. 2025 train only.
2026 research-exposed check, not pristine holdout. One trade/UTC day,
stop-first intraminute ambiguity, no overnight. 0.05% taker fee each
side +18% GST, adverse 2bp slip each side, 1bp funding debit per boundary.
Risk 0.5% account per stop, cap 2x notional; no grid/martingale.
"""
from pathlib import Path
import pandas as pd,numpy as np,itertools,json
ROOT=Path("data/delta_india")
OUT=Path("analysis/daily_compression_breakout_20261119");OUT.mkdir(parents=True,exist_ok=True)
START=int(pd.Timestamp("2025-01-01",tz="UTC").timestamp())
END=int(pd.Timestamp("2026-11-18",tz="UTC").timestamp())
FEE=.0005*1.18;SLIP=.0002;FUND=.0001
LOOK=(30,60,120);QUIET=(.0025,.005,.01);RR=(1.,1.5,2.);STOP=(.0025,.005);HOLD=(30,90)
def load(sym):
 files=sorted((ROOT/sym/"1m").glob("20??-??.csv.gz"))
 if len(files)<22:raise RuntimeError("Missing archive "+sym)
 cols=["time","open","high","low","close","volume"]
 x=pd.concat((pd.read_csv(p,compression="gzip",usecols=cols) for p in files),ignore_index=True)
 x=x[(x.time>=START)&(x.time<END)].sort_values("time").reset_index(drop=True)
 t=x.time.to_numpy(np.int64)
 if len(t)!= (END-START)//60 or t[0]!=START or t[-1]!=END-60 or not np.all(np.diff(t)==60):raise ValueError(sym+" missing 1m bars")
 if not np.isfinite(x[cols].to_numpy(float)).all():raise ValueError(sym+" nonfinite")
 if (x.high<x.low).any() or (x.open<x.low).any() or (x.close<x.low).any() or (x.open>x.high).any() or (x.close>x.high).any():raise ValueError("OHLC")
 return x,dict(symbol=sym,minutes=len(t),files=len(files),first_utc=str(pd.to_datetime(t[0],unit="s",utc=True)),last_utc=str(pd.to_datetime(t[-1],unit="s",utc=True)),missing_minutes=0)
def signals(x):
 c=x.close.to_numpy(float);h=x.high.to_numpy(float);l=x.low.to_numpy(float)
 n=len(x);out={};meta=[]
 for look in LOOK:
  # Window excludes current completed bar. Current minute must CLOSE outside the previously quiet box.
  top=pd.Series(h).shift(1).rolling(look,min_periods=look).max().to_numpy()
  bot=pd.Series(l).shift(1).rolling(look,min_periods=look).min().to_numpy()
  width=(top-bot)/((top+bot)/2)
  for quiet in QUIET:
   sd=np.where((width<=quiet)&(c>top),1,np.where((width<=quiet)&(c<bot),-1,0))
   k=np.flatnonzero(sd)+1
   k=k[(k<n)&(k%1440>=180)&(k%1440<1200)]
   day={}
   for j in k:
    day.setdefault(int(j//1440),(int(j),int(sd[j-1])))
   out[(look,quiet)]=day
   meta.append(dict(lookback_minutes=look,max_prior_box_width=quiet,signals=len(k),days_with_signal=len(day)))
 return out,meta
def replay(x,events,cfg):
 look,quiet,rr,stop,hold=cfg
 t=x.time.to_numpy(np.int64);o=x.open.to_numpy(float);h=x.high.to_numpy(float);l=x.low.to_numpy(float);c=x.close.to_numpy(float)
 eq=1000.;records=[]
 for d in range(len(t)//1440):
  before=eq;net=fee=fund=0.;traded=0
  if d in events:
   k,side=events[d];entry=o[k]*(1+side*SLIP)
   qty=min(eq*.005/(entry*stop),2*eq/entry)
   target=entry*(1+side*stop*rr);st=entry*(1-side*stop)
   finish=min(k+hold,(d+1)*1440);j=finish-1;price=c[j]
   for v in range(k,finish):
    if side>0:
     if l[v]<=st:j=v;price=min(o[v],st);break
     if h[v]>=target:j=v;price=target;break
    else:
     if h[v]>=st:j=v;price=max(o[v],st);break
     if l[v]<=target:j=v;price=target;break
   fill=price*(1-side*SLIP)
   fee=FEE*qty*(entry+fill)
   fund=FUND*qty*fill*sum(1 for v in range(k,j+1) if t[v]%28800==0)
   net=side*qty*(fill-entry)-fee-fund
   eq+=net;traded=1
  records.append((t[d*1440],before,eq,net,fee,fund,traded))
 return np.array(records,float)
def yearrow(sym,cfg,records,year):
 a=records[:365] if year==2025 else records[365:]
 pnl=a[:,3];win=pnl[pnl>1e-7];loss=pnl[pnl<-1e-7]
 st=a[0,1];en=a[-1,2];nav=np.r_[st,a[:,2]]
 streak=maxstreak=0
 for z in pnl:
  streak=streak+1 if z<-1e-7 else 0;maxstreak=max(maxstreak,streak)
 pf=float(win.sum()/-loss.sum()) if len(loss) else None
 look,quiet,rr,stop,hold=cfg
 return dict(symbol=sym,year=year,lookback_min=look,quiet_width_max=quiet,reward_risk=rr,stop_fraction=stop,hold_max_min=hold,
  days=len(a),trades=int(a[:,6].sum()),profitable_days=len(win),losing_days=len(loss),no_trade_days=int((a[:,6]==0).sum()),
  profitable_calendar_days_pct=round(100*len(win)/len(a),3),win_rate_traded_pct=round(100*len(win)/max(1,len(win)+len(loss)),3),
  profit_factor=round(pf,4) if pf is not None else None,net_return_pct=round(100*(en/st-1),4),
  net_profit_usd=round(en-st,3),mean_net_calendar_day_usd=round(float(pnl.mean()),4),
  median_net_calendar_day_usd=round(float(np.median(pnl)),4),
  mean_losing_day_usd=round(float(loss.mean()),4) if len(loss) else None,
  worst_day_usd=round(float(pnl.min()),4),max_losing_day_streak=maxstreak,
  max_dayclose_drawdown_pct=round(float(np.min(nav/np.maximum.accumulate(nav)-1)*100),4),
  fees_usd=round(float(a[:,4].sum()),4),funding_proxy_usd=round(float(a[:,5].sum()),4))
def main():
 summary=[];chosen=[];months=[];quality=[]
 for sym in ("BTCUSD","ETHUSD"):
  x,q=load(sym);quality.append(q);sig,counts=signals(x)
  configs=list(itertools.product(LOOK,QUIET,RR,STOP,HOLD))
  records={}
  for cfg in configs:
   a=replay(x,sig[cfg[:2]],cfg);y25=yearrow(sym,cfg,a,2025);y26=yearrow(sym,cfg,a,2026)
   summary.extend((y25,y26));records[cfg]=(a,y25,y26)
  good=[(k,v) for k,v in records.items() if v[1]["trades"]>=50 and v[1]["net_return_pct"]>0 and v[1]["profit_factor"] is not None and v[1]["profit_factor"]>1]
  passed=bool(good)
  cand=good if passed else list(records.items())
  cfg,(a,y25,y26)=max(cand,key=lambda kv:(kv[1][1]["profitable_calendar_days_pct"],kv[1][1]["net_return_pct"]) if passed else (kv[1][1]["net_return_pct"],kv[1][1]["profitable_calendar_days_pct"]))
  chosen.extend([dict(y25,passes_2025_minimum=passed),dict(y26,passes_2025_minimum=passed)])
  stamps=pd.to_datetime(a[:,0].astype(np.int64),unit="s",utc=True).strftime("%Y-%m")
  for m in pd.unique(stamps):
   z=a[stamps==m]
   months.append(dict(symbol=sym,month_utc=m,net_return_pct=round(100*(z[-1,2]/z[0,1]-1),4),
    trades=int(z[:,6].sum()),profitable_days=int((z[:,3]>1e-7).sum()),losing_days=int((z[:,3]<-1e-7).sum()),
    no_trade_days=int((z[:,6]==0).sum()),fees_usd=round(float(z[:,4].sum()),3)))
  print("SELECTED",sym,cfg,"2025 minimum",passed,y25,y26,flush=True)
 pd.DataFrame(summary).to_csv(OUT/"summary.csv",index=False)
 pd.DataFrame(chosen).to_csv(OUT/"selected.csv",index=False)
 pd.DataFrame(months).to_csv(OUT/"selected_monthly.csv",index=False)
 meta=dict(hypothesis="1m close beyond previous low-volatility rolling price range; enter following 1m open",
  distinct_from=["VWAP exhaustion","wick rejection","1m BTC ETH cross-market lead lag","BTC ETH paired ratio reversion"],
  tested_models_per_symbol=len(configs),archive=quality,
  train="2025",check="2026 through November 17, research-exposed not pristine holdout",
  costs=dict(taker_fee_including_GST_per_side=FEE,adverse_slippage_per_side=SLIP,funding_debit_per_8h_crossing=FUND),
  sizing="0.5% equity nominal stop risk, max 2x notional, at most one trade per UTC day",
  assumptions=["No liquidation engine or exact margin/contract sizing","No depth/impact or real bid/ask","Funding is pessimistic fixed debit proxy, not actual settlement","Stops prioritized over targets on ambiguous OHLC","2026 is not pristine forward data","No guaranteed daily profit"],
  selection="2025 PF>1 and net positive and >=50 trades; rank by profitable calendar days, then net return. If none, rank highest 2025 net return.")
 (OUT/"quality.json").write_text(json.dumps(meta,indent=2)+"\n")
 (OUT/"REPORT.md").write_text("# Independent compression-breakout daily net study\n\n"+pd.DataFrame(chosen).to_string(index=False)+"\n\n"+json.dumps(meta,indent=2)+"\n")
 print("DONE",len(summary),"year-model rows",flush=True)
if __name__=="__main__":main()
