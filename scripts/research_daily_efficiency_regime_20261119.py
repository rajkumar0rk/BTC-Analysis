#!/usr/bin/env python3
"""Novel hypothesis: intraday Kaufman efficiency ratio detects low-noise trends;
enter first efficient 30/60-minute trend after 06:00 UTC, target/stop in ATR
units, exit within day. No VWAP, wicks, cross-asset lag or previous-day box.
Completed 5m signals, next 1m open; 2025 train only, 2026 fixed replay.
Conservative taker 0.05%/side + 18% GST; 2bp slip each side, 1bp
funding debit per crossed 8h settlement. One trade per UTC calendar day.
"""
from pathlib import Path
import itertools,json
import numpy as np,pandas as pd
ROOT=Path("data/delta_india");OUT=Path("analysis/daily_efficiency_regime_20261119")
OUT.mkdir(parents=True,exist_ok=True)
FEE=.0005*1.18;SLIP=.0002;FUND=.0001
CAP=1000.;RISK=.005;MAXLEV=2.
START=1735689600;END=1794960000
LOOKS=(6,12,24)
ER=(.35,.5,.65)
MODE=("trend","fade")
TARGET=(.003,.006)
STOP=(.003,.005)
HOLD=(60,180)
def load(sym):
    files=sorted((ROOT/sym/"1m").glob("20??-??.csv.gz"))
    d=pd.concat([pd.read_csv(f,compression="gzip",usecols=["time","open","high","low","close","volume"]) for f in files],ignore_index=True)
    d=d[(d.time>=START)&(d.time<END)].sort_values("time").reset_index(drop=True)
    t=d.time.to_numpy(np.int64)
    if len(t)%1440 or t[0]!=START or t[-1]!=END-60 or not np.all(np.diff(t)==60):
        raise ValueError("Nonconsecutive minute data "+sym)
    a=d[["open","high","low","close","volume"]].to_numpy(float)
    if not np.isfinite(a).all() or np.any(a[:,1]<a[:,2]) or np.any(a[:,0]>a[:,1]) or np.any(a[:,0]<a[:,2]) or np.any(a[:,3]>a[:,1]) or np.any(a[:,3]<a[:,2]):
        raise ValueError("Invalid bars")
    return d,dict(symbol=sym,rows=len(d),months=len(files),first=int(t[0]),last=int(t[-1]),missing_minutes=0)
def events(d):
    t=pd.to_datetime(d.time,unit="s",utc=True)
    bars=d.set_index(t)[["open","high","low","close","volume"]].resample("5min",closed="left",label="left").agg({"open":"first","high":"max","low":"min","close":"last","volume":"sum"})
    assert len(bars)*5==len(d)
    c=bars.close
    changes=c.diff().abs()
    out={};stats={}
    for look in LOOKS:
        path=changes.rolling(look,min_periods=look).sum()
        ratio=(c-c.shift(look)).abs()/path.replace(0,np.nan)
        direction=np.sign(c-c.shift(look))
        for er,mode in itertools.product(ER,MODE):
            valid=(ratio>=er)&np.isfinite(ratio)&(direction!=0)
            indices=np.flatnonzero(valid.to_numpy())
            byday={}
            for i in indices:
                k=(int(i)+1)*5
                if k>=len(d):continue
                minute=k%1440
                if minute<360 or minute>=1200:continue
                day=k//1440
                if day not in byday:
                    sd=int(direction.iloc[i])*(1 if mode=="trend" else -1)
                    byday[day]=(k,sd)
            out[(look,er,mode)]=byday
            stats[str((look,er,mode))]=len(byday)
    return out,stats
