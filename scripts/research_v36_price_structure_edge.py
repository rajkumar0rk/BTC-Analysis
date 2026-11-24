#!/usr/bin/env python3
"""V36: price structure entry hypotheses, 2024+2025 only.
Freeze before reading 2026. No monthly gates, daily cap, recovery sleeves,
date-specific entry rules, or leverage-specific tuning.
All prices and funding native Delta; conservative OHLC fills.
Historical 2026 has already been examined in previous research, not blind."""
import sys,json,hashlib,urllib.request,urllib.parse,time,itertools
from pathlib import Path
import numpy as np
import pandas as pd
from numba import njit
import research_v24_common_drawdown_control as old
OUT=Path("analysis/v36_price_structure_edge");OUT.mkdir(parents=True,exist_ok=True)
ROOT=Path("data/delta_india/BTCUSD")
ARCH=ROOT/"2024_verified_archive"
IST="Asia/Kolkata";FEE=.00059;MMR=.0025;RISK=.03;CAP=3.
TRAIN_START=pd.Timestamp("2024-01-30",tz="UTC")
TRAIN_END=pd.Timestamp("2026-01-01",tz=IST).tz_convert("UTC")
VALID_END=pd.Timestamp("2026-11-18",tz="UTC")
SC=[s for s in old.SCENARIOS if s[0] in ("base","combined")]
FOLDS=[("2024_H1","2024-02-01","2024-07-01"),("2024_H2","2024-07-01","2025-01-01"),("2025_H1","2025-01-01","2025-07-01"),("2025_H2","2025-07-01","2026-01-01")]
# Only 48 configurations (3 families x 2 entry TF x 2 lookbacks x 2 ATR stops x 2 exits).
FAMILIES={"range_reentry":(20,40),"compression_breakout":(20,40),"expansion_breakout":(20,40)}
TFS=(60,240);STOPS=(2.,3.);RRS=(2.,0.)
# Stops are multiples of completed-bar ATR14; rr=0 means a ratcheting trail.
# Fixed common risk policy chosen in advance, not searched.
def ist(s):return pd.Timestamp(s,tz=IST).tz_convert("UTC")
def read_frame(p):
    z=pd.read_csv(p)
    t=z.pop("time")
    z.index=pd.to_datetime(t,unit="s",utc=True) if pd.api.types.is_numeric_dtype(t) else pd.to_datetime(t,utc=True)
    # Native mark/funding archives can carry nullable optional volume or metadata.
    # Only traded OHLCV and auxiliary OHLC are used; never drop required rows.
    traded=(p.parent.name in ("1m","trade_1m"))
    cols=["open","high","low","close"]+(["volume"] if traded else [])
    z=z[cols].apply(pd.to_numeric,errors="raise")
    assert not z.index.has_duplicates,(str(p),"duplicate timestamp")
    assert np.isfinite(z.to_numpy(float)).all(),(str(p),"nonfinite required OHLCV",z.isna().sum().to_dict())
    return z.sort_index()
def bridge(label,symbol,step):
    # IST archive ends 18:30 UTC; 2025 archive begins midnight UTC.
    # Funding archive ends at 17:00; fill six preceding hours from native API.
    a=int(pd.Timestamp("2024-12-31 18:30" if step==60 else "2024-12-31 18:00",tz="UTC").timestamp())
    b=int(pd.Timestamp("2025-01-01",tz="UTC").timestamp())
    expected=set(range(a,b,step));rows={}
    for pad in (step,3600,7200,18000):
        url="https://api.india.delta.exchange/v2/history/candles?"+urllib.parse.urlencode(dict(symbol=symbol,resolution="1m" if step==60 else "1h",start=a-pad,end=b+pad))
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"BTC-Analysis-research/1.0","Accept":"application/json"}),timeout=45) as resp:d=json.load(resp)
            for r in d["result"]:
                t=int(r["time"])
                if t in expected:
                    cols=["open","high","low","close"]+(["volume"] if label=="trade_1m" else [])
                    rows[t]={c:float(r[c]) for c in cols}
        except Exception as exc:print("BRIDGE_RETRY",label,str(exc),flush=True)
        if set(rows)==expected:break
        time.sleep(1)
    assert set(rows)==expected,(label,len(rows),len(expected))
    z=pd.DataFrame.from_dict(rows,orient="index").sort_index()
    z.index=pd.to_datetime(z.index,unit="s",utc=True)
    return z
