#!/usr/bin/env python3
"""Full-history 1H EMA20+Supertrend ATR-based TAKE-PROFIT exit experiment.

Backtest 4 proposed variants:
 A: BTC-equivalent activation 500 pts, hourly trailing gap 1.0*ATR14
 B: activation 800 pts, hourly trailing gap 1.5*ATR14  (proposed start)
 C: activation 1000 pts, hourly trailing gap 2.0*ATR14
 D: activation 1500 pts, hourly trailing gap 3.0*ATR14

ETH activation is scaled BTC-equivalent via entry*points/80000, rounded to 0.05.
ATR14 uses native BTC/ETH 1H traded-price candles.

Common entry / protection:
 - existing 1H EMA20 touch/reclaim + continuing ST10,3 entry, in both directions
 - 1h signal confirmed at bar close; entry at next 1m traded OPEN (proxy)
 - no entry if >0.2% deviation from previous 1H signal close
 - initial 2x ATR14 emergency stop ALWAYS checked using native MARK 1m OHLC
 - 1H opposite-Supertrend flip exits on next H boundary
 - ONE position per instrument, fixed ~$1,000 trade notional research sizing

Common profit stop level (not TradingView's separate fixed-distance control):
 - only activate once a COMPLETED 1H CLOSE is favorable by activation points
 - track most favorable COMPLETED 1H CLOSE since entry
 - at each completed 1H CLOSE, trail gap=ATR_multiplier*that hour's ATR14
 - protective profit stop never loosens
 - a newly calculated profit stop is effective NEXT 1H BAR, not the hour
   whose candle determined the level
 - exit modes (both always include 1m emergency stop):
      H_CLOSE: exit when next COMPLETED 1H CLOSE crosses the previously
               installed profit stop; send exit next 1m traded OPEN
      M1_TRIGGER: check installed hourly profit stop using successive 1m
                  candle highs/lows; model fill at same 1m traded CLOSE
 - data source sensitivity for *profit* triggers is MARK vs TRADED price;
   emergency stop remains MARK price in all modes.

Critical: The profit anchor is completed 1H CLOSE, NOT completed 1H HIGH/LOW.
This prevents assuming the hour's high occurs before its low. The H_CLOSE
mode cannot protect a gain from hourly intra-bar reversal; 1m emergency
remains active. Native exchange 1H close-based exit is software-driven and
requires a daemon running at hourly close; not a native exchange stop order.

Dataset: Delta India PRODUCTION 1m trade and 1m MARK prices, archived,
full Jan2025 - Oct2026 UTC, Nov2026 deliberately excluded. This is NOT
historical Delta Demo prices, true fills, or a validated live execution path.
For stops hit inside 1m, exit at 1m traded CLOSE (model only), NOT stop price.
No reconstruction of 1m intrabar order, book, latency or slippage.

Fee 0.05% taker EACH leg plus 18% GST. Funding omitted, not assumed zero.
Sizing: per instrument reference notional ceiling ~$1,000, no wallet cap,
no PM liquidation, hence NEGATIVE accumulated balances are not executable
on a $100 starting wallet. This is for strategy-comparison research only.
No editing main branch, no trading orders or live bots.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from numba import njit

from full_history_1h_trailing_100_50_2025_2026 import read_asset,signal_map
from replay_btc_ema_st_screenshot import indicators
from optimize_1h_additional_trailing_stop_points_20261121 import stop_round,point_scale

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"analysis"/"atr_take_profit_1h_close_vs_1m_full22_20261121"
OUT.mkdir(parents=True,exist_ok=True)
FULL_END_EXCLUSIVE=int(pd.Timestamp("2026-11-01",tz="UTC").timestamp())
MONTHS=[str(m) for m in pd.period_range("2025-01","2026-10",freq="M")]
VARIANTS=(("A",500,1.0),("B",800,1.5),("C",1000,2.0),("D",1500,3.0))
MODELS=(("H_CLOSE",0),("M1_TRIGGER",1))
PRICE_SOURCES=(("MARK",0),("TRADED",1))
FEE=.0005
GST=.18
ENTRY_DIVERGENCE=.002
MAX_NOTIONAL=1000.

@njit(cache=True)
def replay(ts,t_o,t_c,m_o,m_h,m_l,m_c,tr_h,tr_l,
           sig,flip,signal_close,initial_dist,h_atr_end,
           activation_points,multiplier,asset_eth,exit_mode,profit_source):
    """One 1m-causal execution. Result cols:
       entry_s exit_s side entry_px exit_px qty gross fees net
       initial_stop final_profit_stop activation_usd num_trail_updates
       exit_code hours_held 
       exit codes: 1 mark gap emergency; 2 flip; 3 1m emergency;
                   4 1m profit; 5 1H close profit; 6 1m profit opening gap
    """
    n=len(ts)
    tick=.05 if asset_eth else .5
    contract=.01 if asset_eth else .001
    trades=np.zeros((10000,15),dtype=np.float64)
    ntrades=0
    skips=np.zeros(4,dtype=np.int64)
    active=0;side=0
    entry=0.;qty=0.;entry_time=0
    emergency=0.;profit_stop=0.;profit_active=0
    activation=0.;best_close=0.;trail_edits=0
    pending_hour_profit_exit=0
    for i in range(n):
        minute_t=ts[i]
        entry_signal=sig[i]
        was_active=active==1
        exit_code=0
        fill=0.
        if was_active:
            # The close-confirmed exit is queued at the PREVIOUS completed 1H
            # bar close and can be filled only at this next minute OPEN.
            if pending_hour_profit_exit==1:
                exit_code=5
                fill=t_o[i]
            elif flip[i]==side:
                exit_code=2
                fill=t_o[i]
            elif (side==1 and m_o[i]<=emergency) or (side==-1 and m_o[i]>=emergency):
                exit_code=1
                fill=t_o[i]
            elif exit_mode==1 and profit_active==1:
                obs_o=m_o[i] if profit_source==0 else t_o[i]
                if (side==1 and obs_o<=profit_stop) or (side==-1 and obs_o>=profit_stop):
                    exit_code=6
                    fill=t_o[i]
        if not was_active and entry_signal!=0:
            s=entry_signal
            ep=t_o[i]
            if abs(ep-signal_close[i])/signal_close[i]>ENTRY_DIVERGENCE:
                skips[0]+=1
            else:
                contracts=math.floor(MAX_NOTIONAL/(ep*contract)+1e-10)
                if contracts<1:
                    skips[1]+=1
                else:
                    emergency_candidate=stop_round(ep-s*initial_dist[i],tick,s)
                    if (s==1 and m_o[i]<=emergency_candidate) or (s==-1 and m_o[i]>=emergency_candidate):
                        skips[2]+=1
                    else:
                        active=1;side=s;entry=ep;qty=contracts*contract
                        entry_time=minute_t
                        emergency=emergency_candidate
                        profit_stop=0.;profit_active=0
                        pending_hour_profit_exit=0
                        activation=point_scale(activation_points,ep,tick,asset_eth)
                        best_close=ep
                        trail_edits=0
        elif was_active and entry_signal!=0:
            skips[3]+=1

        if active==0:
            continue

        if exit_code==0:
            # Initial 2*ATR stop is checked on EVERY minute for BOTH exit modes.
            if (side==1 and m_l[i]<=emergency) or (side==-1 and m_h[i]>=emergency):
                exit_code=3
                fill=t_c[i]
            elif exit_mode==1 and profit_active==1:
                # Intra-minute profit trailing uses LAST COMPLETED hourly stop,
                # NEVER computes a stop using this unfinished minute's HIGH.
                o_l=m_l[i] if profit_source==0 else tr_l[i]
                o_h=m_h[i] if profit_source==0 else tr_h[i]
                if (side==1 and o_l<=profit_stop) or (side==-1 and o_h>=profit_stop):
                    exit_code=4
                    fill=t_c[i]

            if exit_code==0 and minute_t%3600==3540:
                # COMPLETE HOUR. The ATR and close now become observable.
                hour_close=m_c[i] if profit_source==0 else t_c[i]
                if exit_mode==0 and profit_active==1:
                    # Evaluate PREVIOUSLY installed stop BEFORE refreshing it.
                    if (side==1 and hour_close<=profit_stop) or (side==-1 and hour_close>=profit_stop):
                        pending_hour_profit_exit=1
                # If exit is pending the hour just finished, don't adjust
                # the stop using the same closing value.
                if pending_hour_profit_exit==0 and np.isfinite(h_atr_end[i]) and h_atr_end[i]>0:
                    if side==1:
                        best_close=max(best_close,hour_close)
                    else:
                        best_close=min(best_close,hour_close)
                    if side*(best_close-entry)>=activation:
                        was_activated=profit_active
                        profit_active=1
                        candidate=stop_round(best_close-side*(multiplier*h_atr_end[i]),tick,side)
                        if was_activated==0:
                            profit_stop=candidate
                            trail_edits+=1
                        else:
                            tightened=max(profit_stop,candidate) if side==1 else min(profit_stop,candidate)
                            if abs(tightened-profit_stop)>tick/2:
                                profit_stop=tightened
                                trail_edits+=1

        if exit_code!=0:
            gross=(fill-entry)*side*qty
            fees=(entry+fill)*qty*FEE*(1.+GST)
            net=gross-fees
            if ntrades>=len(trades):
                raise ValueError("Exceeded trade ledger buffer")
            trades[ntrades,0]=entry_time
            trades[ntrades,1]=minute_t
            trades[ntrades,2]=side
            trades[ntrades,3]=entry
            trades[ntrades,4]=fill
            trades[ntrades,5]=qty
            trades[ntrades,6]=gross
            trades[ntrades,7]=fees
            trades[ntrades,8]=net
            trades[ntrades,9]=emergency
            trades[ntrades,10]=profit_stop if profit_active==1 else np.nan
            trades[ntrades,11]=activation
            trades[ntrades,12]=trail_edits
            trades[ntrades,13]=exit_code
            trades[ntrades,14]=(minute_t-entry_time)/3600.
            ntrades+=1
            active=0
            pending_hour_profit_exit=0
    end_info=np.zeros(6,dtype=np.float64)
    if active==1:
        end_info[0]=1
        end_info[1]=entry_time
        end_info[2]=entry
        end_info[3]=side
        end_info[4]=emergency
        end_info[5]=profit_stop if profit_active==1 else np.nan
    return trades[:ntrades],skips,end_info

def data_arrays(asset):
    trade,mark,provenance=read_asset(asset)
    mask=trade.time.to_numpy(dtype=np.int64)<FULL_END_EXCLUSIVE
    trade=trade.loc[mask].copy()
    mark=mark.loc[mask].copy()
    ts=trade.time.to_numpy(dtype=np.int64)
    assert len(ts)==len(mark) and np.array_equal(ts,mark.time.to_numpy(dtype=np.int64))
    assert ts[0]==int(pd.Timestamp("2025-01-01",tz="UTC").timestamp())
    assert ts[-1]==FULL_END_EXCLUSIVE-60
    assert np.all(np.diff(ts)==60)

    events,signals_meta=signal_map(trade,asset)
    n=len(ts)
    sig=np.zeros(n,dtype=np.int8);flips=np.zeros(n,dtype=np.int8)
    close=np.zeros(n,dtype=np.float64);dist=np.zeros(n,dtype=np.float64)
    first=int(ts[0])
    for when,event in events.items():
        if when>=FULL_END_EXCLUSIVE:continue
        idx=(int(when)-first)//60
        if idx<0 or idx>=n or int(ts[idx])!=when:
            raise ValueError(f"Hour event misaligned: {asset}, {when}")
        sig[idx]=int(event["side"])
        flips[idx]=int(event["flip"])
        close[idx]=float(event["close"])
        dist[idx]=float(event["stopdist"])
    h=trade.resample("1h",origin="epoch",label="left",closed="left").agg({
        "open":"first","high":"max","low":"min","close":"last","volume":"sum","time":"count"
    })
    assert bool((h.time==60).all())
    hourly=indicators(h.drop(columns=["time"]))
    h_atr=np.zeros(n,dtype=np.float64)
    for when,value in zip(hourly.index.hourly if False else hourly.index, hourly.atr14.to_numpy(dtype=np.float64)):
        ix=(int(when.timestamp())+3540-first)//60
        if ix<0 or ix>=n:raise ValueError("Hour ATR idx out of range")
        assert ts[ix]==int(when.timestamp())+3540
        h_atr[ix]=value
    assert np.count_nonzero(h_atr)>len(hourly)*.9
    args=[
      ts,
      trade.open.to_numpy(dtype=np.float64),
      trade.close.to_numpy(dtype=np.float64),
      mark.open.to_numpy(dtype=np.float64),
      mark.high.to_numpy(dtype=np.float64),
      mark.low.to_numpy(dtype=np.float64),
      mark.close.to_numpy(dtype=np.float64),
      trade.high.to_numpy(dtype=np.float64),
      trade.low.to_numpy(dtype=np.float64),
      sig,flips,close,dist,h_atr
    ]
    return args,{**provenance,**signals_meta,"used_to_utc":str(trade.index[-1]),
                 "used_1m_rows":len(trade),"hour_bars":len(hourly),
                 "mark_trade_timestamps_identical":True}

def ledger_frame(array):
    cols=["entry_epoch","exit_epoch","side_num","entry_price","exit_price_proxy",
          "quantity","gross_usd","fees_gst_usd","net_usd","emergency_stop",
          "final_profit_stop","activation_native","profit_stop_updates",
          "exit_code","holding_hours"]
    df=pd.DataFrame(array,columns=cols)
    if len(df):
        df["entry_utc"]=pd.to_datetime(df.entry_epoch,unit="s",utc=True).astype(str)
        df["exit_utc"]=pd.to_datetime(df.exit_epoch,unit="s",utc=True).astype(str)
        df["month_utc"]=pd.to_datetime(df.exit_epoch,unit="s",utc=True).dt.strftime("%Y-%m")
        df["side"]=df.side_num.map({1.:"LONG",-1.:"SHORT"})
        df["exit_reason"]=df.exit_code.map({
            1.:"mark_emergency_open_gap",2.:"opposite_supertrend_flip",
            3.:"mark_emergency_1m_cross",4.:"profit_stop_1m_cross",
            5.:"profit_1h_close_next_open",6.:"profit_stop_open_gap"})
    return df.drop(columns=["entry_epoch","exit_epoch","side_num","exit_code"],errors="ignore")

def get_summary(df,months):
    selected=df.loc[df["month_utc"].isin(months)] if len(df) else df
    pos=float(selected.loc[selected.net_usd>0,"net_usd"].sum())
    neg=-float(selected.loc[selected.net_usd<0,"net_usd"].sum())
    wins=int((selected.net_usd>0).sum())
    losses=int((selected.net_usd<0).sum())
    running=np.r_[0.,np.cumsum(selected.net_usd.to_numpy())]
    dd=float(np.max(np.maximum.accumulate(running)-running))
    pmonth={}
    for m in months:
        a=selected.loc[selected.month_utc==m]
        p=float(a.loc[a.net_usd>0,"net_usd"].sum())
        l=-float(a.loc[a.net_usd<0,"net_usd"].sum())
        pmonth[m]={
            "net_usd":round(float(a.net_usd.sum()),4),
            "trades":len(a),"wins":int((a.net_usd>0).sum()),
            "losses":int((a.net_usd<0).sum()),
            "profit_factor":round(p/l,4) if l else None,
        }
    return {
        "net_usd":round(float(selected.net_usd.sum()),4),
        "gross_usd":round(float(selected.gross_usd.sum()),4),
        "fees_gst_usd":round(float(selected.fees_gst_usd.sum()),4),
        "trades":len(selected),"wins":wins,"losses":losses,
        "win_rate_pct":round(100*wins/len(selected),2) if len(selected) else None,
        "profit_factor":round(pos/neg,4) if neg else None,
        "max_closed_trade_drawdown_usd":round(dd,4),
        "positive_months":sum(x["net_usd"]>0 for x in pmonth.values()),
        "negative_months":sum(x["net_usd"]<0 for x in pmonth.values()),
        "zero_trade_months":sum(x["trades"]==0 for x in pmonth.values()),
        "monthly":pmonth,
    }

def unit_tests():
    # Same 1H candle may reach H close +15 and move the stop by 1 ATR
    # but MUST NOT fill a stop tightened by that same hour.
    n=180
    ts=np.arange(0,n,dtype=np.int64)*60
    t_o=np.full(n,100.,dtype=np.float64)
    t_c=np.full(n,114.,dtype=np.float64)
    m_o=np.full(n,114.,dtype=np.float64)
    m_h=np.full(n,115.,dtype=np.float64)
    m_l=np.full(n,111.,dtype=np.float64)
    m_c=np.full(n,114.,dtype=np.float64)
    # at entry minute, avoid look-ahead mark open weirdness
    t_c[0]=100.;m_o[0]=100.;m_h[0]=101.;m_l[0]=99.;m_c[0]=100.
    m_h[59]=115.;m_l[59]=99.;m_c[59]=115.
    m_o[60]=114.;m_h[60]=115.;m_l[60]=109.;m_c[60]=114.
    sig=np.zeros(n,dtype=np.int8);sig[0]=1
    flips=np.zeros(n,dtype=np.int8)
    close=np.zeros(n);close[0]=100.
    emergency_dist=np.zeros(n);emergency_dist[0]=10.
    hourly_atr=np.zeros(n);hourly_atr[59]=5.;hourly_atr[119]=5.;hourly_atr[179]=5.
    arrays=(ts,t_o,t_c,m_o,m_h,m_l,m_c,m_h,m_l,
            sig,flips,close,emergency_dist,hourly_atr)
    trig,_,_=replay(*arrays,10.,1.,0,1,0)
    hclose,_,e=replay(*arrays,10.,1.,0,0,0)
    assert len(trig)==1 and trig[0,1]==60*60 and trig[0,13]==4,(len(trig),trig)
    assert len(hclose)==0 and e[0]==1,(len(hclose),e)
    # If a later H closes through the installed stop, H_CLOSE exits at
    # next hour OPEN (not at a prior 1m wick, and no same-bar retroactive stop).
    m_c[119]=109.;t_c[119]=109.
    hclose2,_,_=replay(*arrays,10.,1.,0,0,0)
    assert len(hclose2)==1 and hclose2[0,1]==120*60 and hclose2[0,13]==5,(len(hclose2),hclose2)
    # An emergency 1m mark low cross exits even for hourly-close profit mode.
    m_l[1]=89.
    emergency,_,_=replay(*arrays,10.,1.,0,0,0)
    assert len(emergency)==1 and emergency[0,1]==60 and emergency[0,13]==3
    # Converted ETH activation uses BTC-equivalent price point scale.
    assert abs(point_scale(800,1600,.05,1)-16)<1e-8
    assert abs(point_scale(500,1600,.05,1)-10)<1e-8

def main():
    unit_tests()
    report={
        "title":"Full 22-month ATR-based hourly-close profit trailing vs 1m trigger",
        "date_start_utc":"2025-01-01 00:00 UTC",
        "date_end_inclusive_utc":"2026-10-31 23:59 UTC",
        "month_count":22,
        "venue":"Delta India production historical 1m MARK and traded OHLC, not Demo testnet",
        "signal":"1H EMA20 touch/reclaim + continuing Supertrend(10,3), no ATR/volume filters",
        "initial_stop":"2x ATR(14) at signal hour close; 1m MARK-triggered emergency stop always",
        "activation":"Requires confirmed favorable completed 1h close; ETH BTC-point equivalent scaled by entry/80000",
        "profit_trailing":"Best completed 1h CLOSE since entry +/- ATR14 multiplier; never loosens; applied next hour",
        "modes":{
            "H_CLOSE":"If completed 1h close crosses last installed profit stop, exit next 1m traded open",
            "M1_TRIGGER":"If 1m candle high/low crosses last installed profit stop, exit modeled same minute traded close",
        },
        "profit_price_source":{
            "MARK":"Use 1m MARK close for hourly profit anchor/confirmation; MARK 1m high/low for M1 trigger",
            "TRADED":"Use 1m TRADED close for hourly profit anchor/confirmation; TRADED 1m high/low for M1 trigger",
        },
        "fees":"0.05% taker EACH side +18% GST, no funding, no promo. Fill proxy, no bid/ask/orderbook slippage.",
        "equity":"Fixed ~$1000 notional target, no wallet gate; not a fundable $100 account model; no PM liquidation.",
        "lookahead_control":"Hourly signal & ATR computed from completed hour. Profit stop effective next hour only. 1m emergency uses preceding stop.",
        "limitations":"Intra-minute exact fill impossible from OHLC. H_CLOSE exit is NOT exchange native stop. Funding and PM not modeled.",
        "variants":{name:{"btc_equivalent_activation_pts":activation,"profit_trail_atr_multiplier":multiplier}
                    for name,activation,multiplier in VARIANTS},
        "datasets":{},"scenarios":{},"rankings":{}
    }
    records=[]
    for asset in ("BTC","ETH"):
        args,dataset_info=data_arrays(asset)
        report["datasets"][asset]=dataset_info
        compact=[]
        for label,activation,atr_mult in VARIANTS:
            for mode,mode_id in MODELS:
                for source,source_id in PRICE_SOURCES:
                    arr,skip,open_end=replay(*args,float(activation),float(atr_mult),
                                              int(asset=="ETH"),mode_id,source_id)
                    ledger=ledger_frame(arr)
                    full=get_summary(ledger,MONTHS)
                    in_sample=get_summary(ledger,MONTHS[:12])
                    holdout=get_summary(ledger,MONTHS[12:])
                    name=f"{asset.lower()}_{label}_{mode.lower()}_{source.lower()}"
                    ledger.to_csv(OUT/f"{name}_trades.csv.gz",
                                  index=False,compression="gzip")
                    pd.DataFrame([{"month_utc":m,**v} for m,v in full["monthly"].items()]).to_csv(
                        OUT/f"{name}_monthly.csv",index=False)
                    summary={
                        "asset":asset,"variant":label,"activation":activation,
                        "atr_multiplier":atr_mult,"exit_mode":mode,"profit_source":source,
                        "full22":full,"train_2025":{k:v for k,v in in_sample.items() if k!="monthly"},
                        "holdout_2026_jan_oct":{k:v for k,v in holdout.items() if k!="monthly"},
                        "open_at_2026_10_31_end":bool(open_end[0]),
                        "unrealized_open_position_details":{
                            "entry_time_utc":str(pd.Timestamp(int(open_end[1]),unit="s",tz="UTC")) if open_end[0] else None,
                            "entry_price":float(open_end[2]) if open_end[0] else None,
                            "side":"LONG" if open_end[3]==1 else "SHORT" if open_end[3]==-1 else None,
                            "emergency_stop":float(open_end[4]) if open_end[0] else None,
                            "profit_stop":float(open_end[5]) if open_end[0] and np.isfinite(open_end[5]) else None,
                        },
                        "skips":{"entry_deviation":int(skip[0]),"too_small":int(skip[1]),
                                 "bad_initial_mark_stop":int(skip[2]),"existing_position":int(skip[3])}
                    }
                    report["scenarios"][name]=summary
                    row={
                        "asset":asset,"variant":label,"activation":activation,"atr_multiplier":atr_mult,
                        "exit_mode":mode,"profit_source":source,
                        **{f"all22_{k}":v for k,v in full.items() if k!="monthly"},
                        "train2025_net_usd":in_sample["net_usd"],
                        "holdout2026_net_usd":holdout["net_usd"],
                        "holdout2026_pf":holdout["profit_factor"],
                        "has_open_position_at_end":bool(open_end[0]),
                    }
                    compact.append(row);records.append(row)
                    print("ATR_HYBRID",name,
                        json.dumps({k:full[k] for k in ["net_usd","trades","profit_factor",
                              "positive_months","max_closed_trade_drawdown_usd"]}),
                        flush=True)
        eligible=[x for x in compact if x["all22_trades"]>=50]
        # Report 2025-training-only best with untouched 2026 Jan-Oct validation.
        train_best=max(eligible,key=lambda x:x["train2025_net_usd"])
        full_best=max(eligible,key=lambda x:x["all22_net_usd"])
        most_months=max(eligible,key=lambda x:(x["all22_positive_months"],x["all22_net_usd"]))
        report["rankings"][asset]={
            "best_by_2025_training":train_best,
            "best_full22_in_sample":full_best,
            "most_profitable_months_in_sample":most_months,
            "any_full22_net_positive":any(x["all22_net_usd"]>0 for x in eligible),
            "top_by_net":sorted(eligible,key=lambda x:x["all22_net_usd"],reverse=True)[:8],
            "top_by_months":sorted(eligible,key=lambda x:(x["all22_positive_months"],x["all22_net_usd"]),reverse=True)[:8],
        }
        pd.DataFrame(compact).sort_values("all22_net_usd",ascending=False).to_csv(
            OUT/f"{asset.lower()}_all_variant_scores.csv",index=False)
        del args
    pd.DataFrame(records).to_csv(OUT/"both_assets_scenario_scores.csv",index=False)
    (OUT/"summary.json").write_text(json.dumps(report,indent=2)+"\n")
    print("ATR_HYBRID_FULL22_SUCCESS",OUT,flush=True)

if __name__=="__main__":
    main()
