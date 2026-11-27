"""Six independent trend/expansion strategies; two timeframes; common unbounded exit.
No threshold optimization, no 2026, no live orders.
"""
import csv,gzip,hashlib,json,math
from pathlib import Path
import numpy as np
from numba import njit
import research_rsi14_80_20_2025 as data25
import research_rsi14_reversal_multiple_r_2024 as data24
from research_rsi14_80_20_2025 import dt,FEE
OUT=Path("scratch/independent_big_move")
TICK=.5
FAMILIES=("ema-pullback","compression-breakout","breakout-retest","failed-breakout","momentum-ignition","donchian")
RULES={
"ema-pullback":"EMA20 above EMA50; previous close at/below EMA20, current close above EMA20; mirror short.",
"compression-breakout":"BB20 +/-2 population SD inside EMA20 +/-1.5 ATR14; trade first release close beyond the completed squeeze range.",
"breakout-retest":"Close beyond prior 20-bar range; on a later bar retest level and close back outside; expire after 20 bars or opposite breakout.",
"failed-breakout":"Wick beyond prior 20-bar range and close back inside; directional rejection candle; ambiguous double sweep ignored.",
"momentum-ignition":"5-bar ROC crosses zero in trade direction; true range above prior ATR14; close beyond previous candle extreme.",
"donchian":"Close beyond prior 20 completed candles' high or low; fresh qualifying close can trigger after exit."
}

def read_bars(reader,start,end):
    n=(end-start)//60;bars=np.empty((4,n),dtype=np.float64);i=-1
    for i,(t,o,h,l,c,v) in enumerate(reader()):
        assert t==start+i*60
        bars[:,i]=float(o),float(h),float(l),float(c)
    assert i+1==n
    return bars

def ema(x,p):
    out=np.full(len(x),np.nan)
    if len(x)>=p:
        out[p-1]=np.mean(x[:p])
        for i in range(p,len(x)):out[i]=out[i-1]+2/(p+1)*(x[i]-out[i-1])
    return out

def features(bars,tf):
    assert bars.shape[1]%tf==0
    O,H,L,C=(x.reshape(-1,tf) for x in bars)
    o=O[:,0];h=H.max(axis=1);l=L.min(axis=1);c=C[:,-1]
    tr=h-l;tr[1:]=np.maximum(tr[1:],np.maximum(abs(h[1:]-c[:-1]),abs(l[1:]-c[:-1])))
    atr=np.full(len(c),np.nan)
    if len(c)>=14:
        atr[13]=np.mean(tr[:14])
        for i in range(14,len(c)):atr[i]=(13*atr[i-1]+tr[i])/14
    e20=ema(c,20);e50=ema(c,50)
    high20=np.full(len(c),np.nan);low20=high20.copy();high10=high20.copy();low10=high20.copy()
    bbmid=high20.copy();bbstd=high20.copy()
    for i in range(len(c)):
        if i>=19:
            w=c[i-19:i+1];bbmid[i]=np.mean(w);bbstd[i]=np.std(w)
        if i>=20:high20[i]=max(h[i-20:i]);low20[i]=min(l[i-20:i])
        if i>=9:high10[i]=max(h[i-9:i+1]);low10[i]=min(l[i-9:i+1])
    roc=np.full(len(c),np.nan);roc[5:]=c[5:]/c[:-5]-1
    return dict(o=o,h=h,l=l,c=c,tr=tr,atr=atr,e20=e20,e50=e50,high20=high20,low20=low20,
                high10=high10,low10=low10,bbmid=bbmid,bbstd=bbstd,roc=roc)