def load(stage):
    result={}
    manifest=json.loads((ARCH/"manifest.json").read_text()) if stage=="train" else None
    for label,symbol,step in (("trade_1m","BTCUSD",60),("mark_1m","MARK:BTCUSD",60),("funding_1h","FUNDING:BTCUSD",3600)):
        paths=ROOT/"1m" if label=="trade_1m" else ROOT/"institutional/history"/label
        parts=[]
        if stage=="train":
            for item in manifest["months"]:
                if item["series"]==label:
                    p=ARCH/label/(item["month"]+".csv.gz")
                    assert hashlib.sha256(p.read_bytes()).hexdigest()==item["sha256"]
                    parts.append(read_frame(p))
            parts.append(bridge(label,symbol,step))
            files=sorted(paths.glob("2025-*.csv.gz"))
            start=TRAIN_START;end=TRAIN_END
        else:
            files=[paths/"2025-12.csv.gz"]+sorted(paths.glob("2026-*.csv.gz"))
            start=pd.Timestamp("2025-12-02",tz="UTC");end=VALID_END
        parts.extend(read_frame(p) for p in files)
        z=pd.concat(parts).sort_index()
        # Prior funding observation for the first execution hour.
        a=start-pd.Timedelta(hours=1) if step==3600 else start
        z=z.loc[(z.index>=a)&(z.index<(end.floor("h") if step==3600 else end))]
        # End of IST year is half-hour UTC; funding needs only prior hours.
        expected=pd.date_range(a,end-pd.Timedelta(seconds=step),freq="min" if step==60 else "h")
        if step==3600:expected=pd.date_range(a,end.floor("h")-pd.Timedelta(hours=1),freq="h")
        assert z.index.equals(expected),(label,stage,len(z),len(expected),str(expected.difference(z.index)[:10]))
        assert ((z.low<=z[["open","close"]].min(axis=1))&(z.high>=z[["open","close"]].max(axis=1))).all(),label
        result[label]=z
    m=result["trade_1m"];mk=result["mark_1m"];fr=result["funding_1h"]
    previous=fr.reindex(m.index.floor("h")-pd.Timedelta(hours=1))
    assert not previous.isna().any().any()
    local=m.index.tz_convert(IST)
    ctx=dict(op=m.open.to_numpy(float),hi=m.high.to_numpy(float),lo=m.low.to_numpy(float),cl=m.close.to_numpy(float),mo=mk.open.to_numpy(float),mh=mk.high.to_numpy(float),ml=mk.low.to_numpy(float),rate=previous.close.to_numpy(float)/100,adverse_long=np.maximum(previous.high.to_numpy(float)/100,0),adverse_short=np.minimum(previous.low.to_numpy(float)/100,0),weekday=local.dayofweek.to_numpy(),day=np.asarray(local.strftime("%Y%m%d"),dtype=np.int32),sw=int(m.index.searchsorted(pd.Timestamp("2025-09-08 16:00",tz="UTC"))),end=len(m))
    return m,ctx
