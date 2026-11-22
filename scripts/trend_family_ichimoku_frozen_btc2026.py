#!/usr/bin/env python3
"""Frozen 4H Ichimoku 2026 chronology; identical 2025 strategy, 2026 NAV reset at 100. No live orders."""
import hashlib,json
from pathlib import Path
import numpy as np
import pandas as pd
from research_every_candle_200 import read_archive
OUT=Path("analysis/ichimoku_btc2026_frozen_20261122")
OUT.mkdir(parents=True,exist_ok=True)
f,seg_start,seg_end,q=read_archive()
f=f.loc[(f.index>=pd.Timestamp("2025-10-01",tz="UTC"))&(f.index<pd.Timestamp("2026-10-31 18:30:00",tz="UTC"))].copy()
if f.empty:raise RuntimeError("No source candles")
# Both ends of the January–October 2026 IST window must exist in source.
start_ist_utc=pd.Timestamp("2025-12-31 18:30:00",tz="UTC")
end_ist_utc=pd.Timestamp("2026-10-31 18:29:00",tz="UTC")
if start_ist_utc not in f.index or end_ist_utc not in f.index:
    raise RuntimeError("Incomplete Jan–Oct 2026 IST archive boundaries; cannot claim 10 full months")
# Reject malformed authentic candles before aggregating or simulating stops.
# A corrupt low/high can otherwise create an impossible protective-stop fill.
if not f.index.is_monotonic_increasing or not f.index.is_unique:
    raise RuntimeError("Source timestamps must be strictly increasing and unique")
ohlc=f[["open","high","low","close"]]
if not np.isfinite(ohlc.to_numpy(dtype=float)).all():
    raise RuntimeError("Source contains non-finite OHLC")
if (ohlc<=0).any().any():
    raise RuntimeError("Source contains non-positive OHLC")
if ((ohlc.low>ohlc[["open","close"]].min(axis=1)) |
    (ohlc.high<ohlc[["open","close"]].max(axis=1)) |
    (ohlc.low>ohlc.high)).any():
    raise RuntimeError("Source OHLC ordering invalid")

# Closed 4H candles only; no signals from incomplete source blocks.
b=f[["open","high","low","close"]].resample("4h",closed="left",label="right").agg({"open":"first","high":"max","low":"min","close":"last"})
cnt=f.close.resample("4h",closed="left",label="right").count()
b["valid"]=cnt.rolling(120,min_periods=120).min().eq(240)
mid=lambda n:(b.high.rolling(n).max()+b.low.rolling(n).min())/2
ten=mid(9);kij=mid(26)
# Plotted cloud at time t uses values calculated at t-26, not future cloud.
sa=((ten+kij)/2).shift(26);sb=mid(52).shift(26)
top=pd.concat([sa,sb],axis=1).max(axis=1);bot=pd.concat([sa,sb],axis=1).min(axis=1)
crossup=(ten>kij)&(ten.shift(1)<=kij.shift(1))
crossdn=(ten<kij)&(ten.shift(1)>=kij.shift(1))
long=b.valid&(b.close>top)&crossup&(b.close>b.close.shift(26))
short=b.valid&(b.close<bot)&crossdn&(b.close<b.close.shift(26))
exitlong=b.valid&((b.close<bot)|crossdn)
exitshort=b.valid&((b.close>top)|crossup)
# Timestamp of 4H close is eligible NEXT 1m open at that same timestamp.
events={t:(int(long.loc[t])-int(short.loc[t]),bool(exitlong.loc[t]),bool(exitshort.loc[t])) for t in b.index[b.valid]}
fee=.0005*1.18;capital=100.;risk_fraction=.005
side=0;qty=0.;entry=0.;entry_fee=0.;entry_time=None;stop=0.;equity=capital
trades=[];marks=[];peak=capital;maxdd=0.
last_month=None;month_entries={};source_hash=hashlib.sha256(pd.util.hash_pandas_object(f[["open","high","low","close"]],index=True).values.tobytes()).hexdigest()
prev_time=None
for t,r in f.iterrows():
    if t.tz_convert("Asia/Kolkata")<pd.Timestamp("2026-01-01",tz="Asia/Kolkata"):continue
    if t.tz_convert("Asia/Kolkata")>=pd.Timestamp("2026-11-01",tz="Asia/Kolkata"):
        break
    if prev_time is not None and (t-prev_time)!=pd.Timedelta(minutes=1):
        # A missing minute makes intragap stop execution unknowable.
        # Fail closed: do not invent a favorable historical fill.
        raise RuntimeError(f"Missing 1m source bar between {prev_time} and {t}; replay invalid")
    prev_time=t
    sig,el,es=events.get(t,(0,False,False))
    # Closed-bar exit at next open, stop-first on current 1m candle.
    if side:
        # A completed 4H signal executes at the current minute OPEN.
        # Otherwise, check the current minute for a stop, with gap-aware fills.
        scheduled=(side==1 and el) or (side==-1 and es)
        if scheduled:
            x=float(r.open)
            reason="signal"
        else:
            x=None
        hit=(float(r.low)<=stop if side==1 else float(r.high)>=stop)
        if x is None and hit:
            x=min(float(r.open),stop) if side==1 else max(float(r.open),stop)
            reason="stop"
        if x is not None:
            exitfee=qty*x*fee;pnl=side*qty*(x-entry)-entry_fee-exitfee
            equity+=pnl;trades.append((entry_time,t,side,entry,x,qty,pnl,reason));side=0
    if not side and sig and t in events and t.tz_convert("Asia/Kolkata")<pd.Timestamp("2026-11-01",tz="Asia/Kolkata"):
        # Fixed 2x 4H ATR protective stop; separate risk overlay disclosed.
        loc=b.index.get_indexer([t])[0]
        pc=b.close.shift(1);tr=pd.concat([b.high-b.low,(b.high-pc).abs(),(b.low-pc).abs()],axis=1).max(axis=1)
        atr=tr.rolling(14).mean().iloc[loc]
        if np.isfinite(atr) and atr>0 and equity>0:
            entry=float(r.open);stop=entry-sig*2*float(atr)
            qty=min(equity*risk_fraction/(2*float(atr)),equity/entry)
            entry_fee=qty*entry*fee;side=sig;entry_time=t
            month_entries[str(t.tz_convert("Asia/Kolkata").to_period("M"))]=month_entries.get(str(t.tz_convert("Asia/Kolkata").to_period("M")),0)+1
            # The entry fills at this minute's open. Its subsequent intraminute
            # range can hit the protective stop before the next minute arrives.
            # Omitting this check would systematically suppress immediate losses.
            entry_bar_stop_hit=(float(r.low)<=stop if side==1 else float(r.high)>=stop)
            if entry_bar_stop_hit:
                x=stop
                exitfee=qty*x*fee
                pnl=side*qty*(x-entry)-entry_fee-exitfee
                equity+=pnl
                trades.append((entry_time,t,side,entry,x,qty,pnl,"entry_minute_stop"))
                side=0
    month=str(t.tz_convert("Asia/Kolkata").to_period("M"))
    mark=equity+(side*qty*(float(r.close)-entry)-entry_fee-qty*float(r.close)*fee if side else 0.)
    if month!=last_month and last_month is not None:pass
    if marks and marks[-1][0]==month:marks[-1]=(month,mark)
    else:marks.append((month,mark))
    peak=max(peak,mark);maxdd=max(maxdd,(peak-mark)/peak)
