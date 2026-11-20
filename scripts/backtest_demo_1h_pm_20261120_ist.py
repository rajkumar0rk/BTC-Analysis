#!/usr/bin/env python3
"""Research-only Delta DEMO testnet 1H EMA20+Supertrend 100/50 replay.

Friday November 20, 2026 IST, with genuine Delta Demo 1-hour OHLCV and
1-minute MARK OHLC, not production-market candles. Exact 3-second mark stream
and tick/order fills are NOT available historically; the baseline trailing
observation is the completed one-minute mark CLOSE. Favorable minute extremes
are shown as a separate sensitivity, NEVER as confirmed 3-second observations.

1H signal uses EXACT EMA/ATR/Supertrend indicator port from Delta-Algo-Demo.
Filter master OFF. 1h bar closes -> bot waits ~10s for data -> estimated fill
NEXT complete-minute OPEN, a conservative one-minute-delay approximation.
Bar flip exits at that same minute-open; protective stops trigger on mark.
Position sizing mirrors portfolio_size_contracts (PM shock=1%, budget=$10
sizing target, 100x notional ceiling); $10 is NOT isolated account collateral.
Entire assumed $100 portfolio is at risk. No daily/trade caps.

Portfolio-margin and native stop assumptions:
- Assume NO other account positions for single-product synthetic PM preliq stop,
  OR disable that synthetic stop when other account exposures exist.
- True Delta Demo PM account collateral/positions/liquidation not available.
- Uses original 1H 2*ATR14 initial protective stop, mark-triggered, trailed
  BTC 100/50 and ETH scaled by entry/80000 rounded half up to 0.05.
- Actual per-poll exchange PUT edits, mark/last basis, missing orders, latency,
  stale quotes and order rejections cannot be verified.
- Proxy fills at mark-triggered stop; not an actual executable price.
- Standard taker fee 0.05%/side and GST18%; optionally HYPOTHETICAL 27-min
  Scalper exit waiver. Funding, spreads, and actual Demo exchange fees excluded.

No exchange writes or VPS process changes. Source data and trade ledger saved.
"""
from __future__ import annotations

import json
import math
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from replay_btc_ema_st_screenshot import indicators

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "analysis" / "demo_1h_pm_nov20_ist_2026"
OUT.mkdir(parents=True,exist_ok=True)

API="https://cdn-ind.testnet.deltaex.org"
TZ="Asia/Kolkata"
WARMUP_START=pd.Timestamp("2026-10-01 00:00:00",tz="UTC")
ENTRY_START=pd.Timestamp("2026-11-20 00:00:00",tz=TZ).tz_convert("UTC")
ENTRY_END=pd.Timestamp("2026-11-21 00:00:00",tz=TZ).tz_convert("UTC")
INITIAL=100.0
BUDGET=10.0
LEVERAGE_LIMIT=100
PM_SHOCK_PCT=1.0
PM_MAINTENANCE_RATIO=0.75
TAKER_FEE=0.0005
GST=0.18
WAIVER_MINS=27
WAIT_MINUTES=1
MAX_DEVIATION=.002

def request(path,params):
    url=API+path+("?"+urllib.parse.urlencode(params) if params else "")
    last=None
    for attempt in range(4):
        try:
            req=urllib.request.Request(url,headers={"Accept":"application/json","User-Agent":"BTC-Analysis-Demo-1h-replay/1.0"})
            with urllib.request.urlopen(req,timeout=35) as reply:
                payload=json.load(reply)
            if not isinstance(payload,dict) or payload.get("success") is not True:
                raise ValueError("Delta Demo API unsuccessful: "+str(payload)[:250])
            return payload.get("result")
        except Exception as exc:
            last=exc
            if attempt<3:time.sleep(1.5*(attempt+1))
    raise RuntimeError(f"Public Demo API GET failed for {path} with {params}: {last}")

