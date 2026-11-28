"""Round 4: five frozen independent microstructure hypotheses.
Research only, no parameter search, no candle indicators, no live execution.
"""
import argparse, collections, heapq, json, math, statistics
from pathlib import Path
from research_order_flow_v2 import NS, LOT, FEE, day, files, merged, stamp
from research_order_flow_v3 import Candidate

NAMES=('MICROPRICE_MOMENTUM','LIQUIDITY_VACUUM','TOUCH_REPLENISHMENT','CVD_DIVERGENCE','OI_UNWIND_REVERSAL')
RULES={
 'MICROPRICE_MOMENTUM':'30s mean normalized touch microprice displacement >= 0.25 with 60s mid return in same direction >= 0.03%',
 'LIQUIDITY_VACUUM':'top10 depth on breakout side <= half prior 5m median, mid breaks prior 60s extreme by >= 0.02%, aggressive trade imbalance confirms',
 'TOUCH_REPLENISHMENT':'30s same-price displayed addition >= 80% of depletion, depletion >= median historical touch size and opposite aggressive trade flow >= 30%',
 'CVD_DIVERGENCE':'two consecutive 5m windows; new price extreme by 0.02% while normalized signed trade volume diverges >= 0.2; latest 30s return reverses',
 'OI_UNWIND_REVERSAL':'OI falls >= 0.5% over observed 5-20m, preceding 5m price move >= 0.15%, last 60s return reverses >= 0.05%',
}
class Fixed(Candidate):
    def __init__(self,name,latency,slip,depth):
        super().__init__(0,0,False,.003,.006,latency,slip,depth)
        self.name=name;self.hold=1800
    def report(self):
        r=super().report()
        for key in ('window_seconds','threshold','price_confirmation','persistence_seconds'):r.pop(key,None)
        return r

def imbalance(s,v):return s/v if v>0 else 0.
def trim(q,t,seconds):
    while q and q[0][0]<t-seconds*NS:q.popleft()
