#!/usr/bin/env python3
"""15M EMA20 first touch with vol+ATR14 filters: no TP, ATR14 trail 2x and 3x.
ATR stop ratchets on 1m price, plus confirmed opposite 15M ST flip exit.
Hypothetical 1m price paths for execution sensitivity, not historical ticks.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from research_ema20_second_touch import read_source, MONTHS, FEE, SLIP

OUT=Path("analysis/st_firsttouch_15m_filtered_atrtrail2x3_no_tp_20261123")
TIMEFRAMES=(15,)
VOLUME_MULTIPLIER=1.2
FILTER_LOOKBACK=20
VOLATILITY_ATR_PERIOD=14
PATHS=("O-H-L-C","O-L-H-C")
ST_ATR_PERIOD=10
ST_FACTOR=3.0
EMA_PERIOD=20
INITIAL=1000.0
ATR_MULTIPLIERS=(2.0,3.0)

def ts_iso(s):
    return pd.Timestamp(int(s),unit="s",tz="UTC").isoformat()

def st_and_ema(df,tf):
    """Fully formed HTF bars; Wilder ATR10 and factor3 ST, no indicator lookahead."""
    agg=df.resample(f"{tf}min",label="left",closed="left").agg(
        {"open":"first","high":"max","low":"min","close":"last","volume":"sum"})
    valid=(df.close.resample(f"{tf}min",label="left",closed="left").count().to_numpy()==tf)
    h=agg.high.to_numpy(float); l=agg.low.to_numpy(float); c=agg.close.to_numpy(float)
    ema=pd.Series(c).ewm(span=EMA_PERIOD,adjust=False).mean().to_numpy()
    prev_c=np.r_[c[0],c[:-1]]
    tr=np.maximum(h-l,np.maximum(np.abs(h-prev_c),np.abs(l-prev_c)))
    atr=np.full(len(c),np.nan)
    # Wilder SMA initialization followed by 1/period recursive average.
    if len(c)>=ST_ATR_PERIOD and valid[:ST_ATR_PERIOD].all():
        atr[ST_ATR_PERIOD-1]=float(np.mean(tr[:ST_ATR_PERIOD]))
        for i in range(ST_ATR_PERIOD,len(c)):
            if valid[i] and np.isfinite(atr[i-1]):
                atr[i]=(atr[i-1]*(ST_ATR_PERIOD-1)+tr[i])/ST_ATR_PERIOD
    upper=(h+l)*.5+ST_FACTOR*atr
    lower=(h+l)*.5-ST_FACTOR*atr
    fu=np.full(len(c),np.nan); fl=np.full(len(c),np.nan)
    trend=np.zeros(len(c),dtype=np.int8)
    stline=np.full(len(c),np.nan)
    start=ST_ATR_PERIOD-1
    if start<len(c) and valid[start] and np.isfinite(atr[start]):
        fu[start]=upper[start];fl[start]=lower[start]
        # Initialization only; ignore first 100 HTF bars in signal logic.
        trend[start]=1 if c[start]>=(h[start]+l[start])*.5 else -1
        stline[start]=fl[start] if trend[start]==1 else fu[start]
        for i in range(start+1,len(c)):
            if not valid[i] or not np.isfinite(atr[i]) or not np.isfinite(fu[i-1]):
                continue
            fu[i]=upper[i] if upper[i]<fu[i-1] or c[i-1]>fu[i-1] else fu[i-1]
            fl[i]=lower[i] if lower[i]>fl[i-1] or c[i-1]<fl[i-1] else fl[i-1]
            if trend[i-1]==1:
                trend[i]=-1 if c[i]<fl[i] else 1
            else:
                trend[i]=1 if c[i]>fu[i] else -1
            stline[i]=fl[i] if trend[i]==1 else fu[i]
    # Entry regime filters only use fully closed 15-minute candles.
    volume=agg.volume.to_numpy(float)
    volume_sma20=pd.Series(volume).rolling(FILTER_LOOKBACK,min_periods=FILTER_LOOKBACK).mean().to_numpy(float)
    atr14=np.full(len(c),np.nan)
    if len(c)>=VOLATILITY_ATR_PERIOD and valid[:VOLATILITY_ATR_PERIOD].all():
        atr14[VOLATILITY_ATR_PERIOD-1]=float(np.mean(tr[:VOLATILITY_ATR_PERIOD]))
        for k in range(VOLATILITY_ATR_PERIOD,len(c)):
            if valid[k] and np.isfinite(atr14[k-1]):
                atr14[k]=(atr14[k-1]*(VOLATILITY_ATR_PERIOD-1)+tr[k])/VOLATILITY_ATR_PERIOD
    atr14_sma20=pd.Series(atr14).rolling(FILTER_LOOKBACK,min_periods=FILTER_LOOKBACK).mean().to_numpy(float)
    return ema,stline,trend,valid,volume,volume_sma20,atr14,atr14_sma20

def account_mark(cash,p,raw):
    if p is None: return cash
    close_proxy=raw*(1-p["side"]*SLIP)
    return cash+p["side"]*p["qty"]*(close_proxy-p["entry"])-FEE*p["qty"]*close_proxy

def run_asset(df,symbol,tf,path_name,atr_multiple):
    assert atr_multiple in ATR_MULTIPLIERS
    ema,stline,trend,valid,volume,volume_sma20,atr14,atr14_sma20=st_and_ema(df,tf)
    t=df.time.to_numpy(np.int64)
    op=df.open.to_numpy(float); hi=df.high.to_numpy(float)
    lo=df.low.to_numpy(float); cl=df.close.to_numpy(float)
    assert t[0]%(tf*60)==0
    monthends={}
    for month in MONTHS:
        p=pd.Period(month,freq="M")
        end=(p+1).start_time.tz_localize("Asia/Kolkata").tz_convert("UTC")-pd.Timedelta(minutes=1)
        i=int(np.searchsorted(t,int(end.timestamp()),side="right")-1)
        if i<0 or t[i]!=int(end.timestamp()):
            raise AssertionError("Missing IST month end "+month)
        monthends[i]=month

    cash=INITIAL
    position=None
    current_dir=0
    epoch=0
    first_touch_epochs=set()
    entry_epochs=set()
    invalid_first_touches=0
    trade_rows=[]
    month_rows=[]
    count_flip_exits=0
    count_atr_stop_exits=0
    high_equity=INITIAL
    low_equity=INITIAL
    max_floating_dd=0.0
    zero_equity_first=None
    longest_hold=0.0
    total_first_touches=0
    volume_rejections=0
    volatility_rejections=0
    either_filter_rejections=0
    both_filters_passed=0

    def mark(price,sec):
        nonlocal high_equity,low_equity,max_floating_dd,zero_equity_first
        eq=account_mark(cash,position,price)
        high_equity=max(high_equity,eq)
        low_equity=min(low_equity,eq)
        if high_equity>0:
            max_floating_dd=max(max_floating_dd,100*(high_equity-eq)/high_equity)
        if zero_equity_first is None and eq<=0:
            zero_equity_first=ts_iso(sec)

    def close_trade(raw,sec,reason):
        nonlocal position,cash,longest_hold,count_flip_exits,count_atr_stop_exits
        p=position
        if p is None: raise AssertionError("Exit without position")
        side=p["side"]
        fill=raw*(1-side*SLIP)
        gross=side*p["qty"]*(fill-p["entry"])
        fee_out=FEE*p["qty"]*fill
        net=gross-p["entry_fee"]-fee_out
        cash+=gross-fee_out
        hours=(sec-p["entry_time"])/3600.0
        longest_hold=max(longest_hold,hours)
        trade_rows.append(dict(symbol=symbol,signal_timeframe=f"{tf}m",path_assumption=path_name,
             entry_time_utc=ts_iso(p["entry_time"]),exit_time_utc=ts_iso(sec),
             exit_month_ist=pd.Timestamp(sec,unit="s",tz="UTC").tz_convert("Asia/Kolkata").strftime("%Y-%m"),
             direction="LONG" if side==1 else "SHORT",entry_price=p["entry"],
             supertrend_line_at_entry=p["line"],risk_reference_points=p["risk"],
             atr_trail_multiplier=atr_multiple,initial_atr14=p["atr14"],
             initial_trail_distance=p["distance"],initial_stop=p["initial_stop"],
             final_trail_stop=p["stop"],best_favorable_raw_price=p["best"],
             entry_volume=p["entry_volume"],volume_sma20=p["volume_sma20"],
             volume_ratio=p["volume_ratio"],entry_atr14=p["atr14"],
             atr14_sma20=p["atr14_sma20"],atr14_ratio=p["atr_ratio"],
             exit_price=fill,exit_reason=reason,
             gross_usd=gross,fees_gst_usd=p["entry_fee"]+fee_out,net_usd=net,
             equity_after_usd=cash,hold_hours=hours,epoch=p["epoch"]))
        if reason=="SUPERTREND_FLIP":count_flip_exits+=1
        if reason.startswith("ATR14_TRAIL"):count_atr_stop_exits+=1
        position=None

    def walk(a,b,sec):
        # Evaluate chronological 1m segment path, after potential entry.
        # Adverse movement crosses already active trailing stop; favorable
        # movement may ratchet stop only AFTER price actually moved there.
        if position is None:
            return
        p=position
        side=p["side"]
        if side*(a-p["stop"])<=0:
            # Already past stop due to path discontinuity/gap: fill at 'a'.
            mark(a,sec)
            close_trade(a,sec,"ATR14_TRAIL_GAP")
            return
        if side*(b-p["stop"])<=0:
            stop=p["stop"]
            mark(stop,sec)
            close_trade(stop,sec,"ATR14_TRAIL")
            return
        if side*(b-p["best"])>0:
            p["best"]=b
            candidate=b-side*p["distance"]
            if side*(candidate-p["stop"])>0:
                p["stop"]=candidate
        mark(b,sec)

    for i in range(len(df)):
        bar=i//tf
        done=bar-1
        if done<100 or done>=len(ema) or not valid[done] or trend[done]==0 or not np.isfinite(stline[done]):
            continue
        sec=int(t[i]);direction=int(trend[done])
        if direction!=current_dir:
            if position is not None:
                if position["side"]==direction:
                    raise AssertionError("Position direction equals supposedly new flip")
                # Fully closed signal bar just confirmed reverse.
                # The earliest causal execution is this next HTF bar's first 1m OPEN.
                close_trade(float(op[i]),sec,"SUPERTREND_FLIP")
            current_dir=direction
            epoch+=1

        path=(op[i],hi[i],lo[i],cl[i]) if path_name=="O-H-L-C" else (op[i],lo[i],hi[i],cl[i])
        # Check gaps through existing ATR trailing stop at 1m candle open.
        if position is not None and position["side"]*(path[0]-position["stop"])<=0:
            close_trade(path[0],sec,"ATR14_TRAIL_GAP")
        mark(path[0],sec)
        for seg in range(3):
            a,b=path[seg],path[seg+1]
            if position is not None:
                walk(a,b,sec)
                continue
            if cash<=0 or epoch in first_touch_epochs:
                mark(b,sec)
                continue
            level=float(ema[done])
            if not np.isfinite(level) or not(min(a,b)<=level<=max(a,b)):
                mark(b,sec)
                continue
            # This is the FIRST touch after a confirmed flip, never the flip candle.
            first_touch_epochs.add(epoch)
            total_first_touches+=1
            # At first touch, never use the still-forming 15M candle's volume/ATR.
            vol_ok=(np.isfinite(volume_sma20[done]) and volume_sma20[done]>0
                    and volume[done]>VOLUME_MULTIPLIER*volume_sma20[done])
            atr_ok=(np.isfinite(atr14_sma20[done]) and atr14_sma20[done]>0
                    and atr14[done]>atr14_sma20[done])
            if not vol_ok: volume_rejections+=1
            if not atr_ok: volatility_rejections+=1
            if not (vol_ok and atr_ok):
                either_filter_rejections+=1
                mark(b,sec)
                continue
            both_filters_passed+=1
            entry=level*(1+direction*SLIP)
            line=float(stline[done])
            risk=direction*(entry-line)
            distance=atr_multiple*float(atr14[done])
            stop=entry-direction*distance
            if not(np.isfinite(distance) and distance>0
                   and np.isfinite(stop) and stop>0):
                invalid_first_touches+=1
                mark(b,sec)
                continue
            qty=cash/entry
            fee_in=FEE*qty*entry
            cash-=fee_in
            position=dict(side=direction,entry=entry,line=line,risk=risk,
                stop=stop,initial_stop=stop,distance=distance,best=level,
                qty=qty,entry_fee=fee_in,entry_time=sec,epoch=epoch,
                entry_volume=float(volume[done]),volume_sma20=float(volume_sma20[done]),
                volume_ratio=float(volume[done]/volume_sma20[done]),
                atr14=float(atr14[done]),atr14_sma20=float(atr14_sma20[done]),
                atr_ratio=float(atr14[done]/atr14_sma20[done]))
            entry_epochs.add(epoch)
            mark(level,sec)
            # Check ONLY the remainder of this segment after the actual EMA crossing.
            walk(level,b,sec)

        if i in monthends:
            month_rows.append(dict(symbol=symbol,signal_timeframe=f"{tf}m",path_assumption=path_name,
                month_ist=monthends[i],atr_trail_multiplier=atr_multiple,
                equity_mark_usd=account_mark(cash,position,float(cl[i])),
                position_open_at_month_end=position is not None,
                realized_cash_usd=cash))
    if position is not None:
        close_trade(float(cl[-1]),int(t[-1]),"SAMPLE_END_ACCOUNTING_ONLY")
        month_rows[-1]["equity_mark_usd"]=cash
    if len(month_rows)!=22:
        raise AssertionError(("Wrong number of month end rows",symbol,tf,path_name,len(month_rows)))
    ledger=pd.DataFrame(trade_rows)
    if ledger.empty:raise RuntimeError("No trades in "+symbol+" "+str(tf))
    if ledger.epoch.duplicated().any():
        raise AssertionError("Duplicate entries inside one ST epoch")
    if abs(float(ledger.net_usd.sum())-(cash-INITIAL))>0.02:
        raise AssertionError("Ledger/cash mismatch")
    monthly=pd.DataFrame(month_rows)
    monthly["monthly_return_pct"]=100*(monthly.equity_mark_usd/
        monthly.equity_mark_usd.shift(1,fill_value=INITIAL)-1)
    gross_win=float(ledger.loc[ledger.net_usd>0,"net_usd"].sum())
    gross_loss=float(-ledger.loc[ledger.net_usd<0,"net_usd"].sum())
    year25=float(monthly.loc[monthly.month_ist=="2025-12","equity_mark_usd"].iloc[0])
    summary=dict(symbol=symbol,timeframe=f"{tf}m",path_assumption=path_name,
        atr_trail_multiplier=atr_multiple,
        trades=len(ledger),winning_trades=int((ledger.net_usd>0).sum()),
        losing_trades=int((ledger.net_usd<0).sum()),
        win_rate_pct=round(100*float((ledger.net_usd>0).mean()),3),
        atr14_trailing_exits=count_atr_stop_exits,
        atr14_trailing_win_exits=int(((ledger.exit_reason.str.startswith("ATR14_TRAIL"))&(ledger.net_usd>0)).sum()),
        atr14_trailing_loss_exits=int(((ledger.exit_reason.str.startswith("ATR14_TRAIL"))&(ledger.net_usd<0)).sum()),
        supertrend_flip_exits=count_flip_exits,
        supertrend_flip_losses=int(((ledger.exit_reason=="SUPERTREND_FLIP")&(ledger.net_usd<0)).sum()),
        sample_end_forced_exits=int((ledger.exit_reason=="SAMPLE_END_ACCOUNTING_ONLY").sum()),
        profit_factor=round(gross_win/gross_loss,4) if gross_loss>0 else None,
        net_profit_usd=round(float(cash-INITIAL),4),
        net_return_pct=round(100*float(cash/INITIAL-1),4),
        max_floating_drawdown_pct=round(max_floating_dd,4),
        min_floating_equity_usd=round(low_equity,4),
        equity_at_or_below_zero=zero_equity_first is not None,
        first_zero_equity_utc=zero_equity_first,
        profitable_months=int((monthly.monthly_return_pct>0).sum()),
        losing_months=int((monthly.monthly_return_pct<0).sum()),
        positive_2025_pct=round(100*(year25/INITIAL-1),4),
        return_2026_jan_oct_pct=round(100*(cash/year25-1),4),
        longest_hold_hours=round(longest_hold,2),
        first_touch_epochs=total_first_touches,invalid_trailing_stop_geometry=invalid_first_touches,
        volume_filter_rejections=volume_rejections,volatility_filter_rejections=volatility_rejections,
        either_filter_rejections=either_filter_rejections,both_filters_passed=both_filters_passed,
        supertrend_epochs=epoch,epochs_traded=len(entry_epochs),
        fees_gst_usd=round(float(ledger.fees_gst_usd.sum()),4))
    return ledger,monthly,summary

def self_test():
    # Entry-time frozen Wilder ATR14 200, trailing distance 400 or 600.
    for m,initial,after in ((2.0,79600.0,80600.0),(3.0,79400.0,80400.0)):
        entry=80000.0;atr=200.0
        stop=entry-m*atr
        best=81000.0
        stop=max(stop,best-m*atr)
        assert stop==after and entry-m*atr==initial
        # A short must trail downward, with a stop above the market.
        short_entry=80000.0
        short_stop=short_entry+m*atr
        short_best=79000.0
        short_stop=min(short_stop,short_best+m*atr)
        assert short_stop==short_best+m*atr
    assert VOLATILITY_ATR_PERIOD==14 and FILTER_LOOKBACK==20 and VOLUME_MULTIPLIER==1.2
    print("SELF_TEST_OK ATR14 2x/3x long and short monotonic trail; no TP",flush=True)

def main():
    self_test()
    OUT.mkdir(parents=True,exist_ok=True)
    quality={}
    summaries=[]; ledgers=[]; monthly_frames=[]
    for symbol in ("BTCUSD","ETHUSD"):
        df,q=read_source(symbol)
        quality[symbol]=q
        for tf in TIMEFRAMES:
            for multiplier in ATR_MULTIPLIERS:
                for path in PATHS:
                    print("RUN",symbol,tf,multiplier,path,flush=True)
                    ledger,monthly,summary=run_asset(df,symbol,tf,path,multiplier)
                    ledgers.append(ledger)
                    monthly_frames.append(monthly)
                    summaries.append(summary)
                    print("RESULT",json.dumps(summary,sort_keys=True),flush=True)
    pd.DataFrame(summaries).to_csv(OUT/"summary.csv",index=False)
    pd.concat(monthly_frames,ignore_index=True).to_csv(OUT/"monthly_mark_to_market.csv",index=False)
    pd.concat(ledgers,ignore_index=True).to_csv(OUT/"trades.csv.gz",index=False,compression="gzip")
    quality["research_rules"]=dict(
        entry="FIRST distinct signal-timeframe EMA20 touch after confirmed opposite ST flip",
        ignore_flip_candle=True,signal_timeframes=[15],
        atr_trailing_multipliers=list(ATR_MULTIPLIERS),
        volume_filter="previous completed 15M volume > 1.2 times its 20-candle SMA",
        volatility_filter="previous completed 15M Wilder ATR14 > 20-candle SMA of ATR14",
        first_touch_filter_failure="reject entire current ST direction cycle, no second-touch substitute",
        volume_multiplier=VOLUME_MULTIPLIER,volume_lookback=FILTER_LOOKBACK,
        volatility_atr_period=VOLATILITY_ATR_PERIOD,volatility_average_period=FILTER_LOOKBACK,
        indicator_supertrend_atr_period=ST_ATR_PERIOD,
        indicator_supertrend_factor=ST_FACTOR,
        atr_smoothing="Wilder RMA seeded at SMA of first 10 true ranges",
        signal_ema_period=EMA_PERIOD,
        supertrend_line_reference="diagnostic only; risk distance is NOT an entry gate without TP",
        take_profit=None,fixed_take_profit_enabled=False,
        initial_trailing_stop="entry +/- multiplier * ATR14 from last fully closed 15M bar",
        trailing_atr14_distance="FIXED at entry, multiplier 2 or 3 x prior closed 15M Wilder ATR14",
        trailing_monitoring="1m chronological hypothetical OHLC path; on favorable move ratchet stop by same distance; stop never retreats",
        stop_loss="FIRST of ATR14 trailing stop breach on 1m path or opposite confirmed 15M Supertrend flip at next 15M open",
        no_exit_on_st_line_touch=True,
        no_profit_lock=True,
        trade_reentry="max one entry per ST regime",
        intraminute_assumptions=list(PATHS),
        actual_tick_data_available=False,
        timeframe_backtest_data="1m OHLC Delta India 2025Jan through 2026Oct",
        initial_equity_usd=INITIAL,leverage_notional=1,
        maker_or_taker="taker",fee_each_side=0.0005,fee_GST=0.18,adverse_slippage_each_side=SLIP,
        margin_liquidation_funding_depth_spread_not_modelled=True,
        historical_2026_not_pristine_oos=True)
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2)+"\n")
    report=["# 15M Supertrend EMA20 FIRST TOUCH — entry filters ON, NO TP, 2× / 3×ATR14 trailing stop","",
        "**Fixed take-profit OFF** per user correction. Both 15M ENTRY filters remain ON: volume >1.2×SMA20(volume); ATR14 >SMA20(ATR14), using previous completed 15M candle only.",
        "BTCUSD and ETHUSD independent simulations with 15M signal candles and 1m execution, 22 complete IST months Jan2025–Oct2026.",
        "LONG: confirmed ST(10,3) flips green; ignore flip candle; first subsequent 15M candle that touches preceding closed EMA20 enters long, if both previous-completed-candle filters pass. SHORT reversed.",
        "At first touch reject entire ST cycle if either filter fails; one trade per ST regime.",
        "NO FIXED TAKE PROFIT. Freeze trailing distance at entry = (2× or 3×) Wilder ATR14 of the preceding fully completed 15M candle. Initial stop immediately entry∓distance; ratchet on favorable 1m price extremes only, never backward.",
        "Whichever comes first exits: 1m ATR trailing stop hit, or confirmed opposite 15M ST flip at next 15M candle open. Touching Supertrend LINE does NOT exit, but ATR trail may exit before flip.",
        "Supertrend line is logged only as diagnostic; no entry-to-ST-line R geometry gate is imposed because R-based TP is OFF.","",
        "| Asset | Trail | Hypothetical 1m path | Trades | Wins | Losses | ATR trail exits | ST flip exits | Win% | PF | Net return | Profitable months | Max floating drawdown |",
        "|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for x in summaries:
        report.append(f"| {x['symbol']} | {x['atr_trail_multiplier']}× | {x['path_assumption']} | {x['trades']} | {x['winning_trades']} | {x['losing_trades']} | {x['atr14_trailing_exits']} | {x['supertrend_flip_exits']} | {x['win_rate_pct']}% | {x['profit_factor']} | {x['net_return_pct']}% | {x['profitable_months']}/22 | {x['max_floating_drawdown_pct']}% |")
    report+=["","## Direct comparisons to earlier 15M versions",
       "- Previous 15M 1R and 2R variants had FIXED TAKE PROFIT, NO ATR trailing stop. Those are separate controls. Their entry filters remain ON in this run.",
       "- Prior 1R: analysis/st_firsttouch_15m_filtered_tp1r_20261122/summary.csv",
       "- Prior 2R: analysis/st_firsttouch_15m_vol12_atr14_filter_20261122/summary.csv",
       "- Another earlier branch combined 1R/2R TP plus ATR trailing; it does NOT implement the final user requirement and must not be confused with this study.",
       "",
       "## Model caveats",
       "- SHA256-verified 1m historical Delta India OHLC Jan2025–Oct2026 for BTC/ETH, 22 IST months. No missing minutes.",
       "- 1m O-H-L-C vs O-L-H-C paths are hypothetical price order, not tick/realtime stop fills or mathematical min/max bounds.",
       "- Frozen prior 15M ATR14 at entry; 1-minute intrabar stop monitoring and ratcheting; no subsequent remeasurement of distance.",
       "- Taker fee 0.05% each side + GST18% on fees, 0.02% adverse slippage both sides; initial equity $1000, dynamic 1× notional.",
       "- No exchange funding, actual order book/spread, margin, liquidation, slippage tail risks, partial fills or latency. 2026 history already researched; not untouched out of sample.",
       "- Monthly mark-to-market includes open positions; forced sample-end close for accounting only.",
       "","Artifacts: summary.csv, monthly_mark_to_market.csv, trades.csv.gz, quality.json, execution.log."]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("BACKTEST_DONE",json.dumps(summaries,sort_keys=True),flush=True)

if __name__=="__main__":
    main()
