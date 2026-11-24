#!/usr/bin/env python3
"""Common entry/exit configuration search with hard dollar-profit floors.
Development data only. No ledger-based selection or calendar-specific rules.
All comparisons use the same account model as V24, not points as returns."""
import copy,hashlib,itertools,json
from pathlib import Path
import numpy as np
import pandas as pd
import research_v24_common_drawdown_control as engine
import validate_frozen_high_leverage as audit

OUT=Path("analysis/v25_profit_preserving_drawdown")
OUT.mkdir(parents=True,exist_ok=True)
LEVELS=(20,25,50,100,200)
ALL_LEVELS=(10,20,25,50,100,200)
SC={s[0]:s for s in engine.SCENARIOS}
F=next(f for f in audit.FROZEN if f["leverage"]==50)
ORIGINAL=copy.deepcopy(F["profile"])
def clean(x):
    return json.dumps(x,sort_keys=True,separators=(",",":"),allow_nan=False)
def main():
    ctx=audit.load_context(F["source"],50)
    groups=ctx["data_groups"]; masks=ctx["masks2"]
    base_events=audit.signals(ctx,ORIGINAL)
    print("SIGNALS",len(base_events),"CANDIDATE_GROUPS",len(groups),flush=True)
    # Preserve exact signal IDs and time order. Additional filters are built
    # from completed bar features already used in V19, never current highs/lows.
    # V19 feature layout: [index,side,entry hint,cycle,ATR,trend1,trend4,
    # volume,ADX,ATR ratio,slope,range5,range20,basis,body,ret5,ret15,basis sign].
    for q in (.5,.75,1.,1.25,1.5,2.):
        masks["v25_adx_"+str(q)]=lambda a,q=q:a[:,8]>=20*q
        masks["v25_vol_"+str(q)]=lambda a,q=q:a[:,7]>=q
    for q in (.5,.75,1.,1.25):
        masks["v25_atr_"+str(q)]=lambda a,q=q:a[:,9]>=q
    masks["v25_align_h1"]=lambda a:a[:,5]>0
    masks["v25_align_h4"]=lambda a:a[:,6]>0
    masks["v25_align_both"]=lambda a:(a[:,5]>0)&(a[:,6]>0)
    masks["v25_body"]=lambda a:a[:,14]>.25
    masks["v25_body_strong"]=lambda a:a[:,14]>.5
    masks["v25_ret5"]=lambda a:a[:,15]>0
    masks["v25_ret15"]=lambda a:a[:,16]>0
    def events_for(p,extra):
        rows=[]
        for i,q in enumerate(p["legs"]):
            a=groups[q["group"]]; m=masks[q["filter"]](a)
            if extra.get(str(i)):m=m&masks[extra[str(i)]](a)
            for r in a[m]:rows.append((int(r[0]),int(r[1]),int(r[3]),i))
        return sorted(rows,key=lambda x:x[0])
    def state(p=None,c=None,extra=None):
        return dict(profile=copy.deepcopy(ORIGINAL if p is None else p),control=copy.deepcopy(c or {}),extra_filters=copy.deepcopy(extra or {}))
    original=state()
    base={}
    def simulate(s,lev,scenario,mode,events=None):
        if events is None:events=events_for(s["profile"],s["extra_filters"])
        r=engine.simulate(ctx,s["profile"],events,lev,"cross","fixed_10_margin_budget",SC[scenario],mode,s["control"])
        ret=r.pop("monthly_returns");pts=r.pop("monthly_points");usd=r.pop("monthly_usd")
        return r
    for lev,mode in itertools.product(ALL_LEVELS,(0,1)):
        for sc in ("base","combined","fill100","stop1","cash_0","fill25","entry1","entry2","shock50","mmr35"):
            base[lev,sc,mode]=simulate(original,lev,sc,mode,base_events)
    expected={20:99.40680955715254,25:149.33613186977848,50:322.2315774110829,100:662.7669882929613,200:1359.5096845738988}
    for lev,p in expected.items():
        assert abs(base[lev,"base",0]["net_usd"]-p)<1e-6,(lev,base[lev,"base",0]["net_usd"],p)
    # Base hard floor for BOTH funding modes, at each sizing level.
    # Require 22/22 + November in base as well as no liquidations.
    # Stress floors preserve positive original profit; when original is
    # negative require at least zero, not merely a smaller loss.
    # A partial candidate is never called a strict pass.
    def metrics(rows,baseline_rows):
        n=len(rows);rat=[];debt=[];liqs=0;miss=0;dd=0.;closed=0.;profit=[]
        for r,b in zip(rows,baseline_rows):
            floor=max(0.,b["net_usd"])
            rat.append(r["net_usd"]/max(1.,floor))
            debt.append(max(0.,floor-r["net_usd"])/max(1.,floor))
            liqs+=r["liquidations"]
            miss+=22-r["months_ge_1pct_account"]+int(r["november_account_pct"]<1.)
            dd=max(dd,r["mark_dd_upper_pct"]);closed=max(closed,r["closed_dd_pct"])
            profit.append(r["net_usd"])
        return dict(preserve=all(x<=1e-8 for x in debt),min_ratio=min(rat),deficit=sum(debt),liq=liqs,miss=miss,dd=dd,closed=closed,min_profit=min(profit),sum_profit=sum(profit),count=n)
    # Screening uses all base sizing levels (signed) and stress at both
    # ends of exposure, then full finalists recheck ALL sizes/modes/scenarios.
    base_grid=[(l,"base",0) for l in LEVELS]
    stress_grid=[(l,s,0) for l in (20,50,200) for s in ("combined","fill100","stop1")]
    cache={};ledger=[];evaluations=0
    def evaluate(s):
        nonlocal evaluations
        k=clean(s)
        if k in cache:return cache[k]
        e=events_for(s["profile"],s["extra_filters"])
        bb=[simulate(s,*g,e) for g in base_grid];evaluations+=len(bb)
        bm=metrics(bb,[base[g] for g in base_grid])
        # Do not spend stress runs on hopeless base-profit candidates, but
        # keep a broad secondary search path for close-to-floor strategies.
        if bm["preserve"] or (bm["min_ratio"]>=.85 and bm["liq"]==0):
            ss=[simulate(s,*g,e) for g in stress_grid];evaluations+=len(ss)
            sm=metrics(ss,[base[g] for g in stress_grid])
        else:sm=dict(preserve=False,min_ratio=-1e9,deficit=1e9,liq=10**6,miss=10**6,dd=1e9,closed=1e9,min_profit=-1e9,sum_profit=-1e9,count=0)
        # Lexicographic feasibility first, then drawdown. Baseline retained.
        rank=(int(bm["preserve"] and bm["liq"]==0 and bm["miss"]==0),
              int(bm["preserve"] and bm["liq"]==0),int(sm["preserve"] and sm["liq"]==0),
              -bm["deficit"],-bm["liq"],-bm["miss"],
              -max(bm["dd"],sm["dd"]),-sm["liq"],-sm["miss"],-sm["deficit"],-bm["dd"],bm["sum_profit"])
        z=dict(state=s,rank=rank,base=bm,stress=sm)
        cache[k]=z
        ledger.append(dict(id=hashlib.sha256(k.encode()).hexdigest()[:16],base=bm,stress=sm,rank=rank,state=s))
        return z
    def keep(zs,n):
        unique={clean(z["state"]):z for z in zs}
        return sorted(unique.values(),key=lambda z:z["rank"],reverse=True)[:n]
    seed=evaluate(original)
    print("BASELINE",seed["base"],seed["stress"],flush=True)
    # One common strategy; modify one sleeve at a time. Test symmetric
    # parameters and generic feature filters, not month-specific exceptions.
    beam=[seed];archive=[seed]
    def variants(s,i):
        p=s["profile"];q=p["legs"][i]
        def replace(**kw):
            t=copy.deepcopy(s);t["profile"]["legs"][i].update(kw);return t
        for v in (.10,.20,.30,.40,.50,.60,.75,.90,1.10):
            yield replace(stop_fraction=round(q["stop_fraction"]*v,5))
        for v in (.65,.8,.9,1.1,1.25,1.5,2.):
            yield replace(tp_pct=round(q["tp_pct"]*v,5))
        for v in (120,360,720,1440,2160,2880,4320,5760,7200):
            if v!=q["max_minutes"]:yield replace(max_minutes=v)
        for v in (0.,.3,.6,1.,1.5,2.,3.):
            if v!=q["trail_fraction"]:yield replace(trail_fraction=v)
        for v in (-1000.,0.,500.,1000.,1500.,1e30):
            if v!=q["mtd_gate"]:yield replace(mtd_gate=v)
        for name in ("all","H4_align","H4_not_aligned","high_ATR_ratio","range_ADX20","long_ADX25","short_ADX25","quiet20_0.5"):
            if name in masks and name!=q["filter"]:yield replace(filter=name)
        for name in ("v25_align_h1","v25_align_h4","v25_align_both","v25_body","v25_body_strong","v25_ret5","v25_ret15","v25_adx_0.75","v25_adx_1.25","v25_vol_1.25","v25_atr_0.75","v25_atr_1.25"):
            t=copy.deepcopy(s);t["extra_filters"][str(i)]=name;yield t
        # Removing an entire generic sleeve is permitted, but never individual trades.
        if len(p["legs"])>1:
            t=copy.deepcopy(s);t["profile"]["legs"].pop(i)
            t["extra_filters"]={str(int(k)-(int(k)>i)):v for k,v in t["extra_filters"].items() if int(k)!=i};yield t
    def globals_for(s):
        for cap,lim,loss in itertools.product((1500.,2000.,2500.,3000.,4000.),(1,2,3),(3000.,6000.,10000.)):
            t=copy.deepcopy(s);t["profile"].update(month_ceiling=cap,daily_limit=lim,loss_guard=loss);yield t
        for a,l,g in ((.008,.002,.008),(.012,.003,.01),(.015,.005,.012),(.02,.008,.015),(.025,.01,.015),(.03,.015,.02),(.04,.02,.02)):
            t=copy.deepcopy(s);t["control"].update(protect_activate=a,protect_lock=l,protect_gap=g);yield t
        for risk in (.025,.04,.06,.075,.10,.125,.15,.2):
            t=copy.deepcopy(s);t["control"]["risk_pct"]=risk;yield t
    # Start with global guard changes that may allow more profitable trades,
    # then refine each sleeve and retain diverse feasible and near-feasible states.
    beam=keep([seed]+[evaluate(s) for s in globals_for(original)],5)
    archive=keep(archive+beam,30)
    for epoch in range(2):
        for i in range(len(ORIGINAL["legs"])):
            nxt=[]
            for z in beam[:3]:
                s=z["state"]
                if i>=len(s["profile"]["legs"]):continue
                for t in variants(s,i):nxt.append(evaluate(t))
            beam=keep(beam+nxt,5);archive=keep(archive+beam,35)
            print("LOCAL",epoch,i,"configs",len(cache),"eval",evaluations,"top",beam[0]["base"],beam[0]["stress"],flush=True)
        zz=[]
        for z in beam[:2]:
            for t in globals_for(z["state"]):zz.append(evaluate(t))
        beam=keep(beam+zz,5);archive=keep(archive+beam,35)
    # Candidate add-on recovery from original causal groups; no use of
    # trade outcomes for admission. At most two additional generic sleeves.
    names=[n for n,a in groups.items() if len(a)>=25 and ("squeeze" in n or "Donchian" in n or "reversal" in n or "reclaim" in n)]
    names=sorted(names,key=lambda n:(len(groups[n]),n))[:30]
    for epoch in range(2):
        nxt=[]
        for z in beam[:2]:
            s=z["state"];used={q["group"] for q in s["profile"]["legs"]}
            for n in names:
                if n in used:continue
                for label in ("all","H4_align","high_ATR_ratio"):
                    if label not in masks:continue
                    for sf,tp,hold in ((.3,3.,1440),(.5,4.,4320),(.7,6.,4320)):
                        for gate in (0.,1000.,1e30):
                            t=copy.deepcopy(s);t["profile"]["legs"].append(dict(group=n,filter=label,stop_fraction=sf,tp_pct=tp,max_minutes=hold,trail_fraction=0.,mtd_gate=gate))
                            nxt.append(evaluate(t))
            beam=keep(beam+nxt,5);archive=keep(archive+beam,35)
        print("ADD",epoch,len(cache),evaluations,beam[0]["rank"],flush=True)
    # Additional frontiers retain base profit AND low base DD, even when
    # stress performance is weaker. Report both rather than silently trade
    # base profit for stress improvement.
    feasible=[z for z in cache.values() if z["base"]["preserve"] and z["base"]["liq"]==0 and z["base"]["miss"]==0]
    low_base=sorted(feasible,key=lambda z:(z["base"]["dd"],z["base"]["closed"],-z["base"]["sum_profit"]))[:8]
    low_stress=sorted(feasible,key=lambda z:(z["stress"]["liq"],z["stress"]["dd"],z["stress"]["deficit"],z["stress"]["miss"]))[:8]
    finalists=keep(archive+beam,12)+low_base+low_stress+[seed]
    uniq={clean(z["state"]):z for z in finalists}
    rows=[];monthly=[];full=[]
    grid=list(itertools.product(ALL_LEVELS,SC,(0,1)))
    # Baseline exact stress grid used as reference, including both funding modes.
    for g in grid:
        if g not in base:base[g]=simulate(original,*g,base_events)
    for ix,z in enumerate(uniq.values()):
        s=z["state"];e=events_for(s["profile"],s["extra_filters"])
        name="baseline" if clean(s)==clean(original) else "candidate_"+hashlib.sha256(clean(s).encode()).hexdigest()[:12]
        rr=[]
        for lev,sc,fm in grid:
            r=engine.simulate(ctx,s["profile"],e,lev,"cross","fixed_10_margin_budget",SC[sc],fm,s["control"])
            ret=r.pop("monthly_returns");pts=r.pop("monthly_points");usd=r.pop("monthly_usd")
            row=dict(config=name,leverage=lev,scenario=sc,funding_mode=fm,**r)
            rr.append(row);rows.append(row)
            monthly.extend(dict(config=name,leverage=lev,scenario=sc,funding_mode=fm,month=str(pd.Period("2025-01",freq="M")+i),net_usd=usd[i],account_return_pct=ret[i],net_points=pts[i]) for i in range(23))
        def getm(pred):
            a=[r for r in rr if pred(r)]
            return metrics(a,[base[r["leverage"],r["scenario"],r["funding_mode"]] for r in a])
        b=getm(lambda r:r["leverage"] in LEVELS and r["scenario"]=="base")
        st=getm(lambda r:r["leverage"] in LEVELS and r["scenario"]!="base")
        a=getm(lambda r:r["leverage"] in LEVELS)
        # Strict pass: no loss of profit in every scenario, zero liquidations,
        # 22/22 + November at each sizing level and both funding modes.
        strict=bool(a["preserve"] and a["liq"]==0 and a["miss"]==0)
        bp=bool(b["preserve"] and b["liq"]==0 and b["miss"]==0)
        full.append(dict(config=name,state=s,base=b,stress=st,all=a,base_profit_pass=bp,strict_pass=strict,
            rank=[int(strict),int(bp),int(st["preserve"] and st["liq"]==0),-a["deficit"],-a["liq"],-a["miss"],-a["dd"],-b["dd"],b["sum_profit"]]))
        print("FULL",ix,name,b,st,strict,flush=True)
        pd.DataFrame(rows).to_csv(OUT/"summary.csv",index=False)
        pd.DataFrame(monthly).to_csv(OUT/"monthly.csv",index=False)
        pd.DataFrame([{k:v for k,v in r.items() if k!="state"} for r in ledger]).to_json(OUT/"search_metrics.jsonl",orient="records",lines=True)
        (OUT/"quality.json").write_text(json.dumps(dict(configurations=len(cache),screen_evaluations=evaluations,full_configurations=len(full),full_rows=len(rows),ranked=sorted(full,key=lambda x:x["rank"],reverse=True),base_reference=expected,common_profile=True,profit_floors="per sizing level and funding mode, original V23 baseline; stress floor max(0,original profit)",base_floor_levels=list(LEVELS),ten_x_reported_not_ranked=True,known_development_only=True,exact_exchange_liquidation_unverified=True),indent=2,default=float))
if __name__=="__main__":main()