def signals(f):
    o,h,l,c,tr,atr,e20,e50,hi,lo,mid,sd,roc=(f[k] for k in ("o","h","l","c","tr","atr","e20","e50","high20","low20","bbmid","bbstd","roc"))
    out={name:np.zeros(len(c),dtype=np.int8) for name in FAMILIES}
    squeezed=False;sh=sl=0.;pending=None
    for i in range(1,len(c)):
        if not np.isfinite(atr[i]):continue
        up=c[i]>hi[i];down=c[i]<lo[i]
        out["donchian"][i]=1 if up else -1 if down else 0
        if e20[i]>e50[i] and c[i-1]<=e20[i-1] and c[i]>e20[i]:out["ema-pullback"][i]=1
        elif e20[i]<e50[i] and c[i-1]>=e20[i-1] and c[i]<e20[i]:out["ema-pullback"][i]=-1
        sq=(mid[i]+2*sd[i]<e20[i]+1.5*atr[i] and mid[i]-2*sd[i]>e20[i]-1.5*atr[i])
        if sq:
            sh=max(sh,h[i]) if squeezed else h[i];sl=min(sl,l[i]) if squeezed else l[i]
        elif squeezed:
            out["compression-breakout"][i]=1 if c[i]>sh else -1 if c[i]<sl else 0
        squeezed=bool(sq)
        if pending is not None:
            d,k,level=pending
            if i-k>20 or (d==1 and down) or (d==-1 and up):pending=None
            elif (d==1 and l[i]<=level<c[i]) or (d==-1 and h[i]>=level>c[i]):
                out["breakout-retest"][i]=d;pending=None
        if pending is None:
            if up:pending=(1,i,hi[i])
            elif down:pending=(-1,i,lo[i])
        inside=lo[i]<=c[i]<=hi[i]
        sweep_up=h[i]>hi[i];sweep_down=l[i]<lo[i]
        if inside and sweep_down and not sweep_up and c[i]>o[i]:out["failed-breakout"][i]=1
        elif inside and sweep_up and not sweep_down and c[i]<o[i]:out["failed-breakout"][i]=-1
        if tr[i]>atr[i-1]:
            if roc[i-1]<=0<roc[i] and c[i]>h[i-1]:out["momentum-ignition"][i]=1
            elif roc[i-1]>=0>roc[i] and c[i]<l[i-1]:out["momentum-ignition"][i]=-1
    return out

@njit
def trade_exit(O,H,L,C,k,d,initial,high10,low10,tf):
    # Every update uses only the last completed signal candle. Stop never loosens.
    # One active stop, no target: candle-color order has no effect on stop touch.
    stop=initial
    for j in range(k,len(O)):
        if j%tf==0:
            z=j//tf-1
            if z>=0:
                level=low10[z] if d==1 else high10[z]
                if np.isfinite(level):
                    stop=max(stop,level) if d==1 else min(stop,level)
        if d*(O[j]-stop)<=0:return j,O[j],stop,1
        if (d==1 and L[j]<=stop) or (d==-1 and H[j]>=stop):return j,stop,stop,1
    return len(O)-1,C[-1],stop,2

def summarize(trades,months):
    p=[t["net_points"] for t in trades];r=[t["net_R"] for t in trades]
    def stats(a):
        gain=math.fsum(max(0,x) for x in a);loss=-math.fsum(min(0,x) for x in a);eq=peak=dd=0.
        for x in a:eq+=x;peak=max(peak,eq);dd=max(dd,peak-eq)
        return math.fsum(a),gain/loss if loss else None,dd
    net,pf,dd=stats(p);netr,pfr,ddr=stats(r)
    mp={m:0. for m in months};mr=mp.copy();counts={m:0 for m in months}
    for t in trades:
        m=t["entry_utc"][:7];mp[m]+=t["net_points"];mr[m]+=t["net_R"];counts[m]+=1
    wins=sum(x>0 for x in p);n=len(p)
    return dict(accounting="realized",open_position=None,trades=n,net=net,profit_factor=pf,wins=wins,win_rate=100*wins/n if n else 0,
        realized_drawdown_points=dd,net_R=netr,pf_R=pfr,drawdown_R=ddr,avg_R=netr/n if n else 0,
        monthly_entry_attribution=mp,monthly_R=mr,monthly_trade_counts=counts,profitable_months=sum(x>0 for x in mp.values()),
        profitable_R_months=sum(x>0 for x in mr.values()),trades_per_month=n/len(months),
        winners_3R=sum(x>=3 for x in r),winners_5R=sum(x>=5 for x in r),winners_10R=sum(x>=10 for x in r),
        best_trade_R=max(r,default=0),best_trade_points=max(p,default=0),gross_points=math.fsum(t["gross_points"] for t in trades),
        fees=math.fsum(t["fee_points"] for t in trades),mean_holding_minutes=math.fsum(t["holding_minutes"] for t in trades)/n if n else 0)

