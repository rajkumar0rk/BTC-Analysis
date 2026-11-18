#!/usr/bin/env python3
"""Paired causal Donchian20 breakout / ATR14 stop replay.
Pinned upstream: https://github.com/3kpro/3K_Trading_Bot_V2
SHA ce1656d3589db4446330d981f5cf2c8b770d29e6.
1h completed close vs prior 20h high/low; next 1h open entry.
Stop 2x ATR14; opposite breakout next-hour-open exit; 1m stop monitoring.
1% equity risk capped at 1x exposure, 0.05% taker each side + 18% GST,
BTC 5bps and ETH 2bps adverse per side, month-end MTM.
Corrected causal execution differs from source's same-bar close fills.
Diagnostic: missing Dec 2024 IST January hours and funding/depth data.
"""
import hashlib,json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"analysis"/"external_github_profit_hunt"/"3kpro_donchian20_1h"
MONTHS=pd.period_range("2025-01","2026-10",freq="M").astype(str).tolist()
START=10000.0
FEE=0.0005*1.18
SRC="https://github.com/3kpro/3K_Trading_Bot_V2"
SHA="ce1656d3589db4446330d981f5cf2c8b770d29e6"

def load(symbol):
    base=ROOT/"data"/"delta_india"/symbol/"1m"
    manifest=json.loads((base/"manifest.json").read_text())
    assert manifest["symbol"]==symbol
    parts={p["file"][:7]:p for p in manifest["partitions"]}
    required=pd.period_range("2025-01","2026-10",freq="M").astype(str).tolist()
    frames=[]
    for ym in required:
        p=parts[ym]
        assert p["missing_minutes"]==0,(symbol,ym,"incomplete")
        path=base/p["file"]
        assert hashlib.sha256(path.read_bytes()).hexdigest()==p["sha256_gzip"]
        df=pd.read_csv(path,compression="gzip",usecols=["time","open","high","low","close"])
        assert len(df)==p["observed_candles"]
        frames.append(df)
    data=pd.concat(frames,ignore_index=True)
    t=data.time.to_numpy(np.int64)
    assert np.all(np.diff(t)==60),(symbol,"gaps")
    for name in ("open","high","low","close"):
        assert np.isfinite(data[name].to_numpy(float)).all()
    return data,dict(first_utc=str(pd.to_datetime(t[0],unit="s",utc=True)),
                     last_utc=str(pd.to_datetime(t[-1],unit="s",utc=True)),
                     partitions=len(frames),missing_prior_utc_2024_12_31=True)

