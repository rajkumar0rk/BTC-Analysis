#!/usr/bin/env python3
"""Research replay of screenshot's 15m EMA20 + ST10,3 + ATR/fixed trailing.

ONLY EXPLICITLY SHOWN screenshot controls are taken as ground truth:
 Entry 15m; stop monitor 1m; ST ATR10 factor3; EMA20 pullback;
 initial SL ATR(14)*3 (ST-buffer 50 does not apply to ATR SL mode);
 trailing master ON; mode "ATR Only"; trailing ATR(14)*3 activate 200;
 independent fixed distance enable: activate 500, trail distance250;
 independent trailing stop points enable: stop gap1000.

SCREENSHOT AMBIGUITY: In Pine, "ATR Only" might override or coexist
with separately checked fixed trailing controls. Three interpretations
are compared, never claimed exact TradingView code parity:
 ATR_ONLY     : ATR trail only (all other trailing toggles ignored by mode)
 COMBINED     : ATR trailing active after 200; fixed and extra both after 500
 EXTRA_EARLY  : ATR after 200; fixed after 500; additional gap1000 from ENTRY.
Price stops are cumulative and monotonic; tighter level wins. All updates
only at COMPLETED 1m candle and effective NEXT 1m candle. A price stop
cannot be tightened by an unknown current-minute high and filled by the
same-minute low. Signal and indicator values from completed 15m bars only.
Optional Supertrend flip ON and OFF compared (not visible in screenshots).
Volume/volatility filters omitted (not shown; assumption OFF).
No further initial or protective stops, no manual TP.

Native BTC fixed points. ETH points = BTC-equivalent gap*(entry/80000),
tick-rounded, as the research system did previously. Every ATR gap uses
NATIVE ETH/BTC 15m ATR14 and 15m current confirmed ATR values. Positions
entered at next 1m TRADED OPEN after completed 15m EMA pullback signal,
one active trade per asset; entry drift >0.2% skipped.

Both MARK 1m and TRADED 1m trigger models. Mark stop crossing modeled at
the same minute's TRADED CLOSE; open gaps at traded open. Neither is actual
order execution; no intraminute path reconstruction possible. Research
uses ~$1000 constant notional with no wallet guard. Taker fees 0.05%
EACH side and GST18%; excludes funding, bid/ask, true fills, price impact,
PM liquidation. Not a $100 account realistic equity curve.

Historical Delta India PRODUCTION traded + mark 1m candles, Jan2025-
Oct2026 completed months and Nov16-21 (ending 07:30 IST) partial week;
fetches missing Nov candles from public endpoint to TEMP runner copy,
does not commit market archive. Research branch only, no live orders.
"""
from __future__ import annotations
import json,math
from pathlib import Path
import pandas as pd
import numpy as np
from numba import njit
from current_week_100_300_initial9atr_20261121 import refresh_nov,WEEK_START,END
from full_history_1h_trailing_100_50_2025_2026 import read_asset
from replay_btc_ema_st_screenshot import indicators
from optimize_1h_additional_trailing_stop_points_20261121 import point_scale,stop_round

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"analysis"/"screenshot_15m_atr3_fixed_trailing_20261121"
OUT.mkdir(parents=True,exist_ok=True)
START=int(pd.Timestamp("2025-01-01",tz="UTC").timestamp())
FULL_END=int(pd.Timestamp("2026-11-01",tz="UTC").timestamp())
SPLIT=int(pd.Timestamp("2026-01-01",tz="UTC").timestamp())
MONTHS=[str(m) for m in pd.period_range("2025-01","2026-10",freq="M")]
TP_ACT=200.
FIXED_ACT=500.
FIXED_DIST=250.
ADDITIONAL_GAP=1000.
INITIAL_ATR_MULT=3.
TRAIL_ATR_MULT=3.
MAX_NOTIONAL=1000.
ENTRY_DRIFT=.002
FEE=.0005
GST=.18
MODES=(("ATR_ONLY",0),("COMBINED",1),("EXTRA_EARLY",2))
SOURCES=(("MARK",0),("TRADED",1))
FLIPS=(("ON",1),("OFF",0))