def signals(m,family,tf,n):
    z=m.resample(f"{tf}min").agg(open=("open","first"),high=("high","max"),low=("low","min"),close=("close","last"),volume=("volume","sum"),count=("close","count"))
    z=z[z["count"]==tf]
    c=z.close;prev=c.shift(1);body=(c-z.open)/(z.high-z.low).clip(lower=1e-10)
    # Three price-structure hypotheses, independent of the failed EMA/RSI stack.
    upper=z.high.shift(1).rolling(n).max()
    lower=z.low.shift(1).rolling(n).min()
    tr=pd.concat([z.high-z.low,(z.high-prev).abs(),(z.low-prev).abs()],axis=1).max(axis=1)
    prior_atr=tr.ewm(alpha=1/14,adjust=False,min_periods=14).mean().shift(1)
    if family=="range_reentry":
        # Fade an excursion that closes back inside the prior range.
        # Low prior directional efficiency is an objective range regime.
        eff=(c.shift(1)-c.shift(n+1)).abs()/c.diff().abs().shift(1).rolling(n).sum().replace(0,np.nan)
        up=(eff<.3)&(z.low<lower)&(c>lower)&(c>z.open)
        dn=(eff<.3)&(z.high>upper)&(c<upper)&(c<z.open)
    elif family=="compression_breakout":
        # Compare prior channel width with its own preceding history.
        width=(upper-lower)/prev
        compressed=width<width.shift(1).rolling(100).quantile(.3)
        up=compressed&(c>upper)
        dn=compressed&(c<lower)
    elif family=="expansion_breakout":
        expansion=(tr>=1.5*prior_atr)
        up=expansion&(c>upper)
        dn=expansion&(c<lower)
    else:raise ValueError(family)
    both=up&dn
    up=up&~both;dn=dn&~both
    events=[]
    for i in np.flatnonzero((up|dn).to_numpy()):
        j=int(m.index.searchsorted(z.index[i]+pd.Timedelta(minutes=tf)))
        if j<len(m) and m.index[j].tz_convert(IST).dayofweek<5:
            events.append((j,1 if up.iat[i] else -1,0,0))
    return np.asarray(events,dtype=np.int64).reshape((-1,4))
def atr_series(m,tf):
    z=m.resample(f"{tf}min").agg(high=("high","max"),low=("low","min"),close=("close","last"),count=("close","count"))
    z=z[z["count"]==tf]
    prev=z.close.shift(1)
    tr=pd.concat([z.high-z.low,(z.high-prev).abs(),(z.low-prev).abs()],axis=1).max(axis=1)
    atr=tr.ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    atr.index=atr.index+pd.Timedelta(minutes=tf)
    return atr.reindex(m.index,method="ffill").to_numpy(float)

