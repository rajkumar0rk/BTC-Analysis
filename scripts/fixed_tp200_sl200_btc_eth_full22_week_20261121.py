#!/usr/bin/env python3
"""Backtest FIXED Take Profit 200 points / FIXED Stop Loss 200 points.

Request: replace ATR9 initial stop and both trailing controls with strict
200/200 fixed TP/SL BRACKET from actual next-1m traded entry OPEN.

Keep:
  1H EMA20 touch and close reclaim, continuing Supertrend(10,3).
  Volume and volatility entry filters OFF.
  One independent position per asset, LONG and SHORT.
  Optional Supertrend flip exit ON (previous user setting); OFF compared.
  Monitoring 1M, no trailing, no profit activation, no ATR9 initial stop.

BTC = raw +/-200 USD from entry.
ETH = previous strategy convention BTC-equivalent 200 point move scaled
      by entry/80,000 and tick rounded ($0.05); not raw 200 ETH USD.
Both MARK and TRADED 1M high/low price trigger models.
Stop/Tp price modeled at target/stop for in-minute hits. Open gaps use
next traded 1m open. For same 1m candle with BOTH TP and SL touched,
historical OHLC cannot identify which was touched first: report two
intraminute scenarios: conservative SL_FIRST, optimistic TP_FIRST,
and number of ambiguous bars. These are not actual exchange fills.
Stop/target triggers use 1m OHLC and are static since trade entry,
no invented order within the minute.

Run 22 complete UTC months Jan2025-Oct2026 plus the latest verified
historical week Nov16 00:00 IST through Nov21 07:30 IST, excluding
open/unrealized PnL. Source: Delta India PRODUCTION 1m traded & MARK
OHLC, Nov through historical public candles, not Demo/testnet.
Fixed ~$1000 notional reference (NO equity depletion), 0.05% taker
fee per side + GST18%. No funding, bid-ask spread, impact, order
fill latency or PM liquidation, so not a funded $100 account test.
Research branch only; no live orders and no production changes.
"""
from __future__ import annotations
import math
import json
from pathlib import Path
import numpy as np
import pandas as pd
from numba import njit
from optimize_1h_additional_trailing_stop_points_20261121 import (
    prepare,point_scale,stop_round
)
from current_week_100_300_initial9atr_20261121 import (
    refresh_nov,WEEK_START,END
)

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"analysis"/"fixed_takeprofit200_stoploss200_20261121"
OUT.mkdir(parents=True,exist_ok=True)
FULL_START=int(pd.Timestamp("2025-01-01T00:00:00Z").timestamp())
SPLIT_2026=int(pd.Timestamp("2026-01-01T00:00:00Z").timestamp())
FULL_END=int(pd.Timestamp("2026-11-01T00:00:00Z").timestamp())
MONTHS=[str(m) for m in pd.period_range("2025-01","2026-10",freq="M")]
POINTS=200.
MAX_NOTIONAL=1000.
FEE=.0005
GST=.18
MAX_ENTRY_DRIFT=.002
# exit codes: 1=SL open gap, 2=TP open gap, 3=Supertrend,
# 4=SL intraminute, 5=TP intraminute.
@njit(cache=True)
def bracket(time_s,tr_o,tr_h,tr_l,tr_c,m_o,m_h,m_l,m_c,
            signal,flip,signal_close,
            asset_eth,source,flip_on,sl_first):
    n=len(time_s)
    unit=.01 if asset_eth else .001
    tick=.05 if asset_eth else .5
    result=np.zeros((15000,15),dtype=np.float64)
    ntr=0
    skip=np.zeros(5,dtype=np.int64)
    opened=0;side=0
    ep=0.;qty=0.;t_entry=0
    sl=0.;tp=0.;move=0.
    for i in range(n):
        s=signal[i]
        fl=flip[i]
        op=tr_o[i]
        if source==0:
            o=m_o[i]; hi=m_h[i]; lo=m_l[i]
        else:
            o=op;hi=tr_h[i];lo=tr_l[i]
        was_open=opened==1
        ec=0;px=0.
        ambiguous=0
        if was_open:
            if (side==1 and o<=sl) or (side==-1 and o>=sl):
                ec=1;px=op
            elif (side==1 and o>=tp) or (side==-1 and o<=tp):
                ec=2;px=op
            elif flip_on and fl==side:
                ec=3;px=op
        if not was_open and s!=0:
            if not math.isfinite(signal_close[i]) or signal_close[i]<=0:
                skip[1]+=1
            elif abs(op-signal_close[i])/signal_close[i]>MAX_ENTRY_DRIFT:
                skip[1]+=1
            else:
                contracts=math.floor(MAX_NOTIONAL/(op*unit)+1e-10)
                if contracts<1:
                    skip[2]+=1
                else:
                    p=point_scale(POINTS,op,tick,asset_eth)
                    if p<=0:
                        skip[3]+=1
                    else:
                        opened=1;side=s;ep=op;qty=contracts*unit
                        t_entry=time_s[i];move=p
                        # Round prices to legal tick in correct direction:
                        # LONG TP must not be under requested points,
                        # LONG SL must not be farther than requested points.
                        # With move rounded to exact tick multiples by
                        # point_scale() these equal +/-move exactly.
                        tp=stop_round(ep+side*move,tick,-side)
                        sl=stop_round(ep-side*move,tick,side)
                        if not (side*(tp-ep)>0 and side*(ep-sl)>0):
                            raise AssertionError("Invalid bracket")
        elif was_open and s!=0:
            skip[0]+=1
        if opened==0:
            continue
        if ec==0:
            hit_sl=(lo<=sl) if side==1 else (hi>=sl)
            hit_tp=(hi>=tp) if side==1 else (lo<=tp)
            if hit_tp and hit_sl:
                ambiguous=1
                if sl_first:
                    ec=4;px=sl
                else:
                    ec=5;px=tp
            elif hit_sl:
                ec=4;px=sl
            elif hit_tp:
                ec=5;px=tp
        if ec!=0:
            gross=(px-ep)*side*qty
            fees=(ep+px)*qty*FEE*(1.+GST)
            net=gross-fees
            if ntr>=len(result):
                raise RuntimeError("Trade buffer exceeded")
            result[ntr,0]=t_entry
            result[ntr,1]=time_s[i]
            result[ntr,2]=side
            result[ntr,3]=ep
            result[ntr,4]=px
            result[ntr,5]=qty
            result[ntr,6]=gross
            result[ntr,7]=fees
            result[ntr,8]=net
            result[ntr,9]=sl
            result[ntr,10]=tp
            result[ntr,11]=move
            result[ntr,12]=ec
            result[ntr,13]=ambiguous
            result[ntr,14]=(time_s[i]-t_entry)/60.
            ntr+=1
            opened=0
    return result[:ntr],skip,opened


