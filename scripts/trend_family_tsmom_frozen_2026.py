#!/usr/bin/env python3
"""Frozen BTC2025-selected 90D TSMOM long/short chronological BTC2026 Jan-Sep recheck; 2026 is research-exposed."""
import json,hashlib
from pathlib import Path
import numpy as np
import pandas as pd
from research_every_candle_200 import read_archive
ROOT=Path("analysis/trend_following_family_20261121/tsmom_frozen_2026_jan_sep")
ROOT.mkdir(parents=True,exist_ok=True)
f,_,_,q=read_archive()
f=f.loc[(f.index>=pd.Timestamp("2025-01-01",tz="UTC"))&(f.index<pd.Timestamp("2026-09-30 18:30",tz="UTC"))].copy()
assert f.index.is_unique and f.index.is_monotonic_increasing
assert np.isfinite(f[["open","high","low","close"]].to_numpy()).all()
assert (f[["open","high","low","close"]]>0).all().all()
assert ((f.high>=f[["open","close","low"]].max(axis=1))&(f.low<=f[["open","close","high"]].min(axis=1))).all()
idx=f.index.tz_convert("Asia/Kolkata")
daily=f.assign(day=idx.floor("D")).groupby("day").agg(close=("close","last"),n=("close","size"))
daily["valid"]=daily.n.eq(1440)
logret=np.log(daily.close/daily.close.shift(1))
# Prior completed daily data only; vol estimate uses a full lagged 60-COM EWMA.
vol=logret.ewm(com=60,adjust=False,min_periods=30).std().shift(1)*np.sqrt(365)
fee=.0005*1.18
for horizon,direction in [(90,"long_short")]:
    valid=daily.valid.rolling(horizon+1,min_periods=horizon+1).min().eq(1)
    momentum=np.log(daily.close/daily.close.shift(horizon))
    sig=np.sign(momentum).where(valid & vol.notna(),0).astype(int)
    if direction=="long_flat":sig=sig.clip(lower=0)
    # Orders at next IST midnight minute open, never on the signal-forming daily bar.
    events={}
    for d,s in sig.items():
        if not valid.loc[d] or not np.isfinite(vol.loc[d]):continue
        t=(d+pd.Timedelta(days=1)).tz_convert("UTC")
        events[t]=(int(s),min(1.,.10/float(vol.loc[d])) if vol.loc[d]>0 else 0.)
    nav=100.;qty=0.;entry_cost=0.;trades=[];months=[];lastmonth=None;peak=100.;dd=0.
    last_t=None;last_p=None
    for t,r in f.iterrows():
        local=t.tz_convert("Asia/Kolkata")
        if local.year!=2026 or local.month>9:continue
        if last_t is not None and t-last_t!=pd.Timedelta(minutes=1):
            raise RuntimeError(f"Missing source minute: {last_t} -> {t}")
        last_t=t;price=float(r.open)
        if t in events:
            target,weight=events[t]
            # Rebalance to capped target NAV notional; fee both directions.
            current=nav+qty*price
            newqty=target*weight*current/price
            delta=newqty-qty
            if abs(delta)>1e-12:
                cost=abs(delta)*price*fee
                nav-=delta*price+cost
                trades.append(dict(time_utc=str(t),quantity_change=delta,price=price,fee=cost,side_after=target))
                qty=newqty
        mark=nav+qty*float(r.close)-abs(qty)*float(r.close)*fee
        month=local.strftime("%Y-%m")
        if month==lastmonth:months[-1]["end_nav"]=mark
        else:months.append(dict(month_ist=month,end_nav=mark));lastmonth=month
        peak=max(peak,mark);dd=max(dd,(peak-mark)/peak)
        last_p=float(r.close)
    # Explicit end-of-data liquidation; no fabricated future signal.
    if qty:
        cost=abs(qty)*last_p*fee
        nav+=qty*last_p-cost
        trades.append(dict(time_utc=str(last_t),quantity_change=-qty,price=last_p,fee=cost,side_after=0))
    months[-1]["end_nav"]=nav
    m=pd.DataFrame(months)
    m["start_nav"]=m.end_nav.shift().fillna(100.)
    m["net_return_pct"]=100*(m.end_nav/m.start_nav-1)
    assert len(months)==9, f"Expected Jan-Sep 2026 IST, got {len(months)} months"\n    name=f"tsmom_{horizon}d_{direction}"
    pd.DataFrame(trades).to_csv(ROOT/f"{name}_orders.csv",index=False)
    m.to_csv(ROOT/f"{name}_monthly.csv",index=False)
    summary=dict(model=name,net_pct=nav-100,months=len(m),positive_months=int((m.net_return_pct>0).sum()),negative_months=int((m.net_return_pct<0).sum()),max_dd_pct=100*dd,orders=len(trades),source_missing_minutes=q.get("missing_minutes"),fee_per_side=fee,source="Engineer Investor CRYPTO_SPEC pinned de27263d630303d32fe0df3d5b688e1b8a27350a",caveat="Component study, not faithful full 30/90/365 TSMOM; no funding; 2025 historical warmup included; BTC2026 is research-exposed; Oct 2026 excluded for documented missing minutes")
    (ROOT/f"{name}_summary.json").write_text(json.dumps(summary,indent=2))
    print("COMPONENT_DONE",json.dumps(summary))