def source_arrays(asset):
    trade,mark,provenance=read_asset(asset)
    n=int(np.searchsorted(trade.time.to_numpy(np.int64),END,"left"))
    trade=trade.iloc[:n].copy();mark=mark.iloc[:n].copy()
    t=trade.time.to_numpy(np.int64)
    assert t[0]==START and t[-1]==END-60 and np.all(np.diff(t)==60)
    assert np.array_equal(t,mark.time.to_numpy(np.int64))
    assert n%15==0
    complete=trade.resample("15min",origin="epoch",label="left",closed="left").agg({
       "open":"first","high":"max","low":"min","close":"last",
       "volume":"sum","time":"count"
    })
    assert len(complete)*15==len(trade)
    assert np.all(complete.time.to_numpy()==15)
    ind=indicators(complete.drop(columns="time")) # exact ST and EMA from original
    signal=np.zeros(n,dtype=np.int8);flip=np.zeros(n,dtype=np.int8)
    sigclose=np.zeros(n);atr_on_entry=np.zeros(n);known_atr=np.zeros(n)
    for i in range(36,len(ind)-1):
        j=(i+1)*15
        if not (np.isfinite(ind.atr14.iloc[i]) and np.isfinite(ind.ema.iloc[i])):
            continue
        direction=int(ind.dir.iloc[i]);prior=int(ind.dir.iloc[i-1])
        if direction!=prior and prior!=0:
            flip[j]=+1 if direction==+1 else -1
        # Only completed-15m ATR becomes usable from following 1m boundary.
        known_atr[j]=float(ind.atr14.iloc[i])
        if direction==prior==-1 and ind.low.iloc[i]<=ind.ema.iloc[i] and ind.close.iloc[i]>ind.ema.iloc[i]:
            signal[j]=1
        elif direction==prior==1 and ind.high.iloc[i]>=ind.ema.iloc[i] and ind.close.iloc[i]<ind.ema.iloc[i]:
            signal[j]=-1
        if signal[j]!=0:
            sigclose[j]=float(ind.close.iloc[i])
            atr_on_entry[j]=float(ind.atr14.iloc[i])
    # Fill indicator only FORWARD, never from future bars.
    for i in range(1,len(known_atr)):
        if known_atr[i]==0:known_atr[i]=known_atr[i-1]
    assert np.all(known_atr[2000:]>0)
    meta={"minute_bars":n,"15m_bars":len(ind),
          "unfiltered_signals":int(np.count_nonzero(signal)),
          "supertrend_flips":int(np.count_nonzero(flip)),
          "last_minute_utc":str(trade.index[-1]),
          "original_dataset":provenance}
    arrays=[
        t,
        trade.open.to_numpy(np.float64),trade.high.to_numpy(np.float64),
        trade.low.to_numpy(np.float64),trade.close.to_numpy(np.float64),
        mark.open.to_numpy(np.float64),mark.high.to_numpy(np.float64),
        mark.low.to_numpy(np.float64),mark.close.to_numpy(np.float64),
        signal,flip,sigclose,atr_on_entry,known_atr,
    ]
    return arrays,meta