@njit
def core(op,hi,lo,cl,mo,mh,ml,rate,al,ash,weekday,day,month,sw,events,end,lev,isolated,stopfrac,tp,cost,es,xs,delay,fee,mmr,shock,sd,mode,atr,atr_mode):
    eq=peak=mp=100.;dd=ddp=mdd=mddp=0.;pos=-1;liq=n=w=reject=0;bufmin=1e30;maxeff=0.
    usd=np.zeros(23);points=np.zeros(23)
    for i in range(len(events)):
        orig=events[i,0];side=events[i,1];j=orig+delay
        if j>=end or j<=pos or weekday[j]>=5 or day[j]!=day[orig]:continue
        ep=op[j]+side*es
        distance=ep*(1./50-FEE-MMR)/(1.-side*MMR)
        if atr_mode and (not np.isfinite(atr[orig]) or atr[orig]<=0):continue
        planned=atr[orig]*stopfrac if atr_mode else distance*stopfrac
        reserve=250.+2*fee*ep+max(mh[j-1]-ml[j-1],mh[j-2]-ml[j-2])
        target_notional=min(10.*lev,eq*CAP,eq*RISK*ep/max(1.,planned+reserve))
        lots=int(target_notional/(ep*.001));qty=lots*.001
        imr=1./lev if isolated else 1./200.
        initial=qty*ep*imr;entryfee=qty*ep*fee
        if qty<=0 or eq<=0 or eq<initial+2*entryfee:
            reject+=1;continue
        collateral=initial if isolated else eq
        maxeff=max(maxeff,qty*ep/eq)
        stop=ep-side*planned;target=(ep+side*planned*tp if atr_mode else ep*(1+side*tp/100.))
        best=ep
        fund=early=0.;reason=3;trigger=-1
        x=min(j+(10080 if atr_mode else 4320)-1,end-1);xp=cl[x]-side*xs;m=month[j]
        for k in range(j,x+1):
            if k>j and (k<sw or k%480==0):
                r=rate[k] if mode==0 else (al[k] if side==1 else ash[k])
                f=-side*mo[k]*r/(480. if k<sw else 1.)
                fund+=f
                if month[k]==m:early+=f
            adverse=(ml[k] if side==1 else mh[k])-side*shock
            favorable=mh[k] if side==1 else ml[k]
            buf=collateral-entryfee+qty*(fund+side*(adverse-ep)-mmr*adverse)
            bufmin=min(bufmin,buf)
            feq=eq+qty*(fund+side*(favorable-ep)-fee*(ep+favorable)-cost)
            aeq=eq+qty*(fund+side*(adverse-ep)-fee*(ep+adverse)-cost)
            mp=max(mp,feq);mdd=max(mdd,mp-aeq);mddp=max(mddp,100*(mp-aeq)/max(mp,1e-12))
            if buf<=0:
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
            if (not atr_mode or tp>0) and (hi[k]>=target if side==1 else lo[k]<=target):
                x=k;xp=target-side*xs;reason=2;break
            # A new trail is only active on the NEXT minute; adverse-first fills.
            if atr_mode and tp==0:
                best=max(best,hi[k]) if side==1 else min(best,lo[k])
                new_stop=best-side*planned
                stop=max(stop,new_stop) if side==1 else min(stop,new_stop)
        normal=qty*(side*(xp-ep)-fee*(ep+xp)+fund-cost)
        net=max(-eq,-collateral-entryfee-qty*cost) if reason==4 else max(-eq,normal)
        prior=early if month[x]!=m else 0.
        usd[m]+=prior*qty;usd[month[x]]+=net-prior*qty
        points[m]+=prior;points[month[x]]+=net/qty-prior
        eq+=net;peak=max(peak,eq);dd=max(dd,peak-eq);ddp=max(ddp,100*(peak-eq)/peak)
        mp=max(mp,eq);mdd=max(mdd,mp-eq);mddp=max(mddp,100*(mp-eq)/max(mp,1e-12))
        pos=x;n+=1;w+=int(net>0)
    return eq,dd,ddp,mdd,mddp,n,w,liq,reject,bufmin,maxeff,usd,points
def period(m,ctx,ev,start,end):
    a=ist(start);b=ist(end) if isinstance(end,str) else end
    first=int(m.index.searchsorted(a));last=int(m.index.searchsorted(b))
    assert first>=2 and last>first and m.index[first]==a
    local=m.index.tz_convert(IST)
    base=local[first].year*12+local[first].month
    months=np.asarray(local.year*12+local.month-base,dtype=np.int32)
    events=ev[(ev[:,0]>=first)&(ev[:,0]<last)]
    # Mark day and funding clock unchanged; months relative to this fold.
    return months,events,last,int(months[last-1])+1
def run(ctx,period,cfg,lev,sc,mode,isolated=False,legacy=False):
    month,ev,end,nm=period
    name,cost,es,xs,delay,fee,mmr,shock,sd=sc
    stopfrac=cfg["stop_fraction"];tp=100*(1./50-FEE-MMR)*stopfrac*cfg["rr"] if legacy else cfg["rr"]
    eq,dd,ddp,mdd,mddp,n,w,liq,reject,buf,maxeff,usd,pts=core(*[ctx[k] for k in ("op","hi","lo","cl","mo","mh","ml","rate","adverse_long","adverse_short","weekday","day")],month,ctx["sw"],ev,end,lev,isolated,stopfrac,tp,cost,es,xs,delay,fee,mmr,shock,sd,mode,ctx["atr"][cfg["timeframe"]],not legacy)
    opening=100+np.r_[0.,np.cumsum(usd)[:-1]]
    ret=np.divide(100*usd,opening,out=np.zeros_like(usd),where=opening>0)
    assert abs(100+usd.sum()-eq)<1e-6
    return dict(signal_count=len(ev),signals_not_executed=int(len(ev)-n-reject),net_usd=float(eq-100),ending_equity=float(eq),closed_dd_usd=float(dd),closed_dd_pct=float(ddp),mark_dd_upper_usd=float(mdd),mark_dd_upper_pct=float(mddp),trades=int(n),wins=int(w),liquidations=int(liq),rejected=int(reject),max_effective_leverage=float(maxeff),min_margin_buffer=None if n==0 else float(buf),months=int(nm),positive_months=int((ret[:nm]>0).sum()),months_ge_1pct=int((ret[:nm]>=1).sum()),monthly_returns=ret[:nm],monthly_usd=usd[:nm],monthly_points=pts[:nm])
