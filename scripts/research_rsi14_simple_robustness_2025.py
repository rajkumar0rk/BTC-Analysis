"""Small, predefined 2025 RSI study. Prior selected variants are references, not validation."""
import hashlib,json,math
from pathlib import Path
import numpy as np
from research_rsi14_improvements_2025 import (
    ROOT,START,END,FEE,TF,HOUR,INSTRUMENT,dt,signal,candles,Candle,
    IndicatorBook,spec,IndicatorRecorder,export_bundle,verify,replay,candidates,
)

# One change at a time, standard 1:2 reward/risk, and adjacent distances.
# No selection or retuning after seeing results. All variants published.
PLAN=[
    ("direct","fixed",1000,2000,0,"reference"),
    ("pullback","fixed",1000,2000,0,"entry-only"),
    ("ema-reclaim","fixed",1000,2000,0,"entry-only"),
    ("supertrend","fixed",1000,2000,0,"filter-only"),
    ("direct","atr",2,4,0,"atr-only"),
    ("pullback","atr",2,4,0,"atr-alternative"),
    ("direct","fixed",1000,2000,1000,"fee-protection-at-1R"),
    ("pullback","fixed",1000,2000,1000,"fee-protection-at-1R"),
    ("direct","fixed",750,1500,0,"neighbor"),
    ("direct","fixed",1500,3000,0,"neighbor"),
    ("pullback","fixed",750,1500,0,"neighbor"),
    ("pullback","fixed",1500,3000,0,"neighbor"),
    ("pullback","fixed",750,3000,0,"previously-selected-reference"),
    ("pullback-breakout","fixed",1000,3000,0,"previously-selected-reference"),
]

def load():
    book=IndicatorBook((spec("rsi",TF,period=14),spec("atr",TF,period=14),
        spec("ema",HOUR,period=50),spec("ema",TF,period=20),
        spec("supertrend.direction",TF,period=10,multiplier=3),
        spec("supertrend.line",TF,period=10,multiplier=3)),history_limit=2)
    rec=IndicatorRecorder(book)
    n=(END-START)//60;bars=np.empty((4,n),dtype=np.float64)
    signals=[];snapshots={};extra={};group=[];hour=[];prev=None;ema=None
    def val(name,tf,params):
        v=book.get(name,tf,params)[-1]
        return float(v) if v is not None else None
    for i,(t,o,h,l,c,v) in enumerate(candles()):
        bars[:,i]=[float(o),float(h),float(l),float(c)]
        group.append((o,h,l,c,v));hour.append((o,h,l,c,v));end=t+60
        if len(hour)==60:
            ca=Candle(INSTRUMENT,HOUR,dt(end-3600),dt(end),hour[0][0],max(x[1] for x in hour),min(x[2] for x in hour),hour[-1][3],sum(x[4] for x in hour))
            book.update(ca);rec.completed(ca);hour.clear()
            ema=val("ema",HOUR,{"period":50})
        if len(group)==15:
            ca=Candle(INSTRUMENT,TF,dt(end-900),dt(end),group[0][0],max(x[1] for x in group),min(x[2] for x in group),group[-1][3],sum(x[4] for x in group))
            book.update(ca);rec.completed(ca);group.clear();k=i+1
            r=book.get("rsi",TF,{"period":14})[-1]
            snapshots[k]=(val("atr",TF,{"period":14}),ema,float(ca.open),float(ca.close))
            extra[k]=(val("ema",TF,{"period":20}),val("supertrend.direction",TF,{"period":10,"multiplier":3}),val("supertrend.line",TF,{"period":10,"multiplier":3}),float(ca.high),float(ca.low),float(ca.close))
            d=signal(prev,r)
            if d and k<n:signals.append((k,d,float(r),float(ca.high),float(ca.low)))
            prev=r
    assert i+1==n and not group and not hour
    return bars,signals,snapshots,extra,rec