@njit(cache=True)
def replay(ts,to,th,tl,tc,mo,mh,ml,mc,
           signal,flip,signalclose,atr_entry,atr_known,
           asset_eth,price_source,mode,flip_enabled):
    # result columns entry_t,exit_t,side,entry,exit,qty,gross,fees,net,
    # initial_sl,last_sl,atr_gap_initial,atr_gap_final,
    # native_atr_activation,native_fixed_activation,native_fixed_gap,
    # native_extra_gap,exit_code,stop_updates,hold_min
    result=np.zeros((12000,20),dtype=np.float64)
    count=0
    skip=np.zeros(5,dtype=np.int64)
    tick=.05 if asset_eth else .5
    contract=.01 if asset_eth else .001
    active=0;side=0
    entry=0.;qty=0.;entry_t=0
    sl=0.;initial=0.;best=0.;stop_edits=0
    atr_entry_gap=0.;last_atr_gap=0.
    act_a=0.;act_f=0.;gap_f=0.;gap_x=0.
    for i in range(len(ts)):
        s=signal[i]
        open_t=to[i]
        if price_source==0:
            o=mo[i];h=mh[i];lo=ml[i]
        else:
            o=to[i];h=th[i];lo=tl[i]
        ec=0;exit_price=0.
        had=active==1
        if had:
            if (side==1 and o<=sl) or (side==-1 and o>=sl):
                ec=1;exit_price=open_t
            elif flip_enabled and flip[i]==side:
                ec=2;exit_price=open_t
        if not had and s!=0:
            if signalclose[i]<=0 or abs(open_t-signalclose[i])/signalclose[i] > ENTRY_DRIFT:
                skip[1]+=1
            else:
                contracts=math.floor(MAX_NOTIONAL/(open_t*contract)+1e-10)
                if contracts<1:
                    skip[2]+=1
                elif atr_entry[i]<=0:
                    skip[3]+=1
                else:
                    proposed=stop_round(open_t-s*INITIAL_ATR_MULT*atr_entry[i],tick,s)
                    if (s==1 and o<=proposed) or (s==-1 and o>=proposed):
                        skip[4]+=1
                    else:
                        active=1;side=s;entry=open_t;qty=contracts*contract
                        entry_t=ts[i];best=entry
                        sl=proposed;initial=sl;stop_edits=0
                        atr_entry_gap=INITIAL_ATR_MULT*atr_entry[i]
                        last_atr_gap=TRAIL_ATR_MULT*atr_entry[i]
                        act_a=point_scale(TP_ACT,entry,tick,asset_eth)
                        act_f=point_scale(FIXED_ACT,entry,tick,asset_eth)
                        gap_f=point_scale(FIXED_DIST,entry,tick,asset_eth)
                        gap_x=point_scale(ADDITIONAL_GAP,entry,tick,asset_eth)
                        if mode==2:
                            candidate=stop_round(entry-side*gap_x,tick,side)
                            newer=max(sl,candidate) if side==1 else min(sl,candidate)
                            if abs(newer-sl)>tick/2:
                                sl=newer;stop_edits+=1
        elif had and s!=0:
            skip[0]+=1
        if active==0:continue
        if ec==0:
            if (side==1 and lo<=sl) or (side==-1 and h>=sl):
                ec=3;exit_price=tc[i]
            else:
                # At end of fully formed 1m candle, use favorable high/low.
                best=max(best,h) if side==1 else min(best,lo)
                gain=side*(best-entry)
                if gain>=act_a and atr_known[i]>0:
                    last_atr_gap=TRAIL_ATR_MULT*atr_known[i]
                    candidate=stop_round(best-side*last_atr_gap,tick,side)
                    newer=max(sl,candidate) if side==1 else min(sl,candidate)
                    if abs(newer-sl)>tick/2:
                        sl=newer;stop_edits+=1
                if mode!=0:
                    if gain>=act_f:
                        candidate=stop_round(best-side*gap_f,tick,side)
                        newer=max(sl,candidate) if side==1 else min(sl,candidate)
                        if abs(newer-sl)>tick/2:
                            sl=newer;stop_edits+=1
                    if mode==2 or gain>=act_f:
                        candidate=stop_round(best-side*gap_x,tick,side)
                        newer=max(sl,candidate) if side==1 else min(sl,candidate)
                        if abs(newer-sl)>tick/2:
                            sl=newer;stop_edits+=1
        if ec!=0:
            gross=(exit_price-entry)*side*qty
            fee=(entry+exit_price)*qty*FEE*(1.+GST)
            if count>=len(result):raise RuntimeError("Excess trades buffer")
            result[count,0]=entry_t
            result[count,1]=ts[i]
            result[count,2]=side
            result[count,3]=entry
            result[count,4]=exit_price
            result[count,5]=qty
            result[count,6]=gross
            result[count,7]=fee
            result[count,8]=gross-fee
            result[count,9]=initial
            result[count,10]=sl
            result[count,11]=atr_entry_gap
            result[count,12]=last_atr_gap
            result[count,13]=act_a
            result[count,14]=act_f
            result[count,15]=gap_f
            result[count,16]=gap_x
            result[count,17]=ec
            result[count,18]=stop_edits
            result[count,19]=(ts[i]-entry_t)/60.
            count+=1;active=0
    return result[:count],skip,active