def signals(rows,ois,t):
    out={n:0 for n in NAMES}
    cur=rows[-1];mid=cur[1];biddepth=cur[3];askdepth=cur[4]
    if len(rows)<120 or t-rows[0][0]<590*NS:return out
    def recent(sec):return [r for r in rows if r[0]>=t-sec*NS]
    r30=recent(30);r60=recent(60);r300=recent(300)
    prior60=[r for r in r60 if r[0]<t]
    prev300=[r for r in rows if t-600*NS<=r[0]<t-300*NS]
    prior300=[r for r in r300 if r[0]<t]
    if len(r30)<5 or len(prior60)<10 or len(prior300)<55 or len(prev300)<55:return out
    m30=statistics.mean(r[2] for r in r30)
    ret30=mid/r30[0][1]-1;ret60=mid/r60[0][1]-1
    if m30>=.25 and ret60>=.0003:out[NAMES[0]]=1
    elif m30<=-.25 and ret60<=-.0003:out[NAMES[0]]=-1
    s30=sum(r[5] for r in r30);v30=sum(r[6] for r in r30);f30=imbalance(s30,v30)
    if v30>=10:
        if askdepth<=.5*statistics.median(r[4] for r in prior300) and mid>=max(r[1] for r in prior60)*1.0002 and f30>=.3:out[NAMES[1]]=1
        elif biddepth<=.5*statistics.median(r[3] for r in prior300) and mid<=min(r[1] for r in prior60)*.9998 and f30<=-.3:out[NAMES[1]]=-1
        ba,bd,aa,ad=(sum(r[i] for r in r30) for i in (7,8,9,10))
        if bd>=max(1,statistics.median(r[11] for r in prior300)) and ba>=.8*bd and f30<=-.3 and ret30>=0:out[NAMES[2]]=1
        elif ad>=max(1,statistics.median(r[12] for r in prior300)) and aa>=.8*ad and f30>=.3 and ret30<=0:out[NAMES[2]]=-1
    cur_s=sum(r[5] for r in r300);cur_v=sum(r[6] for r in r300)
    old_s=sum(r[5] for r in prev300);old_v=sum(r[6] for r in prev300)
    if min(cur_v,old_v)>=100:
        f=imbalance(cur_s,cur_v);old=imbalance(old_s,old_v)
        if min(r[1] for r in r300)<=min(r[1] for r in prev300)*.9998 and f-old>=.2 and ret30>=.0002:out[NAMES[3]]=1
        elif max(r[1] for r in r300)>=max(r[1] for r in prev300)*1.0002 and old-f>=.2 and ret30<=-.0002:out[NAMES[3]]=-1
    if len(ois)>=2 and t-ois[-1][0]<=900*NS and 300*NS<=ois[-1][0]-ois[0][0]<=1200*NS:
        change=ois[-1][1]/ois[0][1]-1
        prior_move=r60[0][1]/r300[0][1]-1
        if change<=-.005:
            if prior_move<=-.0015 and ret60>=.0005:out[NAMES[4]]=1
            elif prior_move>=.0015 and ret60<=-.0005:out[NAMES[4]]=-1
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--archive',type=Path,required=True);ap.add_argument('--start',required=True);ap.add_argument('--end',required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    lo,hi=stamp(args.start),stamp(args.end)
    primary=files(args.archive,'delta',lo,hi);backup=files(args.archive,'delta_backup',lo,hi);rest=files(args.archive,'delta_rest',lo,hi)
    if not primary:raise ValueError('no sealed primary data')
    sims=[Fixed(n,l,s,d) for n in NAMES for l,s,d in ((.25,0,1),(.5,2,.5))]
    rows=collections.deque();ois=collections.deque();stats=collections.Counter();days=collections.Counter();signal_counts=collections.Counter()
    last=prev=last_eval=None;signed=vol=0.;replen=[0.]*4
    def reset(t,reason):
        nonlocal last,prev,last_eval,signed,vol,replen
        for sim in sims:sim.gap(t,reason)
        rows.clear();last=prev=last_eval=None;signed=vol=0.;replen=[0.]*4
        stats['boundaries']+=1
    for t,k,m in merged(primary,backup,rest,lo,hi,stats):
        if k=='boundary':reset(t,m);continue
        if k=='oi':
            ois.append((t,m));trim(ois,t,1200);stats['oi_updates']+=1;continue
        if k=='trade':
            if last is None:continue
            try:q=float(m['s']);role=m['r']
            except (ValueError,KeyError,TypeError):stats['bad_trade']+=1;continue
            if not math.isfinite(q) or q<=0 or role not in ('t','m'):stats['bad_trade']+=1;continue
            signed+=q if role=='t' else -q;vol+=q;stats['signed_trades']+=1;continue
        if k!='book':continue
        if last is not None and t-last>5*NS:reset(t,'book_silence')
        last=t
        b=[(float(p),float(q)) for p,q in heapq.nlargest(10,m.bids.items(),key=lambda x:float(x[0]))]
        a=[(float(p),float(q)) for p,q in heapq.nsmallest(10,m.asks.items(),key=lambda x:float(x[0]))]
        bp,bq=b[0];ap,aq=a[0];mid=(bp+ap)/2
        if prev:
            pb,pbq,pa,paq=prev
            if bp==pb:
                x=bq-pbq;replen[0]+=max(x,0);replen[1]+=max(-x,0)
            if ap==pa:
                x=aq-paq;replen[2]+=max(x,0);replen[3]+=max(-x,0)
        prev=(bp,bq,ap,aq)
        evaluate=last_eval is None or t-last_eval>=5*NS
        sig={}
        if evaluate:
            last_eval=t;days[day(t)]+=1
            # normalized microprice displacement equals touch quantity imbalance
            micro=(bq-aq)/(bq+aq) if bq+aq>0 else 0.
            rows.append((t,mid,micro,sum(q for _,q in b),sum(q for _,q in a),signed,vol,*replen,bq,aq))
            signed=vol=0.;replen=[0.]*4
            trim(rows,t,600);trim(ois,t,1200)
            if (ap-bp)/mid<=.0002:sig=signals(rows,ois,t)
            for n,d in sig.items():
                if d:signal_counts[n]+=1
        for sim in sims:
            if evaluate or sim.pos or sim.pending:sim.step(t,b,a,sig.get(sim.name,0) if evaluate else None)
    for sim in sims:sim.gap(hi,'end_of_archive')
    args.output.mkdir(parents=True,exist_ok=True)
    report={'window':[args.start,args.end],'files':[len(primary),len(backup),len(rest)],'stats':dict(stats),'evaluations_by_day':dict(days),'signal_counts':dict(signal_counts),'rules':RULES,'settings':{'capital_usd':100,'lot_btc':LOT,'fee_per_side_incl_gst':FEE,'stop_pct':.3,'target_pct':.6,'hold_minutes':30,'cooldown_seconds':300,'signal_interval_seconds':5,'funding':'hourly boundary avoidance; no funding cashflows simulated','scope':'fixed rules on previously examined week; not independent validation; no tuning; gap exposure unresolved, PnL incomplete when unresolved','proxies':'same-price visible replenishment not proven iceberg; OI decline not confirmed liquidation'},'results':[s.report() for s in sims]}
    (args.output/'summary.json').write_text(json.dumps(report,indent=2))
    for i,s in enumerate(sims):
        (args.output/f'candidate_{i:02d}.json').write_text(json.dumps({'config':s.report(),'closed_trades':s.trades,'unresolved':s.unresolved}))
    print('ORDER_FLOW_SUMMARY',json.dumps(report),flush=True)
if __name__=='__main__':main()
