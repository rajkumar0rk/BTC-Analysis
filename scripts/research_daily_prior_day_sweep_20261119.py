#!/usr/bin/env python3
"""Independent prior-UTC-day extreme reclaim/sweep daily-net research.
No VWAP, candle-wick, cross-asset impulse, or reused entry families.
Completed 5m close beyond previous UTC day extreme and back inside triggers
a next-minute fade, OR acceptance breakout; at most one trade/day.
2025 parameter selection only, 2026 fixed evaluation (not pristine holdout).
Delta taker fee 0.05% each side +18% GST, 2bp slip each side, 1bp funding
debit at each 8h boundary, stop-first intraminute; no real order book/margin.
"""
from pathlib import Path
import itertools,json
import numpy as np,pandas as pd
ROOT=Path("data/delta_india");OUT=Path("analysis/daily_prior_day_sweep_20261119")
OUT.mkdir(parents=True,exist_ok=True)
START=int(pd.Timestamp("2025-01-01",tz="UTC").timestamp())
END=int(pd.Timestamp("2026-11-18",tz="UTC").timestamp())
FEE=.0005*1.18;SLIP=.0002;FUND=.0001;RISK=.005;LEV=2.
MODES=("reclaim","acceptance")
BUFFER=(0.,.0005,.0015)
TAKE=(.003,.005,.008)
STOP=(.0025,.004,.006)
HOLD=(30,90,180)
def load(sym):
    files=sorted((ROOT/sym/"1m").glob("20??-??.csv.gz"))
    if len(files)<22:raise ValueError("Missing monthly source "+sym)
    x=pd.concat((pd.read_csv(p,compression="gzip",usecols=["time","open","high","low","close","volume"]) for p in files),ignore_index=True)
    x=x[(x.time>=START)&(x.time<END)].sort_values("time").reset_index(drop=True)
    t=x.time.to_numpy(np.int64)
    if len(t)%1440 or len(t)<950000 or t[0]!=START or t[-1]!=END-60 or not np.all(np.diff(t)==60):raise ValueError("Missing 1m bars "+sym)
    if not np.isfinite(x[["open","high","low","close","volume"]].to_numpy(float)).all():raise ValueError("Nonfinite "+sym)
    if (x.high<x.low).any() or (x.open<x.low).any() or (x.close<x.low).any() or (x.open>x.high).any() or (x.close>x.high).any():raise ValueError("Bad OHLC "+sym)
    return x,{"symbol":sym,"minutes":len(x),"months":len(files),"missing_minutes":0,"start":START,"end_exclusive":END}
def signals(x):
    o=x.open.to_numpy(float);h=x.high.to_numpy(float);l=x.low.to_numpy(float);c=x.close.to_numpy(float)
    n=len(x);nd=n//1440
    high=h.reshape(nd,1440).max(axis=1);low=l.reshape(nd,1440).min(axis=1)
    # At 5m boundaries use only completed 5m high/low/close.
    out={}
    for mode,buffer in itertools.product(MODES,BUFFER):
        days={}
        for day in range(1,nd):
            ph=high[day-1];pl=low[day-1]
            base=day*1440
            for k in range(base+180,base+1200,5):
                # 5m bar k..k+4 completes before next 1m OPEN k+5.
                hi=max(h[k:k+5]);lo=min(l[k:k+5]);cl=c[k+4]
                if mode=="reclaim":
                    side= -1 if hi>ph*(1+buffer) and cl<ph else (1 if lo<pl*(1-buffer) and cl>pl else 0)
                else:
                    side= 1 if cl>ph*(1+buffer) else (-1 if cl<pl*(1-buffer) else 0)
                if side:
                    days[day]=(k+5,side)
                    break
        out[(mode,buffer)]=days
    return out
