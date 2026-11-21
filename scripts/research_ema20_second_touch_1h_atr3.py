#!/usr/bin/env python3
"""Second-touch EMA20 1H with ONE entry per Supertrend epoch and 3x hourly ATR trailing EXIT.
Research-only, Delta India actual 1m OHLC with hash-checked partitions. No future HTF candle leaks.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from research_ema20_second_touch import read_source, features, MONTHS, FEE, SLIP

OUT=Path("analysis/ema20_second_touch_1h_atr3_20261121")
TF=60
MULT=3.0
INITIAL=1000.

def iso(sec):
    return pd.Timestamp(int(sec),unit="s",tz="UTC").isoformat()

def replay(df, symbol):
    ema, atr, st, complete=features(df,TF)
    times=df.time.to_numpy(dtype=np.int64)
    o=df.open.to_numpy(dtype=float)
    h=df.high.to_numpy(dtype=float)
    l=df.low.to_numpy(dtype=float)
    c=df.close.to_numpy(dtype=float)
    assert times[0]%(TF*60)==0
    assert len(ema)==len(atr)==len(st)
    assert len(c)==len(times)

    monthends={}
    for month in MONTHS:
        p=pd.Period(month,freq="M")
        end=(p+1).start_time.tz_localize("Asia/Kolkata").tz_convert("UTC")-pd.Timedelta(minutes=1)
        ix=int(np.searchsorted(times,int(end.timestamp()),side="right")-1)
        if ix<0 or int(times[ix])!=int(end.timestamp()):
            raise AssertionError("Monthly end minute missing: "+month)
        monthends[ix]=month

    equity=INITIAL
    position=None
    count=0
    last_touch_bar=-1
    last_direction=0
    epoch_id=0
    epoch_traded=False
    epoch_used=set()
    trades=[]
    monthly=[]
    peak=INITIAL
    worst_equity=INITIAL
    max_mtm_dd=0.
    first_zero=None
    touch_events=0
    sample_end_open=False

    for i in range(len(df)):
        b=i//TF
        done=b-1
        if done<100 or done>=len(ema) or not complete[done] or st[done]==0:
            continue

        trend=int(st[done])
        atr_dist=MULT*float(atr[done])
        if not np.isfinite(atr_dist) or atr_dist<=0:
            raise AssertionError("ATR invalid after 100 completed hours")

        if trend!=last_direction:
            # A Supertrend flip is only observable at the start of next 1H candle.
            epoch_id+=1
            last_direction=trend
            count=0
            last_touch_bar=-1
            epoch_traded=False

        now=int(times[i])
        o1,h1,l1,c1=float(o[i]),float(h[i]),float(l[i]),float(c[i])
        if position is not None:
            p=position
            side=p["side"]
            stop=p["trail"]
            if (side==1 and l1<=stop) or (side==-1 and h1>=stop):
                raw=min(o1,stop) if side==1 else max(o1,stop)
                fill=raw*(1-side*SLIP)
                gross=side*p["qty"]*(fill-p["entry"])
                fees=FEE*p["qty"]*(p["entry"]+fill)
                net=gross-fees
                equity+=net
                trades.append(dict(symbol=symbol,timeframe="1h",direction="LONG" if side==1 else "SHORT",
                    entry_utc=iso(p["t"]),exit_utc=iso(now),
                    month_ist=pd.Timestamp(now,unit="s",tz="UTC").tz_convert("Asia/Kolkata").strftime("%Y-%m"),
                    entry=p["entry"],exit=fill,entry_atr14=p["entry_atr"],entry_trail_distance=MULT*p["entry_atr"],
                    exit_trail_level=stop,exit_reason="ATR_TRAIL",
                    supertrend_epoch=p["epoch"],trade_held_hours=(now-p["t"])/3600.,
                    worst_adverse_points=p["max_adverse"],
                    best_favorable_points=p["max_favorable"],
                    gross_usd=gross,fees_gst_usd=fees,net_usd=net,equity_after_usd=equity))
                position=None
                count=0
                last_touch_bar=b
            else:
                # No stop hit within this minute: now it's safe to use the
                # completed minute's favorable extreme to tighten for NEXT minute.
                p["max_adverse"]=max(p["max_adverse"],max(0.,(p["entry"]-(l1 if side==1 else h1))*side))
                p["max_favorable"]=max(p["max_favorable"],max(0.,((h1 if side==1 else l1)-p["entry"])*side))
                if side==1:
                    p["best"]=max(p["best"],h1)
                    p["trail"]=max(p["trail"],p["best"]-atr_dist)
                else:
                    p["best"]=min(p["best"],l1)
                    p["trail"]=min(p["trail"],p["best"]+atr_dist)
                p["trail"]=float(p["trail"])

        elif not epoch_traded and last_touch_bar!=b:
            level=float(ema[done])
            if l1<=level<=h1:
                touch_events+=1
                last_touch_bar=b
                count+=1
                if count==2:
                    if epoch_id in epoch_used:
                        raise AssertionError("Duplicate entry in Supertrend epoch")
                    entry=level*(1+trend*SLIP)
                    qty=equity/entry
                    position=dict(side=trend,entry=entry,qty=qty,t=now,i=i,
                        trail=entry-trend*atr_dist,best=entry,entry_atr=float(atr[done]),
                        max_adverse=0.,max_favorable=0.,epoch=epoch_id)
                    epoch_traded=True
                    epoch_used.add(epoch_id)
                    count=0
                    # The EMA touch minute is ambiguous about high/low order.
                    # Count a same-entry-minute adverse stop trigger. NEVER use
                    # same-entry-minute favorable wick to tighten the stop.
                    stop=position["trail"]
                    if (trend==1 and l1<=stop) or (trend==-1 and h1>=stop):
                        raw=min(o1,stop) if trend==1 else max(o1,stop)
                        fill=raw*(1-trend*SLIP)
                        gross=trend*qty*(fill-entry)
                        fees=FEE*qty*(entry+fill)
                        net=gross-fees
                        equity+=net
                        trades.append(dict(symbol=symbol,timeframe="1h",
                            direction="LONG" if trend==1 else "SHORT",entry_utc=iso(now),exit_utc=iso(now),
                            month_ist=pd.Timestamp(now,unit="s",tz="UTC").tz_convert("Asia/Kolkata").strftime("%Y-%m"),
                            entry=entry,exit=fill,entry_atr14=float(atr[done]),entry_trail_distance=atr_dist,
                            exit_trail_level=stop,exit_reason="ATR_TRAIL_ENTRY_MINUTE",
                            supertrend_epoch=epoch_id,trade_held_hours=0.,
                            worst_adverse_points=max(0.,(entry-(l1 if trend==1 else h1))*trend),
                            best_favorable_points=0.,gross_usd=gross,fees_gst_usd=fees,net_usd=net,
                            equity_after_usd=equity))
                        position=None

        # Mark FULL floating equity each minute, even if exit isn't triggered.
        # Counterfactual adverse wick gives conservative equity stress scenario.
        if position is not None:
            side=position["side"]
            rawclose=c1*(1-side*SLIP)
            worstprice=(l1 if side==1 else h1)*(1-side*SLIP)
            qty=position["qty"]
            entry=position["entry"]
            floating=equity+side*qty*(rawclose-entry)-FEE*qty*(entry+rawclose)
            adverse_equity=equity+side*qty*(worstprice-entry)-FEE*qty*(entry+worstprice)
        else:
            floating=equity
            adverse_equity=equity
        peak=max(peak,floating)
        worst_equity=min(worst_equity,adverse_equity)
        if peak>0:
            max_mtm_dd=max(max_mtm_dd,100.*(peak-adverse_equity)/peak)
        if first_zero is None and adverse_equity<=0:
            first_zero=iso(now)
        if i in monthends:
            monthly.append(dict(symbol=symbol,timeframe="1h",month_ist=monthends[i],
                equity_mark_usd=floating,open_position=position is not None))

    sample_end_open=position is not None
    if sample_end_open:
        p=position
        side=p["side"]
        finalfill=float(c[-1])*(1-side*SLIP)
        gross=side*p["qty"]*(finalfill-p["entry"])
        fees=FEE*p["qty"]*(p["entry"]+finalfill)
        net=gross-fees
        equity+=net
        now=int(times[-1])
        trades.append(dict(symbol=symbol,timeframe="1h",direction="LONG" if side==1 else "SHORT",
            entry_utc=iso(p["t"]),exit_utc=iso(now),
            month_ist=pd.Timestamp(now,unit="s",tz="UTC").tz_convert("Asia/Kolkata").strftime("%Y-%m"),
            entry=p["entry"],exit=finalfill,entry_atr14=p["entry_atr"],entry_trail_distance=MULT*p["entry_atr"],
            exit_trail_level=p["trail"],exit_reason="SAMPLE_END_FORCED",
            supertrend_epoch=p["epoch"],trade_held_hours=(now-p["t"])/3600.,
            worst_adverse_points=p["max_adverse"],best_favorable_points=p["max_favorable"],
            gross_usd=gross,fees_gst_usd=fees,net_usd=net,equity_after_usd=equity))
        monthly[-1]["equity_mark_usd"]=equity

    ledger=pd.DataFrame(trades)
    if ledger.empty:
        ledger=pd.DataFrame(columns=["symbol","timeframe","net_usd","fees_gst_usd","exit_reason","month_ist","equity_after_usd","supertrend_epoch","trade_held_hours"])
    if ledger.supertrend_epoch.duplicated().any():
        raise AssertionError("Multiple entries in same Supertrend direction cycle")
    if abs(float(ledger.net_usd.sum())-(equity-INITIAL))>0.01:
        raise AssertionError("Equity/PnL reconciliation failed")
    assert len(monthly)==22, ("Month ends missing",symbol,len(monthly))
    monthly_summary=[]
    prior=INITIAL
    for row in monthly:
        m=row["month_ist"]
        subset=ledger.loc[ledger.month_ist==m]
        mark=float(row["equity_mark_usd"])
        monthly_summary.append(dict(symbol=symbol,timeframe="1h",month_ist=m,
            trade_exits=len(subset),atr_trail_exits=int(subset.exit_reason.str.startswith("ATR_TRAIL").sum()),
            forced_end_exits=int((subset.exit_reason=="SAMPLE_END_FORCED").sum()),
            realized_trade_pnl_usd=float(subset.net_usd.sum()),
            mark_to_market_equity_usd=mark,
            return_pct=100*(mark/prior-1.) if prior>0 else None,
            open_at_month_end=bool(row["open_position"])))
        prior=mark

    pospnl=ledger.loc[ledger.net_usd>0,"net_usd"].sum()
    negpnl=-ledger.loc[ledger.net_usd<0,"net_usd"].sum()
    first_2025=monthly_summary[11]["mark_to_market_equity_usd"]
    summary=dict(symbol=symbol,entry_timeframe="1h",execution_timeframe="1m",
        atr_period=14,atr_multiplier=MULT,atr_source="last completed 1h candle",
        one_entry_per_supertrend_epoch=True,
        supertrend_epochs_observed=epoch_id,
        epochs_traded=len(epoch_used),
        trades=len(ledger),
        exits_atr=int(ledger.exit_reason.str.startswith("ATR_TRAIL").sum()),
        exits_sample_end=int((ledger.exit_reason=="SAMPLE_END_FORCED").sum()),
        winning_trades=int((ledger.net_usd>0).sum()),
        losing_trades=int((ledger.net_usd<0).sum()),
        win_rate_pct=round(100*float((ledger.net_usd>0).mean()),4) if len(ledger) else 0.,
        profit_factor=round(float(pospnl/negpnl),4) if negpnl>0 else None,
        net_profit_usd=round(equity-INITIAL,5),
        net_return_pct=round(100*(equity/INITIAL-1),5),
        max_mark_to_market_drawdown_pct=round(max_mtm_dd,4),
        min_mark_to_market_equity_usd=round(worst_equity,4),
        equity_at_or_below_zero=first_zero is not None,
        first_zero_time_utc=first_zero,
        positive_months=sum(1 for m in monthly_summary if m["return_pct"] is not None and m["return_pct"]>0),
        negative_months=sum(1 for m in monthly_summary if m["return_pct"] is not None and m["return_pct"]<0),
        flat_months=sum(1 for m in monthly_summary if m["return_pct"] is not None and m["return_pct"]==0),
        return_2025_pct=round(100*(first_2025/INITIAL-1),4),
        return_2026_jan_oct_pct=round(100*(equity/first_2025-1),4),
        max_holding_hours=round(float(ledger.trade_held_hours.max()),2) if len(ledger) else 0.,
        average_holding_hours=round(float(ledger.trade_held_hours.mean()),2) if len(ledger) else 0.,
        total_fees_gst_usd=round(float(ledger.fees_gst_usd.sum()),4),
        sample_end_open=sample_end_open,touch_events=touch_events)
    return ledger,monthly_summary,summary

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    all_trades=[];all_monthly=[];summaries=[];sources={}
    for symbol in ("BTCUSD","ETHUSD"):
        print("RUN",symbol,flush=True)
        df,source=read_source(symbol)
        sources[symbol]=source
        trades,monthly,summary=replay(df,symbol)
        all_trades.append(trades)
        all_monthly.extend(monthly)
        summaries.append(summary)
        print("RESULT",json.dumps(summary,default=str,sort_keys=True),flush=True)
    pd.concat(all_trades,ignore_index=True).to_csv(OUT/"trade_ledger.csv.gz",index=False,compression="gzip")
    pd.DataFrame(all_monthly).to_csv(OUT/"monthly_mark_to_market.csv",index=False)
    pd.DataFrame(summaries).to_csv(OUT/"summary.csv",index=False)
    (OUT/"quality.json").write_text(json.dumps({
        "source":sources,"entry":"Second EMA20 touch on a distinct post-flip 1h candle, immediate 1m approximation",
        "supertrend":"10,3; one entry per confirmed direction epoch",
        "exit":"3x ATR(14) 1h trailing; updated from last completed hour, once per 1m after checking previous stop",
        "initial_atr_stop":True,"fixed_tp":False,"separate_fixed_sl":False,
        "hourly_volume_and_volatility_filters":False,
        "fees":"0.05 percent taker per side; 18 percent GST","adverse_slippage_fraction_each_side":SLIP,
        "capital_usd":INITIAL,"model_exposure":"1x evolving equity",
        "no_orderbook_funding_actual_liquidation_or_tick_sequence":True,
        "month_scope":"2025-01 to 2026-10 Asia/Kolkata",
        "one_minute_double_cross":"active stop checked before favorable trailing updates"
    },indent=2)+"\n")
    lines=["# Second EMA20 touch 1H — one trade per Supertrend — ATR trailing exit","",
        "BTCUSD and ETHUSD Delta Exchange India original SHA-verified 1m candles, Jan 2025–Oct 2026 (22 IST months).",
        "**No fixed TP**. Stop is ATR-only: initialized 2× ATR14, tightened by completed 1m highs/lows at last completed 1h ATR; stop never retreats.",
        "One entry in each confirmed Supertrend direction epoch, 1H EMA20 second distinct touch. No 1H volume/volatility filter.","",
        "| Asset | Trades | Wins | Win rate | Profit factor | Net return | Max floating drawdown | Profitable months |",
        "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for s in summaries:
        lines.append(f"| {s['symbol']} | {s['trades']} | {s['winning_trades']} | {s['win_rate_pct']:.2f}% | {s['profit_factor']} | {s['net_return_pct']:.3f}% | {s['max_mark_to_market_drawdown_pct']:.2f}% | {s['positive_months']}/22 |")
    lines+=["",
        "## Execution model and limitations",
        "- The ATR trailing stop includes an initial 3×ATR protective distance; it is the ONLY stop, not a separate fixed SL.",
        "- Existing stop triggers at the unfavorable of stop or 1m open, with 0.02% adverse slippage; new highs/lows update trailing for the NEXT minute only.",
        "- Upon entry, do not credit favorable first-minute wick for tightening. The adverse wick can trigger an exit; the 1m price path is not known.",
        "- Full model with 1× compounding starting $1000, 0.05% taker fees on both sides + 18% GST; no funding, bid/ask depth, or actual liquidation/margin.",
        "- Month-by-month values include floating mark-to-market equity. 2026 previously explored, so not pristine out-of-sample data.",
        "- Source archive Jan 2025 begins UTC midnight, 5h30 IST missing. No interpolation of subsequent missing candles.",
        "","See summary.csv, monthly_mark_to_market.csv, trade_ledger.csv.gz, quality.json and preregistration."]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(lines)+"\n")
    print("BACKTEST_DONE",json.dumps(summaries,default=str),flush=True)

if __name__=="__main__":
    main()
