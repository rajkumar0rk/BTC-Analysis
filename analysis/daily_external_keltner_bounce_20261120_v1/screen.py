#!/usr/bin/env python3
"""Independent research-only interpretation of external KeltnerBounceV1; BTC 2025 ZERO slip screening."""
import hashlib,json
from pathlib import Path
import numpy as np
import pandas as pd
OUT=Path("analysis/daily_external_keltner_bounce_20261120_v1");OUT.mkdir(parents=True,exist_ok=True)
START=pd.Timestamp("2025-01-01",tz="Asia/Kolkata").tz_convert("UTC")
END=pd.Timestamp("2026-01-01",tz="Asia/Kolkata").tz_convert("UTC")
FILES=sorted(Path("data/delta_india/BTCUSD/1m").glob("202*.csv.gz"))
data=[];sources=[]
for f in FILES:
    if f.name>"2026-01.csv.gz":continue
    z=pd.read_csv(f,compression="gzip")
    assert {"time","open","high","low","close","volume"}.issubset(z.columns),str(f)
    sources.append({"path":str(f),"sha256":hashlib.sha256(f.read_bytes()).hexdigest(),"rows":len(z)})
    data.append(z[["time","open","high","low","close","volume"]])
x=pd.concat(data,ignore_index=True)
x["time"]=pd.to_datetime(pd.to_numeric(x.time),unit="s",utc=True)
x=x.set_index("time").sort_index()
assert not x.index.has_duplicates and not x.isna().any().any()
assert (x[["open","high","low","close"]]>0).all().all() and (x.volume>=0).all()
assert (x.high>=x[["open","close","low"]].max(axis=1)).all() and (x.low<=x[["open","close","high"]].min(axis=1)).all()
h=x.resample("1h").agg({"open":"first","high":"max","low":"min","close":"last","volume":"sum"})
h["complete"]=x.close.resample("1h").count().eq(60)
tr=pd.concat([h.high-h.low,(h.high-h.close.shift()).abs(),(h.low-h.close.shift()).abs()],axis=1).max(axis=1)
h["lower"]=h.close.rolling(25).mean()-2.5*tr.rolling(25).mean()
h["vol_sma"]=h.volume.rolling(20).mean()
h["sma50"]=h.close.rolling(50).mean()
h["ok"]=h.complete.rolling(200,min_periods=200).sum().eq(200)
h["signal"]=h.ok & (h.close>h.lower) & (h.close.shift()<=h.lower.shift()) & (h.volume>1.75*h.vol_sma) & (h.close>h.sma50) & (h.volume>0)
# One BTC-only position at a time, no shorts (external source is spot long-only).
# Next hourly open after completed signal; 1m stop-first, ROI tier and trailing.
# 10% of NAV allocated per trade, no leverage; both-sided fee .05% and 18% GST.
signals=h.index[h.signal & (h.index>=START-pd.Timedelta(hours=1)) & (h.index<END)]
trades=[];equity=1.0;blocked_until=START;ledger=[]
for signal in signals:
    entry_t=signal+pd.Timedelta(hours=1)
    if not START<=entry_t<END or entry_t<=blocked_until:continue
    future=x.loc[(x.index>=entry_t)&(x.index<END)]
    if future.empty or future.index[0]!=entry_t:continue
    entry=float(future.open.iloc[0]);entry_fee=equity*.1*.0005*1.18
    highwater=entry;trailing=False;exit_t=None;exit_px=None;reason=None
    prev=entry_t-pd.Timedelta(minutes=1)
    for t,b in future.iterrows():
        if t!=prev+pd.Timedelta(minutes=1):
            reason="gap_forced";exit_t=prev;exit_px=float(x.loc[prev,"close"]);break
        prev=t
        age=(t-entry_t).total_seconds()/60
        stop=entry*.94
        if trailing:stop=max(stop,highwater*.97)
        if float(b.low)<=stop:
            exit_t=t;exit_px=stop;reason="stop_first";break
        roi=.10 if age<360 else .07 if age<720 else .04 if age<1440 else .02
        if float(b.high)>=entry*(1+roi):
            exit_t=t;exit_px=entry*(1+roi);reason="roi";break
        # Trailing activation only after checking current bar's stop, avoiding same-bar optimistic trail fills.
        highwater=max(highwater,float(b.high))
        if highwater>=entry*1.05:trailing=True
        # Custom stale underwater exit after five days.
        if age>=7200 and float(b.close)<entry:
            exit_t=t;exit_px=float(b.close);reason="stale";break
    if exit_t is None:
        exit_t=future.index[-1];exit_px=float(future.close.iloc[-1]);reason="end_of_discovery"
    # Fees on executed entry/exit notional, zero slippage explicitly.
    exit_fee=equity*.1*(exit_px/entry)*.0005*1.18
    gross=equity*.1*(exit_px/entry-1)
    net=gross-entry_fee-exit_fee
    before=equity;equity+=net
    trades.append(dict(signal_utc=str(signal),entry_utc=str(entry_t),exit_utc=str(exit_t),entry=entry,exit=exit_px,exit_reason=reason,nav_before=before,gross_pnl=gross,commission= (entry_fee+exit_fee)/1.18,gst=(entry_fee+exit_fee)*(.18/1.18),slippage=0,net_pnl=net,nav_after=equity))
    blocked_until=exit_t+pd.Timedelta(hours=2)
