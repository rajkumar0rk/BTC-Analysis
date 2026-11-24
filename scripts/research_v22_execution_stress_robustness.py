#!/usr/bin/env python3
"""Execution-aware development search. No trade ledger inputs.
All entry gates use completed candles or current observable open quote.
All portfolio decisions use realized state; candidate exits are precomputed
only for speed. Frozen original files remain untouched. No forward claim."""
import json,itertools,hashlib
from pathlib import Path
from collections import defaultdict
import numpy as np
import pandas as pd
from numba import njit
import validate_frozen_high_leverage as audit
OUT=Path("analysis/v22_execution_stress_robustness")
OUT.mkdir(parents=True,exist_ok=True)
FEE=.00059
MMR=.0025
# scenario: name, cash cost, entry slip, exit slip, entry delay, fee, mmr,
# adverse mark shock, stop delay. Exact same stress definitions as frozen audit.
BASE=[("baseline_"+str(c),c,5.,5.,0,FEE,MMR,0.,0) for c in (0,10,25,50,60,75,100,125,150,175,200)]
STRESS=[
("actual_fill_10_each",0,10.,10.,0,FEE,MMR,0.,0),
("actual_fill_25_each",0,25.,25.,0,FEE,MMR,0.,0),
("actual_fill_50_each",0,50.,50.,0,FEE,MMR,0.,0),
("actual_fill_100_each",0,100.,100.,0,FEE,MMR,0.,0),
("cost200_fill25_each",200,25.,25.,0,FEE,MMR,0.,0),
("cost200_entry_delay1m",200,5.,5.,1,FEE,MMR,0.,0),
("cost200_entry_delay2m",200,5.,5.,2,FEE,MMR,0.,0),
("cost200_stop_delay1m",200,5.,5.,0,FEE,MMR,0.,1),
("cost200_mark_shock25",200,5.,5.,0,FEE,MMR,25.,0),
("cost200_mark_shock50",200,5.,5.,0,FEE,MMR,50.,0),
("cost200_mmr_0p30pct",200,5.,5.,0,FEE,.003,0.,0),
("cost200_mmr_0p35pct",200,5.,5.,0,FEE,.0035,0.,0),
("cost200_fee_0p07pct",200,5.,5.,0,.0007,MMR,0.,0),
("combined",200,25.,25.,1,FEE,.003,25.,0)]
ALL=BASE+STRESS
# Search anchor subset, final ranking uses every exact stress scenario and
# both funding modes. Extra 250 cost reported but not a required pass.
ANCHOR=[BASE[0],BASE[-1]]+[STRESS[i] for i in (0,3,4,6,7,9,11,13)]
EXTRA=[("baseline_250",250,5.,5.,0,FEE,MMR,0.,0)]
# Each row: j,x,net_before_extra_cost,cycle,side,entry,exit,liq,
# funding in prior month, reason, minimum mark margin buffer, gate.
@njit
def raw_exit(a,first,last,op,hi,lo,cl,mo,mh,ml,rate,al,ash,sw,month,day,weekday,lev,sf,tp,cap,trail,es,xs,delay,fee,mmr,shock,sd,fmode,safety):
    out=np.zeros((len(a),11));n=0
    for i in range(len(a)):
        orig=int(a[i,0]);j=orig+delay;side=int(a[i,1]);cyc=int(a[i,3])
        if orig<first or j>=last or weekday[j]>=5 or day[j]!=day[orig]:continue
        ep=op[j]+side*es
        # Optional common order admission guard. Does not use the realized
        # scenario's slippage or future candle. Budget reserves 100 adverse
        # fill points, 50 mark shock, 0.35% maintenance and higher fee.
        # Guard is identical across scenarios; recomputed at delayed order.
        if safety>0:
            ref=op[j]+side*100.
            prior=mo[j] # opening mark quote observable at order time
            buffer=ref/lev-.0007*ref+side*(prior-ref)-.0035*prior-50.
            # Prior minute ranges only. At 200x this guard may legitimately
            # reject most orders; do not report no-trade as a pass.
            width=max(mh[j-1]-ml[j-1],mh[j-2]-ml[j-2])
            if buffer<=safety*width:continue
        distance=ep*(1./lev-FEE-MMR)/(1.-side*MMR)
        stop=ep-side*distance*sf;target=ep*(1+side*tp/100.)
        fund=early=0.;best=ep;reason=3;trigger=-1
        x=min(j+cap-1,last-1);xp=cl[x]-side*xs;bufmin=1e30
        for k in range(j,x+1):
            if k>j and (k<sw or k%480==0):
                r=rate[k] if fmode==0 else (al[k] if side==1 else ash[k])
                f=-side*mo[k]*r/(480. if k<sw else 1.)
                fund+=f
                if month[k]==month[j]:early+=f
            adverse=(ml[k] if side==1 else mh[k])-side*shock
            buf=ep/lev+fund-fee*ep+side*(adverse-ep)-mmr*adverse
            bufmin=min(bufmin,buf)
            if buf<=0:
                x=k;xp=adverse-side*xs;reason=4;break
            if trigger>=0:
                if k>=trigger+sd:
                    x=k;xp=(lo[k] if side==1 else hi[k])-side*xs;reason=1;break
                continue
            if side*(adverse-stop)<=0:
                if sd:trigger=k;continue
                x=k;xp=(lo[k] if side==1 else hi[k])-side*xs;reason=1;break
            if (lo[k]<=stop if side==1 else hi[k]>=stop):
                if sd:trigger=k;continue
                x=k;xp=(min(op[k],stop) if side==1 else max(op[k],stop))-side*xs;reason=1;break
            if (hi[k]>=target if side==1 else lo[k]<=target):
                x=k;xp=target-side*xs;reason=2;break
            if trail>0:
                best=max(best,hi[k]) if side==1 else min(best,lo[k])
                if side*(best-ep)>=ep*.002:
                    new=best-side*distance*trail
                    stop=max(stop,new) if side==1 else min(stop,new)
        net=(-ep/lev-fee*ep if reason==4 else side*(xp-ep)-fee*(ep+xp)+fund)
        out[n,0]=j;out[n,1]=x;out[n,2]=net;out[n,3]=cyc
        out[n,4]=side;out[n,5]=ep;out[n,6]=xp;out[n,7]=int(reason==4)
        out[n,8]=early if month[x]!=month[j] else 0.
        out[n,9]=reason;out[n,10]=bufmin;n+=1
    return out[:n]