def candles(symbol,res,start,end):
    step=3600 if res=="1h" else 60
    batch=1100
    result={}
    for lo in range(int(start.timestamp()),int(end.timestamp()),batch*step):
        hi=min(lo+batch*step,int(end.timestamp()))
        rows=request("/v2/history/candles",{
            "symbol":symbol,"resolution":res,"start":lo,"end":hi-1,
        })
        if not isinstance(rows,list):
            raise ValueError(f"Unexpected history response shape {symbol} {res}")
        for row in rows:
            t=int(row["time"])
            if lo<=t<hi:
                if t in result:
                    raise ValueError(f"Duplicate candle {symbol} {res} {t}")
                result[t]=row
        print("FETCH",symbol,res,lo,hi,len(rows),flush=True)
        time.sleep(.10)

    expected=np.arange(int(start.timestamp()),int(end.timestamp()),step,dtype="int64")
    present=np.array(sorted(result),dtype="int64")
    if not np.array_equal(expected,present):
        missing=np.setdiff1d(expected,present)
        extra=np.setdiff1d(present,expected)
        raise ValueError(f"{symbol} {res} incomplete, missing {len(missing)} extra {len(extra)}; first missing {missing[:8]}")
    f=pd.DataFrame([result[int(x)] for x in present])
    for name in ("open","high","low","close","volume"):
        if name not in f: f[name]=np.nan
        f[name]=pd.to_numeric(f[name],errors="coerce")
    if f[["open","high","low","close"]].isna().any().any():
        raise ValueError(f"{symbol} {res} invalid OHLC")
    if f[["open","high","low","close"]].min().min()<=0:
        raise ValueError(f"{symbol} {res} nonpositive price")
    if (f.high<f[["open","low","close"]].max(axis=1)).any() or (f.low>f[["open","high","close"]].min(axis=1)).any():
        raise ValueError(f"{symbol} {res} OHLC inconsistency")
    if res=="1h" and f.volume.isna().any():
        raise ValueError(f"{symbol} hourly missing traded volume")
    f["time"]=present
    f["dt"]=pd.to_datetime(f.time,unit="s",utc=True)
    return f.set_index("dt")[["time","open","high","low","close","volume"]]


def product_specs(asset):
    symbol=asset+"USD"
    p=request("/v2/products/"+symbol,None)
    if not isinstance(p,dict):
        raise ValueError(f"Cannot validate Demo testnet {symbol} product")
    value=float(p["contract_value"])
    tick=float(p["tick_size"])
    if value<=0 or tick<=0:
        raise ValueError("Unusable Demo contract value/tick")
    return {"product_id":p["id"],"symbol":p["symbol"],"value":value,"tick":tick,
            "maintenance_margin":p.get("maintenance_margin"),"state":p.get("state"),
            "trading_status":p.get("trading_status")}


def round_stop(raw,tick,side):
    # Exact Demo signals.quantize_stop: long toward entry UP, short DOWN.
    return (math.ceil((raw-1e-9)/tick)*tick if side==1
            else math.floor((raw+1e-9)/tick)*tick)

def pm_size(entry,value):
    notional_limit=BUDGET/max(PM_SHOCK_PCT/100,.005)
    by_target=math.floor(BUDGET*LEVERAGE_LIMIT/(entry*value)+1e-10)
    by_pm=math.floor(notional_limit/(entry*value)+1e-10)
    return max(0,min(by_pm,by_target))

def pm_synthetic(entry,qty,side,equity,tick,asset):
    # Exact research port of Delta-Algo-Demo portfolio_liquidation_proxy.
    rate=max(.005,PM_SHOCK_PCT/100)*PM_MAINTENANCE_RATIO
    net_equity=equity-qty*entry*TAKER_FEE*(1+GST)
    if net_equity<=0:return None,None
    if side==1:
        boundary=(qty*entry-net_equity)/(qty*(1-rate))
        if boundary<=0:return None,None
    else:
        boundary=(qty*entry+net_equity)/(qty*(1+rate))
    buffer=1.0 if asset=="BTC" else .2
    near=round_stop(boundary+side*buffer,tick,side)
    if side*(near-entry)>=0:return boundary,None
    return boundary,near

def candidate_signals(frame,asset):
    f=indicators(frame[["open","high","low","close","volume"]])
    events={}
    candidates=[]
    for i in range(1,len(f)):
        t=f.index[i]+pd.Timedelta(hours=1)
        event_at=t+pd.Timedelta(minutes=WAIT_MINUTES)
        if not ENTRY_START<=event_at<ENTRY_END:continue
        current=f.iloc[i];prev=f.iloc[i-1]
        if not (np.isfinite(current.ema) and np.isfinite(current.atr14)):
            continue
        flip=(int(current.dir)!=int(prev.dir))
        side=0
        if int(current.dir)==int(prev.dir)==-1 and current.low<=current.ema and current.close>current.ema:
            side=1
        elif int(current.dir)==int(prev.dir)==1 and current.high>=current.ema and current.close<current.ema:
            side=-1
        token=int(event_at.timestamp())
        if token in events:raise AssertionError("double hourly event")
        events[token]={
            "side":side,"flip_direction":int(current.dir) if flip else 0,
            "signal_close":float(current.close),
            "atr_stop_dist":max(.5 if asset=="BTC" else .05,
                                round(2*float(current.atr14)/(.5 if asset=="BTC" else .05))*(.5 if asset=="BTC" else .05)),
            "signal_bar_utc":str(f.index[i]),"signal_time_utc":str(t),
            "signal_atr":float(current.atr14),
            "ema":float(current.ema),
            "signal_vol_ratio":float(current.volume_ratio) if np.isfinite(current.volume_ratio) else None,
        }
        if side:
            candidates.append({
                "signal_at_utc":str(t),
                "earliest_simulated_action_utc":str(event_at),
                "action_ist":str(event_at.tz_convert(TZ)),
                "side":"long" if side==1 else "short",
                "signal_close":float(current.close),
                "signal_bar_utc":str(f.index[i]),
                "volume_gate":"DISABLED_1H_PROFILE",
            })
    return events,candidates

