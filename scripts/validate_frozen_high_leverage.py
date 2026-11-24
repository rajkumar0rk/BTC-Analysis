#!/usr/bin/env python3
"""Independent on-demand replay. Signal generation reused verbatim from
each source version, but no precomputed candidate exits or trade-ledger input.
Reference ledger is read only AFTER simulated trades for parity comparison.
No optimization. All historical periods previously examined."""
import importlib,inspect,json,hashlib
from pathlib import Path
import numpy as np
import pandas as pd
OUT=Path("analysis/frozen_high_leverage_validation")
FROZEN=json.loads((OUT/"frozen_profiles.json").read_text())
COSTS=(0,10,25,50,60,75,100,125,150,175,200,225,250)
FEE=.00059
MMR=.0025
SUMMARY=[];MONTHLY=[];PARITY=[];TRADES=[];PREFIX=[]
def load_context(source,lev,cutoff=None):
    mod=importlib.import_module("research_"+source)
    # Use original feature and mask definitions unchanged. Cut before
    # candidate execution/search; source versions remain intact.
    src=inspect.getsource(mod.main)
    prefix=src[:src.index("        # Candidate tuple:")]
    if cutoff:
        prefix=prefix.replace('m=m.loc[:"2026-11-17 23:59:00"].copy()',f'm=m.loc[:"{cutoff}"].copy()')
    ns=vars(mod).copy();ns["LEVS"]=(lev,)
    exec(compile(prefix+"        return locals()\n","frozen_signals_"+source,"exec"),ns)
    return ns["main"]()
def signals(ctx,p):
    rows=[];groups=ctx["data_groups"];filters=ctx["masks2"]
    for i,q in enumerate(p["legs"]):
        a=groups[q["group"]];a=a[filters[q["filter"]](a)]
        for r in a:rows.append((int(r[0]),int(r[1]),int(r[3]),i))
    return sorted(rows,key=lambda x:x[0])