t=pd.DataFrame(trades)
t.to_csv(OUT/"BTC2025_trades.csv",index=False)
# Mark-to-market at each IST midnight with estimated two-sided taker fees.
rows=[];prev_nav=1.0
for day in pd.date_range("2025-01-01","2026-01-01",tz="Asia/Kolkata",freq="D",inclusive="left"):
    cut=(day+pd.Timedelta(days=1)).tz_convert("UTC")-pd.Timedelta(minutes=1)
    covered=cut in x.index
    done=t[pd.to_datetime(t.exit_utc,utc=True)<=cut] if len(t) else t
    nav=float(done.nav_after.iloc[-1]) if len(done) else 1.0
    active=t[(pd.to_datetime(t.entry_utc,utc=True)<=cut)&(pd.to_datetime(t.exit_utc,utc=True)>cut)] if len(t) else t
    if len(active):
        a=active.iloc[-1];price=float(x.loc[cut,"close"]) if covered else float("nan")
        nav=float(a.nav_before)+float(a.nav_before)*.1*(price/float(a.entry)-1)-float(a.nav_before)*.1*.0005*1.18*(1+price/float(a.entry))
    ret=nav/prev_nav-1 if covered and np.isfinite(nav) and np.isfinite(prev_nav) else np.nan
    rows.append(dict(date_ist=str(day.date()),nav=nav if covered else np.nan,return_nav=ret,covered=covered))
    prev_nav=nav if covered else np.nan
d=pd.DataFrame(rows);d.to_csv(OUT/"BTC2025_daily_nav.csv",index=False)
months=[]
for month,g in d.groupby(d.date_ist.str[:7]):
    a=t[pd.to_datetime(t.exit_utc,utc=True).dt.tz_convert("Asia/Kolkata").dt.strftime("%Y-%m")==month] if len(t) else t
    wins=a[a.net_pnl>0];losses=a[a.net_pnl<0]
    pf=float(wins.net_pnl.sum()/-losses.net_pnl.sum()) if len(losses) else ("Infinity" if len(wins) else None)
    months.append(dict(month=month,nav_return_pct=float(((1+g.return_nav).prod()-1)*100) if g.return_nav.notna().all() else None,profitable_days=int((g.return_nav>0).sum()),losing_days=int((g.return_nav<0).sum()),flat_days=int((g.return_nav==0).sum()),unavailable_days=int(g.return_nav.isna().sum()),trades=len(a),wins=len(wins),losses=len(losses),realized_pf=pf))
pd.DataFrame(months).to_csv(OUT/"BTC2025_monthly.csv",index=False)
summary=dict(status="SCREEN_ONLY_NOT_ALL_IN",source="IvPalmer/Master-Trader KeltnerBounceV1",source_commit="b8dc9a00a2bc77a50bc505cf0b9976c16c9d1771",symbol="BTCUSD",period="BTC 2025 IST",trades=len(t),final_closed_nav=equity,profit_factor=float(t.loc[t.net_pnl>0,"net_pnl"].sum()/-t.loc[t.net_pnl<0,"net_pnl"].sum()) if len(t) and (t.net_pnl<0).any() else None,mean_net_trade=float(t.net_pnl.mean()) if len(t) else None,profitable_days=int((d.return_nav>0).sum()),losing_days=int((d.return_nav<0).sum()),flat_days=int((d.return_nav==0).sum()),unavailable_days=int(d.return_nav.isna().sum()),max_daily_nav_drawdown=float((d.nav/d.nav.cummax()-1).min()),commission=float(t.commission.sum()) if len(t) else 0,gst=float(t.gst.sum()) if len(t) else 0,slippage=0,funding="UNMODELED",spread="UNMODELED",sources=sources)
(OUT/"BTC2025_summary.json").write_text(json.dumps(summary,indent=2))
print(json.dumps({k:v for k,v in summary.items() if k!="sources"},indent=2))
