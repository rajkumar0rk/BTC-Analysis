"""Predeclared VWAP ablations: one change at a time, no 2026 data."""
import csv,gzip,json,math
from pathlib import Path
import numpy as np
from numba import njit
from research_rsi14_depth_stability import y24,y25,q,candles25,checks,summarize,FEE,dt
from research_five_independent_strategies import bracket,unit_checks,signal_lists,replay as reference_replay
OUT=Path("scratch/vwap_independent")
# Name, timeframe, deviation ATR, reward mode, ADX filter, reward-to-cost filter.
PLAN=[
("baseline",15,1,2,False,False),
("deeper-deviation",15,2,2,False,False),
("30m",30,1,2,False,False),
("60m",60,1,2,False,False),
("reward-3r",15,1,3,False,False),
("vwap-target",15,1,0,False,False),
("adx-below25",15,1,2,True,False),
("reward-fee-3x",15,1,2,False,True),
]
REF={2024:-12112.14839,2025:-75141.34952}

@njit
def execute(O,H,L,C,i,d,risk,tp):
    ep=O[i];sl=ep-d*risk;mfe=mae=0.
    for j in range(i,len(O)):
        o,h,l,c=O[j],H[j],L[j],C[j]
        if d*(o-sl)<=0:return j,o,1,mfe,max(mae,-d*(o-ep))
        if d*(o-tp)>=0:return j,tp,2,max(mfe,d*(tp-ep)),mae
        mfe=max(mfe,d*(o-ep));mae=max(mae,-d*(o-ep))
        seq=(o,l,h,c) if c>o or (c==o and o-l<=h-o) else (o,h,l,c)
        for k in range(3):
            a,z=seq[k],seq[k+1]
            if d*(z-a)<0:
                if d*(z-sl)<=0:return j,sl,1,mfe,max(mae,risk)
                mae=max(mae,-d*(z-ep))
            elif d*(z-a)>0:
                if d*(z-tp)>=0:return j,tp,2,max(mfe,d*(tp-ep)),mae
                mfe=max(mfe,d*(z-ep))
    return len(O)-1,C[-1],3,mfe,mae

def daily_vwap(bars,volume,start):
    O,H,L,C=bars;out=np.full(len(O),np.nan);vsum=psum=0.;day=-1
    for j in range(len(O)):
        newday=(start+j*60)//86400
        if newday!=day:day=newday;vsum=psum=0.
        v=volume[j];vsum+=v;psum+=v*(H[j]+L[j]+C[j])/3.
        if vsum>0:out[j]=psum/vsum
    return out

def tf_arrays(bars,ind,vw,tf):
    O,H,L,C=bars;n=len(O)//tf*tf
    h=H[:n].reshape(-1,tf).max(axis=1);l=L[:n].reshape(-1,tf).min(axis=1);c=C[tf-1:n:tf];vwap=vw[tf-1:n:tf]
    if tf==15:
        atr=ind[-1][1:len(c)+1];adx=ind[3][1:len(c)+1]
    else:
        prev=np.r_[np.nan,c[:-1]]
        tr=np.maximum(h-l,np.maximum(np.abs(h-prev),np.abs(l-prev)));tr[0]=h[0]-l[0]
        atr=q.wilder(tr);adx=q.adx(h,l,c)
    return c,vwap,atr,adx

def candidates(bars,arrays,tf,dev,start,ev,adx_filter):
    c,vwap,atr,adx=arrays;out=[]
    for k in range(41,len(c)):
        i=(k+1)*tf
        if i>=len(bars[0]) or start+i*60<ev:continue
        a=atr[k];p=atr[k-1]
        if not (np.isfinite(a) and a>0 and np.isfinite(p) and p>0 and np.isfinite(vwap[k]) and np.isfinite(vwap[k-1])):continue
        if (start+i*60-1)//86400!=(start+(i-tf)*60-1)//86400:continue
        if adx_filter and not adx[k]<25:continue
        zprev=(c[k-1]-vwap[k-1])/p;z=(c[k]-vwap[k])/a
        d=1 if zprev<-dev and -dev<=z<0 else -1 if zprev>dev and 0<z<=dev else 0
        if d:out.append((i,d,float(a),float(vwap[k])))
    return out

