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
OUT=Path("analysis/v20_leverage_recovery")
OUT.mkdir(parents=True,exist_ok=True)
FEE=.00059
SLIP=5.
COSTS=(0,10,25,50,60,75,100,125,150,175,200,225,250)
LEVS=(100,200)
LOCKED_V19=json.loads('''[{"leverage":50,"track":"known_november_development","rank":[1,22,484,1,1508.3932575673932,2760.8385538743346,57715.84251661501,-5677.812221765171,0],"evaluations":1298442,"legs":[{"group":"EMA20_ADX_reclaim_confirm1","filter":"all","stop_fraction":0.7,"tp_pct":3,"max_minutes":4320,"trail_fraction":0,"mtd_gate":1e+30},{"group":"M5_EMA50","filter":"high_ATR_ratio","stop_fraction":0.5,"tp_pct":3,"max_minutes":4320,"trail_fraction":0,"mtd_gate":1e+30},{"group":"RSI_reversal","filter":"H4_not_aligned","stop_fraction":0.7,"tp_pct":3.5,"max_minutes":4320,"trail_fraction":0,"mtd_gate":1000},{"group":"M15_squeeze24","filter":"high_ATR_ratio","stop_fraction":0.35,"tp_pct":6,"max_minutes":2880,"trail_fraction":1.5,"mtd_gate":1e+30},{"group":"H1_Donchian72","filter":"long_ADX32","stop_fraction":0.7,"tp_pct":10,"max_minutes":4320,"trail_fraction":0,"mtd_gate":0},{"group":"M60_squeeze24","filter":"long_ADX28","stop_fraction":0.6,"tp_pct":2,"max_minutes":1440,"trail_fraction":0,"mtd_gate":1e+30},{"group":"H1_RSI30_reversal_confirm5","filter":"high_ATR_ratio","stop_fraction":0.15,"tp_pct":4,"max_minutes":4320,"trail_fraction":0,"mtd_gate":500},{"group":"M60_squeeze24_confirm1","filter":"H4_long","stop_fraction":0.7,"tp_pct":3,"max_minutes":1440,"trail_fraction":0,"mtd_gate":1000}],"month_ceiling":1500,"daily_limit":2,"loss_guard":6000},{"leverage":100,"track":"known_november_development","rank":[1,21,482,1,947.322267035537,2781.614495,54984.40033464427,-3095.337414970578,0],"evaluations":1225889,"legs":[{"group":"M30_RSI25","filter":"short_ADX40","stop_fraction":0.5,"tp_pct":3,"max_minutes":4320,"trail_fraction":0,"mtd_gate":1e+30},{"group":"EMA20_ADX_reclaim","filter":"range_ADX20","stop_fraction":0.5,"tp_pct":2,"max_minutes":4320,"trail_fraction":2,"mtd_gate":500},{"group":"M15_squeeze24_pull1","filter":"high_ATR_ratio","stop_fraction":0.35,"tp_pct":6,"max_minutes":4320,"trail_fraction":0,"mtd_gate":0},{"group":"M60_squeeze24_confirm1","filter":"short_ADX18","stop_fraction":0.15,"tp_pct":6,"max_minutes":4320,"trail_fraction":0,"mtd_gate":0},{"group":"line_touch","filter":"ADX_between_10_25","stop_fraction":0.3,"tp_pct":3,"max_minutes":1440,"trail_fraction":0,"mtd_gate":1000},{"group":"M15_sweep12_confirm1","filter":"long_ADX32","stop_fraction":0.3,"tp_pct":9,"max_minutes":4320,"trail_fraction":0,"mtd_gate":-1000},{"group":"H1_RSI30_reversal_confirm1","filter":"quiet20_counter_0.25","stop_fraction":0.7,"tp_pct":6,"max_minutes":4320,"trail_fraction":0,"mtd_gate":-1000},{"group":"BB_stretch_pull3","filter":"entry_quiet_0.5","stop_fraction":0.5,"tp_pct":6,"max_minutes":1440,"trail_fraction":0,"mtd_gate":1000}],"month_ceiling":2000,"daily_limit":3,"loss_guard":6000},{"leverage":200,"track":"known_november_development","rank":[1,15,336,0,-3357.7594274330286,-2481.640025,16462.52458549331,-6038.988291374571,0],"evaluations":1067497,"legs":[{"group":"line_touch_confirm1","filter":"quiet20_trend_1.25","stop_fraction":0.35,"tp_pct":2,"max_minutes":1440,"trail_fraction":0,"mtd_gate":1e+30},{"group":"EMA20_touch","filter":"quiet20_h4","stop_fraction":0.15,"tp_pct":3,"max_minutes":1440,"trail_fraction":0,"mtd_gate":500},{"group":"M5_EMA50","filter":"quiet20_counter_0.25","stop_fraction":0.3,"tp_pct":4,"max_minutes":7200,"trail_fraction":0,"mtd_gate":1e+30},{"group":"BB_stretch_confirm3","filter":"quiet20_trend_0.5","stop_fraction":0.15,"tp_pct":6,"max_minutes":1440,"trail_fraction":0,"mtd_gate":1e+30},{"group":"M30_RSI25_confirm3","filter":"short_ADX40","stop_fraction":0.3,"tp_pct":9,"max_minutes":4320,"trail_fraction":0,"mtd_gate":0},{"group":"H1_RSI40_reversal","filter":"short_ADX40","stop_fraction":0.15,"tp_pct":6,"max_minutes":7200,"trail_fraction":0,"mtd_gate":0},{"group":"M15_squeeze24_pull3","filter":"high_ATR_ratio","stop_fraction":0.7,"tp_pct":6,"max_minutes":1440,"trail_fraction":0,"mtd_gate":0},{"group":"RSI_cross20","filter":"quiet20_counter_0.25","stop_fraction":0.3,"tp_pct":4,"max_minutes":4320,"trail_fraction":0,"mtd_gate":-1000}],"month_ceiling":1000,"daily_limit":1,"loss_guard":3000}]''')
BASE=json.loads('''[{"leverage":50,"rank":[1,22,484,1011.0695597425022,49961.568219475295,-4586.841725156526,0],"evaluations":1074831,"legs":[{"group":"EMA20_ADX_reclaim","filter":"range_ADX20","stop_fraction":0.7,"tp_pct":2,"max_minutes":4320,"trail_fraction":0,"mtd_gate":1e+30},{"group":"M5_EMA50","filter":"high_ATR_ratio","stop_fraction":0.5,"tp_pct":3,"max_minutes":4320,"trail_fraction":0,"mtd_gate":1000},{"group":"RSI_reversal","filter":"H4_not_aligned","stop_fraction":0.7,"tp_pct":3,"max_minutes":4320,"trail_fraction":0,"mtd_gate":500},{"group":"M15_squeeze24","filter":"high_ATR_ratio","stop_fraction":0.35,"tp_pct":6,"max_minutes":1440,"trail_fraction":1.5,"mtd_gate":500},{"group":"H1_Donchian72","filter":"long_ADX32","stop_fraction":0.7,"tp_pct":6,"max_minutes":4320,"trail_fraction":0,"mtd_gate":0},{"group":"M60_squeeze24","filter":"H4_long","stop_fraction":0.7,"tp_pct":2,"max_minutes":1440,"trail_fraction":0,"mtd_gate":1000}],"month_ceiling":1500,"daily_limit":0,"loss_guard":8000,"pass_all":true},{"leverage":100,"rank":[1,20,460,-3870.3394468364577,40917.81857408915,-4799.850705280289,0],"evaluations":1052748,"legs":[{"group":"M30_RSI25","filter":"short_ADX40","stop_fraction":0.5,"tp_pct":3,"max_minutes":4320,"trail_fraction":0,"mtd_gate":1e+30},{"group":"EMA20_ADX_reclaim","filter":"range_ADX20","stop_fraction":0.5,"tp_pct":2,"max_minutes":4320,"trail_fraction":0,"mtd_gate":1000},{"group":"M15_squeeze24","filter":"high_ATR_ratio","stop_fraction":0.5,"tp_pct":6,"max_minutes":4320,"trail_fraction":0,"mtd_gate":0},{"group":"M60_squeeze24","filter":"short_ADX18","stop_fraction":0.15,"tp_pct":4,"max_minutes":4320,"trail_fraction":0,"mtd_gate":0},{"group":"line_touch","filter":"ADX_between_10_25","stop_fraction":0.3,"tp_pct":3,"max_minutes":1440,"trail_fraction":0,"mtd_gate":1000},{"group":"M15_sweep12","filter":"long_ADX32","stop_fraction":0.3,"tp_pct":6,"max_minutes":4320,"trail_fraction":0,"mtd_gate":-1000}],"month_ceiling":2000,"daily_limit":2,"loss_guard":8000,"pass_all":false},{"leverage":200,"rank":[1,10,236,-4216.012034721197,-969.8522376287156,-19636.230918721125,0],"evaluations":1088703,"legs":[{"group":"line_touch","filter":"quiet20_body_0.5","stop_fraction":0.5,"tp_pct":2,"max_minutes":1440,"trail_fraction":0,"mtd_gate":1e+30},{"group":"EMA20_touch","filter":"quiet20_h4","stop_fraction":0.15,"tp_pct":3,"max_minutes":1440,"trail_fraction":0,"mtd_gate":500},{"group":"M5_EMA50","filter":"quiet20_counter_0.25","stop_fraction":0.3,"tp_pct":4,"max_minutes":4320,"trail_fraction":0,"mtd_gate":500},{"group":"BB_stretch","filter":"quiet_align_0.5","stop_fraction":0.15,"tp_pct":6,"max_minutes":1440,"trail_fraction":0,"mtd_gate":0},{"group":"M30_RSI25","filter":"quiet20_trend_0.5","stop_fraction":0.3,"tp_pct":6,"max_minutes":4320,"trail_fraction":0,"mtd_gate":0},{"group":"H1_RSI40_reversal","filter":"short_ADX40","stop_fraction":0.15,"tp_pct":6,"max_minutes":1440,"trail_fraction":0,"mtd_gate":-1000}],"month_ceiling":1000,"daily_limit":2,"loss_guard":4000,"pass_all":false}]''')
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
    # Delayed confirmation: both direction and elapsed minutes are fixed at
    # signal time. At j+delay only completed candles before that open are read.
    seed_names={q["group"] for p in BASE for q in p["legs"]}
    seed_names.update(("Shock_Donchian","M5_sweep12","M15_sweep24","M30_stack_pullback","H1_RSI30_reversal"))
    for name in sorted(seed_names):
        if name not in groups:continue
        rows=list(groups[name].values())
        for delay in (1,3,5):
            for q in rows:
                j=int(q[0]);side=int(q[1]);at=j+delay
                if at>=end or day[at]!=day[j]:continue
                ret=side*(cl[at-1]-op[j])/op[j]*100
                if ret>=0:
                    add(name+f"_confirm{delay}",at,side,op[at],("delayed",int(q[3])) if q[3]>0 else None)
                if ret<=0:
                    add(name+f"_pull{delay}",at,side,op[at],("delayed",int(q[3])) if q[3]>0 else None)
    # Preserve original V19 families exactly. New delayed families have
    # distinct names; only already completed bars determine eligibility.
    needed={q["group"] for p in LOCKED_V19 for q in p["legs"]}
    roots={x.split("_confirm")[0].split("_pull")[0] for x in needed}
    for name in sorted(roots):
        if name not in groups:continue
        rows=list(groups[name].values())
        for delay in (2,4,7,12,20):
            for q in rows:
                j=int(q[0]);side=int(q[1]);at=j+delay
                if at>=end or day[at]!=day[j]:continue
                ret=side*(cl[at-1]-op[j])/op[j]*100
                if ret>=0:add(name+f"_lateconfirm{delay}",at,side,op[at],("late",int(q[3])) if q[3]>0 else None)
                if ret<=0:add(name+f"_latepull{delay}",at,side,op[at],("late",int(q[3])) if q[3]>0 else None)
    # Quiet-market directional transition. The breakout level and all
    # volatility conditions are computed strictly from completed candles.
    for tf in (1,3,5,15):
        z=m.resample(f"{tf}min").agg(open=("open","first"),high=("high","max"),low=("low","min"),close=("close","last"),volume=("volume","sum"))
        cc=z.close
        e=cc.ewm(span=50,adjust=False).mean()
        for n in (8,20):
            hh=z.high.shift(1).rolling(n).max();ll=z.low.shift(1).rolling(n).min()
            width=(hh-ll)/cc.shift(1)
            quiet=width<=width.shift(1).rolling(120,min_periods=120).quantile(.2)
            up=quiet&(cc>hh)&(cc>e);dn=quiet&(cc<ll)&(cc<e)
            for i in np.flatnonzero((up|dn).to_numpy()):
                at=(int(i)+1)*tf
                if at<end:add(f"M{tf}_quiet_break{n}",at,1 if up.iat[i] else -1,op[at])
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
        # Locked V18 profiles are included verbatim and never overwritten.
        seed=next(p for p in LOCKED_V19 if p["leverage"]==lev)
        baselegs=seed["legs"]
        core={q["group"]:q for q in baselegs}
        anchors=(0,50,100,150,200)
        allcost=tuple(c for c in COSTS if c<=200)
        # Add risk-aware prior-minute filter variants, without conditioning
        # acceptance on future trade outcome or liquidation.
        for q in (.2,.35,.5,.7,1.):
            masks2[f"entry_quiet_{q}"]=lambda a,q=q:(a[:,11]<=cutoff*q)&(a[:,13]<=cutoff*.2)&(a[:,14]>=0)
            masks2[f"quiet_reclaim_{q}"]=lambda a,q=q:(a[:,12]<=cutoff*q)&(a[:,17]>=-cutoff*.1)&(a[:,14]>.3)
        # Candidate tuple: name, filter, exit spec, debit-train, debit-Nov.
        tested=0
        def sim(arr,first,last,spec,mode):
            return execute(arr,first,last,month,op,hi,lo,cl,mo,mh,ml,mc,rate,adverse_long,adverse_short,sw,lev,*spec,mode)
        def candidate(name,label,spec,raw=None,nov=None):
            a=data_groups[name];mask=masks2[label](a)
            if raw is None:
                raw=sim(a,0,train_end,spec,1)
                nov=sim(a,train_end,end,spec,1)
            return (name,label,spec,raw[mask[a[:,0]<train_end]],nov[mask[a[:,0]>=train_end]])
        def packed(legs,nov=False):
            rows=[np.column_stack((q[4 if nov else 3],np.full(len(q[4 if nov else 3]),gate))) for q,gate in legs]
            a=np.concatenate(rows)
            return a[np.argsort(a[:,0],kind="stable")]
        def ev(a,c,ceil,lim,loss):
            return replay(a,month,day,float(c),float(ceil),int(lim),float(loss))
        def evaluate(legs,a,b,ceil,lim,loss,dev=False,costs=anchors):
            nonlocal tested
            rr=[ev(a,c,ceil,lim,loss) for c in costs]
            tested+=len(rr)
            counts=[int(np.sum(x[0][:22]>=1000)) for x in rr]
            lq=sum(x[5] for x in rr)
            worst=min(float(x[0][:22].min()) for x in rr)
            net=min(float(x[1]) for x in rr)
            dd=max(float(x[2]) for x in rr)
            if dev:
                nn=[ev(b,c,ceil,lim,loss) for c in costs];tested+=len(nn)
                nliq=sum(x[5] for x in nn);nov=min(float(x[1]) for x in nn)
                # Preserve historic pass first, then recover known November.
                # Explicit development optimization, never an unseen test.
                rank=(int(lq+nliq==0),min(counts),sum(counts),int(nov>=1000),min(worst,nov),nov,net,-dd,-lq-nliq)
            else:
                rank=(int(lq==0),min(counts),sum(counts),worst,net,-dd,-lq)
            return (rank,legs,a,b,ceil,lim,loss)
        def evallegs(legs,ceil,lim,loss,dev=False,costs=anchors):
            return evaluate(legs,packed(legs),packed(legs,True),ceil,lim,loss,dev,costs)
        def keep(p,n):
            p.sort(key=lambda z:z[0],reverse=True);return p[:n]
        basepairs=[]
        for q in baselegs:
            spec=(q["stop_fraction"],q["tp_pct"],q["max_minutes"],q["trail_fraction"])
            basepairs.append((candidate(q["group"],q["filter"],spec),q["mtd_gate"]))
        basepar=(seed["month_ceiling"],seed["daily_limit"],seed["loss_guard"])
        base0=evallegs(basepairs,*basepar,False,allcost)
        expected={100:947.322267035537,200:-3309.5331700000006}
        baseline200=ev(base0[2],200,*basepar)
        assert abs(baseline200[0][:22].min()-expected[lev])<.01,(lev,baseline200[0][:22].min())
        print("V19_REFERENCE",lev,base0[0],flush=True)
        # Select a broad but bounded pool on training only. Keep candidates
        # with positive weak-month coverage for the locked portfolio, and
        # per-family leaders rather than all variations of one signal.
        basevals=ev(base0[2],200,*basepar)[0][:22]
        weakmonth=basevals<1000
        if not weakmonth.any():
            weakmonth=basevals<=np.quantile(basevals,.25)
        pool=[];byfamily=defaultdict(list);neighbors=defaultdict(list)
        for name,arr in data_groups.items():
            train=arr[arr[:,0]<train_end];nov=arr[arr[:,0]>=train_end]
            if len(train)<12:continue
            near=next((q for k,q in core.items() if name==k or name.startswith(k+"_confirm") or name.startswith(k+"_pull") or name.startswith(k+"_late")),None)
            if near:
                ss=near["stop_fraction"];tt=near["tp_pct"];cc=near["max_minutes"];tr=near["trail_fraction"]
                specs={(ss,tt,cc,tr)}
                specs.update((f,tt,cc,tr) for f in (.1,.15,.2,.25,.3,.35,.4,.5,.6,.7,.8,.9))
                specs.update((ss,t,cc,tr) for t in (1.,1.5,2.,2.5,3.,3.5,4.,5.,6.,7.,8.,10.))
                specs.update((ss,tt,c,tr) for c in (180,360,720,1440,2880,4320,7200))
                specs.update((ss,tt,cc,t) for t in (0.,.5,1.,1.5,2.,3.))
                if name==near["group"]:
                    specs.update((ss,round(tt+d,4),cc,tr) for d in (-.2,-.15,-.1,-.075,-.05,-.025,.025,.05,.075,.1,.15,.2,.25,.3,.4,.5) if tt+d>0)
                    specs.update((round(ss+d,4),tt,cc,tr) for d in (-.08,-.06,-.04,-.025,-.015,.015,.025,.04,.06,.08) if .06<=ss+d<=.92)
                    specs.update((ss,tt,max(60,cc+d),tr) for d in (-360,-180,-90,-60,-30,30,60,90,180,360))
                    specs.update((ss,tt,cc,round(tr+d,3)) for d in (-.3,-.2,-.1,.1,.2,.3) if tr+d>=0)
                if name!=near["group"]:
                    specs={(ss,tt,cc,tr),(max(.1,ss*.7),tt,cc,0.),(ss,tt*1.5,cc,0.),(ss,tt,1440,0.)}
            else:
                specs=set(itertools.product((.15,.3,.5,.7), (2.,4.,6.),(1440,4320),(0.,)))
            masks_here={}
            for label,fn in masks2.items():
                if near is None and label not in ("all","long","short","H1_align","H4_align","both_align","ADX20","range_ADX20","high_ATR_ratio","short_ADX25","long_ADX25","quiet20_0.5","quiet20_0.75","quiet20_trend_0.5","quiet20_counter_0.25","quiet20_body_0.5","quiet_align_0.5","entry_quiet_0.5","quiet_reclaim_0.5","basis_guard"):continue
                mm=fn(arr)
                mt=mm[arr[:,0]<train_end]
                if mt.sum()>=12:masks_here[label]=(mt,mm[arr[:,0]>=train_end])
            local=[];netbest=[];weakbest=[];novbest=[]
            for spec in sorted(specs):
                rt=sim(train,0,train_end,spec,1)
                rn=sim(nov,train_end,end,spec,1)
                for label,(mt,mn) in masks_here.items():
                    a=rt[mt];b=rn[mn]
                    x=np.column_stack((a,np.full(len(a),1e30)))
                    z=ev(x,200,1e30,0,1e30);tested+=1
                    if z[3]<8:continue
                    q=(name,label,spec,a,b)
                    if near and name==near["group"] and label==near["filter"]:neighbors[name].append(q)
                    cov=int(np.sum(z[0][:22]>=1000))
                    # Store small per-family rankings; candidate outcome is
                    # used for in-sample selection, never trade acceptance.
                    local.append(((int(z[5]==0),cov,float(z[1]),float(z[0][:22].min())),q))
                    netbest.append(((int(z[5]==0),float(z[1]),cov),q))
                    weakbest.append(((int(z[5]==0),int(np.sum(z[0][:22][weakmonth]>=1000)),float(z[0][:22][weakmonth].sum()),float(z[1])),q))
                    if len(b):
                        bn=np.column_stack((b,np.full(len(b),1e30)))
                        zz=ev(bn,200,1e30,0,1e30);tested+=1
                        # Separate pool explicitly permitted only in known-Nov
                        # development track, not training-only selection.
                        novbest.append(((int(z[5]+zz[5]==0),int(zz[1]>=1000),float(zz[1]),cov,float(z[1])),q))
                    if len(local)>100:local=keep(local,14)
                    if len(netbest)>100:netbest=keep(netbest,8)
                    if len(weakbest)>100:weakbest=keep(weakbest,12)
                    if len(novbest)>100:novbest=keep(novbest,8)
            qs=[x[1] for x in keep(local,14)+keep(netbest,8)+keep(weakbest,12)]
            ds=[x[1] for x in keep(novbest,8)]
            unique={ (q[0],q[1],q[2]):q for q in qs}
            byfamily[name]=list(unique.values())
            pool.extend((q,False) for q in unique.values())
            pool.extend((q,True) for q in ds)
            if len(byfamily)%20==0:print("POOL",lev,len(byfamily),tested,flush=True)
        # Include seed settings exactly, plus profiles chosen by diversity.
        def key(q):return (q[0],q[1],q[2])
        locked=[q for q,_ in basepairs]
        normal={key(q):q for q,d in pool if not d}
        normal.update({key(q):q for q in locked})
        developmental=dict(normal);developmental.update({key(q):q for q,d in pool})
        def fine_search():
            nonlocal tested
            start=evallegs(basepairs,*basepar,True,allcost)
            current=[start];archive=[start]
            for epoch in range(3 if lev==100 else 2):
                for i in range(len(basepairs)):
                    nxt=[]
                    for p in current[:5]:
                        old,gate=p[1][i]
                        choices=neighbors.get(old[0],[])+[old]
                        # Exact seed variants are available even if standalone
                        # rankings were poor; score in full chronological context.
                        for q in choices:
                            legs=p[1].copy();legs[i]=(q,gate)
                            nxt.append(evallegs(legs,p[4],p[5],p[6],True,allcost))
                            if len(nxt)>100:nxt=keep(nxt,20)
                        for g in (-1500.,-1000.,-750.,-500.,-250.,0.,250.,500.,750.,900.,1000.,1100.,1250.,1500.,1750.,2000.,1e30):
                            legs=p[1].copy();legs[i]=(old,g)
                            nxt.append(evallegs(legs,p[4],p[5],p[6],True,allcost))
                    current=keep(current+nxt,10);archive=keep(archive+current,50)
                    print("FINE",lev,epoch,i,tested,current[0][0],flush=True)
                nxt=[]
                for p in current[:5]:
                    for ceil,lim,loss in itertools.product((1000.,1100.,1250.,1400.,1500.,1600.,1750.,1900.,2000.,2100.,2250.,2500.,3000.,4000.),(0,1,2,3),(3000.,4000.,6000.,8000.,1e30)):
                        nxt.append(evaluate(p[1],p[2],p[3],ceil,lim,loss,True,allcost))
                        if len(nxt)>120:nxt=keep(nxt,25)
                current=keep(current+nxt,12);archive=keep(archive+current,50)
                # Avoid repeated development tuning once all debit scenarios
                # have met the target; signed rate validation still required.
                if current[0][0][0]==1 and current[0][0][1]==22 and current[0][0][3]==1:break
            return archive
        fine=fine_search()
        def runtrack(dev):
            nonlocal tested
            universe=list((developmental if dev else normal).values())
            # Score potential add-ons in the actual seed context; filter by
            # past-only MTD eligibility, never by realized future outcome.
            first=evallegs(basepairs,*basepar,dev)
            beam=keep([first]+(fine if dev else []),12);archive=keep([first]+(fine if dev else []),45)
            # Broad guards and gates around the exact V18 portfolio.
            zz=[]
            for ceil,lim,loss in itertools.product((1000.,1250.,1500.,1750.,2000.,2500.,3000.,4000.),(0,1,2,3),(3000.,4000.,6000.,8000.,1e30)):
                zz.append(evaluate(basepairs,first[2],first[3],ceil,lim,loss,dev))
            beam=keep(beam+zz,12);archive=keep(archive+beam,45)
            # Refine each seed component, varying one configuration and
            # realized-MTD gate at a time; retain strong diverse candidates.
            for epoch in range(2 if lev==100 else 3):
                for i in range(len(basepairs)):
                    nxt=[]
                    for p in beam[:4]:
                        old,gate=p[1][i]
                        near=[q for q in universe if q[0]==old[0] or q[0].startswith(old[0]+"_confirm") or q[0].startswith(old[0]+"_pull")]
                        near=near[:100]
                        for q in near+[old]:
                            for g in set((gate,-1000.,0.,500.,1000.,1500.,1e30)):
                                legs=p[1].copy();legs[i]=(q,g)
                                nxt.append(evallegs(legs,p[4],p[5],p[6],dev))
                                if len(nxt)>120:nxt=keep(nxt,20)
                    beam=keep(beam+nxt,12);archive=keep(archive+beam,45)
                    print("LOCAL",lev,dev,epoch,i,tested,beam[0][0],flush=True)
                # Alternative sleeve selection and recovery. All candidates
                # replayed in order and positions never overlap.
                nxt=[]
                for p in beam[:2]:
                    used={q[0] for q,_ in p[1]}
                    for q in universe:
                        if q[0] in used:continue
                        for gate in (-1000.,0.,500.,1000.,1e30):
                            a=np.concatenate((p[2],np.column_stack((q[3],np.full(len(q[3]),gate)))))
                            b=np.concatenate((p[3],np.column_stack((q[4],np.full(len(q[4]),gate)))))
                            a=a[np.argsort(a[:,0],kind="stable")];b=b[np.argsort(b[:,0],kind="stable")]
                            nxt.append(evaluate(p[1]+[(q,gate)],a,b,p[4],p[5],p[6],dev))
                            if len(nxt)>160:nxt=keep(nxt,24)
                beam=keep(beam+nxt,12);archive=keep(archive+beam,45)
                print("ADDON",lev,dev,epoch,tested,beam[0][0],flush=True)
            # Evaluate all stress costs and both funding modes on the small
            # finalists. Training-only track never ranks by November.
            finalists=keep(archive+beam,60)+[first]+(fine[:15] if dev else [])
            full=[]
            for p in finalists:
                modes=[]
                for fundmode in (0,1):
                    aa=[];bb=[]
                    for q,gate in p[1]:
                        name,label,spec=q[:3]
                        arr=data_groups[name];arr=arr[masks2[label](arr)]
                        t=sim(arr,0,train_end,spec,fundmode)
                        n=sim(arr,train_end,end,spec,fundmode)
                        aa.append(np.column_stack((t,np.full(len(t),gate))))
                        bb.append(np.column_stack((n,np.full(len(n),gate))))
                    a=np.concatenate(aa);b=np.concatenate(bb)
                    modes.append((a[np.argsort(a[:,0],kind="stable")],b[np.argsort(b[:,0],kind="stable")]))
                checks=[ev(a,c,p[4],p[5],p[6]) for a,b in modes for c in allcost]
                tested+=len(checks)
                counts=[int(np.sum(x[0][:22]>=1000)) for x in checks]
                lq=sum(x[5] for x in checks)
                worst=min(float(x[0][:22].min()) for x in checks)
                net=min(float(x[1]) for x in checks);dd=max(float(x[2]) for x in checks)
                if dev:
                    nn=[ev(b,c,p[4],p[5],p[6]) for a,b in modes for c in allcost]
                    tested+=len(nn)
                    nov=min(float(x[1]) for x in nn);nliq=sum(x[5] for x in nn)
                    rank=(int(lq+nliq==0),min(counts),sum(counts),int(nov>=1000),min(worst,nov),nov,net,-dd,-lq-nliq)
                else:rank=(int(lq==0),min(counts),sum(counts),worst,net,-dd,-lq)
                full.append((rank,p,modes))
            full.sort(key=lambda z:z[0],reverse=True)
            return full[0]
        for dev in (True,):
            rank,p,modes=runtrack(dev)
            track="known_november_development" if dev else "train_only"
            profile=dict(leverage=lev,track=track,rank=list(rank),evaluations=tested,legs=[dict(group=q[0],filter=q[1],stop_fraction=q[2][0],tp_pct=q[2][1],max_minutes=q[2][2],trail_fraction=q[2][3],mtd_gate=gate) for q,gate in p[1]],month_ceiling=p[4],daily_limit=p[5],loss_guard=p[6])
            selected.append(profile);print("SELECTED",json.dumps(profile),flush=True)
            for mode,(a,b) in enumerate(modes):
                for period,arr,mi in (("train",a,range(22)),("november_known_development" if dev else "november_temporal_check",b,[22])):
                    for cost in COSTS:
                        v,net,dd,n,w,lq,idx=ev(arr,cost,p[4],p[5],p[6])
                        sub=v[:22] if period=="train" else v[22:]
                        t=arr[idx]
                        assert np.all(t[1:,0]>t[:-1,1]) and np.all(weekday[t[:,0].astype(np.int64)]<5)
                        assert abs(sub.sum()-net)<1e-5
                        summary.append(dict(leverage=lev,track=track,period=period,funding_mode="signed_proxy" if mode==0 else "debit_only",cost=cost,net_points=net,trades=n,wins=w,liquidations=lq,months_ge_1pct=int(np.sum(sub>=1000)),min_month_points=float(sub.min()),closed_dd_points=dd))
                        monthly.extend(dict(leverage=lev,track=track,period=period,funding_mode=mode,cost=cost,month=str(pd.Period("2025-01",freq="M")+i),net_points=v[i]) for i in mi)
                        if cost==200:
                            for row in t:
                                alltrades.append(dict(leverage=lev,track=track,period=period,funding_mode=mode,cost=cost,entry_utc=str(m.index[int(row[0])]),exit_utc=str(m.index[int(row[1])]),side=int(row[4]),entry=row[5],exit=row[6],net_points=row[2]-cost,liquidation=int(row[7]),reason=int(row[9])))
            pd.DataFrame(summary).to_csv(OUT/"summary.csv",index=False)
            pd.DataFrame(monthly).to_csv(OUT/"monthly.csv",index=False)
            pd.DataFrame(alltrades).to_csv(OUT/"trades_200.csv",index=False)
            (OUT/"quality.json").write_text(json.dumps(dict(profiles=selected,baseline_preserved="V19 50x locked and unchanged; only 100x and 200x searched",funding="observed-rate proxies only, signed and debit-only",margin="exact isolated 1/leverage; 0.25% MMR, no extra collateral",stop_fill="adverse-first mark and trade OHLC",november="Previously examined partial month; all selected V20 profiles are development-optimized, not holdout",genuine_forward="not available",return_units="normalized points, not account returns",candle_count=train_end),indent=2,default=float))
if __name__=="__main__":main()
