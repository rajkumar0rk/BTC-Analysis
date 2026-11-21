#!/usr/bin/env python3
"""Audit improvements to EMA20/Supertrend 15m/1h fixed TP/SL first-touch.

Preserves original indicator and signal definitions; compares eight prespecified
entry quality gates, with NO training-period fitting of filter parameters.
2025 vs Jan-Oct 2026 are separate reporting windows (not an optimized OOS
evaluation). All filters use only the latest fully closed signal/higher candle.
Fixed 1M OHLC first-touch, exclusive positions, conservative same-minute ties.
Costs: per-side taker 0.05% or hypothetical maker 0.02%, GST 18%; no funding,
spread, slippage, mark-price liquidation or maker fill modeling.
Point P&L: ETH distances normalized to BTC equivalence via 80,000/entry ETH.
"""
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from replay_ema_st_15m_entries_1m_exits_20261121 import load
from replay_btc_ema_st_screenshot import indicators

OUT=ROOT/"analysis"/"ema_st_entry_quality_oos_20261121"
OUT.mkdir(parents=True,exist_ok=True)
ENTRY_CUTOFF=int(pd.Timestamp("2026-11-01",tz="UTC").timestamp())
PAIRS=((200,100),(300,100),(600,200),(900,300))
GATES=("baseline","ema_slope3","candle_body40","trend_age3",
       "higher_ST","higher_ST_and_EMA","vol_ratio_2","atr_ratio_1p2",
       "near_EMA40ATR","ema_slope3_and_higher_ST","ADX25")
TICKETS={("BTC","15m",200,100):(343,697,2),("BTC","15m",300,100):(271,760,0),
 ("BTC","15m",600,200):(246,703,0),("BTC","15m",900,300):(214,637,0),
 ("ETH","15m",200,100):(327,680,17),("ETH","15m",300,100):(246,762,9),
 ("ETH","15m",600,200):(250,699,3),("ETH","15m",900,300):(238,642,1),
 ("BTC","1h",200,100):(133,251,3),("BTC","1h",300,100):(103,283,0),
 ("BTC","1h",600,200):(88,286,0),("BTC","1h",900,300):(87,265,0),
 ("ETH","1h",200,100):(116,214,3),("ETH","1h",300,100):(86,247,0),
 ("ETH","1h",600,200):(84,248,0),("ETH","1h",900,300):(83,235,0)}

def rma(x,n):
    return pd.Series(x).ewm(alpha=1/n,adjust=False,min_periods=n).mean().to_numpy()

def adx14(bars):
    h=bars.high.to_numpy()
    l=bars.low.to_numpy()
    c=bars.close.to_numpy()
    up=np.r_[0.,np.diff(h)]
    dn=np.r_[0.,-np.diff(l)]
    plus=np.where((up>dn)&(up>0),up,0.)
    minus=np.where((dn>up)&(dn>0),dn,0.)
    pclose=np.r_[np.nan,c[:-1]]
    tr=np.maximum(h-l,np.maximum(abs(h-pclose),abs(l-pclose)))
    tr[0]=h[0]-l[0]
    base=rma(tr,14)
    with np.errstate(invalid="ignore",divide="ignore"):
        pdi=100*rma(plus,14)/base
        mdi=100*rma(minus,14)/base
        dx=100*abs(pdi-mdi)/(pdi+mdi)
        out=rma(dx,14)
    return out

def aggregate(minute,minutes):
    b=minute.resample(f"{minutes}min",origin="epoch",label="left",closed="left").agg(
      {"open":"first","high":"max","low":"min","close":"last","volume":"sum","time":"count"})
    assert (b.time==minutes).all()
    assert len(b)*minutes==len(minute)
    b=indicators(b.drop(columns="time"))
    b["adx14"]=adx14(b)
    return b

