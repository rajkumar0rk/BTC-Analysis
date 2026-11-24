#!/usr/bin/env python3
"""V49: one causal delayed retry of a risk-rejected V42 breakout. Training only."""
import sys,json,hashlib,urllib.request,urllib.parse,time,itertools
from pathlib import Path
import numpy as np
import pandas as pd
from numba import njit
import research_v24_common_drawdown_control as old
OUT=Path("analysis/v49_risk_retry");OUT.mkdir(parents=True,exist_ok=True)
ROOT=Path("data/delta_india/BTCUSD")
ARCH=ROOT/"2024_verified_archive"
IST="Asia/Kolkata";FEE=.00059;MMR=.0025;RISK=.03;CAP=3.
TRAIN_START=pd.Timestamp("2024-01-30",tz="UTC")
TRAIN_END=pd.Timestamp("2026-01-01",tz=IST).tz_convert("UTC")
VALID_END=pd.Timestamp("2026-11-18",tz="UTC")
SC=[s for s in old.SCENARIOS if s[0] in ("base","combined")]
FOLDS=[("2024_H1","2024-02-01","2024-07-01"),("2024_H2","2024-07-01","2025-01-01"),("2025_H1","2025-01-01","2025-07-01"),("2025_H2","2025-07-01","2026-01-01")]
# Six configurations: V38, V42 and four prespecified progressive trailing profiles.
FAMILIES={"expansion_breakout":(20,)}
TFS=(240,);STOPS=(3.,);RRS=(0.,)
EXIT_KINDS=("fixed_atr","dynamic_atr","breakeven_1r","lock_1r_at_2r","channel10","channel20")
HOLDS=(10080,)
ACTIVATIONS=(1.,)
LOCKS=(0.,)
FLOORS=(1.5,2.)
CONTRACTION_HOURS=(12,24,48)
CONTRACTION_RATIOS=(.75,.9)
PROGRESS_HOURS=(24,48,72)
TRAIL_PROFILES=((2.5,2.5),(2.,2.),(2.5,2.),(2.,1.5))
EARLY_VARIANTS=[("none",0.,24,3.,3.),("contraction",.75,24,3.,3.)]+[("contraction",.75,24,a,b) for a,b in TRAIL_PROFILES]
EARLY_KINDS=("none","failed","opposite","contraction")
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
    elif family=="expansion_breakout" or family.startswith(("retest","follow")):
        expansion=(tr>=1.5*prior_atr)
        up=expansion&(c>upper)
        dn=expansion&(c<lower)
    else:raise ValueError(family)
    both=up&dn
    up=up&~both;dn=dn&~both
    events=[]
    for i in np.flatnonzero((up|dn).to_numpy()):
        side=1 if up.iat[i] else -1
        entry_i=i
        if family.startswith(("retest","follow")):
            window=int(family[-1])
            level=upper.iat[i] if side==1 else lower.iat[i]
            breakout_close=c.iat[i]
            entry_i=-1
            for k in range(i+1,min(i+window+1,len(z))):
                # Cancel on a close back inside the original channel.
                if side*(c.iat[k]-level)<=0:break
                if family.startswith("retest"):
                    touched=z.low.iat[k]<=level if side==1 else z.high.iat[k]>=level
                    confirmed=touched and side*(c.iat[k]-z.open.iat[k])>0
                else:
                    confirmed=side*(c.iat[k]-breakout_close)>0
                if confirmed:
                    entry_i=k;break
            if entry_i<0:continue
        # Signal is available only at the confirmation candle close.
        j=int(m.index.searchsorted(z.index[entry_i]+pd.Timedelta(minutes=tf)))
        if j<len(m) and m.index[j].tz_convert(IST).dayofweek<5:
            events.append((j,side,0,0))
    # Multiple earlier breakouts can resolve on one confirmation candle.
    # Keep one same-side signal, discard opposite-side conflicts.
    grouped={}
    for j,side,_,_ in events:
        grouped.setdefault(j,set()).add(side)
    return np.asarray([(j,next(iter(sides)),0,0) for j,sides in sorted(grouped.items()) if len(sides)==1],dtype=np.int64).reshape((-1,4))
def atr_series(m,tf):
    z=m.resample(f"{tf}min").agg(high=("high","max"),low=("low","min"),close=("close","last"),count=("close","count"))
    z=z[z["count"]==tf]
    prev=z.close.shift(1)
    tr=pd.concat([z.high-z.low,(z.high-prev).abs(),(z.low-prev).abs()],axis=1).max(axis=1)
    atr=tr.ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    atr.index=atr.index+pd.Timedelta(minutes=tf)
    return atr.reindex(m.index,method="ffill").to_numpy(float)