def independent(ctx,p,events,first,last,cost=200,mode=0,entry_slip=5.,exit_slip=5.,delay=0,fee=FEE,mmr=MMR,mark_shock=0.,stop_delay=0):
    op,hi,lo,cl,mo,mh,ml,mc,rate,al,ash,sw,month,day,weekday=(ctx[x] for x in ("op","hi","lo","cl","mo","mh","ml","mc","rate","adverse_long","adverse_short","sw","month","day","weekday"))
    lev=p["leverage"];legs=p["legs"];v=np.zeros(23);trades=[];used=set()
    occupied=-1;lastday=-1;today=0;eq=peak=dd=0.;lq=0
    minbuf=float("inf");minbuf_pct=float("inf");minliq_dist=float("inf")
    mtm_peak=0.;mtm_dd=0.;day_peak=0.;day_dd=0.;mtm_day=-1;last_marked=0.
    # Include adverse/favorable mark extremes, even if exit occurs inside bar.
    # This deliberately overbounds unknown intraminute order and time exposed.
    def mark_equity(k,adverse,favorable,close):
        nonlocal mtm_peak,mtm_dd,day_peak,day_dd,mtm_day,last_marked
        d=int(day[k])
        if d!=mtm_day:mtm_day=d;day_peak=last_marked
        mtm_peak=max(mtm_peak,favorable);day_peak=max(day_peak,favorable)
        mtm_dd=max(mtm_dd,mtm_peak-adverse);day_dd=max(day_dd,day_peak-adverse)
        last_marked=close
    for original,side,cyc,leg in events:
        j=original+delay
        if original<first or j>=last or j<=occupied or weekday[j]>=5 or day[j]!=day[original] or (cyc>0 and cyc in used):continue
        q=legs[leg];m=int(month[j]);d=int(day[j])
        if d!=lastday:today=0;lastday=d
        if p["daily_limit"] and today>=p["daily_limit"]:continue
        if v[m]>=p["month_ceiling"] or v[m]<=-p["loss_guard"] or v[m]>=q["mtd_gate"]:continue
        today+=1
        if cyc>0:used.add(cyc)
        ep=op[j]+side*entry_slip
        distance=ep*(1./lev-FEE-MMR)/(1.-side*MMR)
        stop=ep-side*distance*q["stop_fraction"];target=ep*(1+side*q["tp_pct"]/100.)
        fund=0.;best=ep;reason=3;trigger=-1
        x=min(j+q["max_minutes"]-1,last-1);xp=cl[x]-side*exit_slip
        earlyfund=0.
        for k in range(j,x+1):
            if k>j and (k<sw or k%480==0):
                r=rate[k] if mode==0 else (al[k] if side==1 else ash[k])
                f=-side*mo[k]*r/(480. if k<sw else 1.)
                fund+=f
                if month[k]==m:earlyfund+=f
            adverse=(ml[k] if side==1 else mh[k])-side*mark_shock
            favorable=mh[k] if side==1 else ml[k]
            buffer=ep/lev+fund-fee*ep+side*(adverse-ep)-mmr*adverse
            minbuf=min(minbuf,buffer);minbuf_pct=min(minbuf_pct,100*buffer/ep)
            minliq_dist=min(minliq_dist,buffer/(1.-side*mmr))
            def marked(price):
                fill=price-side*exit_slip
                return eq+fund+side*(fill-ep)-fee*(ep+fill)-cost
            mark_equity(k,marked(adverse),marked(favorable),marked(mc[k]))
            if buffer<=0:
                x=k;xp=adverse-side*exit_slip;reason=4;lq+=1;break
            if trigger>=0:
                if k>=trigger+stop_delay:
                    x=k;xp=(lo[k] if side==1 else hi[k])-side*exit_slip;reason=1;break
                continue
            if side*(adverse-stop)<=0:
                if stop_delay:trigger=k;continue
                x=k;xp=(lo[k] if side==1 else hi[k])-side*exit_slip;reason=1;break
            if (lo[k]<=stop if side==1 else hi[k]>=stop):
                if stop_delay:trigger=k;continue
                x=k;xp=(min(op[k],stop) if side==1 else max(op[k],stop))-side*exit_slip;reason=1;break
            if (hi[k]>=target if side==1 else lo[k]<=target):
                x=k;xp=target-side*exit_slip;reason=2;break
            if q["trail_fraction"]>0:
                best=max(best,hi[k]) if side==1 else min(best,lo[k])
                if side*(best-ep)>=ep*.002:
                    ns=best-side*distance*q["trail_fraction"]
                    stop=max(stop,ns) if side==1 else min(stop,ns)
        net=(-ep/lev-fee*ep if reason==4 else side*(xp-ep)-fee*(ep+xp)+fund)-cost
        prior=earlyfund if month[x]!=m else 0.
        v[m]+=prior;v[month[x]]+=net-prior
        eq+=net;peak=max(peak,eq);dd=max(dd,peak-eq)
        mark_equity(x,eq,eq,eq)
        trades.append((j,x,side,ep,xp,net,int(reason==4),reason,leg,fund))
        occupied=x
    assert all(b[0]>a[1] for a,b in zip(trades,trades[1:]))
    assert abs(v.sum()-eq)<1e-6
    return dict(v=v,net=eq,dd=dd,trades=trades,liq=lq,min_buffer=None if not trades else minbuf,min_buffer_pct=None if not trades else minbuf_pct,min_liq_distance=None if not trades else minliq_dist,mtm_dd=mtm_dd,intraday_dd=day_dd)