def replay(d,ev,tp,sl,hold):
    o=d.open.to_numpy(float);h=d.high.to_numpy(float);l=d.low.to_numpy(float);c=d.close.to_numpy(float);t=d.time.to_numpy(np.int64)
    eq=CAP;rows=[]
    for day in range(len(t)//1440):
        prev=eq;net=fees=funding=0.;traded=0
        if day in ev and eq>0:
            k,side=ev[day];entry=o[k]*(1+side*SLIP)
            qty=min(eq*RISK/(entry*sl),eq*MAXLEV/entry)
            st=entry*(1-side*sl);target=entry*(1+side*tp)
            end=min(k+hold,(day+1)*1440)
            j=end-1;px=c[j]
            for z in range(k,end):
                if side==1:
                    if l[z]<=st:j=z;px=min(o[z],st);break
                    if h[z]>=target:j=z;px=target;break
                else:
                    if h[z]>=st:j=z;px=max(o[z],st);break
                    if l[z]<=target:j=z;px=target;break
            exitfill=px*(1-side*SLIP)
            fees=FEE*qty*(entry+exitfill)
            funding=FUND*qty*exitfill*sum(1 for z in range(k,j+1) if t[z]%28800==0)
            net=qty*side*(exitfill-entry)-fees-funding
            eq+=net;traded=1
        rows.append((day,t[day*1440],prev,eq,net,fees,funding,traded))
    return np.array(rows)
def metrics(r,sym,cfg,year):
    x=r[:365] if year==2025 else r[365:]
    pnl=x[:,4];wins=pnl[pnl>1e-8];loss=pnl[pnl<-1e-8]
    nav=np.r_[x[0,2],x[:,3]]
    pf=float(wins.sum()/-loss.sum()) if len(loss) else None
    streak=mx=0
    for v in pnl:
        streak=streak+1 if v<-1e-8 else 0;mx=max(mx,streak)
    look,er,mode,tp,sl,hold=cfg
    return dict(symbol=sym,year=year,lookback_5m=look,efficiency_threshold=er,mode=mode,tp=tp,sl=sl,hold_minutes=hold,
      days=len(x),trades=int(x[:,7].sum()),profitable_days=len(wins),losing_days=len(loss),
      no_trade_days=int(len(x)-x[:,7].sum()),profitable_calendar_day_pct=round(100*len(wins)/len(x),3),
      win_rate_traded_pct=round(100*len(wins)/max(1,len(wins)+len(loss)),3),
      net_return_pct=round(100*(x[-1,3]/x[0,2]-1),4),
      net_profit_usd=round(float(x[-1,3]-x[0,2]),3),
      mean_calendar_day_net_usd=round(float(pnl.mean()),4),median_calendar_day_net_usd=round(float(np.median(pnl)),4),
      worst_day_usd=round(float(pnl.min()),4),max_losing_day_streak=mx,
      profit_factor=round(pf,4) if pf is not None else None,
      max_dayclose_drawdown_pct=round(100*float(np.min(nav/np.maximum.accumulate(nav)-1)),4),
      fees_usd=round(float(x[:,5].sum()),3),funding_proxy_usd=round(float(x[:,6].sum()),3))
def main():
    allrows=[];selected=[];monthly=[];qualities=[]
    for sym in ("BTCUSD","ETHUSD"):
        d,q=load(sym);e,stats=events(d);q["signals_per_config"]=stats;qualities.append(q)
        models={}
        for cfg in itertools.product(LOOKS,ER,MODE,TARGET,STOP,HOLD):
            r=replay(d,e[cfg[:3]],*cfg[3:])
            a=metrics(r,sym,cfg,2025);b=metrics(r,sym,cfg,2026)
            allrows.extend([a,b]);models[cfg]=(r,a,b)
        good=[(cfg,v) for cfg,v in models.items() if v[1]["trades"]>=50 and v[1]["net_return_pct"]>0 and (v[1]["profit_factor"] or 0)>1]
        passed=bool(good)
        cfg,(r,a,b)=max(good if good else models.items(),key=lambda x:(x[1][1]["profitable_calendar_day_pct"],x[1][1]["net_return_pct"]) if passed else (x[1][1]["net_return_pct"],x[1][1]["profitable_calendar_day_pct"]))
        selected.extend([{**a,"passes_2025_selection":passed},{**b,"passes_2025_selection":passed}])
        monthnames=pd.to_datetime(r[:,1].astype(np.int64),unit="s",utc=True).strftime("%Y-%m")
        for m in pd.unique(monthnames):
            z=r[monthnames==m];monthly.append(dict(symbol=sym,month=m,return_pct=round(100*(z[-1,3]/z[0,2]-1),4),trades=int(z[:,7].sum()),profit_days=int(np.sum(z[:,4]>1e-8)),loss_days=int(np.sum(z[:,4]<-1e-8)),no_trade_days=int(np.sum(z[:,7]==0))))
        print("SELECTED",sym,cfg,a,b,flush=True)
    pd.DataFrame(allrows).to_csv(OUT/"summary.csv",index=False)
    pd.DataFrame(selected).to_csv(OUT/"selected.csv",index=False)
    pd.DataFrame(monthly).to_csv(OUT/"selected_monthly.csv",index=False)
    quality=dict(hypothesis="Kaufman efficiency ratio intraday trend vs fade",input=qualities,
      models_per_asset=len(LOOKS)*len(ER)*len(MODE)*len(TARGET)*len(STOP)*len(HOLD),
      train_selection="positive 2025 net, PF>1, >=50 trades then highest positive calendar day fraction; otherwise highest 2025 net",
      evaluation_check="fixed params, research-exposed not untouched holdout",
      costs=dict(taker_fee_plus_GST_per_side=FEE,adverse_slippage_per_side=SLIP,funding_debit_per_8h_boundary=FUND),
      risk=dict(stop_risk_per_trade=RISK,max_notional_leverage=MAXLEV,one_trade_per_UTC_day=True),
      limitations=["No guaranteed daily net profit","1m intrabar ambiguous stop-first","No orderbook, real funding, precise lot/margin, or liquidation engine","2026 through Nov 17 UTC only"])
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2))
    (OUT/"REPORT.md").write_text("# Independent efficiency regime daily-profit test\n\n"+pd.DataFrame(selected).to_string(index=False)+"\n\n"+json.dumps(quality,indent=2))
    print("FINISHED",len(allrows),"year-model rows",flush=True)
if __name__=="__main__":main()