def channel_series(m,n):
    z=m.resample("240min").agg(high=("high","max"),low=("low","min"),count=("close","count"))
    z=z[z["count"]==240]
    low=z.low.rolling(n).min();high=z.high.rolling(n).max()
    low.index=low.index+pd.Timedelta(minutes=240);high.index=high.index+pd.Timedelta(minutes=240)
    return low.reindex(m.index,method="ffill").to_numpy(float),high.reindex(m.index,method="ffill").to_numpy(float)

def exit_context(m):
    z=m.resample("240min").agg(high=("high","max"),low=("low","min"),close=("close","last"),count=("close","count"))
    z=z[z["count"]==240]
    prev=z.close.shift(1)
    tr=pd.concat([z.high-z.low,(z.high-prev).abs(),(z.low-prev).abs()],axis=1).max(axis=1)
    a=tr.ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    upper=z.high.shift(1).rolling(20).max()
    lower=z.low.shift(1).rolling(20).min()
    data=pd.DataFrame(dict(close=z.close,upper=upper,lower=lower,expansion=tr/a.shift(1)))
    data.index=data.index+pd.Timedelta(minutes=240)
    aligned=data.reindex(m.index)
    # Values exist only on the first minute after a complete 4H candle.
    return tuple(aligned[k].to_numpy(float) for k in ("close","upper","lower","expansion"))

