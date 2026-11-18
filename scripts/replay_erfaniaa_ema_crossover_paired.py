#!/usr/bin/env python3
"""Independent causal replay of Erfaniaa's example EMA50/EMA100 crossover.
Source SHA 044e8bb516177c8a6a1803e54b482dc4ed9446cb.
15m completed close EMA cross, enter following 15m open, 1% TP/SL,
1x gross exposure, one trade, 1m conservative stop-first fills.
Uses native Delta India BTCUSD/ETHUSD 1m candles with checksums.
January IST incomplete and funding unmodeled: diagnostic, never certified.
"""
import hashlib,json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"analysis"/"external_github_profit_hunt"/"erfaniaa_ema50_100"
MONTHS=pd.period_range("2025-01","2026-10",freq="M").astype(str).tolist()
START=10000.0
FEE=0.0005*1.18
SRC="https://github.com/Erfaniaa/crypto-trading-strategy-backtester"
SHA="044e8bb516177c8a6a1803e54b482dc4ed9446cb"

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
    assert len(df)%15==0
    c15=cl[14::15]
    # The source computes EMA50/100 from last completed 15m candle.
    ema50=pd.Series(c15).ewm(span=50,adjust=False).mean().to_numpy()
    ema100=pd.Series(c15).ewm(span=100,adjust=False).mean().to_numpy()
    cross=np.zeros(len(c15),dtype=np.int8)
    cross[1:][(ema50[1:]>ema100[1:])&(ema50[:-1]<=ema100[:-1])]=1
    cross[1:][(ema50[1:]<ema100[1:])&(ema50[:-1]>=ema100[:-1])]=-1
    # For 15m interval k: completed bar k-1 signal known at first minute k.
    entries=np.zeros(len(df),dtype=np.int8)
    entries[15::15]=cross[:-1]
    # Warmup 256 1m bars minimum in original; use 100 full 15m candles to
    # avoid EMA seeding contamination and be more conservative.
    entries[:1500]=0
    slip=0.0005 if symbol=="BTCUSD" else 0.0002
    capital=START;side=0;qty=0.0;entry=0.0;entry_fee=0.0
    take=0.0;stop=0.0;entry_ts=0
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
        if side==0 and entries[i]!=0 and month in months and capital>0:
            side=int(entries[i]);entry=op[i]*(1+side*slip)
            qty=capital/entry # 1x leverage
            entry_fee=qty*entry*FEE;capital-=entry_fee
            stop=entry*(1-side*0.01);take=entry*(1+side*0.01)
            entry_ts=int(ts[i])
        if side:
            # Stop-first when both intraminute levels touched, conservative.
            stop_hit=(lo[i]<=stop if side==1 else hi[i]>=stop)
            take_hit=(hi[i]>=take if side==1 else lo[i]<=take)
            if stop_hit or take_hit:
                level=stop if stop_hit else take
                # Gap beyond stop on open must use worse actual open.
                if stop_hit:
                    level=min(level,op[i]) if side==1 else max(level,op[i])
                exit_price=level*(1-side*slip)
                fee=qty*exit_price*FEE
                net=(exit_price-entry)*side*qty-entry_fee-fee
                capital+=(exit_price-entry)*side*qty-fee
                exit_month=month
                if exit_month in months:
                    z=months[exit_month];z["trades"]+=1
                    z["wins"]+=int(net>0);z["losses"]+=int(net<0)
                    z["profit"]+=max(net,0);z["loss"]+=max(-net,0)
                    z["realized_pnl"]+=net
                records.append(dict(entry_utc=entry_ts,exit_utc=int(ts[i]),
                  entry_month_ist=pd.Timestamp(entry_ts,unit="s",tz="UTC").tz_convert("Asia/Kolkata").strftime("%Y-%m"),
                  exit_month_ist=exit_month,side=side,entry_price=entry,exit_price=exit_price,
                  qty=qty,net_trade_pnl=net,stop_first=bool(stop_hit)))
                side=0;qty=0;entry_fee=0
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
    print("EMA_CROSS_PAIRED "+json.dumps(result),flush=True)
    return result

def main():
    results=[simulate(s) for s in ("BTCUSD","ETHUSD")]
    verdict=dict(source=SRC,source_sha=SHA,results=results,
      fully_verified=False,
      limitations=["January 2025 IST lacks Dec 2024 18:30 UTC start",
        "Actual settled funding not modeled",
        "L1 depth, liquidations and bid/ask impact not modeled",
        "Stop-first same-minute fills; no 1m internal price path",
        "Monthly account equity marked at month-end but trade PF assigned to exit month",
        "Source uses 15m EMA50/100 crossover, 1% TP/SL, leverage 1x; causal reinterpretation",
        "2026 has been researched before, not pristine OOS"])
    (OUT/"verdict.json").write_text(json.dumps(verdict,indent=2)+"\n")
if __name__=="__main__":main()
