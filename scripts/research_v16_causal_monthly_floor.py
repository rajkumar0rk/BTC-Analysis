#!/usr/bin/env python3
"""V16: raw candle entry/exit search, no historical trade-ledger inputs.

Candidate exits computed from actual OHLC independently of acceptance; the
chronological scheduler never consults an unaccepted trade's outcome. Costs
and optional month profit ceiling are applied to realized closed trades only.
All 22 months previously seen; this is in-sample research, NOT unseen evidence.
"""
from collections import defaultdict
from pathlib import Path
import itertools,json
import numpy as np
import pandas as pd
from numba import njit
import research_v14_chronological_candle_replay as v14

OUT=Path("analysis/v16_causal_monthly_floor")
OUT.mkdir(parents=True,exist_ok=True)
MONTHS=v14.MONTHS
COSTS=(0,10,25,50,60,75,100,125,150,175,200,225,250)
FEE=.00059
SLIP=5.
# all exits: stop first, gap-aware, only advance trail on completed minute.
# j, x, net, cycle, side, ep, xp, reason
@njit
def exits(jj,ss,mid,cyc,atr,op,hi,lo,cl,months,st15,st60,end,sl,tp,cap,typ,trail,sttf):
    n=len(jj); a=np.zeros((n,8),np.float64)
    for i in range(n):
        j=jj[i]; side=ss[i]; ep=mid[i]+side*SLIP
        risk=(atr[i]*sl if typ==1 else ep*sl/100.)
        stop=ep-side*risk; target=ep+side*(risk*tp if typ==1 else ep*tp/100.)
        peak=ep; x=min(j+cap-1,end-1); xm=cl[x]; reason=3
        for k in range(j,x+1):
            # Completed ST reversal exit before current minute high/low.
            if k>j and ((sttf==15 and k%15==0 and st15[k//15-1]!=-side) or
                         (sttf==60 and k%60==0 and st60[k//60-1]!=side)):
                x=k;xm=op[k];reason=4;break
            if (lo[k]<=stop if side==1 else hi[k]>=stop):
                x=k;xm=min(op[k],stop) if side==1 else max(op[k],stop)
                # If an intraminute breakout entry triggered above/below the open,
                # worst-case same-minute stop executes no better than stop.
                if k==j and mid[i]!=op[k]:xm=stop
                reason=1;break
            if (hi[k]>=target if side==1 else lo[k]<=target):
                x=k;xm=target;reason=2;break
            if trail>0:
                peak=max(peak,hi[k]) if side==1 else min(peak,lo[k])
                if side*(peak-ep)>=risk:
                    newstop=peak-side*trail*risk
                    stop=max(stop,newstop) if side==1 else min(stop,newstop)
        xp=xm-side*SLIP
        net=side*(xp-ep)-FEE*(ep+xp)
        a[i,0]=j;a[i,1]=x;a[i,2]=net;a[i,3]=cyc[i];a[i,4]=side;a[i,5]=ep;a[i,6]=xp;a[i,7]=reason
    return a

@njit
def schedule(a,month,cost,ceiling,daily_limit,day,dd_limit):
    vals=np.zeros(22); peak=0.;equity=0.;dd=0.;wins=0;n=0
    pos=-1;used=set();idx=np.empty(len(a),np.int64)
    lastday=-1;today=0;lossday=-1
    for i in range(len(a)):
        j=int(a[i,0]);x=int(a[i,1]);cyc=int(a[i,3]);m=month[j];d=day[j]
        if j<=pos or m<0 or m>=22 or (cyc>0 and cyc in used):continue
        if d!=lastday:lastday=d;today=0
        if daily_limit>0 and today>=daily_limit:continue
        if vals[m]>=ceiling or vals[m]<=-dd_limit:continue
        if a.shape[1]>8 and vals[m]>=a[i,8]:continue
        v=a[i,2]-cost
        # Only now execute the candidate: occupancy does not depend on its PnL.
        pos=x;today+=1
        if cyc>0:used.add(cyc)
        vals[month[x]]+=v;equity+=v;peak=max(peak,equity);dd=max(dd,peak-equity)
        idx[n]=i;n+=1
        if v>0:wins+=1
    return vals,equity,dd,n,wins,idx[:n]

def main():
    m,b,h,end=v14.load()
    events,st,trend,eh,fh=v14.make_signals(m,b,h,end)
    op=m.open.to_numpy(float);hi=m.high.to_numpy(float);lo=m.low.to_numpy(float);cl=m.close.to_numpy(float)
    ist=m.index.tz_convert("Asia/Kolkata")
    month=np.array([(t.year-2025)*12+t.month-1 for t in ist],np.int32)
    day=np.asarray(ist.strftime("%Y%m%d"),dtype=np.int32)
    weekday=ist.dayofweek.to_numpy()
    h=v14.shock.features(m)
    hc=h.close; he=h.ema20; ha=h.atr
    h4=h.resample("4h").agg(open=("open","first"),high=("high","max"),low=("low","min"),close=("close","last"))
    h4ema=h4.close.ewm(span=50,adjust=False,min_periods=50).mean()
    h4trend=np.sign(h4.close-h4ema).shift(1).reindex(h.index,method="ffill").fillna(0).to_numpy()
    h1trend=np.sign(h.ema20-h.ema50).shift(1).fillna(0).to_numpy()
    hvol=(h.volume/h.volume.shift(1).rolling(20).mean()).shift(1).to_numpy()
    hadx=h.adx.shift(1).to_numpy(); hatr=h.atr.shift(1).to_numpy()
    hslope=(100*(he-he.shift(4))/hc).shift(1).to_numpy()
    hratio=h.atr_ratio.shift(1).to_numpy()
    groups=defaultdict(dict);cycles={}
    def add(name,j,side,mid,cyc=None):
        if j>=end or j<60 or weekday[j]>=5 or month[j]<0:return
        k=j//60
        if not np.isfinite(hatr[k]) or hatr[k]<=0:return
        cid=0
        if cyc is not None:
            if cyc not in cycles:cycles[cyc]=len(cycles)+1
            cid=cycles[cyc]
        groups[name][(j,side)]=(j,side,mid,cid,hatr[k],h1trend[k]*side,h4trend[k]*side,hvol[k],hadx[k],hratio[k],hslope[k]*side)
    for j,rows in events.items():
        for e in rows:
            n=e["name"]
            if n in ("RSI_cross5_late","RSI_reversal_late","BB_recovery","EMA20_reclaim_late","EMA20_reclaim_recovery"):continue
            if n.startswith("EMA20_reclaim_"):
                n="EMA20_reclaim" if n!="EMA20_reclaim_short" else "EMA20_reclaim_gap"
            # Intraminute trigger confirmed only once its minute has closed.
            # Enter at the NEXT 1m open; never use pre-entry high or low.
            at=j+1 if "mid" in e else j
            if at<end:add(n,at,e["side"],op[at],e.get("cycle"))
    # Additional market-based trend/pullback signals; complete hour only.
    d=hc.diff(); gain=d.clip(lower=0).ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    loss=(-d.clip(upper=0)).ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    rsi=100*gain/(gain+loss).replace(0,np.nan)
    for n in (12,24,48,72):
        up=hc>h.high.shift(1).rolling(n).max();dn=hc<h.low.shift(1).rolling(n).min()
        for i in np.flatnonzero((up|dn).to_numpy()):
            j=(int(i)+1)*60
            if j<end:add(f"H1_Donchian{n}",j,1 if up.iat[i] else -1,op[j])
    for n in (20,50):
        e=hc.ewm(span=n,adjust=False,min_periods=n).mean()
        up=(h.low<=e)&(hc>e)&(hc>h.open)&(hc.shift(1)>e.shift(1))
        dn=(h.high>=e)&(hc<e)&(hc<h.open)&(hc.shift(1)<e.shift(1))
        for i in np.flatnonzero((up|dn).to_numpy()):
            j=(int(i)+1)*60
            if j<end:add(f"H1_EMA{n}_pullback",j,1 if up.iat[i] else -1,op[j])
    for lo_r,hi_r in ((30,70),(40,60)):
        up=(rsi.shift(1)<=lo_r)&(rsi>lo_r);dn=(rsi.shift(1)>=hi_r)&(rsi<hi_r)
        for i in np.flatnonzero((up|dn).to_numpy()):
            j=(int(i)+1)*60
            if j<end:add(f"H1_RSI{lo_r}_reversal",j,1 if up.iat[i] else -1,op[j])
    for n in (10,20,40):
        up=h4.close>h4.high.shift(1).rolling(n).max();dn=h4.close<h4.low.shift(1).rolling(n).min()
        for i in np.flatnonzero((up|dn).to_numpy()):
            j=int(m.index.searchsorted(h4.index[i]+pd.Timedelta(hours=4)))
            if j<end:add(f"H4_Donchian{n}",j,1 if up.iat[i] else -1,op[j])
    print("RAW_SIGNALS", {k:len(v) for k,v in groups.items()},flush=True)
    masks=(
        ("all",lambda a:np.ones(len(a),bool)),
        ("long",lambda a:a[:,1]==1),("short",lambda a:a[:,1]==-1),
        ("H1_align",lambda a:a[:,5]>0),("H4_align",lambda a:a[:,6]>0),
        ("both_align",lambda a:(a[:,5]>0)&(a[:,6]>0)),
        ("ADX20",lambda a:a[:,8]>=20),("ADX30",lambda a:a[:,8]>=30),
        ("H4_ADX20",lambda a:(a[:,6]>0)&(a[:,8]>=20)),
        ("H4_vol1p25",lambda a:(a[:,6]>0)&(a[:,7]>=1.25)),
        ("H4_ATR_expand",lambda a:(a[:,6]>0)&(a[:,9]>=1.15)),
        ("slope_ADX",lambda a:(a[:,10]>0)&(a[:,8]>=20)),
        ("range_ADX20",lambda a:a[:,8]<20),
        ("vol1p5",lambda a:a[:,7]>=1.5),
        ("H4_long",lambda a:(a[:,6]>0)&(a[:,1]==1)),
        ("H4_short",lambda a:(a[:,6]>0)&(a[:,1]==-1)),
        ("long_ADX25",lambda a:(a[:,1]==1)&(a[:,8]>=25)),
        ("short_ADX25",lambda a:(a[:,1]==-1)&(a[:,8]>=25)),
        *tuple((f"{side_name}_ADX{v}",lambda a,side=side,v=v:(a[:,1]==side)&(a[:,8]>=v)) for side_name,side in (("long",1),("short",-1)) for v in (15,18,22,28,32,35,40)),
        *tuple((f"ADX_between_{l}_{u}",lambda a,l=l,u=u:(a[:,8]>=l)&(a[:,8]<u)) for l,u in ((10,25),(15,30),(20,35),(25,40))),
        ("H4_not_aligned",lambda a:a[:,6]<=0),
        ("H1_not_aligned",lambda a:a[:,5]<=0),
        ("short_H1_align",lambda a:(a[:,1]==-1)&(a[:,5]>0)),
        ("long_H1_align",lambda a:(a[:,1]==1)&(a[:,5]>0)),
        ("vol_low",lambda a:a[:,7]<=.8),
        ("vol_mid",lambda a:(a[:,7]>=.8)&(a[:,7]<=1.5)),
        ("low_ATR_ratio",lambda a:a[:,9]<1),
        ("high_ATR_ratio",lambda a:a[:,9]>=1.4),
        ("long_slope",lambda a:(a[:,1]==1)&(a[:,10]>0)),
        ("short_slope",lambda a:(a[:,1]==-1)&(a[:,10]>0)),
    )
    # Percent stop/TP, ATR stop/target in R; optional next-minute trail.
    specs=[]
    for sl,tp in ((.5,1),(.75,1.5),(1,2),(1.5,3),(2,4),(2,6),(3,6),(3,.5),(1,.3),(.75,3),(.5,2),(1,3)):
        specs.append((sl,tp,4320,0,0.,0))
    for sl,tp,cap in itertools.product((1.,1.4,1.8,2.2,2.5),(2.,2.5,3.,3.5,4.),(1440,4320)):
        specs.append((sl,tp,cap,1,0.,0))
    for sl,tp,trailing in itertools.product((1.5,2.5),(3.,5.),(.75,1.5)):
        specs.append((sl,tp,4320,1,trailing,0))
    for sl,tp,cap in itertools.product((1.5,1.75,2.,2.25,2.5),(3.,3.5,4.,4.5,5.,6.),(2880,4320,5760)):
        spec=(sl,tp,cap,0,0.,0)
        if spec not in specs:specs.append(spec)
    # ST exits on original setups only, as separate candidates.
    records=[]; shortlist=[]; bygroup=defaultdict(list); weakbest=defaultdict(list); local=defaultdict(list); exact={}
    core={"H1_RSI30_reversal":("short_ADX25",(2,4,4320,0,0,0)), "Shock_Donchian":("long_ADX25",(1.8,3,1440,1,0,0)), "EMA20_ADX_reclaim":("all",(2,6,4320,0,0,0))}
    def score(vals,net,dd):
        # Joint target and downside, no calendar-month-specific gates.
        return (int(np.sum(vals>=1000)),float(np.min(vals)),float(net),-float(dd))
    def evalarr(a,cost=200,ceil=1e30,lim=0,loss=1e30):
        return schedule(a,month,float(cost),float(ceil),lim,day,float(loss))
    def record(name,mask,spec,a):
        vals,net,dd,n,w,_=evalarr(a)
        if n<16:return
        row=dict(group=name,filter=mask,exit_spec=str(spec),trades=n,wins=w,net_points=net,dd_points=dd,
                 months_ge_1pct=int(np.sum(vals>=1000)),positive_months=int(np.sum(vals>0)),min_month_points=float(np.min(vals)),
                 dec_points=float(vals[11]),net_2025=float(vals[:12].sum()),net_2026=float(vals[12:].sum()),months_2025=int(np.sum(vals[:12]>=1000)),months_2026=int(np.sum(vals[12:]>=1000)))
        records.append(row)
        q=(score(vals,net,dd),name,mask,spec,a,row)
        # Keep both strong month coverage and total net; cap memory per group.
        p=bygroup[name];p.append(q);p.sort(key=lambda v:v[0],reverse=True)
        if len(p)>16:p.pop()
        # Keep alternative market setups useful in the weakest historical regime.
        wp=weakbest[name];wp.append(q)
        # The ranking is an in-sample optimization objective, not an entry rule.
        wp.sort(key=lambda q:(q[5].get("dec_points",-1e30),q[0]),reverse=True)
        if len(wp)>10:wp.pop()
        if name in core:
            local[name].append(q)
            if (mask,spec)==core[name]:exact[name]=q
    for name,data in groups.items():
        a=np.array(sorted(data.values(),key=lambda x:x[0]),float)
        if len(a)<16:continue
        own=specs.copy() if name in ("H1_RSI30_reversal","Shock_Donchian","EMA20_ADX_reclaim") else specs[:40]
        if name in ("line_touch","bullish_flip","bearish_flip","confirm_long","confirm_short"):
            own+= [(sl,tp,4320,0,0.,15) for sl,tp in ((.75,1.5),(3,.5),(1,.3),(1,2),(1.5,3),(2,4))]
        if name.startswith("EMA20") or name=="H1_ST_flip_exit":
            own+= [(sl,tp,4320,0,0.,60) for sl,tp in ((1,2),(2,3),(2,5),(3,6))]
        for spec in own:
            arr=exits(a[:,0].astype(np.int64),a[:,1].astype(np.int64),a[:,2],a[:,3].astype(np.int64),a[:,4],op,hi,lo,cl,month,trend,eh,end,*spec)
            for label,fn in masks:
                mask=fn(a)
                if mask.sum()>=16:record(name,label,spec,arr[mask])
        print("GROUP",name,"candidates",len(records),"best",bygroup[name][0][5] if bygroup[name] else None,flush=True)
    df=pd.DataFrame(records).sort_values(["months_ge_1pct","min_month_points","net_points"],ascending=False)
    df.to_csv(OUT/"single_candidates.csv",index=False)
    # Chronological replays of candidate signal streams. Outcome only affects
    # state after the accepted trade has exited. No preselected trade ledger.
    def gated(a,threshold=1e30):
        return np.column_stack((a[:,:8],np.full(len(a),threshold)))
    def merge(a,b):
        x=np.concatenate((a,b))
        return x[np.argsort(x[:,0],kind="stable")]
    def pack(legs):
        a=np.concatenate([gated(q[4],threshold) for q,threshold in legs])
        return a[np.argsort(a[:,0],kind="stable")]
    primary=(0,50,100,150,200)
    full=tuple(c for c in COSTS if c<=200)
    portfolio_tests=0
    def evaluate(legs,a,ceil,lim,loss,costs=primary):
        nonlocal portfolio_tests
        checks=[evalarr(a,c,ceil,lim,loss) for c in costs]
        portfolio_tests+=len(costs)
        count=[int(np.sum(v[0]>=1000)) for v in checks]
        worst=min(float(v[0].min()) for v in checks)
        dec=min(float(v[0][11]) for v in checks)
        net=checks[-1][1];dd=checks[-1][2]
        # Rank by worst-case passing months, then total passing months, then
        # minimum monthly PnL and net. No special date in execution logic.
        rank=(min(count),sum(count),worst,net,-dd)
        return (rank,legs,a,ceil,lim,loss,dec)
    def keep(arr,n=30):
        arr.sort(key=lambda z:z[0],reverse=True); return arr[:n]
    if len(exact)!=3:raise RuntimeError("Missing V15 primary profiles")
    base_legs=[(exact[k],1e30) for k in core]
    a=pack(base_legs)
    base_eval=evaluate(base_legs,a,4000.,1,8000.,full)
    print("V15_CONSERVATIVE_REFERENCE",base_eval[0],flush=True)
    base_summary=[]
    for cost in COSTS:
        v,n,d,c,w,_=evalarr(a,cost,4000.,1,8000.)
        base_summary.append(dict(cost=cost,net_points=n,closed_dd_points=d,trades=c,wins=w,months_ge_1pct=int(np.sum(v>=1000)),min_month_points=float(v.min())))
    pd.DataFrame(base_summary).to_csv(OUT/"v15_conservative_reference.csv",index=False)
    # First find robust combinations near the three V15 components. Optimize
    # each component against the other two, not in isolation.
    current=[evaluate(base_legs,a,4000.,1,8000.)]
    all_candidates=current.copy()
    for epoch in range(2):
      for i,name in enumerate(core):
        nxt=[]
        for p in current[:6]:
            for q in local[name]:
                legs=p[1].copy();legs[i]=(q,1e30)
                a=pack(legs)
                nxt.append(evaluate(legs,a,p[3],p[4],p[5]))
                if len(nxt)>120:nxt=keep(nxt,24)
        current=keep(current+nxt,12)
        all_candidates=keep(all_candidates+current,35)
        print("LOCAL",epoch,name,portfolio_tests,current[0][0],flush=True)
    # Sweep common realized monthly ceiling and daily entry limits.
    nxt=[]
    for p in all_candidates[:25]:
        for ceil,lim,loss in itertools.product((1500.,2000.,2500.,3000.,3500.,4000.,4500.,5000.,6000.,8000.,1e30),(0,1,2),(4000.,6000.,8000.,1e30)):
            nxt.append(evaluate(p[1],p[2],ceil,lim,loss))
            if len(nxt)>150:nxt=keep(nxt,40)
    all_candidates=keep(all_candidates+nxt,40)
    print("GUARDS",portfolio_tests,all_candidates[0][0],flush=True)
    # Additional independent recovery sleeve only if actual MTD profit is
    # below a broad threshold. Test every signal chronologically; no future
    # position preservation or selected winning trades.
    pool=[]
    seen=set()
    for rows in list(bygroup.values())+list(weakbest.values()):
        for q in rows:
            key=(q[1],q[2],str(q[3]))
            if key not in seen:seen.add(key);pool.append(q)
    for depth in range(2):
        nxt=[]
        for p in all_candidates[:16]:
            used={q[1] for q,_ in p[1]}
            for q in pool:
                if q[1] in used:continue
                for threshold in (-1000.,0.,500.,1000.,1500.,1e30):
                    legs=p[1]+[(q,threshold)]
                    a=merge(p[2],gated(q[4],threshold))
                    # 200-point pre-screen; then evaluate other costs.
                    v,n,d,c,w,_=evalarr(a,200,p[3],p[4],p[5])
                    portfolio_tests+=1
                    if np.sum(v>=1000)<max(19,all_candidates[0][0][0]-1):continue
                    nxt.append(evaluate(legs,a,p[3],p[4],p[5]))
                    if len(nxt)>160:nxt=keep(nxt,40)
        all_candidates=keep(all_candidates+nxt,40)
        print("RECOVERY",depth,portfolio_tests,all_candidates[0][0],flush=True)
        if all_candidates[0][0][0]==22:break
    # Full 11-cost robustness re-rank. Further neighbors of the top candidate
    # are checked across every cost rather than just five anchor scenarios.
    finals=[]
    for p in all_candidates:
        for ceil,lim,loss in itertools.product((p[3],max(1000.,p[3]-500),p[3]+500),(p[4],1,2),(p[5],6000.,8000.)):
            finals.append(evaluate(p[1],p[2],ceil,lim,loss,full))
            if len(finals)>200:finals=keep(finals,50)
    finals=keep(finals,30)
    p=finals[0];rank,leg_pairs,a,ceil,lim,loss,_=p
    legs=[q for q,_ in leg_pairs]
    print("FULL_ROBUST",portfolio_tests,rank,flush=True)
    # Re-evaluate all 13 costs; outputs keep actual selected entry/exit fills.
    summary=[];monthly=[]
    for cost in COSTS:
        v,n,d,c,w,idx=evalarr(a,cost,ceil,lim,loss)
        t=a[idx];assert np.all(t[1:,0]>t[:-1,1]) and np.all(weekday[t[:,0].astype(int)]<5)
        assert abs(v.sum()-n)<1e-6
        summary.append(dict(cost=cost,net_points=n,closed_dd_points=d,trades=c,wins=w,months_ge_1pct=int(np.sum(v>=1000)),positive_months=int(np.sum(v>0)),min_month_points=float(v.min())))
        monthly.extend(dict(cost=cost,month=mo,net_points=val) for mo,val in zip(MONTHS,v))
        ledger=pd.DataFrame(dict(entry_utc=m.index[t[:,0].astype(int)],exit_utc=m.index[t[:,1].astype(int)],side=t[:,4].astype(int),entry_fill=t[:,5],exit_fill=t[:,6],net_points=t[:,2]-cost,reason=t[:,7].astype(int)))
        ledger.to_csv(OUT/f"trades_{cost}.csv",index=False)
    pd.DataFrame(summary).to_csv(OUT/"summary.csv",index=False)
    pd.DataFrame(monthly).to_csv(OUT/"monthly.csv",index=False)
    top=[dict(score=list(x[0]),legs=[dict(group=q[1],filter=q[2],exit_spec=list(q[3]),recovery_mtd_ceiling=threshold) for q,threshold in x[1]],ceiling=x[3],daily_limit=x[4],month_loss_guard=x[5]) for x in finals[:20]]
    report=dict(single_tests=len(records),portfolio_tests=portfolio_tests,groups=len(groups),raw_signals=sum(len(x) for x in groups.values()),candles=end,source="SHA-verified Delta BTCUSD 1m",result="PASS" if all(x["months_ge_1pct"]==22 for x in summary if x["cost"]<=200) else "FAIL",selected=top[0],top20=top,fee_per_side=FEE,slippage_per_side=SLIP,extra_cost_per_roundtrip=True,entry_weekdays="Mon-Fri IST",single_position=True,stop_first=True,trail_activation="next minute",trigger_fill="next minute open after confirmed intraminute trigger",funding="not modeled",liquidation="not modeled",unseen_holdout=False,trade_ledger_inputs=False,notes="All raw signals and independent OHLC fills regenerated. Scheduler never uses future PnL to accept or reject an entry. No named-month gates. In-sample optimization, not a claim of future profits.")
    (OUT/"quality.json").write_text(json.dumps(report,indent=2,default=float))
    print("RESULT",json.dumps(report,default=float),flush=True)
    print(pd.DataFrame(summary).to_string(index=False),flush=True)
if __name__=="__main__":main()
