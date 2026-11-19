#!/usr/bin/env python3
"""Paired FAdxSmaStrategy diagnostic replay; no live orders.

Upstream: freqtrade/freqtrade-strategies@f3340ce11f5bdf62f598522e64d1f5638eaa13f5
user_data/strategies/futures/FAdxSmaStrategy.py.
Predeclared defaults: 1h SMA12/SMA48 cross, ADX14>30 entry; ADX14<30 exit,
5% protective stop, Freqtrade minimal_roi {0:5%,30:10%,60:7.5%}.
Independent changes: completed-hour signals -> following hour open; 1x gross
notional, one position, stop-first 1m OHLC execution, taker fee+GST,
BTC 5 USD price points or ETH 2bps adverse slippage per leg.
Not a full verification: missing Dec 2024 18:30-23:59 UTC starting January IST;
funding, bid/ask depth, liquidation and spreads unavailable.
"""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import talib

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "analysis/external_github_profit_hunt/fadx_sma_1h_paired"
MONTHS = pd.period_range("2025-01", "2026-10", freq="M").astype(str).tolist()
SOURCE_SHA = "f3340ce11f5bdf62f598522e64d1f5638eaa13f5"
INITIAL = 10000.0
FEE = .0005 * 1.18

def load(symbol):
    folder = ROOT / "data" / "delta_india" / symbol / "1m"
    manifest = json.loads((folder / "manifest.json").read_text())
    assert manifest["symbol"] == symbol
    parts = {p["file"][:7]: p for p in manifest["partitions"]}
    frames = []
    for ym in MONTHS:
        p = parts[ym]
        assert p["missing_minutes"] == 0, (symbol, ym, "not full UTC month")
        file = folder / p["file"]
        assert hashlib.sha256(file.read_bytes()).hexdigest() == p["sha256_gzip"]
        frame = pd.read_csv(file, compression="gzip", usecols=["time","open","high","low","close"])
        assert len(frame) == p["observed_candles"]
        frames.append(frame)
    bars = pd.concat(frames, ignore_index=True)
    ts = bars.time.to_numpy(np.int64)
    assert np.all(np.diff(ts) == 60), "Missing or duplicated 1m data"
    assert ts[0] == int(pd.Timestamp("2025-01-01", tz="UTC").timestamp())
    assert ts[-1] == int(pd.Timestamp("2026-10-31 23:59:00", tz="UTC").timestamp())
    for col in ["open","high","low","close"]:
        v = bars[col].to_numpy(float)
        assert np.isfinite(v).all()
        assert (v > 0).all()
    return bars