def to_frame(x):
    cols=["entry_epoch","exit_epoch","direction","entry_price","exit_price_proxy","quantity",
          "gross_usd","fees_gst_usd","net_usd","stop_loss_price","take_profit_price",
          "movement_native","exit_code","both_hit_same_1m","holding_minutes"]
    df=pd.DataFrame(x,columns=cols)
    if len(df):
        df["entry_utc"]=pd.to_datetime(df.entry_epoch,unit="s",utc=True).astype(str)
        df["exit_utc"]=pd.to_datetime(df.exit_epoch,unit="s",utc=True).astype(str)
        df["side"]=df.direction.map({1.:"LONG",-1.:"SHORT"})
        df["exit_reason"]=df.exit_code.map({
           1.:"stop_gap",2.:"takeprofit_gap",3.:"supertrend_flip",
           4.:"stop_in_1m",5.:"takeprofit_in_1m"})
        df["exit_day_ist"]=pd.to_datetime(df.exit_epoch,unit="s",utc=True).dt.tz_convert("Asia/Kolkata").dt.strftime("%Y-%m-%d")
        df["exit_month_utc"]=pd.to_datetime(df.exit_epoch,unit="s",utc=True).dt.strftime("%Y-%m")
    return df.drop(columns=["entry_epoch","exit_epoch","direction","exit_code"])


def score(raw):
    z=raw[:,8] if len(raw) else np.empty(0,dtype=np.float64)
    pos=float(z[z>0].sum());neg=-float(z[z<0].sum())
    eq=np.r_[0.,np.cumsum(z)]
    c=raw[:,12].astype(int) if len(raw) else np.empty(0,dtype=int)
    return {
        "net_usd":round(float(z.sum()),4),
        "gross_usd":round(float(raw[:,6].sum()),4),
        "fees_gst_usd":round(float(raw[:,7].sum()),4),
        "trades":int(len(raw)),
        "wins":int((z>0).sum()),
        "losses":int((z<0).sum()),
        "win_rate_pct":round(100.*int((z>0).sum())/len(raw),2) if len(raw) else None,
        "profit_factor":round(pos/neg,4) if neg>0 else None,
        "max_closed_trade_drawdown_usd":round(float(np.max(np.maximum.accumulate(eq)-eq)),4),
        "ambiguous_both_hit_same_minute":int(raw[:,13].sum()) if len(raw) else 0,
        "takeprofit_exits":int(((c==2)|(c==5)).sum()),
        "stoploss_exits":int(((c==1)|(c==4)).sum()),
        "supertrend_flip_exits":int((c==3).sum())
    }


