"""Frozen BTC public L2 research baseline, no candle signals, no live orders.

Usage: PYTHONPATH=/path/to/collector python scripts/research_order_flow_baseline.py --archive /path --start ... --end ...
Independent one-lot taker strategies. No optimization, no maker fills, no promotional fee assumption.
"""
import argparse, bisect, collections, datetime as dt, gzip, hashlib, heapq, json, math
from pathlib import Path
from collector import DeltaBook, BadBook

NS=10**9
IST=dt.timezone(dt.timedelta(hours=5,minutes=30))
NAMES=('OFI','ABSORPTION','OBI','SWEEP_REVERSAL','OI_MOMENTUM','CVD_MOMENTUM')
FEE=.0005*1.18
LOT=.001
def stamp(s): return int(dt.datetime.fromisoformat(s).timestamp()*NS)
def day(t):return dt.datetime.fromtimestamp(t/NS,IST).date().isoformat()
def files(root,venue,lo,hi):
    out=[]
    for p in (root/venue).glob('*/*.jsonl.gz'):
        m=Path(str(p)+'.manifest.json')
        if not m.exists():continue
        a=json.loads(m.read_text())
        if a['last_recv_ns']<lo or a['first_recv_ns']>=hi:continue
        if a['sha256']!=hashlib.sha256(p.read_bytes()).hexdigest() or a['bytes']!=p.stat().st_size:
            raise ValueError('archive manifest mismatch '+str(p))
        out.append((a['first_recv_ns'],p))
    return [p for _,p in sorted(out)]
def raw_events(paths,lo,hi):
    prev=0
    for p in paths:
        with gzip.open(p,'rt') as f:
            for line in f:
                r=json.loads(line); t=r['recv_ns']
                if t<lo or t>=hi:continue
                if t<prev:raise ValueError('nonmonotonic receive time')
                prev=t
                k=r['kind']
                if k in ('connection','disconnect','invalid_window','ws_raw','rest_response','book_checkpoint'):
                    raw=r if k=='book_checkpoint' else r.get('raw','{}')
                    m=json.loads(raw) if isinstance(raw,str) else raw
                    if not isinstance(m,dict):m={}
                    yield t,k,m
def oi_events(paths,lo,hi):
    for t,k,m in raw_events(paths,lo,hi):
        r=m.get('result')
        if k=='rest_response' and isinstance(r,dict) and r.get('symbol')=='BTCUSD' and r.get('oi') is not None:
            try:
                x=float(r['oi'])
                if math.isfinite(x) and x>0:yield t,'oi',x
            except (ValueError,TypeError):pass
def lane_events(paths,lo,hi,lane):
    book=DeltaBook(); valid=False
    for t,k,m in raw_events(paths,lo,hi):
        if k in ('connection','disconnect','invalid_window'):
            book=DeltaBook();valid=False;yield t,lane,'gap',k;continue
        if k=='book_checkpoint' and not valid:
            cp=m.get('checkpoint',{})
            try:
                candidate=DeltaBook()
                candidate.apply(candidate.asks,cp['asks']);candidate.apply(candidate.bids,cp['bids'])
                candidate.seq=int(cp['sequence'])
                if not m.get('verified') or not candidate.asks or not candidate.bids or candidate.checksum()!=int(cp['crc32']) or max(map(float,candidate.bids))>=min(map(float,candidate.asks)):raise ValueError('bad checkpoint')
                book=candidate;valid=True
                yield t,lane,'checkpoint',book
            except (ValueError,KeyError,TypeError,BadBook):yield t,lane,'invalid','checkpoint'
            continue
        if k!='ws_raw':continue
        if m.get('type')=='ob_updates' and m.get('sy')=='BTCUSD':
            try:book.update(m);valid=True
            except BadBook as e:
                if valid:yield t,lane,'gap','book_invalid'
                book=DeltaBook();valid=False
                yield t,lane,'invalid',str(e).split(' previous=')[0];continue
            yield t,lane,'book',book
        elif m.get('type')=='trades' and m.get('sy')=='BTCUSD':
            yield t,lane,'trade',m
