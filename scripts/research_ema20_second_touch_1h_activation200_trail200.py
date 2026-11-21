#!/usr/bin/env python3
"""1H second EMA20 touch: activate trailing at +200 points, trail distance 200 points.
No fixed TP or stop before activation; ETH distances BTC-equivalent percent, frozen.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from research_ema20_second_touch import read_source, features, MONTHS, FEE, SLIP

OUT=Path("analysis/ema20_second_touch_1h_activation200_trail200_20261121")
TF=60
ACTIVATE_BTC_POINTS=200.0
TRAIL_BTC_POINTS=200.0
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
            reason=None
            raw=None
            stop=p["trail"]
            was_active=p["active"]
            if was_active and ((side==1 and l1<=stop) or (side==-1 and h1>=stop)):
                # Previously active stop: do not use same-minute newly achieved high.
                raw=min(o1,stop) if side==1 else max(o1,stop)
                reason="TRAIL_ACTIVE"
            else:
                # No active stop, or previous stop survived the current minute.
                p["max_adverse"]=max(p["max_adverse"],
                    max(0.,(p["entry"]-(l1 if side==1 else h1))*side))
                p["max_favorable"]=max(p["max_favorable"],
                    max(0.,((h1 if side==1 else l1)-p["entry"])*side))
                if side==1:
                    p["best"]=max(p["best"],h1)
                    favorable=p["best"]-p["entry"]
                else:
                    p["best"]=min(p["best"],l1)
                    favorable=p["entry"]-p["best"]
                if not was_active and favorable>=p["activation"]:
                    # Activation only after price has moved +200; no stop BEFORE.
                    p["active"]=True
                    newstop=p["best"]-side*p["distance"]
                    p["trail"]=newstop
                    p["activation_utc"]=iso(now)
                    # Ambiguous 1m high/low sequencing: pessimistically assume
                    # the newly activated trail was hit AFTER activation when
                    # this same 1m also crosses the new stop.
                    if (side==1 and l1<=newstop) or (side==-1 and h1>=newstop):
                        raw=newstop
                        reason="TRAIL_ACTIVATION_MINUTE"
                elif was_active:
                    # Only tighten; the new level becomes actionable NEXT 1m.
                    newstop=p["best"]-side*p["distance"]
                    p["trail"]=(max(stop,newstop) if side==1
                                else min(stop,newstop))
            if reason is not None:
                fill=raw*(1-side*SLIP)
                gross=side*p["qty"]*(fill-p["entry"])
                fees=FEE*p["qty"]*(p["entry"]+fill)
                net=gross-fees
                equity+=net
                trades.append(dict(symbol=symbol,timeframe="1h",
                    direction="LONG" if side==1 else "SHORT",
                    entry_utc=iso(p["t"]),exit_utc=iso(now),
                    month_ist=pd.Timestamp(now,unit="s",tz="UTC").tz_convert("Asia/Kolkata").strftime("%Y-%m"),
                    entry=p["entry"],exit=fill,activation_points=p["activation"],
                    trail_distance_points=p["distance"],activation_utc=p["activation_utc"],
                    exit_trail_level=p["trail"],exit_reason=reason,
                    btc_previous_minute_close=p["btc_ref"],
                    supertrend_epoch=p["epoch"],trade_held_hours=(now-p["t"])/3600.,
                    worst_adverse_points=p["max_adverse"],best_favorable_points=p["max_favorable"],
                    gross_usd=gross,fees_gst_usd=fees,net_usd=net,equity_after_usd=equity))
                position=None
                count=0
                last_touch_bar=b

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
                        raise AssertionError("Missing prior 1m BTC close")
                    activation=(ACTIVATE_BTC_POINTS if symbol=="BTCUSD" else
                        ACTIVATE_BTC_POINTS*entry/btc_ref)
                    distance=(TRAIL_BTC_POINTS if symbol=="BTCUSD" else
                        TRAIL_BTC_POINTS*entry/btc_ref)
                    if activation<=0 or distance<=0:
                        raise AssertionError("Invalid activation or trailing distance")
                    qty=equity/entry
                    position=dict(side=trend,entry=entry,qty=qty,t=now,i=i,
                        active=False,trail=np.nan,activation_utc=None,best=entry,
                        distance=distance,activation=activation,btc_ref=btc_ref,
                        max_adverse=0.,max_favorable=0.,epoch=epoch_id)
                    epoch_traded=True
                    epoch_used.add(epoch_id)
                    count=0
                    # Entry 1m candle is ambiguous about crossing order.
                    # No entry-minute activation or stop and no fixed TP.

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
            entry=p["entry"],exit=finalfill,activation_points=p["activation"],
            trail_distance_points=p["distance"],activation_utc=p["activation_utc"],
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
            trail_exits=int(subset.exit_reason.str.startswith("TRAIL_").sum()),
            activation_minute_exits=int((subset.exit_reason=="TRAIL_ACTIVATION_MINUTE").sum()),
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
        fixed_take_profit_points=None,
        btc_activation_points=ACTIVATE_BTC_POINTS,
        btc_trail_distance_points=TRAIL_BTC_POINTS,
        eth_scale_rule="entry_ETH * 200 / previous_closed_1m_BTC",
        trailing_activated_at_entry=False,atr_trailing_enabled=False,
        one_entry_per_supertrend_epoch=True,
        supertrend_epochs_observed=epoch_id,
        epochs_traded=len(epoch_used),
        trades=len(ledger),
        exits_tp=0,
        exits_trail=int(ledger.exit_reason.str.startswith("TRAIL_").sum()),
        activation_minute_exits=int((ledger.exit_reason=="TRAIL_ACTIVATION_MINUTE").sum()),
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
        "fixed_btc_tp_price_points":None,
        "btc_trailing_activation_points":ACTIVATE_BTC_POINTS,
        "btc_trailing_distance_points":TRAIL_BTC_POINTS,
        "eth_price_distance":"activation and distance each = 200 * ETH entry / prior completed 1m BTC close, frozen per entry",
        "trailing_activated":"only after favorable 200 BTC points (percentage equivalent ETH), no stop before activation",
        "atr_exit":False,
        "separate_fixed_sl":False,
        "order_of_1m_exits":"check previously active trailing stop first; tighten for next minute; if trail activates within minute and adverse wick also crosses newly activated stop, assume pessimistic activation-then-retrace and exit at activated stop",
        "entry_minute":"do not activate on the entry minute; no stop exists before +200 points",
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
        "# 1H EMA20 second touch — activate +200, trailing distance 200",
        "",
        "BTCUSD/ETHUSD 22 IST months Jan 2025–Oct 2026, original 1m Delta India data. 1H EMA20 second distinct touch, Supertrend(10,3), one trade per trend epoch.",
        "**No fixed TP. No fixed SL before trailing activation.** Trailing begins only once favorable price reaches +200 BTC points (ETH percent equivalent), then follows best price at 200 BTC-point distance.",
        "Activation-minute ambiguity: if same 1m candle crosses favorable activation and newly computed stop, pessimistically assume immediate trailing exit. Already-active stops are checked before updates and tightened levels activate the next 1m.",
        "",
        "| Asset | Trades | Trail exits | Activation-minute exits | Sample-end forced | Win rate | PF | Net return | Max floating DD | Profitable months |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"
    ]
    for x in summaries:
        lines.append(f"| {x['symbol']} | {x['trades']} | {x['exits_trail']} | {x['activation_minute_exits']} | {x['exits_sample_end']} | {x['win_rate_pct']:.2f}% | {x['profit_factor']} | {x['net_return_pct']:.3f}% | {x['max_mark_to_market_drawdown_pct']:.3f}% | {x['positive_months']}/22 |")
    lines+=["","## Limitations and interpretation",
        "- +200 is activation threshold, not a TP; there is NO fixed take profit.",
        "- Before +200, exposure is unprotected by any stop; severely adverse trends and liquidation are not modeled.",
        "- Once activated, the trailing stop starts about entry (gross breakeven before costs) when exactly +200, then moves with favorable prices. Never retreats.",
        "- Ambiguous OHLC ordering on the activation minute uses a pessimistic activation-then-retrace stop-fill. Actual tick replay would be needed for live parity.",
        "- 1x model equity sizing, taker fee 0.05% each side plus 18% GST, 0.02% adverse slippage each side.",
        "- Funding, exact bid/ask spread, latency, exchange liquidation, tick sequence and real margin use not modeled.",
        "- Sample-end forced close for reporting is not a live exit rule. Results in tested 2026 sample are not pristine OOS.",
        "","Results: summary.csv, trade_ledger.csv.gz, monthly_mark_to_market.csv, quality.json."]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(lines)+"\n")
    print("BACKTEST_DONE",json.dumps(summaries,default=str),flush=True)

if __name__=="__main__":
    main()