def replay(x,events,cfg):
    mode,buf,tp,sl,hold=cfg
    o=x.open.to_numpy(float);h=x.high.to_numpy(float);l=x.low.to_numpy(float);c=x.close.to_numpy(float);t=x.time.to_numpy(np.int64)
    eq=1000.;rows=[]
    for day in range(len(x)//1440):
        old=eq;net=fees=funding=0.;traded=0
        if day in events:
            k,side=events[day]
            entry=o[k]*(1+side*SLIP)
            qty=min(eq*RISK/(sl*entry),eq*LEV/entry)
            stop=entry*(1-side*sl);target=entry*(1+side*tp)
            last=min(k+hold,(day+1)*1440)
            j=last-1;px=c[j]
            for v in range(k,last):
                if side==1:
                    if l[v]<=stop:j=v;px=min(o[v],stop);break
                    if h[v]>=target:j=v;px=target;break
                else:
                    if h[v]>=stop:j=v;px=max(o[v],stop);break
                    if l[v]<=target:j=v;px=target;break
            ex=px*(1-side*SLIP)
            fees=qty*FEE*(entry+ex)
            funding=qty*FUND*ex*sum(t[v]%28800==0 for v in range(k,j+1))
            net=side*qty*(ex-entry)-fees-funding
            eq+=net;traded=1
        rows.append((day,old,eq,net,fees,funding,traded))
    return np.array(rows,float)
def score(sym,cfg,rows,year):
    z=rows[:365] if year==2025 else rows[365:]
    x=z[:,3];win=x[x>1e-8];loss=x[x<-1e-8];n=len(z)
    eq=np.r_[z[0,1],z[:,2]]
    pf=float(win.sum()/-loss.sum()) if len(loss) else None
    streak=mx=0
    for v in x:
        streak=streak+1 if v<-1e-8 else 0;mx=max(mx,streak)
    mode,buf,tp,sl,hold=cfg
    return dict(symbol=sym,year=year,mode=mode,buffer=buf,target=tp,stop=sl,hold_min=hold,
      days=n,trades=int(z[:,6].sum()),profitable_days=len(win),losing_days=len(loss),
      no_trade_days=n-int(z[:,6].sum()),profitable_calendar_day_pct=round(100*len(win)/n,3),
      win_rate_traded_pct=round(100*len(win)/max(1,len(win)+len(loss)),3),
      net_profit_usd=round(eq[-1]-eq[0],3),net_return_pct=round(100*(eq[-1]/eq[0]-1),4),
      profit_factor=round(pf,4) if pf is not None else None,
      mean_daily_usd=round(float(x.mean()),4),median_daily_usd=round(float(np.median(x)),4),
      worst_day_usd=round(float(x.min()),4),max_consecutive_losing_days=mx,
      max_dayclose_drawdown_pct=round(100*float(np.min(eq/np.maximum.accumulate(eq)-1)),4),
      fees_usd=round(float(z[:,4].sum()),4),funding_debit_usd=round(float(z[:,5].sum()),4))
def main():
    allrows=[];selected=[];months=[];quality=[]
    configs=list(itertools.product(MODES,BUFFER,TAKE,STOP,HOLD))
    for sym in ("BTCUSD","ETHUSD"):
        x,q=load(sym);quality.append(q)
        ev=signals(x);models={}
        for cfg in configs:
            r=replay(x,ev[cfg[:2]],cfg)
            a=score(sym,cfg,r,2025);b=score(sym,cfg,r,2026)
            allrows.extend((a,b));models[cfg]=(r,a,b)
        eligible=[(k,v) for k,v in models.items() if v[1]["trades"]>=50 and v[1]["profit_factor"] is not None and v[1]["profit_factor"]>1 and v[1]["net_return_pct"]>0]
        passed=bool(eligible)
        pick=max(eligible,key=lambda kv:(kv[1][1]["profitable_calendar_day_pct"],kv[1][1]["net_return_pct"])) if passed else max(models.items(),key=lambda kv:(kv[1][1]["net_return_pct"],kv[1][1]["profitable_calendar_day_pct"]))
        cfg,(r,a,b)=pick
        selected.extend([{**a,"train_pass":passed},{**b,"train_pass":passed}])
        dates=pd.date_range("2025-01-01","2026-11-17",freq="D",tz="UTC")
        labels=dates.strftime("%Y-%m")
        for month in pd.unique(labels):
            z=r[labels==month]
            months.append(dict(symbol=sym,month_utc=month,return_pct=round(100*(z[-1,2]/z[0,1]-1),4),
                net_usd=round(float(z[:,3].sum()),3),profitable_days=int((z[:,3]>1e-8).sum()),
                losing_days=int((z[:,3]<-1e-8).sum()),no_trade_days=int((z[:,6]==0).sum()),
                fees_usd=round(float(z[:,4].sum()),3)))
        print("SELECTED",sym,cfg,"2025_eligible",passed,a,b,flush=True)
    pd.DataFrame(allrows).to_csv(OUT/"summary.csv",index=False)
    pd.DataFrame(selected).to_csv(OUT/"selected.csv",index=False)
    pd.DataFrame(months).to_csv(OUT/"selected_monthly.csv",index=False)
    metadata=dict(hypothesis="Previous UTC day high/low acceptance breakout versus liquidity sweep reclaim; one trade per day",
       models_per_symbol=len(configs),source=quality,
       assumptions=dict(taker_fee_each_side_including_GST=FEE,adverse_slippage_each_side=SLIP,
          funding_debit_per_8h_boundary=FUND,stop_risk_fraction=RISK,max_notional_leverage=LEV,
          intraminute_ambiguity="stop-first"),
       caveats=["2026 is research-exposed, not pristine forward validation",
          "Funding proxy, no actual funding rates", "No order book or precise margin/liquidation model",
          "No exchange lot-size or tick-size rounding",
          "Calendar days with no trade are NOT counted as profitable",
          "No guarantee of positive daily profit"],
       selection="Only 2025 selects settings; 2026 settings fixed unchanged")
    (OUT/"quality.json").write_text(json.dumps(metadata,indent=2)+"\n")
    (OUT/"REPORT.md").write_text("# Independent prior-day extreme liquidity sweep\n\n"+
        pd.DataFrame(selected).to_string(index=False)+"\n\n"+
        "## Caveats\n"+"\n".join("- "+c for c in metadata["caveats"])+"\n")
    print("COMPLETE",len(allrows),"year rows",flush=True)
if __name__=="__main__":main()