def merged(paths,backup,rest,lo,hi,stats):
    active=None;fresh={};vendor_floor=None;last_vendor=None
    o=((t,'rest','oi',m) for t,k,m in oi_events(rest,lo,hi))
    for t,lane,k,m in heapq.merge(lane_events(paths,lo,hi,'primary'),lane_events(backup,lo,hi,'backup'),o,key=lambda x:x[0]):
        if k=='oi':yield t,'oi',m;continue
        if k=='invalid':stats['invalid_'+lane]+=1;continue
        if k=='gap':
            fresh.pop(lane,None)
        elif k in ('book','checkpoint'):
            fresh[lane]=t;stats['verified_'+lane]+=1
        choice=next((l for l in ('primary','backup') if l in fresh and t-fresh[l]<=5*NS),None)
        if choice!=active:
            stats['lane_switches']+=1;active=choice
            yield t,'boundary','lane_switch'
        if lane!=active:continue
        if k=='trade':yield t,'trade',m
        elif k in ('book','checkpoint'):
            yield t,'book',m
def side(x,threshold):
    return (1 if x>=threshold else -1 if x<=-threshold else 0)
def walk(levels,slip,depth):
    left=1.; v=0.
    for p,q in levels:
        take=min(left,q*depth);v+=take*p;left-=take
        if left<=1e-9:return v+slip
    return None
