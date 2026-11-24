#!/usr/bin/env python3
"""One common profile, one signal stream, fixed stop % independent of leverage.
Compare isolated/cross at equal exposure and at $10 sizing-budget exposures.
Single-position account, USD equivalent INR balances at constant FX.
No additional deposits, no live orders, no optimization per leverage."""
import json,hashlib,itertools
from pathlib import Path
import numpy as np
import pandas as pd
import validate_frozen_high_leverage as audit
OUT=Path("analysis/v23_common_strategy_cross_margin")
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
def simulate(ctx,p,events,lev,margin_mode,sizing,sc,mode):
    name,cost,es,xs,delay,fee,mmr,shock,sd=sc
    op,hi,lo,cl,mo,mh,ml,rate,al,ash,sw,month,day,weekday=(ctx[x] for x in ("op","hi","lo","cl","mo","mh","ml","rate","adverse_long","adverse_short","sw","month","day","weekday"))
    end=ctx["end"];v=np.zeros(23);usd=np.zeros(23);equity=START;peak=START;dd=0.;ddpct=0.;mark_peak=START;markdd=0.;markddpct=0.
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
        stop=ep-side*distance*q["stop_fraction"];target=ep*(1+side*q["tp_pct"]/100.)
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
        equity+=net;peak=max(peak,equity);dd=max(dd,peak-equity);ddpct=max(ddpct,100*(peak-equity)/peak)
        mark_peak=max(mark_peak,equity);markdd=max(markdd,mark_peak-equity)
        markddpct=max(markddpct,100*(mark_peak-equity)/max(mark_peak,1e-12))
        occupied=x;trades.append((j,x,side,ep,xp,net,lots,reason,normalized))
    opening=START+np.r_[0.,np.cumsum(usd)[:-1]]
    returns=np.divide(100*usd,opening,out=np.zeros_like(usd),where=opening>0)
    assert abs(START+usd.sum()-equity)<1e-6
    assert all(b[0]>a[1] for a,b in zip(trades,trades[1:]))
    return dict(net_points=float(v.sum()),net_usd=equity-START,ending_equity=equity,months_ge_1pct_points=int((v[:22]>=1000).sum()),months_ge_1pct_account=int((returns[:22]>=1).sum()),min_month_account_pct=float(returns[:22].min()),november_account_pct=float(returns[22]),november_points=float(v[22]),trades=len(trades),wins=sum(t[5]>0 for t in trades),liquidations=liq,rejected_margin_or_lot=reject,closed_dd_usd=dd,closed_dd_pct=ddpct,mark_dd_upper_usd=markdd,mark_dd_upper_pct=markddpct,min_margin_buffer_usd=None if not trades else minbuf,max_effective_leverage=maxeff,pass_account=bool(trades and liq==0 and (returns>=1).all()),monthly_returns=returns,monthly_points=v,monthly_usd=usd)
def main():
    # Use V19 50x profile as the SINGLE common rule set, because it has
    # the wider original stop geometry. No per-leverage filter changes.
    f=next(f for f in audit.FROZEN if f["leverage"]==50);p=f["profile"]
    ctx=audit.load_context(f["source"],50);events=audit.signals(ctx,p)
    payload=dict(source=f["source"],reference_leverage=50,profile=p,stop_formula="entry * (1/50 - .00059 - .0025)/(1-side*.0025)*stop_fraction",filter_reference_leverage=50,signal_count=len(events),position_limit=1)
    (OUT/"common_profile.json").write_text(json.dumps(payload,indent=2))
    rows=[];months=[]
    for lev in LEVS:
        for mode,sizing,sc,fm in itertools.product(("isolated","cross"),("fixed_10_margin_budget","fixed_notional_100","fixed_notional_500","fixed_notional_1000"),SCENARIOS,(0,1)):
            r=simulate(ctx,p,events,lev,mode,sizing,sc,fm)
            base=dict(leverage_or_sizing_label=lev,margin_mode=mode,sizing=sizing,scenario=sc[0],funding_mode=fm)
            ret=r.pop("monthly_returns");pts=r.pop("monthly_points");usd=r.pop("monthly_usd")
            rows.append(dict(**base,**r))
            months.extend(dict(**base,month=str(pd.Period("2025-01",freq="M")+i),account_return_pct=ret[i],net_points=pts[i],net_usd=usd[i]) for i in range(23))
        print("COMPLETE",lev,len(rows),flush=True)
        pd.DataFrame(rows).to_csv(OUT/"summary.csv",index=False);pd.DataFrame(months).to_csv(OUT/"monthly.csv",index=False)
    (OUT/"quality.json").write_text(json.dumps(dict(common_profile_sha256=hashlib.sha256((OUT/"common_profile.json").read_bytes()).hexdigest(),scenario_rows=len(rows),starting_equity_usd_equivalent=START,margin_sizing_budget_usd=MARGIN,contract_lot_btc=LOT,all_leverage_same_signals_and_stops=True,cross_imr_assumed=.005,actual_account_model="single position, constant FX, no external deposits, realized balance carries continuously",funding="historical proxy only",liquidation="conservative full collateral loss proxy, exact exchange settlement unverified",historical_data="known development through Nov17 UTC",untouched_forward=False),indent=2))
if __name__=="__main__":main()
