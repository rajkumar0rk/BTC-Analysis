#!/usr/bin/env python3
"""Causal independent paired replay of MAKSAT-DEL/mtf-breakout-bot.

Pinned upstream SHA: 9903df12cb3ed13a79a0646cea37f4b311c15bf6
main.py: EMA50 1h/4h/1d alignment, previous UTC daily high/low +/-1.5%,
ADX14>=25, 1h volume >= 1.2*volume-SMA20, ATR14 initial 3.5x stop,
breakeven after +2 ATR and trailing 2 ATR. 1% equity initial risk, capped
at 1x notional, next-hour entry, next-minute trailing updates only.
Causal corrections: completed 4h/daily EMA, stop check precedes trailing
update, position stops checked even when entry filters fail.
No live orders. Diagnostic until Jan IST warmup and settled funding are fixed.
"""
from pathlib import Path
import hashlib,json
import numpy as np
import pandas as pd
import talib
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"analysis/external_github_profit_hunt/maksat_mtf_breakout_paired"
M=pd.period_range("2025-01","2026-10",freq="M").astype(str).tolist()
INIT=10000.
FEE=.0005*1.18
SHA="9903df12cb3ed13a79a0646cea37f4b311c15bf6"
def load(sym):
    base=ROOT/"data/delta_india"/sym/"1m"
    man=json.loads((base/"manifest.json").read_text())
    assert man["symbol"]==sym
    part={p["file"][:7]:p for p in man["partitions"]}
    dfs=[]
    for ym in M:
        p=part[ym]
        assert p["missing_minutes"]==0
        path=base/p["file"]
        assert hashlib.sha256(path.read_bytes()).hexdigest()==p["sha256_gzip"]
        df=pd.read_csv(path,compression="gzip")
        for key in ("time","open","high","low","close","volume"):
            assert key in df.columns,("MISSING REQUIRED MARKET DATA",sym,ym,key)
        assert len(df)==p["observed_candles"]
        dfs.append(df[["time","open","high","low","close","volume"]])
    b=pd.concat(dfs,ignore_index=True)
    t=b.time.to_numpy(np.int64)
    assert np.all(np.diff(t)==60)
    assert t[0]==int(pd.Timestamp("2025-01-01",tz="UTC").timestamp())
    assert len(t)%1440==0
    return b