@njit
def core(op,hi,lo,cl,mo,mh,ml,rate,al,ash,weekday,day,month,sw,events,end,lev,isolated,stopfrac,tp,cost,es,xs,delay,fee,mmr,shock,sd,mode,atr,atr_mode,exit_kind,hold,channel_low,channel_high,activation,lock_r,affordable_floor,adapt_trail,early_kind,early_param,early_hours,bar_close,bar_upper,bar_lower,bar_expansion,progress_hours,trail_half,trail_one):
    eq=peak=mp=100.;dd=ddp=mdd=mddp=0.;pos=-1;liq=n=w=reject=0;bufmin=1e30;maxeff=0.
    usd=np.zeros(23);points=np.zeros(23)
    risk_rejected=budget_rejected=margin_rejected=adapted=early_exits=0;max_planned_risk_pct=0.
    # Ledger: signal status, entry/exit minute, prices, risk distance, qty,
    # completed pre-exit MFE/MAE in R, net PnL, exit reason, blocking exit index.
    ledger=np.full((len(events),12),np.nan)
    progress_exits=0
    pending_risk=-1
    for i in range(len(events)):
        orig=events[i,0];side=events[i,1];j=orig+delay
        ledger[i,0]=0
        if events[i,3]==1:
            if pending_risk!=events[i,2]:continue
            pending_risk=-1
        else:
            pending_risk=-1
        if j>=end or weekday[j]>=5 or day[j]!=day[orig]:continue
        if j<=pos:
            ledger[i,0]=1;ledger[i,11]=pos;continue
        ep=op[j]+side*es
        distance=ep*(1./50-FEE-MMR)/(1.-side*MMR)
        if atr_mode and (not np.isfinite(atr[orig]) or atr[orig]<=0):continue
        planned=atr[orig]*stopfrac if atr_mode else distance*stopfrac
        reserve=250.+2*fee*ep+max(mh[j-1]-ml[j-1],mh[j-2]-ml[j-2])
        original_planned=planned
        # Only rescue a signal that cannot afford even one whole contract.
        # Keep lot size, account risk, exposure, and reserve unchanged.
        if atr_mode and affordable_floor>0 and eq>0 and .001*(planned+reserve)>eq*RISK and min(10.*lev,eq*CAP)>=ep*.001:
            affordable=eq*RISK/.001-reserve
            if affordable>=affordable_floor*atr[orig]:
                planned=min(planned,affordable*(1.-1e-10))
        target_notional=min(10.*lev,eq*CAP,eq*RISK*ep/max(1.,planned+reserve))
        lots=int(target_notional/(ep*.001));qty=lots*.001
        imr=1./lev if isolated else 1./200.
        initial=qty*ep*imr;entryfee=qty*ep*fee
        if qty<=0 or eq<=0 or eq<initial+2*entryfee:
            reject+=1;ledger[i,0]=2
            if eq<=0 or eq<initial+2*entryfee:margin_rejected+=1
            elif min(10.*lev,eq*CAP)<ep*.001:budget_rejected+=1
            else:
                risk_rejected+=1
                if events[i,3]==0:pending_risk=orig
            continue
        planned_risk=100*qty*(planned+reserve)/eq
        max_planned_risk_pct=max(max_planned_risk_pct,planned_risk)
        if planned<original_planned:adapted+=1
        trail_distance=planned if adapt_trail else original_planned
        collateral=initial if isolated else eq
        maxeff=max(maxeff,qty*ep/eq)
        stop=ep-side*planned;target=(ep+side*planned*tp if atr_mode else ep*(1+side*tp/100.))
        best=ep
        audit_mfe=0.;audit_mae=0.
        breakout_level=bar_upper[orig] if side==1 else bar_lower[orig]
        fund=early=0.;reason=3;trigger=-1
        x=min(j+(hold if atr_mode else 4320)-1,end-1);xp=cl[x]-side*xs;m=month[j]
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
            # At a completed 4H boundary, after conservative adverse-first
            # stop/liquidation checks, discretionary exit uses next open.
            # Honor the same scenario execution delay as entry.
            signal_k=k-delay
            if atr_mode and early_kind>0 and k>j and signal_k>orig and np.isfinite(bar_close[signal_k]):
                cc=bar_close[signal_k]
                invalid=False
                if early_kind==1:
                    invalid=side*(cc-breakout_level)<-early_param*atr[orig]
                elif early_kind==2:
                    opposite=(cc<bar_lower[signal_k] if side==1 else cc>bar_upper[signal_k])
                    invalid=opposite and bar_expansion[signal_k]>=early_param
                elif early_kind==3:
                    invalid=k-j>=early_hours*60 and atr[signal_k]<=early_param*atr[orig]
                if invalid:
                    x=k;xp=op[k]-side*xs;reason=5;early_exits+=1;break
            # The no-progress rule uses only prior completed minute excursions
            # and acts at a completed H4 boundary with scenario delay.
            if atr_mode and progress_hours>0 and k>j and signal_k>orig and np.isfinite(bar_close[signal_k]) and k-j>=progress_hours*60 and side*(best-ep)<.5*planned:
                x=k;xp=op[k]-side*xs;reason=6;progress_exits+=1;break
            # Exclude the exit minute from excursion diagnostics: OHLC ordering unknown.
            audit_mfe=max(audit_mfe,side*((hi[k] if side==1 else lo[k])-ep)/planned)
            audit_mae=max(audit_mae,side*(ep-(lo[k] if side==1 else hi[k]))/planned)
            # A new trail is only active on the NEXT minute; adverse-first fills.
            if atr_mode and tp==0:
                best=max(best,hi[k]) if side==1 else min(best,lo[k])
                # Never widen the original risk. Tightening is effective next minute.
                active_distance=trail_distance
                if trail_one<3. and side*(best-ep)>=planned:
                    active_distance=min(active_distance,trail_one*atr[orig])
                elif trail_half<3. and side*(best-ep)>=.5*planned:
                    active_distance=min(active_distance,trail_half*atr[orig])
                new_stop=best-side*active_distance
                if exit_kind==1 and np.isfinite(atr[k]):
                    new_stop=best-side*stopfrac*atr[k]
                elif exit_kind==2 and side*(best-ep)>=activation*planned:
                    # Approximate cost-inclusive breakeven, only active next minute.
                    be=ep+side*(cost+2*fee*ep+xs-fund+lock_r*planned)
                    new_stop=max(new_stop,be) if side==1 else min(new_stop,be)
                elif exit_kind==3 and side*(best-ep)>=2*planned:
                    lock=ep+side*planned
                    new_stop=max(new_stop,lock) if side==1 else min(new_stop,lock)
                elif exit_kind==4 or exit_kind==5:
                    level=channel_low[k] if side==1 else channel_high[k]
                    new_stop=level if np.isfinite(level) else stop
                stop=max(stop,new_stop) if side==1 else min(stop,new_stop)
        normal=qty*(side*(xp-ep)-fee*(ep+xp)+fund-cost)
        net=max(-eq,-collateral-entryfee-qty*cost) if reason==4 else max(-eq,normal)
        prior=early if month[x]!=m else 0.
        usd[m]+=prior*qty;usd[month[x]]+=net-prior*qty
        points[m]+=prior;points[month[x]]+=net/qty-prior
        eq+=net;peak=max(peak,eq);dd=max(dd,peak-eq);ddp=max(ddp,100*(peak-eq)/peak)
        mp=max(mp,eq);mdd=max(mdd,mp-eq);mddp=max(mddp,100*(mp-eq)/max(mp,1e-12))
        ledger[i,0]=3;ledger[i,1]=j;ledger[i,2]=x;ledger[i,3]=ep;ledger[i,4]=xp;ledger[i,5]=planned;ledger[i,6]=qty;ledger[i,7]=audit_mfe;ledger[i,8]=audit_mae;ledger[i,9]=net;ledger[i,10]=reason
        pos=x;n+=1;w+=int(net>0)
    return eq,dd,ddp,mdd,mddp,n,w,liq,reject,bufmin,maxeff,usd,points,risk_rejected,budget_rejected,margin_rejected,adapted,max_planned_risk_pct,early_exits,progress_exits,ledger
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
def run(ctx,period,cfg,lev,sc,mode,isolated=False,legacy=False,audit=False):
    month,ev,end,nm=period
    name,cost,es,xs,delay,fee,mmr,shock,sd=sc
    stopfrac=cfg["stop_fraction"];tp=100*(1./50-FEE-MMR)*stopfrac*cfg["rr"] if legacy else cfg["rr"]
    eq,dd,ddp,mdd,mddp,n,w,liq,reject,buf,maxeff,usd,pts,risk_rej,budget_rej,margin_rej,adapted,maxrisk,early_exits,progress_exits,ledger=core(*[ctx[k] for k in ("op","hi","lo","cl","mo","mh","ml","rate","adverse_long","adverse_short","weekday","day")],month,ctx["sw"],ev,end,lev,isolated,stopfrac,tp,cost,es,xs,delay,fee,mmr,shock,sd,mode,ctx["atr"][cfg["timeframe"]],not legacy,EXIT_KINDS.index(cfg.get("exit_kind","fixed_atr")),cfg.get("hold_minutes",10080),*ctx["channels"][20 if cfg.get("exit_kind")=="channel20" else 10],cfg.get("activation_r",1.),cfg.get("lock_r",0.),cfg.get("affordable_floor",0.),cfg.get("adapt_trail",False),EARLY_KINDS.index(cfg.get("early_kind","none")),cfg.get("early_param",0.),cfg.get("early_hours",24),*ctx["exit_context"],cfg.get("progress_hours",0),cfg.get("trail_half",3.),cfg.get("trail_one",3.))
    opening=100+np.r_[0.,np.cumsum(usd)[:-1]]
    ret=np.divide(100*usd,opening,out=np.zeros_like(usd),where=opening>0)
    assert abs(100+usd.sum()-eq)<1e-6
    assert risk_rej+budget_rej+margin_rej==reject
    assert maxrisk<=100*RISK+1e-7,(maxrisk,RISK)
    result=dict(signal_count=len(ev),signals_not_executed=int(len(ev)-n-reject),net_usd=float(eq-100),ending_equity=float(eq),closed_dd_usd=float(dd),closed_dd_pct=float(ddp),mark_dd_upper_usd=float(mdd),mark_dd_upper_pct=float(mddp),trades=int(n),wins=int(w),liquidations=int(liq),rejected=int(reject),risk_rejected=int(risk_rej),budget_rejected=int(budget_rej),margin_rejected=int(margin_rej),adapted_trades=int(adapted),early_exits=int(early_exits),progress_exits=int(progress_exits),max_planned_risk_pct=float(maxrisk),max_effective_leverage=float(maxeff),min_margin_buffer=None if n==0 else float(buf),months=int(nm),positive_months=int((ret[:nm]>0).sum()),months_ge_1pct=int((ret[:nm]>=1).sum()),monthly_returns=ret[:nm],monthly_usd=usd[:nm],monthly_points=pts[:nm])
    assert int((ledger[:,0]==3).sum())==n and int((ledger[:,0]==2).sum())==reject
    if audit:result["ledger"]=ledger
    return result
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