def all_signals(bars,higher,mins,higher_mins,clock):
    out=[]
    d=bars.dir.to_numpy()
    ema=bars.ema.to_numpy()
    atr=bars.atr14.to_numpy()
    ar=bars.atr_ratio.to_numpy()
    vr=bars.volume_ratio.to_numpy()
    hi=bars.high.to_numpy()
    lo=bars.low.to_numpy()
    cl=bars.close.to_numpy()
    op=bars.open.to_numpy()
    ad=bars.adx14.to_numpy()
    hd=higher.dir.to_numpy()
    hc=higher.close.to_numpy()
    he=higher.ema.to_numpy()
    for i in range(36,len(bars)-1):
        j=(i+1)*mins
        if clock[j]>=ENTRY_CUTOFF:break
        if not (np.isfinite(ema[i]) and np.isfinite(atr[i])
                and np.isfinite(ar[i]) and np.isfinite(vr[i])): continue
        if ar[i]<1.0 or vr[i]<1.5:continue
        side=0
        if d[i]==d[i-1]==-1 and lo[i]<=ema[i] and cl[i]>ema[i]:
            side=1
        elif d[i]==d[i-1]==1 and hi[i]>=ema[i] and cl[i]<ema[i]:
            side=-1
        if side==0:continue
        k=j//higher_mins-1
        hst=k>=0 and hd[k]==-side
        hema=k>=0 and np.isfinite(he[k]) and side*(hc[k]-he[k])>0
        eslope=(side*(ema[i]-ema[i-3])>0) if i>=3 else False
        rng=max(1.e-9,hi[i]-lo[i])
        body=(side*(cl[i]-op[i])>0 and abs(cl[i]-op[i])/rng>=0.4)
        age=(i>=2 and d[i]==d[i-1]==d[i-2])
        gates={
            "baseline":True,
            "ema_slope3":eslope,
            "candle_body40":body,
            "trend_age3":age,
            "higher_ST":hst,
            "higher_ST_and_EMA":hst and hema,
            "vol_ratio_2":vr[i]>=2,
            "atr_ratio_1p2":ar[i]>=1.2,
            "near_EMA40ATR":abs(cl[i]-ema[i])<=0.4*atr[i],
            "ema_slope3_and_higher_ST":eslope and hst,
            "ADX25":np.isfinite(ad[i]) and ad[i]>=25,
        }
        out.append((int(j),int(side),gates))
    return out

def first_touch(op,hi,lo,j,entry,side,tp,sl):
    # Early-exit chunks are exactly equivalent to full-history TP / SL scans,
    # but avoid rereading hundreds of thousands of bars per signal.
    k=j
    N=len(op)
    while k<N:
        e=min(k+1440,N)
        if side>0:
            hits=(hi[k:e]>=tp)|(lo[k:e]<=sl)
        else:
            hits=(lo[k:e]<=tp)|(hi[k:e]>=sl)
        loc=np.flatnonzero(hits)
        if len(loc):
            end=k+int(loc[0])
            if side>0:
                tp_hit=hi[end]>=tp
                sl_hit=lo[end]<=sl
                open_tp=op[end]>=tp
                open_sl=op[end]<=sl
            else:
                tp_hit=lo[end]<=tp
                sl_hit=hi[end]>=sl
                open_tp=op[end]<=tp
                open_sl=op[end]>=sl
            if open_tp:result="TP"
            elif open_sl:result="SL"
            elif tp_hit and sl_hit:result="AMBIGUOUS"
            elif tp_hit:result="TP"
            else:result="SL"
            return end,result
        k=e
    return None

def replay(asset,m,signals,gate,tp_points,sl_points):
    op=m.open.to_numpy(float);hi=m.high.to_numpy(float);lo=m.low.to_numpy(float)
    clock=m.time.to_numpy(np.int64)
    last_exit_j=-1
    rows=[]
    for j,side,gates in signals:
        if not gates[gate] or j<=last_exit_j:continue
        ep=float(op[j])
        scale=1.0 if asset=="BTC" else ep/80000.
        tpp=ep+side*tp_points*scale
        slp=ep-side*sl_points*scale
        response=first_touch(op,hi,lo,j,ep,side,tpp,slp)
        if response is None:continue
        end,outcome=response
        last_exit_j=end
        xp=(tpp if outcome=="TP" else slp)
        gross=(tp_points if outcome=="TP" else -sl_points)
        # ETH gross is normalized to price points vs 80k BTC benchmark.
        # Normalized per-side fees: BTC direct, ETH times 80000/entry price.
        normalized=(1.0 if asset=="BTC" else 80000.0/ep)
        taker_fee=(ep+xp)*.0005*1.18*normalized
        maker_fee=(ep+xp)*.0002*1.18*normalized
        year=(2025 if clock[j]<int(pd.Timestamp("2026-01-01",tz="UTC").timestamp()) else 2026)
        mon=pd.Timestamp(clock[j],unit="s",tz="UTC").strftime("%Y-%m")
        rows.append({"entry_j":j,"exit_j":end,"side":side,"result":outcome,
                     "hold_minutes":int(end-j),"gross_equiv_points":gross,
                     "net_taker_equiv_points":gross-taker_fee,
                     "net_maker_equiv_points":gross-maker_fee,
                     "year":year,"month":mon})
    return rows

