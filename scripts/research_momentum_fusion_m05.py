#!/usr/bin/env python3
"""Source-faithful long-only Fusion VWAP Momentum research replay. BTC 2025, no slippage."""
import json, glob, hashlib
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"analysis/momentum_vwap_score_20261121/m05_baseline"
OUT.mkdir(parents=True,exist_ok=True)
FEE=.0005*1.18
def rma(x,n):
    return x.ewm(alpha=1/n,adjust=False,min_periods=n).mean()
def run():
    files=sorted((ROOT/"data/delta_india/BTCUSD/1m").glob("2025-*.csv.gz"))
    assert len(files)==12, f"expected 12 months, got {len(files)}"
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    fs=[]
    for p in files:
        d=pd.read_csv(p)
        if p==files[0]:print("SOURCE_COLUMNS",list(d.columns),flush=True)
        fs.append(d)
    raw=pd.concat(fs,ignore_index=True)
    cols={c.lower():c for c in raw.columns}
    for x in ("open","high","low","close","volume"):assert x in cols,cols
    if "time" in cols:
        t=raw[cols["time"]]
    elif "timestamp" in cols:t=raw[cols["timestamp"]]
    else:raise RuntimeError("no time column")
    if pd.api.types.is_numeric_dtype(t):
        v=float(t.iloc[0]); unit="ms" if v>1e11 else "s"
        idx=pd.to_datetime(t,unit=unit,utc=True)
    else:idx=pd.to_datetime(t,utc=True)
    raw.index=idx
    raw=raw.rename(columns={cols[x]:x for x in ("open","high","low","close","volume")})
    raw=raw.sort_index()
    assert not raw.index.has_duplicates,"duplicate minutes"
    assert (raw.index.to_series().diff().dropna()==pd.Timedelta(minutes=1)).all(),"missing minutes: reject"
    raw=raw[["open","high","low","close","volume"]].astype(float)
    n=len(raw)
    assert n>=525000,n
    q=raw.resample("4h",closed="left",label="right",origin="start_day").agg({"open":"first","high":"max","low":"min","close":"last","volume":"sum"})
    q["count"]=raw.close.resample("4h",closed="left",label="right",origin="start_day").count()
    q=q[q["count"]==240].copy()
    c=q.close;h=q.high;l=q.low;prev=c.shift()
    tr=pd.concat([h-l,(h-prev).abs(),(l-prev).abs()],axis=1).max(axis=1)
    atr=rma(tr,14)
    fast=c.ewm(span=21,adjust=False).mean()
    slow=c.ewm(span=55,adjust=False).mean()
    trend=c.ewm(span=200,adjust=False).mean()
    roc=c/c.shift(10)-1
    diff=c.diff();up=diff.clip(lower=0);down=(-diff).clip(lower=0)
    rs=rma(up,14)/rma(down,14).replace(0,np.nan)
    rsi=100-100/(1+rs)
    macd=c.ewm(span=12,adjust=False).mean()-c.ewm(span=26,adjust=False).mean()
    hist=macd-macd.ewm(span=9,adjust=False).mean()
    plus=h.diff().clip(lower=0);minus=(-l.diff()).clip(lower=0)
    p_dm=plus.where(plus>minus,0);m_dm=minus.where(minus>plus,0)
    pdi=100*rma(p_dm,14)/atr;mDI=100*rma(m_dm,14)/atr
    dx=100*(pdi-mDI).abs()/(pdi+mDI).replace(0,np.nan)
    adx=rma(dx,14)
    # Pine ta.vwap(hlc3) resets at exchange session day; on UTC crypto bars 00:00.
    tp=(h+l+c)/3
    day=q.index.tz_convert("UTC").strftime("%Y-%m-%d")
    weighted=tp*q.volume
    vwap=weighted.groupby(day).cumsum()/q.volume.groupby(day).cumsum().replace(0,np.nan)
    vwap=vwap.fillna(tp.ewm(span=48,adjust=False).mean())
    slope=vwap.ewm(span=8,adjust=False).mean().diff()/atr
    score=((roc>0).astype(int)+(rsi>52).astype(int)+((hist>0)&(hist>hist.shift())).astype(int)+((pdi>mDI)&(adx>=14)).astype(int)+(c>fast).astype(int)+(fast>slow).astype(int)+(c>prev).astype(int))
    signal=(c>trend)&(c>fast)&(fast>slow)&(c>vwap)&(slope>=.01)&((c-vwap)/atr<=1.5)&((h-l)/atr<=2.5)&(score>=7)&(l<=vwap+.75*atr)&(c>q.open)&(c>prev)
    invalid=(c<vwap-.75*atr)|(score<=1)|(fast<slow)
    q["signal"]=signal.fillna(False);q["invalid"]=invalid.fillna(False);q["atr"]=atr
    # Sequential 1m fills; 4h signals visible only at completed 4h boundaries.
    # Stop is entered on first subsequent minute, conservative gap execution.
    events={t:(bool(r.signal),bool(r.invalid),float(r.atr),i) for i,(t,r) in enumerate(q.iterrows())}
    equity=10000.;qty=0.;entry=0.;entryfee=0.;stop=0.;lastbar=-1000;rows=[]
    monthly_nav={}
    for j,(ts,r) in enumerate(raw.iterrows()):
        if ts in events:
            sig,inv,a,bar=events[ts]
            if qty>0 and inv:
                price=float(r.open)
                exitfee=qty*price*FEE
                pnl=qty*(price-entry)-entryfee-exitfee
                equity+=qty*price-exitfee
                rows.append(dict(entry=str(entrytime),exit=str(ts),entry_price=entry,exit_price=price,quantity=qty,net_usd=pnl,reason="momentum_exit",bars_held=j-entryidx))
                qty=0.
            if qty==0 and sig and bar-lastbar>12 and np.isfinite(a) and a>0:
                price=float(r.open)
                qty=equity/(price*(1+FEE))
                entryfee=qty*price*FEE
                equity-=qty*price+entryfee
                entry=price;entrytime=ts;entryidx=j;stop=entry-2.6*a;lastbar=bar
        if qty>0 and r.low<=stop:
            price=min(float(r.open),stop)
            exitfee=qty*price*FEE
            pnl=qty*(price-entry)-entryfee-exitfee
            equity+=qty*price-exitfee
            rows.append(dict(entry=str(entrytime),exit=str(ts),entry_price=entry,exit_price=price,quantity=qty,net_usd=pnl,reason="atr_stop",bars_held=j-entryidx))
            qty=0.
        if j==n-1 and qty>0:
            price=float(r.close);exitfee=qty*price*FEE
            pnl=qty*(price-entry)-entryfee-exitfee
            equity+=qty*price-exitfee
            rows.append(dict(entry=str(entrytime),exit=str(ts),entry_price=entry,exit_price=price,quantity=qty,net_usd=pnl,reason="end_of_data",bars_held=j-entryidx))
            qty=0.
        if j==n-1 or (ts+pd.Timedelta(minutes=1)).tz_convert("Asia/Kolkata").strftime("%Y-%m")!=ts.tz_convert("Asia/Kolkata").strftime("%Y-%m"):
            monthly_nav[ts.tz_convert("Asia/Kolkata").strftime("%Y-%m")]=equity+qty*float(r.close)
    trades=pd.DataFrame(rows)
    trades.to_csv(OUT/"trades.csv",index=False)
    months=[];last=10000.
    for month,nav in sorted(monthly_nav.items()):
        months.append(dict(month_ist=month,ending_nav=nav,net_return_pct=(nav/last-1)*100))
        last=nav
    pd.DataFrame(months).to_csv(OUT/"monthly_nav.csv",index=False)
    wins=trades.loc[trades.net_usd>0,"net_usd"].sum() if len(trades) else 0
    losses=-trades.loc[trades.net_usd<0,"net_usd"].sum() if len(trades) else 0
    meta=dict(source="shahzaib-574/MarketCipherTrading/vwap_momentum_strategy.pine",model="Delta zero-slip baseline, 0.05pct fee each side +18pct GST",funding="UNMODELED",files_sha256=hashes,minute_count=n,signal_count=int(signal.sum()),trades=len(trades),profit_factor=float(wins/losses) if losses else None,ending_nav=equity,net_return_pct=(equity/10000-1)*100,months=months)
    (OUT/"summary.json").write_text(json.dumps(meta,indent=2))
    print("MOMENTUM_M05_COMPLETED "+json.dumps({k:meta[k] for k in ("minute_count","signal_count","trades","profit_factor","net_return_pct")}),flush=True)
if __name__=="__main__":run()
