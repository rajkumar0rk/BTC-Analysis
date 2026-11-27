"""2025 in-sample factorial study; no live execution, no 2026 data."""
import csv, gzip, hashlib, json, math
from itertools import product
from pathlib import Path
import numpy as np
from numba import njit
from research_rsi14_80_20_2025 import (
    ROOT, START, END, FEE, TF, INSTRUMENT, dt, signal, candles,
    Candle, IndicatorBook, spec, IndicatorRecorder, export_bundle, Timeframe,
)
HOUR = Timeframe(3600)
ENTRIES = ("direct","pullback","breakout","pullback-breakout")
BRACKETS = [("fixed",s,t) for s,t in product((750,1000,1500,2000),(1000,2000,3000,4000))]
BRACKETS += [("atr",s,t) for s,t in product((1,2,3),(2,3,4))]
PROTECTIONS = (0,500,750,1000)
OUT = Path("scratch/rsi14_improvements")

@njit
def execute(O,H,L,C,i,d,sd,td,activation,mid):
    ep=O[i];stop=ep-d*sd;target=ep+d*td;armed=False
    # Solve gross profit = both taker fees plus GST, then round
    # in the favorable direction to the modeled half-dollar tick.
    lock=(ep*(d+FEE))/(d-FEE)
    lock=math.ceil(lock*2)/2 if d==1 else math.floor(lock*2)/2
    for j in range(i,len(O)):
        o,h,l,c=O[j],H[j],L[j],C[j]
        if d*(o-stop)<=0:
            return j,o,4 if armed else 2,stop
        if d*(o-target)>=0:
            return j,target,1,stop
        if j==mid:
            return j,o,3,stop
        if activation>0 and not armed and d*(o-ep)>=activation:
            stop=lock;armed=True
        # Color path. Skip segments if neither exit nor activation can occur.
        adverse=l if d==1 else h
        favorable=h if d==1 else l
        if d*(adverse-stop)>0 and d*(favorable-target)<0 and (activation==0 or armed or d*(favorable-ep)<activation):
            continue
        if c>o or (c==o and o-l<=h-o):
            seq=(o,l,h,c)
        else:
            seq=(o,h,l,c)
        for k in range(3):
            a,b=seq[k],seq[k+1]
            if d*(b-a)<0:
                if d*(b-stop)<=0 and d*(a-stop)>=0:
                    return j,stop,4 if armed else 2,stop
            elif d*(b-a)>0:
                if d*(b-target)>=0 and d*(a-target)<=0:
                    return j,target,1,stop
                if activation>0 and not armed and d*(b-ep)>=activation:
                    stop=lock;armed=True
    return len(O)-1,C[-1],5,stop

def verify():
    a=np.array([10000.]);h=np.array([10250.]);l=np.array([9750.])
    assert execute(a,h,l,np.array([10010.]),0,1,100,200,0,-1)[2]==2
    assert execute(a,h,l,np.array([9990.]),0,1,100,200,0,-1)[2]==1
    assert execute(a,h,l,np.array([10010.]),0,-1,100,200,0,-1)[2]==1
    assert execute(a,h,l,np.array([9990.]),0,-1,100,200,0,-1)[2]==2
    # High first arms the fee stop, then price retraces to it.
    r=execute(a,np.array([10800.]),np.array([9800.]),np.array([9990.]),0,1,1000,2000,500,-1)
    assert r[2]==4 and r[1]>=10000 and (r[1]-10000)-(r[1]+10000)*FEE>=0
    r=execute(a,np.array([10200.]),np.array([9200.]),np.array([10010.]),0,-1,1000,2000,500,-1)
    assert r[2]==4 and r[1]<=10000 and (10000-r[1])-(r[1]+10000)*FEE>=0
    assert execute(a,np.array([10001.]),np.array([9999.]),a,0,1,1000,2000,0,0)[2]==3

def load():
    book=IndicatorBook((spec("rsi",TF,period=14),spec("atr",TF,period=14),spec("ema",HOUR,period=50)),history_limit=2)
    rec=IndicatorRecorder(book)
    n=(END-START)//60
    bars=np.empty((4,n),dtype=np.float64)
    signals=[]; mid={1:[],-1:[]}; snapshots={}; group=[];hour=[];prev=None
    ema=None
    for i,(t,o,h,l,c,v) in enumerate(candles()):
        bars[:,i]=[float(o),float(h),float(l),float(c)]
        group.append((o,h,l,c,v));hour.append((o,h,l,c,v))
        end=t+60
        if len(hour)==60:
            ca=Candle(INSTRUMENT,HOUR,dt(end-3600),dt(end),hour[0][0],max(x[1] for x in hour),min(x[2] for x in hour),hour[-1][3],sum(x[4] for x in hour))
            book.update(ca);rec.completed(ca);hour.clear()
            val=book.get("ema",HOUR,{"period":50})[-1]
            ema=float(val) if val is not None else None
        if len(group)==15:
            ca=Candle(INSTRUMENT,TF,dt(end-900),dt(end),group[0][0],max(x[1] for x in group),min(x[2] for x in group),group[-1][3],sum(x[4] for x in group))
            book.update(ca);rec.completed(ca);group.clear()
            r=book.get("rsi",TF,{"period":14})[-1];at=book.get("atr",TF,{"period":14})[-1]
            k=i+1
            snapshots[k]=(float(at) if at is not None else None,ema,float(ca.open),float(ca.close))
            d=signal(prev,r)
            if d and k<n:signals.append((k,d,float(r),float(ca.high),float(ca.low)))
            if prev is not None and r is not None and k<n:
                if prev>=50>r:mid[1].append(k)
                if prev<=50<r:mid[-1].append(k)
            prev=r
    assert i+1==n and not group and not hour
    return bars,signals,mid,snapshots,rec

