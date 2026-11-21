#!/usr/bin/env python3
"""Backtest screenshot: BOTH 'Enable Trailing Distance (Fixed Points)' and
'Enable Trailing Stop Points' checked, with Fixed Activation=500,
Fixed Distance=250, Additional Stop Points=1000.

Retains PREVIOUS UNCHANGED user context:
  initial protective SL=9x 1H ATR(14), one stop never loosens;
  1H EMA20 touch/reclaim in continuing Supertrend(10,3), ST flip exit ON;
  volume and volatility filters OFF; 1m MARK or TRADED stop monitoring;
  long and short one position/instrument, no fixed TP/time stop.
  ETH points are BTC-equivalent scaled by entry / 80,000, tick rounded.

The screenshot does NOT expose the Pine logic for whether the separate
Additional Stop Points control is activated by the fixed-activation setting.
Therefore we explicitly compare:
  FIXED_ONLY: fixed activation 500, distance 250;
  EXTRA_ONLY: additional stop points 1000 with activation 500;
  BOTH_SHARED: both start after favorable 500 point excursion;
  BOTH_IMMEDIATE_EXTRA: additional 1000-point stop applies from entry
                        independently of fixed activation 500.
The two latter are PLAUSIBLE distinct interpretations; DO NOT assert
an exact TradingView parity without the Pine source.

At every completed 1m bar, observe favorable mark/traded high/low, compute
installed stop for use NEXT minute. Test existing stop BEFORE moving it;
never combine unknown wick-order into look-ahead. When BOTH_SHARED, 250
is mechanically tighter than 1000 after activation so fixed stop dominates.

Delta India production archive Jan2025 - Oct2026 + Nov 2026 fresh historical
1m candles through Nov21 07:30 IST, no price fabrication. The week window
is Monday Nov16 00:00 IST through Saturday Nov21 07:30 IST exclusive.
Costs: 0.05% taker EACH side + GST18% modeled. Funding, true spread,
fill prices, slippage, PM margin/liquidation excluded. ~$1000 notional
historical reference has no wallet insolvency constraint. Trade exit is
1m traded CLOSE proxy when stop crossed within 1m, not exchange stop fill.
Research branch ONLY. No exchange orders, no production bot changes.
"""
from __future__ import annotations
import json
import math
from pathlib import Path
import numpy as np
import pandas as pd
from numba import njit

from current_week_100_300_initial9atr_20261121 import (
    refresh_nov, summarize_week, WEEK_START, END,
)
from extra_trailing_stop_100_300_initial9atr_full22_20261121 import (
    INIT_STOP_SCALE, INIT_ATR14_MULT, unit_tests as previous_tests,
)
from optimize_1h_additional_trailing_stop_points_20261121 import (
    prepare, compute as original_single_trail, stop_round, point_scale,
    frame_rows, metrics,
)

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"analysis"/"screenshot_dual_trail_500_250_extra1000_sl9atr_20261121"
OUT.mkdir(parents=True,exist_ok=True)
FULL_END=int(pd.Timestamp("2026-11-01T00:00:00Z").timestamp())
FULL_START=int(pd.Timestamp("2025-01-01T00:00:00Z").timestamp())
YEAR_SPLIT=int(pd.Timestamp("2026-01-01T00:00:00Z").timestamp())
MONTHS=[str(p) for p in pd.period_range("2025-01","2026-10",freq="M")]
ACT=500.
FIXED_DISTANCE=250.
EXTRA_STOP_POINTS=1000.
FEE=0.0005
GST=0.18
ENTRY_DRIFT=0.002
START_WALLET=100.
MIN_WALLET=11.
MAX_NOTIONAL=1000.
VARIANTS=(
    ("FIXED_ONLY",1,0,0),
    ("EXTRA_ONLY",0,1,0),
    ("BOTH_SHARED",1,1,0),
    ("BOTH_IMMEDIATE_EXTRA",1,1,1),
)
SOURCES=(("MARK",0),("TRADED",1))

