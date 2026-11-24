#!/usr/bin/env python3
"""Frozen V16: raw candle entry/exit search, no historical trade-ledger inputs.

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

OUT=Path("analysis/v16_frozen_execution_validation")
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
    # Exact frozen V16 rules, no configuration search.
    specs=(
       ("H1_RSI30_reversal","short_ADX25",(2.,4.,4320,0,0.,0),1e30),
       ("Shock_Donchian","long_ADX25",(1.8,3.,1440,1,0.,0),1e30),
       ("EMA20_ADX_reclaim","all",(1.75,6.,4320,0,0.,0),1e30),
       ("H1_Donchian12","range_ADX20",(1.8,3.5,1440,1,0.,0),-1000.),
    )
    filters=dict(masks)
    streams=[]; signals=[]
    train_end=int(m.index.searchsorted(pd.Timestamp("2026-11-01",tz="Asia/Kolkata").tz_convert("UTC")))
    for leg,(name,mask,spec,ceiling) in enumerate(specs):
        a=np.array(sorted(groups[name].values(),key=lambda x:x[0]),float)
        a=a[filters[mask](a)]
        assert len(a)>0
        sl,tp,cap,typ,trail,sttf=spec
        for j,side,mid,cyc,atr,*_ in a:
            signals.append([j,side,mid,cyc,atr,leg,sl,tp,cap,typ,ceiling])
        a=a[a[:,0]<train_end]
        x=exits(a[:,0].astype(np.int64),a[:,1].astype(np.int64),a[:,2],a[:,3].astype(np.int64),a[:,4],op,hi,lo,cl,month,trend,eh,train_end,*spec)
        streams.append(np.column_stack((x,np.full(len(x),ceiling))))
    a=np.concatenate(streams);a=a[np.argsort(a[:,0],kind="stable")]
    checks=[]
    expected={0:(81544.2875794394,75),200:(75282.7685501421,88)}
    for cost in COSTS:
        vals,n,d,c,w,_=schedule(a,month,float(cost),2000.,1,day,8000.)
        if cost in expected:
            assert abs(n-expected[cost][0])<.01 and c==expected[cost][1],(cost,n,c,expected[cost])
        checks.append(dict(cost=cost,net_points=n,trades=c,months_ge_1pct=int(np.sum(vals>=1000)),min_month_points=float(vals.min())))
    pd.DataFrame(checks).to_csv(OUT/"frozen_parity.csv",index=False)
    print("FROZEN_PARITY",checks,flush=True)
    signal=np.array(sorted(signals,key=lambda z:z[0]),float)
    # Native institutional observations. Validate continuity, timestamps,
    # OHLC bounds and finiteness, never replace a missing rate with zero.
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
    rows=[];mons=[];liqrows=[]
    for period,first,last in (("train",0,train_end),("november_temporal_holdout",train_end,end)):
        for mode,lev in [("no_funding",0),("hourly_rate_proxy",0),("interval_rate_proxy",0),("debit_only_stress",0)]+[("hourly_rate_proxy",v) for v in (5,10,20,25,50,100,200)]:
            for cost in (COSTS if lev==0 else (0,100,200)):
                trades,vals,credit,debit,dd,mtm,lc,minbuffer=run_frozen(signal,first,last,month,day,op,hi,lo,cl,mo,mh,ml,rate,interval_rate,adverse_long,adverse_short,sw,mode,lev,float(cost))
                sub=vals[:22] if period=="train" else vals[22:23]
                total=float(sub.sum())
                assert abs(total-sum(t[7] for t in trades))<1e-5,(period,mode,lev,cost,total)
                if period=="train" and mode=="no_funding" and cost in expected:
                    assert abs(total-expected[cost][0])<.01 and len(trades)==expected[cost][1],("on demand parity",cost,total,len(trades))
                rows.append(dict(period=period,mode=mode,leverage=lev,cost=cost,net_points=total,trades=len(trades),wins=sum(t[7]>0 for t in trades),months_ge_1pct=int(np.sum(sub>=1000)),min_month_points=float(sub.min()),funding_credits=credit,funding_debits=debit,net_funding=credit-debit,closed_dd_points=dd,mtm_close_dd_points=mtm,liquidation_events=lc,min_maintenance_buffer_per_btc=minbuffer))
                mons.extend(dict(period=period,mode=mode,leverage=lev,cost=cost,month=str(pd.Period("2025-01",freq="M")+i),net_points=float(vals[i])) for i in (range(22) if period=="train" else [22]))
                if mode=="hourly_rate_proxy" and cost in (0,200):
                    for t in trades:
                        liqrows.append(dict(period=period,leverage=lev,cost=cost,entry_utc=str(m.index[int(t[0])]),exit_utc=str(m.index[int(t[1])]),side=int(t[2]),leg=specs[int(t[3])][0],entry=t[4],exit=t[5],funding=t[6],net=t[7],reason=t[8]))
    pd.DataFrame(rows).to_csv(OUT/"validation_summary.csv",index=False)
    pd.DataFrame(mons).to_csv(OUT/"validation_monthly.csv",index=False)
    pd.DataFrame(liqrows).to_csv(OUT/"funding_liquidation_trades.csv",index=False)
    quality=dict(frozen_source_commit="8cb6dc0cf29ceb6294dad03fed420bb960da1785",frozen_rules=specs,monthly_profit_ceiling=2000,daily_entries=1,monthly_loss_guard=8000,parity_verified=True,training_end=str(m.index[train_end-1]),holdout_start=str(m.index[train_end]),holdout_end=str(m.index[end-1]),holdout_partial_month=True,holdout_prior_use="November excluded from V16 optimization, but not proven untouched across prior project research; no retuning here",genuine_untouched="Requires forward candles after freeze on 2026-11-24; not available in this archive",funding_data="actual hourly rate OHLC, not account settlement",funding_price_proxy="MARK:BTCUSD open, underlying index not available",funding_rate_proxy="previous completed hour close, alternate prior 8h boundary observation, adverse debit-only scenario",funding_schedule="minute proration before 2025-09-08 16 UTC; 0/8/16 UTC thereafter",liquidation_model="isolated margin, one lot, 0.25% maintenance, no auto-top-up; conservative mark adverse first; full initial margin loss proxy if liquidation, exact engine fills/fees unverified; no account balance simulation",funding_settlement_verified=False,exchange_liquidation_engine_verified=False,retuned=False)
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2))
    print(pd.DataFrame(rows).to_string(index=False),flush=True)

def run_frozen(signal,first,last,month,day,op,hi,lo,cl,mo,mh,ml,rate,interval_rate,adverse_long,adverse_short,sw,mode,lev,cost):
    vals=np.zeros(23);used=set();trades=[]; occupied=-1;last_day=-1;today=0
    credit=debit=equity=peak=dd=mtm_peak=mtmdd=0.;lc=0;minbuffer=float("inf")
    for sig in signal:
        j=int(sig[0]);side=int(sig[1]);cyc=int(sig[3]);atr=sig[4];leg=int(sig[5]);sl,tp,cap,typ,ceiling=sig[6:]
        if j<first or j>=last or j<=occupied or (cyc>0 and cyc in used):continue
        m=month[j];d=day[j]
        if d!=last_day:last_day=d;today=0
        if today>=1 or vals[m]>=2000 or vals[m]<=-8000 or vals[m]>=ceiling:continue
        today+=1
        if cyc>0:used.add(cyc)
        ep=op[j]+side*SLIP
        risk=atr*sl if typ==1 else ep*sl/100.
        stop=ep-side*risk;target=ep+side*(risk*tp if typ==1 else ep*tp/100.)
        fund=0.;x=min(j+int(cap)-1,last-1);xm=cl[x];reason="timeout_or_test_end"
        for k in range(j,x+1):
            if mode!="no_funding" and k>j:
                if k<sw or k%480==0:
                    r=rate[k]
                    if mode=="interval_rate_proxy" and k>=sw:r=interval_rate[k]
                    if mode=="debit_only_stress":r=adverse_long[k] if side==1 else adverse_short[k]
                    f=-side*mo[k]*r/(480. if k<sw else 1.)
                    fund+=f;vals[month[k]]+=f
                    credit+=max(f,0.);debit+=max(-f,0.)
            if lev:
                # Liquidation uses native mark-price adverse extreme, not trade
                # price. Current small-position maintenance rate; assume entry
                # fee reduces allocated equity, conservative adverse-first.
                mark=ml[k] if side==1 else mh[k]
                buffer=ep/lev+fund-FEE*ep+side*(mark-ep)-.0025*mark
                minbuffer=min(minbuffer,buffer)
                if buffer<=0:
                    x=k;xm=mark;reason="mark_liquidation";lc+=1;break
            if (lo[k]<=stop if side==1 else hi[k]>=stop):
                x=k;xm=min(op[k],stop) if side==1 else max(op[k],stop);reason="stop";break
            if (hi[k]>=target if side==1 else lo[k]<=target):
                x=k;xm=target;reason="target";break
            marked=equity+fund+side*(cl[k]-side*SLIP-ep)-FEE*(ep+cl[k]-side*SLIP)-cost
            mtm_peak=max(mtm_peak,marked);mtmdd=max(mtmdd,mtm_peak-marked)
        xp=xm-side*SLIP
        if reason=="mark_liquidation":
            # Isolated collateral loss bound; accrued funding is included in
            # depleted margin, so do not double count it in net.
            net=-ep/lev-FEE*ep-cost
            exnet=net-fund
        else:
            exnet=side*(xp-ep)-FEE*(ep+xp)-cost;net=exnet+fund
        vals[month[x]]+=exnet;equity+=net;peak=max(peak,equity);dd=max(dd,peak-equity)
        mtm_peak=max(mtm_peak,equity);mtmdd=max(mtmdd,mtm_peak-equity)
        trades.append((j,x,side,leg,ep,xp,fund,net,reason));occupied=x
    return trades,vals,credit,debit,dd,mtmdd,lc,minbuffer if lev else None

if __name__=="__main__":main()