@njit
def replay(a,month,day,cost,ceil,lim,loss):
    v=np.zeros(23);pos=-1;used=set();lastday=-1;today=0
    n=w=lq=0;eq=peak=dd=0.;minbuf=1e30
    ids=np.empty(len(a),np.int64)
    for i in range(len(a)):
        j=int(a[i,0]);x=int(a[i,1]);cyc=int(a[i,3]);m=month[j];d=day[j]
        if j<=pos or (cyc>0 and cyc in used):continue
        if d!=lastday:lastday=d;today=0
        if lim and today>=lim:continue
        if v[m]>=ceil or v[m]<=-loss or v[m]>=a[i,11]:continue
        pos=x;today+=1
        if cyc>0:used.add(cyc)
        net=a[i,2]-cost;prior=a[i,8];v[m]+=prior;v[month[x]]+=net-prior
        eq+=net;peak=max(peak,eq);dd=max(dd,peak-eq)
        ids[n]=i;n+=1;w+=net>0;lq+=int(a[i,7]);minbuf=min(minbuf,a[i,10])
    return v,eq,dd,n,w,lq,minbuf,ids[:n]
def sorted_pack(rows,gate):
    return np.column_stack((rows,np.full(len(rows),gate)))
def merge(parts):
    a=np.concatenate(parts);return a[np.argsort(a[:,0],kind="stable")]