def split_score(x):
    times=x[:,1]
    full=x[(times>=FULL_START)&(times<FULL_END)]
    train=full[full[:,1]<SPLIT_2026]
    holdout=full[full[:,1]>=SPLIT_2026]
    week=x[(times>=WEEK_START)&(times<END)]
    dates=full[:,1].astype(np.int64).astype("datetime64[s]").astype("datetime64[M]")
    monthly=[]
    for m in MONTHS:
        mrows=full[dates==np.datetime64(m,"M")]
        monthly.append({"month_utc":m,**score(mrows)})
    if sum(r["trades"] for r in monthly)!=len(full):
        raise AssertionError("Monthly trade total mismatch")
    if abs(sum(r["net_usd"] for r in monthly)-score(full)["net_usd"])>.01:
        raise AssertionError("Monthly PnL sum mismatch")
    days=[]
    ist_dates=(week[:,1].astype(np.int64).astype("datetime64[s]")+
               np.timedelta64(330,"m")).astype("datetime64[D]")
    for day in pd.date_range("2026-11-16","2026-11-21",freq="D"):
        ds=np.datetime64(str(day.date()))
        days.append({"date_ist":str(day.date()),**score(week[ist_dates==ds])})
    if sum(x["trades"] for x in days)!=len(week):
        raise AssertionError("Weekly daily count mismatch")
    return {
      "full22":score(full),"train2025":score(train),
      "holdout2026_jan_oct":score(holdout),
      "week_partial":score(week),
      "positive_months":sum(m["net_usd"]>0 for m in monthly),
      "negative_months":sum(m["net_usd"]<0 for m in monthly),
      "monthly":monthly,"daily_ist":days,
    }


def unit_tests():
    assert point_scale(200.,60000.,.5,0)==200.
    assert point_scale(200.,1600.,.05,1)==4.
    # Both stop and target crossed IN SAME historical candle.
    n=4; t=np.arange(n,dtype=np.int64)*60
    vals=[np.full(n,60000.,dtype=np.float64) for _ in range(8)]
    tr_o,tr_h,tr_l,tr_c,m_o,m_h,m_l,m_c=vals
    tr_h[0]=60250.;m_h[0]=60250.
    tr_l[0]=59750.;m_l[0]=59750.
    sig=np.zeros(n,dtype=np.int8);sig[0]=1
    flip=np.zeros(n,dtype=np.int8)
    close=np.zeros(n,dtype=np.float64);close[0]=60000.
    args=(t,tr_o,tr_h,tr_l,tr_c,m_o,m_h,m_l,m_c,sig,flip,close)
    sl,_,_=bracket(*args,0,0,False,True)
    tp,_,_=bracket(*args,0,0,False,False)
    assert len(sl)==1 and len(tp)==1
    assert sl[0,12]==4 and sl[0,13]==1 and sl[0,8]<0
    assert tp[0,12]==5 and tp[0,13]==1 and tp[0,8]>0
    # SHORT direction symmetric.
    sig[0]=-1
    sh_sl,_,_=bracket(*args,0,0,False,True)
    sh_tp,_,_=bracket(*args,0,0,False,False)
    assert len(sh_sl)==len(sh_tp)==1 and sh_sl[0,8]<0 and sh_tp[0,8]>0
    # Confirm one-sided TP without stop is a win.
    sig[0]=1;tr_l[0]=59990.;m_l[0]=59990.
    one,_,_=bracket(*args,0,0,False,True)
    assert one[0,12]==5 and one[0,13]==0 and one[0,8]>0
    # Fee: at $1000 notional, approx $1.18 roundtrip (vary with exit).
    assert .8<one[0,7]<1.5


