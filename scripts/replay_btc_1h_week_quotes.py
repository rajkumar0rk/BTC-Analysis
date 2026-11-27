"""BTC 1h replay: real observed production L2 + mark, alongside minute path sensitivity.
No authenticated orders, no future quote use. Demo execution is not production execution.
"""
import argparse,csv,gzip,hashlib,heapq,json,math,time
from collections import Counter
from pathlib import Path
from urllib.request import urlopen,Request
from urllib.parse import urlencode
import numpy as np
import pandas as pd
from btc_quote_book import DeltaBook,BadBook
from btc_1h_bot_indicators import indicators
START=int(pd.Timestamp("2026-11-23 00:00",tz="Asia/Kolkata").timestamp())
END=int(pd.Timestamp("2026-11-27 09:30",tz="Asia/Kolkata").timestamp())
FEE=.00059; BUDGET=10.; SHOCK=.01; LOT=.001; TICK=.5; POLL=3; STALE=15
def api(path,params):
    url="https://api.india.delta.exchange"+path+"?"+urlencode(params)
    with urlopen(Request(url,headers={"User-Agent":"BTC-Analysis/quote-replay","Accept":"application/json"}),timeout=25) as r:
        j=json.load(r)
    if not j.get("success"):raise ValueError("API failure")
    return j["result"]
def candles(symbol,a,b,step=60):
    rows={};res="1m" if step==60 else "1h"
    for attempt in range(6):
        for lo in range(a,b,900*step):
            hi=min(b,lo+900*step)
            if all(t in rows for t in range(lo,hi,step)):continue
            try:
                for x in api("/v2/history/candles",dict(symbol=symbol,resolution=res,start=lo,end=hi-1)):
                    t=int(x["time"])
                    if lo<=t<hi and t%step==0:
                        v=[float(x[k]) for k in ("open","high","low","close")]+[float(x.get("volume") or 0)]
                        assert all(math.isfinite(y) for y in v) and 0<v[2]<=min(v[0],v[3])<=max(v[0],v[3])<=v[1]
                        if t in rows and rows[t]!=v:raise RuntimeError("conflicting candles")
                        rows[t]=v
            except RuntimeError:raise
            except Exception as e: print("CANDLE_RETRY",symbol,lo,type(e).__name__,flush=True)
            time.sleep(.2)
        if len(rows)==(b-a)//step:break
    assert len(rows)==(b-a)//step,(symbol,len(rows),(b-a)//step)
    return pd.DataFrame([rows[t] for t in range(a,b,step)],index=pd.to_datetime(list(range(a,b,step)),unit="s",utc=True),columns=["open","high","low","close","volume"])
