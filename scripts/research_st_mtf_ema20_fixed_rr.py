"""Causal BTCUSD 15m/1h Supertrend + EMA20 fixed RR research."""
from pathlib import Path
import numpy as np
import pandas as pd
import json
ROOT=Path("data/delta_india/BTCUSD/2024_verified_archive")
OUT=Path("analysis/st_mtf_ema20_fixed_rr")
OUT.mkdir(parents=True,exist_ok=True)
START=pd.Timestamp("2024-03-01",tz="Asia/Kolkata").tz_convert("UTC")
END=pd.Timestamp("2025-01-01",tz="Asia/Kolkata").tz_convert("UTC")
FEE=.0005*1.18
PAIRS=[(100,200),(100,300),(100,400),(200,400),(200,600),(200,800),(300,600),(300,900),(300,1200),(400,800),(400,1200),(500,1000),(500,1500)]
def read(folder):
    parts=[]
    for month in pd.period_range("2024-03","2024-12",freq="M"):
        x=pd.read_csv(folder/f"{month}.csv.gz")
        x.index=pd.to_datetime(x.pop("time").astype("int64"),unit="s",utc=True)
        parts.append(x)
    d=pd.concat(parts).sort_index()
    if d.index.has_duplicates: raise ValueError("Duplicate timestamps "+str(folder))
    return d
d=read(ROOT/"trade_1m")
expected=pd.date_range(START,END,freq="min",inclusive="left")
if not d.index.equals(expected): raise ValueError(f"Missing/extra minutes: {len(expected.difference(d.index))}/{len(d.index.difference(expected))}")
if d[["open","high","low","close"]].isna().any().any(): raise ValueError("Missing OHLC")
def bars(n):
    b=d.resample(f"{n}min",label="right",closed="left").agg({"open":"first","high":"max","low":"min","close":"last"})
    c=b.close
    tr=pd.concat([b.high-b.low,(b.high-c.shift()).abs(),(b.low-c.shift()).abs()],axis=1).max(axis=1).to_numpy()
    a=np.full(len(b),np.nan);a[9]=np.mean(tr[:10])
    for i in range(10,len(b)): a[i]=(9*a[i-1]+tr[i])/10
    mid=(b.high.to_numpy()+b.low.to_numpy())/2
    u=mid+3*a;l=mid-3*a;close=c.to_numpy()
    trend=np.zeros(len(b),dtype=np.int8);trend[9]=-1
    for i in range(10,len(b)):
        if u[i]>=u[i-1] and close[i-1]<=u[i-1]:u[i]=u[i-1]
        if l[i]<=l[i-1] and close[i-1]>=l[i-1]:l[i]=l[i-1]
        trend[i]=1 if (trend[i-1]==-1 and close[i]>u[i]) or (trend[i-1]==1 and close[i]>=l[i]) else -1
    b["st"]=trend;b["ema"]=c.ewm(span=20,adjust=False,min_periods=20).mean()
    return b
