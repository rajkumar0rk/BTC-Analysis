"""Predeclared 120 reversal combinations; 2025 in-sample only."""
import hashlib,json,math,gzip,csv
from pathlib import Path
from datetime import datetime
from decimal import Decimal as D
import numpy as np
from numba import njit
from research_rsi14_reversal_confirmation_2025 import entries_for,MODES
from research_rsi14_runner_refinements_2025 import ROOT,START,END,checks,load,dt,export_bundle
from research_rsi14_improvements_2025 import FEE,INSTRUMENT,HOUR,Candle,IndicatorBook,spec
OUT=Path("scratch/rsi14_reversal_targets")
FIXED=((250,500),(250,750),(500,500),(500,1000),(500,1500),(750,1500),(1000,1000),(1000,2000))
STOPS=(("fixed",250),("fixed",500),("fixed",750),("fixed",1000),("atr",1),("atr",2))

@njit
def execute(O,H,L,C,i,d,sl,target,mode,mid,EMA):
    ep=O[i];stop=ep-d*sl
    for j in range(i,len(O)):
        o,h,l,c=O[j],H[j],L[j],C[j]
        t=target if mode==0 else EMA[j//15]
        if d*(o-stop)<=0:return j,o,1
        if mode==1 and j==mid:return j,o,3
        if mode!=1 and np.isfinite(t) and d*(o-t)>=0:return j,o if mode==2 else t,2
        if c>o or (c==o and o-l<=h-o):seq=(o,l,h,c)
        else:seq=(o,h,l,c)
        for k in range(3):
            a,b=seq[k],seq[k+1]
            if d*(b-a)<0 and d*(a-stop)>=0 and d*(b-stop)<=0:return j,stop,1
            if mode!=1 and np.isfinite(t) and d*(b-a)>0 and d*(a-t)<=0 and d*(b-t)>=0:return j,t,2
    return len(O)-1,C[-1],4

def hourly(bars):
    O,H,L,C=bars
    book=IndicatorBook((spec("rsi",HOUR,period=14),),history_limit=2)
    result=np.full(len(O)//60+1,np.nan)
    for k in range(60,len(O)+1,60):
        a=k-60
        candle=Candle(INSTRUMENT,HOUR,dt(START+a*60),dt(START+k*60),
            D(str(O[a])),D(str(max(H[a:k]))),D(str(min(L[a:k]))),D(str(C[k-1])),D(0))
        book.update(candle)
        r=book.get("rsi",HOUR,{"period":14})[-1]
        if r is not None:result[k//60]=float(r)
    return result

def divergence_entries(bars,signals,snapshots,extra,rsi):
    # Strict local price pivots with two closed bars on each side.
    # Confirmation is available only at the close of the second right bar.
    keys=sorted(extra)
    pivots={1:[],-1:[]}
    for z in range(2,len(keys)-2):
        k=keys[z];r=rsi.get(k)
        if r is None:continue
        for d,col in ((1,4),(-1,3)):
            p=extra[k][col]
            if all(d*p<d*extra[keys[j]][col] for j in (z-2,z-1,z+1,z+2)):
                pivots[d].append((keys[z+2],k,p,r))
    out=[]
    for q,(i,d,r,hi,lo) in enumerate(signals):
        until=signals[q+1][0] if q+1<len(signals) else len(bars[0])
        ps=pivots[d]
        for a,b in zip(ps,ps[1:]):
            j,k,p,rr=b
            if j<=i or k<i:continue
            if j>=until:break
            if d*(p-a[2])<0 and d*(rr-a[3])>0:
                atr,ema,_,_=snapshots[j]
                _,_,_,ph,pl,_=extra[j]
                out.append((j,d,r,i,atr,ema,pl-.5 if d==1 else ph+.5,hi if d==1 else lo,j))
                break
    return out

def tests():
    a=np.array([10000.]);ema=np.array([10100.])
    assert execute(a,np.array([10600.]),np.array([9700.]),np.array([10100.]),0,1,250,10500,0,-1,ema)[2]==1
    assert execute(a,np.array([10600.]),np.array([9700.]),np.array([9900.]),0,1,250,10500,0,-1,ema)[2]==2
    assert execute(a,a,a,a,0,1,250,10500,1,0,ema)[2]==3

def run():
    checks();tests()
    bars,momentum,snapshots,extra,rec=load()
    O,H,L,C=bars
    signals=[(i,-d,r,hi,lo) for i,d,r,hi,lo in momentum]
    rsi_id=next(m["id"] for d,m in zip(rec.specs,rec.definitions) if d.base=="rsi" and m["timeframe_minutes"]==15)
    rsi={(t-START)//60:r for t,r in rec.series[rsi_id]}
    ema=np.full(len(O)//15+1,np.nan)
    for k,v in extra.items():
        if v[0] is not None:ema[k//15]=v[0]
    hr=hourly(bars)
    mid={d:np.array([k for k,r in sorted(rsi.items()) if r is not None and d*(r-50)>=0],dtype=np.int64) for d in (1,-1)}
    entries={m:entries_for(bars,signals,snapshots,extra,rsi,m) for m in MODES}
    entries["rsi-divergence"]=divergence_entries(bars,signals,snapshots,extra,rsi)
    entries["recovery-h1-rsi"]= [e for e in entries["rsi-recovery"] if (hr[e[0]//60]<30 if e[1]==1 else hr[e[0]//60]>70)]
    # H1 indicator history uses exactly the same completed-bar values as filter.
    defs=list(rec.definitions)+[dict(id="h1_rsi14",name="rsi.value",timeframe_minutes=60,panel="panel",parameters={"period":14})]
    series=dict(rec.series,h1_rsi14=[[START+k*3600,None if np.isnan(hr[k]) else float(hr[k])] for k in range(1,len(hr))])
    plans=[("fixed","fixed",sl,tp) for sl,tp in FIXED]+[(x,kind,sl,0) for x in ("rsi50","ema20") for kind,sl in STOPS]
    variants=[]
    for entry,es in entries.items():
        for mode,kind,sl,tp in plans:
            trades=[];free=0
            for i,d,r,trigger,atr,em,struct,level,confirm in es:
                if trigger<free or i<free:continue
                ep=float(O[i])
                if kind=="atr" and (atr is None or atr<=0):continue
                sd=float(sl if kind=="fixed" else max(.5,math.ceil(sl*atr*2)/2))
                target=ep+d*tp
                if mode=="ema20" and (not np.isfinite(ema[i//15]) or d*(ema[i//15]-ep)<=0):continue
                hit=-1
                if mode=="rsi50":
                    ix=np.searchsorted(mid[d],i,side="left")
                    if ix<len(mid[d]):hit=int(mid[d][ix])
                    if hit==i:continue
                j,xp,reason=execute(O,H,L,C,i,d,sd,target,("fixed","rsi50","ema20").index(mode),hit,ema)
                free=j+1;gross=d*(xp-ep);fee=(ep+xp)*FEE
                vals={"indicator_0":r}
                if atr is not None:vals["indicator_1"]=atr
                if em is not None:vals["indicator_2"]=em
                if np.isfinite(ema[i//15]):vals["indicator_3"]=float(ema[i//15])
                if np.isfinite(hr[i//60]):vals["h1_rsi14"]=float(hr[i//60])
                trades.append(dict(entry_utc=dt(START+i*60).isoformat(),trigger_utc=dt(START+trigger*60).isoformat(),exit_utc=dt(END if reason==4 else START+j*60).isoformat(),side=d,entry_price=ep,exit_price=float(xp),stop_price=ep-d*sd,target_price=target if mode=="fixed" else float(ema[i//15]) if mode=="ema20" else None,gross_points=gross,fee_points=fee,net_points=gross-fee,assumed_slippage_points=0,entry_reason=entry,exit_reason={1:"Initial stop",2:"Target reached",3:"Completed RSI50",4:"End of 2025 evaluation"}[reason],signal_context=dict(rsi14=r,confirmation_utc=dt(START+confirm*60).isoformat()),indicator_values=vals))
            p=[t["net_points"] for t in trades];gain=math.fsum(max(0,x) for x in p);loss=-math.fsum(min(0,x) for x in p)
            months={f"2025-{m:02d}":0. for m in range(1,13)};eq=peak=dd=0.
            for t,x in zip(trades,p):
                months[t["entry_utc"][:7]]+=x;eq+=x;peak=max(peak,eq);dd=max(dd,peak-eq)
            wins=sum(x>0 for x in p)
            summary=dict(accounting="realized",open_position=None,trades=len(p),net=math.fsum(p),wins=wins,win_rate=100*wins/len(p) if p else 0,profit_factor=gain/loss if loss else None,realized_drawdown_points=dd,monthly_entry_attribution=months,profitable_months=sum(x>0 for x in months.values()))
            key=f"{entry}-{mode}-{kind}-sl{sl}-tp{tp}"
            params=dict(entry=entry,exit=mode,stop_kind=kind,stop_loss=sl,take_profit=tp if mode=="fixed" else None,long_threshold=20,short_threshold=80,rsi_period=14,signals_while_open="ignored",trading_days="all")
            variants.append(dict(key=key,name="RSI14 reversal | "+key,parameters=params,summary=summary,trades=trades))
            print("RESULT",key,json.dumps(summary,separators=(",",":"),allow_nan=False))
    assert len(variants)==120
    OUT.mkdir(parents=True,exist_ok=True)
    with gzip.open(OUT/"all_ledgers.json.gz","wt") as f:json.dump(variants,f,allow_nan=False,separators=(",",":"))
    rows=[dict(key=v["key"],**v["parameters"],**{k:x for k,x in v["summary"].items() if k!="monthly_entry_attribution"},**v["summary"]["monthly_entry_attribution"]) for v in variants]
    with (OUT/"all_results.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    # Full results archived; publish best by net and months for each entry to bound dashboard growth.
    selected={}
    for entry in entries:
        vs=[v for v in variants if v["parameters"]["entry"]==entry]
        for v in sorted(vs,key=lambda v:v["summary"]["net"],reverse=True)[:2]+sorted(vs,key=lambda v:(v["summary"]["profitable_months"],v["summary"]["net"]),reverse=True)[:2]:
            selected[v["key"]]=v
    export_bundle(OUT/"backtest.json",family="rsi14-reversal-targets-2025",symbol="BTCUSD",unit="price points",start_utc=dt(START).isoformat(),end_utc=dt(END).isoformat(),execution_timeframe_minutes=1,signal_timeframe_minutes=15,costs="0.05% taker each side +18% GST; no Scalper Offer; zero extra slippage; funding and liquidation excluded; Color execution.",variants=list(selected.values()),indicator_definitions=defs,indicator_series=series,data_provenance=dict(manifest=str(ROOT/"manifest.json"),manifest_sha256=hashlib.sha256((ROOT/"manifest.json").read_bytes()).hexdigest(),input_minutes=len(O),selection="120 predefined combinations, in-sample; full ledgers archived; selected net and month leaders per entry for dashboard only",ema_target="latest completed 15m EMA20, fixed within each 1m candle; no entry if already reached",rsi_target="first completed RSI at or beyond 50, next 1m open",divergence="two strict 2-left/2-right price pivots, RSI at pivot, second pivot at or after signal, enter after right-bar confirmation",h1_filter="last completed H1 RSI14 at recovery entry, long <30 short >70",month_attribution="UTC entry month; trade-close drawdown"))
    print("TOTAL",len(variants),"PROFITABLE",sum(v["summary"]["net"]>0 for v in variants),"PUBLISHED",len(selected))
if __name__=="__main__":run()