def record(lev,scenario,period,mode,cost,res,ctx):
    v=res["v"];mi=range(22) if period=="train" else [22] if period=="november" else range(23)
    a=v[list(mi)];t=res["trades"]
    SUMMARY.append(dict(leverage=lev,scenario=scenario,period=period,funding_mode=mode,extra_cost_points=cost,net_points=res["net"],trades=len(t),wins=sum(x[5]>0 for x in t),liquidations=res["liq"],months_ge_1000=int((a>=1000).sum()),months_tested=len(a),min_month_points=float(a.min()),closed_dd_points=res["dd"],intraminute_mark_dd_upper_bound=res["mtm_dd"],intraday_mark_dd_upper_bound=res["intraday_dd"],min_mark_margin_buffer_points=res["min_buffer"],min_mark_margin_buffer_pct=res["min_buffer_pct"],min_mark_liquidation_distance_points=res["min_liq_distance"],pass_target=bool(len(t) and res["liq"]==0 and (a>=1000).all())))
    MONTHLY.extend(dict(leverage=lev,scenario=scenario,period=period,funding_mode=mode,cost=cost,month=str(pd.Period("2025-01",freq="M")+i),net_points=v[i]) for i in mi)
    if scenario=="baseline" and cost==200:
        for j,x,side,ep,xp,net,lq,reason,leg,fund in t:
            TRADES.append(dict(leverage=lev,period=period,funding_mode=mode,entry_utc=str(ctx["m"].index[j]),exit_utc=str(ctx["m"].index[x]),side=side,entry=ep,exit=xp,net_points=net,liquidation=lq,reason=reason,leg=leg,funding_proxy=fund))
def compare(res,ref,ledger,ctx,lev,period,mode,cost):
    t=res["trades"];a=res["v"][:22] if period=="train" else res["v"][22:]
    expected=ref.iloc[0]
    err=abs(res["net"]-expected.net_points)
    ok=err<1e-6 and len(t)==expected.trades and res["liq"]==expected.liquidations and int((a>=1000).sum())==expected.months_ge_1pct and abs(a.min()-expected.min_month_points)<1e-6 and abs(res["dd"]-expected.closed_dd_points)<1e-6
    ledger_ok=None
    if cost==200:
        ledger_ok=len(t)==len(ledger)
        for x,(_,r) in zip(t,ledger.iterrows()):
            ledger_ok=ledger_ok and str(ctx["m"].index[x[0]])==r.entry_utc and str(ctx["m"].index[x[1]])==r.exit_utc and x[2]==r.side and abs(x[3]-r.entry)<1e-6 and abs(x[4]-r.exit)<1e-6 and abs(x[5]-r.net_points)<1e-6 and x[6]==r.liquidation and x[7]==r.reason
    PARITY.append(dict(leverage=lev,period=period,funding_mode=mode,cost=cost,summary_parity=bool(ok),ledger_parity=ledger_ok,absolute_net_error_points=err))