def main():
    unit_tests()
    evidence=refresh_nov()
    report={
      "request":"Fixed take profit 200 points and fixed stop loss 200 points, replace all trailing and 9xATR SL",
      "controls":{"take_profit_points_btc_equiv":200,"stop_loss_points_btc_equiv":200,
         "initial_sl_atr":False,"fixed_distance_trailing":False,"additional_trailing_stop":False,
         "volume_filter":False,"volatility_filter":False,
         "entry":"1H EMA20 touch/reclaim continuing Supertrend10,3"},
      "eth_point_convention":"BTC equivalent 200 points * ETH entry / 80000, tick rounded (not raw $200 ETH)",
      "models":{"MARK":"1m native mark OHLC hits thresholds; target/stop-price fills approximated",
                "TRADED":"1m traded OHLC hits thresholds; target/stop-price fills approximated"},
      "supertrend_exit_modes":{"ON":"keep earlier opposite Supertrend exit as next 1m open",
                               "OFF":"hold until fixed 200pt target/SL only"},
      "ambiguous_intraminute":{"SL_FIRST":"both hit same 1m, assume stop first (conservative)",
                               "TP_FIRST":"both hit same 1m, assume target first (optimistic)"},
      "date_window":{"week_start_ist":"2026-11-16T00:00:00+05:30",
                     "week_end_exclusive_ist":"2026-11-21T07:30:00+05:30",
                     "full22":"2025-01 through 2026-10, complete UTC months"},
      "sizing":"~$1000 fixed notional per trade without equity depletion guard; not a funded $100 account curve",
      "fee_model":"0.05% taker entry +0.05% taker exit, 18% GST on fees; excludes funding, true fill slippage, bid/ask and PM liquidation",
      "data_sources":evidence,
      "scenarios":{}
    }
    table=[]
    for asset in ("BTC","ETH"):
        args,meta=prepare(asset)
        assert args[0][0]==FULL_START and args[0][-1]==END-60
        report["data_sources"][asset]["full_history"]=meta
        for source,source_id in (("MARK",0),("TRADED",1)):
            for flip_name,flip_on in (("ON",True),("OFF",False)):
                for tie_name,sl_first in (("SL_FIRST",True),("TP_FIRST",False)):
                    raw,skips,openpos=bracket(*args[:12],int(asset=="ETH"),source_id,flip_on,sl_first)
                    summary=split_score(raw)
                    k=f"{asset.lower()}_{source.lower()}_flip_{flip_name.lower()}_{tie_name.lower()}"
                    report["scenarios"][k]={
                        "asset":asset,"monitor_price":source,
                        "supertrend_flip":flip_name,"same_minute_tie_order":tie_name,
                        "open_position_at_week_cutoff":bool(openpos),
                        "skipped_entry_signals":{"already_open":int(skips[0]),
                            "entry_deviation":int(skips[1]),"not_enough_contract_qty":int(skips[2]),
                            "invalid_point_scale":int(skips[3]),"other":int(skips[4])},
                        **summary,
                    }
                    tab={
                        "asset":asset,"price_source":source,"supertrend_flip":flip_name,
                        "same_minute_order":tie_name,
                        **{f"full22_{n}":v for n,v in summary["full22"].items()},
                        "positive_months":summary["positive_months"],
                        "training2025_usd":summary["train2025"]["net_usd"],
                        "holdout2026_usd":summary["holdout2026_jan_oct"]["net_usd"],
                        **{f"week_{n}":v for n,v in summary["week_partial"].items()},
                    }
                    table.append(tab)
                    pd.DataFrame(summary["monthly"]).to_csv(OUT/f"{k}_monthly.csv",index=False)
                    pd.DataFrame(summary["daily_ist"]).to_csv(OUT/f"{k}_daily_ist.csv",index=False)
                    d=to_frame(raw)
                    if len(d):
                        week=d.loc[(pd.to_datetime(d.exit_utc,utc=True)>=pd.Timestamp(WEEK_START,unit="s",tz="UTC"))&
                                   (pd.to_datetime(d.exit_utc,utc=True)<pd.Timestamp(END,unit="s",tz="UTC"))]
                    else:
                        week=d
                    week.to_csv(OUT/f"{k}_week_trades.csv",index=False)
                    d.to_csv(OUT/f"{k}_all_trades.csv.gz",index=False,compression="gzip")
                    print("FIXED_TP200_SL200",k,json.dumps({
                        "full22":summary["full22"],"week":summary["week_partial"],
                        "positive_months":summary["positive_months"],
                        "train2025":summary["train2025"]["net_usd"],
                        "test2026":summary["holdout2026_jan_oct"]["net_usd"]}),flush=True)
        del args
    pd.DataFrame(table).to_csv(OUT/"all_scenarios_comparison.csv",index=False)
    (OUT/"summary.json").write_text(json.dumps(report,indent=2)+"\n")
    print("FIXED_TP200_SL200_REPLAY_SUCCESS",OUT,flush=True)

if __name__=="__main__":
    main()
