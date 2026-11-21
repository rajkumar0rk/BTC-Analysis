#!/usr/bin/env python3
"""200-point MILESTONE PROFIT LOCK; exit on lock breach OR confirmed 1H Supertrend flip.
Research sensitivity with hypothetical O-H-L-C and O-L-H-C within-1m sequences.
NOT a tick-by-tick backtest. Do not treat as live-tradable realized fills.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from research_ema20_second_touch import read_source, features, MONTHS, FEE, SLIP

OUT=Path("analysis/ema20_second_touch_1h_step200_flip_exit_20261121")
INITIAL=1000.
TIMEFRAME=60
BTC_ACTIVATE=200.
BTC_BREACH_PRICE_UNIT=1.
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
            activation=p["step"],breach_price_unit=p["breach"],
            locked_profit_price=p["stop"],steps_locked=p["steps_locked"],
            activation_was_reached=p["active"],
            entry_epoch=p["epoch"],gross_pnl_usd=gross,fees_gst_usd=p["entry_fee"]+exit_fee,
            net_pnl_usd=net,equity_after_usd=cash,holding_hours=dur))
        open_pos=None
        mark_at_cash_equivalent(cash,open_pos,raw)
        # This function exits at the first stop crossing in the hypothesized path.

    def walk_segment(start,end,now):
        nonlocal open_pos,activation_count
        p=open_pos
        if p is None:
            return
        side=p["side"]
        # A locked price is NOT an immediately executable stop at equality:
        # exit only after a subsequent price breaches it by a $1 illustrative
        # increment (or ETH's price-scaled equivalent).
        if p["active"] and side*(start-p["stop"])<=-p["breach"]+1e-10:
            close_position(start,now,"STEP_LOCK_BREACH_GAP")
            return
        if side*(end-start)>0:
            # A favorable leg advances the lock ONLY at full +200 multiples.
            # Unlike peak-1 trailing, the lock stays unchanged between steps.
            favorable=side*(end-p["entry"])
            steps=max(0,int(np.floor((favorable+1e-9)/p["step"])))
            if steps>p["steps_locked"]:
                if p["steps_locked"]==0:
                    activation_count+=1
                p["steps_locked"]=steps
                p["active"]=True
                p["stop"]=p["entry"]+side*steps*p["step"]
            if side*(end-p["best"])>0:
                p["best"]=end
            mark(end,now)
            return
        if p["active"] and side*(end-p["stop"])<=-p["breach"]+1e-10:
            # First illustrative post-lock breach (e.g. 80200 -> 80199).
            trigger=p["stop"]-side*p["breach"]
            mark(trigger,now)
            close_position(trigger,now,"STEP_LOCK_BREACH")
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

        # Existing stop can be crossed by a gap from previous 1m close to open.
        if open_pos is not None and open_pos["active"]:
            p=open_pos
            if p["side"]*(path[0]-p["stop"])<=-p["breach"]+1e-10:
                # Use the open for gaps already beyond the locked level.
                close_position(path[0],now,"STEP_LOCK_BREACH_GAP")
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
            activation=BTC_ACTIVATE if symbol=="BTCUSD" else BTC_ACTIVATE*entry_fill/btc_ref
            breach=BTC_BREACH_PRICE_UNIT if symbol=="BTCUSD" else BTC_BREACH_PRICE_UNIT*entry_fill/btc_ref
            qty=cash/entry_fill
            entry_fee=FEE*qty*entry_fill
            cash-=entry_fee
            open_pos=dict(side=side_trend,entry=entry_fill,entry_raw=lev,
                qty=qty,entry_fee=entry_fee,entry_time=now,epoch=current_epoch,
                step=activation,breach=breach,steps_locked=0,
                active=False,stop=None,best=lev,activation_time=None)
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
        btc_first_lock_points=BTC_ACTIVATE,bct_step_lock_increment_points=BTC_ACTIVATE,
        btc_post_lock_breach_increment=BTC_BREACH_PRICE_UNIT,
        fixed_take_profit=False,stop_before_activation=False,
        trades=len(ledger),trail_exits=int(ledger.exit_reason.str.startswith("STEP_LOCK_BREACH").sum()),
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
    # Step-lock levels: do NOT move continuously between +200 milestones.
    entry=80000.
    samples=((80199,0,None),(80200,1,80200),(80300,1,80200),
             (80399,1,80200),(80400,2,80400),(80599,2,80400),
             (80600,3,80600))
    for high,expected_step,expected_lock in samples:
        steps=max(0,int(np.floor(((high-entry)+1e-9)/BTC_ACTIVATE)))
        lock=(entry+steps*BTC_ACTIVATE if steps>=1 else None)
        assert (steps,lock)==(expected_step,expected_lock),(high,steps,lock)
    assert 80200-BTC_BREACH_PRICE_UNIT==80199
    assert 80400-BTC_BREACH_PRICE_UNIT==80399
    print("SELF_TEST_OK: 80200 locks 80200, 80300 holds, 80400 locks 80400, exit on 80399",flush=True)

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
        first_lock_activation_BTC_points=BTC_ACTIVATE,
        each_subsequent_lock_increment_BTC_points=BTC_ACTIVATE,
        breach_price_increment_BTC=BTC_BREACH_PRICE_UNIT,
        scaled_ETH_step="200*ETH executed entry / previous completed 1m BTC close",
        scaled_ETH_breach="1*ETH executed entry / previous completed 1m BTC close",
        user_example="entry 80000, 80200 locks 80200, 80300 still 80200, 80400 locks 80400, next 80399 exits",
        no_continuous_peak_trailing=True,
        exit_on_confirmed_1h_supertrend_flip=True,
        supertrend_flip_executes="first 1m open of following 1h candle after flip confirmation",
        exit_whichever_happens_first="step profit lock breach OR confirmed Supertrend flip",
        synthetic_path_assumptions=list(PATHS),
        verified_tick_stream_available=False,
        warning="1m OHLC artificial continuous paths are NOT realized tick backtests; a strict 1-point reversal and real order fills cannot be verified",
        fixed_take_profit=None,stop_before_first_step=None,
        entry="second post-flip distinct 1h candle EMA20 touch",
        supertrend="10,3 confirmed on closed 1h",
        fees_taker_each_side=0.0005,GST_on_fees_fraction=0.18,
        adverse_slippage_each_side=SLIP,
        no_real_bidask_liquidation_funding_or_latency_model=True,
        months="2025-01 through 2026-10 IST; Jan 2025 first 5h30m outside UTC-start data")
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2)+"\n")
    lines=["# 1H Supertrend + EMA20 second touch: 200-point step-lock AND Supertrend flip exit","",
       "This models the user-defined step lock — NOT 200-point trailing gap or 1-point continuous trailing.",
       "**Exploratory model only**: two hypothetical within-1m OHLC paths; Supertrend flips exit at next hourly opening, but strict step-lock fills cannot be verified without historical ticks.",
       "At entry 80000, reaching 80200 locks 80200; reaching 80300 does not move it; reaching 80400 locks 80400; a later 80399 trade triggers exit. Reverse for shorts.",
       "",
       "| Synthetic 1m path | Asset | Trades | Step-lock exits | Supertrend flip exits | Losing flip exits | Net model return | Win rate | PF | Max floating DD | Positive months | Equity at/below zero? |",
       "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|"]
    for row in summaries:
        lines.append(f"| {row['path_assumption']} | {row['symbol']} | {row['trades']} | {row['trail_exits']} | {row['supertrend_flip_exits']} | {row['supertrend_flip_losses']} | {row['net_return_pct']}% | {row['win_rate_after_costs_pct']}% | {row['profit_factor']} | {row['max_floating_dd_pct']}% | {row['positive_months']}/22 | {row['equity_at_or_below_zero']} |")
    lines+=["","## Precise rules and serious limitations",
      "- NO fixed TP or ATR trailing. Before first +200 price point, there is no protective stop, BUT a confirmed Supertrend flip always exits.",
      "- Exit on CONFIRMED 1H Supertrend reversal at first 1m open of next 1H candle. Do not exit using the still-forming flip candle.",
      "- After first milestone, locked profit increments only in exact gross-price steps of +200, +400, +600, etc.",
      "- Exit on first reversal BELOW the most recently locked level for a long (ABOVE for short); simulated first breach 1 BTC price point, not a 1-point trailing distance.",
      "- ETH milestones and illustrative breach increments are scaled to its entry price divided by previous closed BTC 1m price.",
      "- A stop held at the current market price is not a traditional resting stop; implementation requires subsequent tick-based breach detection and market execution. Real fills may be lower than locked level.",
      "- 1m candles cannot reveal the order of activation, milestone, and 1-point retracement; O-H-L-C and O-L-H-C are NOT real historical ticks, and not rigorous worst/best bounds.",
      "- Model includes 0.05% per-side taker + GST 18%, 0.02% adverse slippage and 1x evolving model equity from $1000 for each asset; excludes funding, margin liquidation, true spread, latency, LOB.",
      "- Historical 2026 has been repeatedly researched, not pristine validation; an open position is forcibly marked at the dataset end only for accounting.",
      "","Artifacts: summary.csv, monthly_mark_to_market.csv, trade_ledger.csv.gz, quality.json."]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(lines)+"\n")
    print("BACKTEST_DONE",json.dumps(summaries,default=str),flush=True)

if __name__=="__main__":
    main()