def simulate(symbol):
    df,quality=load(symbol)
    ts=df.time.to_numpy(np.int64)
    op=df.open.to_numpy(float);hi=df.high.to_numpy(float)
    lo=df.low.to_numpy(float);cl=df.close.to_numpy(float)
    assert len(df)%60==0
    # 1-hour candles formed only from fully completed native 1m bars.
    c60=cl[59::60];h60=hi.reshape(-1,60).max(axis=1)
    l60=lo.reshape(-1,60).min(axis=1)
    upper=pd.Series(h60).shift(1).rolling(20,min_periods=20).max().to_numpy()
    lower=pd.Series(l60).shift(1).rolling(20,min_periods=20).min().to_numpy()
    prev=np.r_[np.nan,c60[:-1]]
    tr=np.maximum(h60-l60,np.maximum(abs(h60-prev),abs(l60-prev)))
    atr=pd.Series(tr).rolling(14,min_periods=14).mean().to_numpy()
    # Donchian source default RSI_MIN=0 and RSI_MAX=100, so no filtering.
    signal=np.zeros(len(c60),dtype=np.int8)
    signal[(c60>upper)&np.isfinite(atr)]=1
    signal[(c60<lower)&np.isfinite(atr)]=-1
    entries=np.zeros(len(df),dtype=np.int8)
    stop_dist=np.zeros(len(df))
    entries[60::60]=signal[:-1]
    stop_dist[60::60]=2*atr[:-1]
    entries[:1440]=0
    slip=0.0005 if symbol=="BTCUSD" else 0.0002
    capital=START;side=0;qty=0.0;entry=0.0;entry_fee=0.0
    stop=0.0;entry_ts=0
    records=[]
    months={m:dict(month_ist=m,trades=0,wins=0,losses=0,
      profit=0.0,loss=0.0,realized_pnl=0.0) for m in MONTHS}
    monthly_equity={}
    lastmonth=""
    for i in range(len(ts)):
        # Close previous IST month at last 1m close, marking any open trade.
        month=pd.Timestamp(ts[i],unit="s",tz="UTC").tz_convert("Asia/Kolkata").strftime("%Y-%m")
        if month!=lastmonth and lastmonth in months:
            mark=cl[i-1]
            floating=(mark-entry)*side*qty if side else 0.0
            monthly_equity[lastmonth]=capital+floating
        lastmonth=month
        # The source exits at stop or opposite Donchian breakout; execute
        # opposite signal on the next 1h bar open, not the signal bar close.
        opposite=bool(side and entries[i]==-side)
        stop_hit=bool(side and (lo[i]<=stop if side==1 else hi[i]>=stop))
        if side and (opposite or stop_hit):
            if stop_hit:
                level=min(stop,op[i]) if side==1 else max(stop,op[i])
            else:
                level=op[i]
            exit_price=level*(1-side*slip)
            fee=qty*exit_price*FEE
            net=(exit_price-entry)*side*qty-entry_fee-fee
            capital+=(exit_price-entry)*side*qty-fee
            if month in months:
                z=months[month];z["trades"]+=1
                z["wins"]+=int(net>0);z["losses"]+=int(net<0)
                z["profit"]+=max(net,0);z["loss"]+=max(-net,0)
                z["realized_pnl"]+=net
            records.append(dict(entry_utc=entry_ts,exit_utc=int(ts[i]),
                entry_month_ist=pd.Timestamp(entry_ts,unit="s",tz="UTC").tz_convert("Asia/Kolkata").strftime("%Y-%m"),
                exit_month_ist=month,side=side,entry_price=entry,exit_price=exit_price,
                qty=qty,net_trade_pnl=net,stop_first=bool(stop_hit)))
            side=0;qty=0;entry_fee=0
        # No same-bar reversal: the next independent entry is allowed only
        # on a subsequent completed 1h signal after the prior position exits.
        elif side==0 and entries[i]!=0 and month in months and capital>0 and stop_dist[i]>0:
            side=int(entries[i]);entry=op[i]*(1+side*slip)
            # Risk 1% account equity, capped at 1x gross notional.
            qty=min(capital/entry,capital*0.01/stop_dist[i])
            if qty<=0:
                side=0
                continue
            entry_fee=qty*entry*FEE;capital-=entry_fee
            stop=entry-side*stop_dist[i]
            entry_ts=int(ts[i])
    if lastmonth in months:
        monthly_equity[lastmonth]=capital+((cl[-1]-entry)*side*qty if side else 0)
    previous=START
    rows=[]
    for month in MONTHS:
        z=months[month]
        end=monthly_equity.get(month)
        if end is None:raise RuntimeError("Month missing "+month)
        ret=100*(end/previous-1) if previous>0 else float("nan")
        previous=end
        pf=z["profit"]/z["loss"] if z["loss"]>0 else (float("inf") if z["profit"]>0 else float("nan"))
        rows.append({**z,"month_end_marked_equity":end,"monthly_net_return_pct":ret,
                     "profit_factor":round(pf,6) if np.isfinite(pf) else ("Infinity" if pf>0 else "N/A"),
                     "high_pf_positive_month":bool(pf>=1.5 and ret>0)})
    out=pd.DataFrame(rows)
    trades=pd.DataFrame(records)
    OUT.mkdir(parents=True,exist_ok=True)
    out.to_csv(OUT/(symbol+"_22_months.csv"),index=False)
    trades.to_csv(OUT/(symbol+"_trades.csv.gz"),index=False,compression="gzip")
    p=out.profit.to_numpy().sum();l=out.loss.to_numpy().sum()
    y2025=100*(out.loc[out.month_ist=="2025-12","month_end_marked_equity"].iloc[0]/START-1)
    y2026=100*(out.iloc[-1].month_end_marked_equity/out.loc[out.month_ist=="2025-12","month_end_marked_equity"].iloc[0]-1)
    eq=out.month_end_marked_equity.to_numpy()
    dd=np.max(1-eq/np.maximum.accumulate(np.r_[START,eq])[1:])*100
    result=dict(symbol=symbol,source=SRC,sha=SHA,
       trades=len(trades),profitable_months=int((out.monthly_net_return_pct>0).sum()),
       high_pf_months=int(out.high_pf_positive_month.sum()),
       losing_months=int((out.monthly_net_return_pct<0).sum()),
       overall_profit_factor=float(p/l) if l else None,
       total_return_pct=float(100*(eq[-1]/START-1)),
       year_2025_return_pct=float(y2025),year_2026_jan_oct_ytd_return_pct=float(y2026),
       max_month_end_drawdown_pct=float(dd),monthly_mtm=True,
       complete_ist_january_2025=False,funding_settlements_modeled=False,
       quality=quality)
    print("DONCHIAN20_PAIRED "+json.dumps(result),flush=True)
    return result

def main():
    results=[simulate(s) for s in ("BTCUSD","ETHUSD")]
    verdict=dict(source=SRC,source_sha=SHA,results=results,
      fully_verified=False,
      limitations=["January 2025 IST lacks Dec 2024 18:30 UTC start",
        "Actual settled funding not modeled",
        "L1 depth, liquidations and bid/ask impact not modeled",
        "1m OHLC stop fills; no intra-minute price path",
        "Monthly account equity marked at month-end but trade PF assigned to exit month",
        "Source uses 1h Donchian20 breakout, 2x ATR14 stop, RSI0-100 unrestricted; this causal replay fixes same-bar fills, adds 1m stops and 1x cap, exits opposite signal at next-hour open",
        "2026 has been researched before, not pristine OOS"])
    (OUT/"verdict.json").write_text(json.dumps(verdict,indent=2)+"\n")
if __name__=="__main__":main()