def profile(cfg):
    return dict(legs=[dict(stop_fraction=cfg["stop_fraction"],tp_pct=100*(1./50-FEE-MMR)*cfg["stop_fraction"]*cfg["rr"],max_minutes=4320,trail_fraction=0,mtd_gate=1e30)],daily_limit=0,month_ceiling=1e30,loss_guard=1e30)
def parity(ctx,per,cfg,lev,sc,mode):
    # Check the accelerated single-setup engine against existing V24
    # independent Python account simulator on identical causal signals.
    month,events,end,nm=per;cc=dict(ctx,month=month,end=end)
    ref=old.simulate(cc,profile(cfg),events,lev,"cross","fixed_10_margin_budget",sc,mode,dict(risk_pct=RISK,max_eff=CAP))
    got=run(ctx,per,cfg,lev,sc,mode,legacy=True)
    for k in ("net_usd","closed_dd_usd","closed_dd_pct","mark_dd_upper_usd","mark_dd_upper_pct","trades","wins","liquidations"):
        assert abs(ref[k]-got[k])<1e-6,(k,ref[k],got[k])
    assert np.allclose(ref["monthly_usd"][:nm],got["monthly_usd"])
def train():
    m,ctx=load("train")
    ctx["atr"]={tf:atr_series(m,tf) for tf in TFS}
    entries={(f,tf,n):signals(m,f,tf,n) for f,ns in FAMILIES.items() for tf in TFS for n in ns}
    # Diagnostic independent of account sizing and stop/target tuning.
    # Nonoverlapping 24h/72h fixed-horizon returns, net of fee and 210 points;
    # funding omitted ONLY in this diagnostic, not the account replay.
    diagnostics=[]
    for (f,tf,n),ev in entries.items():
        for label,a,b in FOLDS:
            first=int(m.index.searchsorted(ist(a)));last=int(m.index.searchsorted(ist(b)))
            for horizon in (1440,4320):
                returns=[];end_prev=-1
                for j,side,_,_ in ev:
                    if j<first or j<=end_prev or j+horizon>=last:continue
                    ep=ctx["op"][j];xp=ctx["op"][j+horizon]
                    returns.append(100*(side*(xp-ep)-FEE*(ep+xp)-210.)/ep)
                    end_prev=j+horizon
                diagnostics.append(dict(family=f,timeframe=tf,lookback=n,fold=label,horizon_minutes=horizon,trades=len(returns),mean_net_pct=float(np.mean(returns)) if returns else None,median_net_pct=float(np.median(returns)) if returns else None,positive_fraction=float(np.mean(np.asarray(returns)>0)) if returns else None))
    pd.DataFrame(diagnostics).to_csv(OUT/"entry_edge_diagnostic.csv",index=False)
    configs=[];rows=[];metrics=[]
    for f,tf,n in entries:
        ev=entries[(f,tf,n)]
        periods=[(label,period(m,ctx,ev,a,b)) for label,a,b in FOLDS]
        for sf,rr in itertools.product(STOPS,RRS):
            cfg=dict(family=f,timeframe=tf,lookback=n,stop_fraction=sf,rr=rr)
            cid=len(configs);configs.append(cfg);rrs=[]
            if cid==0:
                # Exact legacy parity before using the new ATR path.
                for _,p in periods[:1]:
                    for sc,mode in ((SC[0],0),(SC[1],1)):parity(ctx,p,cfg,50,sc,mode)
            full=period(m,ctx,ev,"2024-02-01","2026-01-01")
            for (label,p),lev,(sc,mode) in itertools.product(periods+[("continuous",full)],(20,50,200),((SC[0],0),(SC[1],1))):
                r=run(ctx,p,cfg,lev,sc,mode)
                years=(float(r["monthly_usd"][:11].sum()),float(r["monthly_usd"][11:].sum())) if label=="continuous" else (0.,0.)
                r={k:v for k,v in r.items() if not k.startswith("monthly_")}
                r.update(year2024_usd=years[0],year2025_usd=years[1])
                rr0=dict(config=cid,fold=label,leverage=lev,scenario=sc[0],funding_mode=mode,**r);rrs.append(rr0);rows.append(rr0)
            # Both years / all four chronological blocks / stressed costs.
            # No calendar-specific adjustment; require meaningful activity.
            valid=all(r["liquidations"]==0 and r["trades"]>=max(4,r["months"]*2) and r["net_usd"]>0 and (r["fold"]!="continuous" or min(r["year2024_usd"],r["year2025_usd"])>0) for r in rrs)
            min_return=min(r["net_usd"] for r in rrs);worst_dd=max(r["mark_dd_upper_pct"] for r in rrs)
            min_month=min(r["months_ge_1pct"]/r["months"] for r in rrs)
            pos_ratio=sum(r["net_usd"]>0 for r in rrs)/len(rrs)
            mean_month=np.mean([r["months_ge_1pct"]/r["months"] for r in rrs])
            continuous=[r for r in rrs if r["fold"]=="continuous"]
            min_year=min(min(r["year2024_usd"],r["year2025_usd"]) for r in continuous)
            base50=next(r for r in continuous if r["leverage"]==50 and r["scenario"]=="base" and r["funding_mode"]==0)
            # Training-only promotion gate versus V33. Do not lower the risk bar.
            valid=valid and base50["net_usd"]>6.669577955892976 and base50["months_ge_1pct"]>3 and base50["closed_dd_pct"]<=9.151042470129736
            continuous_month_min=min(r["months_ge_1pct"]/23 for r in continuous)
            continuous_positive_min=min(r["positive_months"]/23 for r in continuous)
            continuous_trades_min=min(r["trades"] for r in continuous)
            # Bounded score: reward distributed wins and penalize drawdown,
            # use neighbor quartile to suppress isolated parameter spikes.
            score=float(2*pos_ratio+2*mean_month+min_month+2*continuous_month_min+continuous_positive_min+min_year/100+min_return/100-worst_dd/100)
            metrics.append(dict(config=cid,valid=valid,min_profit=min_return,worst_dd=worst_dd,min_month_fraction=min_month,mean_month_fraction=float(mean_month),positive_fold_fraction=pos_ratio,continuous_month_min=continuous_month_min,continuous_positive_min=continuous_positive_min,continuous_trades_min=continuous_trades_min,min_year_profit=min_year,score=score))
        print("TRAIN_FAMILY",f,tf,n,"configurations",len(configs),flush=True)
        pd.DataFrame(rows).to_csv(OUT/"training_folds.csv",index=False)
    for i,c in enumerate(configs):
        neighbors=[]
        for j,d in enumerate(configs):
            if c["family"]!=d["family"]:continue
            if sum(c[k]!=d[k] for k in ("timeframe","lookback","stop_fraction","rr"))==1 and abs(TFS.index(c["timeframe"])-TFS.index(d["timeframe"]))<=1:neighbors.append(j)
        met=metrics[i];met["neighbor_q25"]=float(np.quantile([metrics[j]["score"] for j in neighbors]+[met["score"]],.25));met["neighbor_valid_fraction"]=float(np.mean([metrics[j]["valid"] for j in neighbors]))
        met["robust_score"]=min(met["score"],met["neighbor_q25"])
    order=sorted(range(len(configs)),key=lambda i:(metrics[i]["valid"],metrics[i]["robust_score"],metrics[i]["neighbor_valid_fraction"],metrics[i]["min_profit"],-metrics[i]["worst_dd"]),reverse=True)
    best=order[0];chosen=configs[best]
    pd.DataFrame([dict(**configs[i],**metrics[i],rank=rank+1) for rank,i in enumerate(order)]).to_csv(OUT/"training_ranking.csv",index=False)
    frozen=dict(config=chosen,training_metrics=metrics[best],grid_size=len(configs),training_period="2024-02 through 2025-12",folds=FOLDS,risk_pct=RISK,max_effective_exposure=CAP,max_hold_minutes=10080,stop_definition="ATR14 from last completed signal-timeframe candle",exit_definition="2R fixed target or same-distance ratcheting stop",weekdays_only=True,one_position=True,no_monthly_gates=True,no_daily_limit=True,no_leverage_tuning=True,training_pass=bool(metrics[best]["valid"]),promotion_gate=dict(min_net_usd_exclusive=6.669577955892976,min_months_ge_1pct_exclusive=3,max_closed_dd_pct=9.151042470129736),holdout_previously_examined=True,regime_filter=None,research_batch='V36; independent range reentry, compression breakout and expansion breakout; 48 candidates, fixed-horizon entry diagnostic, same training gate',warmup_limited=True,warmup_start=str(TRAIN_START))
    (OUT/"frozen.json").write_text(json.dumps(frozen,indent=2))
    print("FROZEN",json.dumps(frozen),flush=True)
    # Full training replay (continuous, no resets) after selecting on folds.
    ev=entries[(chosen["family"],chosen["timeframe"],chosen["lookback"])]
    full_period=period(m,ctx,ev,"2024-02-01","2026-01-01")
    report(ctx,full_period,chosen,"training","2024-02")