def replay(bars,signals,start,end,reward,fee_filter):
    O,H,L,C=bars;free=0;ts=[]
    for i,d,a,vwap in signals:
        if i<free:continue
        ep=float(O[i]);risk=max(.5,math.ceil(2*a*2)/2)
        # Conservative taker fees in every variant; static signal-time VWAP target.
        if fee_filter and d*(vwap-ep)<3*(ep+vwap)*FEE:continue
        tp=ep+d*reward*risk if reward else (math.floor(vwap*2)/2 if d==1 else math.ceil(vwap*2)/2)
        if d*(tp-ep)<=0:continue
        j,xp,reason,mfe,mae=execute(O,H,L,C,i,d,risk,tp)
        free=j+1;gross=d*(xp-ep);fee=(ep+xp)*FEE
        ts.append(dict(entry_utc=dt(start+i*60).isoformat(),exit_utc=dt(end if reason==3 else start+j*60).isoformat(),side=d,entry_price=ep,exit_price=float(xp),gross_points=float(gross),fee_points=float(fee),net_points=float(gross-fee),exit_reason={1:"Initial SL",2:"Target",3:"Evaluation end"}[reason],signal_context=dict(risk_points=float(risk),entry_atr=float(a),mfe=float(mfe),mae=float(mae),vwap=vwap,target=float(tp))))
    return ts

def run():
    checks();unit_checks();OUT.mkdir(parents=True,exist_ok=True)
    o=np.array([100.]);h=np.array([130.]);l=np.array([85.])
    assert execute(o,h,l,np.array([110.]),0,1,10.,120.)[:3]==(0,90.,1)
    assert execute(o,h,l,np.array([95.]),0,1,10.,120.)[:3]==(0,120.,2)
    results={p[0]:dict(plan=p,years={}) for p in PLAN}
    for year in (2024,2025):
        if year==2024:
            q.candles=y24.candles;bars,signals,snapshots,extra,rec=y24.load();start,end,ev=y24.START,y24.END,y24.EVAL
        else:
            q.candles=candles25;bars,signals,snapshots,extra,rec=y25.load();start,end,ev=y25.START,y25.END,y25.START
        ind=q.indicators(bars,snapshots);vw=daily_vwap(bars,ind[0],start)
        arrays={tf:tf_arrays(bars,ind,vw,tf) for tf in (15,30,60)}
        for name,tf,dev,reward,adx_filter,fee_filter in PLAN:
            sig=candidates(bars,arrays[tf],tf,dev,start,ev,adx_filter)
            ts=replay(bars,sig,start,end,reward,fee_filter);s=summarize(ts,year);st=summarize(ts,year,50)
            if name=="baseline":
                old=signal_lists(bars,ind,snapshots,extra,start,ev)["vwap-mean-reversion"]
                assert [(i,d,a) for i,d,a,_ in sig]==old
                assert math.isclose(s["net"],REF[year],abs_tol=1e-5),(year,s["net"])
                assert len(ts)==(649 if year==2024 else 792)
            s["signals"]=len(sig);s["stress"]=dict(net=st["net"],months=st["profitable_months"],pf=st["profit_factor"],dd=st["realized_drawdown_points"])
            s["median_risk"]=float(np.median([t["signal_context"]["risk_points"] for t in ts])) if ts else None
            results[name]["years"][year]=dict(summary=s,trades=ts)
        del bars,ind,snapshots,extra,rec
    rows=[]
    for name,v in results.items():
        a,b=[v["years"][y]["summary"] for y in (2024,2025)]
        blocks=[sum(p for m,p in s["monthly_entry_attribution"].items() if (int(m[-2:])>6)==bool(h)) for s in (a,b) for h in (0,1)]
        row=dict(key=name,net24=a["net"],net25=b["net"],net=a["net"]+b["net"],months24=a["profitable_months"],months25=b["profitable_months"],months=a["profitable_months"]+b["profitable_months"],dd24=a["realized_drawdown_points"],dd25=b["realized_drawdown_points"],dd=max(a["realized_drawdown_points"],b["realized_drawdown_points"]),trades24=a["trades"],trades25=b["trades"],pf24=a["profit_factor"],pf25=b["profit_factor"],win24=a["win_rate"],win25=b["win_rate"],stress24=a["stress"]["net"],stress25=b["stress"]["net"],stress_months=a["stress"]["months"]+b["stress"]["months"],positive_blocks=sum(p>0 for p in blocks),blocks=blocks,gross24=a["gross"],gross25=b["gross"],fees24=a["fees"],fees25=b["fees"],median_risk24=a["median_risk"],median_risk25=b["median_risk"],accepted=all(x["stress"]["net"]>0 and x["trades"]>=30 for x in (a,b)) and all(p>0 for p in blocks))
        rows.append(row);print("RESULT",json.dumps(row,allow_nan=False))
        print("DETAIL",json.dumps(dict(key=name,years={y:v["years"][y]["summary"] for y in (2024,2025)}),allow_nan=False))
    with (OUT/"results.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    with gzip.open(OUT/"all_results.json.gz","wt") as f:json.dump(results,f,allow_nan=False,separators=(",",":"))
    print("COUNTS",json.dumps(dict(total=len(rows),both_year_positive=sum(x["net24"]>0 and x["net25"]>0 for x in rows),accepted=sum(x["accepted"] for x in rows),max_months=max(x["months"] for x in rows))))
if __name__=="__main__":run()
