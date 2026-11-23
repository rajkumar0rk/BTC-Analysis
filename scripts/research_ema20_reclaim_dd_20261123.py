#!/usr/bin/env python3
"""Reconstruct and audit BTCUSD 15m Supertrend/EMA20 reclaim drawdown controls.

Historical, exploratory research. No original 77-trade ledger is available.
If replay does not match the cited baseline, its comparisons are NOT a validation
of the earlier +114.68% claim. No look-ahead feature inputs or retuned rules.
"""
from pathlib import Path
from itertools import product
import numpy as np
import pandas as pd

DATA = Path("data/delta_india/BTCUSD/1m")
OUT = Path("analysis/ema20_reclaim_dd_20261123")
FEE = .0005 * 1.18  # Delta taker 0.05%, GST 18% on trading fee
SLIP = .0002        # adverse price slippage per side
START = pd.Timestamp("2025-01-01",tz="UTC")
END = pd.Timestamp("2026-11-01",tz="UTC")

def load():
    paths = sorted(DATA.glob("20??-??.csv.gz"))
    parts=[]
    for p in paths:
        if p.stem[:7] > "2026-10": continue
        x=pd.read_csv(p,compression="gzip",usecols=["time","open","high","low","close","volume"])
        x["time"]=pd.to_datetime(x.time.astype("int64"),unit="s",utc=True)
        parts.append(x.set_index("time"))
    d=pd.concat(parts).sort_index().loc[START:END-pd.Timedelta(minutes=1)]
    if d.index.has_duplicates: raise RuntimeError("Duplicate 1m timestamps")
    expected=pd.date_range(START,END-pd.Timedelta(minutes=1),freq="min")
    if not d.index.equals(expected): raise RuntimeError("Missing or misordered 1m timestamps")
    return d

def rma(a, n):
    out=np.full(len(a),np.nan)
    valid=np.flatnonzero(np.isfinite(a))
    if len(valid) < n: return out
    seed=valid[0]+n-1
    out[seed]=np.mean(a[valid[0]:seed+1])
    for i in range(seed+1,len(a)):
        out[i]=(out[i-1]*(n-1)+a[i])/n
    return out

def features(d):
    m=d.resample("15min",label="left",closed="left").agg({"open":"first","high":"max","low":"min","close":"last","volume":"sum"})
    assert d.close.resample("15min").count().eq(15).all()
    c=m.close.to_numpy(); hi=m.high.to_numpy(); lo=m.low.to_numpy()
    op=m.open.to_numpy()
    tr=np.maximum(hi-lo,np.maximum(np.abs(hi-np.roll(c,1)),np.abs(lo-np.roll(c,1))))
    tr[0]=hi[0]-lo[0]
    atr=rma(tr,10)
    basic_u=(hi+lo)/2 + 3*atr
    basic_l=(hi+lo)/2 - 3*atr
    upper=np.full(len(c),np.nan);lower=np.full(len(c),np.nan)
    direction=np.zeros(len(c),dtype="int8")
    first=np.flatnonzero(np.isfinite(atr))[0]
    upper[first]=basic_u[first];lower[first]=basic_l[first]
    direction[first]=-1
    for k in range(first+1,len(c)):
        upper[k]=basic_u[k] if basic_u[k]<upper[k-1] or c[k-1]>upper[k-1] else upper[k-1]
        lower[k]=basic_l[k] if basic_l[k]>lower[k-1] or c[k-1]<lower[k-1] else lower[k-1]
        if direction[k-1]==1:
            direction[k]=-1 if c[k]<lower[k] else 1
        else:
            direction[k]=1 if c[k]>upper[k] else -1
    m["direction"]=direction
    m["ema20"]=pd.Series(c,index=m.index).ewm(span=20,adjust=False).mean()
    m["atr_pct"]=100*atr/c
    m["vol_ratio"]=m.volume/m.volume.rolling(20,min_periods=20).mean()
    m["body_ratio"]=np.abs(m.close-m.open)/(m.high-m.low).replace(0,np.nan)
    m["close_strength"]=np.abs(m.close-m.ema20)/m.close*100
    return m

def candidates(m):
    arr=[]
    armed=0; spent=False; age=0; prev_dir=0
    for k in range(50,len(m)-1):
        side=int(m.direction.iloc[k])
        if side != prev_dir:
            armed=0;spent=False;age=0;prev_dir=side
            continue  # never enter on Supertrend flip candle
        age+=1
        if spent or side==0: continue
        x=m.iloc[k]; ema=float(x.ema20)
        if armed==0:
            # LONG: touch EMA20 and close below it; SHORT inverse.
            if (side==1 and x.low<=ema and x.close<ema) or (side==-1 and x.high>=ema and x.close>ema):
                armed=k
            continue
        # Reclaim AFTER a distinct completed 15m set-up candle
        if (side==1 and x.close>ema) or (side==-1 and x.close<ema):
            j=k+1
            arr.append(dict(k=j,entry_ix=j*15,side=side,signal_time=str(m.index[k]),
                 entry_time=str(m.index[j]),atr_pct=float(x.atr_pct),
                 vol_ratio=float(x.vol_ratio),body_ratio=float(x.body_ratio),
                 close_strength=float(x.close_strength),trend_age=age))
            spent=True
    return pd.DataFrame(arr)

