#!/usr/bin/env python3
"""Preregistered spot-led futures dislocation; experimental, not validated."""
import io, zipfile, urllib.request, hashlib, json
from pathlib import Path
import numpy as np, pandas as pd
OUT=Path("analysis/independent_spot_lead_lag_20261119")
ROOT=Path("data/delta_india")
OUT.mkdir(parents=True,exist_ok=True)
def delta(symbol):
    files=sorted((ROOT/symbol/"1m").glob("20??-??.csv.gz"))
    if not files: raise RuntimeError("MISSING_DELTA_1M_"+symbol)
    parts=[]; hashes={}
    for f in files:
        hashes[str(f)]=hashlib.sha256(f.read_bytes()).hexdigest()
        z=pd.read_csv(f,compression="gzip",usecols=["time","open","high","low","close"])
        z["time"]=pd.to_datetime(z.time.astype("int64"),unit="s",utc=True)
        parts.append(z)
    x=pd.concat(parts).set_index("time").sort_index()
    if x.index.has_duplicates: raise RuntimeError("DUPLICATE_DELTA_MINUTES_"+symbol)
    if (x.high < x[["open","close","low"]].max(axis=1)).any() or (x.low > x[["open","close","high"]].min(axis=1)).any():raise RuntimeError("BAD_OHLC_"+symbol)
    g=x.resample("1h",label="left",closed="left").agg({"open":"first","high":"max","low":"min","close":"last"})
    counts=x.open.resample("1h").count()
    g=g[counts.eq(60)]
    return g,hashes
def spot(symbol):
    parts=[]; provenance=[]
    for y,m in [(y,m) for y in (2025,2026) for m in range(1,13) if (y,m)<=(2026,10)]:
        key=f"{y}-{m:02d}"
        url=f"https://data.binance.vision/data/spot/monthly/klines/{symbol}USDT/1h/{symbol}USDT-1h-{key}.zip"
        with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"Research/1.0"}),timeout=75) as r: raw=r.read()
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            name=next(n for n in z.namelist() if n.endswith(".csv"))
            frame=pd.read_csv(io.BytesIO(z.read(name)),header=None)
        t=frame.iloc[:,0].astype("int64")
        idx=pd.to_datetime(t,unit="us" if t.iloc[0]>10**14 else "ms",utc=True)
        if idx.has_duplicates:raise RuntimeError("DUPLICATE_SPOT_"+key)
        parts.append(pd.Series(pd.to_numeric(frame.iloc[:,4]),index=idx))
        provenance.append(dict(url=url,sha256=hashlib.sha256(raw).hexdigest(),rows=len(frame)))
    return pd.concat(parts).sort_index(),provenance
def simulate(symbol):
    fut, hashes=delta(symbol); sp, prov=spot("BTC" if symbol=="BTCUSD" else "ETH")
    sp=sp.reindex(fut.index)
    fr=fut.close.pct_change(fill_method=None); sr=sp.pct_change(fill_method=None)
    contiguous=fut.index.to_series().diff().eq(pd.Timedelta(hours=1))
    eligible=contiguous & contiguous.shift(1).fillna(False) & sp.notna() & sp.shift(1).notna()
    # signal known at end of hour i; execute at OPEN of i+1, provided adjacent.
    sig=eligible & sr.abs().ge(.008) & fr.abs().le(.003) & (sr.abs()-fr.abs()).ge(.005)
    nav=10000.; peak=nav; maxdd=0.; trades=[]; equity=[]
    ix=fut.index
    i=1
    while i<len(fut)-1:
        t=ix[i]; equity.append(dict(time_utc=str(t),nav=nav))
        if not sig.iloc[i] or ix[i+1]-ix[i]!=pd.Timedelta(hours=1):
            i+=1;continue
        side=int(np.sign(sr.iloc[i])); entry=float(fut.open.iloc[i+1])
        slip=max(5.,entry*.0002) if symbol=="BTCUSD" else entry*.0002
        entry+=side*slip
        stop=entry*(1-side*.005); risk=abs(entry-stop)
        qty=min(nav*.0025/risk,nav*2/entry)
        fee=.0005*1.18
        nav-=qty*entry*fee
        best=entry; exit_price=None; end=i+1
        for j in range(i+1,min(i+14,len(fut))):
            if j>i+1 and ix[j]-ix[j-1]!=pd.Timedelta(hours=1):break
            bar=fut.iloc[j]
            if side==1:
                if bar.low<=stop:exit_price=stop;end=j;break
                best=max(best,float(bar.high))
                if best-entry>=entry*.05:stop=max(stop,best-entry*.025)
            else:
                if bar.high>=stop:exit_price=stop;end=j;break
                best=min(best,float(bar.low))
                if entry-best>=entry*.05:stop=min(stop,best+entry*.025)
            end=j
        if exit_price is None:exit_price=float(fut.close.iloc[end])
        exit_price-=side*slip
        pnl=side*qty*(exit_price-entry)-qty*exit_price*fee
        nav+=pnl
        trades.append(dict(symbol=symbol,signal_utc=str(ix[i]),entry_utc=str(ix[i+1]),exit_utc=str(ix[end]),side=side,qty=qty,entry=entry,exit=exit_price,net_pnl=pnl,net_R=pnl/(qty*risk),nav_after=nav))
        peak=max(peak,nav);maxdd=max(maxdd,1-nav/peak)
        i=end+1
    return trades,equity,dict(symbol=symbol,delta_sha256=hashes,spot_source=prov,eligible_signals=int(sig.sum()),closed=len(trades),nav_end=nav,drawdown_closed_equity_only=maxdd,warning="NOT MTM: open-position monthly NAV and funding absent; stop-first hourly approximate, no intrabar sequencing; incomplete validation")
def main():
    for symbol in ("BTCUSD","ETHUSD"):
        tr,eq,quality=simulate(symbol)
        pd.DataFrame(tr).to_csv(OUT/(symbol+"_trades.csv"),index=False)
        pd.DataFrame(eq).to_csv(OUT/(symbol+"_equity.csv"),index=False)
        (OUT/(symbol+"_quality.json")).write_text(json.dumps(quality,indent=2))
        pnl=np.array([x["net_pnl"] for x in tr])
        pf=float(pnl[pnl>0].sum()/-pnl[pnl<0].sum()) if (pnl<0).any() else None
        print(symbol,"closed",len(tr),"PF",pf,"NAV",quality["nav_end"],flush=True)
if __name__=="__main__":main()
