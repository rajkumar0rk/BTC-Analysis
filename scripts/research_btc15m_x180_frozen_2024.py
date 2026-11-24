#!/usr/bin/env python3
"""Frozen X180 validation; no search or selection using 2024 returns."""
import sys, json, hashlib
from pathlib import Path
import numpy as np
import pandas as pd
import research_btc15m_dynamic_management_refine_20261124 as frozen
from sync_delta_btcusd_1m import fetch_month,write_month
OUT=Path("analysis/btc15m_x180_frozen_2024")
DATA=Path("_validation_data")
TZ="Asia/Kolkata"
def download(mon):
    m=pd.Period(mon,freq="M")
    a=m.start_time.tz_localize(TZ).tz_convert("UTC")
    b=(m+1).start_time.tz_localize(TZ).tz_convert("UTC")
    start,stop=int(a.timestamp()),int(b.timestamp())
    rows=fetch_month(start,stop)
    DATA.mkdir(parents=True,exist_ok=True)
    path=DATA/(mon+".csv.gz")
    sha=write_month(path,rows)
    stamps=np.array(sorted(rows),dtype=np.int64)
    expected=(stop-start)//60
    complete=len(stamps)==expected and np.array_equal(stamps,np.arange(start,stop,60,dtype=np.int64))
    meta=dict(month=mon,expected=expected,observed=len(rows),missing=expected-len(rows),complete=bool(complete),sha256=sha,first_utc=pd.Timestamp(int(stamps[0]),unit="s",tz="UTC").isoformat() if len(stamps) else None,last_utc=pd.Timestamp(int(stamps[-1]),unit="s",tz="UTC").isoformat() if len(stamps) else None)
    (DATA/(mon+".json")).write_text(json.dumps(meta,indent=2))
    print(meta,flush=True)
def validate():
    OUT.mkdir(parents=True,exist_ok=True)
    months=pd.period_range("2023-12","2024-12",freq="M").astype(str).tolist()
    meta=[]
    for m in months:
        d=json.loads((DATA/(m+".json")).read_text())
        assert hashlib.sha256((DATA/(m+".csv.gz")).read_bytes()).hexdigest()==d["sha256"]
        meta.append(d)
    coverage=pd.DataFrame(meta)
    coverage.to_csv(OUT/"coverage.csv",index=False)
    # Prefer a single uninterrupted replay. Choose by coverage alone.
    groups=[];g=[]
    for d in meta:
        if d["complete"]:g.append(d["month"])
        elif g:groups.append(g);g=[]
    if g:groups.append(g)
    # Require a preceding complete month to warm up the original indicators.
    eligible=[g for g in groups if len(g)>=2 and any(m.startswith("2024") for m in g[1:])]
    lines=["# Frozen X180 BTCUSD 2024 validation","", "Frozen from research/btc15m-dynamic-management-refine-20261124, rule X180; original risk rules and fees/slippage, no optimization on 2024.","","## Data coverage",coverage[["month","expected","observed","missing","complete"]].to_markdown(index=False),""]
    if not eligible:
        lines+=["No uninterrupted fully covered 2024 month with a full preceding warm-up month. No valid backtest was produced."]
        (OUT/"REPORT.md").write_text("\n".join(lines)+"\n");return
    g=max(eligible,key=lambda g:len(g))
    score=[m for m in g[1:] if m.startswith("2024")]
    frames=[pd.read_csv(DATA/(m+".csv.gz")) for m in g]
    df=pd.concat(frames,ignore_index=True)
    assert np.all(np.diff(df.time.to_numpy(np.int64))==60)
    df.index=pd.to_datetime(df.time,unit="s",utc=True)
    end=(pd.Period(score[-1],freq="M")+1).start_time.tz_localize(TZ).tz_convert("UTC")
    df=df.loc[df.index<end].copy()
    assert len(df)%15==0
    start=pd.Period(score[0],freq="M").start_time.tz_localize(TZ).tz_convert("UTC")
    start_i=int(np.searchsorted(df.time.to_numpy(),int(start.timestamp())))
    base=frozen.base;base.MONTHS=score
    assert frozen.MANAGE["X180"]==("dynamic",.5,.75,0.)
    assert frozen.RULES["X180"][0]==(.9,.1,.1,.75)
    assert frozen.VARIANTS["X180"]==("refine",2.45,3.,2,3.25,2.,1.,.25,9.)
    sim=frozen.factory()
    ema,stline,trend,valid=base.st_and_ema(df,base.TF)
    ind=base.make_indicators(df);frozen.entry.enrich(df,ind,ema)
    sig=base.make_signals(df,ema,trend,valid,"reclaim",4)[0]
    sig={i:v for i,v in sig.items() if i>=start_i}
    cfg=(4,"ATRMIN_0p2","PCT",3.,3.,frozen.p.r.LOCK)
    summaries=[];monthly=[];ledger=[]
    for prof in frozen.PROFILES:
        for path in base.PATHS:
            name=f"reclaim_NOFLIP_LATE825_MLOSS5__P_{prof}__Q_X180_SL300_TP3R"
            x,m,l=sim(df,ema,stline,trend,ind,name,cfg,sig,path)
            x["profile"]=prof
            for k in ("profitable_2025_months","profitable_2026_months","return_2025_pct","return_2026_pct"):x.pop(k,None)
            m["profile"]=prof;l["profile"]=prof
            summaries.append(x);monthly.append(m);ledger.append(l)
    s=pd.DataFrame(summaries);m=pd.concat(monthly,ignore_index=True);l=pd.concat(ledger,ignore_index=True)
    s.to_csv(OUT/"summary.csv",index=False);m.to_csv(OUT/"monthly.csv",index=False);l.to_csv(OUT/"ledger.csv",index=False)
    lines += [f"## Scored period: {score[0]} to {score[-1]} ({len(score)}/12 complete IST months)",f"Warmup: {g[0]}; no trades during warmup. Full-year coverage: {len(score)==12}.","", "Both intraminute paths, starting equity $1000. Fee 0.05% per side plus GST18%; slippage 0.02% per side. Funding and actual exchange fills not modeled.","",s[["profile","path_assumption","trades","wins","losses","net_return_pct","max_floating_drawdown_pct","profitable_months","fees_gst_usd"]].to_markdown(index=False),"","## Monthly returns",m.pivot(index="month_ist",columns=["profile","path_assumption"],values="monthly_return_pct").to_markdown(),""]
    (OUT/"REPORT.md").write_text("\n".join(lines)+"\n")
    print(s[["profile","path_assumption","net_return_pct","profitable_months"]].to_string(index=False),flush=True)
if __name__=="__main__":
    if sys.argv[1]=="download":download(sys.argv[2])
    else:validate()