def candidates(bars,signals,snapshots,mode,trend):
    O,H,L,C=bars
    out=[]
    for q,(i,d,r,hi,lo) in enumerate(signals):
        # The next RSI threshold crossing replaces any outstanding setup.
        until=signals[q+1][0] if q+1<len(signals) else len(O)
        j=i
        if "pullback" in mode:
            j=-1
            for k in range(i+15,until,15):
                _,_,o,c=snapshots[k]
                if d*(c-o)<0:
                    j=k;break
            if j<0:continue
        if "breakout" in mode:
            # Confirm on a completed minute close beyond signal-bar high/low.
            # Entry is the following minute's open, not a retrospective fill.
            level=hi if d==1 else lo
            hits=np.flatnonzero(d*(C[j:until-1]-level)>0)
            if not len(hits):continue
            j+=int(hits[0])+1
        if j>=until or j>=len(O):continue
        at,ema,_,_=snapshots[(j//15)*15]
        if trend and (ema is None or d*(C[j-1]-ema)<=0):continue
        out.append((j,d,r,i,at,ema))
    return out

REASONS={1:"Take profit",2:"Stop loss",3:"RSI midpoint exit",4:"Fee protection stop",5:"End of 2025 evaluation"}

def replay(bars,entries,mid,mode,trend,kind,sl,tp,protection,rsi_exit):
    O,H,L,C=bars
    trades=[];next_free=0
    for i,d,r,trigger,atr,ema in entries:
        if i<next_free or (kind=="atr" and (atr is None or atr<=0)):continue
        ep=float(O[i])
        sd=float(sl if kind=="fixed" else max(.5,math.ceil(sl*atr*2)/2))
        td=float(tp if kind=="fixed" else max(.5,math.ceil(tp*atr*2)/2))
        m=-1
        if rsi_exit:
            ix=np.searchsorted(mid[d],i,side="right")
            if ix<len(mid[d]):m=int(mid[d][ix])
        j,xp,reason,final_stop=execute(O,H,L,C,i,d,sd,td,protection,m)
        next_free=j+1;gross=d*(xp-ep);fee=(ep+xp)*FEE
        et=START+i*60;xt=END if reason==5 else START+j*60
        values={"indicator_0":r}
        if atr is not None:values["indicator_1"]=atr
        if ema is not None:values["indicator_2"]=ema
        trades.append(dict(entry_utc=dt(et).isoformat(),trigger_utc=dt(START+trigger*60).isoformat(),
            exit_utc=dt(xt).isoformat(),side=d,entry_price=ep,exit_price=xp,
            stop_price=ep-d*sd,target_price=ep+d*td,final_stop_price=final_stop,
            gross_points=gross,fee_points=fee,net_points=gross-fee,assumed_slippage_points=0,
            entry_reason=mode,exit_reason=REASONS[reason],
            signal_context={"rsi14":r,"entry_atr14":atr,"entry_h1_ema50":ema,"protection_activation_points":protection},
            indicator_values=values))
    net=math.fsum(t["net_points"] for t in trades)
    wins=sum(t["net_points"]>1e-8 for t in trades)
    # Values recorded at fee breakeven are rounded toward profit; use
    # publisher's exact positive-net definition for reported win count.
    wins=sum(t["net_points"]>0 for t in trades)
    gain=math.fsum(max(0,t["net_points"]) for t in trades);loss=-math.fsum(min(0,t["net_points"]) for t in trades)
    eq=peak=dd=0.;monthly={f"2025-{m:02d}":0. for m in range(1,13)}
    for t in trades:
        eq+=t["net_points"];peak=max(peak,eq);dd=max(dd,peak-eq);monthly[t["entry_utc"][:7]]+=t["net_points"]
    p=dict(entry=mode,trend_h1_ema50=trend,bracket=kind,stop_loss=sl,take_profit=tp,
        profit_protection_points=protection,rsi_midpoint_exit=rsi_exit,rsi_period=14,long_threshold=80,short_threshold=20,
        trading_days="all",opposite_signals_while_open="ignored")
    s=dict(accounting="realized",open_position=None,trades=len(trades),net=net,wins=wins,
        win_rate=100*wins/len(trades) if trades else 0,profit_factor=gain/loss if loss else None,
        realized_drawdown_points=dd,profitable_months=sum(v>0 for v in monthly.values()),monthly_entry_attribution=monthly,
        protection_exits=sum(t["exit_reason"]=="Fee protection stop" for t in trades))
    key=f"{mode}-ema{int(trend)}-{kind}-{sl}-{tp}-be{protection}-mid{int(rsi_exit)}"
    name=f"RSI14 80/20 | {mode} | EMA {int(trend)} | {kind} SL {sl} TP {tp} | BE {protection} | RSI50 {int(rsi_exit)}"
    return dict(key=key,name=name,parameters=p,summary=s,trades=trades)

def run():
    verify()
    bars,signals,mid,snapshots,rec=load()
    mid={k:np.array(v,dtype=np.int64) for k,v in mid.items()}
    OUT.mkdir(parents=True,exist_ok=True)
    variants=[]
    for mode,trend in product(ENTRIES,(False,True)):
        entries=candidates(bars,signals,snapshots,mode,trend)
        for (kind,sl,tp),protection,rsi_exit in product(BRACKETS,PROTECTIONS,(False,True)):
            variants.append(replay(bars,entries,mid,mode,trend,kind,sl,tp,protection,rsi_exit))
    assert len(variants)==1600
    bynet=sorted(variants,key=lambda v:v["summary"]["net"],reverse=True)
    bymonth=sorted(variants,key=lambda v:(v["summary"]["profitable_months"],v["summary"]["net"]),reverse=True)
    profitable=[v for v in variants if v["summary"]["net"]>0]
    lowdd=sorted(profitable,key=lambda v:v["summary"]["realized_drawdown_points"])
    chosen={}
    # Keep Explorer bounded; all 1,600 summaries and ledgers are archived separately.
    for v in bynet[:5]+bymonth[:5]+lowdd[:3]:
        chosen[v["key"]]=v
    for mode in ENTRIES:
        group=[v for v in bynet if v["parameters"]["entry"]==mode]
        chosen[group[0]["key"]]=group[0]
    for key in ("direct-ema0-fixed-1000-1000-be0-mid0","direct-ema0-fixed-1000-2000-be0-mid0"):
        v=next(v for v in variants if v["key"]==key);chosen[key]=v
    with gzip.open(OUT/"all_variants.json.gz","wt") as f:
        json.dump(variants,f,separators=(",",":"),allow_nan=False)
    with (OUT/"all_results.csv").open("w",newline="") as f:
        rows=[]
        for v in bynet:
            s=dict(v["summary"]);months=s.pop("monthly_entry_attribution")
            rows.append(dict(key=v["key"],**v["parameters"],**s,**months))
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    export_bundle(OUT/"backtest.json",family="rsi14-improvement-grid-2025",symbol="BTCUSD",unit="price points",
        start_utc=dt(START).isoformat(),end_utc=dt(END).isoformat(),execution_timeframe_minutes=1,
        signal_timeframe_minutes=15,costs="0.05% taker each side + 18% GST; no Scalper Offer; zero slippage; funding and liquidation not modeled. Color OHLC execution; limit target gap at target, stop gap at open. Fee protection includes both entry and exit fees, tick rounded.",
        variants=list(chosen.values()),recorder=rec,
        data_provenance=dict(manifest=str(ROOT/"manifest.json"),manifest_sha256=hashlib.sha256((ROOT/"manifest.json").read_bytes()).hexdigest(),input_minutes=len(bars[0]),timestamp_label="assumed open UTC",
            total_grid_variants=len(variants),published_variants=len(chosen),full_archive="rsi14-improvement-grid-full",
            setup_expiry="next RSI threshold crossing",midpoint_exit="cross against position through 50 at completed 15m close, next 1m open",
            atr="Wilder ATR14, last completed 15m",protection="intraminute favorable excursion triggers fee-adjusted breakeven",
            execution_path="Color: bullish OLHC, bearish OHLC, doji nearest extreme first, tie OLHC"))
    print("TOTAL",len(variants),"PROFITABLE",len(profitable),"SIGNALS",len(signals),"PUBLISHED",len(chosen))
    for label,group in (("NET",bynet[:10]),("MONTH",bymonth[:10]),("DD",lowdd[:5]),("PUBLISH",list(chosen.values()))):
        for v in group:print(label,json.dumps(dict(key=v["key"],**v["parameters"],**v["summary"]),separators=(",",":"),allow_nan=False))

if __name__=="__main__":run()
