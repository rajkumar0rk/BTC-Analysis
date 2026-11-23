#!/usr/bin/env python3
"""Pinned Kali-Uga NQ continuous-trend signal, adapted to Delta BTC 5m->1m.
Source MIT d562ec7a42d2727975b7076a6413fbb2d452579d.
Original sensitivity anchor: period=263, scale=.01; no BTC fitting.
"""
import hashlib,json
from pathlib import Path
import numpy as np,pandas as pd
from research_every_candle_200 import read_archive
OUT=Path("analysis/trend_following_family_20261121/kali_uga_btc2025")
OUT.mkdir(parents=True,exist_ok=True)
f,_,_,quality=read_archive()
start=pd.Timestamp("2025-01-01",tz="UTC")
end=pd.Timestamp("2025-12-31 18:30",tz="UTC")
f=f.loc[(f.index>=start)&(f.index<end)].copy()
assert len(f)>500000 and f.index.is_unique and f.index.is_monotonic_increasing
assert ((f.index[1:]-f.index[:-1])==pd.Timedelta(minutes=1)).all(),"Source minute gaps"
assert np.isfinite(f[['open','high','low','close']].to_numpy()).all()
assert (f[['open','high','low','close']]>0).all().all()
assert ((f.high>=f[['open','close','low']].max(axis=1))&(f.low<=f[['open','close','high']].min(axis=1))).all()
# 5m bar closes at UTC xx:04, xx:09...; trade at the following minute's OPEN.
g=f['close'].resample('5min',label='right',closed='left').agg(['last','count'])
g=g[g['count']==5]
# Resample label 00:05 corresponds to minute 00:04 close; 00:05 open is eligible.
r=np.log(g['last']/g['last'].shift(1))
past=r.shift(1)
signal=past.ewm(span=525,adjust=False).mean()
signal_vol=signal.abs().ewm(span=399,adjust=False).mean()+1e-9
asset_vol=(past.abs().ewm(span=39,adjust=False).mean()*np.sqrt(20)).ewm(span=399,adjust=False).mean()*np.sqrt(200)+1e-9
weight=(signal/signal_vol/asset_vol*.01).clip(-1,1).replace([np.inf,-np.inf],np.nan).fillna(0)
# Signal formed on last complete 5m bar ending at t-1 minute; past shift follows upstream.
events={t:float(w) for t,w in weight.items() if t>=start+pd.Timedelta(minutes=1500)}
fee=.0005*1.18
cash=100.;qty=0.;peak=100.;maxdd=0.;orders=[];months=[];lastmonth=None
total_fees=0.;last_price=None;last_t=None
for t,row in f.iterrows():
    price=float(row.open)
    if t in events:
        desired=events[t]
        equity=cash+qty*price
        # Solve fee-funded target notional for a signed position; cap gross to equity.
        target=desired*max(equity,0.)/price
        delta=target-qty
        if abs(delta)*price>1e-8:
            cost=abs(delta)*price*fee
            cash-=delta*price+cost
            total_fees+=cost
            orders.append(dict(time_utc=str(t),price=price,quantity_change=delta,fee=cost,target_weight=desired))
            qty=target
    mark=cash+qty*float(row.close)-abs(qty)*float(row.close)*fee
    peak=max(peak,mark)
    maxdd=max(maxdd,1-mark/peak)
    month=t.tz_convert("Asia/Kolkata").strftime("%Y-%m")
    if month==lastmonth:months[-1]['end_nav']=mark
    else:months.append(dict(month_ist=month,end_nav=mark));lastmonth=month
    last_price=float(row.close);last_t=t
# Close position at last observed close; no fabricated subsequent price.
if abs(qty)>1e-12:
    cost=abs(qty)*last_price*fee
    cash+=qty*last_price-cost
    total_fees+=cost
    orders.append(dict(time_utc=str(last_t),price=last_price,quantity_change=-qty,fee=cost,target_weight=0.))
else: cash=cash
months[-1]['end_nav']=cash
m=pd.DataFrame(months)
m['start_nav']=m.end_nav.shift().fillna(100.)
m['net_return_pct']=100*(m.end_nav/m.start_nav-1)
o=pd.DataFrame(orders)
assert abs(100*np.prod(1+m.net_return_pct/100)-cash)<1e-6
assert abs(100+sum(-z['quantity_change']*z['price']-z['fee'] for z in orders)-cash)<1e-6
assert len(m)==12 and np.isfinite(m.net_return_pct).all()
m.to_csv(OUT/'monthly_ist.csv',index=False)
o.to_csv(OUT/'orders.csv',index=False)
summary=dict(model='kali_uga_continuous_ema_original_anchor',period=263,scale=.01,source_commit='d562ec7a42d2727975b7076a6413fbb2d452579d',net_return_pct=100*(cash/100-1),max_dd_pct=100*maxdd,positive_months=int((m.net_return_pct>0).sum()),negative_months=int((m.net_return_pct<0).sum()),orders=len(o),total_fees=total_fees,final_nav=cash,fee_per_side=fee,slippage=0,funding='UNMODELED',source_missing_minutes=quality.get('missing_minutes'),code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),caveat='NQ source adapted to Delta BTC 5m completed signals and next-minute opens; source turnover cost replaced by Delta fee+GST; 2025 warmup begins with archive')
(OUT/'summary.json').write_text(json.dumps(summary,indent=2))
print('KALI_BTC2025_COMPLETE',json.dumps(summary))