def score(x):
    n=len(x)
    z=x[:,8] if n else np.empty(0)
    win=z[z>0];loss=z[z<0]
    cum=np.r_[0.,np.cumsum(z)]
    codes=x[:,17].astype("int64") if n else np.empty(0,dtype="int64")
    return {
      "net_usd":round(float(z.sum()),4),
      "gross_usd":round(float(x[:,6].sum()),4),
      "fees_gst_usd":round(float(x[:,7].sum()),4),
      "trades":n,
      "wins":len(win),"losses":len(loss),
      "win_rate_pct":round(100.*len(win)/n,2) if n else None,
      "profit_factor":round(float(win.sum()/-loss.sum()),4) if len(loss) else None,
      "max_closed_trade_drawdown_usd":round(float(np.max(np.maximum.accumulate(cum)-cum)),4),
      "stop_exits":int(((codes==1)|(codes==3)).sum()),
      "supertrend_flip_exits":int((codes==2).sum()),
      "trades_with_stop_edits":int(np.count_nonzero(x[:,18])) if n else 0,
    }

def split(x):
    out={}
    y=x[:,1]
    full=x[(y>=START)&(y<FULL_END)]
    week=x[(y>=WEEK_START)&(y<END)]
    out["full22"]=score(full)
    out["train2025"]=score(full[full[:,1]<SPLIT])
    out["test2026_jan_oct"]=score(full[full[:,1]>=SPLIT])
    out["week_nov16_21_partial"]=score(week)
    mtime=full[:,1].astype("int64").astype("datetime64[s]").astype("datetime64[M]")
    months=[]
    for m in MONTHS:
        months.append({"month_utc":m,**score(full[mtime==np.datetime64(m,"M")])})
    out["monthly"]=months
    out["positive_months"]=sum(m["net_usd"]>0 for m in months)
    if sum(m["trades"] for m in months)!=len(full) or abs(sum(m["net_usd"] for m in months)-out["full22"]["net_usd"])>.01:
        raise AssertionError("22-month reconciliation failure")
    days=pd.date_range("2026-11-16","2026-11-21")
    ist=(week[:,1].astype("int64").astype("datetime64[s]")+np.timedelta64(330,"m")).astype("datetime64[D]")
    out["daily_ist"]=[{"date_ist":str(day.date()),**score(week[ist==np.datetime64(str(day.date()))])} for day in days]
    if sum(d["trades"] for d in out["daily_ist"])!=len(week):
        raise AssertionError("Week reconciliation failure")
    return out

def to_frame(x):
    columns=("entry_epoch exit_epoch side_num entry_price exit_price_proxy qty "
             "gross_usd fees_gst_usd net_usd initial_stop final_stop "
             "initial_atr_gap last_atr_gap atr_activation fixed_activation "
             "fixed_distance additional_gap exit_code stop_updates hold_minutes").split()
    df=pd.DataFrame(x,columns=columns)
    if len(df):
        df["entry_utc"]=pd.to_datetime(df.entry_epoch,unit="s",utc=True).astype(str)
        df["exit_utc"]=pd.to_datetime(df.exit_epoch,unit="s",utc=True).astype(str)
        df["direction"]=df.side_num.map({1.:"LONG",-1.:"SHORT"})
        df["exit_reason"]=df.exit_code.map({1.:"stop_open_gap",2.:"supertrend_flip",3.:"stop_cross_1m"})
    return df.drop(columns=["entry_epoch","exit_epoch","side_num","exit_code"])