def replay(a, op, hi, lo, cl, stop=.03, take=.09, activation=.0825, lock=0):
    # a is pre-entry signal generated on completed 15m candle.
    entry_idx=int(a.entry_ix);side=int(a.side)
    entry_mid=float(op[entry_idx]);en=entry_mid*(1+side*SLIP)
    st=en*(1-side*stop);tp=en*(1+side*take)
    activated=False; exit_idx=len(op)-1
    px=float(cl[-1]);why="end"
    for j in range(entry_idx,len(op)):
        o=float(op[j]);h=float(hi[j]);l=float(lo[j])
        if (side==1 and l<=st) or (side==-1 and h>=st):
            px=min(o,st) if side==1 else max(o,st);why="stop";exit_idx=j;break
        if (side==1 and h>=tp) or (side==-1 and l<=tp):
            px=tp;why="target";exit_idx=j;break
        if not activated and ((side==1 and h>=en*(1+activation)) or (side==-1 and l<=en*(1-activation))):
            activated=True
            st=max(st,en*(1+lock)) if side==1 else min(st,en*(1-lock))
    ex=px*(1-side*SLIP)
    net_pct=100*(side*(ex-en)-FEE*(en+ex))/en
    return dict(exit_ix=exit_idx,net_pct=net_pct,exit_time=exit_idx,reason=why,activation=activated)

def choose(candidates_, results, predicate=None, cooldown=0):
    ledger=[];last_exit=-1;skip=0
    for i,a in candidates_.iterrows():
        if a.entry_ix<=last_exit: continue
        if predicate and not predicate(a): continue
        if skip>0:
            skip-=1;continue
        r=results[i]
        ledger.append({**a.to_dict(),**r})
        last_exit=r["exit_ix"]
        if r["net_pct"]<0: skip=cooldown
    return ledger

