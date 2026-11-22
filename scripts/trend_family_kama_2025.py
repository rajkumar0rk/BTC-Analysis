#!/usr/bin/env python3
"""TF-KAMA-001: independent implementation of Quant Arena TREND-11 daily long/cash baseline.
Source: https://quantarenas.com/code/trend-11-kaufman-adaptive-moving-average/
Source page dated 2025-06-01; defaults ER10, fast2, slow30, slope5.
Research adaptation: actual Delta India BTCUSD 1m next-day-open fills and fees/GST.
"""
import json, hashlib
from pathlib import Path
import numpy as np
import pandas as pd
from research_every_candle_200 import read_archive
OUT=Path("analysis/trend_following_family_20261121/kama_btc2025")
OUT.mkdir(parents=True,exist_ok=True)
f,_,_,quality=read_archive()
f=f.loc[(f.index>=pd.Timestamp("2025-01-01",tz="UTC"))&(f.index<pd.Timestamp("2025-12-31 18:30",tz="UTC"))].copy()
assert f.index.is_unique and f.index.is_monotonic_increasing
assert np.isfinite(f[["open","high","low","close"]].to_numpy()).all()
assert (f[["open","high","low","close"]]>0).all().all()
assert ((f.high>=f[["open","close","low"]].max(axis=1))&(f.low<=f[["open","close","high"]].min(axis=1))).all()
local=f.index.tz_convert("Asia/Kolkata")
daily=f.assign(day=local.floor("D")).groupby("day").agg(close=("close","last"),n=("close","size"))
daily["valid"]=daily.n.eq(1440)
# UTC archive begins 2025-01-01 00:00: Jan 1 IST lacks its first 330 minutes.
# Exclude this boundary day from signal formation, never label it testable.
assert daily.iloc[0].n==1110, "Unexpected first-day boundary; inspect source"
daily=daily.iloc[1:].copy()
assert daily.valid.all(), "Incomplete IST daily source candle; fail closed"
c=daily.close.to_numpy(dtype=float)
k=np.full(len(c),np.nan)
k[9]=c[9]
for i in range(10,len(c)):
    change=abs(c[i]-c[i-10])
    noise=np.abs(np.diff(c[i-10:i+1])).sum()
    er=change/noise if noise else 0.
    sc=(er*(2/3-2/31)+2/31)**2
    k[i]=k[i-1]+sc*(c[i]-k[i-1])
sig=np.zeros(len(c),dtype=int)
for i in range(15,len(c)):
    if c[i]>k[i] and k[i]>k[i-5]:sig[i]=1
    elif c[i]<=k[i]:sig[i]=0
    else:sig[i]=sig[i-1]
events={(day+pd.Timedelta(days=1)).tz_convert("UTC"):int(s) for day,s in zip(daily.index,sig)}
fee=.0005*1.18
cash=100.;qty=0.;entry_price=None;entry_fee=0.;orders=[];roundtrips=[];months=[];month=None
peak=100.;maxdd=0.;last_t=None;last_close=None
for t,r in f.iterrows():
    if last_t is not None and t-last_t!=pd.Timedelta(minutes=1):
        raise RuntimeError(f"Missing minute: {last_t} -> {t}")
    last_t=t;price=float(r.open);last_close=float(r.close)
    if t in events:
        target=events[t]
        if target and qty==0:
            # Fully fee-funded position, never borrow for baseline 100% allocation.
            qty=cash/(price*(1+fee))
            paid=qty*price*fee
            cash-=qty*price+paid
            entry_price=price;entry_fee=paid
            orders.append(dict(time_utc=str(t),side="BUY",qty=qty,price=price,fee=paid))
        elif not target and qty>0:
            proceeds=qty*price;paid=proceeds*fee
            cash+=proceeds-paid
            net=(price-entry_price)*qty-entry_fee-paid
            roundtrips.append(dict(entry_price=entry_price,exit_price=price,exit_utc=str(t),qty=qty,net_pnl=net,fees=entry_fee+paid))
            orders.append(dict(time_utc=str(t),side="SELL",qty=qty,price=price,fee=paid))
            qty=0.;entry_price=None;entry_fee=0.
    mark=cash+qty*last_close*(1-fee)
    m=t.tz_convert("Asia/Kolkata").strftime("%Y-%m")
    if m==month:months[-1]["end_nav"]=mark
    else:months.append(dict(month_ist=m,end_nav=mark));month=m
    peak=max(peak,mark);maxdd=max(maxdd,1-mark/peak)
if qty:
    paid=qty*last_close*fee
    cash+=qty*last_close-paid
    net=(last_close-entry_price)*qty-entry_fee-paid
    roundtrips.append(dict(entry_price=entry_price,exit_price=last_close,exit_utc=str(last_t),qty=qty,net_pnl=net,fees=entry_fee+paid))
    orders.append(dict(time_utc=str(last_t),side="SELL_FINAL",qty=qty,price=last_close,fee=paid))
    qty=0.
months[-1]["end_nav"]=cash
monthly=pd.DataFrame(months)
monthly["start_nav"]=monthly.end_nav.shift().fillna(100.)
monthly["net_return_pct"]=100*(monthly.end_nav/monthly.start_nav-1)
tr=pd.DataFrame(roundtrips)
gross_win=float(tr.loc[tr.net_pnl>0,"net_pnl"].sum()) if len(tr) else 0.
gross_loss=float(-tr.loc[tr.net_pnl<0,"net_pnl"].sum()) if len(tr) else 0.
assert abs(100+tr.net_pnl.sum()-cash)<1e-7, "Closed PnL NAV reconciliation failed"
assert abs(np.prod(1+monthly.net_return_pct/100)*100-cash)<1e-7, "Monthly NAV reconciliation failed"
monthly.to_csv(OUT/"monthly_ist.csv",index=False)
tr.to_csv(OUT/"roundtrips.csv",index=False)
pd.DataFrame(orders).to_csv(OUT/"orders.csv",index=False)
summary=dict(model="quant_arena_trend11_kama_default",source="https://quantarenas.com/code/trend-11-kaufman-adaptive-moving-average/",net_return_pct=100*(cash/100-1),max_dd_pct=100*maxdd,positive_months=int((monthly.net_return_pct>1e-9).sum()),negative_months=int((monthly.net_return_pct< -1e-9).sum()),flat_months=int((monthly.net_return_pct.abs()<=1e-9).sum()),roundtrips=len(tr),orders=len(orders),pf=(gross_win/gross_loss if gross_loss else None),gross_win=gross_win,gross_loss=gross_loss,total_fees=sum(o["fee"] for o in orders),final_nav=cash,source_missing_minutes=quality.get("missing_minutes"),fee_per_side=fee,slippage_points=0,funding="UNMODELED",source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),caveat="Original long/cash signal, but Delta India futures fee-aware 1m execution is an adaptation; no 2024 warmup")
(OUT/"summary.json").write_text(json.dumps(summary,indent=2))
print("KAMA_COMPLETE",json.dumps(summary))
