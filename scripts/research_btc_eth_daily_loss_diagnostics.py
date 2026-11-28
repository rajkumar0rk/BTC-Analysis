"""Independent reconstructed baseline screen. Never load 2026. No live orders."""
import calendar,itertools,json
from pathlib import Path
import numpy as np
import pandas as pd
from numba import njit
ROOT=Path("data/delta_india")
OUT=Path("scratch/daily_loss_diagnostics"); OUT.mkdir(parents=True,exist_ok=True)
FEE=.00059
FUND=.0001/480 # adverse illustrative 0.01% per 8h, not actual settlements
NAMES=["vwap","ema9_21","bollinger_rsi","breakout_retest","liquidity_sweep"]
FLAGS=["trend","atr_expansion","volume","confirmation","profit_protection","one_trade_day","no_time_cap"]
def load(symbol,year,month):
    key=f"{year}-{month:02d}"
    candidates=[ROOT/symbol/"1m"/f"{key}.csv.gz"] if year==2025 else [ROOT/symbol/"2024_verified_archive"/"trade_1m"/f"{key}.csv.gz",ROOT/"2024_recovery_candidates"/symbol/key/"trade_1m.csv.gz"]
    start=int(pd.Timestamp(key+"-01",tz="UTC").timestamp()); n=calendar.monthrange(year,month)[1]*1440
    for p in candidates:
        if not p.exists(): continue
        df=pd.read_csv(p)
        if not set(["time","open","high","low","close","volume"]).issubset(df): continue
        if len(df)!=n or not np.array_equal(df.time.to_numpy(),start+60*np.arange(n)): continue
        a=df[["open","high","low","close","volume"]].to_numpy(float)
        if not np.isfinite(a).all() or not ((a[:,2]>0)&(a[:,2]<=np.minimum(a[:,0],a[:,3]))&(np.maximum(a[:,0],a[:,3])<=a[:,1])&(a[:,4]>=0)).all(): continue
        return a,str(p)
    return None,None
