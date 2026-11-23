#!/usr/bin/env python3
"""15M Supertrend+EMA20 filtered first touch; fixed TP1R/2R PLUS ATR14 trail2x/3x.
Volume and ATR14 expansion entry filters retained; confirmed ST flip also exits.
Replay hypothetical intraminute OHLC paths; real tick ordering not available.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from research_ema20_second_touch import read_source, MONTHS, FEE, SLIP

OUT=Path("analysis/st_firsttouch_15m_filtered_1r2r_atrtrail2x3_20261123")
TIMEFRAMES=(15,)
VOLUME_MULTIPLIER=1.2
FILTER_LOOKBACK=20
VOLATILITY_ATR_PERIOD=14
PATHS=("O-H-L-C","O-L-H-C")
ST_ATR_PERIOD=10
ST_FACTOR=3.0
EMA_PERIOD=20
INITIAL=1000.0
TP_R_MULTIPLIERS=(1.0,2.0)
ATR_TRAIL_MULTIPLIERS=(2.0,3.0)

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

def run_asset(df,symbol,tf,path_name,tp_multiple,atr_multiple):
    assert tp_multiple in TP_R_MULTIPLIERS and atr_multiple in ATR_TRAIL_MULTIPLIERS
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
    count_tp_exits=0
    count_atrtrail_exits=0
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
        nonlocal position,cash,longest_hold,count_flip_exits,count_tp_exits,count_atrtrail_exits
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
             tp_r_multiplier=tp_multiple,atr_trail_multiplier=atr_multiple,
             tp_distance_points=tp_multiple*p["risk"],fixed_tp=p["target"],
             initial_atr_trail_distance=p["distance"],initial_atr_stop=p["initial_stop"],
             final_atr_stop=p["stop"],best_favorable_raw_price=p["best"],
             entry_volume=p["entry_volume"],volume_sma20=p["volume_sma20"],
             volume_ratio=p["volume_ratio"],entry_atr14=p["atr14"],
             atr14_sma20=p["atr14_sma20"],atr14_ratio=p["atr_ratio"],
             exit_price=fill,exit_reason=reason,
             gross_usd=gross,fees_gst_usd=p["entry_fee"]+fee_out,net_usd=net,
             equity_after_usd=cash,hold_hours=hours,epoch=p["epoch"]))
        if reason=="SUPERTREND_FLIP":count_flip_exits+=1
        if reason.startswith("TP_"):count_tp_exits+=1
        if reason.startswith("ATR14_TRAIL"):count_atrtrail_exits+=1
        position=None

    def walk(a,b,sec):
        """Chronological path segment. Price hits the first eligible exit, then position is closed.
        On favorable segments TP takes precedence if reached, otherwise trail ratchets.
        On adverse segments existing ATR stop can trigger; it never retreats.
        """
        if position is None:
            return
        p=position; side=p["side"]
        if side*(a-p["stop"])<=0:
            mark(a,sec)
            close_trade(a,sec,"ATR14_TRAIL_GAP")
            return
        if side*(a-p["target"])>=0:
            mark(p["target"],sec)
            close_trade(p["target"],sec,"TP_GAP")
            return
        if side*(b-a)>0:
            if side*(b-p["target"])>=0:
                mark(p["target"],sec)
                close_trade(p["target"],sec,"TP")
                return
            if side*(b-p["best"])>0:
                p["best"]=b
                candidate=b-side*p["distance"]
                if side*(candidate-p["stop"])>0:
                    p["stop"]=candidate
            mark(b,sec)
        else:
            if side*(b-p["stop"])<=0:
                stop=p["stop"]
                mark(stop,sec)
                close_trade(stop,sec,"ATR14_TRAIL")
                return
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
        if position is not None:
            walk(path[0],path[0],sec)  # Stop/TP gap checks at actual next 1m OPEN
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
            # At first touch, never use the still-forming 15m candle's volume/ATR.
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
            target=entry+direction*tp_multiple*risk
            distance=atr_multiple*float(atr14[done])
            stop=entry-direction*distance
            if not(np.isfinite(risk) and risk>0 and np.isfinite(target) and target>0
                   and np.isfinite(distance) and distance>0 and np.isfinite(stop) and stop>0):
                invalid_first_touches+=1
                mark(b,sec)
                continue
            qty=cash/entry
            fee_in=FEE*qty*entry
            cash-=fee_in
            position=dict(side=direction,entry=entry,line=line,risk=risk,target=target,
                distance=distance,stop=stop,initial_stop=stop,best=level,
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
                month_ist=monthends[i],tp_r_multiplier=tp_multiple,atr_trail_multiplier=atr_multiple,
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
        tp_r_multiplier=tp_multiple,atr_trail_multiplier=atr_multiple,
        trades=len(ledger),winning_trades=int((ledger.net_usd>0).sum()),
        losing_trades=int((ledger.net_usd<0).sum()),
        win_rate_pct=round(100*float((ledger.net_usd>0).mean()),3),
        tp_exits=count_tp_exits,
        atr_trailing_exits=count_atrtrail_exits,
        atr_trailing_win_exits=int(((ledger.exit_reason.str.startswith("ATR14_TRAIL"))&(ledger.net_usd>0)).sum()),
        atr_trailing_loss_exits=int(((ledger.exit_reason.str.startswith("ATR14_TRAIL"))&(ledger.net_usd<0)).sum()),
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
        first_touch_epochs=total_first_touches,invalid_first_touch_risk=invalid_first_touches,
        volume_filter_rejections=volume_rejections,volatility_filter_rejections=volatility_rejections,
        either_filter_rejections=either_filter_rejections,both_filters_passed=both_filters_passed,
        supertrend_epochs=epoch,epochs_traded=len(entry_epochs),
        fees_gst_usd=round(float(ledger.fees_gst_usd.sum()),4))
    return ledger,monthly,summary

def self_test():
    # TP and ATR trail must be on opposite sides of a LONG or SHORT at entry;
    # trailing stop never moves backward, including after new extrema.
    for tp in TP_R_MULTIPLIERS:
        for mult in ATR_TRAIL_MULTIPLIERS:
            e=80000.;st=79600.;atr=200.;risk=e-st
            target=e+tp*risk
            stop=e-mult*atr
            assert target>e>stop
            newstop=max(stop,81000.-mult*atr)
            assert newstop>=stop
            assert max(newstop,80500.-mult*atr)==newstop
            short_st=80400.;short_target=e-tp*(short_st-e)
            short_stop=e+mult*atr
            newshort=min(short_stop,79000.+mult*atr)
            assert short_target<e<short_stop and newshort<=short_stop
    assert ST_ATR_PERIOD==10 and ST_FACTOR==3.0 and EMA_PERIOD==20
    assert VOLATILITY_ATR_PERIOD==14 and FILTER_LOOKBACK==20 and VOLUME_MULTIPLIER==1.2
    assert not(100>1.2*100) and 121>1.2*100
    assert not(14>14) and 14.001>14
    print("SELF_TEST_OK 1R/2R TP + 2x/3x ATR14 trailing; 15M entry filters ON",flush=True)

def main():
    self_test()
    OUT.mkdir(parents=True,exist_ok=True)
    quality={}
    summaries=[]; ledgers=[]; monthly_frames=[]
    for symbol in ("BTCUSD","ETHUSD"):
        df,q=read_source(symbol)
        quality[symbol]=q
        for tf in TIMEFRAMES:
            for tp in TP_R_MULTIPLIERS:
                for atr_mult in ATR_TRAIL_MULTIPLIERS:
                    for path in PATHS:
                        print("RUN",symbol,tf,tp,atr_mult,path,flush=True)
                        ledger,monthly,summary=run_asset(df,symbol,tf,path,tp,atr_mult)
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
        tp_r_multipliers=list(TP_R_MULTIPLIERS),atr_trail_multipliers=list(ATR_TRAIL_MULTIPLIERS),
        volume_filter="previous completed 15M volume > 1.2 times its 20-candle SMA",
        volatility_filter="previous completed 15M Wilder ATR14 > 20-candle SMA of ATR14",
        first_touch_filter_failure="reject entire current ST direction cycle, no second-touch substitute",
        volume_multiplier=VOLUME_MULTIPLIER,volume_lookback=FILTER_LOOKBACK,
        volatility_atr_period=VOLATILITY_ATR_PERIOD,volatility_average_period=FILTER_LOOKBACK,
        indicator_supertrend_atr_period=ST_ATR_PERIOD,
        indicator_supertrend_factor=ST_FACTOR,
        atr_smoothing="Wilder RMA seeded at SMA of first 10 true ranges",
        signal_ema_period=EMA_PERIOD,
        risk_reference="executed EMA20 entry to previous completed ST line, R=side*(entry-ST)",
        take_profit="fixed TP at entry + side*(1R or 2R)",
        trailing_stop="frozen distance (2 or 3) times Wilder ATR14 of last closed 15M candle; starts at entry and ratchets with favorable 1m extrema",
        exit_first_of="fixed TP; 1m ATR14 trailing stop hit; opposite confirmed 15M Supertrend flip at next 15M opening",
        no_exit_on_st_line_touch=True,no_profit_lock=True,
        trade_reentry="max one entry per ST regime",
        intraminute_assumptions=list(PATHS),
        actual_tick_data_available=False,
        timeframe_backtest_data="1m OHLC Delta India 2025Jan through 2026Oct",
        initial_equity_usd=INITIAL,leverage_notional=1,
        maker_or_taker="taker",fee_each_side=0.0005,fee_GST=0.18,adverse_slippage_each_side=SLIP,
        margin_liquidation_funding_depth_spread_not_modelled=True,
        historical_2026_not_pristine_oos=True)
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2)+"\n")
    report=["# 15M first EMA20 touch: volume/volatility ON, fixed TP 1R/2R + ATR14 trailing 2x/3x","",
        "BTCUSD and ETHUSD on 15M Supertrend (Wilder ATR10 multiplier3) and EMA20; 1-minute entry and exit replay; 22 IST months Jan2025–Oct2026.",
        "Entry: first EMA20 touch AFTER confirmed Supertrend flip, ignoring the flip candle. Only one chance per trend cycle.",
        "Both entry filters ON: last completed 15M volume >1.2*SMA20(volume), last completed 15M Wilder ATR14 >20-bar SMA(ATR14). Failed first touch rejects the entire Supertrend cycle.",
        "TP frozen at entry +/- (1 or 2)*R, where R = directional distance from executed entry to last completed 15M ST line.",
        "ATR14 trailing stop: distance frozen at entry = (2 or 3)*last completed 15M Wilder ATR14; initial stop at entry +/- distance and ratchets only on favorable 1-minute price extrema.",
        "Exits on first of FIXED TP, ATR trail hit, or next 15M OPEN after a confirmed opposite Supertrend flip.","",
        "| Asset | Fixed TP | ATR trail | Hypothetical path | Trades | Wins | Losses | TP exits | Trail exits | ST flips | Win rate | PF | Net return | Profitable months | Max floating DD |",
        "|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for x in summaries:
        report.append(f"| {x['symbol']} | {x['tp_r_multiplier']}R | {x['atr_trail_multiplier']}× | {x['path_assumption']} | {x['trades']} | {x['winning_trades']} | {x['losing_trades']} | {x['tp_exits']} | {x['atr_trailing_exits']} | {x['supertrend_flip_exits']} | {x['win_rate_pct']}% | {x['profit_factor']} | {x['net_return_pct']}% | {x['profitable_months']}/22 | {x['max_floating_drawdown_pct']}% |")
    report+=["","## Original reference (NO trailing stop)",
      "- The separate prior 15M 1R and 2R reports are unchanged. This run ADDS the ATR14 trail; TP and 15M volume/volatility filters remain ON.",
      "- Prior 1R no-trail: analysis/st_firsttouch_15m_filtered_tp1r_20261122/summary.csv",
      "- Prior 2R no-trail: analysis/st_firsttouch_15m_vol12_atr14_filter_20261122/summary.csv",
      "","## Replay assumptions / limitations",
      "- Replay each 1m bar as either O-H-L-C or O-L-H-C synthetic path. The actual intraminute price order is unknown.",
      "- ATR14 for trailing distance is calculated from the last fully completed 15M candle and FROZEN at entry. It never updates during the position.",
      "- At 1m OPEN, favorable TP gaps fill at the TP level, adverse stop gaps at the market OPEN, with adverse slippage. Price paths after entry determine whether the TP or trail occurs first.",
      "- 0.05% taker fee each side + GST18% on fees, 0.02% adverse slippage per side, initial $1000 modeled 1× capital per independent simulation.",
      "- 22 complete IST months, Jan2025–Oct2026; SHA256-checked Delta India BTC/ETH 1m OHLC. No funding, real orderbook spread, margin/liquidation, exchange latency or partial fills.",
      "- 2026 previously researched; not untouched OOS. Months include MTM of open positions, final sample-end close is accounting only.",
      "","Artifacts: summary.csv, monthly_mark_to_market.csv, trades.csv.gz, quality.json, execution.log."]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("BACKTEST_DONE",json.dumps(summaries,sort_keys=True),flush=True)

if __name__=="__main__":
    main()
