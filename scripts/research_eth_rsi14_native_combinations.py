"""Coarse ETH-native RSI grid; fixed entries, no 2026 reads. Research only."""
import csv,gzip,json,math
from itertools import product
from pathlib import Path
import numpy as np
from numba import njit
from research_eth_rsi14_native import segment,entries,summary,MONTHS24,MONTHS25,TICK,FEE,STRESS,dt,checks
OUT=Path("scratch/eth_rsi14_native_combinations")
MODES=("fixed","chandelier","continuation")
SL=(2.,3.,4.)
PROTECT=(.5,.75,1.)
ACT=(2.,3.,4.)
def trails(mode):return (2.,3.,4.) if mode=="chandelier" else (.75,1.,1.5)
PLAN=[(mode,m,p,a,t) for mode in MODES for m,p,a,t in product(SL,PROTECT,ACT,trails(mode))]
REF={"fixed":{2:(64.07586,624.1931625),3:(180.4803685,1333.613094),4:(430.722888,1630.7610765)},"chandelier":{2:(90.633884,786.6834915),3:(184.61258,1315.4820625),4:(153.0320405,1916.8164845)},"continuation":{2:(64.07586,624.1931625),3:(243.0434345,1087.3910795),4:(141.593575,1380.763665)}}
@njit
def sim(O,H,L,C,atr,i,d,risk,style,protect,activation,trail):
    ep=O[i];stop=ep-d*risk;act=ep+d*activation*risk;best=ep;armed=False;mfe=mae=0.
    lock=ep*(d+FEE)/(d-FEE)
    lock=math.ceil(lock/TICK)*TICK if d==1 else math.floor(lock/TICK)*TICK
    for j in range(i,len(O)):
        o,h,l,c=O[j],H[j],L[j],C[j]
        if d*(o-stop)<=0:return j,o,2 if armed else 1,mfe,max(mae,-d*(o-ep))
        if style==2 and armed and j>i and j%15==0 and j>=30:
            adverse=np.min(L[j-30:j-15]) if d==1 else np.max(H[j-30:j-15])
            if d*(C[j-1]-adverse)<0:return j,o,3,mfe,mae
        dist=risk*trail if style!=1 else risk
        if style==1 and np.isfinite(atr[j//15]) and atr[j//15]>0:dist=math.ceil(trail*atr[j//15]/TICK)*TICK
        mfe=max(mfe,d*(o-ep));mae=max(mae,-d*(o-ep))
        if d*(o-best)>0:best=o
        if d*(best-ep)>=protect*risk and d*(best-lock)>=0 and d*(lock-stop)>0:stop=lock
        if d*(best-act)>=0:armed=True
        if armed and d*(best-d*dist-stop)>0:stop=best-d*dist
        if d*(o-stop)<=0:return j,o,2 if armed else 1,mfe,mae
        seq=(o,l,h,c) if c>o or (c==o and o-l<=h-o) else (o,h,l,c)
        for k in range(3):
            a,z=seq[k],seq[k+1]
            if d*(z-a)<0:
                if d*(z-stop)<=0:return j,stop,2 if armed else 1,mfe,max(mae,-d*(stop-ep))
                mae=max(mae,-d*(z-ep))
            elif d*(z-a)>0:
                mfe=max(mfe,d*(z-ep))
                if d*(z-best)>0:best=z
                if d*(best-ep)>=protect*risk and d*(best-lock)>=0 and d*(lock-stop)>0:stop=lock
                if d*(best-act)>=0:armed=True
                if armed and d*(best-d*dist-stop)>0:stop=best-d*dist
    return len(O)-1,C[-1],4,mfe,mae

def replay(bars,start,end,atr,events,mode,m,p,act,t):
    O,H,L,C=bars;free=0;ts=[]
    for first,i,d,trigger,level,depth,a in events:
        if first<free or i<free:continue
        ep=float(O[i]);risk=math.ceil(m*a/TICK)*TICK
        j,xp,reason,mfe,mae=sim(O,H,L,C,atr,i,d,risk,("fixed","chandelier","continuation").index(mode),p,act,t)
        free=j+1;gross=d*(xp-ep);fee=(ep+xp)*FEE
        ts.append(dict(entry_utc=dt(start+i*60).isoformat(),exit_utc=dt(end if reason==4 else start+j*60).isoformat(),side=d,entry_price=ep,exit_price=float(xp),gross=float(gross),fee=float(fee),net=float(gross-fee),risk=float(risk),atr=a,mfe=float(mfe),mae=float(mae),reason=int(reason)))
    return ts


def key(cfg):
    mode,m,p,a,t=cfg
    return f"{mode}|SL={m:g}ATR|BE={p:g}R|ACT={a:g}R|TRAIL={t:g}"+("ATR" if mode=="chandelier" else "R")
def stress_months(ts,months):
    ms=dict.fromkeys(months,0.)
    for t in ts:ms[t["entry_utc"][:7]]+=t["net"]-STRESS*t["entry_price"]
    return sum(v>0 for v in ms.values())
def run():
    checks();OUT.mkdir(parents=True,exist_ok=True);assert len(PLAN)==243
    results={cfg:{2024:[],2025:[]} for cfg in PLAN}
    for year,months,prior in [(2024,["2024-05"],"2024-04"),(2024,["2024-10","2024-11","2024-12"],"2024-09"),(2025,MONTHS25,"2024-12")]:
        bars,start,end,ev=segment(months,prior);atr,events=entries(bars,start,ev)
        print("EVENTS",year,len(events))
        for cfg in PLAN:results[cfg][year].extend(replay(bars,start,end,atr,events,*cfg))
    rows={}
    for cfg,ts in results.items():
        mode,m,p,act,t=cfg
        a=summary(ts[2024],MONTHS24);b=summary(ts[2025],MONTHS25)
        ref=(p==.75 and act==3 and t==(3 if mode=="chandelier" else 1))
        if ref:
            for v,z in zip((a["net"],b["net"]),REF[mode][m]):assert math.isclose(v,z,abs_tol=1e-5),(cfg,v,z)
        blocks=[a["monthly"]["2024-05"],sum(a["monthly"][x] for x in MONTHS24[1:]),sum(b["monthly"][x] for x in MONTHS25[:6]),sum(b["monthly"][x] for x in MONTHS25[6:])]
        row=dict(key=key(cfg),mode=mode,sl=m,protect=p,activation=act,trail=t,reference=ref,net24=a["net"],net25=b["net"],net=a["net"]+b["net"],months24=a["months"],months25=b["months"],months=a["months"]+b["months"],trades24=a["trades"],trades25=b["trades"],pf24=a["pf"],pf25=b["pf"],dd24=a["dd"],dd25=b["dd"],dd=max(a["dd"],b["dd"]),stress24=a["stress"],stress25=b["stress"],stress_months=stress_months(ts[2024],MONTHS24)+stress_months(ts[2025],MONTHS25),positive_blocks=sum(v>0 for v in blocks),blocks=blocks,win24=a["win"],win25=b["win"],median_sl24=a["median_sl"],median_sl25=b["median_sl"])
        row["stress_pass"]=a["stress"]>0 and b["stress"]>0
        row["screen_pass"]=row["stress_pass"] and all(v>0 for v in blocks) and a["trades"]>=10 and b["trades"]>=30
        rows[cfg]=row
    for cfg,row in rows.items():
        mode=cfg[0];axes=(SL,PROTECT,ACT,trails(mode));neighbors=[]
        for i,axis in enumerate(axes,1):
            ix=axis.index(cfg[i])
            for j in (ix-1,ix+1):
                if 0<=j<len(axis):
                    z=list(cfg);z[i]=axis[j];neighbors.append(rows[tuple(z)])
        row["neighbors"]=len(neighbors);row["neighbors_stress_pass"]=sum(z["stress_pass"] for z in neighbors);row["neighbors_screen_pass"]=sum(z["screen_pass"] for z in neighbors)
        row["neighbor_pass_fraction"]=row["neighbors_screen_pass"]/len(neighbors)
        row["robust_screen"]=row["screen_pass"] and row["neighbor_pass_fraction"]>=.75
    def rank(z):return (z["months"],z["stress_months"],z["neighbor_pass_fraction"],min(z["stress24"]/4,z["stress25"]/12),-z["dd"])
    for mode in MODES:
        g=[z for z in rows.values() if z["mode"]==mode];eligible=[z for z in g if z["robust_screen"]]
        print("FAMILY",json.dumps(dict(mode=mode,total=len(g),both_positive=sum(z["net24"]>0 and z["net25"]>0 for z in g),stress_pass=sum(z["stress_pass"] for z in g),screen_pass=sum(z["screen_pass"] for z in g),robust_screen=len(eligible),max_months=max(z["months"] for z in g)),allow_nan=False))
        for z in sorted(eligible or [z for z in g if z["stress_pass"]] or g,key=rank,reverse=True)[:5]:print("TOP",json.dumps(z,allow_nan=False))
        print("PROFIT",json.dumps(max(g,key=lambda z:z["net"]),allow_nan=False))
        print("LOWDD",json.dumps(min([z for z in g if z["screen_pass"]] or g,key=lambda z:z["dd"]),allow_nan=False))
    print("COUNTS",json.dumps(dict(total=len(rows),both_positive=sum(z["net24"]>0 and z["net25"]>0 for z in rows.values()),stress_pass=sum(z["stress_pass"] for z in rows.values()),screen_pass=sum(z["screen_pass"] for z in rows.values()),robust_screen=sum(z["robust_screen"] for z in rows.values()),max_months=max(z["months"] for z in rows.values()),baseline_regression=9)))
    with (OUT/"results.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(next(iter(rows.values()))));w.writeheader();w.writerows(rows.values())
    with gzip.open(OUT/"all_results.json.gz","wt") as f:json.dump({key(cfg):dict(row=rows[cfg],trades=ts,monthly={y:summary(ts[y],MONTHS24 if y==2024 else MONTHS25)["monthly"] for y in (2024,2025)}) for cfg,ts in results.items()},f,allow_nan=False)
if __name__=="__main__":run()