@njit(cache=True)
def dual_compute(time_s,traded_o,traded_h,traded_l,traded_c,
                 mark_o,mark_h,mark_l,mark_c,
                 signal,flip,signalclose,stopdist,
                 act_points,fixed_points,extra_points,asset_eth,mode,
                 fixed_on,extra_on,extra_immediate,guard_wallet):
    """Rows match original research replay schema, with extra edit count:
    [entry time, exit time, side, entry, exit, quantity, gross, fees,
     net, initial stop, final stop, act native, fixed native, extra native,
     stop update count, exit code]
    """
    n=len(time_s)
    tick=.05 if asset_eth else .5
    val=.01 if asset_eth else .001
    trades=np.zeros((10000,16),dtype=np.float64)
    ntrades=0
    skips=np.zeros(5,dtype=np.int64)
    wallet=START_WALLET
    active=0;side=0
    entry=0.;quantity=0.;entry_t=0
    best=0.;stop=0.;initial_stop=0.;activated=0
    activation=0.;fixed=0.;extra=0.;edits=0
    for i in range(n):
        s=signal[i]
        fl=flip[i]
        open_t=traded_o[i]
        close_t=traded_c[i]
        if mode==0:
            o=mark_o[i];h=mark_h[i];lo=mark_l[i]
        else:
            o=open_t;h=traded_h[i];lo=traded_l[i]
        exit_code=0;exit_price=0.
        was_active=active==1

        if was_active:
            if (side==1 and o<=stop) or (side==-1 and o>=stop):
                exit_code=1;exit_price=open_t
            elif fl==side:
                exit_code=2;exit_price=open_t

        if active==0 and s!=0:
            if guard_wallet and wallet<MIN_WALLET:
                skips[2]+=1
            elif abs(open_t-signalclose[i])/signalclose[i]>ENTRY_DRIFT:
                skips[1]+=1
            else:
                contracts=math.floor(MAX_NOTIONAL/(open_t*val)+1e-10)
                if contracts<1:
                    skips[3]+=1
                else:
                    proposed=stop_round(open_t-s*stopdist[i],tick,s)
                    if (s==1 and o<=proposed) or (s==-1 and o>=proposed):
                        skips[4]+=1
                    else:
                        active=1;side=s;entry=open_t;quantity=contracts*val
                        entry_t=time_s[i];best=entry;activated=0
                        stop=proposed;initial_stop=stop
                        activation=point_scale(act_points,entry,tick,asset_eth)
                        fixed=point_scale(fixed_points,entry,tick,asset_eth)
                        extra=point_scale(extra_points,entry,tick,asset_eth)
                        edits=0
                        if extra_on and extra_immediate:
                            # This stop is active from entry; it is not
                            # dependent on favorable 500-point activation.
                            candidate=stop_round(entry-side*extra,tick,side)
                            stop=max(stop,candidate) if side==1 else min(stop,candidate)
                            if abs(stop-proposed)>tick/2:
                                edits+=1
        elif was_active and s!=0:
            skips[0]+=1
        if active==0:
            continue
        if exit_code==0:
            # Previously installed stop crosses first; new highwater is not
            # yet known until the completed candle has finished.
            if (side==1 and lo<=stop) or (side==-1 and h>=stop):
                exit_code=3;exit_price=close_t
            else:
                best=max(best,h) if side==1 else min(best,lo)
                if side*(best-entry)>=activation:
                    activated=1
                if fixed_on and activated:
                    candidate=stop_round(best-side*fixed,tick,side)
                    newstop=max(stop,candidate) if side==1 else min(stop,candidate)
                    if abs(newstop-stop)>tick/2:
                        stop=newstop;edits+=1
                if extra_on and (activated or extra_immediate):
                    candidate=stop_round(best-side*extra,tick,side)
                    newstop=max(stop,candidate) if side==1 else min(stop,candidate)
                    if abs(newstop-stop)>tick/2:
                        stop=newstop;edits+=1

        if exit_code!=0:
            gross=(exit_price-entry)*side*quantity
            fees=(entry+exit_price)*quantity*FEE*(1.+GST)
            net=gross-fees
            wallet+=net
            if ntrades>=len(trades):
                raise ValueError("Trade buffer exceeded")
            trades[ntrades,0]=entry_t
            trades[ntrades,1]=time_s[i]
            trades[ntrades,2]=side
            trades[ntrades,3]=entry
            trades[ntrades,4]=exit_price
            trades[ntrades,5]=quantity
            trades[ntrades,6]=gross
            trades[ntrades,7]=fees
            trades[ntrades,8]=net
            trades[ntrades,9]=initial_stop
            trades[ntrades,10]=stop
            trades[ntrades,11]=activation
            trades[ntrades,12]=fixed
            trades[ntrades,13]=extra
            trades[ntrades,14]=edits
            trades[ntrades,15]=exit_code
            ntrades+=1
            active=0
    return trades[:ntrades],skips,wallet,active


