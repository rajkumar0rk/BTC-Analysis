#!/usr/bin/env python3
"""One common profile, one signal stream, fixed stop % independent of leverage.
Compare isolated/cross at equal exposure and at $10 sizing-budget exposures.
Single-position account, USD equivalent INR balances at constant FX.
No additional deposits, no live orders, no optimization per leverage."""
import json,hashlib,itertools,copy
from pathlib import Path
import numpy as np
import pandas as pd
import validate_frozen_high_leverage as audit
OUT=Path("analysis/v24_common_drawdown_control")
OUT.mkdir(parents=True,exist_ok=True)
START=100.;MARGIN=10.;LOT=.001;MAXLEV=200
LEVS=(5,10,20,25,50,100,200)
FEE=.00059;MMR=.0025;LIQ_FEE=.00295
SCENARIOS=[
("base",200,5.,5.,0,FEE,MMR,0.,0),
("cash_0",0,5.,5.,0,FEE,MMR,0.,0),
("cash_50",50,5.,5.,0,FEE,MMR,0.,0),
("cash_100",100,5.,5.,0,FEE,MMR,0.,0),
("cash_150",150,5.,5.,0,FEE,MMR,0.,0),
("cash_250",250,5.,5.,0,FEE,MMR,0.,0),
("fill10",0,10.,10.,0,FEE,MMR,0.,0),
("fill25",0,25.,25.,0,FEE,MMR,0.,0),
("fill50",0,50.,50.,0,FEE,MMR,0.,0),
("fill100",0,100.,100.,0,FEE,MMR,0.,0),
("cost200_fill25",200,25.,25.,0,FEE,MMR,0.,0),
("entry1",200,5.,5.,1,FEE,MMR,0.,0),
("entry2",200,5.,5.,2,FEE,MMR,0.,0),
("stop1",200,5.,5.,0,FEE,MMR,0.,1),
("shock25",200,5.,5.,0,FEE,MMR,25.,0),
("shock50",200,5.,5.,0,FEE,MMR,50.,0),
("mmr30",200,5.,5.,0,FEE,.003,0.,0),
("mmr35",200,5.,5.,0,FEE,.0035,0.,0),
("fee07",200,5.,5.,0,.0007,MMR,0.,0),
("combined",200,25.,25.,1,FEE,.003,25.,0)]
def simulate(ctx,p,events,lev,margin_mode,sizing,sc,mode,control=None):
    control=control or {}
    name,cost,es,xs,delay,fee,mmr,shock,sd=sc
    op,hi,lo,cl,mo,mh,ml,rate,al,ash,sw,month,day,weekday=(ctx[x] for x in ("op","hi","lo","cl","mo","mh","ml","rate","adverse_long","adverse_short","sw","month","day","weekday"))
    end=ctx["end"];v=np.zeros(23);usd=np.zeros(23);equity=START;peak=START;dd=0.;ddpct=0.;mark_peak=START;markdd=0.;markddpct=0.
    days_usd={};monthly_open={};monthly_peak={};reject_risk=0
    mtd=np.zeros(23);occupied=-1;used=set();lastday=-1;today=0;trades=[];reject=0;liq=0;minbuf=1e30;maxeff=0.
    # same reference profile geometry, never calculated from selected leverage
    refdist=(1./50-FEE-MMR)
    for orig,side,cyc,leg in events:
        j=orig+delay
        if j>=end or j<=occupied or weekday[j]>=5 or day[j]!=day[orig] or (cyc>0 and cyc in used):continue
        q=p["legs"][leg];m=int(month[j]);d=int(day[j])
        if d!=lastday:lastday=d;today=0
        if p["daily_limit"] and today>=p["daily_limit"]:continue
        if mtd[m]>=p["month_ceiling"] or mtd[m]<=-p["loss_guard"] or mtd[m]>=q["mtd_gate"]:continue
        ep=op[j]+side*es
        target_notional=MARGIN*lev if sizing=="fixed_10_margin_budget" else float(sizing.split("_")[-1])
        # Common controls: no per-leverage calibration. Risk estimates
        # use planned stop, prior closed volatility and fixed execution reserve,
        # not future extremes. Equity is current realized account balance.
        distance=ep*refdist/(1.-side*MMR)
        planned_stop=distance*q["stop_fraction"]*control.get("stop_scale",1.)
        dd_now=max(0.,(peak-equity)/peak)
        throttle=1.
        threshold=control.get("throttle_at",0.)
        if threshold>0 and dd_now>=threshold:throttle=max(control.get("throttle_floor",.35),1.-dd_now/threshold*.5)
        risk=control.get("risk_pct",0.)
        maxeff_control=control.get("max_eff",0.)
        if maxeff_control>0:target_notional=min(target_notional,equity*maxeff_control)
        if risk>0:
            reserve=control.get("reserve_points",250.)+2*fee*ep+max(mh[j-1]-ml[j-1],mh[j-2]-ml[j-2])
            target_notional=min(target_notional,equity*risk*ep/max(1.,planned_stop+reserve))
        target_notional*=throttle
        # Realized daily/monthly loss budget; only blocks new entries,
        # never masks or deletes realized losing trades.
        if m not in monthly_open:monthly_open[m]=equity;monthly_peak[m]=equity
        monthly_peak[m]=max(monthly_peak[m],equity)
        md=control.get("monthly_loss",0.);dl=control.get("daily_loss",0.)
        if (md>0 and equity<=monthly_open[m]*(1-md)) or (dl>0 and days_usd.get(d,0.)<=-equity*dl):
            reject_risk+=1;continue
        lots=int(target_notional/(ep*LOT));qty=lots*LOT
        if qty<=0:reject+=1;continue
        # Cross labels represent size-budget exposure, not adjustable
        # exchange leverage. Current initial margin assumed 0.5%.
        imr=1./lev if margin_mode=="isolated" else 1./MAXLEV
        initial=qty*ep*imr;entryfee=qty*ep*fee
        if equity<=0 or equity<initial+entryfee+qty*ep*fee:
            reject+=1;continue
        # Actual wallet / position collateral, not virtual added funds.
        collateral=initial if margin_mode=="isolated" else equity
        maxeff=max(maxeff,qty*ep/equity)
        today+=1
        if cyc>0:used.add(cyc)
        distance=ep*refdist/(1.-side*MMR)
        stop=ep-side*planned_stop;target=ep*(1+side*q["tp_pct"]/100.)
        fund=early=0.;best=ep;reason=3;trigger=-1
        x=min(j+q["max_minutes"]-1,end-1);xp=cl[x]-side*xs
        for k in range(j,x+1):
            if k>j and (k<sw or k%480==0):
                r=rate[k] if mode==0 else (al[k] if side==1 else ash[k])
                ff=-side*mo[k]*r/(480. if k<sw else 1.)
                fund+=ff
                if month[k]==m:early+=ff
            adverse=(ml[k] if side==1 else mh[k])-side*shock
            favorable=mh[k] if side==1 else ml[k]
            margin_buffer=collateral-entryfee+qty*(fund+side*(adverse-ep)-mmr*adverse)
            minbuf=min(minbuf,margin_buffer)
            favorable_equity=equity+qty*(fund+side*(favorable-ep)-fee*(ep+favorable)-cost)
            adverse_equity=equity+qty*(fund+side*(adverse-ep)-fee*(ep+adverse)-cost)
            mark_peak=max(mark_peak,favorable_equity)
            markdd=max(markdd,mark_peak-adverse_equity)
            markddpct=max(markddpct,100*(mark_peak-adverse_equity)/max(mark_peak,1e-12))
            if margin_buffer<=0:
                x=k;xp=adverse-side*xs;reason=4;liq+=1;break
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
            # New protection activates after the minute has completed;
            # never assume that a favorable extreme precedes an adverse one.
            activation=control.get("protect_activate",0.)
            if activation>0:
                best=max(best,hi[k]) if side==1 else min(best,lo[k])
                favorable_pct=side*(best-ep)/ep
                if favorable_pct>=activation:
                    lock=control.get("protect_lock",.002)
                    gap=control.get("protect_gap",.006)
                    locked=max(lock,favorable_pct-gap)
                    ns=ep*(1+side*locked)
                    stop=max(stop,ns) if side==1 else min(stop,ns)
            if q["trail_fraction"]>0:
                best=max(best,hi[k]) if side==1 else min(best,lo[k])
                if side*(best-ep)>=ep*.002:
                    ns=best-side*distance*q["trail_fraction"]
                    stop=max(stop,ns) if side==1 else min(stop,ns)
        normal=qty*(side*(xp-ep)-fee*(ep+xp)+fund-cost)
        # Conservative liquidation proxy: entire allocated isolated
        # collateral, or entire cross wallet, is lost. No exact partial
        # liquidation or exchange liquidation fee claim.
        net=max(-equity,-collateral-entryfee-qty*cost) if reason==4 else max(-equity,normal)
        normalized=net/qty
        prev=early if month[x]!=m else 0.
        mtd[m]+=prev;mtd[month[x]]+=normalized-prev
        v[m]+=prev;v[month[x]]+=normalized-prev
        usd[m]+=prev*qty;usd[month[x]]+=net-prev*qty
        days_usd[int(day[x])]=days_usd.get(int(day[x]),0.)+net
        equity+=net;peak=max(peak,equity);dd=max(dd,peak-equity);ddpct=max(ddpct,100*(peak-equity)/peak)
        mark_peak=max(mark_peak,equity);markdd=max(markdd,mark_peak-equity)
        markddpct=max(markddpct,100*(mark_peak-equity)/max(mark_peak,1e-12))
        occupied=x;trades.append((j,x,side,ep,xp,net,lots,reason,normalized))
    opening=START+np.r_[0.,np.cumsum(usd)[:-1]]
    returns=np.divide(100*usd,opening,out=np.zeros_like(usd),where=opening>0)
    assert abs(START+usd.sum()-equity)<1e-6
    assert all(b[0]>a[1] for a,b in zip(trades,trades[1:]))
    return dict(net_points=float(v.sum()),net_usd=equity-START,ending_equity=equity,months_ge_1pct_points=int((v[:22]>=1000).sum()),months_ge_1pct_account=int((returns[:22]>=1).sum()),min_month_account_pct=float(returns[:22].min()),november_account_pct=float(returns[22]),november_points=float(v[22]),trades=len(trades),wins=sum(t[5]>0 for t in trades),liquidations=liq,rejected_margin_or_lot=reject,rejected_risk_guard=reject_risk,closed_dd_usd=dd,closed_dd_pct=ddpct,mark_dd_upper_usd=markdd,mark_dd_upper_pct=markddpct,min_margin_buffer_usd=None if not trades else minbuf,max_effective_leverage=maxeff,pass_account=bool(trades and liq==0 and (returns>=1).all()),monthly_returns=returns,monthly_points=v,monthly_usd=usd)