def precheck(side,mo,mh,ml,stop):
    # Existing native stop can trigger on MARK within minute. Executed price
    # is *assumed equal to mark stop*, except an opening gap.
    if side==1 and mo<=stop:return float(mo),"native_stop_gap"
    if side==-1 and mo>=stop:return float(mo),"native_stop_gap"
    if side==1 and ml<=stop:return float(stop),"native_stop"
    if side==-1 and mh>=stop:return float(stop),"native_stop"
    return None,None

def backtest(asset,minute,mark,events,product,observation,external,waiver):
    assert observation in ("close","extreme")
    assert len(minute)==len(mark)==1440
    assert np.array_equal(minute.time.to_numpy(),mark.time.to_numpy())
    tick=product["tick"];value=product["value"]
    idx=minute.index
    op=minute.open.to_numpy(dtype=float)
    close=minute.close.to_numpy(dtype=float)
    mo=mark.open.to_numpy(dtype=float)
    mh=mark.high.to_numpy(dtype=float)
    ml=mark.low.to_numpy(dtype=float)
    mc=mark.close.to_numpy(dtype=float)

    wallet=INITIAL
    pos=None
    peak=INITIAL
    worst_dd=0.
    attempted=0
    skips=[]
    trades=[]
    for j in range(len(minute)):
        t=int(minute.time.iloc[j])
        evt=events.get(t)
        existed=pos is not None
        fill=None;reason=None

        if existed:
            # At decision minute's OPEN, previously active native stop at OPEN
            # protects first; if no gap, completed-hour flip exits now.
            p=pos
            if (p["side"]==1 and mo[j]<=p["stop"] or
                p["side"]==-1 and mo[j]>=p["stop"]):
                fill=float(mo[j]);reason="stop_open_gap"
            elif evt and evt["flip_direction"]==p["side"]:
                fill=float(op[j]);reason="supertrend_flip"
            else:
                fill,reason=precheck(p["side"],mo[j],mh[j],ml[j],p["stop"])

        if not existed and evt and evt["side"]:
            attempted+=1
            side=int(evt["side"])
            px=float(op[j])
            why=None
            if abs(px-evt["signal_close"])/evt["signal_close"]>MAX_DEVIATION:
                why="skip_price_moved_gt_0.2pct"
            elif wallet < BUDGET+1:
                why="skip_wallet_below_margin_plus_1"
            else:
                count=pm_size(px,value)
                if count<=0:why="skip_less_than_one_contract"
                else:
                    qty=count*value
                    initial=round_stop(px-side*evt["atr_stop_dist"],tick,side)
                    liquidation=None
                    near=None
                    # No historical account exposure feed. Scenario explicitly
                    # models single-instrument vs existing external exposure.
                    if not external:
                        liquidation,near=pm_synthetic(px,qty,side,wallet,tick,asset)
                    stop=(max(initial,near) if side==1 else min(initial,near)) if near is not None else initial
                    if side*(stop-px)>=0:
                        why="skip_invalid_provisional_stop"
                    elif side==1 and mo[j]<=stop or side==-1 and mo[j]>=stop:
                        why="skip_mark_already_crossed_protective_stop"
                    else:
                        activation=(100. if asset=="BTC" else
                                    max(tick,math.floor((px*100/80000)/tick+.5)*tick))
                        distance=(50. if asset=="BTC" else
                                  max(tick,math.floor((px*50/80000)/tick+.5)*tick))
                        pos=dict(
                            side=side,entry=px,count=count,qty=qty,
                            entry_j=j,entry_ts=str(idx[j]),stop=stop,
                            initial_stop=stop,initial_atr_stop=initial,
                            modeled_preliq=near,modeled_pm_boundary=liquidation,
                            best=px,trail_active=False,activation=activation,
                            distance=distance,signal_bar=evt["signal_bar_utc"],
                            signal_time=evt["signal_time_utc"],
                        )
                        fill,reason=precheck(side,mo[j],mh[j],ml[j,],stop)
            if why is not None:
                skips.append(dict(ist=str(idx[j].tz_convert(TZ)),side=side,
                                  price=px,reason=why))
        elif existed and evt and evt["side"]:
            skips.append(dict(ist=str(idx[j].tz_convert(TZ)),side=int(evt["side"]),
                              price=float(op[j]),reason="skip_position_already_open"))

        if pos is not None and reason is not None:
            p=pos
            side=p["side"]
            # Proxy fills at mark-trigger; exact bid/ask and delay unavailable.
            exit_px=float(fill)
            minutes=j-p["entry_j"]
            gross=(exit_px-p["entry"])*side*p["qty"]
            entry_fee=p["entry"]*p["qty"]*TAKER_FEE
            discount=bool(waiver and minutes<=WAIVER_MINS)
            exit_fee=0.0 if discount else exit_px*p["qty"]*TAKER_FEE
            gst=(entry_fee+exit_fee)*GST
            net=gross-entry_fee-exit_fee-gst
            before=wallet
            wallet+=net
            peak=max(peak,wallet)
            worst_dd=max(worst_dd,100*(1-wallet/peak))
            trades.append(dict(
                entry_ist=str(idx[p["entry_j"]].tz_convert(TZ)),
                exit_ist=str(idx[j].tz_convert(TZ)),
                side="long" if side==1 else "short",
                entry=p["entry"],exit_proxy=exit_px,
                points=round((exit_px-p["entry"])*side,4),
                qty=p["qty"],contracts=p["count"],
                gross_usd=round(gross,4),entry_fee_usd=round(entry_fee,4),
                exit_fee_usd=round(exit_fee,4),gst_usd=round(gst,4),
                net_usd=round(net,4),balance_after=round(wallet,4),
                hold_minutes=minutes,exit_reason=reason,
                mark_stop_at_exit=p["stop"],initial_stop=p["initial_stop"],
                atr_stop=p["initial_atr_stop"],
                modeled_pm_boundary=p["modeled_pm_boundary"],
                modeled_preliq=p["modeled_preliq"],
                trailing_active_at_exit=p["trail_active"],
                signal_bar_utc=p["signal_bar"],
                scalper_discount_hypothetical=discount))
            pos=None
        if pos is not None:
            p=pos
            # Completed 1m mark observation updates the next minute stop.
            obs=float(mc[j]) if observation=="close" else (
                float(mh[j]) if p["side"]==1 else float(ml[j]))
            side=p["side"]
            if side*(obs-p["entry"])>=p["activation"]:
                p["trail_active"]=True
            if p["trail_active"]:
                p["best"]=max(p["best"],obs) if side==1 else min(p["best"],obs)
                candidate=round_stop(p["best"]-side*p["distance"],tick,side)
                p["stop"]=max(p["stop"],candidate) if side==1 else min(p["stop"],candidate)

    opened=pos
    unrealized=None
    if opened is not None:
        p=opened
        gross=(float(close[-1])-p["entry"])*p["side"]*p["qty"]
        unrealized=dict(entry_ist=str(idx[p["entry_j"]].tz_convert(TZ)),
                        side="long" if p["side"]==1 else "short",
                        entry=p["entry"],last_traded_close=float(close[-1]),
                        mark_close=float(mc[-1]),stop=p["stop"],gross_open_usd=round(gross,4),
                        note="OPEN at IST day end; gross unrealized excludes closing costs")
    df=pd.DataFrame(trades)
    wins=sum(row["net_usd"] for row in trades if row["net_usd"]>0)
    losses=-sum(row["net_usd"] for row in trades if row["net_usd"]<0)
    result=dict(
        asset=asset,day_ist="2026-11-20",
        method=f"1h signal / 1m Demo MARK {observation} observations, +1m decision delay",
        account="hypothetical standalone 100USD Portfolio Margin account",
        other_instruments_assumed=bool(external),
        preliq_model="DISABLED_EXTERNAL_EXPOSURE" if external else "SYNTHETIC_PM_ONLY",
        scalper_waiver_hypothetical=bool(waiver),
        starting_usd=INITIAL,ending_realized_usd=round(wallet,4),
        net_realized_usd=round(wallet-INITIAL,4),
        closed_trades=len(trades),open_at_end=unrealized,
        attempts_when_flat=attempted,skipped=skips,
        wins=sum(1 for x in trades if x["net_usd"]>0),
        losses=sum(1 for x in trades if x["net_usd"]<0),
        win_rate_pct=round(100*sum(x["net_usd"]>0 for x in trades)/len(trades),2) if trades else None,
        pf=round(wins/losses,4) if losses else None,
        max_closed_equity_drawdown_pct=round(worst_dd,2),
        totals=dict(gross=round(sum(t["gross_usd"] for t in trades),4),
                    entry_fee=round(sum(t["entry_fee_usd"] for t in trades),4),
                    exit_fee=round(sum(t["exit_fee_usd"] for t in trades),4),
                    gst=round(sum(t["gst_usd"] for t in trades),4)))
    return df,result

