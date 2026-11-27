"""BTC 15m paper replay: real observed production L2 + mark, alongside minute path sensitivity.
No authenticated orders. Quote replay uses receive-time L1 reconstructed from verified production L2 at 3-second polls, not exact historical REST ticker snapshots. OHLC paths use synthetic timing. Funding excluded; portfolio risk proxy.
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
    rows={};res={60:'1m',900:'15m',3600:'1h'}[step]
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
    a=(START//900-1000)*900;b=END//900*900
    h=candles("BTCUSD",a,b,900);out={}
    for k in range(999,len(h)):
        f=indicators(h.iloc[k-999:k+1]);p,x=f.iloc[-2],f.iloc[-1];ts=int(x.name.timestamp())+900+12
        if START<=ts<END:
            side=1 if p.dir==x.dir==-1 and x.low<=x.ema<x.close else -1 if p.dir==x.dir==1 and x.high>=x.ema>x.close else 0
            if not (x.atr_ratio>=1 and x.volume_ratio>=1.5):side=0
            out[ts]=(side,float(x.close),max(TICK,round(2*x.atr14/TICK)*TICK),int(p.dir),int(x.dir))
    print("SIGNALS",json.dumps(dict(bars_15m=len(h),eligible=sum(bool(v[0]) for v in out.values()))),flush=True)
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
        if self.book.seq is None or self.mark is None or self.last is None or t-self.bt>STALE or t-self.mt>STALE or t-self.lt>STALE:return None
        bid=max(self.book.bids,key=float);ask=min(self.book.asks,key=float)
        if 100*(float(ask)-float(bid))/((float(ask)+float(bid))/2)>.30:return None
        if min(float(self.book.bids[bid]),float(self.book.asks[ask]))<1:return None
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
        return min(map(float,book.asks)) if side==1 else max(map(float,book.bids))
    def close(self,t,snap,reason):
        p=self.p;price=self.fill(snap,-p["side"],p["contracts"])
        if price is None:self.stats["exit_depth_unavailable"]+=1;self.gap_open=True;return
        fee=0. if t-p["t"]<=30*60 and reason!="liquidation_proxy" else price*p["qty"]*FEE
        gross=p["side"]*(price-p["entry"])*p["qty"];net=gross-p["fee"]-fee
        end_cash=max(0,self.cash+gross-fee);net=end_cash-self.cash-p["fee"];self.cash=end_cash
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
            else:
                if s*(mark-p["entry"])>=150:p["active"]=True
                if p["active"]:
                    p["best"]=max(p["best"],mark) if s==1 else min(p["best"],mark)
                    candidate=p["best"]-s*50
                    p["stop"]=max(p["stop"],candidate) if s==1 else min(p["stop"],candidate)
                if s*(mark-p["stop"])<=0:self.close(t,snap,"underlying_trail" if p["active"] else "underlying_atr")
        if signal is not None:
            side,close,dist,prior,d=signal
            if self.p:
                if self.p["side"]==1 and prior==-1 and d==1 or self.p["side"]==-1 and prior==1 and d==-1:self.close(t,snap,"supertrend_flip")
                if side:self.stats["busy_signal"]+=1
                return
            if not side:return
            self.stats["entry_signals"]+=1
            if last is None or abs(last-close)/close>.002:
                self.stats["entry_guard_skip"]+=1;return
            entry=self.fill(snap,side,1)
            n=math.floor(min(BUDGET*100,BUDGET/SHOCK)/(entry*LOT)+1e-10)
            book=snap[2]
            if not isinstance(book,(int,float)):
                bid=max(book.bids,key=float);ask=min(book.asks,key=float)
                n=min(n,int(float(book.bids[bid])),int(float(book.asks[ask])))
            if n<1:self.stats["size_skip"]+=1;return
            qty=n*LOT;fee=entry*qty*FEE;after=self.cash-fee
            if self.cash<entry*qty*SHOCK+fee:self.stats["margin_skip"]+=1;return
            liq=(qty*entry-after)/(qty*(1-.0075)) if side==1 else (qty*entry+after)/(qty*(1+.0075))
            if liq<=0:liq=None
            stop=quant(entry-side*dist,side)
            if liq is not None:
                near=quant(liq+side*1.,side)
                if side*(entry-near)>0:stop=max(stop,near) if side==1 else min(stop,near)
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
    print("BTC15_QUOTE_RESULT "+json.dumps(q),flush=True)
    (args.output/"quote-summary.json").write_text(json.dumps(q,indent=2))
    scenarios=ohlc(s,args.output)
    for r in scenarios:print("BTC15_OHLC_RESULT "+json.dumps(r),flush=True)
    (args.output/"summary.json").write_text(json.dumps([q]+scenarios,indent=2))
