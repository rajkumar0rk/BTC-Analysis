#!/usr/bin/env python3
"""EMA20 second-touch intrabar research. Exact rules in NOVELTY_CHECK.md."""
from pathlib import Path
import hashlib, json, math
import numpy as np
import pandas as pd

DATA=Path("data/delta_india")
OUT=Path("analysis/ema20_second_touch_20261121")
FEE=0.0005*1.18
SLIP=0.0002
START="2025-01"
LAST="2026-10"
CUTOFF=pd.Timestamp("2026-10-31T18:30:00Z")
MONTHS=pd.period_range(START,LAST,freq="M").astype(str).tolist()
assert len(MONTHS)==22

def read_source(symbol):
    root=DATA/symbol/"1m"
    manifest=json.loads((root/"manifest.json").read_text())
    parts=[p for p in manifest["partitions"] if "2025-01.csv.gz"<=p["file"]<="2026-10.csv.gz"]
    assert len(parts)==22, (symbol,len(parts))
    frames=[]
    for p in parts:
        path=root/p["file"]
        if hashlib.sha256(path.read_bytes()).hexdigest()!=p["sha256_gzip"]:
            raise RuntimeError("Source file checksum mismatch "+str(path))
        if p["missing_minutes"]!=0:
            raise RuntimeError("Missing candles "+str(path))
        f=pd.read_csv(path,compression="gzip",usecols=["time","open","high","low","close","volume"])
        if len(f)!=p["observed_candles"]:
            raise RuntimeError("Wrong row count "+str(path))
        frames.append(f)
    df=pd.concat(frames,ignore_index=True).sort_values("time").reset_index(drop=True)
    t=df.time.to_numpy(dtype=np.int64)
    if np.any(np.diff(t)!=60):
        raise RuntimeError("Unexpected missing or duplicate 1-minute timestamp "+symbol)
    for c in ("open","high","low","close"):
        if not np.isfinite(df[c].to_numpy(dtype=float)).all():
            raise RuntimeError("Nonfinite "+symbol+" "+c)
    if ((df.low<=0)|(df.high<df.low)|(df.open<df.low)|(df.open>df.high)|
        (df.close<df.low)|(df.close>df.high)).any():
        raise RuntimeError("Bad candle "+symbol)
    df.index=pd.to_datetime(df.time,unit="s",utc=True)
    df=df.loc[df.index<CUTOFF].copy()
    return df, {"rows":len(df),"first_utc":str(df.index[0]),"last_utc":str(df.index[-1]),
                "partitions_sha256_verified":len(parts),"missing_minutes":0}

def features(df,tf):
    agg=df.resample(f"{tf}min",label="left",closed="left").agg(
        {"open":"first","high":"max","low":"min","close":"last","volume":"sum"})
    counts=df.close.resample(f"{tf}min",label="left",closed="left").count()
    valid=counts.to_numpy()==tf
    h=agg.high.to_numpy(dtype=np.float64)
    l=agg.low.to_numpy(dtype=np.float64)
    c=agg.close.to_numpy(dtype=np.float64)
    prev=np.r_[c[0],c[:-1]]
    tr=np.maximum(h-l,np.maximum(np.abs(h-prev),np.abs(l-prev)))
    atr=pd.Series(tr).ewm(alpha=1/14,adjust=False,min_periods=14).mean().to_numpy()
    ema=pd.Series(c).ewm(span=20,adjust=False).mean().to_numpy()
    upper=(h+l)/2+3*atr
    lower=(h+l)/2-3*atr
    fu=np.full(len(agg),np.nan)
    fl=np.full(len(agg),np.nan)
    trend=np.zeros(len(agg),dtype=np.int8)
    first=next(i for i in range(len(agg)) if valid[i] and np.isfinite(atr[i]))
    fu[first],fl[first]=upper[first],lower[first]
    trend[first]=1 if c[first]>=((h[first]+l[first])/2) else -1
    for j in range(first+1,len(agg)):
        if not valid[j] or not np.isfinite(atr[j]):
            continue
        fu[j]=upper[j] if (upper[j]<fu[j-1] or c[j-1]>fu[j-1]) else fu[j-1]
        fl[j]=lower[j] if (lower[j]>fl[j-1] or c[j-1]<fl[j-1]) else fl[j-1]
        if trend[j-1]==1:
            trend[j]=-1 if c[j]<fl[j] else 1
        elif trend[j-1]==-1:
            trend[j]=1 if c[j]>fu[j] else -1
    return ema,atr,trend,valid