def replay(symbol):
    bars=load(symbol)
    ts=bars.time.to_numpy(np.int64)
    op=bars.open.to_numpy(float)
    hi=bars.high.to_numpy(float)
    lo=bars.low.to_numpy(float)
    cl=bars.close.to_numpy(float)
    assert len(ts)%60==0
    h=hi.reshape(-1,60).max(axis=1)
    l=lo.reshape(-1,60).min(axis=1)
    c=cl[59::60]
    fast=talib.SMA(c,timeperiod=12)
    slow=talib.SMA(c,timeperiod=48)
    adx=talib.ADX(h,l,c,timeperiod=14)
    above=(fast>slow)&(np.r_[False,fast[:-1]<=slow[:-1]])&(adx>30)
    below=(fast<slow)&(np.r_[False,fast[:-1]>=slow[:-1]])&(adx>30)
    close_adx=(adx<30)
    # Inputs for hour j derive ONLY from fully complete hour j-1.
    signal=np.zeros(len(c),dtype=np.int8)
    signal[1:][above[:-1]]=1
    signal[1:][below[:-1]]=-1
    sigexit=np.zeros(len(c),dtype=bool)
    sigexit[1:]=close_adx[:-1]
    # Do not treat January's missing 5.5 IST hours as filled; report it.
    active_end=int(pd.Timestamp("2026-10-31 18:30:00",tz="UTC").timestamp())
    last=np.searchsorted(ts,active_end)
    month=pd.to_datetime(ts[:last],unit="s",utc=True).tz_convert("Asia/Kolkata").strftime("%Y-%m").to_numpy()
    assert len(set(month))==22
    book={m:dict(month_ist=m,trades=0,entries=0,wins=0,losses=0,
                 gross_wins=0.0,gross_losses=0.0,active_minutes=0) for m in MONTHS}
    equity={}
    closed=[]
    cash=INITIAL
    side=0
    qty=0.0
    entry=0.0
    feein=0.0
    entrytime=0
    lastmonth=""
    def adverse(raw,s,is_entry):
        direction=s if is_entry else -s
        return raw + direction*5.0 if symbol=="BTCUSD" else raw*(1+direction*.0002)
    for i in range(last):
        mm=month[i]
        if mm!=lastmonth and lastmonth in book:
            equity[lastmonth]=cash+(cl[i-1]-entry)*side*qty if side else cash
        lastmonth=mm
        z=book[mm]
        boundary=i%60==0
        hour=i//60
        just_entered=False
        if side and boundary and sigexit[hour]:
            xp=adverse(op[i],side,False)
            feeout=abs(qty*xp)*FEE
            net=(xp-entry)*side*qty-feein-feeout
            cash+=(xp-entry)*side*qty-feeout
            z["trades"]+=1;z["wins"]+=int(net>0);z["losses"]+=int(net<0)
            z["gross_wins"]+=max(net,0);z["gross_losses"]+=max(-net,0)
            closed.append(dict(entry_utc=entrytime,exit_utc=int(ts[i]),side=side,qty=qty,
              entry_price=entry,exit_price=xp,entry_fee=feein,exit_fee=feeout,
              net_pnl=net,exit_reason="ADX",exit_month_ist=mm))
            side=0
        if not side and boundary and signal[hour] and cash>0 and not (closed and closed[-1]["exit_utc"]==int(ts[i])):
            side=int(signal[hour])
            entry=adverse(op[i],side,True)
            qty=max(0.0,cash/entry)
            feein=abs(qty*entry)*FEE
            cash-=feein
            entrytime=int(ts[i])
            z["entries"]+=1
            just_entered=True
        if side:
            z["active_minutes"]+=1
            stop=entry*(1-side*.05)
            age=(ts[i]-entrytime)//60
            roi=.05 if age<30 else (.10 if age<60 else .075)
            tp=entry*(1+side*roi)
            stop_hit=lo[i]<=stop if side==1 else hi[i]>=stop
            tp_hit=hi[i]>=tp if side==1 else lo[i]<=tp
            if stop_hit or tp_hit:
                # Stop-first when 1m OHLC touches both; gap through stop fills at open.
                if stop_hit:
                    raw=min(op[i],stop) if side==1 else max(op[i],stop)
                    reason="STOP"
                else:
                    raw=tp
                    reason="ROI"
                xp=adverse(raw,side,False)
                feeout=abs(qty*xp)*FEE
                net=(xp-entry)*side*qty-feein-feeout
                cash+=(xp-entry)*side*qty-feeout
                z["trades"]+=1;z["wins"]+=int(net>0);z["losses"]+=int(net<0)
                z["gross_wins"]+=max(net,0);z["gross_losses"]+=max(-net,0)
                closed.append(dict(entry_utc=entrytime,exit_utc=int(ts[i]),side=side,qty=qty,
                    entry_price=entry,exit_price=xp,entry_fee=feein,exit_fee=feeout,
                    net_pnl=net,exit_reason=reason,exit_month_ist=mm))
                side=0
    if lastmonth in book:
        equity[lastmonth]=cash+(cl[last-1]-entry)*side*qty if side else cash
    rows=[]
    prior=INITIAL
    for mm in MONTHS:
        z=book[mm]
        end=equity[mm]
        ret=100*(end/prior-1)
        prior=end
        profit=z["gross_wins"];loss=z["gross_losses"]
        pf=profit/loss if loss>0 else (float("inf") if profit>0 else None)
        rows.append({**z,"marked_equity":end,"monthly_net_return_pct":ret,
          "profit_factor":round(pf,6) if pf is not None and np.isfinite(pf) else ("Infinity" if pf else "N/A"),
          "high_pf_positive_month":bool(pf is not None and pf>=1.5 and ret>0),
          "completely_inactive_month":bool(z["active_minutes"]==0 and z["entries"]==0 and z["trades"]==0)})
    df=pd.DataFrame(rows)
    # All actually inactive months must be exactly flat and have undefined PF.
    for _,z in df[df.completely_inactive_month].iterrows():
        assert abs(z.monthly_net_return_pct)<1e-9 and z.profit_factor=="N/A"
    OUT.mkdir(parents=True,exist_ok=True)
    df.to_csv(OUT/(symbol+"_22_months.csv"),index=False)
    pd.DataFrame(closed).to_csv(OUT/(symbol+"_trades.csv.gz"),compression="gzip",index=False)
    eq=df.marked_equity.to_numpy()
    year_end=df.loc[df.month_ist=="2025-12","marked_equity"].iloc[0]
    draw=100*np.max(1-eq/np.maximum.accumulate(np.r_[INITIAL,eq])[1:])
    result=dict(symbol=symbol,trades=len(closed),
        wins=int(df.wins.sum()),losses=int(df.losses.sum()),
        high_pf_months=int(df.high_pf_positive_month.sum()),
        profitable_months=int((df.monthly_net_return_pct>0).sum()),
        losing_months=int((df.monthly_net_return_pct<0).sum()),
        inactive_months=int(df.completely_inactive_month.sum()),
        median_monthly_net_pct=float(df.monthly_net_return_pct.median()),
        median_positive_month_net_pct=float(df.loc[df.monthly_net_return_pct>0,"monthly_net_return_pct"].median()) if (df.monthly_net_return_pct>0).any() else None,
        aggregate_pf=float(df.gross_wins.sum()/df.gross_losses.sum()) if df.gross_losses.sum()>0 else None,
        net_22m_pct=float(100*(eq[-1]/INITIAL-1)),
        net_2025_pct=float(100*(year_end/INITIAL-1)),
        net_2026_ytd_pct=float(100*(eq[-1]/year_end-1)),
        max_month_end_drawdown_pct=float(draw),
        complete_january_2025_ist=False,settled_funding_modeled=False)
    print("FADX_PAIRED "+json.dumps(result),flush=True)
    return result

def main():
    results=[replay(s) for s in ("BTCUSD","ETHUSD")]
    verdict=dict(upstream_repo="https://github.com/freqtrade/freqtrade-strategies",
        source_sha=SOURCE_SHA,source_path="user_data/strategies/futures/FAdxSmaStrategy.py",
        results=results,fully_verified=False,
        differences=["Default SMA12/48 ADX14 used; TA-Lib indicators, no source hyperopt",
          "Signals execute at next 1h open; intraminute stop-first",
          "1x gross exposure, synthetic taker fills rather than actual order execution"],
        limitations=["January 2025 IST missing 2024-12-31 18:30-23:59 UTC; partial month only",
          "Real settled funding, bid/ask, market impact, margin/liquidation are not modeled",
          "Exit-month realized after-cost PF differs from month-end MTM account returns",
          "2026 previously researched, not pristine OOS",
          "Month-end MTM on open positions excludes hypothetical closeout fee",
          "One-minute candle path unknown: stop-first assumption"])
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"verdict.json").write_text(json.dumps(verdict,indent=2)+"\n")
if __name__=="__main__":
    main()