def signals():
    a=(START//3600-350)*3600;b=END//3600*3600
    h=candles("BTCUSD",a,b,3600);f=indicators(h);out={}
    for k in range(1,len(f)):
        p,x=f.iloc[k-1],f.iloc[k];ts=int(f.index[k].timestamp())+3600+12
        if START<=ts<END:
            side=1 if p.dir==x.dir==-1 and x.low<=x.ema<x.close else -1 if p.dir==x.dir==1 and x.high>=x.ema>x.close else 0
            out[ts]=(side,float(x.close),max(TICK,round(2*x.atr14/TICK)*TICK),int(p.dir),int(x.dir))
    print("SIGNALS",json.dumps(dict(hours=len(h),eligible=sum(bool(v[0]) for v in out.values()))),flush=True)
    return out
def quant(p,side):return (math.ceil((p-1e-9)/TICK) if side==1 else math.floor((p+1e-9)/TICK))*TICK
def value(msg,keys):
    for k in keys:
        try:
            v=float(msg[k])
            if math.isfinite(v) and v>0:return v
        except (KeyError,ValueError,TypeError):pass
    return None
class Feed:
    def __init__(self):
        self.book=DeltaBook();self.bt=self.mt=self.lt=-1e30;self.mark=self.last=None;self.stats=Counter()
    def reset(self):
        self.book=DeltaBook();self.bt=self.mt=self.lt=-1e30;self.mark=self.last=None
    def update(self,row,t):
        kind=row["kind"]
        if kind in ("disconnect","invalid_window","connection"):
            self.stats[kind]+=1;self.reset();return
        if kind!="ws_raw":return
        m=json.loads(row["raw"])
        if not isinstance(m,dict):return
        typ=m.get("type");sym=m.get("symbol") or m.get("sy")
        if typ=="ob_updates" and sym=="BTCUSD":
            try:self.book.update(m);self.bt=t;self.stats["verified_book"]+=1
            except BadBook:self.book=DeltaBook();self.bt=-1e30;self.stats["invalid_book"]+=1
        elif typ=="mark_price" and sym in ("MARK:BTCUSD","BTCUSD"):
            self.stats["mark_messages"]+=1
            v=value(m,("price","mark_price","mark","p"))
            if v is not None:self.mark=v;self.mt=t;self.stats["parsed_mark"]+=1
        elif sym=="BTCUSD" and typ in ("trades","trade","ticker"):
            v=value(m,("price","close","last_price","last","p"))
            if v is not None:self.last=v;self.lt=t;self.stats["parsed_last"]+=1
    def snapshot(self,t):
        if self.book.seq is None or self.mark is None or t-self.bt>STALE or t-self.mt>STALE:return None
        # Entry uses a fresh last trade; exits use observed mark and verified book.
        last=self.last if t-self.lt<=STALE else None
        return (self.mark,last,self.book)
def records(root,venue,counts):
    entries=[]
    for p in (root/venue).glob("*/*.jsonl.gz"):
        m=json.loads(Path(str(p)+".manifest.json").read_text())
        if m["last_recv_ns"]<(START-1800)*10**9 or m["first_recv_ns"]>=END*10**9:continue
        assert hashlib.sha256(p.read_bytes()).hexdigest()==m["sha256"],str(p)
        entries.append((m["first_recv_ns"],p));counts[venue+"_files"]+=1
    prev=-1
    for _,p in sorted(entries):
        with gzip.open(p,"rt") as f:
            for l in f:
                r=json.loads(l);n=int(r["recv_ns"])
                if n<prev:raise ValueError("nonmonotonic source timestamps")
                prev=n
                if (START-1800)*10**9<=n<END*10**9:
                    yield (n,venue,r)
class Engine:
    def __init__(self,name,sigs):
        self.name=name;self.sigs=sigs;self.cash=100.;self.p=None;self.trades=[];self.stats=Counter();self.peak=100.;self.dd=0.;self.gap_open=False;self.last_mark=None
    def equity(self,mark):
        return self.cash+(self.p["side"]*self.p["qty"]*(mark-self.p["entry"]) if self.p else 0.)
    def observe(self,mark):
        e=self.equity(mark);self.peak=max(self.peak,e);self.dd=max(self.dd,100*(self.peak-e)/self.peak);self.last_mark=mark
    def fill(self,snap,side,n):
        mark,last,book=snap
        if isinstance(book,(int,float)):return float(book)
        levels=book.asks if side==1 else book.bids
        left=n;cost=0.
        for price,qty in sorted(((float(p),float(q)) for p,q in levels.items()),reverse=side==-1):
            q=min(left,qty);cost+=price*q;left-=q
            if left<=1e-9:return cost/n
        return None
    def close(self,t,snap,reason):
        p=self.p;price=self.fill(snap,-p["side"],p["contracts"])
        if price is None:self.stats["exit_depth_unavailable"]+=1;self.gap_open=True;return
        fee=0. if t-p["t"]<=27*60 else price*p["qty"]*FEE
        if reason=="liquidation_proxy":fee+=price*p["qty"]*FEE
        gross=p["side"]*(price-p["entry"])*p["qty"];net=gross-p["fee"]-fee
        self.cash+=gross-fee
        self.trades.append(dict(entry_utc=pd.Timestamp(p["t"],unit="s",tz="UTC").isoformat(),exit_utc=pd.Timestamp(t,unit="s",tz="UTC").isoformat(),side=p["side"],entry=p["entry"],exit=price,contracts=p["contracts"],gross=gross,fees_gst=p["fee"]+fee,net=net,reason=reason,gap_while_open=self.gap_open))
        self.p=None;self.gap_open=False
    def step(self,t,snap,poll=False,signal=None):
        if snap is None:
            if poll:self.stats["invalid_poll"]+=1
            if self.p:self.gap_open=True
            if signal is not None and signal[0]:self.stats["signal_no_quote"]+=1
            return
        mark,last,_=snap
        if poll:self.stats["valid_poll"]+=1
        self.observe(mark)
        if self.p:
            p=self.p;s=p["side"]
            if p["liq"] is not None and s*(mark-p["liq"])<=0:self.close(t,snap,"liquidation_proxy")
            elif s*(mark-p["stop"])<=0:self.close(t,snap,"native_stop_proxy")
            elif poll:
                if s*(mark-p["entry"])>=100:p["active"]=True
                if p["active"]:
                    p["best"]=max(p["best"],mark) if s==1 else min(p["best"],mark)
                    candidate=quant(p["best"]-s*50,s)
                    if s*(mark-candidate)>=max(4*TICK,abs(mark)*.00001):
                        p["stop"]=max(p["stop"],candidate) if s==1 else min(p["stop"],candidate)
        if signal is not None:
            side,close,dist,prior,d=signal
            if self.p:
                if self.p["side"]==1 and prior==-1 and d==1 or self.p["side"]==-1 and prior==1 and d==-1:self.close(t,snap,"supertrend_flip")
                if side:self.stats["busy_signal"]+=1
                return
            if not side:return
            self.stats["entry_signals"]+=1
            if last is None or abs(last-close)/close>.002 or self.cash<11:
                self.stats["entry_guard_skip"]+=1;return
            n=math.floor(min(BUDGET*100,BUDGET/SHOCK)/(last*LOT)+1e-10)
            if n<1:self.stats["size_skip"]+=1;return
            entry=self.fill(snap,side,n)
            if entry is None:self.stats["entry_depth_unavailable"]+=1;return
            qty=n*LOT;fee=entry*qty*FEE;after=self.cash-fee
            liq=(qty*entry-after)/(qty*(1-.0075)) if side==1 else (qty*entry+after)/(qty*(1+.0075))
            if liq<=0:liq=None
            stop=quant(entry-side*dist,side)
            if liq is not None:
                near=quant(liq+side*1.,side)
                if side*(entry-near)>0:stop=max(stop,near) if side==1 else min(stop,near)
            if side*(mark-stop)<=0:self.stats["mark_stop_skip"]+=1;return
            self.cash=after;self.p=dict(side=side,entry=entry,qty=qty,contracts=n,fee=fee,t=t,stop=stop,liq=liq,active=False,best=entry)
        self.observe(mark)
    def result(self,out):
        v=[x["net"] for x in self.trades];wins=sum(x>0 for x in v);loss=-sum(x for x in v if x<0)
        end=self.equity(self.last_mark) if self.last_mark is not None else self.cash
        with (out/(self.name+"-trades.csv")).open("w") as f:
            if self.trades:
                w=csv.DictWriter(f,fieldnames=list(self.trades[0]));w.writeheader();w.writerows(self.trades)
        day={}
        for r in self.trades:
            k=pd.Timestamp(r["exit_utc"]).tz_convert("Asia/Kolkata").strftime("%Y-%m-%d")
            day[k]=day.get(k,0)+r["net"]
        return dict(model=self.name,net=end-100,realized=sum(v),end_equity=end,trades=len(v),wins=wins,losses=sum(x<0 for x in v),win_rate=100*wins/len(v) if v else None,pf=sum(x for x in v if x>0)/loss if loss else None,dd=self.dd,fees=sum(r["fees_gst"] for r in self.trades)+(self.p["fee"] if self.p else 0),open_at_end=bool(self.p),gap_affected_trades=sum(r["gap_while_open"] for r in self.trades),open_gap=self.gap_open,liquidations=sum(r["reason"]=="liquidation_proxy" for r in self.trades),days=day,stats=dict(self.stats))
def quotes(root,sigs,out):
    fs={v:Feed() for v in ("delta","delta_backup")};counts=Counter()
    e=Engine("recorded_quotes",sigs)
    poll=START+((-START)%POLL)
    def snapshot(t):
        for f in fs.values():
            q=f.snapshot(t)
            if q is not None:return q
        return None
    last_event=None
    for ns,venue,row in heapq.merge(*(records(root,v,counts) for v in fs),key=lambda x:(x[0],x[1])):
        t=ns/1e9
        while poll<t and poll<END:
            e.step(poll,snapshot(poll),True,sigs.get(poll));poll+=POLL
        fs[venue].update(row,t);counts["events"]+=1
        if t>=START and e.p:
            q=snapshot(t)
            # Native stop checked on every recorded event; trailing only on 3s polls.
            if q is not None:
                mark=q[0]
                if e.p["side"]*(mark-e.p["stop"])<=0 or (e.p["liq"] is not None and e.p["side"]*(mark-e.p["liq"])<=0):
                    e.step(t,q)
            elif all(t-f.bt>STALE or t-f.mt>STALE or f.book.seq is None for f in fs.values()):e.gap_open=True
        last_event=t
    while poll<END:e.step(poll,snapshot(poll),True,sigs.get(poll));poll+=POLL
    result=e.result(out);result["archive_counts"]=dict(counts);result["feed_stats"]={k:dict(f.stats) for k,f in fs.items()}
    result["last_event_utc"]=pd.Timestamp(last_event,unit="s",tz="UTC").isoformat() if last_event else None
    if result["stats"].get("invalid_poll",0) or result["gap_affected_trades"] or result["open_gap"]:result["coverage_warning"]="Invalid/stale observations occurred; not continuous or exact; gap-affected P&L provisional."
    return result
def ohlc(sigs,out):
    a=candles("BTCUSD",START,END);m=candles("MARK:BTCUSD",START,END);results=[]
    for name in ("OHLC","OLHC","COLOR","DIRECTION"):
        e=Engine(name,sigs)
        for i,(ar,mr) in enumerate(zip(a.to_numpy(),m.to_numpy())):
            t=START+i*60
            # Same minute-open proxy used in previous comparisons; signal processed +12s.
            e.step(t,(mr[0],ar[0],ar[0]),True)
            e.step(t+12,(mr[0],ar[0],ar[0]),True,sigs.get(t+12))
            low_first=name=="OLHC" or (name=="COLOR" and (ar[3]>ar[0] or ar[3]==ar[0] and ar[0]-ar[2]<=ar[1]-ar[0])) or (name=="DIRECTION" and e.p is not None and e.p["side"]==1)
            for ts,k in zip((t+20,t+40,t+59),(2,1,3) if low_first else (1,2,3)):
                e.step(ts,(mr[k],ar[k],ar[k]),True)
        results.append(e.result(out))
    return results
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--archive",type=Path,required=True);p.add_argument("--output",type=Path,required=True);args=p.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    s=signals();q=quotes(args.archive,s,args.output)
    print("BTC_QUOTE_RESULT "+json.dumps(q),flush=True)
    (args.output/"quote-summary.json").write_text(json.dumps(q,indent=2))
    scenarios=ohlc(s,args.output)
    for r in scenarios:print("BTC_OHLC_RESULT "+json.dumps(r),flush=True)
    (args.output/"summary.json").write_text(json.dumps([q]+scenarios,indent=2))
