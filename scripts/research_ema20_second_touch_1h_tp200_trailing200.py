#!/usr/bin/env python3
"""1H second-EMA20-touch Supertrend: TP200 + immediately active 200-point trailing stop.
ETH distances use BTC-equivalent percentage frozen ex ante at entry. 1m stop-first OHLC.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from research_ema20_second_touch import read_source, features, MONTHS, FEE, SLIP

OUT=Path("analysis/ema20_second_touch_1h_tp200_trailing200_20261121")
TF=60
BTC_POINTS=200.0
INITIAL=1000.

def iso(sec):
    return pd.Timestamp(int(sec),unit="s",tz="UTC").isoformat()

def replay(df, symbol, btc_prev):
    ema, atr, st, complete=features(df,TF)
    times=df.time.to_numpy(dtype=np.int64)
    o=df.open.to_numpy(dtype=float)
    h=df.high.to_numpy(dtype=float)
    l=df.low.to_numpy(dtype=float)
    c=df.close.to_numpy(dtype=float)
    assert times[0]%(TF*60)==0
    assert len(ema)==len(atr)==len(st)
    assert len(c)==len(times) and len(btc_prev)==len(times)

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
        # Use no ATR in exit calculation. 200 BTC-price points are fixed
        # for BTC, and proportionally converted for ETH at its entry.

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
            hit_stop=(side==1 and l1<=stop) or (side==-1 and h1>=stop)
            hit_tp=(side==1 and h1>=p["target"]) or (side==-1 and l1<=p["target"])
            # Stop-FIRST if both TP and trailing stop occur within same minute.
            # The intraminute ordering is unknown and this avoids a free win.
            if hit_stop or hit_tp:
                if hit_stop:
                    raw=min(o1,stop) if side==1 else max(o1,stop)
                    reason="TRAIL_STOP"
                else:
                    raw=p["target"]  # target fill, no favorable gap improvement
                    reason="TAKE_PROFIT"
                fill=raw*(1-side*SLIP)
                gross=side*p["qty"]*(fill-p["entry"])
                fees=FEE*p["qty"]*(p["entry"]+fill)
                net=gross-fees
                equity+=net
                trades.append(dict(symbol=symbol,timeframe="1h",direction="LONG" if side==1 else "SHORT",
                    entry_utc=iso(p["t"]),exit_utc=iso(now),
                    month_ist=pd.Timestamp(now,unit="s",tz="UTC").tz_convert("Asia/Kolkata").strftime("%Y-%m"),
                    entry=p["entry"],exit=fill,entry_distance=p["distance"],target=p["target"],
                    exit_trail_level=stop,exit_reason=reason,
                    btc_previous_minute_close=p["btc_ref"],
                    supertrend_epoch=p["epoch"],trade_held_hours=(now-p["t"])/3600.,
                    worst_adverse_points=p["max_adverse"],
                    best_favorable_points=p["max_favorable"],
                    gross_usd=gross,fees_gst_usd=fees,net_usd=net,equity_after_usd=equity))
                position=None
                count=0
                last_touch_bar=b
            else:
                # Neither exit hit. Update stop with the completed 1m bar's
                # favorable wick; tightened stop becomes effective NEXT minute.
                p["max_adverse"]=max(p["max_adverse"],max(0.,(p["entry"]-(l1 if side==1 else h1))*side))
                p["max_favorable"]=max(p["max_favorable"],max(0.,((h1 if side==1 else l1)-p["entry"])*side))
                if side==1:
                    p["best"]=max(p["best"],h1)
                    p["trail"]=max(p["trail"],p["best"]-p["distance"])
                else:
                    p["best"]=min(p["best"],l1)
                    p["trail"]=min(p["trail"],p["best"]+p["distance"])

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
                    btc_ref=float(btc_prev[i])
                    if not(np.isfinite(btc_ref) and btc_ref>0):
                        raise AssertionError("Missing ex-ante BTC prior-minute close")
                    dist=(BTC_POINTS if symbol=="BTCUSD" else BTC_POINTS*entry/btc_ref)
                    if dist<=0:
                        raise AssertionError("Invalid target/trail points")
                    qty=equity/entry
                    position=dict(side=trend,entry=entry,qty=qty,t=now,i=i,
                        trail=entry-trend*dist,target=entry+trend*dist,
                        best=entry,distance=dist,btc_ref=btc_ref,
                        max_adverse=0.,max_favorable=0.,epoch=epoch_id)
                    epoch_traded=True
                    epoch_used.add(epoch_id)
                    count=0
                    # Entry minute: do NOT award target or advance trailing with
                    # its high/low, because order of events in 1m is unknown.
                    # If that same minute also spans the initial protective
                    # trail, assume stop-first at the actual trail LEVEL.
                    # Its open may predate entry; don't use open as gap fill.
                    stop=position["trail"]
                    if (trend==1 and l1<=stop) or (trend==-1 and h1>=stop):
                        raw=stop
                        fill=raw*(1-trend*SLIP)
                        gross=trend*qty*(fill-entry)
                        fees=FEE*qty*(entry+fill)
                        net=gross-fees
                        equity+=net
                        trades.append(dict(symbol=symbol,timeframe="1h",
                            direction="LONG" if trend==1 else "SHORT",entry_utc=iso(now),exit_utc=iso(now),
                            month_ist=pd.Timestamp(now,unit="s",tz="UTC").tz_convert("Asia/Kolkata").strftime("%Y-%m"),
                            entry=entry,exit=fill,entry_distance=dist,target=entry+trend*dist,
                            exit_trail_level=stop,exit_reason="TRAIL_STOP_ENTRY_MINUTE",
                            btc_previous_minute_close=btc_ref,
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
            entry=p["entry"],exit=finalfill,entry_distance=p["distance"],target=p["target"],
            exit_trail_level=p["trail"],exit_reason="SAMPLE_END_FORCED",
            btc_previous_minute_close=p["btc_ref"],
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
            trade_exits=len(subset),
            tp_exits=int((subset.exit_reason=="TAKE_PROFIT").sum()),
            trail_exits=int(subset.exit_reason.str.startswith("TRAIL_STOP").sum()),
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
        btc_fixed_tp_points=BTC_POINTS,btc_trail_distance_points=BTC_POINTS,
        eth_scale_rule="entry_ETH * 200 / previous_closed_1m_BTC",
        trailing_activated_at_entry=True,atr_trailing_enabled=False,
        one_entry_per_supertrend_epoch=True,
        supertrend_epochs_observed=epoch_id,
        epochs_traded=len(epoch_used),
        trades=len(ledger),
        exits_tp=int((ledger.exit_reason=="TAKE_PROFIT").sum()),
        exits_trail=int(ledger.exit_reason.str.startswith("TRAIL_STOP").sum()),
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
    btc,bc_quality=read_source("BTCUSD")
    eth,eth_quality=read_source("ETHUSD")
    sources.update(BTCUSD=bc_quality,ETHUSD=eth_quality)
    if not np.array_equal(btc.time.to_numpy(),eth.time.to_numpy()):
        raise AssertionError("BTC and ETH 1m timestamps are not aligned")
    btc_previous_close=np.r_[np.nan,btc.close.to_numpy(dtype=float)[:-1]]
    for symbol,df in (("BTCUSD",btc),("ETHUSD",eth)):
        print("RUN",symbol,flush=True)
        trades,monthly,summary=replay(df,symbol,btc_previous_close)
        all_trades.append(trades)
        all_monthly.extend(monthly)
        summaries.append(summary)
        print("RESULT",json.dumps(summary,default=str,sort_keys=True),flush=True)
    pd.concat(all_trades,ignore_index=True).to_csv(OUT/"trade_ledger.csv.gz",index=False,compression="gzip")
    pd.DataFrame(all_monthly).to_csv(OUT/"monthly_mark_to_market.csv",index=False)
    pd.DataFrame(summaries).to_csv(OUT/"summary.csv",index=False)
    (OUT/"quality.json").write_text(json.dumps({
        "source":sources,
        "entry":"1H completed Supertrend(10,3) EMA20 second distinct touch, immediate 1m OHLC approximation",
        "one_entry_per_confirmed_supertrend_epoch":True,
        "fixed_btc_tp_price_points":BTC_POINTS,
        "fixed_btc_trailing_price_points":BTC_POINTS,
        "eth_price_distance":"200 * ETH entry / preceding completed 1m BTC close (frozen at entry)",
        "trailing_activated":"immediately at entry, no separate activation threshold",
        "atr_exit":False,
        "separate_fixed_sl":False,
        "order_of_1m_exits":"previously active trailing stop FIRST, then fixed TP; update trail for NEXT minute",
        "entry_minute":"if adverse wick hits initial trail, conservatively stop there; no entry-minute TP or high/low trail tightening",
        "hourly_volume_and_volatility_filters":False,
        "fees":"0.05 percent taker per side plus GST 18 percent",
        "adverse_slippage_fraction_each_side":SLIP,
        "initial_usd":INITIAL,"model_exposure":"1x evolving model equity",
        "date_scope":"2025-01 through 2026-10 IST, source SHA verified",
        "not_modeled":["funding","true spreads","orderbook","liquidation","tick-level sequence","latency"],
        "sample_end_forced_close_only_for_reporting":True,
        "historical_2026_not_pristine_out_of_sample":True
    },indent=2)+"\n")
    lines=[
        "# 1H EMA20 second touch — TP200 plus 200-point trailing stop",
        "",
        "One entry per Supertrend 10,3 cycle. Second distinct post-flip EMA20 touch enters immediately on 1m OHLC.",
        "Fixed take profit +200 BTC price points; trailing distance 200 BTC price points, active immediately. ETH both distances scaled as 200*ETHentry/precedingBTCclose and frozen. NO ATR trailing, no separate fixed SL.",
        "Stop-first if 1m candle crosses both exit levels; trailing updates on completed 1m candles become active next minute.",
        "22 months 2025-01–2026-10 (IST) using SHA-verified Delta India BTCUSD and ETHUSD 1m data. 1x evolving notional, $1000 starting account, fees+GST and adverse slippage.",
        "",
        "| Asset | Trades | TP exits | Trailing-stop exits | Win rate after fees | Profit factor | Net return | Max floating DD | Profitable months |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|"
    ]
    for x in summaries:
        lines.append(f"| {x['symbol']} | {x['trades']} | {x['exits_tp']} | {x['exits_trail']} | {x['win_rate_pct']:.2f}% | {x['profit_factor']} | {x['net_return_pct']:.3f}% | {x['max_mark_to_market_drawdown_pct']:.3f}% | {x['positive_months']}/22 |")
    lines+=["","## Cautions",
        "- The trailing stop is initially at ±200 points, so it IS a protective stop. There is no ATR-based trail or extra stop.",
        "- Ambiguous 1m candle that reaches TP and trailing stop counts stop FIRST. Do not backfill a candle's new high/low into its already-active trail.",
        "- On the entry minute no TP or favorable trail update is credited. Initial stop touched on entry minute is filled at its stop level; tick ordering is unknown.",
        "- Gross/model net equity and 22-month monthly returns count fees (0.05% each side + 18% GST) and 0.02% adverse slippage both sides.",
        "- Not a live execution guarantee: funding, exact fills, actual bid/ask spread, margin/liquidation, and real tick ordering missing.",
        "- Historic 2026 already extensively explored and cannot be considered a pristine out-of-sample validation.",
        "- 2025 archive begins UTC Jan 1 and excludes first 5.5 IST hours of Jan 2025.",
        "","Outputs: summary.csv, monthly_mark_to_market.csv, trade_ledger.csv.gz, quality.json."
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(lines)+"\n")
    print("BACKTEST_DONE",json.dumps(summaries,default=str),flush=True)

if __name__=="__main__":
    main()