def test():
    assert pm_size(60000,.001)==16
    assert pm_size(1700,.01)==58
    assert round_stop(100.26,.5,1)==100.5
    assert round_stop(100.26,.5,-1)==100.0
    assert precheck(1,100,105,89,90)==(90.0,"native_stop")
    assert precheck(-1,100,111,90,110)==(110.0,"native_stop")
    assert precheck(1,80,105,79,90)==(80.0,"native_stop_gap")
    assert pm_synthetic(60000,.016,-1,100,.5,"BTC")[1]>60000
    assert pm_synthetic(1700,.58,1,100,.05,"ETH")[1]<1700

def main():
    test()
    meta=dict(
        date_ist="2026-11-20",timezone=TZ,
        repo_profile="ema20_st_1h_100_50",
        source_base_url=API,
        actual_vps_profile_verified_this_run=False,
        historical_3_second_feed=False,
        actual_exchange_order_fills_verified=False,
        entry_logic="1h EMA20 pullback + ST (10,3) stable direction, no ATR/volume entry gate",
        entry_delay_assumption="+1 minute after hourly close for 10s finalized candle rule",
        trailing_100_50="BTC 100/50, ETH proportional to entry/80000 with tick rounding",
        portfolio="PM 1pct shock, initial equity hypothetical $100, $10 sizing target, 100x maximum notional ceiling; not isolated margin",
        execution="1m mark OHLC existing stop touches; mark CLOSE trailing updates next minute; optimistic favorable extreme sensitivity separate",
        stop="1h 2xATR14 initial stop, optional synthetic single-position PM preliq only if no other instruments",
        fee="0.05% taker entry/exit plus 18% GST; unverified 27min waived exit hypothesis",
        exclusions=["tick-by-tick 3s sampling","historical bid/ask","historical actual account portfolio equity and other positions",
                    "real Delta account liquidation","funding","actual order rejects/stop-edit latency"],
        dataset={},scenario={}
    )
    for asset in ("BTC","ETH"):
        product=product_specs(asset)
        h=candles(asset+"USD","1h",WARMUP_START,ENTRY_END)
        trade=candles(asset+"USD","1m",ENTRY_START,ENTRY_END)
        mark=candles("MARK:"+asset+"USD","1m",ENTRY_START,ENTRY_END)
        if len(trade)!=1440 or len(mark)!=1440 or not (trade.index==mark.index).all():
            raise AssertionError("INCOMPLETE DEMO MARK/trade minute data")
        h.to_csv(OUT/f"{asset.lower()}_demo_1h_source.csv.gz",compression="gzip")
        trade.to_csv(OUT/f"{asset.lower()}_demo_traded_1m_source.csv.gz",compression="gzip")
        mark.to_csv(OUT/f"{asset.lower()}_demo_mark_1m_source.csv.gz",compression="gzip")
        ev,candidates=candidate_signals(h,asset)
        meta["dataset"][asset]=dict(product=product,
            hourly_bars=len(h),trade_minutes=len(trade),mark_minutes=len(mark),
            first_hour_utc=str(h.index[0]),last_hour_utc=str(h.index[-1]),
            mark_start_utc=str(mark.index[0]),mark_end_utc=str(mark.index[-1]),
            candidate_signals=candidates)
        for external in (False,True):
            for sampling in ("close","extreme"):
                for offer in (False,True):
                    label=f"{asset.lower()}_{'shared' if external else 'single'}_{sampling}_{'offer' if offer else 'nooffer'}"
                    table,stats=backtest(asset,trade,mark,ev,product,sampling,external,offer)
                    table.to_csv(OUT/f"{label}_trades.csv",index=False)
                    meta["scenario"][label]=stats
                    print("DEMO_1H_PM_RESULT",label,json.dumps(stats),flush=True)
    (OUT/"summary.json").write_text(json.dumps(meta,indent=2)+"\n",encoding="utf-8")
    print("SUCCESS_DEMO_1H_PM_NOV20",OUT,flush=True)

if __name__=="__main__":
    main()