def unit_tests():
    # Unfinished 15m signal must never enter before next 15m start.
    # Check stop is not repriced to the current 1m high and hit by same low.
    n=17
    ts=np.arange(n,dtype=np.int64)*60
    vals=[np.full(n,60000.,dtype=np.float64) for _ in range(8)]
    to,th,tl,tc,mo,mh,ml,mc=vals
    sig=np.zeros(n,dtype=np.int8);sig[0]=1
    flip=np.zeros(n,dtype=np.int8)
    signalclose=np.zeros(n);signalclose[0]=60000.
    atr_entry=np.zeros(n);atr_entry[0]=100.
    known=np.full(n,100.)
    th[1]=60600.;mh[1]=60600.
    tl[1]=59800.;ml[1]=59800. # initial stop 59700 not hit, would breach NEW fixed stop if retroactive.
    tc[1]=60300.;mc[1]=60300.
    to[2:]=60300.;mo[2:]=60300.
    tl[2]=60200.;ml[2]=60200.
    args=(ts,to,th,tl,tc,mo,mh,ml,mc,sig,flip,signalclose,atr_entry,known)
    combo,_,_=replay(*args,0,0,1,0)
    assert len(combo)==1 and combo[0,1]==120 and combo[0,17]==3,combo
    # LONG initial 3xATR: 59700; ATR trail after 200 points uses
    # observed favorable 60600, ATR gap300 => 60300; fixed trail
    # when favorable >=500 yields 60350, so stop at 60350 next bar.
    assert abs(combo[0,9]-59700)<1e-6
    assert abs(combo[0,10]-60350)<1e-6
    assert point_scale(500.,1600.,.05,1)==10.
    assert point_scale(250.,1600.,.05,1)==5.
    assert point_scale(1000.,1600.,.05,1)==20.

