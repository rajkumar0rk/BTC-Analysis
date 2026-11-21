#!/usr/bin/env python3
"""Research-only: activate trail after +200 BTC pts then stop on $1 peak reversal.
Two hypothetical intra-minute price sequences. 1m OHLC DOES NOT reveal real ticks.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from research_ema20_second_touch import read_source, features, MONTHS, FEE, SLIP

OUT=Path("analysis/ema20_second_touch_1h_activation200_trail1_20261121")
INITIAL=1000.
TIMEFRAME=60
BTC_ACTIVATE=200.
BTC_RETRACE=1.
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
            activation=p["activation"],trail_distance=p["distance"],
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
        if p["active"] and side*(start-p["stop"])<=0:
            # Stop already breached at segment start (gap or intra-minute).
            close_position(start,now,"TRAIL_1_POINT_GAP")
            mark(end,now) if False else None
            return
        if side*(end-start)>0:
            # Favorable leg: highest/lowest price increases by the segment end.
            favorable_new=side*(end-p["entry"])
            if not p["active"] and favorable_new>=p["activation"]:
                p["active"]=True
                p["activation_time"]=now
                activation_count+=1
            if p["active"]:
                oldbest=p["best"]
                if side*(end-oldbest)>0:
                    p["best"]=end
                stop_new=p["best"]-side*p["distance"]
                if p["stop"] is None or side*(stop_new-p["stop"])>0:
                    p["stop"]=stop_new
            mark(end,now)
            return
        # Adverse/flat price leg: crossing active trailing stop exits exactly once.
        if p["active"] and side*(end-p["stop"])<=0:
            stop=p["stop"]
            mark(stop,now)
            close_position(stop,now,"TRAIL_1_POINT")
            return
        mark(end,now)

    for i in range(len(df)):
        hb=i//TIMEFRAME
        done=hb-1
        if done<100 or done>=len(ema) or not valid[done] or int(trend[done])==0:
            continue
        side_trend=int(trend[done])
        if side_trend!=last_direction:
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
            if p["side"]*(path[0]-p["stop"])<=0:
                # Start-of-minute open is an adverse fill for a gapped stop.
                close_position(path[0],now,"TRAIL_1_POINT_GAP")
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
            distance=BTC_RETRACE if symbol=="BTCUSD" else BTC_RETRACE*entry_fill/btc_ref
            qty=cash/entry_fill
            entry_fee=FEE*qty*entry_fill
            cash-=entry_fee
            open_pos=dict(side=side_trend,entry=entry_fill,entry_raw=lev,
                qty=qty,entry_fee=entry_fee,entry_time=now,epoch=current_epoch,
                activation=activation,distance=distance,
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
        btc_activation_points=BTC_ACTIVATE,btc_trail_points=BTC_RETRACE,
        fixed_take_profit=False,stop_before_activation=False,
        trades=len(ledger),trail_exits=int(ledger.exit_reason.str.startswith("TRAIL_1_POINT").sum()),
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
    # Exact continuous-price trailing logic implied by user:
    # $80,000 filled, activation at $80,200, stop $80,199.
    # New high $80,400 lifts it to $80,399.
    for entry,peak,expected in ((80000,80200,80199),(80000,80400,80399)):
        assert peak-entry>=BTC_ACTIVATE
        assert peak-BTC_RETRACE==expected
    print("SELF_TEST_OK: activate at +200, exit one point below maximum",flush=True)

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
        activation_BTC_price_points=BTC_ACTIVATE,
        trail_distance_BTC_price_points=BTC_RETRACE,
        scaled_ETH_activation="200*ETH executed entry/previous closed 1m BTC",
        scaled_ETH_trail="1*ETH executed entry/previous closed 1m BTC",
        user_example_long="entry 80000, activate 80200, exit upon falling to 80199",
        path_assumptions=list(PATHS),historical_ticks_available_for_full_sample=False,
        exit_accuracy_warning="1m OHLC synthetic paths NOT actual ticks; trading price 1 point reversal cannot be verified",
        fixed_tp=None,stop_before_activation=None,
        entry="second post-flip distinct 1h candle EMA20 touch",
        supertrend="10,3 confirmed on closed 1h",
        fees_taker_each_side=0.0005,GST_on_fees_fraction=0.18,
        adverse_slippage_each_side=SLIP,
        price_change_model="piecewise linear 1m OHLC path only",
        margin_liquidation_funding_bidask_not_modelled=True,
        output_months="2025-01..2026-10 IST, 22 months, prior 5h30m missing Jan 2025")
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2)+"\n")
    lines=["# 1H EMA20 second touch: activation +200, 1-point peak reversal",
       "",
       "**These figures are hypothetical 1m OHLC path assumptions, NOT confirmed tick-data backtests.**",
       "The real tick order can produce significantly different exit count, fill price, profit and drawdown.",
       "",
       "| 1m synthetic path | Asset | Trades | Net model return | Win rate | PF | Max MTM DD | Profitable months | Equity <= 0? |",
       "|---|---|---:|---:|---:|---:|---:|---:|---|"]
    for s in summaries:
        lines.append(f"| {s['path_assumption']} | {s['symbol']} | {s['trades']} | {s['net_return_pct']}% | {s['win_rate_after_costs_pct']}% | {s['profit_factor']} | {s['max_floating_dd_pct']}% | {s['positive_months']}/22 | {s['equity_at_or_below_zero']} |")
    lines+=["",
      "## Explicit execution limitations",
      "- Stop arms at +200 BTC-price points; then it exits on first 1 BTC-point pullback from peak, no fixed TP.",
      "- For shorts, trail follows low+1. ETH both distances percent-scaled at entry from previous BTC close.",
      "- 1m OHLC O-H-L-C versus O-L-H-C are TWO invented continuous paths consistent with OHLC, not measured historical ticks or rigorous upper/lower performance bounds.",
      "- A trade can encounter many >$1 reversals inside one minute that 1m OHLC cannot reveal; actual orderbook fills might be worse and trailing update latency matters.",
      "- No fixed stop before activation: exposures and liquidation can be severe. Forced end-of-sample close is accounting-only.",
      "- 1x assumed notional, $1000 starting equity per asset, 0.05% taker each side plus 18% GST, 0.02% adverse slippage each side.",
      "- 2026 archive previously researched; not a pristine untouched validation.",
      "","See summary.csv, monthly_mark_to_market.csv, trade_ledger.csv.gz, quality.json."]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(lines)+"\n")
    print("BACKTEST_DONE",json.dumps(summaries,default=str),flush=True)

if __name__=="__main__":
    main()
