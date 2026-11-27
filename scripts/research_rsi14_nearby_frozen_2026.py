"""Frozen RSI 83/17 candidate and 80/20 comparator on 2026. No tuning."""
import csv,gzip,hashlib,json,math
from datetime import datetime,timezone,timedelta
from decimal import Decimal as D
from pathlib import Path
import numpy as np
import research_rsi14_consistency_risk_2025 as risk
import research_rsi14_entry_quality_2025 as quality
import research_rsi14_simple_robustness_2025 as simple
from research_rsi14_80_20_2025 import TF,INSTRUMENT,dt,signal,Candle,IndicatorBook,spec,IndicatorRecorder,export_bundle
from research_rsi14_improvements_2025 import HOUR
ROOT=Path("data/delta_india/BTCUSD/1m")
IST=timezone.utc
START=int(datetime(2025,12,24,tzinfo=timezone.utc).timestamp())
EVAL=int(datetime(2026,1,1,tzinfo=timezone.utc).timestamp())
END=int(datetime(2026,11,27,tzinfo=timezone.utc).timestamp())
CUTOFF=int(datetime(2026,11,1,tzinfo=timezone.utc).timestamp())
MONTHS=[f"2026-{m:02d}" for m in range(1,12)]
OUT=Path("scratch/rsi14_nearby_frozen_2026")
def candles():
    meta=json.loads((ROOT/"manifest.json").read_text())
    parts=[p for p in meta["partitions"] if p["file"]=="2025-12.csv.gz" or p["file"].startswith("2026-")]
    assert len(parts)==12 and all(p["missing_minutes"]==0 for p in parts)
    expected=START
    for p in parts:
        path=ROOT/p["file"]
        assert hashlib.sha256(path.read_bytes()).hexdigest()==p["sha256_gzip"],path
        count=0;previous=-1
        with gzip.open(path,"rt") as f:
            for row in csv.DictReader(f):
                t=int(row["time"]);count+=1
                assert t%60==0 and t>previous
                previous=t
                if t<START:continue
                assert t==expected,(t,expected,path)
                expected+=60
                o,h,l,c,v=(D(row[k]) for k in ("open","high","low","close","volume"))
                assert all(x.is_finite() for x in (o,h,l,c,v))
                assert 0<l<=min(o,c)<=max(o,c)<=h and v>=0
                yield t,o,h,l,c,v
        assert count==p["observed_candles"]
    assert expected==END,(expected,END)
def load():
    # Identical indicator definitions and aggregation to the 2025 loader;
    # the last partial UTC hour is not submitted to the indicator book.
    book=IndicatorBook((spec("rsi",TF,period=14),spec("atr",TF,period=14),spec("ema",HOUR,period=50),spec("ema",TF,period=20),spec("supertrend.direction",TF,period=10,multiplier=3),spec("supertrend.line",TF,period=10,multiplier=3)),history_limit=2)
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
            book.update(ca);rec.completed(ca);hour.clear();ema=val("ema",HOUR,{"period":50})
        if len(group)==15:
            ca=Candle(INSTRUMENT,TF,dt(end-900),dt(end),group[0][0],max(x[1] for x in group),min(x[2] for x in group),group[-1][3],sum(x[4] for x in group))
            book.update(ca);rec.completed(ca);group.clear();k=i+1
            r=book.get("rsi",TF,{"period":14})[-1]
            snapshots[k]=(val("atr",TF,{"period":14}),ema,float(ca.open),float(ca.close))
            extra[k]=(val("ema",TF,{"period":20}),val("supertrend.direction",TF,{"period":10,"multiplier":3}),val("supertrend.line",TF,{"period":10,"multiplier":3}),float(ca.high),float(ca.low),float(ca.close))
            d=signal(prev,r)
            if d and k<n and end>=EVAL:signals.append((k,d,float(r),float(ca.high),float(ca.low)))
            prev=r
    assert i+1==n and not group and not hour
    return bars,signals,snapshots,extra,rec
def summarize(trades,cost=0):
    months={k:dict(net=0.,trades=0,wins=0) for k in MONTHS};p=[];eq=peak=dd=0.
    for t in trades:
        k=datetime.fromisoformat(t["entry_utc"]).astimezone(IST).strftime("%Y-%m")
        n=t["net_points"]-cost;p.append(n);m=months[k]
        m["net"]+=n;m["trades"]+=1;m["wins"]+=n>0
        eq+=n;peak=max(peak,eq);dd=max(dd,peak-eq)
    gain=math.fsum(max(0,n) for n in p);loss=-math.fsum(min(0,n) for n in p);wins=sum(n>0 for n in p)
    return dict(accounting="realized",open_position=None,net=math.fsum(p),trades=len(p),wins=wins,win_rate=100*wins/len(p) if p else 0,profit_factor=gain/loss if loss else None,realized_drawdown_points=dd,profitable_months=sum(m["net"]>0 for m in months.values()),monthly_entry_attribution={k:m["net"] for k,m in months.items()},month_details=months,worst_month=min(m["net"] for m in months.values()),losing_months=sum(m["net"]<0 for m in months.values()),flat_months=sum(m["net"]==0 for m in months.values()))