def replay(df,symbol,tf):
    ema,atr,trend,valid=features(df,tf)
    raw_o=df.open.to_numpy(dtype=np.float64)
    raw_h=df.high.to_numpy(dtype=np.float64)
    raw_l=df.low.to_numpy(dtype=np.float64)
    raw_c=df.close.to_numpy(dtype=np.float64)
    times=df.time.to_numpy(dtype=np.int64)
    # Beginning UTC is aligned to midnight and every tf boundary.
    assert times[0]% (tf*60)==0
    asset_rows=[]
    eq=1000.
    peak=eq
    max_dd=0.
    count=0
    touch_bar=-1
    active_trend=0
    position=None
    ignored=0
    for i in range(len(df)):
        bar=i//tf
        done=bar-1
        if done<100 or done>=len(ema) or not valid[done] or trend[done]==0:
            continue
        direction=int(trend[done])
        if active_trend!=direction:
            # Updated only at the next HTF bar start: flip candle itself never counts.
            active_trend=direction
            count=0
            touch_bar=-1
        o,h,l,c=raw_o[i],raw_h[i],raw_l[i],raw_c[i]
        when=int(times[i])
        if position is not None:
            p=position
            islong=p["side"]==1
            # Existing stop always checked before high/low moves trailing.
            triggered=(l<=p["stop"]) if islong else (h>=p["stop"])
            if triggered:
                exit_raw=min(o,p["stop"]) if islong else max(o,p["stop"])
                exit_fill=exit_raw*(1-SLIP if islong else 1+SLIP)
                exit_reason="stop"
            else:
                favorable=h if islong else l
                if islong:
                    p["best"]=max(p["best"],favorable)
                    gain=p["best"]-p["entry"]
                    if gain>=p["R"]:
                        p["stop"]=max(p["stop"],p["entry"])
                    if gain>=2*p["R"]:
                        p["stop"]=max(p["stop"],p["best"]-p["R"])
                else:
                    p["best"]=min(p["best"],favorable)
                    gain=p["entry"]-p["best"]
                    if gain>=p["R"]:
                        p["stop"]=min(p["stop"],p["entry"])
                    if gain>=2*p["R"]:
                        p["stop"]=min(p["stop"],p["best"]+p["R"])
                # Updated stops become executable on next one-minute candle.
                continue
            exit_pnl=p["side"]*p["qty"]*(exit_fill-p["entry"])
            fees=FEE*p["qty"]*(p["entry"]+exit_fill)
            net=exit_pnl-fees
            eq+=net
            peak=max(peak,eq)
            max_dd=max(max_dd,(peak-eq)/peak)
            asset_rows.append(dict(symbol=symbol,timeframe=f"{tf}m",
                entry_utc=pd.Timestamp(p["t"],unit="s",tz="UTC").isoformat(),
                exit_utc=pd.Timestamp(when,unit="s",tz="UTC").isoformat(),
                month_ist=pd.Timestamp(when,unit="s",tz="UTC").tz_convert("Asia/Kolkata").strftime("%Y-%m"),
                side="LONG" if islong else "SHORT",
                entry=p["entry"],exit=exit_fill,initial_r=p["R"],
                exit_reason=exit_reason,gross_usd=exit_pnl,fees_usd=fees,
                net_usd=net,net_pct_of_entry_notional=100*net/(p["qty"]*p["entry"]),
                equity_after=eq))
            position=None
            count=0
            touch_bar=-1
            continue
        level=ema[done]
        if not np.isfinite(level) or not np.isfinite(atr[done]) or atr[done]<=0:
            continue
        if touch_bar==bar:
            continue
        if not(l<=level<=h):
            continue
        count+=1
        touch_bar=bar
        if count<2:
            continue
        entry=level*(1+direction*SLIP)
        R=min(2*float(atr[done]),entry*.01)
        if R<=0:
            continue
        qty=eq/entry
        stop=entry-direction*R
        p=dict(side=direction,entry=entry,R=R,stop=stop,best=entry,t=when,qty=qty)
        position=p
        count=0
        touch_bar=-1
        # Entry can occur at an unknown instant within this 1m candle.
        # To avoid assuming favorable 1m high happened AFTER entry, do not
        # activate BE/trail on entry candle. Conservatively stop if adverse
        # range crosses newly established initial stop (path-ambiguous).
        if (direction==1 and l<=stop) or (direction==-1 and h>=stop):
            # Record the stop at this minute; then skip touch processing.
            exit_fill=stop*(1-direction*SLIP)
            gross=direction*qty*(exit_fill-entry)
            fees=FEE*qty*(entry+exit_fill)
            net=gross-fees
            eq+=net
            peak=max(peak,eq)
            max_dd=max(max_dd,(peak-eq)/peak)
            asset_rows.append(dict(symbol=symbol,timeframe=f"{tf}m",
                entry_utc=pd.Timestamp(when,unit="s",tz="UTC").isoformat(),
                exit_utc=pd.Timestamp(when,unit="s",tz="UTC").isoformat(),
                month_ist=pd.Timestamp(when,unit="s",tz="UTC").tz_convert("Asia/Kolkata").strftime("%Y-%m"),
                side="LONG" if direction==1 else "SHORT",
                entry=entry,exit=exit_fill,initial_r=R,
                exit_reason="entry_minute_stop_first",gross_usd=gross,fees_usd=fees,
                net_usd=net,net_pct_of_entry_notional=100*net/(qty*entry),
                equity_after=eq))
            position=None
    if position is not None:
        p=position
        end=float(raw_c[-1])*(1-p["side"]*SLIP)
        gross=p["side"]*p["qty"]*(end-p["entry"])
        fees=FEE*p["qty"]*(end+p["entry"])
        net=gross-fees
        eq+=net
        peak=max(peak,eq)
        max_dd=max(max_dd,(peak-eq)/peak)
        when=int(times[-1])
        asset_rows.append(dict(symbol=symbol,timeframe=f"{tf}m",
            entry_utc=pd.Timestamp(p["t"],unit="s",tz="UTC").isoformat(),
            exit_utc=pd.Timestamp(when,unit="s",tz="UTC").isoformat(),
            month_ist=pd.Timestamp(when,unit="s",tz="UTC").tz_convert("Asia/Kolkata").strftime("%Y-%m"),
            side="LONG" if p["side"]==1 else "SHORT",
            entry=p["entry"],exit=end,initial_r=p["R"],
            exit_reason="sample_end",gross_usd=gross,fees_usd=fees,
            net_usd=net,net_pct_of_entry_notional=100*net/(p["qty"]*p["entry"]),
            equity_after=eq))
    result=pd.DataFrame(asset_rows)
    monthly=[]
    m_equity=1000.
    for m in MONTHS:
        rows=result.loc[result.month_ist==m] if len(result) else result
        net=rows.net_usd.sum() if len(rows) else 0.
        end_eq=m_equity+net
        monthly.append(dict(symbol=symbol,timeframe=f"{tf}m",month_ist=m,trades=len(rows),
            winners=int((rows.net_usd>0).sum()) if len(rows) else 0,
            losers=int((rows.net_usd<0).sum()) if len(rows) else 0,
            net_usd=round(float(net),4),return_pct=round(100*float(net)/m_equity,5)))
        m_equity=end_eq
    # Independently calculate maximum drawdown on post-trade realized equity.
    curve=np.r_[1000.,result.equity_after.to_numpy()] if len(result) else np.array([1000.])
    dd=(np.maximum.accumulate(curve)-curve)/np.maximum.accumulate(curve)
    wins=result[result.net_usd>0] if len(result) else result
    losses=result[result.net_usd<0] if len(result) else result
    gp=float(wins.net_usd.sum()) if len(wins) else 0.
    gl=float(-losses.net_usd.sum()) if len(losses) else 0.
    summary=dict(symbol=symbol,timeframe=f"{tf}m",trades=len(result),
       wins=len(wins),losses=len(losses),win_rate_pct=round(100*len(wins)/max(1,len(result)),3),
       profit_factor=round(gp/gl,4) if gl>0 else None,
       gross_profit_usd=round(gp,4),gross_loss_usd=round(gl,4),
       fee_usd=round(float(result.fees_usd.sum()),4) if len(result) else 0,
       net_profit_usd=round(eq-1000,4),net_return_pct=round((eq/1000-1)*100,4),
       max_closed_trade_drawdown_pct=round(float(dd.max()*100),4),
       positive_months=sum(m["net_usd"]>0 for m in monthly),
       negative_months=sum(m["net_usd"]<0 for m in monthly),
       zero_months=sum(m["net_usd"]==0 for m in monthly),
       train_2025_return_pct=round(100*(1+sum(m["net_usd"] for m in monthly[:12])/1000-1),4),
       check_2026_net_usd=round(sum(m["net_usd"] for m in monthly[12:]),4))
    assert abs((eq-1000)-float(result.net_usd.sum()))<0.01
    return result,monthly,summary

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    ledgers=[]; rows=[]; summaries=[]; quality={}
    for symbol in ("BTCUSD","ETHUSD"):
        df,q=read_source(symbol)
        quality[symbol]=q
        for tf in (15,60):
            print("Starting",symbol,tf,flush=True)
            trades,monthly,summary=replay(df,symbol,tf)
            rows.extend(monthly)
            summaries.append(summary)
            if len(trades):ledgers.append(trades)
            print(json.dumps(summary),flush=True)
    pd.DataFrame(rows).to_csv(OUT/"monthly_results.csv",index=False)
    pd.DataFrame(summaries).to_csv(OUT/"summary.csv",index=False)
    if ledgers:pd.concat(ledgers,ignore_index=True).to_csv(OUT/"trade_ledger.csv.gz",index=False,compression="gzip")
    quality["assumptions"]=dict(fee_taker_each_side=0.0005,fee_gst_rate=0.18,
        slippage_each_side_fraction=SLIP,account_initial_usd=1000,
        notional_leverage=1,position_exclusivity="per symbol and timeframe",
        monthly_period="Asia/Kolkata, closed trades at exit",fixed_take_profit=False,
        supertrend="10-period Wilder ATR, 3x; previous fully closed HTF bar",
        touch_price="last completed signal timeframe EMA20",
        instant_touch_fill="EMA20 plus adverse 0.02% slippage; 1m OHLC approximation",
        stop_update="breakeven 1R, trailing from 2R at 1R distance; new stop effective next minute",
        disclaimer="No spreads, funding, tick-level order paths or guaranteed executable fills; entry-minute stop-first")
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2)+"\n")
    r=pd.DataFrame(summaries)
    lines=["# EMA20 second-touch intrabar backtest","",
      "Reproducible research on 1m Delta Exchange India OHLC. Not live fills.",
      "2025-01 to 2026-10 inclusive, 22 IST calendar months; January 2025 first 5h30m IST unavailable.",
      "2026 is prior-research-exposed rather than untouched holdout.","",
      "| Symbol | Entry TF | Trades | Win rate | Profit factor | Net % (1x) | Max closed-trade DD | Positive months |",
      "|---|---|---:|---:|---:|---:|---:|---:|"]
    for _,s in r.iterrows():
        lines.append(f"| {s.symbol} | {s.timeframe} | {s.trades} | {s.win_rate_pct:.2f}% | {s.profit_factor} | {s.net_return_pct:.3f}% | {s.max_closed_trade_drawdown_pct:.3f}% | {s.positive_months}/22 |")
    lines+=["","## Cost and execution caveats",
      "- Assumed 0.05% taker fee per side plus 18% GST on fees; 0.02% adverse slippage per side.",
      "- 1x evolving notional, initial 1000 USD model equity, no leverage, no funding, no actual spreads.",
      "- Last completed HTF EMA and Supertrend; touches distinct HTF candles, entry in 1m candle.",
      "- On same entry 1m candle, SL crossing is adverse-first; BE/trailing changes only effective next minute.",
      "- There is no tick tape; a 1-minute high/low cannot establish exact touch ordering or stop trigger time.",
      "- No optimization or selection against 2026. Exit-counted IST months, no-trade months included.",
      "","See summary.csv, monthly_results.csv, quality.json and trade_ledger.csv.gz."]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(lines)+"\n")
    print("BACKTEST_DONE",json.dumps(summaries),flush=True)

if __name__=="__main__":main()