def original_shape(dualrows,use_additional=False):
    """Compare core fields exactly with original validated single-stop engine."""
    if not len(dualrows):
        return dualrows.reshape(0,15)
    return dualrows[:,[0,1,2,3,4,5,6,7,8,9,10,11,(13 if use_additional else 12),14,15]]

def unit_tests():
    previous_tests()
    entry=60000
    assert point_scale(500,1600,.05,1)==10.
    assert point_scale(250,1600,.05,1)==5.
    assert point_scale(1000,1600,.05,1)==20.
    assert stop_round(60550-250,.5,1)==60300.
    assert stop_round(60550-1000,.5,1)==59550.
    # Whenever both share the same activation/high-watermark,
    # 250 point gap must dominate the looser 1000 point gap.
    assert max(59000.,60300.,59550.)==60300.
    n=180
    time_s=np.arange(n,dtype=np.int64)*60
    arrs=[np.full(n,60000.,dtype=np.float64) for _ in range(8)]
    # traded O H L C and mark O H L C
    t_o,t_h,t_l,t_c,m_o,m_h,m_l,m_c=arrs
    t_h[59]=60550;m_h[59]=60550
    t_c[59]=60550;m_c[59]=60550
    t_o[60:]=60550;m_o[60:]=60550
    t_h[60:]=60560;m_h[60:]=60560
    t_l[60:]=60200;m_l[60:]=60200
    sig=np.zeros(n,dtype=np.int8);sig[0]=1
    flip=np.zeros(n,dtype=np.int8)
    close=np.zeros(n,dtype=np.float64);close[0]=60000.
    dist=np.zeros(n,dtype=np.float64);dist[0]=900.
    args=(time_s,t_o,t_h,t_l,t_c,m_o,m_h,m_l,m_c,sig,flip,close,dist)
    a,_,_,_=dual_compute(*args,500.,250.,1000.,0,0,1,0,0,False)
    b,_,_,_=dual_compute(*args,500.,250.,1000.,0,0,1,1,0,False)
    assert np.array_equal(a,b),(a,b)
    # Unit trace should stop on the installed stop only after bar completes.
    assert len(a)==1 and a[0,1]>=60*60 and a[0,15]==3,a
    # Same user settings on SHORT should mirror behavior.
    sig[0]=-1
    t_h[1:]=60000.;m_h[1:]=60000.
    t_l[59]=59450.;m_l[59]=59450.
    t_c[59]=59450.;m_c[59]=59450.
    t_o[60:]=59450.;m_o[60:]=59450.
    t_l[60:]=59440.;m_l[60:]=59440.
    t_h[60:]=59800.;m_h[60:]=59800.
    ar,_,_,_=dual_compute(*args,500.,250.,1000.,0,0,1,0,0,False)
    br,_,_,_=dual_compute(*args,500.,250.,1000.,0,0,1,1,0,False)
    assert np.array_equal(ar,br),(ar,br)


def measures(raw):
    x=raw
    n=len(x)
    z=x[:,8] if n else np.empty(0)
    pos=float(z[z>0].sum());neg=-float(z[z<0].sum())
    run=np.r_[0.,np.cumsum(z)]
    return {
      "net_usd":round(float(z.sum()),4),
      "gross_usd":round(float(x[:,6].sum()),4),
      "fees_gst_usd":round(float(x[:,7].sum()),4),
      "trades":n,"wins":int((z>0).sum()),"losses":int((z<0).sum()),
      "win_rate_pct":round(float((z>0).mean())*100,2) if n else None,
      "profit_factor":round(pos/neg,4) if neg else None,
      "max_closed_trade_drawdown_usd":round(float(np.max(np.maximum.accumulate(run)-run)),4),
    }

def slice_and_measure(raw,begin,end):
    return measures(raw[(raw[:,1]>=begin)&(raw[:,1]<end)])

