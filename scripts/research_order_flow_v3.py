"""Exploratory OFI research: longer aggregation, confirmation and wider exits.
Uses V2 integrity-checked source-exclusive replay. No OHLC signals or live orders.
"""
import argparse, collections, heapq, json
from pathlib import Path
from research_order_flow_v2 import NS, LOT, FEE, Sim, day, files, merged, stamp, side

WINDOWS=(60,300,900)
THRESHOLDS=(.15,.30)
EXITS=((.003,.006),(.005,.010))
class Rolling:
    def __init__(self,window):
        self.window=window*NS;self.rows=collections.deque();self.total=0.;self.absolute=0.
    def add(self,t,e):
        self.rows.append((t,e));self.total+=e;self.absolute+=abs(e)
        while self.rows and self.rows[0][0]<t-self.window:
            _,x=self.rows.popleft();self.total-=x;self.absolute-=abs(x)
    def value(self):return self.total/self.absolute if self.absolute>1e-9 else 0.
class Candidate(Sim):
    def __init__(self,w,th,confirm,stop,target,latency=.25,slip=0,depth=1):
        super().__init__('OFI',latency,slip,depth,3600,0)
        self.w=w;self.th=th;self.confirm=confirm;self.stop=stop;self.target=target
    def gap(self,t,reason):
        # Keep gap-exposed entries in unresolved ledger. Never silently claim complete P&L.
        super().gap(t,reason)
    def step(self,t,b,a,signal):
        # Exit or entry only after simulated latency at later observed depth.
        # Conservative no-position rule around every UTC hour (funding timing not certified).
        remain=3600-(t//NS)%3600
        if self.pos and t//(3600*NS)!=self.pos[0]//(3600*NS):
            self.gap(t,'hour_boundary');return
        if self.pending and t>=self.pending[0]:
            due,d,why=self.pending;self.pending=None
            if why=='entry' and remain<=30:
                self.rejects+=1;return
            p=self.price(d,b,a)
            if p is None:
                self.rejects+=1
                if self.pos:self.gap(t,'exit_depth_unavailable')
            elif why=='entry':
                if p*LOT*(1+FEE)<=self.equity:self.pos=(t,d,p)
                else:self.rejects+=1;self.cool=t+300*NS
            elif self.pos:
                et,ed,ep=self.pos;fee=(ep+p)*LOT*FEE;net=ed*(p-ep)*LOT-fee
                self.equity+=net
                self.peak=max(self.peak,self.equity)
                self.dd=max(self.dd,(self.peak-self.equity)/self.peak)
                self.trades.append({'entry_ns':et,'exit_ns':t,'day':day(t),'side':ed,'entry':ep,'exit':p,'net':net,'fee':fee,'reason':why})
                self.pos=None;self.cool=t+300*NS
        if self.pos:
            et,d,ep=self.pos
            p=b[0][0] if d==1 else a[0][0];move=d*(p/ep-1)
            eq=self.equity+d*(p-ep)*LOT-(ep+p)*LOT*FEE
            self.peak=max(self.peak,eq);self.dd=max(self.dd,(self.peak-eq)/self.peak)
            if not self.pending:
                why='stop' if move<=-self.stop else 'target' if move>=self.target else 'timeout' if t-et>=self.hold*NS else 'hour_guard' if remain<=15 else None
                if why:self.pending=(t+self.latency,-d,why)
        elif signal is not None and signal and not self.pending and t>=self.cool and remain>300 and (t//NS)%3600>15:
            self.pending=(t+self.latency,signal,'entry')
    def report(self):
        r=super().report();r.update(window_seconds=self.w,threshold=self.th,price_confirmation=self.confirm,stop_pct=self.stop*100,target_pct=self.target*100,gross_closed_usd=round(sum(x['net']+x['fee'] for x in self.trades),6))
        return r
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--archive',type=Path,required=True);ap.add_argument('--start',required=True);ap.add_argument('--end',required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    lo,hi=stamp(args.start),stamp(args.end)
    primary=files(args.archive,'delta',lo,hi);backup=files(args.archive,'delta_backup',lo,hi)
    if not primary:raise ValueError('no primary sealed data')
    # 24 research candidates x 2 execution scenarios; thresholds chosen before run.
    sims=[Candidate(w,th,c,sl,tp,l,s,d) for w in WINDOWS for th in THRESHOLDS for c in (False,True) for sl,tp in EXITS for l,s,d in ((.25,0,1),(.5,2,.5))]
    stats=collections.Counter();days=collections.Counter()
    rolls={w:Rolling(w) for w in WINDOWS};price={w:collections.deque() for w in WINDOWS};prev=None;warm=None;last=None;last_eval=None
    def reset(t,reason):
        nonlocal rolls,price,prev,warm,last,last_eval
        for sim in sims:sim.gap(t,reason)
        rolls={w:Rolling(w) for w in WINDOWS};price={w:collections.deque() for w in WINDOWS}
        prev=warm=last=last_eval=None;stats['boundaries']+=1
    for t,k,m in merged(primary,backup,[],lo,hi,stats):
        if k=='boundary':reset(t,m);continue
        if k!='book':continue
        if last is not None and t-last>5*NS:reset(t,'book_silence')
        last=t
        if warm is None:warm=t
        b=[(float(p),float(q)) for p,q in heapq.nlargest(10,m.bids.items(),key=lambda x:float(x[0]))]
        a=[(float(p),float(q)) for p,q in heapq.nsmallest(10,m.asks.items(),key=lambda x:float(x[0]))]
        bp,bq=b[0];ap,aq=a[0];mid=(bp+ap)/2
        if prev is not None:
            pb,pbq,pa,paq=prev
            e=(bq if bp>=pb else 0)-(pbq if bp<=pb else 0)-(aq if ap<=pa else 0)+(paq if ap>=pa else 0)
            for r in rolls.values():r.add(t,e)
        prev=(bp,bq,ap,aq)
        evaluate=last_eval is None or t-last_eval>=5*NS
        ready={}
        if evaluate:
            last_eval=t;days[day(t)]+=1
            for w in WINDOWS:
                q=price[w];q.append((t,mid))
                while len(q)>1 and q[1][0]<=t-w*NS:q.popleft()
                if t-warm>=w*NS and (ap-bp)/mid<=.0002:
                    ready[w]=(rolls[w].value(),mid/q[0][1]-1)
        for sim in sims:
            signal=None
            if evaluate:
                f,r=ready.get(sim.w,(0,0));signal=side(f,sim.th)
                if sim.confirm and signal!=side(r,.0005):signal=0
            if evaluate or sim.pos or sim.pending:sim.step(t,b,a,signal)
    for sim in sims:sim.gap(hi,'end_of_archive')
    args.output.mkdir(parents=True,exist_ok=True)
    result={'window':[args.start,args.end],'primary_files':len(primary),'backup_files':len(backup),'stats':dict(stats),'evaluations_by_day':dict(days),'settings':{'capital_usd':100,'lot_btc':LOT,'fee_per_side_incl_gst':FEE,'signal_interval_seconds':5,'cooldown_seconds':300,'max_hold_seconds':3600,'funding':'avoid all UTC hour boundaries; no funding cashflows simulated','scope':'same-week exploratory grid; no independent validation; incomplete P&L if unresolved'},'results':[s.report() for s in sims]}
    (args.output/'summary.json').write_text(json.dumps(result,indent=2))
    for i,s in enumerate(sims):
        (args.output/f'candidate_{i:02d}.json').write_text(json.dumps({'config':s.report(),'closed_trades':s.trades,'unresolved':s.unresolved}))
    print('ORDER_FLOW_SUMMARY',json.dumps(result),flush=True)
if __name__=='__main__':main()