def main():
    summaries=[];monthly=[];profiles=[];baseline=[]
    for f in audit.FROZEN:
        lev=f["leverage"];p=f["profile"];ctx=audit.load_context(f["source"],lev)
        # Original context exactly preserves frozen signal and cycle IDs.
        groups=ctx["data_groups"];masks=dict(ctx["masks2"])
        month=ctx["month"];day=ctx["day"];te=ctx["train_end"];end=ctx["end"]
        core={q["group"]:q for q in p["legs"]}
        args=tuple(ctx[x] for x in ("op","hi","lo","cl","mo","mh","ml","rate","adverse_long","adverse_short","sw","month","day","weekday"))
        cutoff=(1./lev-FEE-MMR)*100
        # New gates based only on completed range/basis and market direction.
        for q in (.15,.25,.4,.6,.8,1.):
            masks[f"robust_quiet_{q}"]=lambda a,q=q:(a[:,11]<=cutoff*q)&(a[:,13]<=cutoff*.15)
            masks[f"robust_mean_{q}"]=lambda a,q=q:(a[:,12]<=cutoff*q)&(a[:,13]<=cutoff*.15)
            masks[f"robust_long_{q}"]=lambda a,q=q:(a[:,1]==1)&(a[:,12]<=cutoff*q)&(a[:,13]<=cutoff*.2)
            masks[f"robust_short_{q}"]=lambda a,q=q:(a[:,1]==-1)&(a[:,12]<=cutoff*q)&(a[:,13]<=cutoff*.2)
        # candidate key: (signal group, filter, stop fraction, target %, cap,
        # trail fraction, order safety multiplier). No per-date exclusions.
        def key(q):return (q["group"],q["filter"],q["stop_fraction"],q["tp_pct"],q["max_minutes"],q["trail_fraction"],0.)
        seed=[(key(q),q["mtd_gate"]) for q in p["legs"]]
        seedpar=(p["month_ceiling"],p["daily_limit"],p["loss_guard"])
        count=0
        def candidate(k,scenarios=ANCHOR,modes=(1,)):
            name,label,sf,tp,cap,trail,safety=k
            a=groups[name];a=a[masks[label](a)]
            aa=[]
            for mode in modes:
                for sc in scenarios:
                    _,cost,es,xs,delay,fee,mmr,shock,sd=sc
                    # Continuous replay: all months incl. known November.
                    # No artificial end-October close or state reset.
                    raw=raw_exit(a,0,end,*args,lev,sf,tp,int(cap),trail,es,xs,delay,fee,mmr,shock,sd,mode,safety)
                    aa.append(raw)
            return aa
        costs=[s[1] for s in ANCHOR]
        def rank(rr):
            v=np.stack([r[0] for r in rr]);counts=(v>=1000).sum(axis=1)
            lq=sum(r[5] for r in rr);worstliq=max(r[5] for r in rr)
            # Avoid an empty strategy being ranked as robust.
            mintr=min(r[3] for r in rr)
            deficit=np.maximum(1000-v,0).sum()
            return (int(lq==0 and mintr>=23),int(mintr>=23),int(lq==0),int(counts.min()),int(counts.sum()),-int(worstliq),-int(lq),float(v.min()),-float(deficit),min(float(r[1]) for r in rr),-max(float(r[2]) for r in rr))
        def evaluate(legs,arrays,par,cs=costs):
            nonlocal count
            rr=[replay(a,month,day,float(c),float(par[0]),int(par[1]),float(par[2])) for a,c in zip(arrays,cs)]
            count+=len(rr)
            return (rank(rr),legs,arrays,par)
        def packed(legs,cache):
            return [merge([sorted_pack(cache[k][i],g) for k,g in legs]) for i in range(len(next(iter(cache.values()))))]
        def keep(rows,n):
            # Deduplicate identical configurations to maintain search diversity.
            seen=set();out=[]
            for z in sorted(rows,key=lambda z:z[0],reverse=True):
                tag=(tuple(z[1]),z[3])
                if tag in seen:continue
                seen.add(tag);out.append(z)
                if len(out)>=n:break
            return out
        cache={k:candidate(k) for k,g in seed}
        initial=evaluate(seed,packed(seed,cache),seedpar)
        print("REFERENCE",lev,initial[0],flush=True)
        # Verify baseline continuous at cost200 vs independent frozen audit.
        ii=1;ref=audit.independent(ctx,p,audit.signals(ctx,p),0,end,200,1)
        check=replay(initial[2][ii],month,day,200.,*seedpar)
        assert abs(check[1]-ref["net"])<1e-6 and check[3]==len(ref["trades"]) and check[5]==ref["liq"],(lev,check[1],ref["net"])
        # Candidate search: bounded signal families from frozen sources; add
        # top raw candidates per family rather than selecting specific trades.
        selected_names=list(core)
        extra=[n for n in groups if n not in core and (("squeeze" in n or "sweep" in n or "quiet" in n or "Donchian" in n or "RSI" in n) and len(groups[n])>=25)]
        # Deterministic family diversity, favor less frequent signals.
        extra.sort(key=lambda n:(len(groups[n]),n))
        selected_names+=extra[:40]
        pool=[];neighbors=defaultdict(list)
        for name in selected_names:
            arr=groups[name];q=core.get(name)
            labels=list(dict.fromkeys(([q["filter"]] if q else [])+["all","H4_align","short_ADX25","long_ADX25","range_ADX20","quiet20_0.5","quiet20_h4","robust_quiet_0.25","robust_quiet_0.6","robust_mean_0.25","robust_mean_0.6","robust_short_0.6","robust_long_0.6"]))
            labels=[l for l in labels if l in masks and masks[l](arr).sum()>=12]
            specs=[(.15,2.,720,0.),(.3,3.,1440,0.),(.5,4.,4320,0.),(.7,6.,4320,0.),(.3,6.,4320,0.),(.5,2.,1440,0.)]
            if q:
                sf,tp,cap,tr=q["stop_fraction"],q["tp_pct"],q["max_minutes"],q["trail_fraction"]
                specs+= [(sf,tp,cap,tr)]+[(x,tp,cap,tr) for x in (.08,.12,.2,.3,.4,.5,.65,.8)]+[(sf,x,cap,tr) for x in (1.,2.,3.,4.,6.,8.)]+[(sf,tp,x,tr) for x in (180,720,1440,2880,4320)]
            specs=list(dict.fromkeys(specs))
            local=[];near=[]
            for l in labels:
                for sf,tp,cap,tr in specs:
                    for safety in (0.,.5,1.):
                        k=(name,l,sf,tp,cap,tr,safety)
                        aa=cache.get(k)
                        if aa is None:aa=candidate(k)
                        rr=[replay(sorted_pack(a,1e30),month,day,float(c),1e30,1,1e30) for a,c in zip(aa,costs)]
                        count+=len(rr)
                        # Standalone candidate scores are selection only.
                        # Never reject an individual entry based on its exit.
                        if max(r[3] for r in rr)<8:continue
                        z=(rank(rr),k,aa)
                        local.append(z)
                        if q and l==q["filter"]:near.append(z)
                        if len(local)>30:local=sorted(local,key=lambda x:x[0],reverse=True)[:8]
                        if len(near)>30:near=sorted(near,key=lambda x:x[0],reverse=True)[:12]
            for z in sorted(local,key=lambda x:x[0],reverse=True)[:8]+sorted(near,key=lambda x:x[0],reverse=True)[:12]:
                cache[z[1]]=z[2];pool.append(z[1])
                if q:neighbors[name].append(z[1])
            print("POOL",lev,name,count,local[0][0] if local else None,flush=True)
        pool=list(dict.fromkeys(pool+list(cache)))
        # Start from frozen portfolio plus stress-resistant individual signals.
        beam=[initial]
        for k in pool:
            for ceiling in (1500.,2500.,4000.):
                beam.append(evaluate([(k,1e30)],[sorted_pack(a,1e30) for a in cache[k]],(ceiling,1,6000.)))
        beam=keep(beam,12);archive=keep(beam+[initial],35)
        # Fixed seed local replacements, removals, recovery add-ons. All
        # accepted trades execute chronologically at actual stressed prices.
        for epoch in range(4):
            nxt=[]
            for b in beam[:5]:
                legs=b[1];par=b[3]
                for i,(old,g) in enumerate(legs):
                    for k in neighbors.get(old[0],[]):
                        for gate in (g,0.,500.,1000.,1e30):
                            ll=legs.copy();ll[i]=(k,gate)
                            nxt.append(evaluate(ll,packed(ll,cache),par))
                            if len(nxt)>80:nxt=keep(nxt,20)
                    if len(legs)>1:
                        ll=legs[:i]+legs[i+1:]
                        nxt.append(evaluate(ll,packed(ll,cache),par))
                for ceiling,lim,loss in itertools.product((1000.,1500.,2000.,3000.,4000.),(0,1,2),(3000.,6000.,1e30)):
                    nxt.append(evaluate(legs,b[2],(ceiling,lim,loss)))
                    if len(nxt)>80:nxt=keep(nxt,20)
            beam=keep(beam+nxt,12)
            nxt=[]
            for b in beam[:4]:
                used={k[0] for k,g in b[1]}
                for k in pool:
                    if k[0] in used:continue
                    for gate in (0.,500.,1000.,1e30):
                        aa=[merge([a,sorted_pack(r,gate)]) for a,r in zip(b[2],cache[k])]
                        nxt.append(evaluate(b[1]+[(k,gate)],aa,b[3]))
                        if len(nxt)>100:nxt=keep(nxt,24)
            beam=keep(beam+nxt,12);archive=keep(archive+beam,40)
            print("BEAM",lev,epoch,count,beam[0][0],flush=True)
        # Full exact grid, signed and debit-only, with baseline frozen included.
        final=[]
        for b in keep(archive+beam,25)+[initial]:
            legs=b[1];par=b[3]
            fullcache={k:candidate(k,ALL,(0,1)) for k,g in legs}
            aa=packed(legs,fullcache)
            full=evaluate(legs,aa,par,[s[1] for s in ALL]*2)
            final.append(full)
        final.sort(key=lambda z:z[0],reverse=True)
        best=final[0];refresult=final[-1] # not necessarily seed; record seed explicitly
        # Baseline and selected evaluated on the same continuous exact grid.
        for tag,legs,par in (("frozen",seed,seedpar),("v22",best[1],best[3])):
            cs=ALL+EXTRA
            fc={k:candidate(k,cs,(0,1)) for k,g in legs}
            aa=packed(legs,fc)
            rr=[]
            for i,(mode,sc) in enumerate(itertools.product((0,1),cs)):
                name,cost,*_=sc
                r=replay(aa[i],month,day,float(cost),float(par[0]),int(par[1]),float(par[2]));count+=1
                v,net,dd,n,w,lq,buf,ids=r
                assert abs(v.sum()-net)<1e-5
                trades=aa[i][ids];assert np.all(trades[1:,0]>trades[:-1,1])
                summaries.append(dict(leverage=lev,profile=tag,scenario=name,funding_mode=mode,net_points=net,months_ge_1000=int((v[:22]>=1000).sum()),november_points=v[22],min_month_points=float(v[:22].min()),trades=n,wins=w,liquidations=lq,closed_dd_points=dd,min_mark_buffer_points=None if n==0 else buf,pass_target=bool(n and lq==0 and (v>=1000).all())))
                monthly.extend(dict(leverage=lev,profile=tag,scenario=name,funding_mode=mode,month=str(pd.Period("2025-01",freq="M")+j),net_points=v[j]) for j in range(23))
                if name!="baseline_250":rr.append(r)
            if tag=="v22":
                profiles.append(dict(leverage=lev,rank=list(rank(rr)),evaluations=count,legs=[dict(group=k[0],filter=k[1],stop_fraction=k[2],tp_pct=k[3],max_minutes=k[4],trail_fraction=k[5],entry_safety=k[6],mtd_gate=g) for k,g in legs],month_ceiling=par[0],daily_limit=par[1],loss_guard=par[2],all_stress_pass=bool(all(r[5]==0 and (r[0]>=1000).all() for r in rr))))
        print("SELECTED",lev,profiles[-1],flush=True)
        pd.DataFrame(summaries).to_csv(OUT/"summary.csv",index=False)
        pd.DataFrame(monthly).to_csv(OUT/"monthly.csv",index=False)
        (OUT/"quality.json").write_text(json.dumps(dict(profiles=profiles,required_scenarios=[s[0] for s in ALL],funding_modes=["signed_proxy","debit_only"],rank_definition="zero liquidation with >=23 trades each scenario, >=23 trades each scenario, zero liquidation, worst scenario months >=1000 incl Nov, total scenario hits, negative worst liquidation count, negative total liquidations, worst month, negative deficit, minimum net, negative max closed DD",data="continuous Jan2025–Nov17 2026 UTC, all previously examined",raw_trade_ledger_used=False,exact_exchange_liquidation=False,exact_funding_settlement=False,account_level=False,forward_validation=False),indent=2,default=float))
        del ctx,cache
if __name__=="__main__":main()
