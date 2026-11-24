#!/usr/bin/env python3
"""High leverage research; isolated collateral exactly entry/leverage.
No additional collateral, no synthetic reduction in effective leverage.
No trade-ledger input or future filters. Conservative mark-first simulation.
"""
from collections import defaultdict
from pathlib import Path
import itertools,json
import numpy as np
import pandas as pd
from numba import njit
import research_v14_chronological_candle_replay as v14
OUT=Path("analysis/v18_high_leverage_robustness")
OUT.mkdir(parents=True,exist_ok=True)
FEE=.00059
SLIP=5.
COSTS=(0,10,25,50,60,75,100,125,150,175,200,225,250)
LEVS=(50,100,200)
# Candidate exit calculation is only read by the scheduler AFTER accepting the
# entry. The scheduler sees entry time, cycle, and realized state, not outcomes.
@njit
def execute(a,first,last,month,op,hi,lo,cl,mo,mh,ml,mc,rate,al,ash,sw,lev,stopfrac,tp,cap,trail,fundmode):
    out=np.zeros((len(a),10))
    n=0
    for i in range(len(a)):
        j=int(a[i,0]);side=int(a[i,1]);cyc=int(a[i,3])
        if j<first or j>=last:continue
        ep=op[j]+side*SLIP
        # Liquidation threshold with 0.25% MMR and entry fee debit.
        # Distance is conservative: long denominator .9975, short 1.0025.
        distance=ep*(1./lev-FEE-.0025)/(1.-side*.0025)
        if distance<=0:continue
        stop=ep-side*distance*stopfrac
        target=ep*(1+side*tp/100.)
        peak=ep;fund=0.;earlyfund=0.;liq=0
        x=min(j+cap-1,last-1);xp=cl[x]-side*SLIP;reason=3
        for k in range(j,x+1):
            if k>j and (k<sw or k%480==0):
                r=rate[k] if fundmode==0 else (al[k] if side==1 else ash[k])
                f=-side*mo[k]*r/(480. if k<sw else 1.)
                fund+=f
                if month[k]==month[j]:earlyfund+=f
            mark=ml[k] if side==1 else mh[k]
            # Any same-minute liquidation threshold hit is a liquidation even
            # if the stop also touched: no assumed favorable event order.
            buffer=ep/lev+fund-FEE*ep+side*(mark-ep)-.0025*mark
            if buffer<=0:
                x=k;xp=mark-side*SLIP;liq=1;reason=4;break
            # Native mark-triggered stop; adverse trade extreme is conservative
            # fill bound for unknown mark/trade order within the minute.
            if side*(mark-stop)<=0:
                x=k;xp=(lo[k] if side==1 else hi[k])-side*SLIP;reason=1;break
            # Independent traded-price stop for venue basis divergence.
            if (lo[k]<=stop if side==1 else hi[k]>=stop):
                x=k;xp=(min(op[k],stop) if side==1 else max(op[k],stop))-side*SLIP;reason=1;break
            if (hi[k]>=target if side==1 else lo[k]<=target):
                x=k;xp=target-side*SLIP;reason=2;break
            if trail>0:
                peak=max(peak,hi[k]) if side==1 else min(peak,lo[k])
                if side*(peak-ep)>=ep*.002:
                    ns=peak-side*distance*trail
                    stop=max(stop,ns) if side==1 else min(stop,ns)
        net=(-ep/lev-FEE*ep if liq else side*(xp-ep)-FEE*(ep+xp)+fund)
        # Allocate cross-month funding to its actual first-month settlement
        # bucket; liquidation loss already includes funding in initial margin.
        prior=earlyfund if month[x]!=month[j] else 0.
        out[n,0]=j;out[n,1]=x;out[n,2]=net;out[n,3]=cyc
        out[n,4]=side;out[n,5]=ep;out[n,6]=xp;out[n,7]=liq
        out[n,8]=prior;out[n,9]=reason;n+=1
    return out[:n]