if side:
    t=f.index[-1];x=float(f.close.iloc[-1]);pnl=side*qty*(x-entry)-entry_fee-qty*x*fee
    equity+=pnl;trades.append((entry_time,t,side,entry,x,qty,pnl,"end_of_data"))
    # Last monthly mark must agree with forced end-of-data close, after costs.
    if marks:marks[-1]=(marks[-1][0],equity)
# Every closed trade has both fees in net_usd; no unrealized position remains.
assert abs(capital+sum(float(row[6]) for row in trades)-equity)<1e-7, "NAV/trade reconciliation failed"
def _trade_sum(rows):
    return sum(float(row[6]) for row in rows)
trade=pd.DataFrame(trades,columns=["entry_utc","exit_utc","side","entry_price","exit_price","quantity","net_usd","reason"])
trade.to_csv(OUT/"trades.csv",index=False)
months=pd.DataFrame(marks,columns=["month_ist","end_nav"])
months=months[(months.month_ist>="2026-01")&(months.month_ist<="2026-10")].copy()
months["start_nav"]=months.end_nav.shift(1).fillna(capital)
months["net_return_pct"]=100*(months.end_nav/months.start_nav-1)
months["entries"]=months.month_ist.map(month_entries).fillna(0).astype(int)
assert len(months)==10, f"Expected all 10 IST months, got {len(months)}"
assert abs(float(months.end_nav.iloc[-1])-equity)<1e-7, "Final monthly NAV mismatch"
# Realized PF is grouped by EXIT month, distinct from mark-to-market NAV returns.
# Include every losing exit and both-side fee-adjusted P&L; an empty group has no PF.
trade["exit_month_ist"]=pd.to_datetime(trade.exit_utc,utc=True).dt.tz_convert("Asia/Kolkata").dt.strftime("%Y-%m")
realized=[]
for m in months.month_ist:
    closed=trade.loc[trade.exit_month_ist.eq(m),"net_usd"]
    positive=float(closed.loc[closed>0].sum())
    negative=float(-closed.loc[closed<0].sum())
    realized.append((int(len(closed)),positive,negative,
                     positive/negative if negative>0 else (None if positive==0 else float("inf"))))
months[["closed_trades","realized_wins_net_usd","realized_losses_abs_net_usd","realized_pf"]]=pd.DataFrame(realized,index=months.index)
months.to_csv(OUT/"monthly_nav.csv",index=False)
wins=trade.loc[trade.net_usd>0,"net_usd"].sum() if len(trade) else 0
loss=-trade.loc[trade.net_usd<0,"net_usd"].sum() if len(trade) else 0
result={"window_ist":"2026-01-01 through 2026-10-31","validation":"unchanged 2025 trading rules; 2026 NAV started separately at 100","source":"https://github.com/sakshamverma2030/Algorithmic-Trading-Framework-in-Crypto-Python","strategy":"4H Ichimoku 9/26/52/26 TK cross cloud Chikou causal","cost":"0.05% per side plus 18% GST; zero slippage; funding unmodeled","risk":"0.5% nominal initial risk, 1x notional cap; 2ATR stop added as protective overlay","source_missing_minutes":q.get("missing_minutes"),"candle_frame_hash_sha256":source_hash,"trades":len(trade),"pf":float(wins/loss) if loss else None,"end_nav":float(equity),"max_dd_pct":100*maxdd,"positive_months":int((months.net_return_pct>0).sum()),"losing_months":int((months.net_return_pct<0).sum()),"flat_months":int((months.net_return_pct==0).sum()),"months":len(months)}
(OUT/"summary.json").write_text(json.dumps(result,indent=2))
print("ICHIMOKU_BTC2026_FROZEN_DONE",json.dumps(result))