def export_frame(raw):
    cols=["entry_epoch","exit_epoch","side_num","entry_price","exit_price_proxy",
          "quantity","gross_usd","fees_gst_usd","net_usd","initial_stop",
          "final_stop","activation_native","fixed_distance_native",
          "additional_stop_native","stop_edits","exit_code"]
    df=pd.DataFrame(raw,columns=cols)
    if len(df):
        df["entry_utc"]=pd.to_datetime(df.entry_epoch,unit="s",utc=True).astype(str)
        df["exit_utc"]=pd.to_datetime(df.exit_epoch,unit="s",utc=True).astype(str)
        df["month_utc"]=pd.to_datetime(df.exit_epoch,unit="s",utc=True).dt.strftime("%Y-%m")
        df["exit_day_ist"]=pd.to_datetime(df.exit_epoch,unit="s",utc=True).dt.tz_convert("Asia/Kolkata").dt.strftime("%Y-%m-%d")
        df["side"]=df.side_num.map({1.:"LONG",-1.:"SHORT"})
        df["exit_reason"]=df.exit_code.map({1.:"stop_gap",2.:"supertrend_flip",3.:"stop_crossed_1m"})
    return df.drop(columns=["entry_epoch","exit_epoch","side_num","exit_code"])

def main():
    unit_tests()
    evidence=refresh_nov()
    report={
      "study":"Screenshot: both Fixed Trailing Distance (500 activation, 250 distance) and Additional Trailing Stop Points (1000) ENABLED",
      "source_screen":{"fixed_trailing_distance_enabled":True,"activation_points":500,
        "trailing_distance_points":250,"additional_trailing_stop_enabled":True,
        "additional_trailing_stop_points":1000},
      "inherited_settings":{"initial_sl":"9xATR(14) completed 1H signal",
          "volume_filter":False,"volatility_filter":False,
          "supertrend_flip_exit":True,"entry":"1H EMA20 reclaim in ST(10,3)",
          "execution":"1m mark/traded, stop update effective NEXT 1m candle"},
      "semantics":"Both controls use observed 1m favorable high/low and independent stop levels; tighter installed stop wins. BOTH_SHARED uses common activation=500. BOTH_IMMEDIATE_EXTRA assumes extra 1000 stop exists from entry. Actual Pine dual-control precedence not verified.",
      "periods":{"week_start_ist":"2026-11-16T00:00:00+05:30",
                 "week_end_exclusive_ist":"2026-11-21T07:30:00+05:30",
                 "full22":"2025-01 through 2026-10 complete UTC months"},
      "data":evidence,"scenarios":{},"validation":{},
      "costs":"0.05% taker per side + GST18%, no funding/spread/slippage/market impact/liquidation",
      "wallet":"Fixed ~$1000 notional without equity depletion guard, not realizable on $100 account",
      "limitations":"Actual TradingView Pine precedence not available; two plausible joint-control activation rules modeled. No real 1m fills, historical order book, or live trading.",
    }
    for asset in ("BTC","ETH"):
        a,info=prepare(asset)
        assert a[0][0]==FULL_START and a[0][-1]==END-60
        cfg=[x.copy() for x in a]
        assert np.all(cfg[12][cfg[9]!=0]>0)
        cfg[12]*=INIT_STOP_SCALE
        assert INIT_ATR14_MULT==9. and INIT_STOP_SCALE==4.5
        report["data"][asset]["historical"]=info
        for source,mode in SOURCES:
            sim={}
            for name,fixed_on,extra_on,extra_immediate in VARIANTS:
                raw,skips,wallet,openpos=dual_compute(
                    *cfg,ACT,FIXED_DISTANCE,EXTRA_STOP_POINTS,int(asset=="ETH"),
                    mode,fixed_on,extra_on,extra_immediate,False
                )
                df=export_frame(raw)
                cutoff=raw[raw[:,1]<FULL_END]
                wk=raw[(raw[:,1]>=WEEK_START)&(raw[:,1]<END)]
                score={
                    "asset":asset,"source":source,"variant":name,
                    "full22":measures(cutoff),
                    "year2025":slice_and_measure(raw,FULL_START,YEAR_SPLIT),
                    "jan_oct2026":slice_and_measure(raw,YEAR_SPLIT,FULL_END),
                    "current_week":measures(wk),
                    "positive_months":0,
                    "monthly":[],
                    "daily_ist":[],
                    "open_at_data_cutoff":bool(openpos),
                    "wallet_reference_usd":round(float(wallet),4),
                    "skips":{"open_position":int(skips[0]),
                        "stale_signal":int(skips[1]),"wallet_min":int(skips[2]),
                        "quantity":int(skips[3]),"initial_stop_invalid":int(skips[4])},
                }
                for month in MONTHS:
                    start=int(pd.Timestamp(month+"-01T00:00:00Z").timestamp())
                    nextmonth=int((pd.Period(month)+1).start_time.tz_localize("UTC").timestamp())
                    monthscore=slice_and_measure(raw,start,nextmonth)
                    score["monthly"].append({"month_utc":month,**monthscore})
                score["positive_months"]=sum(m["net_usd"]>0 for m in score["monthly"])
                for day in pd.date_range("2026-11-16","2026-11-21",freq="D"):
                    start=int(pd.Timestamp(str(day.date())+"T00:00:00+05:30").timestamp())
                    stop=min(int(pd.Timestamp(str(day.date())+"T00:00:00+05:30").timestamp())+86400,END)
                    daydata=slice_and_measure(raw,start,stop)
                    score["daily_ist"].append({"day_ist":str(day.date()),**daydata})
                assert len(score["monthly"])==22
                assert score["full22"]["trades"]==sum(m["trades"] for m in score["monthly"])
                assert abs(score["full22"]["net_usd"]-sum(m["net_usd"] for m in score["monthly"]))<.006
                assert score["current_week"]["trades"]==sum(d["trades"] for d in score["daily_ist"])
                sim[name]=(raw,score)
                code=f"{asset.lower()}_{source.lower()}_{name.lower()}"
                report["scenarios"][code]=score
                df.loc[(pd.to_datetime(df.exit_utc,utc=True)>=(pd.Timestamp(WEEK_START,unit="s",tz="UTC")))&
                       (pd.to_datetime(df.exit_utc,utc=True)<(pd.Timestamp(END,unit="s",tz="UTC")))]\
                    .to_csv(OUT/f"{code}_weekly_trades.csv",index=False)
                pd.DataFrame(score["daily_ist"]).to_csv(OUT/f"{code}_daily_ist.csv",index=False)
                pd.DataFrame(score["monthly"]).to_csv(OUT/f"{code}_monthly.csv",index=False)
                print("DUAL_TRAIL_SCENARIO",code,json.dumps({
                    "weekly":score["current_week"],"full22":score["full22"],
                    "positive_months":score["positive_months"],
                    "open":score["open_at_data_cutoff"]
                }),flush=True)

            # Reproduce the original robust single-stop replay exactly.
            for variant,act,points in (("FIXED_ONLY",ACT,FIXED_DISTANCE),
                                       ("EXTRA_ONLY",ACT,EXTRA_STOP_POINTS)):
                original,_,_,_=original_single_trail(
                    *cfg,float(act),float(points),int(asset=="ETH"),mode,False
                )
                got=original_shape(sim[variant][0],variant=="EXTRA_ONLY")
                assert got.shape==original.shape,(asset,source,variant,got.shape,original.shape)
                assert np.allclose(got,original,atol=.000001,rtol=0.),(
                    "Mismatch against validated original engine",asset,source,variant,
                    np.max(np.abs(got-original)) if len(got) else 0
                )
            # BOTH_SHARED must behave precisely like tighter FIXED_ONLY.
            aa=sim["BOTH_SHARED"][0]
            bb=sim["FIXED_ONLY"][0]
            assert aa.shape==bb.shape and np.allclose(aa,bb,atol=.000001,rtol=0.),(
                "Dual shared activation should reduce to 250 point tighter stop",asset,source
            )
            report["validation"][f"{asset.lower()}_{source.lower()}"]={
                "fixed_only_parity_with_original":True,
                "extra_only_parity_with_original":True,
                "both_shared_equals_fixed_only":True,
                "note":"Only if Pine uses common 500 activation & independent price stop levels; actual Pine dual precedence not verified"
            }
        del cfg,a

    (OUT/"summary.json").write_text(json.dumps(report,indent=2)+"\n")
    print("SCREENSHOT_BOTH_TRAIL_CONTROLS_TEST_COMPLETE",str(OUT),flush=True)

if __name__=="__main__":
    main()