def main():
    f=next(f for f in audit.FROZEN if f["leverage"]==50);p=f["profile"]
    ctx=audit.load_context(f["source"],50);events=audit.signals(ctx,p)
    # All configurations tested as a common policy at each sizing label.
    # Keep the baseline, compare controls and report tradeoffs transparently.
    configs=[("baseline",{})]
    for risk in (.02,.03,.04,.05,.075,.10,.15,.20):
        configs.append((f"risk_{risk}",dict(risk_pct=risk)))
    for cap in (1.5,2.,3.,4.,5.,6.,8.,10.):
        configs.append((f"exposure_{cap}",dict(max_eff=cap)))
    for t in (.05,.08,.12,.18):
        configs.append((f"throttle_{t}",dict(throttle_at=t,throttle_floor=.4)))
    for ss in (.55,.7,.85,1.15):
        configs.append((f"stop_{ss}",dict(stop_scale=ss)))
    for a,l,g in ((.004,.002,.003),(.006,.002,.004),(.008,.003,.005),(.01,.003,.006),(.012,.004,.008),(.015,.005,.01),(.02,.008,.012)):
        configs.append((f"protect_{a}_{l}_{g}",dict(protect_activate=a,protect_lock=l,protect_gap=g)))
    for risk,cap in ((.03,3.),(.04,4.),(.05,5.),(.075,6.),(.1,8.)):
        configs.append((f"hybrid_{risk}_{cap}",dict(risk_pct=risk,max_eff=cap,throttle_at=.10,throttle_floor=.5)))
        configs.append((f"hybrid_protect_{risk}_{cap}",dict(risk_pct=risk,max_eff=cap,throttle_at=.10,throttle_floor=.5,protect_activate=.01,protect_lock=.003,protect_gap=.006)))
    for md in (.03,.05,.08):
        configs.append((f"monthly_guard_{md}",dict(monthly_loss=md)))
    levels=(10,20,25,50,100,200)
    focus=[sc for sc in SCENARIOS if sc[0] in ("base","combined","fill100","stop1")]
    summaries=[];months=[];ranks=[]
    def run(name,ctrl,scens,modes,stage):
        out=[]
        for lev,sc,fm in itertools.product(levels,scens,modes):
            r=simulate(ctx,p,events,lev,"cross","fixed_10_margin_budget",sc,fm,ctrl)
            b=dict(config=name,stage=stage,leverage=lev,scenario=sc[0],funding_mode=fm)
            ret=r.pop("monthly_returns");pts=r.pop("monthly_points");usd=r.pop("monthly_usd")
            row=dict(**b,**r);out.append(row);summaries.append(row)
            if stage=="full":
                months.extend(dict(**b,month=str(pd.Period("2025-01",freq="M")+i),account_return_pct=ret[i],net_usd=usd[i],net_points=pts[i]) for i in range(23))
        return out
    def score(rows):
        # 10x frequently fails minimum lot/return target for structural
        # reasons. Rank 20x–200x, still report 10x transparently.
        a=[r for r in rows if r["leverage"]>=20]
        return (int(all(r["liquidations"]==0 and r["trades"]>=23 for r in a)),
                min(r["months_ge_1pct_account"]+int(r["november_account_pct"]>=1) for r in a),
                sum(r["months_ge_1pct_account"]+int(r["november_account_pct"]>=1) for r in a),
                -max(r["mark_dd_upper_pct"] for r in a),
                min(r["net_usd"] for r in a))
    def metrics(rows):
        a=[r for r in rows if r["leverage"]>=20]
        return dict(worst_dd=max(r["mark_dd_upper_pct"] for r in a),worst_closed_dd=max(r["closed_dd_pct"] for r in a),min_profit=min(r["net_usd"] for r in a),max_liq=max(r["liquidations"] for r in a),min_trades=min(r["trades"] for r in a),min_months=min(r["months_ge_1pct_account"] for r in a),sum_months=sum(r["months_ge_1pct_account"] for r in a),base_profit_sum=sum(r["net_usd"] for r in a if r["scenario"]=="base"))
    scanned=[]
    for name,ctrl in configs:
        rr=run(name,ctrl,focus,(0,1),"search")
        met=metrics(rr);scanned.append((name,ctrl,score(rr),met))
        print("SEARCH",name,scanned[-1][2],met,flush=True)
        pd.DataFrame(summaries).to_csv(OUT/"summary.csv",index=False)
    # Select candidates across different drawdown budgets; also retain
    # monthly-consistency leaders and profit leaders. No per-leverage fit.
    valid=[x for x in scanned if x[3]["max_liq"]==0 and x[3]["min_trades"]>=23]
    chosen={"baseline"}
    for limit in (10.,15.,20.,25.,30.,40.,50.):
        eligible=[x for x in valid if x[3]["worst_dd"]<=limit]
        if eligible:
            chosen.add(max(eligible,key=lambda x:(x[3]["sum_months"],x[3]["min_profit"],x[3]["base_profit_sum"]))[0])
    chosen.update(x[0] for x in sorted(valid,key=lambda x:x[2],reverse=True)[:4])
    chosen.update(x[0] for x in sorted(valid,key=lambda x:(x[3]["worst_dd"],-x[3]["min_profit"]))[:3])
    chosen.update(x[0] for x in sorted(valid,key=lambda x:x[3]["min_profit"],reverse=True)[:3])
    full=[]
    for name,ctrl in configs:
        if name not in chosen:continue
        rr=run(name,ctrl,SCENARIOS,(0,1),"full")
        met=metrics(rr);rank=score(rr)
        full.append(dict(config=name,controls=ctrl,rank=list(rank),**met))
        print("FULL",name,rank,met,flush=True)
        pd.DataFrame(summaries).to_csv(OUT/"summary.csv",index=False)
        pd.DataFrame(months).to_csv(OUT/"monthly.csv",index=False)
    # Same common configuration across leverages. Report Pareto tradeoffs,
    # not an artificial claim that lower exposure preserves dollar profit.
    full.sort(key=lambda x:x["rank"],reverse=True)
    (OUT/"quality.json").write_text(json.dumps(dict(configs_tested=len(configs),full_configs=len(full),scenario_rows=len(summaries),common_profile=p,ranking=full,all_leverages_same_strategy=True,account_start=START,margin_budget=MARGIN,search_scenarios=[s[0] for s in focus],full_scenarios=[s[0] for s in SCENARIOS],funding_modes=[0,1],known_development_only=True,exact_exchange_liquidation_unverified=True),indent=2,default=float))
if __name__=="__main__":main()
