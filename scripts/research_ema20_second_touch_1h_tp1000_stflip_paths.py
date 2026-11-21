#!/usr/bin/env python3
"""1H EMA20 second-touch: fixed TP1000 or confirmed Supertrend flip, first exit wins.
NO step-profit-lock or trailing stop. ETH TP is percentage-equivalent to BTC1000.
Two hypothetical 1m OHLC paths used for entry-minute sequencing sensitivity.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from research_ema20_second_touch import read_source, features, MONTHS, FEE, SLIP

OUT=Path("analysis/ema20_second_touch_1h_tp1000_stflip_20261121")
INITIAL=1000.
TIMEFRAME=60
BTC_FIXED_TP=1000.
PATHS=("O-H-L-C","O-L-H-C")

def timestamp(sec):
    return pd.Timestamp(int(sec),unit="s",tz="UTC")

def mark_at_cash_equivalent(balance,pos,raw):
    if pos is None:
        return balance
    side=pos["side"]
    liquidation_proxy=raw*(1-side*SLIP)
    return (balance+side*pos["qty"]*(liquidation_proxy-pos["entry"])
       -FEE*pos["qty"]*liquidation_proxy)

def run_asset(df,symbol,btc_previous,path_name):
    ema,_,trend,valid=features(df,TIMEFRAME)
    ts=df.time.to_numpy(dtype=np.int64)
    op=df.open.to_numpy(float)
    high=df.high.to_numpy(float)
    low=df.low.to_numpy(float)
    close=df.close.to_numpy(float)
    assert len(op)==len(ts)==len(btc_previous)
    assert ts[0]%(TIMEFRAME*60)==0
    assert path_name in PATHS

    monthends={}
    for month in MONTHS:
        p=pd.Period(month,freq="M")
        end=(p+1).start_time.tz_localize("Asia/Kolkata").tz_convert("UTC")-pd.Timedelta(minutes=1)
        i=int(np.searchsorted(ts,int(end.timestamp()),side="right")-1)
        if i<0 or ts[i]!=int(end.timestamp()):
            raise AssertionError("Month end 1m candle missing: "+month)
        monthends[i]=month

    cash=INITIAL
    open_pos=None
    last_direction=0
    current_epoch=0
    entry_epochs=set()
    touches=0
    last_touched_bar=-1
    touch_count=0
    peak_eq=INITIAL
    lowest_eq=INITIAL
    largest_dd=0.
    first_zero=None
    trades=[]
    monthly=[]
    activation_count=0
    max_hold=0.

    def mark(raw, time_sec):
        nonlocal peak_eq,lowest_eq,largest_dd,first_zero
        eq=mark_at_cash_equivalent(cash,open_pos,raw)
        peak_eq=max(peak_eq,eq)
        lowest_eq=min(lowest_eq,eq)
        if peak_eq>0:
            largest_dd=max(largest_dd,100.*(peak_eq-eq)/peak_eq)
        if first_zero is None and eq<=0:
            first_zero=timestamp(time_sec).isoformat()

    def close_position(raw,now,reason):
        nonlocal cash,open_pos,max_hold
        p=open_pos
        if p is None:
            raise AssertionError("No position")
        side=p["side"]
        fill=raw*(1-side*SLIP)
        gross=side*p["qty"]*(fill-p["entry"])
        exit_fee=FEE*p["qty"]*fill
        net=gross-p["entry_fee"]-exit_fee
        cash+=gross-exit_fee
        dur=(now-p["entry_time"])/3600.
        max_hold=max(max_hold,dur)
        trades.append(dict(symbol=symbol,path_model=path_name,
            entry_time_utc=timestamp(p["entry_time"]).isoformat(),
            exit_time_utc=timestamp(now).isoformat(),
            month_ist=timestamp(now).tz_convert("Asia/Kolkata").strftime("%Y-%m"),
            direction="LONG" if side==1 else "SHORT",entry_fill=p["entry"],
            exit_fill=fill,exit_reason=reason,
            fixed_target_raw=p["target"],tp_distance=p["distance"],
            entry_epoch=p["epoch"],gross_pnl_usd=gross,fees_gst_usd=p["entry_fee"]+exit_fee,
            net_pnl_usd=net,equity_after_usd=cash,holding_hours=dur))
        open_pos=None
        mark_at_cash_equivalent(cash,open_pos,raw)
        # This function exits at the first stop crossing in the hypothesized path.

    def walk_segment(start,end,now):
        # Within a hypothetical OHLC path segment, check fixed TP if reached.
        # No stop or profit lock, and no exit on adverse movement before flip.
        if open_pos is None:
            return
        p=open_pos
        side=p["side"]
        if side*(start-p["target"])>=0 or side*(end-p["target"])>=0:
            # Conservatively fill at the predefined target even if a favorable
            # opening gap would allow a better price; apply adverse slippage.
            target=p["target"]
            mark(target,now)
            close_position(target,now,"FIXED_TP_1000")
            return
        mark(end,now)

    for i in range(len(df)):
        hb=i//TIMEFRAME
        done=hb-1
        if done<100 or done>=len(ema) or not valid[done] or int(trend[done])==0:
            continue
        side_trend=int(trend[done])
        if side_trend!=last_direction:
            # The latest 1H candle has CLOSED and Supertrend flipped.
            # Its newly confirmed direction is only actionable at THIS
            # next 1H candle's first minute OPEN; never look into an
            # unfinished reversal candle or exit at its historical close.
            if open_pos is not None:
                if open_pos["side"]==side_trend:
                    raise AssertionError("Already aligned position on Supertrend flip")
                close_position(float(op[i]),int(ts[i]),"SUPERTREND_FLIP")
            last_direction=side_trend
            current_epoch+=1
            touch_count=0
            last_touched_bar=-1
        now=int(ts[i])
        if path_name=="O-H-L-C":
            path=(op[i],high[i],low[i],close[i])
        else:
            path=(op[i],low[i],high[i],close[i])

        # A carried position can hit fixed TP on the new 1m OPEN.
        # Fill at target, not favorable gap improvement.
        if open_pos is not None and open_pos["side"]*(path[0]-open_pos["target"])>=0:
            close_position(open_pos["target"],now,"FIXED_TP_1000_GAP")
        mark(path[0],now)
        for seg in range(3):
            a,b=path[seg],path[seg+1]
            if open_pos is not None:
                walk_segment(a,b,now)
                continue
            if cash<=0 or current_epoch in entry_epochs or last_touched_bar==hb:
                continue
            lev=float(ema[done])
            if not(min(a,b)<=lev<=max(a,b)):
                mark(b,now)
                continue
            last_touched_bar=hb
            touch_count+=1
            touches+=1
            if touch_count!=2:
                mark(b,now)
                continue
            if current_epoch in entry_epochs:
                raise AssertionError("Reentry within one Supertrend cycle")
            entry_fill=lev*(1+side_trend*SLIP)
            btc_ref=float(btc_previous[i])
            if not(np.isfinite(btc_ref) and btc_ref>0):
                raise AssertionError("Previous BTC 1m reference missing")
            distance=BTC_FIXED_TP if symbol=="BTCUSD" else BTC_FIXED_TP*entry_fill/btc_ref
            qty=cash/entry_fill
            entry_fee=FEE*qty*entry_fill
            cash-=entry_fee
            open_pos=dict(side=side_trend,entry=entry_fill,entry_raw=lev,
                qty=qty,entry_fee=entry_fee,entry_time=now,epoch=current_epoch,
                distance=distance,target=entry_fill+side_trend*distance)
            entry_epochs.add(current_epoch)
            touch_count=0
            mark(lev,now)
            # The entry occurs at the first path segment crossing EMA20.
            # Process the remainder of THAT segment in sequence.
            walk_segment(lev,b,now)

        if i in monthends:
            eq=mark_at_cash_equivalent(cash,open_pos,float(close[i]))
            monthly.append(dict(symbol=symbol,path_model=path_name,
                month_ist=monthends[i],
                equity_mark_usd=eq,
                position_open_at_month_end=open_pos is not None,
                realized_cash_usd=cash))

    sample_end_open=open_pos is not None
    if sample_end_open:
        close_position(float(close[-1]),int(ts[-1]),"SAMPLE_END_ACCOUNTING_ONLY")
        monthly[-1]["equity_mark_usd"]=cash
    if len(monthly)!=22:
        raise AssertionError((symbol,path_name,"Missing month end",len(monthly)))

    ledger=pd.DataFrame(trades)
    if ledger.empty:
        raise RuntimeError("Unexpectedly no trades")
    if ledger.entry_epoch.duplicated().any():
        raise AssertionError("Duplicate entries in Supertrend epoch")
    if abs(float(ledger.net_pnl_usd.sum())-(cash-INITIAL))>0.02:
        raise AssertionError("Ledger cash reconciliation failed")
    monthly_frame=pd.DataFrame(monthly)
    monthly_frame["monthly_return_pct"]=100*(monthly_frame.equity_mark_usd/
           monthly_frame.equity_mark_usd.shift(1,fill_value=INITIAL)-1.)
    # Final reports must always count floating exposure and sample-end forced close.
    loss= -ledger.loc[ledger.net_pnl_usd<0,"net_pnl_usd"].sum()
    win=ledger.loc[ledger.net_pnl_usd>0,"net_pnl_usd"].sum()
    year25=float(monthly_frame.loc[monthly_frame.month_ist=="2025-12","equity_mark_usd"].iloc[0])
    summary=dict(symbol=symbol,path_assumption=path_name,
        historical_tick_backtest=False,
        actual_data_resolution="1-minute OHLC",
        one_entry_per_supertrend=True,
        btc_fixed_tp_points=BTC_FIXED_TP,
        fixed_take_profit=True,profit_lock_enabled=False,atr_trailing_enabled=False,
        standalone_stop_loss_enabled=False,
        trades=len(ledger),tp_exits=int(ledger.exit_reason.str.startswith("FIXED_TP_1000").sum()),
        supertrend_flip_exits=int((ledger.exit_reason=="SUPERTREND_FLIP").sum()),
        supertrend_flip_wins=int(((ledger.exit_reason=="SUPERTREND_FLIP")&(ledger.net_pnl_usd>0)).sum()),
        supertrend_flip_losses=int(((ledger.exit_reason=="SUPERTREND_FLIP")&(ledger.net_pnl_usd<0)).sum()),
        sample_end_forced=int((ledger.exit_reason=="SAMPLE_END_ACCOUNTING_ONLY").sum()),
        win_trades_after_costs=int((ledger.net_pnl_usd>0).sum()),
        loss_trades_after_costs=int((ledger.net_pnl_usd<0).sum()),
        win_rate_after_costs_pct=round(100*float((ledger.net_pnl_usd>0).mean()),4),
        profit_factor=round(float(win/loss),4) if loss>0 else None,
        profit_usd=round(float(cash-INITIAL),5),
        net_return_pct=round(float(100*(cash/INITIAL-1)),5),
        max_floating_dd_pct=round(largest_dd,4),
        min_equity_usd=round(lowest_eq,4),
        equity_at_or_below_zero=first_zero is not None,
        first_zero_utc=first_zero,
        positive_months=int((monthly_frame.monthly_return_pct>0).sum()),
        negative_months=int((monthly_frame.monthly_return_pct<0).sum()),
        positive_2025_return_pct=round(float(100*(year25/INITIAL-1)),4),
        return_2026_jan_oct_pct=round(float(100*(cash/year25-1)),4),
        longest_hold_hours=round(max_hold,2),
        activation_count=activation_count,
        supertrend_epochs=current_epoch,epochs_traded=len(entry_epochs),
        touched_hour_candles=touches,
        fees_gst_usd=round(float(ledger.fees_gst_usd.sum()),4))
    return ledger,monthly_frame,summary

def self_test():
    entry=80000.
    assert entry+BTC_FIXED_TP==81000
    assert entry-BTC_FIXED_TP==79000
    assert BTC_FIXED_TP==1000.
    print("SELF_TEST_OK: LONG 80000 TP 81000, SHORT 80000 TP 79000, no trailing",flush=True)

def main():
    self_test()
    OUT.mkdir(parents=True,exist_ok=True)
    btc,bq=read_source("BTCUSD")
    eth,eq=read_source("ETHUSD")
    if not np.array_equal(btc.time.to_numpy(),eth.time.to_numpy()):
        raise AssertionError("BTC ETH timelines mismatch")
    btc_prev=np.r_[np.nan,btc.close.to_numpy(float)[:-1]]
    quality=dict(BTCUSD=bq,ETHUSD=eq)
    summaries=[]
    all_trades=[]
    all_months=[]
    for mode in PATHS:
        for symbol,df in (("BTCUSD",btc),("ETHUSD",eth)):
            print("RUN",mode,symbol,flush=True)
            ledger,monthly,summary=run_asset(df,symbol,btc_prev,mode)
            all_trades.append(ledger)
            all_months.append(monthly)
            summaries.append(summary)
            print("RESULT",json.dumps(summary,default=str,sort_keys=True),flush=True)
    pd.concat(all_trades,ignore_index=True).to_csv(OUT/"trade_ledger.csv.gz",index=False,compression="gzip")
    pd.concat(all_months,ignore_index=True).to_csv(OUT/"monthly_mark_to_market.csv",index=False)
    pd.DataFrame(summaries).to_csv(OUT/"summary.csv",index=False)
    quality["research_rules"]=dict(
        fixed_take_profit_BTC_price_points=BTC_FIXED_TP,
        eth_fixed_target="1000*ETH executed entry / preceding completed 1m BTC close (frozen)",
        profit_lock_enabled=False,trailing_stop_enabled=False,
        initial_stop_loss_enabled=False,
        exit_on_confirmed_1h_supertrend_flip=True,
        supertrend_flip_execution="first 1m OPEN of the hour after confirmed 1h Supertrend reversal",
        exit_priority="whichever occurs first: fixed TP1000 or confirmed Supertrend flip",
        one_entry_per_supertrend_direction_cycle=True,
        entry="second post-flip distinct 1h candle last-completed EMA20 touch with 1m OHLC",
        indicator="1H Supertrend(10,3), 1H EMA20",
        synthetic_entry_minute_path_assumptions=list(PATHS),
        data="Original SHA-verified Delta India 1m BTCUSD ETHUSD Jan 2025-Oct 2026",
        no_actual_intraminute_ticks=True,
        slippage_each_side=SLIP,
        taker_fee_per_side=0.0005,GST_on_fee=0.18,
        real_funding_bidask_margin_liquidation_execution_latency_not_modeled=True,
        backtest_historical_not_pristine_oos=True)
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2)+"\n")
    lines=["# 1H EMA20 second touch — FIXED TP 1000 BTC points OR confirmed Supertrend reversal",
       "",
       "**Exact exit setup: no profit lock, no trailing stop, no separate SL.**",
       "First exit wins: fixed +1000 BTC-price points (percentage equivalent frozen for ETH), or confirmed 1H Supertrend flip at the following 1H candle's first 1m open.",
       "Entry unchanged: second distinct 1H EMA20-touch candle after Supertrend(10,3) flip; one trade per trend cycle; entry at 1m crossing of last completed hourly EMA20.",
       "",
       "| 1m assumed path | Asset | Trades | Fixed TP exits | Supertrend flip exits | Net wins | Net losses | Win rate | Profit factor | Net return | Profitable months | Max floating DD |",
       "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for x in summaries:
        lines.append(f"| {x['path_assumption']} | {x['symbol']} | {x['trades']} | {x['tp_exits']} | {x['supertrend_flip_exits']} | {x['win_trades_after_costs']} | {x['loss_trades_after_costs']} | {x['win_rate_after_costs_pct']}% | {x['profit_factor']} | {x['net_return_pct']}% | {x['positive_months']}/22 | {x['max_floating_dd_pct']}% |")
    lines+=["","## Limitations",
        "- 1-minute OHLC historical candles, two synthetic within-minute paths O-H-L-C and O-L-H-C ONLY to test ambiguous entry-minute sequence. Not measured historical ticks.",
        "- 1H reversal only confirmed at hour close, exit at NEXT hour open. No future peeking.",
        "- 1x account-sizing ($1000 starting each symbol), adverse 0.02% slippage each side, 0.05% taker each side, GST 18% on fees.",
        "- No liquidation, real margin, bid/ask, funding, orderbook, latency, exchange marketable-order impact. Positive model is not a live guarantee.",
        "- A final open position is closed for sample accounting only. 2026 was researched before and is not untouched out-of-sample.",
        "","Artifacts: summary.csv, monthly_mark_to_market.csv, trade_ledger.csv.gz, quality.json."]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(lines)+"\n")
    print("BACKTEST_DONE",json.dumps(summaries,default=str),flush=True)

if __name__=="__main__":
    main()