@njit
def replay(a,month,day,cost,ceil,lim,loss):
    v=np.zeros(23);pos=-1;used=set();lastday=-1;today=0
    n=w=lq=0;eq=peak=dd=0.;ids=np.empty(len(a),np.int64)
    for i in range(len(a)):
        j=int(a[i,0]);x=int(a[i,1]);cyc=int(a[i,3]);m=month[j];d=day[j]
        if j<=pos or (cyc>0 and cyc in used):continue
        if d!=lastday:lastday=d;today=0
        if lim>0 and today>=lim:continue
        if v[m]>=ceil or v[m]<=-loss or v[m]>=a[i,10]:continue
        pos=x;today+=1
        if cyc>0:used.add(cyc)
        net=a[i,2]-cost;prior=a[i,8]
        v[m]+=prior;v[month[x]]+=net-prior;eq+=net
        peak=max(peak,eq);dd=max(dd,peak-eq)
        ids[n]=i;n+=1;w+=net>0;lq+=int(a[i,7])
    return v,eq,dd,n,w,lq,ids[:n]

def main():
    m,manifest=v14.shock.load()
    # Institutional mark and funding archive ends Nov 17 UTC. Keep the
    # entire common archive for indicator warmup and separately bounded replay.
    m=m.loc[:"2026-11-17 23:59:00"].copy()
    b=m.resample("15min").agg(open=("open","first"),high=("high","max"),low=("low","min"),close=("close","last"),volume=("volume","sum"))
    h=m.resample("1h").agg(open=("open","first"),high=("high","max"),low=("low","min"),close=("close","last"),volume=("volume","sum"))
    assert len(m)==len(b)*15==len(h)*60
    end=len(m)
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
    # More frequent closed-candle signals for tight high-leverage stops.
    for tf in (5,15,30):
        z=m.resample(f"{tf}min").agg(open=("open","first"),high=("high","max"),low=("low","min"),close=("close","last"),volume=("volume","sum"))
        cc=z.close;dd=cc.diff();u=dd.clip(lower=0).ewm(alpha=1/14,adjust=False,min_periods=14).mean();dn=(-dd.clip(upper=0)).ewm(alpha=1/14,adjust=False,min_periods=14).mean()
        rs=100*u/(u+dn).replace(0,np.nan)
        for n in (12,24):
            up=cc>z.high.shift(1).rolling(n).max();down=cc<z.low.shift(1).rolling(n).min()
            for i in np.flatnonzero((up|down).to_numpy()):
                j=(int(i)+1)*tf
                if j<end:add(f"M{tf}_Donchian{n}",j,1 if up.iat[i] else -1,op[j])
        for n in (9,20,50):
            e=cc.ewm(span=n,adjust=False,min_periods=n).mean()
            up=(z.low<=e)&(cc>e)&(cc>z.open)&(cc.shift(1)>e.shift(1))
            down=(z.high>=e)&(cc<e)&(cc<z.open)&(cc.shift(1)<e.shift(1))
            for i in np.flatnonzero((up|down).to_numpy()):
                j=(int(i)+1)*tf
                if j<end:add(f"M{tf}_EMA{n}",j,1 if up.iat[i] else -1,op[j])
        for l,u in ((25,75),(35,65)):
            up=(rs.shift(1)<=l)&(rs>l);down=(rs.shift(1)>=u)&(rs<u)
            for i in np.flatnonzero((up|down).to_numpy()):
                j=(int(i)+1)*tf
                if j<end:add(f"M{tf}_RSI{l}",j,1 if up.iat[i] else -1,op[j])
    # Additional causal entry families intended for tight risk budgets:
    # momentum after a compressed range, rejection of prior swing levels,
    # continuation after a small pullback, and lower-timeframe timing.
    for tf in (3,5,15,30,60):
        z=m.resample(f"{tf}min").agg(open=("open","first"),high=("high","max"),low=("low","min"),close=("close","last"),volume=("volume","sum"))
        cc=z.close;span=(z.high-z.low).clip(lower=1e-9)
        body=(cc-z.open)/span
        v=z.volume/z.volume.shift(1).rolling(20).mean()
        e9=cc.ewm(span=9,adjust=False).mean();e21=cc.ewm(span=21,adjust=False).mean()
        e50=cc.ewm(span=50,adjust=False).mean()
        for n in (12,24):
            uh=z.high.shift(1).rolling(n).max();ll=z.low.shift(1).rolling(n).min()
            up=(z.low<ll)&(cc>ll)&(body>=.35)
            dn=(z.high>uh)&(cc<uh)&(body<=-.35)
            for i in np.flatnonzero((up|dn).to_numpy()):
                j=(int(i)+1)*tf
                if j<end:add(f"M{tf}_sweep{n}",j,1 if up.iat[i] else -1,op[j])
            # Compression measured before breakout candle, not after.
            width=(uh-ll)/cc.shift(1)
            quiet=width<width.shift(1).rolling(100,min_periods=100).quantile(.30)
            up=(cc>uh)&quiet&(body>.35);dn=(cc<ll)&quiet&(body<-.35)
            for i in np.flatnonzero((up|dn).to_numpy()):
                j=(int(i)+1)*tf
                if j<end:add(f"M{tf}_squeeze{n}",j,1 if up.iat[i] else -1,op[j])
        up=(e9>e21)&(e21>e50)&(z.low<=e9)&(cc>e9)&(body>.3)&(v>=.8)
        dn=(e9<e21)&(e21<e50)&(z.high>=e9)&(cc<e9)&(body<-.3)&(v>=.8)
        for i in np.flatnonzero((up|dn).to_numpy()):
            j=(int(i)+1)*tf
            if j<end:add(f"M{tf}_stack_pullback",j,1 if up.iat[i] else -1,op[j])
        d=cc.diff();u=d.clip(lower=0).ewm(alpha=.5,adjust=False,min_periods=2).mean()
        dn=(-d.clip(upper=0)).ewm(alpha=.5,adjust=False,min_periods=2).mean()
        r=100*u/(u+dn).replace(0,np.nan)
        up=(r.shift(1)<10)&(r>=10)&(cc>e50)
        down=(r.shift(1)>90)&(r<=90)&(cc<e50)
        for i in np.flatnonzero((up|down).to_numpy()):
            j=(int(i)+1)*tf
            if j<end:add(f"M{tf}_RSI2_trend",j,1 if up.iat[i] else -1,op[j])
    # Prior daily and session range sweeps. Use only completed prior levels.
    for n in (60,240,1440):
        priorhi=m.high.shift(1).rolling(n).max()
        priorlo=m.low.shift(1).rolling(n).min()
        u=(m.low<priorlo)&(m.close>priorlo)&(m.close>m.open)
        d=(m.high>priorhi)&(m.close<priorhi)&(m.close<m.open)
        for i in np.flatnonzero((u|d).to_numpy()):
            j=int(i)+1
            if j<end:add(f"M1_sweep{n}",j,1 if u.iat[i] else -1,op[j])
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
    root=Path("data/delta_india/BTCUSD/institutional/history")
    def load_series(label,res):
        blocks=[]
        for f in sorted((root/label).glob("20??-??.csv.gz")):
            x=pd.read_csv(f,compression="gzip")
            if pd.api.types.is_numeric_dtype(x.time):
                x["time"]=pd.to_datetime(x.time.astype("int64"),unit="s",utc=True)
            else:x["time"]=pd.to_datetime(x.time,utc=True)
            blocks.append(x.set_index("time")[["open","high","low","close"]])
        z=pd.concat(blocks).sort_index()
        assert not z.index.has_duplicates and z.index.to_series().diff().dropna().eq(pd.Timedelta(res)).all(),label
        assert np.isfinite(z.to_numpy(float)).all(),label
        assert ((z.low<=z[["open","close"]].min(axis=1))&(z.high>=z[["open","close"]].max(axis=1))).all(),label
        return z
    mark=load_series("mark_1m","1min").reindex(m.index)
    assert not mark.isna().any().any()
    fr=load_series("funding_1h","1h")
    print("FUNDING_SAMPLE",fr.head(12).to_string(),"RANGE",fr.min().to_dict(),fr.max().to_dict(),flush=True)
    # Public funding OHLC is quoted in percentage points (0.01 = 0.01%).
    # No account settlement ledger or exact underlying index in archive;
    # close of preceding hour is a causal rate proxy. Compare prior interval
    # open and adverse observed range, without labeling exact actual cashflow.
    hourly=m.index.floor("h")
    previous=fr.reindex(hourly-pd.Timedelta(hours=1))
    # First hour of archive has no prior observation, no valid warmup entry.
    assert not previous.iloc[60:].isna().any().any()
    rate=previous.close.to_numpy(float)/100.
    begin8=hourly.floor("8h")
    interval=fr.reindex(begin8-pd.Timedelta(hours=1))
    interval_rate=interval.close.to_numpy(float)/100.
    # Conservative debit only using previous hour low/high, to probe uncertainty.
    adverse_long=np.maximum(previous.high.to_numpy(float)/100.,0)
    adverse_short=np.minimum(previous.low.to_numpy(float)/100.,0)
    rate[:60]=0.;interval_rate[:480]=0.;adverse_long[:60]=0.;adverse_short[:60]=0.
    mo=mark.open.to_numpy(float);mh=mark.high.to_numpy(float);ml=mark.low.to_numpy(float)
    # Exchange change effective interval starts Sep 8 2025; document conflicting
    # 17:30 IST wording vs 05:30/13:30/21:30 standard snapshots. Model first
    # discrete settlement at next 21:30 IST (16 UTC), and alternate one later.
    sw=int(m.index.searchsorted(pd.Timestamp("2025-09-08 16:00:00",tz="UTC")))
    mc=mark.close.to_numpy(float)
    train_end=int(m.index.searchsorted(pd.Timestamp("2026-11-01",tz="Asia/Kolkata").tz_convert("UTC")))
    # All entry filters are based on the previous fully completed minute(s).
    # Do not skip trades based on any price in their entry or exit minute.
    mr=((mark.high-mark.low)/mark.close*100)
    range5=mr.rolling(5).max().shift(1).to_numpy()
    range20=mr.rolling(20).mean().shift(1).to_numpy()
    basis=(abs(mark.close-m.close)/m.close*100).shift(1).to_numpy()
    data_groups={}
    for name,g in groups.items():
        z=np.array(sorted(g.values(),key=lambda x:x[0]),float)
        if len(z)<22:continue
        ids=z[:,0].astype(np.int64)
        # Closed minute directional candle quality and prior volatility.
        closeprev=cl[ids-1]; openprev=op[ids-1]
        prevspan=np.maximum(hi[ids-1]-lo[ids-1],1e-9)
        body=(closeprev-openprev)/prevspan*z[:,1]
        ret5=(cl[ids-1]/cl[np.maximum(0,ids-6)]-1)*100*z[:,1]
        ret15=(cl[ids-1]/cl[np.maximum(0,ids-16)]-1)*100*z[:,1]
        # Mark/trade basis sign known at entry from preceding minute.
        signedbasis=(mark.close.to_numpy()[ids-1]-cl[ids-1])/cl[ids-1]*100*z[:,1]
        data_groups[name]=np.column_stack((z,range5[ids],range20[ids],basis[ids],body,ret5,ret15,signedbasis))
    # Same entry/exit rules applied independently at each leverage. Search on
    # Jan 2025-Oct 2026 only; November is a separate temporal holdout.
    summary=[];monthly=[];selected=[];alltrades=[]
    for lev in LEVS:
        cutoff=(1./lev-FEE-.0025)*100
        masks2=dict(masks)
        for q in (.20,.35,.5,.75,1.):
            masks2[f"quiet5_{q}"]=lambda a,q=q:(a[:,11]<=cutoff*q)&(a[:,13]<=cutoff*.35)
            masks2[f"quiet20_{q}"]=lambda a,q=q:(a[:,12]<=cutoff*q)&(a[:,13]<=cutoff*.35)
            masks2[f"quiet_align_{q}"]=lambda a,q=q:(a[:,11]<=cutoff*q)&(a[:,13]<=cutoff*.35)&(a[:,5]>0)
        masks2["basis_guard"]=lambda a:(a[:,13]<=cutoff*.25)
        masks2["quiet_short"]=lambda a:(a[:,1]==-1)&(a[:,11]<=cutoff*.5)&(a[:,13]<=cutoff*.35)
        masks2["quiet_long"]=lambda a:(a[:,1]==1)&(a[:,11]<=cutoff*.5)&(a[:,13]<=cutoff*.35)
        for q in (.25,.5,.75,1.25,1.5):
            masks2[f"quiet20_body_{q}"]=lambda a,q=q:(a[:,12]<=cutoff*q)&(a[:,14]>=.25)&(a[:,13]<=cutoff*.3)
            masks2[f"quiet20_trend_{q}"]=lambda a,q=q:(a[:,12]<=cutoff*q)&(a[:,5]>0)&(a[:,13]<=cutoff*.3)
            masks2[f"quiet20_counter_{q}"]=lambda a,q=q:(a[:,12]<=cutoff*q)&(a[:,15]<0)&(a[:,13]<=cutoff*.3)
            masks2[f"quiet20_basis_{q}"]=lambda a,q=q:(a[:,12]<=cutoff*q)&(a[:,17]>=-cutoff*.1)&(a[:,13]<=cutoff*.3)
        masks2["quiet20_short"]=lambda a:(a[:,1]==-1)&(a[:,12]<=cutoff*.75)&(a[:,13]<=cutoff*.3)
        masks2["quiet20_long"]=lambda a:(a[:,1]==1)&(a[:,12]<=cutoff*.75)&(a[:,13]<=cutoff*.3)
        masks2["quiet20_h4"]=lambda a:(a[:,6]>0)&(a[:,12]<=cutoff*.75)&(a[:,13]<=cutoff*.3)
        masks2["body_confirmed"]=lambda a:(a[:,14]>.5)&(a[:,13]<=cutoff*.3)
        # Stop as fraction of liquidation distance (never beyond it).
        # Profit targets are independent, to allow asymmetric payoff.
        configs=list(itertools.product((.15,.3,.5,.7,.85),(.5,1.,2.,3.,4.,6.),(360,1440,4320), (0.,)))
        configs+=list(itertools.product((.35,.65), (2.,4.,6.),(1440,),(.5,1.,1.5)))
        pool=[];tested=0
        def ev(a,cost,ceil=1e30,lim=0,loss=1e30):
            return replay(a,month,day,float(cost),float(ceil),lim,float(loss))
        def rank(z,months=22):
            v,net,dd,n,w,lq,_=z;v=v[:months]
            return (int(lq==0),int(np.sum(v>=1000)),float(v.min()),float(net),-float(dd),-int(lq))
        def keep(p,n):
            p.sort(key=lambda z:z[0],reverse=True);return p[:n]
        for name,full in data_groups.items():
            a=full[full[:,0]<train_end]
            if len(a)<16:continue
            fm={label:fn(a) for label,fn in masks2.items()}
            fm={label:mask for label,mask in fm.items() if mask.sum()>=16}
            local=[];bestnet=[];bestmonths=[];weak=[]
            for spec in configs:
                # Use debit-only funding in the optimization, then re-run with
                # signed rate proxy in independent final validation.
                raw=execute(a,0,train_end,month,op,hi,lo,cl,mo,mh,ml,mc,rate,adverse_long,adverse_short,sw,lev,*spec,1)
                for label,mask in fm.items():
                    ar=np.column_stack((raw[mask],np.full(mask.sum(),1e30)))
                    z=ev(ar,200);tested+=1
                    if z[3]<16:continue
                    item=(rank(z),name,label,spec,ar,z[:6])
                    local.append(item)
                    bestnet.append(item)
                    bestmonths.append(item)
                    # Preserve profiles with genuinely positive net, not just monthly hit counts.
                    if z[5]==0 and z[1]>0:weak.append(item)
                    if len(weak)>80:weak=sorted(weak,key=lambda p:(p[5][1],p[0][1]),reverse=True)[:10]
                    if len(local)>100:local=keep(local,12)
                    if len(bestnet)>100:bestnet=sorted(bestnet,key=lambda q:(q[5][5]==0,q[5][1],q[0]),reverse=True)[:5]
                    if len(bestmonths)>100:bestmonths=sorted(bestmonths,key=lambda q:(q[0][1],-q[5][5],q[5][1]),reverse=True)[:5]
            local=keep(local,12);bestnet=sorted(bestnet,key=lambda q:(q[5][5]==0,q[5][1]),reverse=True)[:5]
            bestmonths=sorted(bestmonths,key=lambda q:(q[0][1],-q[5][5],q[5][1]),reverse=True)[:5]
            pool.extend(local+bestnet+bestmonths+weak[:10])
            if local:print("GROUP",lev,name,tested,local[0][0],flush=True)
        # Remove exact duplicate configs. Keep broad family diversity.
        seen=set();unique=[]
        for p in pool:
            key=(p[1],p[2],p[3])
            if key not in seen:seen.add(key);unique.append(p)
        # Diversity: keep top candidates per family and by profit as well as month coverage.
        byfam=defaultdict(list)
        for q in unique:byfam[q[1]].append(q)
        diverse=[q for qs in byfam.values() for q in keep(qs,4)]
        pool=keep(unique,160)+sorted(diverse,key=lambda q:(q[5][5]==0,q[5][1],q[0][1]),reverse=True)[:160]
        dedup={ (q[1],q[2],q[3]):q for q in pool};pool=list(dedup.values())
        if not pool:raise RuntimeError("No candidate with enough trades")
        def robust(legs,a,ceil,lim,loss,costs=(0,100,200)):
            nonlocal tested
            zz=[ev(a,c,ceil,lim,loss) for c in costs];tested+=len(costs)
            worst=min(x[0][:22].min() for x in zz)
            counts=[int(np.sum(x[0][:22]>=1000)) for x in zz]
            lq=sum(x[5] for x in zz)
            # No zero-trade pass: require 22 profitable months and zero liq.
            r=(int(lq==0),min(counts),sum(counts),float(worst),zz[-1][1],-zz[-1][2],-lq)
            return (r,legs,a,ceil,lim,loss)
        beam=[robust([(q,1e30)],q[4],1e30,0,1e30) for q in pool]
        beam=keep(beam,36);allp=beam.copy()
        for depth in (2,3,4,5,6):
            nxt=[]
            for p in beam[:18]:
                used={q[1] for q,_ in p[1]}
                for q in pool:
                    if q[1] in used:continue
                    for threshold in (-1000.,0.,500.,1000.,1500.,1e30):
                        ar=q[4].copy();ar[:,10]=threshold
                        a=np.concatenate((p[2],ar));a=a[np.argsort(a[:,0],kind="stable")]
                        nxt.append(robust(p[1]+[(q,threshold)],a,p[3],p[4],p[5]))
                        if len(nxt)>160:nxt=keep(nxt,36)
            if not nxt:break
            beam=keep(nxt,36);allp=keep(allp+beam,60)
            print("BEAM",lev,depth,tested,allp[0][0],flush=True)
        finals=[]
        for p in allp:
            for ceil,lim,loss in itertools.product((1000.,1250.,1500.,1750.,2000.,2500.,4000.,1e30),(0,1,2,3),(2000.,4000.,8000.,1e30)):
                finals.append(robust(p[1],p[2],ceil,lim,loss))
                if len(finals)>100:finals=keep(finals,40)
        finals=keep(finals+allp,60)
        # Validate both signed-rate and debit-only funding with full stress
        # using freshly generated exits, without changing config between costs.
        final=[]
        for p in finals:
            legs=p[1];arrs=[]
            for fmode in (0,1):
                aa=[]
                for q,threshold in legs:
                    arr=data_groups[q[1]];arr=arr[masks2[q[2]](arr)]
                    x=execute(arr,0,train_end,month,op,hi,lo,cl,mo,mh,ml,mc,rate,adverse_long,adverse_short,sw,lev,*q[3],fmode)
                    aa.append(np.column_stack((x,np.full(len(x),threshold))))
                x=np.concatenate(aa);arrs.append(x[np.argsort(x[:,0],kind="stable")])
            zz=[ev(a,c,p[3],p[4],p[5]) for a in arrs for c in COSTS if c<=200];tested+=len(zz)
            counts=[int(np.sum(x[0][:22]>=1000)) for x in zz];lq=sum(x[5] for x in zz)
            r=(int(lq==0),min(counts),sum(counts),min(float(x[0][:22].min()) for x in zz),min(x[1] for x in zz),-max(x[2] for x in zz),-lq)
            final.append((r,p,arrs))
        final.sort(key=lambda z:z[0],reverse=True)
        score,p,arrs=final[0]
        profile=dict(leverage=lev,rank=list(score),evaluations=tested,legs=[dict(group=q[1],filter=q[2],stop_fraction=q[3][0],tp_pct=q[3][1],max_minutes=q[3][2],trail_fraction=q[3][3],mtd_gate=threshold) for q,threshold in p[1]],month_ceiling=p[3],daily_limit=p[4],loss_guard=p[5],pass_all=bool(score[0] and score[1]==22))
        selected.append(profile);print("SELECTED",json.dumps(profile),flush=True)
        for period in ("train","november_temporal_holdout"):
            for fmode in (0,1):
                if period=="train":a=arrs[fmode]
                else:
                    aa=[]
                    for q,threshold in p[1]:
                        a=data_groups[q[1]];a=a[masks2[q[2]](a)]
                        x=execute(a,train_end,end,month,op,hi,lo,cl,mo,mh,ml,mc,rate,adverse_long,adverse_short,sw,lev,*q[3],fmode)
                        aa.append(np.column_stack((x,np.full(len(x),threshold))))
                    a=np.concatenate(aa);a=a[np.argsort(a[:,0],kind="stable")]
                for cost in COSTS:
                    v,net,dd,n,w,lq,idx=ev(a,cost,p[3],p[4],p[5])
                    sub=v[:22] if period=="train" else v[22:]
                    t=a[idx]
                    assert np.all(t[1:,0]>t[:-1,1]) and np.all(weekday[t[:,0].astype(np.int64)]<5)
                    assert abs(sub.sum()-net)<1e-5
                    summary.append(dict(leverage=lev,period=period,funding_mode="signed_proxy" if fmode==0 else "debit_only",cost=cost,net_points=net,trades=n,wins=w,liquidations=lq,months_ge_1pct=int(np.sum(sub>=1000)),min_month_points=float(sub.min()),closed_dd_points=dd))
                    monthly.extend(dict(leverage=lev,period=period,funding_mode=fmode,cost=cost,month=str(pd.Period("2025-01",freq="M")+i),net_points=v[i]) for i in (range(22) if period=="train" else [22]))
                    if cost==200:
                        for row in t:
                            alltrades.append(dict(leverage=lev,period=period,funding_mode=fmode,cost=cost,entry_utc=str(m.index[int(row[0])]),exit_utc=str(m.index[int(row[1])]),side=int(row[4]),entry=row[5],exit=row[6],net_points=row[2]-cost,liquidation=int(row[7]),reason=int(row[9])))
        pd.DataFrame(summary).to_csv(OUT/"summary.csv",index=False)
        pd.DataFrame(monthly).to_csv(OUT/"monthly.csv",index=False)
        pd.DataFrame(alltrades).to_csv(OUT/"trades_200.csv",index=False)
        (OUT/"quality.json").write_text(json.dumps(dict(profiles=selected,completed_leverages=[x["leverage"] for x in selected],pass_all=bool(len(selected)==3 and all(x["pass_all"] for x in selected)),margin_mode="isolated exact 1/leverage, no top-up",liquidation_assumption="adverse mark first; full initial margin loss plus fee proxy",stop_fill="mark-triggered safety stop at adverse trade minute extreme; independent trade stop, no favorable ordering",funding="historical rate proxy, signed and debit-only; exact exchange settlement not verified",entry="closed signals next minute open; prior-only volatility and basis filters",raw_trade_ledger_inputs=False,holdout="November partial temporal, already examined for prior versions; not certified untouched; not used to select this run",return_units="normalized points, not account return",candle_count=train_end),indent=2,default=float))
if __name__=="__main__":main()