def stats(rows):
    if not rows:return {"trades":0}
    df=pd.DataFrame(rows)
    d={}
    d["trades"]=int(len(df))
    for res in ("TP","SL","AMBIGUOUS"):
        d[res]=int((df.result==res).sum())
    resolved=d["TP"]+d["SL"]
    d["TP_first_rate_pct"]=round(d["TP"]/resolved*100,2) if resolved else None
    for key in ("gross_equiv_points","net_taker_equiv_points","net_maker_equiv_points"):
        d["avg_"+key]=round(float(df[key].mean()),3)
        d["sum_"+key]=round(float(df[key].sum()),2)
    d["avg_hold_minutes"]=round(float(df.hold_minutes.mean()),1)
    d["under_30m_fraction_pct"]=round(100*float((df.hold_minutes<=30).mean()),2)
    for year in (2025,2026):
        x=df[df.year==year]
        d[f"{year}_trades"]=int(len(x))
        d[f"{year}_taker_avg_points"]=round(float(x.net_taker_equiv_points.mean()),3) if len(x) else None
        d[f"{year}_taker_sum_points"]=round(float(x.net_taker_equiv_points.sum()),2)
        d[f"{year}_taker_profitable_months"]=int((x.groupby("month").net_taker_equiv_points.sum()>0).sum()) if len(x) else 0
    return d

def main():
    allstats={"method":"15m or 1h confirmed EMA20+ST 10,3 filtered entry; 1m fixed first touch, no other exits, one exclusive position",
        "fees":"0.05% taker or hypothetical 0.02% maker per side +18% GST, no funding/slippage/spread",
        "no_fee_rebates_assumed":True,
        "signals_date_range":"2025-01-01 through 2026-10-31 UTC inclusive",
        "out_of_sample":"Report 2025 and 2026 Jan-Oct separately, neither used to fit parameters in this exploratory grid.",
        "variants":list(GATES),
        "results":{}}
    flat=[]
    for asset in ("BTC","ETH"):
        m,b15,manifest=load(asset)
        clock=m.time.to_numpy(np.int64)
        assert clock[0]==int(pd.Timestamp("2025-01-01",tz="UTC").timestamp())
        b15["adx14"]=adx14(b15)
        b60=aggregate(m,60);b240=aggregate(m,240)
        for tf,mins,bars,higher,hm in (("15m",15,b15,b60,60),("1h",60,b60,b240,240)):
            signals=all_signals(bars,higher,mins,hm,clock)
            print("SIGNALS",asset,tf,len(signals),flush=True)
            for gate in GATES:
                for tp,sl in PAIRS:
                    trades=replay(asset,m,signals,gate,tp,sl)
                    st=stats(trades)
                    if gate=="baseline":
                        expected=TICKETS[(asset,tf,tp,sl)]
                        actual=tuple(st[k] for k in ("TP","SL","AMBIGUOUS"))
                        assert actual==expected,(asset,tf,tp,sl,actual,expected)
                    name=f"{asset}_{tf}_{gate}_{tp}_{sl}"
                    allstats["results"][name]=st
                    flat.append(dict(asset=asset,timeframe=tf,filter=gate,tp=tp,sl=sl,**st))
                    print("FILTER_RESULT",name,json.dumps(st),flush=True)
    data=pd.DataFrame(flat)
    data.to_csv(OUT/"filter_grid.csv",index=False)
    (OUT/"full_summary.json").write_text(json.dumps(allstats,indent=2)+"\n")
    # Screen improvements: no tiny samples; favor positive after-cost performance
    # in BOTH periods. Does not constitute proof of forward live edge.
    strong=data[(data["2025_trades"]>=30)&(data["2026_trades"]>=20)&
                (data["2025_taker_avg_points"]>0)&(data["2026_taker_avg_points"]>0)]
    cols=["asset","timeframe","filter","tp","sl","trades","TP_first_rate_pct",
          "avg_gross_equiv_points","avg_net_taker_equiv_points",
          "2025_trades","2025_taker_avg_points","2026_trades","2026_taker_avg_points"]
    print("ROBUST_POSITIVE_TAKER_CANDIDATES",strong[cols].to_json(orient="records"),flush=True)
    for asset in ("BTC","ETH"):
        for tf in ("15m","1h"):
            subset=data[(data.asset==asset)&(data.timeframe==tf)]
            best=subset.sort_values("avg_net_taker_equiv_points",ascending=False).head(8)
            print("TOP_AFTER_COST",asset,tf,best[cols].to_json(orient="records"),flush=True)
    print("DONE_ENTRY_QUALITY_FILTER_MATRIX",str(OUT),flush=True)

if __name__=="__main__":
    main()
