#!/usr/bin/env python3
"""MR002 source-derived VWAP z crossback, authentic BTC 1m conservative replay.
Pinned source: vaultik/algo-trading-system 7f9bcd24d0e1cf7258699f4835ecd80dcb684a84
The original publisher uses Bybit 5m, 3x leverage and optimistic intrabar fills.
This research adaptation uses 1x NAV notional, 1m stop-first, zero slippage,
0.05% taker fee each side plus 18% GST, and funding UNMODELED.
"""
import hashlib, json
from pathlib import Path
import numpy as np
import pandas as pd
from research_every_candle_200 import read_archive
OUT=Path("analysis/mean_reversion_research/MR002/results")
MONTHS=pd.period_range("2025-01","2026-10",freq="M").astype(str).tolist()
FEE=.0005*1.18
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    raw,seg_start,seg_end,quality=read_archive()
    raw=raw.loc[raw.index < pd.Timestamp("2026-11-01 00:00",tz="UTC")].copy()
    # Strict 5m groups: all five original minute timestamps required.
    g=raw.resample("5min",label="left",closed="left")
    bars=g.agg({"open":"first","high":"max","low":"min","close":"last","volume":"sum","time":"count"})
    bars=bars[bars.time.eq(5)].copy()
    # 5m continuity for indicator warmup; never bridge a missing 5m bar.
    tp=(bars.high+bars.low+bars.close)/3
    vol=bars.volume
    tv=tp*vol
    vwap=tv.rolling(288,min_periods=288).sum()/vol.rolling(288,min_periods=288).sum()
    variance=((tp*tp*vol).rolling(288,min_periods=288).sum()/vol.rolling(288,min_periods=288).sum()-vwap*vwap).clip(lower=0)
    sd=np.sqrt(variance)
    rvol=vol/vol.rolling(288,min_periods=288).mean()
    z=(bars.close-vwap)/sd.replace(0,np.nan)
    # Reset rolling window at 5m discontinuities: count consecutive groups.
    grp=(bars.index.to_series().diff().dt.total_seconds().fillna(300)!=300).cumsum()
    consecutive=bars.groupby(grp).cumcount()+1
    valid=consecutive>=289
    signals=[]
    for k in np.flatnonzero(valid.to_numpy()):
        if k==0:continue
        side=1 if z.iat[k-1]<-3 and z.iat[k]>=-3 else (-1 if z.iat[k-1]>3 and z.iat[k]<=3 else 0)
        if not side or not np.isfinite(rvol.iat[k-1]) or rvol.iat[k-1]<2.5:continue
        # Signal 5m bar closes at timestamp +5m, trade at that instant's 1m open.
        ts=bars.index[k]+pd.Timedelta(minutes=5)
        signals.append((ts,side,float(vwap.iat[k]),float(sd.iat[k])))
    op=raw.open.to_numpy(float); hi=raw.high.to_numpy(float)
    lo=raw.low.to_numpy(float); cl=raw.close.to_numpy(float)
    times=raw.index; lookup={int(t.value//10**9):i for i,t in enumerate(times)}
    rows=[]; cash=1.;peak=1.;dd=0.;last_end=-1
    month_end_nav={}
    # Track minute-level NAV, including floating PnL, to avoid exit-month accounting bias.
    minute_nav=np.full(len(raw),np.nan)
    cursor=0
    for ts,side,vw,sd0 in signals:
        k=lookup.get(int(ts.value//10**9))
        if k is None or k<=last_end or k<cursor or not np.isfinite(sd0) or sd0<=0:continue
        if times[k].strftime("%Y-%m") not in MONTHS:continue
        entry=op[k]
        stop=vw-side*4*sd0
        tp1=vw-side*sd0
        tp2=vw
        if side==1:
            if tp1<=entry:tp1=entry+.5*sd0
            if tp2<=tp1:tp2=tp1+.5*sd0
        else:
            if tp1>=entry:tp1=entry-.5*sd0
            if tp2>=tp1:tp2=tp1-.5*sd0
        # Gaps beyond the structural stop are not tradable at an assumed better fill.
        if side*(entry-stop)<=0:continue
        # Pre-entry idle NAV must not include a fee paid only at entry.
        minute_nav[cursor:k]=cash
        qty=cash/entry
        start_cash=cash
        fee_in=qty*entry*FEE
        cash-=fee_in
        realized=0.;rem=qty;partial=False
        exit_parts=[];end=min(k+240,len(raw),int(seg_end[k]))
        if end<=k:continue
        for j in range(k,end):
            # Mark-to-market at 1m close; prioritize stop over TP on same minute.
            if side==1:
                stop_hit=lo[j]<=stop;target1=hi[j]>=tp1;target2=hi[j]>=tp2
            else:
                stop_hit=hi[j]>=stop;target1=lo[j]<=tp1;target2=lo[j]<=tp2
            action=None;px=None;fraction=0.
            if stop_hit:
                action="stop";px=min(op[j],stop) if side==1 else max(op[j],stop);fraction=1.
            elif not partial and target1:
                action="tp1";px=tp1;fraction=.5
            elif partial and target2:
                action="tp2";px=tp2;fraction=1.
            elif j==end-1:
                action="timeout_or_gap";px=cl[j];fraction=1.
            if action:
                closed=rem*fraction
                pnl=side*closed*(px-entry)
                fee=closed*px*FEE
                cash+=pnl-fee;realized+=pnl-fee
                rem-=closed
                exit_parts.append(dict(time_utc=str(times[j]),reason=action,price=px,quantity=closed,pnl=pnl,fee=fee))
                if action=="tp1":
                    partial=True;stop=entry
                if rem<=qty*1e-9:
                    rem=0.
            minute_nav[j]=cash+side*rem*(cl[j]-entry)
            peak=max(peak,minute_nav[j]);dd=max(dd,1-minute_nav[j]/peak)
            if rem==0:break
        last_end=j;cursor=j+1
        rows.append(dict(entry_utc=str(times[k]),exit_utc=str(times[j]),side=side,
                         entry_price=entry,initial_stop=vw-side*4*sd0,
                         tp1=tp1,tp2=tp2,entry_fee=fee_in,
                         gross_pnl=sum(x["pnl"] for x in exit_parts),
                         exit_fees=sum(x["fee"] for x in exit_parts),
                         net_pnl=realized-fee_in,
                         nav_before=start_cash,nav_after=cash,
                         exit_parts=json.dumps(exit_parts),entry_month_ist=times[k].tz_convert("Asia/Kolkata").strftime("%Y-%m")))
    minute_nav[cursor:]=cash
    # Month end NAV is sampled from every actual 1m close, not trade-close attribution.
    nav=pd.Series(minute_nav,index=times).ffill()
    ist=nav.tz_convert("Asia/Kolkata")
    ends=ist.resample("ME").last()
    start_nav=1.;monthly=[]
    for m in MONTHS:
        # Period end timezone matching via PeriodIndex avoids DST and month-label confusion.
        e=next((float(v) for t,v in ends.items() if t.strftime("%Y-%m")==m),float("nan"))
        if not np.isfinite(e):raise RuntimeError("Missing IST month "+m)
        monthly.append(dict(month_ist=m,net_return_pct=(e/start_nav-1)*100,
                            end_nav=e,trade_entries=sum(x["entry_month_ist"]==m for x in rows)))
        start_nav=e
    ledger=pd.DataFrame(rows);table=pd.DataFrame(monthly)
    ledger.to_csv(OUT/"trade_ledger.csv",index=False)
    table.to_csv(OUT/"monthly_ist_nav.csv",index=False)
    # All minute marks saved for audit, compressed to avoid artifact size blowup.
    nav.rename("account_nav").to_csv(OUT/"minute_nav.csv.gz",compression="gzip")
    # Stop-first on every minute is conservative, but entry-minute OHLC paths
    # are unknowable: an adverse gap at the next open must not be filled
    # at a more favorable stop.
    summary=dict(source_commit="7f9bcd24d0e1cf7258699f4835ecd80dcb684a84",
                 data_quality=quality,signals=len(signals),trades=len(rows),
                 net_return_pct=100*(cash-1),positive_months=int((table.net_return_pct>0).sum()),
                 losing_months=int((table.net_return_pct<0).sum()),
                 flat_months=int((table.net_return_pct==0).sum()),
                 max_minute_close_drawdown_pct=100*dd,
                 gross_pnl=float(ledger.gross_pnl.sum()) if len(ledger) else 0,
                 entry_fees=float(ledger.entry_fee.sum()) if len(ledger) else 0,
                 exit_fees=float(ledger.exit_fees.sum()) if len(ledger) else 0,
                 fee_gst_per_side=FEE,slippage_price_points_per_side=0,
                 funding="UNMODELED",sizing="1x current NAV notional",
                 note="Source-derived adaptation; stop-first 1m; no authentic L1 bid/ask or margin model")
    assert abs(cash-(1+float(ledger.net_pnl.sum())))<1e-7,"P&L NAV mismatch"
    (OUT/"summary.json").write_text(json.dumps(summary,indent=2,default=str))
    print(json.dumps({k:v for k,v in summary.items() if k!="data_quality"},indent=2))
if __name__=="__main__":main()
