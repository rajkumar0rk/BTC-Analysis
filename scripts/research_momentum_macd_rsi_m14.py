#!/usr/bin/env python3
"""M14 BTC2025 Delta 1m MACD%/RSI impulse first screen.
Source pinned in analysis/momentum_macd_rsi_m14/NOVELTY_CHECK.md.
Exit handling is an explicit causal Freqtrade approximation, NOT verified engine parity.
"""
from pathlib import Path
import pandas as pd, numpy as np, json, hashlib
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"analysis/momentum_macd_rsi_m14/replay"
OUT.mkdir(parents=True,exist_ok=True)
FEE=.0005*1.18
files=sorted((ROOT/"data/delta_india/BTCUSD/1m").glob("2025-*.csv.gz"))
assert len(files)==12, f"missing authentic 2025 partitions: {len(files)}"
hashes={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in files}
raw=pd.concat([pd.read_csv(f) for f in files],ignore_index=True)
assert set(["time","open","high","low","close","volume"]).issubset(raw.columns)
t=raw.time
idx=pd.to_datetime(t,unit="ms" if float(t.iloc[0])>1e11 else "s",utc=True) if pd.api.types.is_numeric_dtype(t) else pd.to_datetime(t,utc=True)
raw.index=idx
raw=raw.sort_index()
assert len(raw)==525600 and raw.index.is_unique
assert (raw.index.to_series().diff().dropna()==pd.Timedelta(minutes=1)).all()
assert ((raw.low<=raw.open)&(raw.low<=raw.close)&(raw.high>=raw.open)&(raw.high>=raw.close)&(raw.high>=raw.low)&(raw.volume>=0)).all()
h=raw.resample("1h",label="right",closed="left").agg({"open":"first","high":"max","low":"min","close":"last","volume":"sum"})
cnt=raw.close.resample("1h",label="right",closed="left").count()
h=h[cnt==60].copy()
c=h.close
macd=c.ewm(span=12,adjust=False).mean()-c.ewm(span=26,adjust=False).mean()
d=c.diff()
gain=d.clip(lower=0).ewm(alpha=1/14,min_periods=14).mean()
loss=(-d.clip(upper=0)).ewm(alpha=1/14,min_periods=14).mean()
rsi=100-100/(1+gain/loss.replace(0,np.nan))
h["entry"]=((macd/c)>.008)&(rsi>70)&(h.volume>0)
h["exit"]=((rsi<50)|(macd<0))
events={k:(bool(v.entry),bool(v.exit)) for k,v in h.iterrows()}
cash=10000.;qty=0.;entry=0.;entryfee=0.;entrytime=None;peak=0.;stop=0.;rows=[];monthly={};equity_path=[]
for j,(ts,r) in enumerate(raw.iterrows()):
    op,hi,lo,cl=map(float,(r.open,r.high,r.low,r.close))
    # Events are known only at the close of the previous 1h candle.
    if ts in events:
        en,ex=events[ts]
        if qty>0 and ex:
            fee=qty*op*FEE
            pnl=qty*(op-entry)-entryfee-fee
            cash+=qty*op-fee
            rows.append(dict(entry=str(entrytime),exit=str(ts),entry_price=entry,exit_price=op,qty=qty,net_usd=pnl,reason="indicator_exit",minutes_held=j-entryidx))
            qty=0.
        if qty==0 and en and j>=100*60:
            qty=cash/(op*(1+FEE));entry=op;entryfee=qty*op*FEE
            cash-=qty*op+entryfee;entrytime=ts;entryidx=j;peak=op
            stop=entry*.9
    if qty>0:
        # Stop evaluated before profit-taking on every minute; gap-through at open.
        if lo<=stop:
            px=min(op,stop);fee=qty*px*FEE
            pnl=qty*(px-entry)-entryfee-fee
            cash+=qty*px-fee
            rows.append(dict(entry=str(entrytime),exit=str(ts),entry_price=entry,exit_price=px,qty=qty,net_usd=pnl,reason="stop_first",minutes_held=j-entryidx))
            qty=0.
        elif hi>=entry*1.30:
            px=max(op,entry*1.30);fee=qty*px*FEE
            pnl=qty*(px-entry)-entryfee-fee
            cash+=qty*px-fee
            rows.append(dict(entry=str(entrytime),exit=str(ts),entry_price=entry,exit_price=px,qty=qty,net_usd=pnl,reason="roi_30pct",minutes_held=j-entryidx))
            qty=0.
        else:
            # Update using completed minute CLOSE only; cannot trigger within same minute.
            peak=max(peak,cl)
            if peak>=entry*1.03:
                stop=max(stop,cl*.995,peak*.99)
    nav=cash+qty*cl
    equity_path.append(nav)
    if (ts+pd.Timedelta(minutes=1)).tz_convert("Asia/Kolkata").strftime("%Y-%m")!=ts.tz_convert("Asia/Kolkata").strftime("%Y-%m"):
        monthly[ts.tz_convert("Asia/Kolkata").strftime("%Y-%m")]=nav
if qty:
    ts=raw.index[-1];px=float(raw.close.iloc[-1]);fee=qty*px*FEE
    pnl=qty*(px-entry)-entryfee-fee;cash+=qty*px-fee
    rows.append(dict(entry=str(entrytime),exit=str(ts),entry_price=entry,exit_price=px,qty=qty,net_usd=pnl,reason="end_of_utc_data",minutes_held=len(raw)-1-entryidx))
trades=pd.DataFrame(rows,columns=["entry","exit","entry_price","exit_price","qty","net_usd","reason","minutes_held"])
assert abs(10000+trades.net_usd.sum()-cash)<1e-6
trades.to_csv(OUT/"trades.csv",index=False)
months=[];last=10000.
for m,nav in sorted(monthly.items()):
    if not m.startswith("2025"):continue
    months.append(dict(month_ist=m,ending_nav=nav,net_return_pct=(nav/last-1)*100,trades_exited=int(trades.exit.str.startswith(m).sum()) if len(trades) else 0))
    last=nav
assert len(months)==12
pd.DataFrame(months).to_csv(OUT/"monthly_nav.csv",index=False)
w=trades.net_usd[trades.net_usd>0].sum();l=-trades.net_usd[trades.net_usd<0].sum()
ep=np.asarray(equity_path);dd=float((ep/np.maximum.accumulate(ep)-1).min()*100)
summary=dict(source="Roshan7869/algotrading@72a67c4",engine_parity="UNVERIFIED Freqtrade exit approximation; not source-faithful until checked",data_sha256=hashes,minute_count=len(raw),entry_signal_count=int(h.entry.sum()),trades=len(trades),net_return_pct=(cash/10000-1)*100,ending_nav=cash,profit_factor=float(w/l) if l else None,max_drawdown_pct=dd,positive_months=sum(x["net_return_pct"]>0 for x in months),negative_months=sum(x["net_return_pct"]<0 for x in months),flat_months=sum(x["net_return_pct"]==0 for x in months),monthly_ist=months,jan_ist_partial=True,funding="UNMODELED",slippage="zero",fee_per_side_with_gst=FEE,avg_hold_minutes=float(trades.minutes_held.mean()) if len(trades) else None)
(OUT/"summary.json").write_text(json.dumps(summary,indent=2))
print(json.dumps({k:v for k,v in summary.items() if k not in ("data_sha256","monthly_ist")},indent=2),flush=True)
