#!/usr/bin/env python3
"""Independent research-only interpretation of external EmaVwapLong; BTC 2025 ZERO slip screening."""
import hashlib,json
from pathlib import Path
import numpy as np
import pandas as pd
OUT=Path("analysis/daily_external_ema_vwap_armed_20261120_v1");OUT.mkdir(parents=True,exist_ok=True)
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
# Independent conservative 1h-candle interpretation of the external two-stage setup.
# At close of candle i: EMA9 crosses above UTC-day VWAP, candle closes above both.
# Setup is armed for the next three completed 1h candles; their highs must exceed setup high.
# Entry at the FOLLOWING hour open, not the unknown intrabar breakout price.
h["ema9"]=h.close.ewm(span=9,adjust=False).mean()
typical=(h.high+h.low+h.close)/3
day=h.index.floor("D")
pv=(typical*h.volume).groupby(day).cumsum()
cv=h.volume.groupby(day).cumsum()
h["vwap"]=pv/cv.replace(0,np.nan)
tr=pd.concat([h.high-h.low,(h.high-h.close.shift()).abs(),(h.low-h.close.shift()).abs()],axis=1).max(axis=1)
h["atr"]=tr.ewm(span=14,adjust=False).mean()
h["ok"]=h.complete.rolling(60,min_periods=60).sum().eq(60)
h["cross"]=h.ok & (h.ema9>h.vwap)&(h.ema9.shift()<=h.vwap.shift())&(h.close>h.ema9)&(h.close>h.vwap)&(h.volume>0)&((1.5*h.atr/h.high)<.038)
signals=[]
for i in range(60,len(h)-3):
    if not bool(h.cross.iloc[i]):continue
    trigger=float(h.high.iloc[i]);atr=float(h.atr.iloc[i])
    for j in range(i+1,min(i+4,len(h))):
        if not bool(h.complete.iloc[j]) or h.ema9.iloc[j]<=h.vwap.iloc[j]:break
        if h.high.iloc[j]>trigger:
            signals.append((h.index[j],atr))
            break
# 10% unlevered NAV per trade; identical 1.5 ATR stop / 3 ATR target and 60h timeout.
# Source leverage and liquidation prefilter retained as signal criterion; no fabricated liquidation fills.
trades=[];equity=1.0;blocked_until=START
for signal,atr in signals:
    entry_t=signal+pd.Timedelta(hours=1)
    if not START<=entry_t<END or entry_t<=blocked_until:continue
    future=x.loc[(x.index>=entry_t)&(x.index<END)]
    if future.empty or future.index[0]!=entry_t:continue
    entry=float(future.open.iloc[0]);entry_fee=equity*.1*.0005*1.18
    stop=entry-1.5*atr;target=entry+3*atr
    exit_t=None;exit_px=None;reason=None;prev=entry_t-pd.Timedelta(minutes=1)
    for t,b in future.iterrows():
        if t!=prev+pd.Timedelta(minutes=1):
            exit_t=prev;exit_px=float(x.loc[prev,"close"]);reason="gap_forced";break
        prev=t
        if float(b.low)<=stop:
            exit_t=t;exit_px=stop;reason="stop_first";break
        if float(b.high)>=target:
            exit_t=t;exit_px=target;reason="target";break
        if t>=entry_t+pd.Timedelta(hours=60):
            exit_t=t;exit_px=float(b.close);reason="timeout";break
    if exit_t is None:
        exit_t=future.index[-1];exit_px=float(future.close.iloc[-1]);reason="end_of_discovery"
    exit_fee=equity*.1*(exit_px/entry)*.0005*1.18
    gross=equity*.1*(exit_px/entry-1);net=gross-entry_fee-exit_fee
    before=equity;equity+=net
    trades.append(dict(signal_utc=str(signal),entry_utc=str(entry_t),exit_utc=str(exit_t),entry=entry,exit=exit_px,exit_reason=reason,nav_before=before,gross_pnl=gross,commission=(entry_fee+exit_fee)/1.18,gst=(entry_fee+exit_fee)*(.18/1.18),slippage=0,net_pnl=net,nav_after=equity))
    blocked_until=exit_t
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
summary=dict(status="SCREEN_ONLY_NOT_ALL_IN",source="xenoxavier/freqtrade-ema-vwap EmaVwapLong",source_commit="UNPINNED",symbol="BTCUSD",period="BTC 2025 IST",trades=len(t),final_closed_nav=equity,profit_factor=float(t.loc[t.net_pnl>0,"net_pnl"].sum()/-t.loc[t.net_pnl<0,"net_pnl"].sum()) if len(t) and (t.net_pnl<0).any() else None,mean_net_trade=float(t.net_pnl.mean()) if len(t) else None,profitable_days=int((d.return_nav>0).sum()),losing_days=int((d.return_nav<0).sum()),flat_days=int((d.return_nav==0).sum()),unavailable_days=int(d.return_nav.isna().sum()),max_daily_nav_drawdown=float((d.nav/d.nav.cummax()-1).min()),commission=float(t.commission.sum()) if len(t) else 0,gst=float(t.gst.sum()) if len(t) else 0,slippage=0,funding="UNMODELED",spread="UNMODELED",sources=sources)
(OUT/"BTC2025_summary.json").write_text(json.dumps(summary,indent=2))
print(json.dumps({k:v for k,v in summary.items() if k!="sources"},indent=2))