def replay(sym):
    b=load(sym)
    ts=b.time.to_numpy(np.int64)
    op=b.open.to_numpy(float);hi=b.high.to_numpy(float)
    lo=b.low.to_numpy(float);cl=b.close.to_numpy(float)
    vol=b.volume.to_numpy(float)
    assert np.isfinite(vol).all() and (vol>=0).all()
    assert np.isfinite(cl).all() and (cl>0).all()
    h1=hi.reshape(-1,60).max(axis=1)
    l1=lo.reshape(-1,60).min(axis=1)
    c1=cl[59::60]
    v1=vol.reshape(-1,60).sum(axis=1)
    e1=talib.EMA(c1,timeperiod=50)
    e4=talib.EMA(c1[3::4],timeperiod=50)
    ed=talib.EMA(c1[23::24],timeperiod=50)
    atr=talib.SMA(np.maximum(h1-l1,np.maximum(abs(h1-np.r_[np.nan,c1[:-1]]),abs(l1-np.r_[np.nan,c1[:-1]]))),timeperiod=14)
    adx=talib.ADX(h1,l1,c1,timeperiod=14)
    vma=talib.SMA(v1,timeperiod=20)
    d_hi=h1.reshape(-1,24).max(axis=1)
    d_lo=l1.reshape(-1,24).min(axis=1)
    count=len(c1)
    sig=np.zeros(count,dtype=np.int8)
    dist=np.zeros(count,dtype=float)
    # Signal hour j closes before next open (minute 60*(j+1)).
    # 4h/daily EMA uses a bar only after its completion; previous daily
    # breakout boundary always refers to PREVIOUS UTC calendar day.
    for j in range(1200,count-1):
        i4=(j+1)//4-1
        i24=(j+1)//24-1
        prev_day=j//24-1
        if min(i4,i24,prev_day)<0:continue
        vals=(e1[j],e4[i4],ed[i24],atr[j],adx[j],vma[j])
        if not np.isfinite(vals).all() or atr[j]<=0 or vma[j]<=0:continue
        if adx[j]<25 or v1[j]<1.2*vma[j]:continue
        long=(c1[j]>d_hi[prev_day]*1.015) and all(c1[j]>x for x in vals[:3])
        short=(c1[j]<d_lo[prev_day]*.985) and all(c1[j]<x for x in vals[:3])
        if long or short:
            sig[j+1]=1 if long else -1
            dist[j+1]=atr[j]
    cutoff=int(pd.Timestamp("2026-10-31 18:30:00",tz="UTC").timestamp())
    n=np.searchsorted(ts,cutoff)
    month=pd.to_datetime(ts[:n],unit="s",utc=True).tz_convert("Asia/Kolkata").strftime("%Y-%m").to_numpy()
    assert set(month)==set(M)
    z={m:dict(month_ist=m,trades=0,entries=0,wins=0,losses=0,positive_pnl=0.,negative_pnl=0.,active_minutes=0) for m in M}
    eq={};trades=[]
    cash=INIT;side=0;qty=0.;entry=0.;entry_fee=0.;entrytime=0;stop=0.;entry_atr=0.
    previous=""
    def adverse(raw,s,entry_leg):
        direction=s if entry_leg else -s
        return raw+direction*5 if sym=="BTCUSD" else raw*(1+direction*.0002)
    for i in range(n):
        mm=month[i];row=z[mm]
        if mm!=previous and previous in z:
            eq[previous]=cash+(cl[i-1]-entry)*side*qty if side else cash
        previous=mm
        if i%60==0 and not side and sig[i//60] and cash>0 and dist[i//60]>0:
            side=int(sig[i//60])
            entry=adverse(op[i],side,True)
            entry_atr=dist[i//60]
            qty=min(cash/entry,cash*.01/(3.5*entry_atr))
            if qty>0:
                entry_fee=abs(qty*entry)*FEE
                cash-=entry_fee
                stop=entry-side*3.5*entry_atr
                entrytime=int(ts[i])
                row["entries"]+=1
            else:side=0
        if side:
            row["active_minutes"]+=1
            hit=lo[i]<=stop if side==1 else hi[i]>=stop
            if hit:
                raw=min(op[i],stop) if side==1 else max(op[i],stop)
                xp=adverse(raw,side,False)
                feeout=abs(xp*qty)*FEE
                net=(xp-entry)*side*qty-entry_fee-feeout
                cash+=(xp-entry)*side*qty-feeout
                row["trades"]+=1;row["wins"]+=int(net>0);row["losses"]+=int(net<0)
                row["positive_pnl"]+=max(net,0);row["negative_pnl"]+=max(-net,0)
                trades.append(dict(entry_utc=entrytime,exit_utc=int(ts[i]),side=side,qty=qty,entry_price=entry,exit_price=xp,
                                   entry_fee=entry_fee,exit_fee=feeout,net_pnl=net,exit_month_ist=mm,stop_first=True))
                side=0
            else:
                # Stop is updated only AFTER this minute's stop check.
                # Favorable excursion observed in this bar can activate BE
                # from NEXT minute, never retroactively on its own bar.
                favorable=(hi[i]-entry if side==1 else entry-lo[i])
                if favorable>=2*entry_atr:
                    stop=max(stop,entry) if side==1 else min(stop,entry)
                trail=cl[i]-side*2*entry_atr
                stop=max(stop,trail) if side==1 else min(stop,trail)
    if previous in z:
        eq[previous]=cash+(cl[n-1]-entry)*side*qty if side else cash
    results=[]
    old=INIT
    for mm in M:
        row=z[mm];end=eq[mm]
        ret=(end/old-1)*100;old=end
        p=row["positive_pnl"];loss=row["negative_pnl"]
        pf=p/loss if loss else (float("inf") if p else None)
        results.append({**row,"marked_equity":end,"monthly_net_return_pct":ret,
            "profit_factor":round(pf,6) if pf is not None and np.isfinite(pf) else ("Infinity" if pf else "N/A"),
            "high_pf_positive_month":bool(pf is not None and pf>=1.5 and ret>0),
            "inactive":bool(row["active_minutes"]==0 and row["entries"]==0 and row["trades"]==0)})
    out=pd.DataFrame(results);OUT.mkdir(parents=True,exist_ok=True)
    assert all(abs(v)<1e-10 for v in out.loc[out.inactive,"monthly_net_return_pct"])
    out.to_csv(OUT/(sym+"_22_months.csv"),index=False)
    pd.DataFrame(trades).to_csv(OUT/(sym+"_trades.csv.gz"),index=False,compression="gzip")
    e=out.marked_equity.to_numpy()
    e25=out.loc[out.month_ist=="2025-12","marked_equity"].iloc[0]
    result=dict(symbol=sym,trades=len(trades),wins=int(out.wins.sum()),losses=int(out.losses.sum()),
                high_pf_months=int(out.high_pf_positive_month.sum()),
                positive_months=int((out.monthly_net_return_pct>0).sum()),
                negative_months=int((out.monthly_net_return_pct<0).sum()),
                inactive_months=int(out.inactive.sum()),
                median_monthly_return_pct=float(out.monthly_net_return_pct.median()),
                aggregate_pf=float(out.positive_pnl.sum()/out.negative_pnl.sum()) if out.negative_pnl.sum()>0 else None,
                total_net_pct=float(100*(e[-1]/INIT-1)),
                net_2025_pct=float(100*(e25/INIT-1)),
                net_2026_jan_oct_pct=float(100*(e[-1]/e25-1)),
                max_month_end_dd_pct=float(np.max(1-e/np.maximum.accumulate(np.r_[INIT,e])[1:])*100),
                complete_ist_jan_2025=False,funding_modeled=False)
    print("MAKSAT_PAIRED "+json.dumps(result),flush=True)
    return result
def main():
    results=[replay(s) for s in ("BTCUSD","ETHUSD")]
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"verdict.json").write_text(json.dumps(dict(source="https://github.com/MAKSAT-DEL/mtf-breakout-bot",
        source_sha=SHA,results=results,fully_verified=False,
        causal_repairs=["No 4h/daily EMA future leak","Stop checked before trailing update",
          "Open position stop checked independently of entry filters",
          "Next 1h open fills, 1m OHLC stop-first"],
        deviations=["1x notional cap, taker+GST+slippage, actual source omitted fees",
          "No real funding, spread, depth, market impact or liquidation",
          "2024-12-31 18:30-23:59 UTC Jan IST gap","2026 research-exposed"]),indent=2)+"\n")
if __name__=="__main__":main()