b=bars(15);h=bars(60)
st15=b.st.reindex(d.index,method="ffill").fillna(0).to_numpy()
st60=h.st.reindex(d.index,method="ffill").fillna(0).to_numpy()
side=np.where(st15==st60,st15,0)
ema=b.ema.reindex(d.index,method="ffill").to_numpy()
cycles=np.cumsum(np.r_[True,side[1:]!=side[:-1]])
o,hi,lo,c=[d[k].to_numpy() for k in ["open","high","low","close"]]
wk=np.asarray(d.index.tz_convert("Asia/Kolkata").dayofweek<5)
ready=np.arange(len(d))>=60*100
prev=np.r_[np.nan,c[:-1]]
touch=(side!=0)&((side*(prev-ema)>0)&(side*(o-ema)>=0))&(lo<=ema)&(hi>=ema)
# Touch observed on a completed 1m bar; entry at following open.
touch_signal=np.r_[False,touch[:-1]]&(side==np.r_[0,side[:-1]])
# Reclaim uses EMA fixed at start of completed 15m candle and trend alignment at entry.
e=b.ema.shift()
rl=(b.close.shift()>e)&(b.low<=e)&(b.high>=e)&(b.close>e)
rs=(b.close.shift()<e)&(b.low<=e)&(b.high>=e)&(b.close<e)
rec=(rl.astype(int)-rs.astype(int)).reindex(d.index).fillna(0).to_numpy()
signals={"touch":touch_signal,"reclaim":(rec!=0)&(rec==side)}
# Repo funding history is an indicative percent rate, NOT payment ledger.
fund=read(ROOT/"funding_1h").close
settle=(d.index.minute==0)&(d.index.hour%8==0)
rate=fund.shift(1,freq="h").reindex(d.index).to_numpy()/100
valid=np.isfinite(rate)
cash=np.where(settle&valid,rate*o,0.)
missing=settle&~valid
cum=np.r_[0.,np.cumsum(cash)]
miss=np.r_[0,np.cumsum(missing)]
month=d.index.tz_convert("Asia/Kolkata").strftime("%Y-%m").to_numpy()
months=pd.period_range("2024-03","2024-12",freq="M").astype(str).tolist()
rows=[];alltr=[]
for name,mask in signals.items():
    entries=np.flatnonzero(mask&wk&ready&(side!=0))
    for sl,tp in PAIRS:
        last=-1;lastcycle=-1;tr=[]
        for j in entries:
            if j<=last or cycles[j]==lastcycle: continue
            s=int(side[j]);entry=o[j];stop=entry-s*sl;target=entry+s*tp
            lastcycle=cycles[j]
            for k in range(j,len(d)):
                # Weekend exits remain enabled; no new weekend entries.
                if s*(o[k]-stop)<=0: px=o[k];why="stop_gap";break
                hitstop=lo[k]<=stop if s==1 else hi[k]>=stop
                hittp=hi[k]>=target if s==1 else lo[k]<=target
                if hitstop: px=stop;why="stop";break
                if hittp: px=target;why="target";break
            else:
                k=len(d)-1;px=c[k];why="end_mark"
            last=k
            # Conservative funding boundary: exclude entry minute; include exit minute.
            funding=-s*(cum[k+1]-cum[j+1])
            missing_count=int(miss[k+1]-miss[j+1])
            gross=s*(px-entry)
            standard=gross-FEE*(entry+px)
            offer=gross-FEE*entry-(0 if k-j<29 else FEE*px)
            tr.append((name,sl,tp,str(d.index[j]),str(d.index[k]),month[k],s,entry,px,why,gross,standard,offer,funding,missing_count))
        alltr.extend(tr)
        x=pd.DataFrame(tr,columns=["entry","sl","tp","entry_time","exit_time","month","side","entry_price","exit_price","reason","gross","standard","offer","funding_proxy","missing_funding"])
        for fee in ["standard","offer"]:
            net=x[fee]+x.funding_proxy
            monthly=net.groupby(x.month).sum().reindex(months,fill_value=0)
            run=np.r_[0.,net.cumsum().to_numpy()]
            dd=(np.maximum.accumulate(run)-run).max()
            loss=-net[net<0].sum()
            for period,ms in [("all",months)]:
                ix=x.month.isin(ms);v=net[ix];m=monthly.loc[ms]
                curve=np.r_[0.,v.cumsum().to_numpy()]
                denom=-v[v<0].sum()
                rows.append(dict(entry=name,sl=sl,tp=tp,fee=fee,period=period,trades=len(v),win_pct=100*(v>0).mean(),net_points=v.sum(),profit_factor=v[v>0].sum()/denom if denom else np.nan,max_closed_trade_dd_points=(np.maximum.accumulate(curve)-curve).max(),positive_months=int((m>0).sum()),negative_months=int((m<0).sum()),flat_months=int((m==0).sum()),missing_funding=int(x.loc[ix,"missing_funding"].sum()),**{key:float(value) for key,value in m.items()}))
cols=["entry","sl","tp","entry_time","exit_time","month","side","entry_price","exit_price","reason","gross","standard","offer","funding_proxy","missing_funding"]
pd.DataFrame(alltr,columns=cols).to_csv(OUT/"trades.csv.gz",index=False)
r=pd.DataFrame(rows)
r.to_csv(OUT/"summary.csv",index=False)
rank=r[(r.period=="all")&(r.fee=="standard")].sort_values(["positive_months","net_points"],ascending=False)
rank.to_csv(OUT/"ranked.csv",index=False)
print("STANDARD\n"+rank.iloc[:,:14].to_string(index=False))
print("OFFER WHATIF\n"+r[r.fee=="offer"].sort_values(["positive_months","net_points"],ascending=False).iloc[:,:14].to_string(index=False))
quality=dict(bars=len(d),start=str(d.index[0]),end=str(d.index[-1]),funding_missing_settlements=int(missing.sum()),fee=FEE,slippage=0,weekdays="IST entries only",entry_execution="next open after touch or reclaim confirmation",one_trade="per contiguous aligned trend",funding="indicative prior hourly rate, 8h settlement assumed, not reconciled",offer="hypothetical exit fee waiver for under 30 minutes",limitations="No margin/liquidation, spread, actual funding ledger, or intratrade drawdown; no guaranteed fills. January and February excluded due to gaps. March initial 100h warmup excluded. No 2025/2026 candles.")
(OUT/"quality.json").write_text(json.dumps(quality,indent=2))