def replay(bars,f,sig,name,tf,start,end):
    O,H,L,C=bars;trades=[];free=0
    for i in np.flatnonzero(sig):
        k=(int(i)+1)*tf
        if k>=len(O) or k<free:continue
        d=int(sig[i]);ep=float(O[k]);risk=max(TICK,math.ceil(2*f["atr"][i]/TICK)*TICK)
        initial=ep-d*risk
        j,xp,stop,reason=trade_exit(O,H,L,C,k,d,initial,f["high10"],f["low10"],tf)
        free=j+1
        gross=d*(float(xp)-ep);fee=(ep+float(xp))*FEE;net=gross-fee
        trades.append(dict(entry_utc=dt(start+k*60).isoformat(),trigger_utc=dt(start+k*60).isoformat(),
            exit_utc=dt(end if reason==2 else start+j*60).isoformat(),side=d,entry_price=ep,exit_price=float(xp),stop_price=initial,
            final_stop=float(stop),target_price=None,gross_points=gross,fee_points=fee,net_points=net,net_R=net/risk,
            assumed_slippage_points=0,entry_reason=name,exit_reason="Initial/channel trailing stop" if reason==1 else "End of yearly evaluation",
            holding_minutes=int(j-k),signal_context=dict(initial_risk_points=risk,atr14=float(f["atr"][i]),signal_timeframe_minutes=tf),indicator_values={}))
    key=f"{name}-{tf}m";months=[f"{dt(start).year}-{m:02d}" for m in range(dt(start).month,13)]
    s=summarize(trades,months);s["signal_count"]=int(np.count_nonzero(sig))
    return dict(key=key,name=key,parameters=dict(strategy=name,signal_timeframe_minutes=tf,initial_stop="2 ATR14",exit="ratcheting opposite 10-bar channel",fixed_tp=None,entry_rule=RULES[name]),summary=s,trades=trades)

def tests():
    # Prefix invariance: future bars never change any entry or indicator.
    rng=np.random.default_rng(17);c=100+np.cumsum(rng.normal(0,.3,600));o=np.r_[c[0],c[:-1]];h=np.maximum(o,c)+.2;l=np.minimum(o,c)-.2
    bars=np.array([o,h,l,c])
    for tf in (5,15):
        a=features(bars,tf);b=features(bars[:,:300],tf);sa=signals(a);sb=signals(b)
        for key in a:assert np.allclose(a[key][:len(b[key])],b[key],equal_nan=True),key
        for key in sa:assert np.array_equal(sa[key][:len(sb[key])],sb[key]),key
    O=np.array([100.,103.,94.]);H=np.array([104.,106.,98.]);L=np.array([99.,102.,92.]);C=np.array([103.,104.,95.])
    assert trade_exit(O,H,L,C,0,1,90,np.array([110.,110.,110.]),np.array([98.,101.,90.]),1)==(2,94.,101.,1)

def run():
    tests();by_year={}
    for year,start,end,reader in ((2024,data24.START,data24.END,data24.candles_2024),(2025,data25.START,data25.END,data25.candles)):
        bars=read_bars(reader,start,end);by_year[year]=[]
        for tf in (5,15):
            f=features(bars,tf);ss=signals(f)
            for name in FAMILIES:
                v=replay(bars,f,ss[name],name,tf,start,end)
                by_year[year].append(v);print("YEAR",year,v["key"],json.dumps(v["summary"],separators=(",",":"),allow_nan=False))
    variants=[]
    for a,b in zip(by_year[2024],by_year[2025]):
        assert a["key"]==b["key"]
        trades=a["trades"]+b["trades"];months=list(a["summary"]["monthly_entry_attribution"])+list(b["summary"]["monthly_entry_attribution"])
        s=summarize(trades,months);s["years"]={"2024":a["summary"],"2025":b["summary"]}
        v=dict(key=a["key"],name=a["name"],parameters=a["parameters"],summary=s,trades=trades)
        variants.append(v);print("RESULT",v["key"],json.dumps(s,separators=(",",":"),allow_nan=False))
    assert len(variants)==12
    OUT.mkdir(parents=True,exist_ok=True)
    with gzip.open(OUT/"all_ledgers.json.gz","wt") as f:json.dump(variants,f,separators=(",",":"),allow_nan=False)
    rows=[]
    for v in variants:
        s=v["summary"];row=dict(key=v["key"],**v["parameters"],**{k:x for k,x in s.items() if not isinstance(x,dict)})
        for y,ys in s["years"].items():row.update({y+"_"+k:x for k,x in ys.items() if not isinstance(x,dict)})
        rows.append(row)
    with (OUT/"all_results.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    (OUT/"provenance.json").write_text(json.dumps(dict(
        families=RULES,timeframes=[5,15],initial_stop="2 ATR14, rounded up to 0.5 point",exit="ratcheting opposite 10-bar channel, 1m touch or worse gap open",
        costs="0.05% taker per side plus 18% GST, zero extra slippage, no offer, funding/liquidation excluded",
        data="Feb 1 2024 12:00 UTC to Jan 1 2025 and calendar 2025, verified continuous data, separate annual resets and forced end close",
        sizing="fixed BTC points and equal initial risk R, no compounding",selection="12 independent predeclared configurations, no 2026",
        entry="completed candle, next minute open; one position, ignore signals while open; all days",
        manifests={"2024":hashlib.sha256((data24.ROOT/"manifest.json").read_bytes()).hexdigest(),"2025":hashlib.sha256((data25.ROOT/"manifest.json").read_bytes()).hexdigest()}),indent=2))
    print("TOTAL",len(variants))
if __name__=="__main__":run()