from research_rsi14_nearby_thresholds import signals_for
from research_rsi14_depth_stability import replay,checks
def run():
    global MONTHS
    checks()
    quality.candles=candles
    bars,signals,snapshots,extra,rec=load()
    ind=quality.indicators(bars,snapshots)
    OUT.mkdir(parents=True,exist_ok=True)
    all_results={}
    plans=(("rsi83-17-depth37.5-be0",83,.375,0,False),("rsi80-20-depth25-be750-ema50",80,.25,750,True),("rsi83-17-depth37.5-be1000",83,.375,1000,False))
    ss80=signals_for(rec,extra,START,END,EVAL,80)
    assert len(ss80)==len(signals) and all(a[:2]==b[:2] and a[3:]==b[3:] and math.isclose(a[2],b[2],abs_tol=1e-8) for a,b in zip(ss80,signals))
    for label,end in (("full-months",CUTOFF),("through-nov26",END)):
        MONTHS=[f"2026-{m:02d}" for m in range(1,11 if end==CUTOFF else 12)]
        n=(end-START)//60
        bb=bars[:,:n]
        ii=tuple(x[:n] if k<2 else x[:n//60+1] if k==4 else x[:n//15+1] for k,x in enumerate(ind))
        vs=[]
        for key,hi,depth,be,ema in plans:
            ss=signals_for(rec,extra,START,end,EVAL,hi)
            setups=quality.setup_rows(bb,ss,snapshots,extra)
            trades=replay(bb,ii,setups,START,end,("original",ema,depth,(be,False),3000.),snapshots)
            for t in trades:
                assert EVAL<=int(datetime.fromisoformat(t["entry_utc"]).timestamp())<end
            s=summarize(trades);stress=summarize(trades,50)
            s["stress_extra_50_points_roundtrip"]=dict(net=stress["net"],pf=stress["profit_factor"],months=stress["profitable_months"],dd=stress["realized_drawdown_points"],monthly=stress["monthly_entry_attribution"])
            s["input_minutes"]=(end-EVAL)//60
            s["meaningful_wins_over_50"]=sum(t["net_points"]>50 for t in trades)
            s["gross"]=sum(t["gross_points"] for t in trades);s["fees"]=sum(t["fee_points"] for t in trades)
            p=dict(entry="pullback-breakout",rsi_period=14,long_threshold=hi,short_threshold=100-hi,min_pullback_depth=depth,ema50=ema,fee_protection_points=be,stop_loss_points=1000,activation_points=3000,trail_points=1000,position_size="fixed",trading_days="all")
            v=dict(key=key+"-"+label,name="RSI14 "+key+" | 2026 "+label,parameters=p,summary=s,trades=trades)
            vs.append(v)
            print("VALIDATION",json.dumps(dict(period=label,key=key,**s),separators=(",",":"),allow_nan=False))
        all_results[label]=vs
        if end==CUTOFF:
            series={k:[x for x in a if EVAL<=x[0]<=end] for k,a in rec.series.items()}
            export_bundle(OUT/"backtest.json",family="rsi14-nearby-frozen-2026",symbol="BTCUSD",unit="price points",start_utc=dt(EVAL).isoformat(),end_utc=dt(end).isoformat(),execution_timeframe_minutes=1,signal_timeframe_minutes=15,costs="0.05% taker each side plus 18% GST; 1m Color; stop gaps at open; no funding, liquidation, extra slippage or Scalper Offer",variants=vs,indicator_definitions=rec.definitions,indicator_series=series,data_provenance=dict(manifest=str(ROOT/"manifest.json"),manifest_sha256=hashlib.sha256((ROOT/"manifest.json").read_bytes()).hexdigest(),input_minutes=(end-EVAL)//60,warmup_minutes=(EVAL-START)//60,monthly_timezone="UTC",timestamp_label="UTC open",synthetic_rows=0,selection="frozen 83/17 candidates and 80/20 comparator, no retuning on 2026",boundary="force-close final observed minute; monthly P&L entry attribution"))
    (OUT/"all_results.json").write_text(json.dumps(all_results,allow_nan=False,separators=(",",":")))
if __name__=="__main__":run()
