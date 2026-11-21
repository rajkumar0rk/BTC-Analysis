#!/usr/bin/env python3
"""One-entry-per-IST-day BTCUSD futures scalp for +1% NET account target.

Predeclared two 15m families, independent and combined chronological-first.
Historical 2026 was already exposed; this is NOT pristine forward validation.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd

BASE=Path("data/delta_india/BTCUSD/1m")
OUT=Path("analysis/daily_1pct_scalp_20261121")
FEE=0.0005*1.18
SLIP=5.
LEVERAGE=2.
NET_TP=.01
NET_SL=-.01
MAX_HOLD=240
INITIAL_EQUITY=10000.
MONTHS=pd.period_range("2025-01","2026-10",freq="M").astype(str).tolist()

def read_data():
    files=sorted(BASE.glob("20??-??.csv.gz"))
    if len(files)<22: raise ValueError("Expected 22+ archive files")
    pieces=[pd.read_csv(p,compression="gzip",
        usecols=["time","open","high","low","close","volume"]) for p in files]
    f=pd.concat(pieces,ignore_index=True).sort_values("time",kind="stable")
    t=f.time.to_numpy(np.int64)
    if np.any(np.diff(t)<=0) or np.any(np.diff(t)%60):
        raise ValueError("Non-monotonic/duplicate/minute-off data")
    gaps=np.flatnonzero(np.diff(t)!=60)+1
    for c in ("open","high","low","close","volume"):
        if not np.isfinite(f[c].to_numpy(float)).all(): raise ValueError("Nonfinite "+c)
    if ((f.low<=0)|(f.low>f.high)|(f.open<f.low)|(f.close<f.low)|
        (f.open>f.high)|(f.close>f.high)|(f.volume<0)).any():
        raise ValueError("OHLCV invalid")
    f.index=pd.to_datetime(t,unit="s",utc=True)
    quality={"rows":len(f),"files":[p.name for p in files],
        "first_utc":str(f.index[0]),"last_utc":str(f.index[-1]),
        "missing_utc_minutes":int((t[-1]-t[0])//60+1-len(f)),
        "gaps":[{"before":str(f.index[i-1]),"after":str(f.index[i]),
                 "minutes":int((t[i]-t[i-1])//60-1)} for i in gaps],
        "candle_label_assumption":"UTC minute START as used in repository"}
    return f,quality

def features(f):
    b15=f.resample("15min",label="left",closed="left").agg(
        open=("open","first"),high=("high","max"),low=("low","min"),
        close=("close","last"),volume=("volume","sum"),n=("close","size"))
    b1h=f.resample("1h",label="right",closed="left").agg(
        close=("close","last"),n=("close","size"))
    v15=b15.n.eq(15)
    v1h=b1h.n.eq(60)
    # Every candle in lookback must exist and be complete.
    valid_15=v15.rolling(21,min_periods=21).sum().eq(21)
    valid_1h=v1h.rolling(55,min_periods=55).sum().eq(55)
    h_close=b1h.close.where(v1h)
    ema20=h_close.ewm(span=20,adjust=False,min_periods=50).mean()
    ema50=h_close.ewm(span=50,adjust=False,min_periods=50).mean()
    hour_end=b15.index+pd.Timedelta(minutes=15)
    hour=pd.DataFrame({"e20":ema20.where(valid_1h),
                       "e50":ema50.where(valid_1h)})
    aligned=hour.reindex(hour_end,method="ffill")
    trend_up=(aligned.e20.to_numpy(float)>aligned.e50.to_numpy(float))
    trend_down=(aligned.e20.to_numpy(float)<aligned.e50.to_numpy(float))
    spread=np.abs(aligned.e20.to_numpy(float)-aligned.e50.to_numpy(float))
    flat=spread/b15.close.to_numpy(float)<.01
    d=b15.close.diff()
    gain=d.clip(lower=0).ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    loss=(-d.clip(upper=0)).ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    rsi=100-100/(1+gain/loss.replace(0,np.nan))
    rsi=rsi.where(~((loss==0)&(gain>0)),100)
    rsi=rsi.where(~((gain==0)&(loss>0)),0)
    avgvol=b15.volume.rolling(20,min_periods=20).mean().shift(1)
    hi8=b15.high.rolling(8,min_periods=8).max().shift(1)
    lo8=b15.low.rolling(8,min_periods=8).min().shift(1)
    hi12=b15.high.rolling(12,min_periods=12).max().shift(1)
    lo12=b15.low.rolling(12,min_periods=12).min().shift(1)
    rng=(b15.high-b15.low)
    pos=(b15.close-b15.low)/rng.replace(0,np.nan)
    valid=valid_15.to_numpy(bool) & np.isfinite(spread)
    vol=b15.volume.to_numpy(float)
    volref=avgvol.to_numpy(float)
    close=b15.close.to_numpy(float)
    op=b15.open.to_numpy(float)
    hi=b15.high.to_numpy(float)
    lo=b15.low.to_numpy(float)
    rs=rsi.to_numpy(float)
    vu=vol >= 1.25*volref
    # Momentum continuation only when breakout closes strong with volume.
    trend_long=(valid &trend_up &vu &(rs>58)&
        (close>hi8.to_numpy(float))&(pos.to_numpy(float)>=.75))
    trend_short=(valid &trend_down&vu &(rs<42)&
        (close<lo8.to_numpy(float))&(pos.to_numpy(float)<=.25))
    # Liquidity swept, then rejected; RSI stretch and 15m closing reversal.
    sweep_long=(valid&flat&(vol>=volref)&(lo<lo12.to_numpy(float))&
        (close>lo12.to_numpy(float))&(close>op)&(rs<38))
    sweep_short=(valid&flat&(vol>=volref)&(hi>hi12.to_numpy(float))&
        (close<hi12.to_numpy(float))&(close<op)&(rs>62))

    # UTC 15m bar ending at HH:15:00 can enter at HH:15 1m OPEN.
    local=hour_end.tz_convert("Asia/Kolkata")
    session=(local.hour>=12)&(local.hour<19)
    valid_day=np.asarray(local.strftime("%Y-%m").isin(MONTHS),bool)
    t=f.time.to_numpy(np.int64)
    # Pandas 3 may store DatetimeIndex internally in microseconds; .asi8/1e9 is NOT portable.
    # Explicit datetime64[s] conversion preserves UTC epoch second labels.
    end_seconds=hour_end.to_numpy(dtype="datetime64[s]").astype(np.int64)
    k=np.searchsorted(t,end_seconds,side="left")
    k_safe=np.minimum(k,len(t)-1)
    present=(k<len(t))&(t[k_safe]==end_seconds)
    eligible=np.asarray(session,bool)&valid_day&present
    longmask={"trend":trend_long,"sweep":sweep_long}
    shortmask={"trend":trend_short,"sweep":sweep_short}
    # Correctness diagnostics: assert non-degenerate time and signal alignment.
    print("SIGNAL_DIAGNOSTIC",json.dumps({
        "minute_rows":len(f),"fifteen_bars":len(b15),
        "valid_15m":int(valid.sum()),"complete_hours":int(v1h.sum()),
        "finite_hour_spread":int(np.isfinite(spread).sum()),
        "hour_trend_up":int(trend_up.sum()),"hour_trend_down":int(trend_down.sum()),
        "session_eligible":int(eligible.sum()),
        "next_open_matches":int(present.sum()),
        "vol_ge_1p25":int(vu.sum()),
        "trend_long_unrestricted":int(trend_long.sum()),
        "trend_short_unrestricted":int(trend_short.sum()),
        "sweep_long_unrestricted":int(sweep_long.sum()),
        "sweep_short_unrestricted":int(sweep_short.sum()),
        "trend_session_signals":int((eligible&(trend_long|trend_short)).sum()),
        "sweep_session_signals":int((eligible&(sweep_long|sweep_short)).sum()),
        "first_15m":str(b15.index[0]),"first_hour":str(b1h.index[0]),
        "sample_hour_e20":float(aligned.e20.dropna().iloc[0]) if aligned.e20.notna().any() else None,
        "sample_first_close":float(b15.close.iloc[0])
    }))
    models={}
    for name in ("trend","sweep","combined"):
        if name=="combined":
            ml=trend_long|sweep_long
            ms=trend_short|sweep_short
        else:
            ml=longmask[name];ms=shortmask[name]
        selected=np.flatnonzero(eligible&(ml|ms))
        rows=[]
        for ix in selected:
            # All conflicting signals: trend preferred; any same-mode dual
            # direction conflict is removed (cannot know which is true).
            if ml[ix] and ms[ix]:continue
            side=1 if ml[ix] else -1
            chosen_kind=("trend" if trend_long[ix] or trend_short[ix] else "sweep")
            rows.append((int(k[ix]),int(side),str(chosen_kind)))
        models[name]=rows
    return models

def price_for_net(entry,qty,net_dollars,side):
    desired=net_dollars/qty
    if side==1:
        return (desired+(1+FEE)*entry+2*SLIP)/(1-FEE)
    return ((1-FEE)*entry-2*SLIP-desired)/(1+FEE)

def run_model(f,models,which):
    op=f.open.to_numpy(float); hi=f.high.to_numpy(float)
    lo=f.low.to_numpy(float); cl=f.close.to_numpy(float)
    t=f.time.to_numpy(np.int64)
    ix=f.index.tz_convert("Asia/Kolkata")
    dayid=ix.year.to_numpy()*10000+ix.month.to_numpy()*100+ix.day.to_numpy()
    ymd=ix.strftime("%Y-%m-%d").to_numpy()
    booked_day=set()
    equity=INITIAL_EQUITY
    ledger=[]
    last_exit=-1
    for k,side,kind in models[which]:
        day=str(ymd[k])
        if k<=last_exit or day in booked_day:continue
        booked_day.add(day)
        start_equity=equity
        p=float(op[k])
        qty=LEVERAGE*equity/p
        target=price_for_net(p,qty,NET_TP*equity,side)
        stop=price_for_net(p,qty,NET_SL*equity,side)
        if not (stop<p<target) if side==1 else not (target<p<stop):
            raise ValueError("Fee-aware stop and target not ordered")
        # Stop checks until max hold or last minute before IST date rolls.
        nxt=np.searchsorted(dayid,dayid[k]+1,side="left")
        end=min(k+MAX_HOLD-1,nxt-1,len(f)-1)
        reason="timeout"
        exit_price=float(cl[end]);last=end
        for j in range(k,end+1):
            stop_hit=(lo[j]<=stop) if side==1 else (hi[j]>=stop)
            tp_hit=(hi[j]>=target) if side==1 else (lo[j]<=target)
            if stop_hit:
                exit_price=min(op[j],stop) if side==1 else max(op[j],stop)
                last=j;reason="stop"
                break
            if tp_hit:
                exit_price=target
                last=j;reason="target"
                break
        # Same-bar stop takes precedence. No ambiguous intra-bar favorable fill.
        entryfill=p+side*SLIP
        exitfill=exit_price-side*SLIP
        fee_dollars=FEE*qty*(entryfill+exitfill)
        gross=side*qty*(exit_price-p)
        slip_dollars=2*SLIP*qty
        net=gross-fee_dollars-slip_dollars
        equity+=net
        if equity<=0:raise RuntimeError("Account depleted; cannot size subsequent trades")
        pnl_pct=100*net/start_equity
        if reason=="target" and abs(pnl_pct-1.)>1e-6:
            raise AssertionError("Target doesn't net 1%: "+str(pnl_pct))
        if reason=="stop" and pnl_pct>-.9999:
            raise AssertionError("Stop doesn't lose 1%: "+str(pnl_pct))
        ledger.append({"model":which,"setup":kind,"entry_ist":str(ix[k]),
          "exit_ist":str(ix[last]),"day_ist":day,"month_ist":day[:7],
          "side":"LONG" if side==1 else "SHORT","entry_btc":p,
          "exit_btc_mid":exit_price,"target_btc":target,"stop_btc":stop,
          "holding_minutes":int(last-k+1),"exit_reason":reason,
          "equity_before_usd":start_equity,"equity_after_usd":equity,
          "quantity_btc_equiv":qty,"gross_usd":gross,"fee_gst_usd":fee_dollars,
          "slippage_usd":slip_dollars,"net_usd":net,"net_account_pct":pnl_pct})
        last_exit=last
    return pd.DataFrame(ledger)

def audit(trades,which,quality):
    start=pd.Timestamp("2025-01-01",tz="Asia/Kolkata")
    end=pd.Timestamp("2026-10-31",tz="Asia/Kolkata")
    all_days=pd.date_range(start,end,freq="D")
    daily=pd.DataFrame({"day_ist":all_days.strftime("%Y-%m-%d")})
    if len(trades):
        value=trades.set_index("day_ist")["net_account_pct"]
        if value.index.duplicated().any():raise AssertionError("More than 1 trade per day")
        daily["return_pct"]=daily.day_ist.map(value).fillna(0.).to_numpy(float)
        # Equity account return is measured at each trade close; no carry across days.
    else:
        daily["return_pct"]=0.
    daily["month_ist"]=daily.day_ist.str[:7]
    daily["state"]=np.where(daily.return_pct>1e-8,"profit",
        np.where(daily.return_pct< -1e-8,"loss","no_trade_or_flat"))
    grouped=daily.groupby("month_ist").agg(
       calendar_days=("day_ist","size"),
       winning_days=("state",lambda x:int((x=="profit").sum())),
       losing_days=("state",lambda x:int((x=="loss").sum())),
       no_trade_or_flat_days=("state",lambda x:int((x=="no_trade_or_flat").sum())),
       target_1pct_days=("return_pct",lambda x:int((np.abs(x-1.)<1e-6).sum())),
       monthly_return_pct=("return_pct",lambda x:float(100*(np.prod(1+x.to_numpy(float)/100)-1)))
    ).reset_index()
    grouped["trades"]=grouped.winning_days+grouped.losing_days
    # actual trades classified by exit reason, not only net result.
    eq=np.r_[INITIAL_EQUITY,trades.equity_after_usd.to_numpy(float)] if len(trades) else np.array([INITIAL_EQUITY])
    maxdd=100*np.max(1-eq/np.maximum.accumulate(eq))
    values=trades.net_usd.to_numpy(float) if len(trades) else np.array([],float)
    gross_wins=values[values>0].sum()
    gross_losses=-values[values<0].sum()
    metrics={
       "model":which,"data_quality":quality,"capital_start_usd":INITIAL_EQUITY,
       "capital_end_usd":round(float(eq[-1]),2),
       "net_compounded_return_pct":round(100*(float(eq[-1])/INITIAL_EQUITY-1),5),
       "max_trade_close_drawdown_pct":round(float(maxdd),4),
       "trades":len(trades),
       "profitable_trades":int((values>0).sum()),
       "losing_or_flat_trades":int((values<=0).sum()),
       "profit_factor_usd":round(float(gross_wins/gross_losses),4) if gross_losses else None,
       "days_in_sample":len(daily),
       "positive_days":int((daily.state=="profit").sum()),
       "negative_days":int((daily.state=="loss").sum()),
       "no_trade_or_flat_days":int((daily.state=="no_trade_or_flat").sum()),
       "days_net_1pct_target_reached":int((trades.exit_reason=="target").sum()) if len(trades) else 0,
       "daily_target_hit_pct_all_days":round(100*(trades.exit_reason=="target").sum()/len(daily),3) if len(trades) else 0,
       "months_positive":int((grouped.monthly_return_pct>1e-8).sum()),
       "months_negative":int((grouped.monthly_return_pct< -1e-8).sum()),
       "months_zero":int((np.abs(grouped.monthly_return_pct)<=1e-8).sum()),
       "model_gross_usd":round(float(trades.gross_usd.sum()),2) if len(trades) else 0,
       "total_fee_gst_usd":round(float(trades.fee_gst_usd.sum()),2) if len(trades) else 0,
       "total_slippage_usd":round(float(trades.slippage_usd.sum()),2) if len(trades) else 0,
       "year2025_return_pct":round(100*(np.prod(1+daily.loc[daily.month_ist.str.startswith("2025"),"return_pct"]/100)-1),4),
       "year2026_JanOct_return_pct":round(100*(np.prod(1+daily.loc[daily.month_ist.str.startswith("2026"),"return_pct"]/100)-1),4),
       "constraints":["2x exposure relative to running account equity",
          "stop and target EXACT net equity percent after 0.05% taker per side +18% GST and 5 USD/side slippage",
          "one entry maximum per IST day (12:00–18:59 IST), 4h expiry, flat before day end",
          "15-minute signal after complete 15m close, 1h trend after complete hour",
          "1-minute stop-first exits; stop gaps worse than price levels",
          "No quote spread, actual funding, exchange lot constraints or mark-price liquidations",
          "All 2025 and 2026 data already researched; NOT independent holdout"]
    }
    return daily,grouped,metrics

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    f,q=read_data()
    models=features(f)
    all_metrics=[]
    all_month=[]
    all_daily=[]
    all_trades=[]
    for name in ("trend","sweep","combined"):
        ledger=run_model(f,models,name)
        daily,monthly,metrics=audit(ledger,name,q)
        ledger.to_csv(OUT/f"{name}_trades.csv",index=False)
        daily.to_csv(OUT/f"{name}_daily.csv",index=False)
        monthly.insert(0,"model",name)
        all_month.append(monthly)
        all_metrics.append({k:v for k,v in metrics.items() if k not in ("data_quality","constraints")})
        all_trades.append(ledger)
    monthly=pd.concat(all_month,ignore_index=True)
    summary={"models":all_metrics,"source":q,
        "limitations":[
            "The goal is 1% net account profit on qualifying days, NOT guaranteed daily income",
            "At most one trade each IST day; no-trade days are failures of daily-profit goal",
            "5 USD/side slippage is assumed, not actual bid/ask prices; funding unmodeled",
            "Original 1m source label convention must be independently verified on live Delta candles",
            "Both years were already studied on earlier research, so 2026 is not untouched validation",
            "No forward trading recommendation until paper audit and independent data are positive"]}
    monthly.to_csv(OUT/"monthly_results.csv",index=False)
    (OUT/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    report=["# BTC daily 1% NET ACCOUNT scalp (research; not a guaranteed daily return)","",
      "## Predeclared settings","",
      "- BTCUSD Delta India 1m authentic candles; 15m triggers and completed 1h EMA confirmation.",
      "- 2x notional leverage at each entry; one trade per IST day; 12:00-18:59 IST.",
      "- Stop exactly -1% account NAV and TP exactly +1% account NAV after 0.05% taker/side, 18% GST and 5 USD/side slippage.",
      "- 4h maximum hold or before day boundary, 1m stop-first OHLC execution.","",
      "## Summary per fixed setup","",
      pd.DataFrame(all_metrics).to_markdown(index=False),"",
      "## Every complete IST month","",
      monthly[["model","month_ist","trades","target_1pct_days","winning_days","losing_days","no_trade_or_flat_days","monthly_return_pct"]].to_markdown(index=False),"",
      "## Limitations",""]
    report+=["- "+i for i in summary["limitations"]]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("DAILY_1PCT_SCALP_COMPLETE "+json.dumps(all_metrics))
    print("MONTHLY_RESULTS")
    print(monthly.to_string(index=False))

if __name__=="__main__": main()
