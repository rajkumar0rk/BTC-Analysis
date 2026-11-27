"""Independent RSI reversal: six predeclared entry ideas x twelve exits."""
import csv,gzip,hashlib,json,math
from pathlib import Path
from decimal import Decimal as D
import numpy as np
from research_rsi14_80_20_2025 import (
    ROOT,START,END,FEE,TF,INSTRUMENT,dt,candles,Candle,IndicatorBook,spec,
    IndicatorRecorder,export_bundle,Timeframe,
)
from research_rsi14_reversal_targets_2025 import execute,tests

OUT=Path("scratch/rsi14_reversal_regimes")
H4=Timeframe(14400)
MODES=("trend-recovery","bollinger-reclaim","liquidity-sweep","volume-exhaustion","double-test","adx-range-recovery")
PLANS=tuple((kind,0,r) for kind in ("signal","swing") for r in (1,2,3))+tuple(("atr",s,t) for s in (1.5,2) for t in (2,3,4))
TICK=.5

def load_data():
    book=IndicatorBook((spec("rsi",TF,period=14),spec("atr",TF,period=14),
        spec("ema",H4,period=50),spec("bollinger.upper",TF,period=20,multiplier=2),
        spec("bollinger.lower",TF,period=20,multiplier=2),spec("adx",TF,period=14)),history_limit=2)
    rec=IndicatorRecorder(book)
    bars=np.empty((4,(END-START)//60),dtype=np.float64)
    group=[];h4=[];rows=[];signals=[];prev=None;ema=None;h4close=None
    def val(name,tf,params):
        v=book.get(name,tf,params)[-1]
        return None if v is None else float(v)
    def candle(g,tf,end):
        return Candle(INSTRUMENT,tf,dt(end-tf.seconds),dt(end),g[0][0],
            max(x[1] for x in g),min(x[2] for x in g),g[-1][3],sum(x[4] for x in g))
    for i,(t,o,h,l,c,v) in enumerate(candles()):
        bars[:,i]=float(o),float(h),float(l),float(c)
        group.append((o,h,l,c,v));h4.append((o,h,l,c,v))
        end=t+60
        if len(h4)==240:
            ca=candle(h4,H4,end);book.update(ca);rec.completed(ca);h4.clear()
            ema=val("ema",H4,{"period":50});h4close=float(ca.close)
        if len(group)==15:
            ca=candle(group,TF,end);book.update(ca);rec.completed(ca);group.clear()
            r=val("rsi",TF,{"period":14});a=val("atr",TF,{"period":14})
            u=val("bollinger.upper",TF,{"period":20,"multiplier":2})
            l=val("bollinger.lower",TF,{"period":20,"multiplier":2})
            adx=val("adx",TF,{"period":14})
            rows.append(dict(k=i+1,o=float(ca.open),h=float(ca.high),l=float(ca.low),c=float(ca.close),v=float(ca.volume),
                r=r,atr=a,upper=u,lower=l,adx=adx,ema=ema,h4close=h4close))
            if prev is not None and r is not None and i+1<len(bars[0]):
                if prev>=20>r:signals.append((len(rows)-1,1))
                elif prev<=80<r:signals.append((len(rows)-1,-1))
            prev=r
    assert i+1==len(bars[0]) and not group and not h4
    return bars,rows,signals,rec

def pivots(rows):
    # At bar j, the pivot at j-2 first becomes known.
    last={1:None,-1:None};known={1:[], -1:[]}
    for j in range(len(rows)):
        if j>=4:
            z=j-2
            for d,col in ((1,"l"),(-1,"h")):
                p=rows[z][col]
                if all(d*p<d*rows[x][col] for x in (z-2,z-1,z+1,z+2)):
                    last[d]=(z,p)
        for d in (1,-1):known[d].append(last[d])
    return known

def entry_sets(rows,signals):
    known=pivots(rows);out={m:[] for m in MODES}
    vol=np.asarray([x["v"] for x in rows])
    for q,(i,d) in enumerate(signals):
        until=signals[q+1][0] if q+1<len(signals) else len(rows)-1
        anchor=rows[i];col="l" if d==1 else "h"
        prior=known[d][i-1] if i else None
        extreme=anchor[col];found=set()
        for j in range(i,until):
            b=rows[j];p=rows[j-1] if j else b
            if b["k"]>=len(rows)*15:break
            extreme=min(extreme,b[col]) if d==1 else max(extreme,b[col])
            r=b["r"];pr=p["r"]
            recovery=j>i and r is not None and pr is not None and (pr<=20<r if d==1 else pr>=80>r)
            directional=d*(b["c"]-b["o"])>0
            band="lower" if d==1 else "upper"
            reclaim=j>i and b[band] is not None and p[band] is not None and d*(p["c"]-p[band])<=0 and d*(b["c"]-b[band])>0
            sweep=prior is not None and d*(b[col]-prior[1])<0 and d*(b["c"]-prior[1])>0 and directional
            wick=min(b["o"],b["c"])-b["l"] if d==1 else b["h"]-max(b["o"],b["c"])
            volume=j>=20 and b["v"]>=1.5*np.mean(vol[j-20:j]) and np.mean(vol[j-20:j])>0 and directional and wick>=abs(b["c"]-b["o"])
            # First post-signal confirmed pivot; second distinct test within
            # half ATR, directional candle closes back past the first extreme.
            pivot=known[d][j-1] if j else None
            double=j>i and pivot is not None and pivot[0]>=i and j-pivot[0]>=3 and b["atr"] is not None and abs(b[col]-pivot[1])<=.5*b["atr"] and d*(b["c"]-pivot[1])>0 and directional
            conditions={
                "trend-recovery":recovery and b["ema"] is not None and d*(b["h4close"]-b["ema"])>0,
                "bollinger-reclaim":reclaim,
                "liquidity-sweep":sweep,
                "volume-exhaustion":volume,
                "double-test":double,
                "adx-range-recovery":recovery and b["adx"] is not None and b["adx"]<25,
            }
            for mode,ok in conditions.items():
                if ok and mode not in found:
                    # Store the known adverse extreme of the setup, not a future pivot.
                    out[mode].append((i,j,d,extreme))
                    found.add(mode)
            if len(found)==len(MODES):break
    return out

def replay(bars,rows,es,mode,plan,rec):
    O,H,L,C=bars;kind,s,t=plan
    trades=[];free=0;empty=np.empty(0,dtype=np.float64)
    ids={ (d.base,d.name,d.timeframe.seconds):m["id"] for d,m in zip(rec.specs,rec.definitions)}
    # Recorder order is canonical and matches book specifications.
    for i,j,d,extreme in es:
        a,b=rows[i],rows[j];k=b["k"]
        if a["k"]<free or k<free or k>=len(O):continue
        ep=float(O[k]);atr=b["atr"]
        if kind=="atr":
            if atr is None or atr<=0:continue
            sd=max(TICK,math.ceil(s*atr/TICK)*TICK)
            td=max(TICK,math.ceil(t*atr/TICK)*TICK)
        else:
            level=(a["l"] if d==1 else a["h"]) if kind=="signal" else extreme
            stop=level-d*TICK;sd=d*(ep-stop)
            if sd<=0:continue
            td=max(TICK,math.ceil(t*sd/TICK)*TICK)
        target=ep+d*td
        x,xp,reason=execute(O,H,L,C,k,d,sd,target,0,-1,empty)
        free=x+1;gross=d*(xp-ep);fee=(ep+xp)*FEE
        vals={}
        for spec_obj,m in zip(rec.specs,rec.definitions):
            key={"rsi":"r","atr":"atr","ema":"ema","adx":"adx"}.get(spec_obj.base)
            if spec_obj.base=="bollinger":key="upper" if spec_obj.name.endswith("upper") else "lower"
            if key and b[key] is not None:vals[m["id"]]=b[key]
        trades.append(dict(entry_utc=dt(START+k*60).isoformat(),trigger_utc=dt(START+a["k"]*60).isoformat(),
            exit_utc=dt(END if reason==4 else START+x*60).isoformat(),side=d,entry_price=ep,exit_price=float(xp),
            stop_price=ep-d*sd,target_price=target,gross_points=gross,fee_points=fee,net_points=gross-fee,
            assumed_slippage_points=0,entry_reason=mode,exit_reason={1:"Initial stop",2:"Fixed target",4:"End of 2025 evaluation"}[reason],
            signal_context=dict(rsi14=a["r"],confirmation_rsi14=b["r"],confirmation_utc=dt(START+k*60).isoformat(),
                initial_risk_points=sd,setup_extreme=extreme,atr14=atr,adx14=b["adx"],h4_ema50=b["ema"]),indicator_values=vals))
    p=[x["net_points"] for x in trades];gain=math.fsum(max(0,n) for n in p);loss=-math.fsum(min(0,n) for n in p)
    months={f"2025-{m:02d}":0. for m in range(1,13)};eq=peak=dd=0.
    for tr,n in zip(trades,p):
        months[tr["entry_utc"][:7]]+=n;eq+=n;peak=max(peak,eq);dd=max(dd,peak-eq)
    wins=sum(n>0 for n in p)
    summary=dict(accounting="realized",open_position=None,trades=len(p),net=math.fsum(p),wins=wins,
        win_rate=100*wins/len(p) if p else 0,profit_factor=gain/loss if loss else None,
        realized_drawdown_points=dd,monthly_entry_attribution=months,profitable_months=sum(x>0 for x in months.values()))
    key=f"{mode}-{kind}-sl{s}-target{t}"
    params=dict(entry=mode,stop_kind=kind,stop_atr_multiple=s if kind=="atr" else None,target_multiple=t,
        target_unit="ATR" if kind=="atr" else "R",rsi_period=14,long_threshold=20,short_threshold=80,
        trading_days="all",signals_while_open="ignored")
    return dict(key=key,name="15M RSI14 Reversal | "+key,parameters=params,summary=summary,trades=trades)

def run():
    tests()
    bars,rows,signals,rec=load_data()
    entries=entry_sets(rows,signals)
    variants=[]
    for mode in MODES:
        print("ENTRIES",mode,len(entries[mode]))
        for plan in PLANS:
            v=replay(bars,rows,entries[mode],mode,plan,rec)
            variants.append(v);print("RESULT",v["key"],json.dumps(v["summary"],allow_nan=False,separators=(",",":")))
    assert len(variants)==72
    OUT.mkdir(parents=True,exist_ok=True)
    with gzip.open(OUT/"all_ledgers.json.gz","wt") as f:json.dump(variants,f,allow_nan=False,separators=(",",":"))
    results=[dict(key=v["key"],**v["parameters"],**{k:x for k,x in v["summary"].items() if k!="monthly_entry_attribution"},**v["summary"]["monthly_entry_attribution"]) for v in variants]
    with (OUT/"all_results.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(results[0]));w.writeheader();w.writerows(results)
    selected={}
    for mode in MODES:
        vs=[v for v in variants if v["parameters"]["entry"]==mode]
        for v in (max(vs,key=lambda v:v["summary"]["net"]),max(vs,key=lambda v:(v["summary"]["profitable_months"],v["summary"]["net"]))):
            selected[v["key"]]=v
    export_bundle(OUT/"backtest.json",family="rsi14-reversal-regimes-2025",symbol="BTCUSD",unit="price points",
        start_utc=dt(START).isoformat(),end_utc=dt(END).isoformat(),execution_timeframe_minutes=1,signal_timeframe_minutes=15,
        costs="0.05% taker each side +18% GST; no Scalper Offer; zero extra slippage; funding/liquidation excluded; 1m Color, stop gap at open.",
        variants=list(selected.values()),recorder=rec,data_provenance=dict(
            manifest=str(ROOT/"manifest.json"),manifest_sha256=hashlib.sha256((ROOT/"manifest.json").read_bytes()).hexdigest(),
            input_minutes=len(bars[0]),selection="72 predeclared combinations; 2025 in-sample, all archived; net/month leaders per entry submitted to dashboard",
            trend="RSI recovery and last completed H4 close on directional side of EMA50",
            bollinger="20,2 close back inside outer band",sweep="prior confirmed 2-left/2-right pivot, sweep and directional reclaim",
            volume="true 15m volume >=1.5 times preceding 20 average, rejection wick >= body",
            double="confirmed post-signal pivot retest within 0.5 ATR, at least 3 bars apart, directional reclaim",
            adx="RSI recovery and 15m ADX14 below 25",swing_stop="adverse extreme from RSI signal through confirmation plus one tick",
            month_attribution="UTC entry month; trade-close drawdown",setup_expiry="next threshold crossing; signals during position ignored"))
    print("TOTAL",len(variants),"PROFITABLE",sum(v["summary"]["net"]>0 for v in variants),"SUBMITTED",len(selected))
if __name__=="__main__":run()