class Sim:
    def __init__(self,name,latency,slip,depth,hold,persistence):
        self.hold=hold;self.persistence=persistence;self.signal_side=0;self.signal_since=None;self.name=name;self.latency=int(latency*NS);self.slip=slip;self.depth=depth
        self.pos=None;self.pending=None;self.cool=0;self.trades=[];self.unresolved=[];self.rejects=0;self.equity=100.;self.peak=100.;self.dd=0.
    def gap(self,t,reason):
        if self.pos:
            self.unresolved.append({'entry_ns':self.pos[0],'side':self.pos[1],'entry':self.pos[2],'reason':reason,'at_ns':t})
        self.pos=None;self.pending=None;self.cool=t+60*NS;self.signal_side=0;self.signal_since=None
    def price(self,d,b,a):return walk(a if d==1 else b,d*self.slip,self.depth)
    def step(self,t,b,a,signal):
        if self.pending and t>=self.pending[0]:
            due,d,why=self.pending;self.pending=None
            p=self.price(d,b,a)
            if p is None:
                self.rejects+=1
                if self.pos:self.gap(t,'exit_depth_unavailable')
            elif why=='entry':
                if p*LOT*(1+FEE)<=self.equity:
                    self.pos=(t,d,p)
                else:self.rejects+=1
            elif self.pos:
                et,ed,ep=self.pos;fee=(ep+p)*LOT*FEE;net=ed*(p-ep)*LOT-fee
                self.equity+=net;self.peak=max(self.peak,self.equity);self.dd=max(self.dd,(self.peak-self.equity)/self.peak)
                self.trades.append({'entry_ns':et,'exit_ns':t,'day':day(t),'side':ed,'entry':ep,'exit':p,'net':net,'fee':fee,'reason':why})
                self.pos=None;self.cool=t+30*NS
        # No modeled funding crossing: flatten well before any UTC hour boundary.
        # 1x, one contract, no exchange liquidation assumption.
        remain=28800-(t//NS)%28800
        if self.pos:
            et,d,ep=self.pos
            if t//(28800*NS)!=et//(28800*NS):
                self.gap(t,'funding_boundary_crossed');return
            p=b[0][0] if d==1 else a[0][0]; move=d*(p/ep-1)
            eq=self.equity+d*(p-ep)*LOT-(ep+p)*LOT*FEE
            self.dd=max(self.dd,(self.peak-eq)/self.peak)
            if not self.pending:
                why='stop' if move<=-.002 else 'target' if move>=.004 else 'timeout' if t-et>=self.hold*NS else 'funding_guard' if remain<=15 else None
                if why:self.pending=(t+self.latency,-d,why)
        elif signal is not None:
            if signal!=self.signal_side:
                self.signal_side=signal;self.signal_since=t
            if signal and self.signal_since is not None and t-self.signal_since>=self.persistence*NS and not self.pending and t>=self.cool and remain>self.hold+30 and (t//NS)%28800>15:
                self.pending=(t+self.latency,signal,'entry');self.signal_since=t
        if self.pos:self.signal_side=0;self.signal_since=None
    def report(self):
        ds=collections.defaultdict(float)
        for tr in self.trades:ds[tr['day']]+=tr['net']
        w=sum(t['net']>0 for t in self.trades);gp=sum(max(0,t['net']) for t in self.trades);gl=-sum(min(0,t['net']) for t in self.trades)
        return {'strategy':self.name,'hold_minutes':self.hold/60,'persistence_seconds':self.persistence,'latency_ms':self.latency/1e6,'extra_slip_points':self.slip,'depth_fraction':self.depth,'closed_trades':len(self.trades),'wins':w,'closed_net_usd':round(gp-gl,6),'fees_usd':round(sum(t['fee'] for t in self.trades),6),'pf_closed':gp/gl if gl else None,'observed_dd_pct':100*self.dd,'daily_closed_net':dict(ds),'unresolved_positions':len(self.unresolved),'rejected_orders':self.rejects,'complete_pnl':not self.unresolved}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--archive',type=Path,required=True);ap.add_argument('--start',required=True);ap.add_argument('--end',required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    lo,hi=stamp(args.start),stamp(args.end)
    paths=files(args.archive,'delta',lo,hi);backup=files(args.archive,'delta_backup',lo,hi);rest=files(args.archive,'delta_rest',lo,hi)
    if not paths:raise ValueError('no sealed primary data')
    sims=[Sim(n,.25,0,1,h,p) for n in NAMES for h in (300,900,1800,3600) for p in (0,10)]
    book=DeltaBook();last_book=None;last_eval=None;warm=None;prev_quote=None
    flow=collections.deque();prints=collections.deque();mids=collections.deque();oi=collections.deque()
    ofi=0.;abs_ofi=0.;signed=0.;volume=0.;stats=collections.Counter();days=collections.Counter()
    def reset(t,why):
        nonlocal book,last_book,last_eval,warm,prev_quote,ofi,abs_ofi,signed,volume
        for sim in sims:sim.gap(t,why)
        book=DeltaBook();last_book=last_eval=warm=prev_quote=None
        flow.clear();prints.clear();mids.clear();ofi=abs_ofi=signed=volume=0.
        stats['gap_'+why]+=1
    for t,k,m in merged(paths,backup,rest,lo,hi,stats):
        if k=='oi':
            oi.append((t,m))
            while len(oi)>1 and oi[1][0]<t-600*NS:oi.popleft()
            stats['oi_updates']+=1;continue
        if k=='boundary':
            reset(t,m);continue
        if k=='trade':
            role=m.get('r')
            try:q=float(m['s'])
            except (ValueError,KeyError,TypeError):stats['trade_bad_size']+=1;continue
            if role not in ('m','t') or not math.isfinite(q) or q<=0:
                stats['trade_unknown_side']+=1;continue
            stats['trade_valid_side']+=1
            if last_book is not None:
                x=q if role=='t' else -q;prints.append((t,x,q));signed+=x;volume+=q
            continue
        if k!='book':continue
        if last_book is not None and t-last_book>5*NS:reset(t,'book_silence')
        book=m
        if warm is None:warm=t
        last_book=t;stats['verified_book_messages']+=1
        # Book checksum has already sorted the ladder. Limit additional work to the top 10.
        b=[(float(p),float(q)) for p,q in heapq.nlargest(10,book.bids.items(),key=lambda x:float(x[0]))]
        a=[(float(p),float(q)) for p,q in heapq.nsmallest(10,book.asks.items(),key=lambda x:float(x[0]))]
        bp,bq=b[0];ap,aq=a[0];mid=(bp+ap)/2
        if prev_quote:
            pb,pbq,pa,paq=prev_quote
            e=(bq if bp>=pb else 0)-(pbq if bp<=pb else 0)-(aq if ap<=pa else 0)+(paq if ap>=pa else 0)
            flow.append((t,e,abs(e)));ofi+=e;abs_ofi+=abs(e)
        prev_quote=(bp,bq,ap,aq)
        for queue,window in ((flow,30),(prints,30)):
            while queue and queue[0][0]<t-window*NS:
                _,x,q=queue.popleft()
                if queue is flow:ofi-=x;abs_ofi-=q
                else:signed-=x;volume-=q
        sig={};evaluate=last_eval is None or t-last_eval>=NS
        if evaluate:
            last_eval=t;mids.append((t,mid))
            while len(mids)>1 and mids[1][0]<t-60*NS:mids.popleft()
            if t-warm>=60*NS and len(mids)>30:
                days[day(t)]+=1
                d=sum(q for _,q in b);s=sum(q for _,q in a)
                imbalance=(d-s)/(d+s)
                f=ofi/abs_ofi if abs_ofi>0 else 0
                cvd=signed/volume if volume>0 else 0
                ret=mid/mids[0][1]-1
                sig['OFI']=side(f,.35)
                sig['OBI']=side(imbalance,.6)
                sig['CVD_MOMENTUM']=side(cvd,.6) if volume>=10 and side(cvd,.6)==side(ret,.0003) else 0
                sig['ABSORPTION']=-side(cvd,.7) if volume>=10 and abs(ret)<=.0002 else 0
                past=[p for ts,p in mids if ts<t-5*NS]
                recent=[p for ts,p in mids if ts>=t-5*NS]
                if past and recent:
                    if min(recent)<min(past)*.9998 and mid>min(recent)*1.0002:sig['SWEEP_REVERSAL']=1
                    elif max(recent)>max(past)*1.0002 and mid<max(recent)*.9998:sig['SWEEP_REVERSAL']=-1
                if len(oi)>=2 and t-oi[-1][0]<=900*NS and oi[-1][0]-oi[0][0]>=300*NS:
                    change=oi[-1][1]/oi[0][1]-1
                    if change>=.002:sig['OI_MOMENTUM']=side(ret,.0005)
                if (ap-bp)/mid>.0002:sig={}
        for sim in sims:sim.step(t,b,a,sig.get(sim.name,0) if evaluate else None)
    for sim in sims:sim.gap(hi,'end_of_archive')
    args.output.mkdir(parents=True,exist_ok=True)
    result={'window':[args.start,args.end],'primary_only':False,'sealed_backup_files':len(backup),'sealed_primary_files':len(paths),'sealed_rest_files':len(rest),'stats':dict(stats),'eligible_evaluation_seconds_by_IST_day':dict(days),'settings':{'capital_usd':100,'one_lot_btc':LOT,'fee_per_side_incl_gst':FEE,'stop_pct':.2,'target_pct':.4,'max_hold_seconds':[300,900,1800,3600],'signal_min_interval_seconds':1,'funding':'assumed BTC eight-hour UTC funding boundaries; no position may cross; boundary-crossed positions unresolved','unresolved':'not counted as closed PnL; incomplete result if any','train_validation':'no fitting; Nov23-25 descriptive, Nov26-28 chronological check'},'results':[s.report() for s in sims]}
    (args.output/'summary.json').write_text(json.dumps(result,indent=2))
    for s in sims:
        (args.output/f'{s.name}_{s.hold}_{s.persistence}.json').write_text(json.dumps({'closed_trades':s.trades,'unresolved':s.unresolved}))
    print('ORDER_FLOW_SUMMARY',json.dumps(result),flush=True)
if __name__=='__main__':main()