def main():
    unit_tests()
    fresh=refresh_nov()
    report={
      "screenshot_15m_settings":{
        "entry_timeframe":"15 minutes","stop_monitoring_timeframe":"1 minute",
        "supertrend":{"atr_length":10,"factor":3},
        "ema":{"length":20,"pullback_mode":"EMA20"},
        "initial_stop":{"mode":"ATR x Multiplier","atr_length":14,"atr_multiplier":3,
                        "supertrend_stop_buffer_points":50,"buffer_unused_in_atr_mode":True},
        "trailing_exit":{"enabled":True,"mode":"ATR Only"},
        "fixed_trailing":{"distance_enabled":True,"activation_points":500,
                          "trailing_distance_points":250,"additional_stop_enabled":True,
                          "additional_stop_points":1000},
        "atr_trailing":{"length":14,"multiplier":3,"activation_points":200}
      },
      "unshown_assumptions":{
        "supertrend_flip_exit":"not pictured; independently test ON/OFF",
        "volume_filter":"not pictured; OFF for this test",
        "volatility_filter":"not pictured; OFF for this test",
        "EMA20_signal":"Completed 15m candle touches EMA20 and closes on correct side in same continuing ST trend",
        "trail_activation":"Favorable 1m extrema relative to entry after completed 1m only",
        "eth_point_scaling":"ETH BTC-equivalent fixed points scaled by entry/80000, tick rounded"
      },
      "mode_semantics":{
        "ATR_ONLY":"ATR Only mode ignores checked fixed trailing controls",
        "COMBINED":"ATR activates at 200; fixed trailing and extra point stop activate together at 500; tighter cumulative stop prevails",
        "EXTRA_EARLY":"ATR activates at 200; fixed trailing at 500; 1000 additional stop is independently active from entry",
        "WARNING":"Exact TradingView Pine control precedence is unknown from screenshots. None is proven Pine parity."
      },
      "historical_window":{
        "months":"Jan2025-Oct2026 complete UTC 22 months",
        "week":"Nov16 00:00 IST through Nov21 07:30 IST, PARTIAL"
      },
      "costs":"Taker 0.05% per side + 18% GST on fees, no scalper waiver. No spread, funding, live fills, market impact, PM liquidation",
      "wallet":"Fixed ~$1000 reference notional, not a wallet-aware $100 live simulation",
      "source":"Delta India production historical MARK + traded 1m candles",
      "data_freshness":fresh,
      "datasets":{},"scenarios":{},"rankings":{}
    }
    scores=[]
    for asset in ("BTC","ETH"):
        args,meta=source_arrays(asset)
        report["datasets"][asset]=meta
        for source,source_id in SOURCES:
            for mode,modeid in MODES:
                for flip,fl_id in FLIPS:
                    x,skips,isopen=replay(*args,int(asset=="ETH"),source_id,modeid,fl_id)
                    stats=split(x)
                    k=f"{asset.lower()}_{source.lower()}_{mode.lower()}_flip_{flip.lower()}"
                    report["scenarios"][k]={
                         "asset":asset,"price_source":source,"mode":mode,
                         "flip_exit":flip,"is_open_at_cutoff":bool(isopen),
                         "skips":{"existing_position":int(skips[0]),
                                  "deviation":int(skips[1]),"minimum_contract":int(skips[2]),
                                  "ATR_unavailable":int(skips[3]),"invalid_initial_mark_stop":int(skips[4])},
                         **stats
                    }
                    monthly=pd.DataFrame(stats["monthly"])
                    monthly.to_csv(OUT/f"{k}_monthly.csv",index=False)
                    pd.DataFrame(stats["daily_ist"]).to_csv(OUT/f"{k}_daily_ist.csv",index=False)
                    df=to_frame(x)
                    df.to_csv(OUT/f"{k}_trade_ledger.csv.gz",index=False,compression="gzip")
                    if len(df):
                        wk=df.loc[(pd.to_datetime(df.exit_utc,utc=True)>=pd.Timestamp(WEEK_START,unit="s",tz="UTC"))&
                                  (pd.to_datetime(df.exit_utc,utc=True)<pd.Timestamp(END,unit="s",tz="UTC"))]
                    else:wk=df
                    wk.to_csv(OUT/f"{k}_week_trades.csv",index=False)
                    row={"asset":asset,"price_source":source,"mode":mode,
                         "flip_exit":flip,"full22_net":stats["full22"]["net_usd"],
                         "full22_pf":stats["full22"]["profit_factor"],
                         "full22_trades":stats["full22"]["trades"],
                         "full22_positive_months":stats["positive_months"],
                         "max_closed_drawdown_usd":stats["full22"]["max_closed_trade_drawdown_usd"],
                         "train2025_net":stats["train2025"]["net_usd"],
                         "test2026_net":stats["test2026_jan_oct"]["net_usd"],
                         "week_net":stats["week_nov16_21_partial"]["net_usd"],
                         "week_trades":stats["week_nov16_21_partial"]["trades"]}
                    scores.append(row)
                    print("SCREENSHOT_15M_RUN",k,json.dumps(row),flush=True)
        del args
    pd.DataFrame(scores).sort_values("full22_net",ascending=False).to_csv(
        OUT/"all_24_scenario_scores.csv",index=False)
    report["rankings"]={
      a:sorted([r for r in scores if r["asset"]==a],
               key=lambda v:v["full22_net"],reverse=True)
      for a in ("BTC","ETH")
    }
    (OUT/"summary.json").write_text(json.dumps(report,indent=2)+"\n")
    print("SCREENSHOT_15M_ATR3_FIXED_AND_EXTRA_REPLAY_COMPLETE",OUT,flush=True)

if __name__=="__main__":
    main()