def retry_events(m,ctx,events,bars):
    if bars==0:return events
    close,upper,lower,_=ctx["exit_context"]
    originals=set(int(row[0]) for row in events)
    extra={}
    for j,side,_,_ in events:
        level=upper[j] if side==1 else lower[j]
        if not np.isfinite(level):continue
        target=j+240*bars
        if target>=len(m) or target in originals:continue
        if any((j+240*k in originals) or not np.isfinite(close[j+240*k]) or side*(close[j+240*k]-level)<=0 for k in range(1,bars+1)):continue
        if m.index[target].tz_convert(IST).dayofweek>=5:continue
        extra[target]=(target,side,j,1)
    return np.asarray(sorted([tuple(x) for x in events]+list(extra.values())),dtype=np.int64).reshape(-1,4)

def train():
    m,ctx=load("train")
    ctx["atr"]={240:atr_series(m,240)}
    ctx["channels"]={n:channel_series(m,n) for n in (10,20)}
    ctx["exit_context"]=exit_context(m)
    ev=signals(m,"expansion_breakout",240,20)
    cfg=dict(family="expansion_breakout",timeframe=240,lookback=20,stop_fraction=3.,rr=0.,exit_kind="breakeven_1r",hold_minutes=10080,activation_r=1.,lock_r=0.,early_kind="contraction",early_param=.75,early_hours=24)
    rows=[];months=[];audits=[]
    for bars in (0,1,2):
        events=retry_events(m,ctx,ev,bars)
        for label,a,b in FOLDS+[("continuous","2024-02-01","2026-01-01")]:
            p=period(m,ctx,events,a,b)
            for lev,(sc,mode) in itertools.product((20,50,200),((SC[0],0),(SC[1],1))):
                r=run(ctx,p,cfg,lev,sc,mode,audit=True)
                ledger=r.pop("ledger")
                us=r.pop("monthly_usd");re=r.pop("monthly_returns");r.pop("monthly_points")
                if label=="continuous":
                    r.update(year2024_usd=float(us[:11].sum()),year2025_usd=float(us[11:].sum()))
                    months.extend(dict(retry_bars=bars,leverage=lev,scenario=sc[0],month=str(pd.Period("2024-02",freq="M")+i),net_usd=v,return_pct=re[i]) for i,v in enumerate(us))
                    for e,l in zip(p[1],ledger):
                        audits.append(dict(retry_bars=bars,leverage=lev,scenario=sc[0],signal_time=str(m.index[e[0]]),parent_time=str(m.index[e[2]]) if e[3] else "",is_retry=int(e[3]),status=int(l[0]),net_usd=l[9]))
                r.update(retry_bars=bars,fold=label,leverage=lev,scenario=sc[0],executed_retries=int(((p[1][:,3]==1)&(ledger[:,0]==3)).sum()))
                rows.append(r)
        print("V49_RETRY_BARS_DONE",bars,flush=True)
    df=pd.DataFrame(rows)
    df.to_csv(OUT/"training_folds.csv",index=False)
    pd.DataFrame(months).to_csv(OUT/"training_monthly.csv",index=False)
    pd.DataFrame(audits).to_csv(OUT/"signal_audit.csv",index=False)
    full=df[df.fold=="continuous"]
    base=full[(full.retry_bars==0)&(full.leverage==50)&(full.scenario=="base")].iloc[0]
    stress=full[(full.retry_bars==0)&(full.leverage==50)&(full.scenario=="combined")].iloc[0]
    assert abs(base.net_usd-34.990697617170554)<1e-6
    assert abs(stress.net_usd-29.456191741520115)<1e-6
    ranking=[]
    for bars in (0,1,2):
        x=full[(full.retry_bars==bars)&(full.leverage==50)&(full.scenario=="base")].iloc[0]
        y=full[(full.retry_bars==bars)&(full.leverage==50)&(full.scenario=="combined")].iloc[0]
        allr=df[df.retry_bars==bars]
        passed=bool(bars>0 and x.net_usd>=base.net_usd and x.positive_months>base.positive_months and x.months_ge_1pct>=base.months_ge_1pct and x.closed_dd_pct<=base.closed_dd_pct and x.year2024_usd>0 and x.year2025_usd>0 and y.net_usd>=stress.net_usd and (allr.net_usd>0).all() and (allr.liquidations==0).all())
        ranking.append(dict(retry_bars=bars,net_usd=x.net_usd,positive_months=x.positive_months,months_ge_1pct=x.months_ge_1pct,closed_dd_pct=x.closed_dd_pct,mark_dd_upper_pct=x.mark_dd_upper_pct,year2024_usd=x.year2024_usd,year2025_usd=x.year2025_usd,stress_net_usd=y.net_usd,trades=x.trades,executed_retries=x.executed_retries,training_pass=passed))
    pd.DataFrame(ranking).to_csv(OUT/"training_ranking.csv",index=False)
    print(pd.DataFrame(ranking).to_string(index=False),flush=True)
    (OUT/"quality.json").write_text(json.dumps(dict(baseline_parity=True,training_period="2024-02 through 2025-12",validation_2026_run=False,risk_pct=RISK,whole_lot_btc=.001,exposure_cap=CAP,retry_rule="one attempt after 4h or 8h; still beyond original breakout; any newer fresh signal cancels; only risk-budget rejection qualifies",cost_model="inherited V48",historical_2026_previously_examined=True),indent=2))

if __name__=="__main__":train()
