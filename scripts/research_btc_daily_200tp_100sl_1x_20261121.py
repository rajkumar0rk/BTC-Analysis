#!/usr/bin/env python3
"""Exact 1x BTCUSD one-per-IST-day, 1H EMA trend + 15M EMA pullback/breakout.

Single predeclared 200 BTC chart-point TP and 100 BTC chart-point SL.
Net account PnL uses 0.05% taker per side, 18% GST and 5-point slip each way.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd

DATA = Path("data/delta_india/BTCUSD/1m")
OUT = Path("analysis/btc_daily_200tp_100sl_1x_20261121")
TP, SL, HOLD_MIN = 200.0, 100.0, 240
LEVERAGE = 1.0
TAKER_FEE_WITH_GST = 0.0005 * 1.18
SLIP_POINTS = 5.0
INITIAL_EQUITY = 10000.0
FULL_DAY_START, FULL_DAY_END = "2025-01-02", "2026-10-30"
MODEL = "h1_ema20_50_m15_prior4_ema20_touch_previous_high_break_200tp_100sl_1x"
MONTHS = pd.period_range("2025-01","2026-10",freq="M").astype(str).tolist()

def load_1m():
    files = sorted(DATA.glob("20??-??.csv.gz"))
    if len(files) < 22:
        raise RuntimeError("Expected original Delta India BTCUSD monthly 1m archive")
    frames=[]
    for p in files:
        # Keep archive all, even recent, for an explicit latest date quality check;
        # filter out anything beyond Oct 2026 before computing signals.
        if p.stem[:7] > "2026-10":
            continue
        frame=pd.read_csv(p,compression="gzip",
            usecols=["time","open","high","low","close","volume"])
        frames.append(frame)
    f=pd.concat(frames,ignore_index=True).sort_values("time",kind="stable")
    sec=f.time.to_numpy(np.int64)
    if np.any(np.diff(sec)<=0):
        raise AssertionError("Time labels overlap or are not monotonic")
    if np.any(sec%60 != 0):
        raise AssertionError("All source bars must start on minute")
    min_delta=np.diff(sec)
    gaps=np.where(min_delta != 60)[0]
    expected_utc_end=pd.Timestamp("2026-10-31T00:00:00Z")
    f=f.loc[f.time< int(expected_utc_end.timestamp())].copy()
    sec=f.time.to_numpy(np.int64)
    for name in ("open","high","low","close","volume"):
        if not np.all(np.isfinite(f[name].to_numpy(float))):
            raise AssertionError("NaN/inf in "+name)
    if ((f.low<=0)|(f.low>f.high)|(f.open<f.low)|(f.open>f.high)|
        (f.close<f.low)|(f.close>f.high)|(f.volume<0)).any():
        raise AssertionError("Invalid OHLCV bar")
    f.index=pd.to_datetime(sec,unit="s",utc=True)
    q={"instrument":"Delta Exchange India BTCUSD perpetual",
       "files_used":[p.name for p in files if p.stem[:7]<="2026-10"],
       "native_1m_rows":len(f),"source_first_utc":str(f.index[0]),
       "source_last_utc":str(f.index[-1]),
       "missing_in_source_span_minutes":int((sec[-1]-sec[0])//60+1-len(f)),
       "gap_count":int(len(gaps)),
       "excluded_incomplete_IST_dates":["2025-01-01","2026-10-31"],
       "first_full_IST_date":FULL_DAY_START,"last_full_IST_date":FULL_DAY_END,
       "historical_quality_warning":"Oct 2026 lacks final 5.5 hours of Oct31 IST; not fully verified"}
    if len(gaps):
        q["gap_examples"]=[{"prev":str(f.index[i]),"next":str(f.index[i+1]),
                            "missing_minutes":int(min_delta[i]/60-1)} for i in gaps[:12]]
    # Our evaluation period must not silently cross missing candles.
    if f.index[-1] < pd.Timestamp("2026-10-30 18:29:00+00:00"):
        raise RuntimeError("Insufficient archive for final full IST date")
    return f,q

def signals(f):
    m15=f.resample("15min",label="left",closed="left").agg(
      open=("open","first"),high=("high","max"),low=("low","min"),
      close=("close","last"),n=("close","size"))
    h1=f.resample("1h",label="right",closed="left").agg(
      close=("close","last"),n=("close","size"))
    complete15=m15.n.eq(15)
    complete_hour=h1.n.eq(60)
    # Closed 15m EMA and closed hourly EMA; insufficient warm-up excluded.
    c15=m15.close.where(complete15)
    c1h=h1.close.where(complete_hour)
    e15=c15.ewm(span=20,min_periods=20,adjust=False).mean()
    e1h20=c1h.ewm(span=20,min_periods=50,adjust=False).mean()
    e1h50=c1h.ewm(span=50,min_periods=50,adjust=False).mean()
    valid15=complete15.rolling(25,min_periods=25).sum().eq(25)
    valid1h=complete_hour.rolling(55,min_periods=55).sum().eq(55)

    # An earlier (NOT current) 15m candle touched the 15m EMA20.
    touch_l=(complete15 & (m15.low<=e15))
    touch_s=(complete15 & (m15.high>=e15))
    prior_touch_long=touch_l.rolling(4,min_periods=4).max().shift(1).fillna(0).gt(0)
    prior_touch_short=touch_s.rolling(4,min_periods=4).max().shift(1).fillna(0).gt(0)

    # Last COMPLETED hourly bar as-of 15-minute close, never current forming hour.
    signal_end=m15.index+pd.Timedelta(minutes=15)
    hour_source=pd.DataFrame({
       "h1_close":h1.close.where(valid1h),
       "ema20":e1h20.where(valid1h),
       "ema50":e1h50.where(valid1h)})
    hour=hour_source.reindex(signal_end,method="ffill")
    hlong=(hour.h1_close.to_numpy(float)>hour.ema20.to_numpy(float))&(
      hour.ema20.to_numpy(float)>hour.ema50.to_numpy(float))
    hshort=(hour.h1_close.to_numpy(float)<hour.ema20.to_numpy(float))&(
      hour.ema20.to_numpy(float)<hour.ema50.to_numpy(float))
    prev_high=m15.high.shift(1)
    prev_low=m15.low.shift(1)
    local=signal_end.tz_convert("Asia/Kolkata")
    date_str=np.asarray(local.strftime("%Y-%m-%d"))
    eligible=(date_str>=FULL_DAY_START)&(date_str<=FULL_DAY_END)
    # For current candle breakout, a prior pullback touch within last four bars
    # must have completed. The current signal candle is required to confirm.
    slong=(valid15.to_numpy(bool) & hlong &
       prior_touch_long.to_numpy(bool) &
       (m15.close.to_numpy(float)>e15.to_numpy(float)) &
       (m15.close.to_numpy(float)>prev_high.to_numpy(float)) &
       (m15.close.to_numpy(float)>m15.open.to_numpy(float)))
    sshort=(valid15.to_numpy(bool) & hshort &
       prior_touch_short.to_numpy(bool) &
       (m15.close.to_numpy(float)<e15.to_numpy(float)) &
       (m15.close.to_numpy(float)<prev_low.to_numpy(float)) &
       (m15.close.to_numpy(float)<m15.open.to_numpy(float)))

    sec=f.time.to_numpy(np.int64)
    # DATETIME64[s], NOT DatetimeIndex.asi8 (pandas 3 can mean microseconds).
    end_sec=signal_end.to_numpy(dtype="datetime64[s]").astype(np.int64)
    m_idx=np.searchsorted(sec,end_sec,side="left")
    safe=np.minimum(m_idx,len(sec)-1)
    has_entry=(m_idx<len(sec))&(sec[safe]==end_sec)
    raw=np.flatnonzero(eligible&has_entry&(slong|sshort)&~(slong&sshort))
    events=[(int(m_idx[j]),1 if slong[j] else -1) for j in raw]
    diag={"complete15":int(complete15.sum()),"complete1h":int(complete_hour.sum()),
        "prior_touch_long_count":int(prior_touch_long.sum()),
        "prior_touch_short_count":int(prior_touch_short.sum()),
        "confirmed_h1_long_count":int(hlong.sum()),
        "confirmed_h1_short_count":int(hshort.sum()),
        "long_entry_signals":int(slong.sum()),
        "short_entry_signals":int(sshort.sum()),
        "eligible_1m_entries":len(events),
        "entry_minute_alignment_matches":int(has_entry.sum()),
        "sample_signal":str(signal_end[raw[0]]) if len(raw) else None}
    if not events: raise AssertionError("No events; inspect time alignment and entries")
    return events,diag

def replay(f,events):
    op=f.open.to_numpy(float);hi=f.high.to_numpy(float)
    lo=f.low.to_numpy(float);cl=f.close.to_numpy(float)
    ix=f.index.tz_convert("Asia/Kolkata")
    date=np.asarray(ix.strftime("%Y-%m-%d"))
    equity=INITIAL_EQUITY
    last_exit_idx=-1
    booked=set()
    rows=[]
    for k,side in events:
        day=str(date[k])
        if day in booked or k <= last_exit_idx:
            continue
        booked.add(day)
        if not(FULL_DAY_START<=day<=FULL_DAY_END):
            raise AssertionError("Incomplete day entry")
        p=float(op[k])
        entry_fill=p + side*SLIP_POINTS
        target=p+side*TP
        stop=p-side*SL
        qty=LEVERAGE*equity/p
        if qty<=0: raise RuntimeError("No positive equity to enter trade")
        # There is a single first trade per day; no carry to next IST day.
        next_day_idx=np.searchsorted(date,day,side="right")
        final=min(k+HOLD_MIN-1, next_day_idx-1, len(f)-1)
        if final<k: raise AssertionError("Malformed date boundary")
        exit_chart=float(cl[final])
        exit_idx=int(final)
        reason="time_limit" if final ==k+HOLD_MIN-1 else "day_end"
        for j in range(k,final+1):
            stop_hit=(lo[j]<=stop) if side>0 else (hi[j]>=stop)
            target_hit=(hi[j]>=target) if side>0 else (lo[j]<=target)
            if stop_hit:
                # Conservative stop-first if both trigger in a 1m OHLC bar.
                # If gap through stop, fill at the worse minute OPEN.
                exit_chart=float(min(stop,op[j]) if side>0 else max(stop,op[j]))
                reason="stop"
                exit_idx=j
                break
            if target_hit:
                # No optimistic better-than-target fills on favorable jumps.
                exit_chart=float(target)
                reason="target"
                exit_idx=j
                break
        if date[exit_idx] != day: raise AssertionError("Held across IST midnight")
        exit_fill=exit_chart - side*SLIP_POINTS
        chart_points=side*(exit_chart-p)
        execution_points=side*(exit_fill-entry_fill)
        if abs(execution_points-(chart_points-2*SLIP_POINTS))>1e-7:
            raise AssertionError("Slippage accounting changed")
        gross_usd=qty*chart_points
        slip_usd=qty*2*SLIP_POINTS
        fee_usd=qty*TAKER_FEE_WITH_GST*(entry_fill+exit_fill)
        net_usd=gross_usd-slip_usd-fee_usd
        equity_before=equity
        equity+=net_usd
        if equity<=0: raise RuntimeError("Account equity depleted")
        if reason=="target" and abs(chart_points-TP)>1e-6:raise AssertionError("TP")
        if reason=="stop" and chart_points>-SL+1e-6:raise AssertionError("SL")
        rows.append({"day_ist":day,"month_ist":day[:7],
            "entry_ist":str(ix[k]),"exit_ist":str(ix[exit_idx]),
            "direction":"LONG" if side>0 else "SHORT","exit_reason":reason,
            "entry_chart_usd":p,"entry_filled_usd":entry_fill,
            "take_profit_chart_usd":target,"stop_loss_chart_usd":stop,
            "exit_chart_usd":exit_chart,"exit_filled_usd":exit_fill,
            "holding_minutes":int(exit_idx-k+1),"btc_equivalent_qty":qty,
            "gross_btc_price_points":chart_points,
            "after_slippage_points_before_fee":execution_points,
            "gross_usd":gross_usd,"slippage_usd":slip_usd,"fee_gst_usd":fee_usd,
            "net_usd":net_usd,"account_return_pct":100*net_usd/equity_before,
            "equity_before_usd":equity_before,"equity_after_usd":equity})
        last_exit_idx=exit_idx
    result=pd.DataFrame(rows)
    if not len(result):
        raise AssertionError("No trades despite qualifying setup events")
    if result.day_ist.duplicated().any():
        raise AssertionError("More than one trade in an IST date")
    if abs(result.net_usd.sum()-(equity-INITIAL_EQUITY))>1e-6:
        raise AssertionError("Cash PnL does not reconcile")
    return result

def summarize(trades,quality,diag):
    days=pd.date_range(FULL_DAY_START,FULL_DAY_END,freq="D",tz="Asia/Kolkata")
    daily=pd.DataFrame({"date_ist":days.strftime("%Y-%m-%d")})
    daily["month_ist"]=daily.date_ist.str[:7]
    trade_idx=trades.set_index("day_ist")
    daily["account_return_pct"]=daily.date_ist.map(trade_idx.account_return_pct).fillna(0.)
    daily["exit_reason"]=daily.date_ist.map(trade_idx.exit_reason).fillna("no_trade")
    daily["net_usd"]=daily.date_ist.map(trade_idx.net_usd).fillna(0.)
    daily["outcome"]=np.where(daily.exit_reason=="no_trade","no_trade",
       np.where(daily.account_return_pct>0,"net_profit",
       np.where(daily.account_return_pct<0,"net_loss","net_flat")))
    monthly=daily.groupby("month_ist",sort=True).agg(
       days=("date_ist","size"),
       entries=("exit_reason",lambda v:int((v!="no_trade").sum())),
       tp_hit_first=("exit_reason",lambda v:int((v=="target").sum())),
       sl_hit_first=("exit_reason",lambda v:int((v=="stop").sum())),
       time_or_day_exit=("exit_reason",lambda v:int(((v=="time_limit")|(v=="day_end")).sum())),
       winning_days=("outcome",lambda v:int((v=="net_profit").sum())),
       losing_days=("outcome",lambda v:int((v=="net_loss").sum())),
       no_trade_days=("outcome",lambda v:int((v=="no_trade").sum())),
       compounded_net_account_pct=("account_return_pct",
          lambda v:float((np.prod(1+v.to_numpy(float)/100)-1)*100)),
       sum_of_daily_net_usd=("net_usd","sum")).reset_index()
    monthly["archive_boundary_incomplete"]=monthly.month_ist.isin(["2025-01","2026-10"])
    equity_path=np.r_[INITIAL_EQUITY,trades.equity_after_usd.to_numpy(float)]
    maxdrawdown=float((1-equity_path/np.maximum.accumulate(equity_path)).max()*100)
    n=len(trades)
    win=trades.net_usd>0
    loss=trades.net_usd<0
    grossprofit=float(trades.loc[win,"net_usd"].sum())
    grossloss=float(-trades.loc[loss,"net_usd"].sum())
    summary={
       "strategy":MODEL,"data_quality":quality,"entry_diagnostics":diag,
       "execution":{"leverage":1,"raw_chart_tp_points":TP,"raw_chart_sl_points":SL,
           "max_holding_minutes":HOLD_MIN,"max_entries_per_IST_day":1,
           "fee_taker_one_side":.0005,"GST_on_fee":.18,
           "adverse_slippage_BTC_points_one_side":SLIP_POINTS,
           "unmodeled":["true spread","impact","funding","margin liquidation",
             "lot size and exchange minimums"]},
       "trades":n,"longs":int((trades.direction=="LONG").sum()),
       "shorts":int((trades.direction=="SHORT").sum()),
       "tp_before_sl_count":int((trades.exit_reason=="target").sum()),
       "sl_before_tp_count":int((trades.exit_reason=="stop").sum()),
       "time_or_day_exit_count":int(trades.exit_reason.isin(["time_limit","day_end"]).sum()),
       "tp_first_pct_of_trades":round(100*(trades.exit_reason=="target").mean(),4),
       "net_win_trades":int(win.sum()),"net_loss_trades":int(loss.sum()),
       "net_trade_win_rate_pct":round(100*win.mean(),4),
       "days_in_sample":len(daily),
       "net_profitable_days":int((daily.outcome=="net_profit").sum()),
       "net_losing_days":int((daily.outcome=="net_loss").sum()),
       "no_trade_days":int((daily.outcome=="no_trade").sum()),
       "tp_days_pct_all_calendar":round(100*(trades.exit_reason=="target").sum()/len(daily),4),
       "positive_months":int((monthly.compounded_net_account_pct>1e-8).sum()),
       "negative_months":int((monthly.compounded_net_account_pct< -1e-8).sum()),
       "flat_months":int((np.abs(monthly.compounded_net_account_pct)<=1e-8).sum()),
       "capital_start_usd":INITIAL_EQUITY,
       "capital_end_usd":round(float(trades.equity_after_usd.iloc[-1]),2),
       "full_period_compounded_net_account_pct":round(100*(float(trades.equity_after_usd.iloc[-1])/INITIAL_EQUITY-1),5),
       "mean_after_fee_BTC_price_points":round(float((trades.net_usd/trades.btc_equivalent_qty).mean()),4),
       "mean_gross_BTC_price_points":round(float(trades.gross_btc_price_points.mean()),4),
       "total_gross_usd":round(float(trades.gross_usd.sum()),2),
       "total_fee_gst_usd":round(float(trades.fee_gst_usd.sum()),2),
       "total_slippage_usd":round(float(trades.slippage_usd.sum()),2),
       "total_net_usd":round(float(trades.net_usd.sum()),2),
       "net_profit_factor":round(grossprofit/grossloss,4) if grossloss>0 else None,
       "trade_close_max_drawdown_pct":round(maxdrawdown,4),
       "2025_net_compounded_pct":round(100*(np.prod(1+daily.loc[daily.month_ist.str.startswith("2025"),"account_return_pct"]/100)-1),5),
       "2026_JanOct_net_compounded_pct":round(100*(np.prod(1+daily.loc[daily.month_ist.str.startswith("2026"),"account_return_pct"]/100)-1),5),
       "research_warning":"2026 previously researched in BTC-Analysis; this is NOT an untouched holdout",
       "conclusion_warning":"A 200-point daily profit target is not a daily profit guarantee"}
    # Independent consistency: compounding the daily or monthly return equals final NAV.
    reconstructed=float(np.prod(1+daily.account_return_pct.to_numpy(float)/100))
    reconstructed_m=float(np.prod(1+monthly.compounded_net_account_pct.to_numpy(float)/100))
    equity_ratio=trades.equity_after_usd.iloc[-1]/INITIAL_EQUITY
    if abs(reconstructed-equity_ratio)>1e-8 or abs(reconstructed_m-equity_ratio)>1e-8:
        raise AssertionError("Daily/monthly account return compounding inconsistent")
    if not (monthly.days.sum()==len(daily) and monthly.entries.sum()==len(trades)):
        raise AssertionError("Daily/monthly trade coverage")
    return daily,monthly,summary

def main():
    OUT.mkdir(exist_ok=True,parents=True)
    f,q=load_1m()
    events,diag=signals(f)
    trades=replay(f,events)
    daily,monthly,summary=summarize(trades,q,diag)
    trades.to_csv(OUT/"trades.csv",index=False)
    daily.to_csv(OUT/"daily.csv",index=False)
    monthly.to_csv(OUT/"monthly.csv",index=False)
    (OUT/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    report=[
      "# BTCUSD 1× 15M pullback breakout — fixed 200-point TP, 100-point SL",
      "",
      "## Exact methodology",
      "",
      "- Native Delta India BTCUSD 1m OHLCV. Use last **closed 1H** EMA20 > EMA50 and 1H close > EMA20 for long; reverse for short.",
      "- Prior four 15m completed candles must touch the 15m EMA20. Signal's **closed 15m** candle must break previous 15m high/low, close beyond its EMA20, and have confirming bullish/bearish body.",
      "- Enter next 1m OPEN. First qualifying IST-day entry, at most one trade, 7 days/week. No other indicators or session filters.",
      "- Target +200 BTC chart-price points, stop −100 BTC chart-price points from 1m raw entry OPEN; if both touched in one 1m bar, stop wins.",
      "- Four-hour time exit or flat by IST midnight. 1× equity notional. $10,000 hypothetical initial account, notional re-sized on realized equity.",
      "- Taker 0.05% per side + 18% GST on fees, $5 BTC-points adverse slippage per side. Funding, true spread/impact, contract-lot constraints missing.",
      "- Full IST days 2025-01-02 through 2026-10-30. January 2025 and October 2026 incomplete archive-edge months. 2026 previously seen, not blind OOS.",
      "",
      "## Summary",
      "",
      pd.DataFrame([ {k:v for k,v in summary.items() if k not in ('data_quality','entry_diagnostics','execution') and not isinstance(v,(dict,list))}]).T.to_markdown(),
      "",
      "## Monthly results (NET after modeled trading costs)",
      "",
      monthly.to_markdown(index=False),
      "",
      "## Data integrity",
      "",
      "Source: "+str(q["native_1m_rows"])+" 1m bars; "+str(q["missing_in_source_span_minutes"])+" missing within sampled UTC span; last candle "+q["source_last_utc"],
      "",
      "## Interpretation",
      "",
      "- TP/SL levels are **raw chart points**, not net price points or account-return percentages. Even a +200 chart-point win earns fewer than +200 net BTC points after costs.",
      "- Incomplete calendar boundary dates excluded; not a fully verified 22 complete-month history.",
      "- Zero-trade days are included when measuring the goal of capturing 200 every day.",
      "- No strategy threshold was adjusted after seeing results; potential live deployment still requires additional independent forward testing."
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("SIGNAL_DIAGNOSTICS "+json.dumps(diag))
    print("BACKTEST_RESULT "+json.dumps({k:v for k,v in summary.items() if k not in ("execution","data_quality","entry_diagnostics")}))
    print("MONTHLY_RESULT\n"+monthly.to_string(index=False))

if __name__=="__main__": main()
