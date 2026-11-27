"""Original RSI14 pullback-breakout configuration on gap-free IST March-Dec 2024."""
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
ROOT=Path("data/delta_india/BTCUSD/2024_verified_archive")
IST=timezone(timedelta(hours=5,minutes=30))
START=int(datetime(2024,2,22,tzinfo=timezone.utc).timestamp())
EVAL=int(datetime(2024,3,1,tzinfo=IST).timestamp())
END=int(datetime(2025,1,1,tzinfo=IST).timestamp())
MONTHS=[f"2024-{m:02d}" for m in range(3,13)]
OUT=Path("scratch/rsi14_original_2024")
OLD=risk.BASES["original"][0]
CFG=(False,False,False,0,3.,False)
def candles():
    meta=json.loads((ROOT/"manifest.json").read_text())
    assert meta["synthetic_rows"]==0 and meta["original_trade_rows_preserved"]
    parts=sorted((p for p in meta["months"] if p["series"]=="trade_1m"),key=lambda p:p["month"])
    assert [p["month"] for p in parts if p["missing"]==0]==MONTHS
    expected=START
    for p in parts[1:]:
        path=ROOT/"trade_1m"/(p["month"]+".csv.gz")
        assert hashlib.sha256(path.read_bytes()).hexdigest()==p["sha256"],path
        a=int(datetime.fromisoformat(p["month"]+"-01").replace(tzinfo=IST).timestamp())
        b=a+p["expected"]*60
        count=0;previous=-1
        with gzip.open(path,"rt") as f:
            for row in csv.DictReader(f):
                t=int(row["time"]);count+=1
                assert a<=t<b and t%60==0 and t>previous
                previous=t
                if t<START:continue
                assert t==expected,(t,expected,path)
                expected+=60
                o,h,l,c,v=(D(row[k]) for k in ("open","high","low","close","volume"))
                assert all(x.is_finite() for x in (o,h,l,c,v))
                assert 0<l<=min(o,c)<=max(o,c)<=h and v>=0
                yield t,o,h,l,c,v
        assert count==p["observed"]
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
    assert i+1==n and not group and len(hour)==30
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
def run():
    risk.checks()
    # Baseline regression is already verified in parent workflow. No tuning.
    risk.START,risk.END=START,END
    quality.candles=candles
    bars,signals,snapshots,extra,rec=load()
    ind=quality.indicators(bars,snapshots);setups=quality.setup_rows(bars,signals,snapshots,extra)
    trades=risk.entries(bars,ind,np.full(len(ind[-1]),np.nan),setups,OLD,CFG)
    for t in trades:
        assert EVAL<=int(datetime.fromisoformat(t["entry_utc"]).timestamp())<END
        if t["exit_reason"]=="End of 2025":t["exit_reason"]="End of 2024 evaluation"
    s=summarize(trades);stress=summarize(trades,50)
    s["stress_extra_50_points_roundtrip"]=dict(net=stress["net"],pf=stress["profit_factor"],months=stress["profitable_months"],monthly=stress["monthly_entry_attribution"])
    s["input_minutes"]=(END-EVAL)//60
    p=dict(entry="pullback-breakout",rsi_period=14,long_threshold=80,short_threshold=20,rsi15_midpoint=False,rsi1h_midpoint=False,adx14_above25=False,one_retry=False,breakout_distance_points=None,stop_loss_points=1000,activation_points=3000,trail_points=1000,position_size="fixed",trading_days="all",frozen_2025_net=38547.273445)
    v=dict(key="original-38547-gapfree-2024",name="RSI14 original 38547 | 2024 Mar-Dec gap-free",parameters=p,summary=s,trades=trades)
    # Indicator history for the evaluation interval only; UTC candle grid retained.
    for k in rec.series:rec.series[k]=[x for x in rec.series[k] if x[0]>=EVAL]
    OUT.mkdir(parents=True,exist_ok=True)
    export_bundle(OUT/"backtest.json",family="rsi14-original-2024-gapfree",symbol="BTCUSD",unit="price points",start_utc=dt(EVAL).isoformat(),end_utc=dt(END).isoformat(),execution_timeframe_minutes=1,signal_timeframe_minutes=15,costs="0.05% taker each side plus 18% GST; 1m Color; stops gap at open; no funding, liquidation, additional slippage or Scalper Offer",variants=[v],recorder=rec,data_provenance=dict(manifest=str(ROOT/"manifest.json"),manifest_sha256=hashlib.sha256((ROOT/"manifest.json").read_bytes()).hexdigest(),input_minutes=(END-EVAL)//60,warmup_minutes=(EVAL-START)//60,monthly_timezone="Asia/Kolkata",timestamp_label="UTC open",excluded_months={"2024-01":29768,"2024-02":193},synthetic_rows=0,selection="single frozen 2025-selected configuration; retrospective 2024 validation, not untouched if prior research used 2024",warmup="verified contiguous February tail only, no warmup signals or trades; UTC-aligned 1h bars",boundary="force-close at final observed minute; monthly P&L attributed to entry in IST"))
    (OUT/"summary.json").write_text(json.dumps(s,indent=2,allow_nan=False))
    print("VALIDATION",json.dumps(s,separators=(",",":"),allow_nan=False))
if __name__=="__main__":run()