def report(ctx,p,cfg,stage,start):
    rows=[];months=[]
    for lev,sc,mode in itertools.product(old.LEVS,old.SCENARIOS,(0,1)):
        r=run(ctx,p,cfg,lev,sc,mode)
        re=r.pop("monthly_returns");us=r.pop("monthly_usd");pt=r.pop("monthly_points")
        tag=dict(leverage=lev,scenario=sc[0],funding_mode=mode,margin_mode="cross")
        rows.append(dict(**tag,**r))
        months.extend(dict(**tag,month=str(pd.Period(start,freq="M")+i),net_usd=us[i],return_pct=re[i],net_points=pt[i]) for i in range(len(re)))
    pd.DataFrame(rows).to_csv(OUT/(stage+"_summary.csv"),index=False);pd.DataFrame(months).to_csv(OUT/(stage+"_monthly.csv"),index=False)
def validate():
    p=OUT/"frozen.json";sha=hashlib.sha256(p.read_bytes()).hexdigest()
    frozen=json.loads(p.read_text());cfg=frozen["config"]
    if not frozen["training_pass"]:
        print("NO TRAINING PASS; 2026 not evaluated",flush=True)
        return
    m,ctx=load("validate")
    ctx["atr"]={tf:atr_series(m,tf) for tf in TFS}
    ev=signals(m,cfg["family"],cfg["timeframe"],cfg["lookback"])
    pp=period(m,ctx,ev,"2026-01-01",VALID_END)
    report(ctx,pp,cfg,"validation","2026-01")
    # Separate complete-month validation report; November is not a full month.
    report(ctx,period(m,ctx,ev,"2026-01-01","2026-11-01"),cfg,"validation_full_months","2026-01")
    assert hashlib.sha256(p.read_bytes()).hexdigest()==sha
    (OUT/"validation_quality.json").write_text(json.dumps(dict(frozen_sha256=sha,config=cfg,training_pass=frozen["training_pass"],validation_period="2026-01-01 IST through 2026-11-17 UTC; November partial",validation_used_for_selection=False,prior_2026_research_exists=True,funding_proxy=True,liquidation_proxy=True,live_execution=False,scenario_rows=len(old.LEVS)*len(old.SCENARIOS)*2),indent=2))
if __name__=="__main__":
    if sys.argv[1]=="train":train()
    elif sys.argv[1]=="validate":validate()
    else:raise SystemExit("train or validate")