def stats(ledger):
    if not ledger:return dict(n=0,net_sum_pct=0,compounded_pct=0,dd_pct=0,months_pos=0,worst_month_pct=0,net2025=0,net2026=0)
    x=np.array([z["net_pct"] for z in ledger])/100
    eq=np.cumprod(1+x)
    peaks=np.maximum.accumulate(np.r_[1,eq])[:-1]
    dd=100*max(0,float(np.max(1-eq/peaks)))
    dates=pd.to_datetime([z["entry_time"] for z in ledger],utc=True)
    s=pd.Series(x,index=dates)
    months=s.groupby(s.index.to_period("M")).apply(lambda g:(np.prod(1+g)-1)*100)
    full=pd.period_range("2025-01","2026-10",freq="M")
    months=months.reindex(full,fill_value=0)
    y25=months.loc["2025-01":"2025-12"]
    y26=months.loc["2026-01":"2026-10"]
    return dict(n=len(x),wins=int(sum(x>0)),net_sum_pct=round(float(100*sum(x)),3),
      compounded_pct=round(float(100*(eq[-1]-1)),3),dd_pct=round(dd,3),
      months_pos=int(sum(months>0)),worst_month_pct=round(float(months.min()),3),
      net2025=round(float(100*(np.prod(1+y25/100)-1)),3),
      net2026=round(float(100*(np.prod(1+y26/100)-1)),3),
      monthly=months.round(3).to_dict())

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    d=load()
    m=features(d)
    sig=candidates(m)
    if sig.empty: raise RuntimeError("No signals; review exact entry interpretation")
    print("Complete 1-minute bars:",len(d),"signals:",len(sig))
    op=d.open.to_numpy();hi=d.high.to_numpy();lo=d.low.to_numpy();cl=d.close.to_numpy()
    modes=[
       ("baseline",.03,.09,.0825,0),
       ("no_protection",.03,.09,1.0,0),
    ]
    for activ, lock in product([.03,.04,.05,.06,.07,.075,.08,.0825],[0,.01,.02,.03,.04,.05,.06,.07]):
        if lock >= activ:continue
        modes.append((f"protect_{activ:.4f}_{lock:.4f}",.03,.09,activ,lock))
    for stop in [.015,.02,.025,.035]:
        modes.append((f"sl_{stop:.3f}",stop,.09,.0825,0))
    findings=[]; baseline=None
    for label,sl,tp,act,lk in modes:
        rs=[replay(a,op,hi,lo,cl,sl,tp,act,lk) for _,a in sig.iterrows()]
        ledger=choose(sig,rs)
        st=stats(ledger)
        row={k:v for k,v in st.items() if k!="monthly"}
        row.update(name=label,stop=sl,tp=tp,activation=act,lock=lk)
        findings.append(row)
        if label=="baseline":
            baseline=(st,ledger)
            pd.DataFrame(ledger).to_csv(OUT/"reconstructed_baseline_ledger.csv",index=False)
            pd.Series(st["monthly"]).to_csv(OUT/"reconstructed_baseline_monthly.csv",header=["return_pct"])
    base=baseline[0]
    # Apply pre-entry, causal feature filters; use exactly baseline exits.
    base_rs=[replay(a,op,hi,lo,cl) for _,a in sig.iterrows()]
    filter_funcs=[("none",lambda a:True)]
    for cap in [.3,.4,.5,.6,.8,1.0]:
        filter_funcs.append((f"atr_pct_le_{cap}",lambda a,cap=cap:a.atr_pct<=cap))
    for v in [.6,.8,1,1.2,1.5]:
        filter_funcs.append((f"vol_ratio_ge_{v}",lambda a,v=v:a.vol_ratio>=v))
    for b in [.1,.2,.35,.5,.65]:
        filter_funcs.append((f"body_ratio_ge_{b}",lambda a,b=b:a.body_ratio>=b))
    for age in [4,8,16,32,64]:
        filter_funcs.append((f"trend_age_le_{age}",lambda a,age=age:a.trend_age<=age))
    for cs in [.01,.025,.05,.1]:
        filter_funcs.append((f"close_strength_ge_{cs}",lambda a,cs=cs:a.close_strength>=cs))
    for cap,v in product([.4,.6,.8],[.6,.8,1,1.2]):
        filter_funcs.append((f"atr_le_{cap}_vol_ge_{v}",lambda a,cap=cap,v=v:a.atr_pct<=cap and a.vol_ratio>=v))
    for v,b in product([.8,1,1.2],[.2,.35,.5]):
        filter_funcs.append((f"vol_ge_{v}_body_ge_{b}",lambda a,v=v,b=b:a.vol_ratio>=v and a.body_ratio>=b))
    for label,fn in filter_funcs:
        if label=="none":continue
        st=stats(choose(sig,base_rs,fn))
        findings.append({**{k:v for k,v in st.items() if k!="monthly"}, "name":label,
                         "stop":.03,"tp":.09,"activation":.0825,"lock":0})
    for n in [1,2,3]:
        st=stats(choose(sig,base_rs,cooldown=n))
        findings.append({**{k:v for k,v in st.items() if k!="monthly"},"name":f"cooldown_after_loss_{n}",
                         "stop":.03,"tp":.09,"activation":.0825,"lock":0})
    frame=pd.DataFrame(findings)
    frame.sort_values(["dd_pct","compounded_pct"],ascending=[True,False]).to_csv(OUT/"all_variants.csv",index=False)
    qualify=frame.loc[(frame.compounded_pct>=base["compounded_pct"]-1e-7)&
                     (frame.months_pos>=base["months_pos"])&
                     (frame.dd_pct < base["dd_pct"]-1e-7)]
    best=qualify.sort_values(["dd_pct","compounded_pct"],ascending=[True,False])
    frame.sort_values(["compounded_pct","dd_pct"],ascending=[False,True]).head(15).to_csv(OUT/"best_return_candidates.csv",index=False)
    best.to_csv(OUT/"qualified_lower_dd_same_profit.csv",index=False)
    md=["# BTCUSD 15M Supertrend / EMA20 reclaim research", "",
      "**Exploratory reconstruction, not verification of the historical +114.68% / 77 trade claim.**",
      "Data: Jan 2025–Oct 2026 1-minute Delta futures. Signals on completed 15m candles; next-15m-open entry;",
      "one trade per Supertrend cycle; 1m stop-first OHLC exits; 0.05% taker per side + 18% GST on fee + 0.02% adverse slippage per side.",
      "All returns are one-times notional (no leverage). Floating intratrade drawdown is **not** modeled; DD is closed-trade compounded equity drawdown.",
      "All 2026 results are already research-exposed, not an untouched validation sample.",
      "", "## Reconstructed baseline", "",
      pd.DataFrame([{k:v for k,v in base.items() if k!="monthly"}]).to_markdown(index=False), "",
      "## Candidates with lower closed-trade drawdown, >= baseline compounded return, >= baseline winning months", "",
      ("None found." if best.empty else best.head(25).to_markdown(index=False)), "",
      "## Top highest-return candidates (exploratory)", "",
      frame.sort_values(["compounded_pct","dd_pct"],ascending=[False,True]).head(15).to_markdown(index=False), "",
      "## Baseline months", "",pd.Series(base["monthly"]).to_markdown(), "",
      "### Reproducibility guard", "",
      "Before claiming improvement relative to previously reported result, baseline must reproduce +114.68%, 77 trades and 20.86% DD on the same metric convention. Otherwise compare only within this reconstructed experiment."]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(md))
    print("\n".join(md[:17]))

if __name__=="__main__": main()
