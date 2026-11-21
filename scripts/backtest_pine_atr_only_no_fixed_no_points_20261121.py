#!/usr/bin/env python3
"""Reproduce user-corrected BTCUSD Pine v6 controls on a 1m chart; BOTH fixed-point trailing switches OFF.
15m EMA20 touch/reclaim + Supertrend ATR10 factor3; initial stop 3x 15m ATR14.
Mode ATR Only: useATR True, useFixed False, usePointTrail False. Custom
ATR14x3 on 1m, activated after favorable 200 BTCUSD price points;
NO native strategy.exit point trailing: trailing distance and additional
trailing-stop switches BOTH OFF. Historical 500/250/1000 point inputs
are inactive and must not affect results. ST flip exit ON. Entry/flip
at confirmed 15m signal close (process_orders_on_close=True). Both filters
OFF (Pine default; not specified in screenshots). Native trail repriced
intraminute using TradingView 1m broker emulator nearest-extreme OHLC path,
and opposite-path sensitivity. Custom ATR stop updated at completed 1m
close for subsequent 1m only (causal). Mark-trigger sensitivity is NOT Pine
parity, because Pine on BTCUSD traded candles uses traded OHLC.
Pine 1 TV contract = .001 BTC, 0.05% taker entry/exit, GST18%.
Default historical scalper offer: waive exit trading fee for holding<=30m;
also compare offer OFF; this is an unverified historical offer assumption.
Delta India PROD 1m archive Jan2025-Oct2026 and partial Nov16-21 current
IST week. No actual fills, spread, funding, latency, liquidation, wallet
depletion; historical native-stop intraminute execution is estimated.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from numba import njit
from current_week_100_300_initial9atr_20261121 import refresh_nov,WEEK_START,END
from full_history_1h_trailing_100_50_2025_2026 import read_asset
from replay_btc_ema_st_screenshot import indicators,rma
from optimize_1h_additional_trailing_stop_points_20261121 import stop_round

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"analysis"/"pine_atr_only_no_fixed_no_points_20261121"
OUT.mkdir(parents=True,exist_ok=True)
FULL_START=int(pd.Timestamp("2025-01-01",tz="UTC").timestamp())
FULL_END=int(pd.Timestamp("2026-11-01",tz="UTC").timestamp())
SPLIT=int(pd.Timestamp("2026-01-01",tz="UTC").timestamp())
MONTHS=[str(x) for x in pd.period_range("2025-01","2026-10",freq="M")]
FEE=.0005
GST=.18
QTY=.001
TICK=.5

def inputs():
    trade,mark,source=read_asset("BTC")
    times=trade.time.to_numpy(np.int64)
    n=int(np.searchsorted(times,END))
    trade=trade.iloc[:n];mark=mark.iloc[:n]
    ts=trade.time.to_numpy(np.int64)
    assert ts[0]==FULL_START and ts[-1]==END-60
    assert n%15==0 and np.all(np.diff(ts)==60)
    assert np.array_equal(ts,mark.time.to_numpy(np.int64))
    prev=trade.close.shift(1)
    tr=pd.concat([trade.high-trade.low,(trade.high-prev).abs(),(trade.low-prev).abs()],axis=1).max(axis=1)
    atr1m=rma(tr,14).to_numpy(np.float64)
    h=trade.resample("15min",origin="epoch",label="left",closed="left").agg({
      "open":"first","high":"max","low":"min","close":"last","volume":"sum","time":"count"})
    assert len(h)==n//15 and (h.time==15).all()
    ind=indicators(h.drop(columns=["time"]))
    signal=np.zeros(n,dtype=np.int8);flip=np.zeros(n,dtype=np.int8);atr15=np.zeros(n)
    for k in range(36,len(ind)):
        i=15*(k+1)-1
        d=int(ind.dir.iloc[k]);p=int(ind.dir.iloc[k-1])
        if d!=p:
            if p==-1 and d==1:flip[i]=1 # bearish flip -> close long
            if p==1 and d==-1:flip[i]=-1 # bullish flip -> close short
        if not np.isfinite(ind.atr14.iloc[k]):continue
        atr15[i]=float(ind.atr14.iloc[k])
        if d==p==-1 and ind.low.iloc[k]<=ind.ema.iloc[k] and ind.close.iloc[k]>ind.ema.iloc[k]:
            signal[i]=1
        elif d==p==1 and ind.high.iloc[k]>=ind.ema.iloc[k] and ind.close.iloc[k]<ind.ema.iloc[k]:
            signal[i]=-1
    assert int(np.count_nonzero(signal))>1000
    assert int(np.count_nonzero(flip))>1000
    assert np.isfinite(atr1m[35:]).all()
    return [
      ts,trade.open.to_numpy(np.float64),trade.high.to_numpy(np.float64),
      trade.low.to_numpy(np.float64),trade.close.to_numpy(np.float64),
      mark.open.to_numpy(np.float64),mark.high.to_numpy(np.float64),
      mark.low.to_numpy(np.float64),mark.close.to_numpy(np.float64),
      signal,flip,atr15,atr1m,
    ],{"minute_bars":n,"15m_bars":len(ind),"signal_count":int(np.count_nonzero(signal)),
       "supertrend_flip_events":int(np.count_nonzero(flip)),
       "last_1m_utc":str(trade.index[-1]),"original_data":source}

@njit(cache=True)
def execute(ts,to,th,tl,tc,mo,mh,ml,mc,signal,flip,atr15,atr1m,
            price_source,bar_path,scalper,native_enabled):
    # row: entry,exit,side,entrypx,exitpx,qty,gross,fees,gst,net,
    #       initialsl,customsl,nativestop,exitcode,minutes,updates,nativeactivated
    out=np.zeros((16000,17),dtype=np.float64)
    nout=0;active=0;side=0
    entry=0.;entry_t=0;custom=0.;initial=0.;best=0.;native_best=0.
    native=0.;native_on=0;edits=0
    skips=np.zeros(3,dtype=np.int64)
    for i in range(len(ts)):
        if price_source==0:
            o=to[i];hi=th[i];lo=tl[i];c=tc[i]
        else:
            o=mo[i];hi=mh[i];lo=ml[i];c=mc[i]
        ec=0;xp=0.
        was_open=active==1
        if was_open:
            eff=custom
            if native_on:
                eff=max(custom,native) if side==1 else min(custom,native)
            if (side==1 and o<=eff) or (side==-1 and o>=eff):
                ec=1;xp=to[i]
            else:
                high_first=(hi-o<o-lo)
                if bar_path==1:high_first=not high_first
                p2=hi if high_first else lo
                p3=lo if high_first else hi
                cur=o
                for nxt in (p2,p3,c):
                    if side*(nxt-cur)<0:
                        current=custom;which=3
                        if native_on:
                            better=(native>current) if side==1 else (native<current)
                            if better:current=native;which=2
                        if (side==1 and nxt<=current) or (side==-1 and nxt>=current):
                            ec=which;xp=current if price_source==0 else tc[i]
                            break
                    elif native_enabled and side*(nxt-cur)>0:
                        if not native_on:
                            if side*(nxt-entry)>=500.:
                                native_on=1;native_best=nxt
                                native=stop_round(native_best-side*1000.,TICK,side)
                        else:
                            new_best=max(native_best,nxt) if side==1 else min(native_best,nxt)
                            native_best=new_best
                            candidate=stop_round(native_best-side*1000.,TICK,side)
                            native=max(native,candidate) if side==1 else min(native,candidate)
                    cur=nxt
                # Pine confirmed entry-timeframe Supertrend flip is on 15m CLOSE
                if ec==0 and flip[i]==side:
                    ec=4;xp=tc[i]
            if ec==0:
                best=max(best,hi) if side==1 else min(best,lo)
                if side*(best-entry)>=200. and np.isfinite(atr1m[i]):
                    candidate=stop_round(best-side*3.*atr1m[i],TICK,side)
                    tighter=max(custom,candidate) if side==1 else min(custom,candidate)
                    if abs(tighter-custom)>=TICK*.5:edits+=1
                    custom=tighter
        if ec:
            hold=(ts[i]-entry_t)/60.
            gross=(xp-entry)*side*QTY
            opening=entry*QTY*FEE
            closing=xp*QTY*FEE
            if scalper and hold<=30.:closing=0.
            fee=opening+closing
            tax=fee*GST
            if nout>=len(out):raise RuntimeError("Exceeded result capacity")
            out[nout,0]=entry_t;out[nout,1]=ts[i];out[nout,2]=side
            out[nout,3]=entry;out[nout,4]=xp;out[nout,5]=QTY
            out[nout,6]=gross;out[nout,7]=fee;out[nout,8]=tax
            out[nout,9]=gross-fee-tax;out[nout,10]=initial
            out[nout,11]=custom;out[nout,12]=native if native_on else np.nan
            out[nout,13]=ec;out[nout,14]=hold;out[nout,15]=edits
            out[nout,16]=native_on
            nout+=1;active=0;native_on=0;edits=0
        # Pine process_orders_on_close=True: enter on close of 1m candle
        # that completes the signal's 15m candle; no use of its prior wick.
        if active==0 and signal[i]!=0:
            if atr15[i]>0 and np.isfinite(atr15[i]):
                active=1;side=signal[i];entry=tc[i];entry_t=ts[i]
                initial=stop_round(entry-side*3.*atr15[i],TICK,side)
                custom=initial;native_on=0;native=0.;native_best=entry
                best=entry;edits=0
            else:skips[0]+=1
        elif was_open and active and signal[i]!=0:skips[1]+=1
    return out[:nout],skips,active

def statistics(a):
    n=len(a);p=a[:,9] if n else np.empty(0)
    win=p[p>0];lose=p[p<0]
    eq=np.r_[0.,np.cumsum(p)]
    reasons=a[:,13] if n else np.empty(0)
    return {
      "net_usd":round(float(p.sum()),5),
      "gross_usd":round(float(a[:,6].sum()),5),
      "fees_usd":round(float(a[:,7].sum()),5),
      "gst_usd":round(float(a[:,8].sum()),5),
      "trades":int(n),"wins":int(len(win)),"losses":int(len(lose)),
      "win_rate_pct":round(100*len(win)/n,2) if n else None,
      "profit_factor":round(float(win.sum()/-lose.sum()),4) if len(lose) else None,
      "max_closed_trade_dd_usd":round(float(np.max(np.maximum.accumulate(eq)-eq)),5),
      "native_trail_exits":int((reasons==2).sum()),
      "custom_atr_or_gap_exits":int(((reasons==1)|(reasons==3)).sum()),
      "supertrend_flip_exits":int((reasons==4).sum()),
      "under30min_trades":int((a[:,14]<=30).sum()) if n else 0,
    }

def reports(a):
    t=a[:,1];full=a[(t>=FULL_START)&(t<FULL_END)]
    week=a[(t>=WEEK_START)&(t<END)]
    x={
      "full22":statistics(full),
      "year2025":statistics(full[full[:,1]<SPLIT]),
      "jan_oct2026":statistics(full[full[:,1]>=SPLIT]),
      "current_partial_week":statistics(week),
    }
    months=full[:,1].astype("int64").astype("datetime64[s]").astype("datetime64[M]")
    x["monthly"]=[{"month_utc":m,**statistics(full[months==np.datetime64(m,"M")])} for m in MONTHS]
    x["positive_months"]=sum(v["net_usd"]>0 for v in x["monthly"])
    ist=(week[:,1].astype("int64").astype("datetime64[s]")+np.timedelta64(330,"m")).astype("datetime64[D]")
    x["daily_ist"]=[{"date_ist":str(day.date()),
                    **statistics(week[ist==np.datetime64(str(day.date()))])}
                    for day in pd.date_range("2026-11-16","2026-11-21")]
    assert sum(v["trades"] for v in x["monthly"])==x["full22"]["trades"]
    assert abs(sum(v["net_usd"] for v in x["monthly"])-x["full22"]["net_usd"])<.0003
    assert sum(v["trades"] for v in x["daily_ist"])==x["current_partial_week"]["trades"]
    return x

def ledger_frame(a):
    cols=("entry_epoch exit_epoch direction entry_price exit_price quantity gross_usd "
          "fees_usd gst_usd net_usd initial_stop custom_stop native_stop exit_code "
          "hold_minutes custom_stop_updates native_activated").split()
    df=pd.DataFrame(a,columns=cols)
    if len(df):
        df["entry_utc"]=pd.to_datetime(df.entry_epoch,unit="s",utc=True).astype(str)
        df["exit_utc"]=pd.to_datetime(df.exit_epoch,unit="s",utc=True).astype(str)
        df["exit_reason"]=df.exit_code.map({1.:"open_gap_stop",2.:"native_point_trail",
                         3.:"custom_atr_stop",4.:"supertrend_flip"})
    return df.drop(columns=["entry_epoch","exit_epoch","exit_code"])

def unit_tests():
    # OFF must entirely suppress native trailing even when the chart moves
    # more than the old native activation (500 points).
    n=20
    ts=np.arange(n,dtype=np.int64)*60
    to=np.full(n,60000.,dtype=np.float64)
    th=to.copy();tl=to.copy();tc=to.copy()
    mo=to.copy();mh=to.copy();ml=to.copy();mc=to.copy()
    sig=np.zeros(n,dtype=np.int8);sig[14]=1
    flips=np.zeros(n,dtype=np.int8)
    initatr=np.zeros(n);initatr[14]=1000.
    chartatr=np.full(n,100.)
    th[15]=60700.;mh[15]=60700.
    tl[15]=59400.;ml[15]=59400.
    args=(ts,to,th,tl,tc,mo,mh,ml,mc,sig,flips,initatr,chartatr)
    near_off,_,_=execute(*args,0,0,0,False)
    other_off,_,_=execute(*args,0,1,0,False)
    near_old,_,_=execute(*args,0,0,0,True)
    other_old,_,_=execute(*args,0,1,0,True)
    assert len(near_off)==len(other_off)==len(near_old)==len(other_old)==1
    assert near_off[0,1]==16*60 and other_off[0,1]==16*60
    assert near_off[0,13] in (1,3) and other_off[0,13] in (1,3)
    assert near_off[0,16]==0 and other_off[0,16]==0
    assert near_off[0,10]==57000. and near_off[0,11]==60400.
    assert np.array_equal(near_off,other_off,equal_nan=True),("Native OFF paths differ",near_off,other_off)
    assert near_old[0,1]==16*60 and other_old[0,1]==15*60
    assert other_old[0,13]==2,other_old
    # Verify the two disabled controls do not affect outputs even in
    # a candle which previously activated a native point trail.
    assert not np.array_equal(near_off,other_old,equal_nan=True)

def main():
    unit_tests()
    fresh=refresh_nov()
    arrays,info=inputs()
    result={
      "source":"Exact uploaded BTCUSD Pine v6 plus screenshots and the user correction: both section-7 trailing switches OFF",
      "asset":"BTCUSD (source Pine is BTCUSD only)",
      "parameters":{"entry_tf":"15m","chart_stop_tf":"1m",
         "st_atr10_factor":3,"EMA_length":20,"pullback":"EMA20",
         "initial_stop":"3x ATR14 from completed 15m candle",
         "trailing_mode":"ATR Only","trailing_master_on":True,
         "ATR_trail":"3x ATR14 of native 1m chart, activated at 200 BTCUSD points",
         "fixed_distance_switch_checked":False,"fixed_activation":500,"fixed_distance":250,
         "fixed_distance_effectively_active":False,
         "additional_native_trail_switch_on":False,
         "native_trail_activation":500,"native_trail_offset":1000,
         "native_trailing_effectively_active":False,
         "fixed_and_native_inputs_inactive":True,
         "supertrend_flip_exit":True,"volume_volatility_filter":"Off (Pine default)"},
      "cost":"Pine manual table: 1 TV contract=0.001 BTC, taker 0.05% each way +18% GST. Scalper flag enables waived exit fee on <=30 min holds assumed historically; NO_SCALPER tests baseline fees",
      "method":"15m entry at last 1m close; no native point trail; custom ATR(14)x3 on 1m updates only at completed 1m close; stop applies next minute",
      "limitations":"1m OHLC has no true tick path, bid-ask, real fills, funding, liquidation, or historical scalper offer proof. MARK is not the Pine traded-chart execution source.",
      "historical_window":"22 complete UTC months Jan2025-Oct2026 plus partial IST week Nov16-21 through 07:30",
      "data_refresh":fresh,"data_info":info,"scenarios":{},
      "regression_validation":{},
    }
    summaries=[]
    for src,pid in (("TRADED",0),("MARK",1)):
        for path,barid in (("TV_NEAREST",0),("ALTERNATE_PATH",1)):
            for fees,offer in (("SCALPER_ASSUMED",1),("NO_SCALPER",0)):
                arr,skips,open_=execute(*arrays,pid,barid,offer,False)
                out=reports(arr)
                # There can be no native point trailing exit once both
                # section 7 switches are disabled.
                assert out["full22"]["native_trail_exits"]==0
                assert np.count_nonzero(arr[:,16])==0
                k=f"btc_{src.lower()}_{path.lower()}_{fees.lower()}"
                result["scenarios"][k]={"price_source":src,"bar_path":path,"scalper_assumed":bool(offer),
                    "still_open":bool(open_),"skips":list(map(int,skips)),**out}
                stem=OUT/k
                pd.DataFrame(out["monthly"]).to_csv(str(stem)+"_monthly.csv",index=False)
                pd.DataFrame(out["daily_ist"]).to_csv(str(stem)+"_daily_ist.csv",index=False)
                ledger_frame(arr).to_csv(str(stem)+"_all_trades.csv.gz",index=False,compression="gzip")
                w=arr[(arr[:,1]>=WEEK_START)&(arr[:,1]<END)]
                ledger_frame(w).to_csv(str(stem)+"_weekly_trades.csv",index=False)
                row={"scenario":k,"net_full22":out["full22"]["net_usd"],
                  "pf_full22":out["full22"]["profit_factor"],
                  "trades_full22":out["full22"]["trades"],
                  "positive_months":out["positive_months"],
                  "net_2025":out["year2025"]["net_usd"],
                  "net_2026":out["jan_oct2026"]["net_usd"],
                  "net_week":out["current_partial_week"]["net_usd"],
                  "trades_week":out["current_partial_week"]["trades"]}
                summaries.append(row)
                print("PINE_15M_ATR_ONLY",json.dumps(row),flush=True)
    # Regression: switching native trailing back ON must reproduce the
    # previous completed study exactly, verifying entry/ATR/fee parity.
    previous=json.loads((ROOT/"analysis"/"pine_atr_only_15m_1m_source_20261121"/"summary.json").read_text())
    old,_,_=execute(*arrays,0,0,1,True)
    old_score=reports(old)
    prior=previous["scenarios"]["btc_traded_tv_nearest_scalper_assumed"]["full22"]
    assert abs(old_score["full22"]["net_usd"]-prior["net_usd"])<1e-5
    assert old_score["full22"]["trades"]==prior["trades"]
    assert abs(old_score["full22"]["profit_factor"]-prior["profit_factor"])<1e-4
    result["regression_validation"]={
        "prior_native_on_reproduced":True,
        "native_on_22month_net":old_score["full22"]["net_usd"],
        "native_on_22month_trades":old_score["full22"]["trades"],
        "native_off_native_exits":0
    }
    pd.DataFrame(summaries).to_csv(OUT/"model_comparison.csv",index=False)
    (OUT/"summary.json").write_text(json.dumps(result,indent=2)+"\n")
    print("PINE_NATIVE_OFF_ATR_ONLY_BACKTEST_FINISHED",OUT,flush=True)

if __name__=="__main__":
    main()
