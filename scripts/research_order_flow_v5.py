"""Round 5: four independent confirmation hypotheses and three exit ratios.
Exploratory on previously viewed data. No live execution or candle indicators.
"""
import argparse, collections, heapq, json, math, statistics
from pathlib import Path
from research_order_flow_v2 import NS, LOT, FEE, day, files, merged, stamp
from research_order_flow_v3 import Candidate

from research_order_flow_v4 import signals as baseline_signals

NAMES=('MICROPRICE_MOMENTUM','LIQUIDITY_VACUUM','CVD_DIVERGENCE','OI_UNWIND_REVERSAL')
RULES={
 'MICROPRICE_MOMENTUM':'Original microprice signal plus each of three consecutive 30s blocks has mean touch imbalance >= 0.25 in signal direction',
 'LIQUIDITY_VACUUM':'Original depth <= half prior 5m median and signed trade imbalance >= 0.30; replace fixed 0.02% breakout buffer by median absolute 60s return measured strictly before current evaluation',
 'CVD_DIVERGENCE':'Original CVD divergence plus break beyond all preceding 60s midquotes in reversal direction',
 'OI_UNWIND_REVERSAL':'Original OI unwind plus break beyond all preceding 30s midquotes in reversal direction',
}
class Fixed(Candidate):
    def __init__(self,name,target,latency,slip,depth):
        super().__init__(0,0,False,.003,target,latency,slip,depth)
        self.name=name;self.hold=3600
    def report(self):
        r=super().report()
        for key in ('window_seconds','threshold','price_confirmation','persistence_seconds'):r.pop(key,None)
        return r

def imbalance(s,v):return s/v if v>0 else 0.
def trim(q,t,seconds):
    while q and q[0][0]<t-seconds*NS:q.popleft()
def trim_signal_history(rows,t):
    # Retain the single observation at or before the 600s cutoff.
    # A count of 120 is not guaranteed by a >=5s event-driven evaluation cadence.
    cutoff=t-600*NS
    while len(rows)>1 and rows[1][0]<=cutoff:rows.popleft()

def signals(rows,ois,t,stats):
    # Use original frozen rules and identical history-readiness gate.
    before=stats['signal_evaluations_ready']
    base=baseline_signals(rows,ois,t,stats)
    out={n:0 for n in NAMES}
    if stats['signal_evaluations_ready']==before:return out
    for n in NAMES:
        if base[n]:stats['original_signal_'+n]+=1
    cur=rows[-1];mid=cur[1]
    r30=[r for r in rows if t-30*NS<=r[0]<t]
    r60=[r for r in rows if t-60*NS<=r[0]<t]
    r300=[r for r in rows if t-300*NS<=r[0]<t]
    d=base['MICROPRICE_MOMENTUM']
    if d:
        blocks=[[r[2] for r in rows if t-(i+1)*30*NS<r[0]<=t-i*30*NS] for i in range(3)]
        if all(len(b)>=5 and d*statistics.mean(b)>=.25 for b in blocks):out['MICROPRICE_MOMENTUM']=d
    d=base['CVD_DIVERGENCE']
    if d and ((d==1 and mid>max(r[1] for r in r60)) or (d==-1 and mid<min(r[1] for r in r60))):out['CVD_DIVERGENCE']=d
    d=base['OI_UNWIND_REVERSAL']
    if d and ((d==1 and mid>max(r[1] for r in r30)) or (d==-1 and mid<min(r[1] for r in r30))):out['OI_UNWIND_REVERSAL']=d
    # Estimate typical one-minute move using prior samples only, with as-of anchors.
    # No same-week percentile calibration or future values.
    past=[r for r in rows if r[0]<t];j=0;rets=[]
    for i,r in enumerate(past):
        if r[0]<t-300*NS:continue
        cutoff=r[0]-60*NS
        while j+1<i and past[j+1][0]<=cutoff:j+=1
        if past[j][0]<=cutoff and cutoff-past[j][0]<=10*NS:
            rets.append(abs(r[1]/past[j][1]-1))
    if len(rets)>=30:
        buf=statistics.median(rets)
        if buf>0:
            recent=[r for r in rows if r[0]>=t-30*NS]
            vol=sum(r[6] for r in recent);f=imbalance(sum(r[5] for r in recent),vol)
            if vol>=10:
                if cur[4]<=.5*statistics.median(r[4] for r in r300) and mid>=max(r[1] for r in r60)*(1+buf) and f>=.3:out['LIQUIDITY_VACUUM']=1
                elif cur[3]<=.5*statistics.median(r[3] for r in r300) and mid<=min(r[1] for r in r60)*(1-buf) and f<=-.3:out['LIQUIDITY_VACUUM']=-1
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--archive',type=Path,required=True);ap.add_argument('--start',required=True);ap.add_argument('--end',required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    lo,hi=stamp(args.start),stamp(args.end)
    primary=files(args.archive,'delta',lo,hi);backup=files(args.archive,'delta_backup',lo,hi);rest=files(args.archive,'delta_rest',lo,hi)
    if not primary:raise ValueError('no sealed primary data')
    sims=[Fixed(n,tp,l,s,d) for n in NAMES for tp in (.006,.009,.012) for l,s,d in ((.25,0,1),(.5,2,.5))]
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
            trim_signal_history(rows,t);trim(ois,t,1200)
            if (ap-bp)/mid<=.0002:sig=signals(rows,ois,t,stats)
            else:stats['spread_block']+=1
            for n,d in sig.items():
                if d:signal_counts[n]+=1
        for sim in sims:
            if evaluate or sim.pos or sim.pending:sim.step(t,b,a,sig.get(sim.name,0) if evaluate else None)
    for sim in sims:sim.gap(hi,'end_of_archive')
    args.output.mkdir(parents=True,exist_ok=True)
    report={'window':[args.start,args.end],'files':[len(primary),len(backup),len(rest)],'stats':dict(stats),'evaluations_by_day':dict(days),'signal_counts':dict(signal_counts),'rules':RULES,'settings':{'capital_usd':100,'lot_btc':LOT,'fee_per_side_incl_gst':FEE,'stop_pct':.3,'target_pct':[.6,.9,1.2],'hold_minutes':60,'cooldown_seconds':300,'signal_interval_seconds':5,'funding':'hourly boundary avoidance; no funding cashflows simulated','scope':'precommitted exploratory hypotheses on previously examined week; not independent validation; gap exposure unresolved, PnL incomplete when unresolved','proxies':'same-price visible replenishment not proven iceberg; OI decline not confirmed liquidation'},'results':[s.report() for s in sims]}
    if not stats['signal_evaluations_ready']:
        raise RuntimeError('No eligible signal evaluations; coverage diagnostics: '+json.dumps(dict(stats)))
    (args.output/'summary.json').write_text(json.dumps(report,indent=2))
    for i,s in enumerate(sims):
        (args.output/f'candidate_{i:02d}.json').write_text(json.dumps({'config':s.report(),'closed_trades':s.trades,'unresolved':s.unresolved}))
    print('ORDER_FLOW_SUMMARY',json.dumps(report),flush=True)
if __name__=='__main__':main()