def entry_list(bars,signals,snapshots,extra,mode):
    if mode not in ("ema-reclaim","supertrend"):
        return candidates(bars,signals,snapshots,mode,False)
    out=[]
    for q,(i,d,r,hi,lo) in enumerate(signals):
        until=signals[q+1][0] if q+1<len(signals) else len(bars[0])
        if mode=="supertrend":
            if extra[i][1]!=d:continue
            j=i
        else:
            j=-1
            # Only a subsequent completed 15m bar may confirm. Touch/pierce
            # EMA20 and close back strictly on the directional side.
            for k in range(i+15,until,15):
                e,st,line,h,l,c=extra[k]
                if e is not None and ((d==1 and l<=e<c) or (d==-1 and h>=e>c)):
                    j=k;break
            if j<0:continue
        at,ema,_,_=snapshots[j]
        out.append((j,d,r,i,at,ema))
    return out

def sensitivity(trades,extra_cost):
    # Accounting stress only; does not change fills or triggers.
    p=[t["net_points"]-extra_cost for t in trades]
    monthly={f"2025-{m:02d}":0. for m in range(1,13)}
    for t,n in zip(trades,p):monthly[t["entry_utc"][:7]]+=n
    gain=math.fsum(max(0,n) for n in p);loss=-math.fsum(min(0,n) for n in p)
    return dict(net=math.fsum(p),pf=gain/loss if loss else None,months=sum(n>0 for n in monthly.values()))

def run():
    verify()
    bars,signals,snapshots,extra,rec=load()
    mid={1:np.array([],dtype=np.int64),-1:np.array([],dtype=np.int64)}
    entries={mode:entry_list(bars,signals,snapshots,extra,mode) for mode in sorted({p[0] for p in PLAN})}
    variants=[]
    for mode,kind,sl,tp,be,role in PLAN:
        v=replay(bars,entries[mode],mid,mode,False,kind,sl,tp,be,False)
        v["parameters"]["research_role"]=role
        v["parameters"]["supertrend_filter"]=mode=="supertrend"
        v["parameters"]["ema20_reclaim"]=mode=="ema-reclaim"
        for t in v["trades"]:
            idx=(int(__import__("datetime").datetime.fromisoformat(t["entry_utc"]).timestamp())-START)//60
            e,st,line,_,_,_=extra[(idx//15)*15]
            for id,value in (("indicator_3",e),("indicator_4",st),("indicator_5",line)):
                if value is not None:t["indicator_values"][id]=value
        s=v["summary"]
        s["stress_extra_10_points_roundtrip"]=sensitivity(v["trades"],10)
        s["stress_extra_50_points_roundtrip"]=sensitivity(v["trades"],50)
        m=s["monthly_entry_attribution"]
        s["h1_net"]=sum(m[f"2025-{i:02d}"] for i in range(1,7))
        s["h2_net"]=sum(m[f"2025-{i:02d}"] for i in range(7,13))
        variants.append(v)
    assert len(variants)==14
    export_bundle(Path("scratch/rsi14_simple/backtest.json"),family="rsi14-simple-robustness-2025",symbol="BTCUSD",unit="price points",
        start_utc=dt(START).isoformat(),end_utc=dt(END).isoformat(),execution_timeframe_minutes=1,signal_timeframe_minutes=15,
        costs="0.05% taker per side + 18% GST; zero additional slippage baseline; extra 10/50 points per closed trade accounting stress only, not simulated fills. Funding and liquidation excluded. Color 1m execution; no Scalper Offer.",
        variants=variants,recorder=rec,data_provenance=dict(manifest=str(ROOT/"manifest.json"),
            manifest_sha256=hashlib.sha256((ROOT/"manifest.json").read_bytes()).hexdigest(),
            input_minutes=len(bars[0]),timestamp_label="assumed open UTC",selection="14 predefined variants; 12 comparisons and 2 previously selected references; 2025 in-sample; no 2026 access",
            setup_expiry="next RSI threshold crossing",entry_execution="next 1m open",month_attribution="entry month"))
    for v in variants:print("SIMPLE",json.dumps(dict(key=v["key"],**v["parameters"],**v["summary"]),allow_nan=False,separators=(",",":")))
if __name__=="__main__":run()