def main():
    for f in FROZEN:
        lev=f["leverage"];p=f["profile"];source=f["source"]
        ctx=load_context(source,lev);event=signals(ctx,p)
        te=ctx["train_end"];end=ctx["end"]
        print("FROZEN",lev,"signals",len(event),"train candles",te,flush=True)
        # Check prefix stability (same selected signal times, sides, component
        # order) with future raw candles removed. IDs are allocation artifacts.
        for cutoff in ("2026-06-30 23:59:00","2026-10-31 17:59:00"):
            short=load_context(source,lev,cutoff)
            e=signals(short,p);bound=short["end"]-60
            key=lambda x:(x[0],x[1],x[3])
            l=[key(x) for x in event if x[0]<bound];r=[key(x) for x in e if x[0]<bound]
            PREFIX.append(dict(leverage=lev,cutoff_utc=cutoff,full_count=len(l),truncated_count=len(r),same_signals=l==r))
            del short
        folder=Path("analysis")/source
        reference=pd.read_csv(folder/"summary.csv");ledger=pd.read_csv(folder/"trades_200.csv")
        reference=reference[(reference.track=="known_november_development")&(reference.leverage==lev)];ledger=ledger[(ledger.track=="known_november_development")&(ledger.leverage==lev)]
        for period,first,last,oldperiod in (("train",0,te,"train"),("november",te,end,"november_known_development")):
            for mode in (0,1):
                label="signed_proxy" if mode==0 else "debit_only"
                for cost in COSTS:
                    res=independent(ctx,p,event,first,last,cost,mode)
                    record(lev,"baseline",period,mode,cost,res,ctx)
                    ref=reference[(reference.period==oldperiod)&(reference.funding_mode==label)&(reference.cost==cost)]
                    ld=ledger[(ledger.period==oldperiod)&(ledger.funding_mode==mode)&(ledger.cost==cost)]
                    compare(res,ref,ld,ctx,lev,period,mode,cost)
                # Separate cash-cost vs execution-fill stress; no double count
                # in actual-fill-only cases. Combined stress explicitly adds both.
                scenarios=[
                    ("actual_fill_10_each",0,dict(entry_slip=10.,exit_slip=10.)),
                    ("actual_fill_25_each",0,dict(entry_slip=25.,exit_slip=25.)),
                    ("actual_fill_50_each",0,dict(entry_slip=50.,exit_slip=50.)),
                    ("actual_fill_100_each",0,dict(entry_slip=100.,exit_slip=100.)),
                    ("cost200_fill25_each",200,dict(entry_slip=25.,exit_slip=25.)),
                    ("cost200_entry_delay1m",200,dict(delay=1)),
                    ("cost200_entry_delay2m",200,dict(delay=2)),
                    ("cost200_stop_delay1m",200,dict(stop_delay=1)),
                    ("cost200_mark_shock25",200,dict(mark_shock=25.)),
                    ("cost200_mark_shock50",200,dict(mark_shock=50.)),
                    ("cost200_mmr_0p30pct",200,dict(mmr=.003)),
                    ("cost200_mmr_0p35pct",200,dict(mmr=.0035)),
                    ("cost200_fee_0p07pct",200,dict(fee=.0007)),
                    ("combined",200,dict(entry_slip=25.,exit_slip=25.,delay=1,mmr=.003,mark_shock=25.)),
                ]
                for name,cost,kwargs in scenarios:
                    res=independent(ctx,p,event,first,last,cost,mode,**kwargs)
                    record(lev,name,period,mode,cost,res,ctx)
        for mode in (0,1):
            for cost in (0,200,250):
                res=independent(ctx,p,event,0,end,cost,mode)
                record(lev,"continuous_no_flat_reset","continuous",mode,cost,res,ctx)
        del ctx
        publish()
def publish():
    for name,rows in (("summary",SUMMARY),("monthly",MONTHLY),("parity",PARITY),("trades_200",TRADES),("prefix_audit",PREFIX)):
        pd.DataFrame(rows).to_csv(OUT/(name+".csv"),index=False)
    (OUT/"quality.json").write_text(json.dumps(dict(frozen_profiles_sha256=hashlib.sha256((OUT/"frozen_profiles.json").read_bytes()).hexdigest(),completed_leverages=sorted(set(r["leverage"] for r in SUMMARY)),summary_parity_pass=all(r["summary_parity"] for r in PARITY),ledger_parity_pass=all(r["ledger_parity"] is not False for r in PARITY),prefix_signal_audit_pass=all(r["same_signals"] for r in PREFIX),parity_cases=len(PARITY),scenario_rows=len(SUMMARY),independent_exit_replay=True,raw_trade_ledger_used_for_acceptance=False,drawdown="Conservative adverse/favorable mark extremes incl. exit minute, not exact tick ordering; normalized points",fee_and_mmr="Historical exact tiers/settlement records not verified; base 0.059% per side and 0.25% maintenance assumption",november="Known development data, no untouched holdout",forward_validation="pending new data after freeze",actual_account_margin_availability="not modeled, fixed per-BTC normalized points",exact_exchange_liquidation="unverified",demo_live="pending"),indent=2))
if __name__=="__main__":main()