def indicators(a):
    m=pd.DataFrame(a,columns=["o","h","l","c","v"])
    b=m.groupby(m.index//15).agg({"o":"first","h":"max","l":"min","c":"last","v":"sum"})
    c=b.c; h=b.h; l=b.l; v=b.v
    ema9=c.ewm(span=9,adjust=False,min_periods=9).mean()
    ema21=c.ewm(span=21,adjust=False,min_periods=21).mean()
    tr=pd.concat([h-l,(h-c.shift()).abs(),(l-c.shift()).abs()],axis=1).max(axis=1)
    atr=tr.ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    delta=c.diff(); up=delta.clip(lower=0).ewm(alpha=1/14,adjust=False,min_periods=14).mean(); down=(-delta.clip(upper=0)).ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    rsi=100-100/(1+up/down)
    mean=c.rolling(20).mean(); sd=c.rolling(20).std(ddof=0)
    vwap=(((h+l+c)/3*v).groupby(b.index//96).cumsum()/v.groupby(b.index//96).cumsum())
    hi=h.shift(2).rolling(20).max(); lo=l.shift(2).rolling(20).min()
    def sign(L,S): return L.fillna(False).to_numpy(np.int8)-S.fillna(False).to_numpy(np.int8)
    signals=np.array([
        sign((c>vwap)&(c.shift()<=vwap.shift()),(c<vwap)&(c.shift()>=vwap.shift())),
        sign((ema9>ema21)&(ema9.shift()<=ema21.shift()),(ema9<ema21)&(ema9.shift()>=ema21.shift())),
        sign((c<mean-2*sd)&(rsi<30),(c>mean+2*sd)&(rsi>70)),
        sign((c.shift()>hi)&(l<=hi+.2*atr)&(c>hi),(c.shift()<lo)&(h>=lo-.2*atr)&(c<lo)),
        sign((l<l.shift().rolling(20).min())&(c>l.shift().rolling(20).min()),(h>h.shift().rolling(20).max())&(c<h.shift().rolling(20).max()))
    ])
    hourly=b.groupby(b.index//4).c.last()
    e=hourly.ewm(span=20,adjust=False,min_periods=20).mean()
    ht=sign(hourly>e,hourly<e)
    # At a completed 15m close, only the last fully completed hourly bar is visible.
    trend=np.zeros(len(b),np.int8)
    for j in range(3,len(b)): trend[j]=ht[(j+1)//4-1]
    return signals,atr.to_numpy(),trend,(atr>atr.shift().rolling(20).mean()).to_numpy(),(v>=1.25*v.shift().rolling(20).mean()).to_numpy(),sign(c>b.o,c<b.o),np.sign(ema9-ema21).fillna(0).to_numpy()
@njit
def replay(a,sig,atr,trend,expand,volume,body,ema,mask,side,hold,regime,fee):
    days=len(a)//1440
    daily=np.zeros(days); equity=1.; peak=1.; dd=0.; gross=0.; costs=0.; wins=0; trades=0; posgain=0.; negloss=0.; longnet=0.; shortnet=0.; exitcounts=np.zeros(5,np.int64)
    i=15*80
    count=np.zeros(days,np.int64)
    while i<len(a)-1:
        if i%15: i+=1; continue
        day=i//1440
        if (mask&32 and count[day]) or daily[day]>=.01 or daily[day]<=-.005: i+=15; continue
        j=i//15-1
        d=sig[j] if not(mask&8) else sig[j-1]
        if not d or (side and d!=side) or not np.isfinite(atr[j]) or atr[j]<=0: i+=15; continue
        if (mask&1 and trend[j]!=d) or (mask&2 and not expand[j]) or (mask&4 and not volume[j]) or (mask&8 and body[j]!=d) or (regime==1 and trend[j]!=d) or (regime==2 and trend[j]!=0 and trend[j]==d): i+=15; continue
        ep=a[i,0]; risk=1.5*atr[j]; stop=ep-d*risk; target=ep+d*2*risk
        qty=min(.0025*equity/risk,equity/ep) # fractional 1x notional cap
        best=ep; end=min(len(a)-1,i+(1440 if mask&64 else hold)); x=end; xp=a[end,3]; why=2
        for k in range(i,end+1):
            o,h,l,c=a[k,0],a[k,1],a[k,2],a[k,3]
            if d*(o-stop)<=0: x=k;xp=o;why=0;break
            if d*(o-target)>=0: x=k;xp=target;why=1;break
            if mask&64 and k>i and k%15==0 and (sig[k//15-1]==-d or ema[k//15-1]==-d):
                x=k;xp=o;why=3;break
            seq=(o,l,h,c) if c>o or (c==o and o-l<=h-o) else (o,h,l,c)
            hit=False
            for u in range(3):
                z=seq[u+1]
                if d*(z-stop)<=0:
                    x=k;xp=stop;why=0;hit=True;break
                if d*(z-target)>=0:
                    x=k;xp=target;why=1;hit=True;break
                if d*(z-best)>0: best=z
                if mask&16 and d*(best-ep)>=risk:
                    lock=ep*(d+fee)/(d-fee)
                    if d*(lock-stop)>0:stop=lock
            if hit:break
        g=d*(xp-ep)*qty; cost=(fee*(ep+xp)+FUND*ep*(x-i+1))*qty if fee else 0.
        net=g-cost; gross+=g;costs+=cost; equity+=net
        daily[x//1440]+=net;count[day]+=1
        trades+=1;wins+=int(net>0);exitcounts[why]+=1
        if net>0:posgain+=net
        else:negloss-=net
        if d==1:longnet+=net
        else:shortnet+=net
        peak=max(peak,equity);dd=max(dd,(peak-equity)/peak)
        i=x+1
    return (equity-1,gross,costs,trades,wins,posgain,negloss,dd,int(np.sum(daily>0)),int(np.sum(daily<0)),int(np.sum(daily==0)),longnet,shortnet,*exitcounts)
def main():
    results=[]; coverage=[]
    for symbol in ("BTCUSD","ETHUSD"):
        for year in (2024,2025):
            for month in range(1,13):
                a,source=load(symbol,year,month)
                coverage.append({"symbol":symbol,"year":year,"month":month,"complete":a is not None,"source":source})
                if a is None:
                    if year==2025: raise ValueError(f"Incomplete required month {symbol} {year}-{month}")
                    continue
                sig,atr,trend,expand,volume,body,ema=indicators(a)
                for k,name in enumerate(NAMES):
                    # 128 coarse structural combinations, plus isolated diagnostic controls.
                    plans=[(mask,0,60,0,FEE,"factorial") for mask in range(128)]
                    plans += [(0,0,60,0,0.,"no_cost"),(0,1,60,0,FEE,"long_only"),(0,-1,60,0,FEE,"short_only"),(0,0,60,1,FEE,"aligned"),(0,0,60,2,FEE,"not_aligned"),(0,0,240,0,FEE,"240min"),(0,0,480,0,FEE,"480min")]
                    for mask,side,hold,regime,fee,test in plans:
                        vals=replay(a,sig[k],atr,trend,expand,volume,body,ema,mask,side,hold,regime,fee)
                        row=dict(zip(("net","gross","cost","trades","wins","gain","loss","realized_dd","positive_days","negative_days","zero_net_days","long_net","short_net","stop","target","timeout","reversal","unused"),vals))
                        row.update(symbol=symbol,year=year,month=month,strategy=name,mask=mask,test=test,flags="+".join(x for bit,x in enumerate(FLAGS) if mask&(1<<bit)) or "baseline")
                        results.append(row)
                print(f"processed {symbol} {year}-{month:02d}",flush=True)
    df=pd.DataFrame(results); df.to_csv(OUT/"monthly.csv",index=False)
    summary=df.groupby(["symbol","year","strategy","mask","test","flags"],dropna=False).agg(net=("net",lambda x:np.prod(1+x)-1),gross=("gross","sum"),cost=("cost","sum"),trades=("trades","sum"),wins=("wins","sum"),gain=("gain","sum"),loss=("loss","sum"),positive_days=("positive_days","sum"),negative_days=("negative_days","sum"),zero_net_days=("zero_net_days","sum"),profitable_months=("net",lambda x:int((x>0).sum())),months=("month","count"),max_month_realized_dd=("realized_dd","max"),long_net=("long_net","sum"),short_net=("short_net","sum")).reset_index()
    summary["pf"]=summary.gain/summary.loss.replace(0,np.nan)
    summary.to_csv(OUT/"yearly.csv",index=False)
    pair=summary[summary.test=="factorial"].pivot(index=["symbol","strategy","mask","flags"],columns="year",values="net").reset_index()
    pair.columns=["symbol","strategy","mask","flags","net2024","net2025"]
    pair["both_profitable"]=(pair.net2024>0)&(pair.net2025>0)
    pair["min_return"]=pair[["net2024","net2025"]].min(axis=1)
    pair.sort_values("min_return",ascending=False).to_csv(OUT/"ranked.csv",index=False)
    (OUT/"coverage.json").write_text(json.dumps(coverage,indent=2))
    print("coverage",json.dumps(coverage),flush=True)
    print("both profitable count",int(pair.both_profitable.sum()),flush=True)
    print("baseline diagnostics",summary[(summary.mask==0)].to_json(orient="records"),flush=True)
    print("ranked",pair.sort_values("min_return",ascending=False).head(20).to_json(orient="records"),flush=True)
if __name__=="__main__":main()
