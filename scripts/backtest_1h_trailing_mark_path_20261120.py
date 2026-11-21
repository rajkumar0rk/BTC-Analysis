#!/usr/bin/env python3
"""Independent 1H EMA20/Supertrend trailing-stop replay of Nov 20 2026 IST.

Research only: DEMO testnet 1h candles + authentic DEMO traded and mark
1-minute OHLC copied from the preceding archived backtest branch. Two causal
hypothetical within-minute price orders (O-H-L-C, O-L-H-C) are compared. Never
assert that a path occurred; neither 1m wick order nor the actual bot 3s polls
can be reconstructed from OHLC.

Entry decision is tested at the 1h close minute OPEN (early proxy) and CLOSE
(late proxy). Actual Demo bot often decides ~10 seconds after the close. Both
are boundaries/proxies, not known live decision prices.

Stops: native exchange MARK trigger, 2 ATR14 initial (and synthetic PM proxy
only for no external exposures), BTC 100-point activation / 50-point trail;
ETH values scaled by entry/80000 with HALF-UP rounding to 0.05 per bot.
Dynamic stop is ratcheted at each path observation; never loosened; stops
trigger only if price crosses previously installed stop during next segment.
Fills: traded 1m open minus mark 1m open basis plus mark stop trigger, optionally
one adverse execution tick; this is NOT historical bid/ask or actual fills.
No maker claims. Fee .05%/side, GST18%, funding missing (explicit).
Portfolio size min($10*100x, $10/1% risk shock); starting account $100 each.
Trading uptime can be restricted to post 17:23 IST as a separate scenario.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from backtest_demo_1h_pm_20261120_ist import (
    candidate_signals, pm_size, pm_synthetic, round_stop, ENTRY_START, ENTRY_END,
    INITIAL, BUDGET, MAX_DEVIATION, TAKER_FEE, GST, TZ
)

HERE=Path(__file__).resolve().parents[1]
SOURCE=HERE/"analysis"/"demo_1h_pm_nov20_ist_2026"
OUT=HERE/"analysis"/"demo_trailing_1h_nov20_ist_2026"
OUT.mkdir(parents=True,exist_ok=True)

def load(asset,segment):
    frame=pd.read_csv(SOURCE/f"{asset.lower()}_{segment}.csv.gz",
                      compression="gzip",index_col=0,parse_dates=[0])
    frame.index=pd.to_datetime(frame.index,utc=True)
    frame=frame.sort_index()
    assert not frame.index.has_duplicates
    return frame

def iscross(prev, nxt, stop, side):
    if side==1:
        return prev>stop and nxt<=stop
    return prev<stop and nxt>=stop

def trail_point(price,asset,entry, tick, activation,distance,side,best,active,old_stop):
    if (price-entry)*side>=activation:
        active=True
    if active:
        best=max(best,price) if side==1 else min(best,price)
        proposal=round_stop(best-side*distance,tick,side)
        old_stop=max(old_stop,proposal) if side==1 else min(old_stop,proposal)
    return best,active,old_stop

def simulate(asset,h,trade,mark,product,entry_timing,path_order,extra_slip_ticks,uptime):
    assert entry_timing in ("early_open","late_close")
    assert path_order in ("OHLC","OLHC")
    assert extra_slip_ticks in (0,1)
    assert uptime in ("whole_day","after_1723")
    tick=float(product["tick"]);value=float(product["value"])
    assert len(trade)==len(mark)==1440
    assert np.array_equal(trade.time.to_numpy(),mark.time.to_numpy())
    events_next,_=candidate_signals(h,asset)
    events={key-60:val for key,val in events_next.items()}
    offset=0 if entry_timing=="early_open" else 0
    trade=trade.copy();mark=mark.copy()
    wallet=INITIAL;position=None;ledger=[];skips=[];candidates=0
    price_cols=("open","high","low","close") if path_order=="OHLC" else ("open","low","high","close")
    for t,tc in trade.iterrows():
        ts=int(tc.time)
        mk=mark.loc[t]
        ev=events.get(ts)
        if ev and ev["side"] and t>=ENTRY_START:
            candidates+=1
        if position is None and ev and ev["side"]:
            reason=None
            if uptime=="after_1723" and t < pd.Timestamp("2026-11-20 17:23:05",tz=TZ).tz_convert("UTC"):
                reason="bot_not_running_at_hourly_decision"
            early=entry_timing=="early_open"
            entry=float(tc.open if early else tc.close)
            mark_entry=float(mk.open if early else mk.close)
            side=int(ev["side"])
            if reason is None and abs(entry-ev["signal_close"])/ev["signal_close"]>MAX_DEVIATION:
                reason="price_divergence_gt_0.2pct"
            if reason is None and wallet < BUDGET+1:reason="insufficient_wallet"
            qtyc=pm_size(entry,value)
            if reason is None and qtyc<1:reason="too_small_contract_size"
            if reason is None:
                qty=qtyc*value
                atr=round_stop(entry-side*ev["atr_stop_dist"],tick,side)
                _,near=pm_synthetic(entry,qty,side,wallet,tick,asset)
                stop=max(atr,near) if side==1 and near is not None else (
                    min(atr,near) if side==-1 and near is not None else atr)
                if side*(stop-entry)>=0:reason="invalid_stop_vs_entry"
                elif side*(mark_entry-stop)>=0:reason="mark_crosses_initial_stop"
            if reason is None:
                activation=100. if asset=="BTC" else max(tick,math.floor((entry*100/80000)/tick+.5)*tick)
                distance=50. if asset=="BTC" else max(tick,math.floor((entry*50/80000)/tick+.5)*tick)
                position=dict(side=side,entry=entry,qty=qty,contracts=qtyc,
                    entry_time=t,initial=stop,stop=stop,best=entry,
                    active=False,activation=activation,distance=distance,
                    entry_at="open" if early else "close",
                    original_signal_utc=ev["signal_time_utc"],
                    changes=0,stop_edits=[])
            else:
                skips.append(dict(time_ist=str(t.tz_convert(TZ)),side=side,reason=reason))
        elif position is not None and ev and ev["side"]:
            skips.append(dict(time_ist=str(t.tz_convert(TZ)),
                              side=int(ev["side"]),reason="position_already_open"))
        if position is None:continue
        p=position
        side=p["side"]
        if ev and ev["flip_direction"]==side and p["entry_time"]!=t:
            fill=float(tc.open)
            why="opposite_supertrend_flip"
            stop_mark=None
        else:
            fill=None;why=None;stop_mark=None
            points=[float(mk[col]) for col in price_cols]
            if p["entry_time"]==t and p["entry_at"]=="close":
                # Earlier minute wick cannot occur after a late entry.
                points=[float(mk.close)]
            stop=float(p["stop"])
            basis=float(tc.open)-float(mk.open) # only first-minute observed basis
            prev_mark=None
            for k,price in enumerate(points):
                # Stop installed before the interval; don't look ahead to
                # the current minute extreme to set and fill it.
                if k==0 and (side==1 and price<=stop or side==-1 and price>=stop):
                    stop_mark=price;why="native_stop_open_gap"
                    break
                if prev_mark is not None and iscross(prev_mark,price,stop,side):
                    stop_mark=stop;why="native_trailing_or_initial_stop"
                    break
                # Price is an observation, not a future predictor.
                p["best"],p["active"],new_stop=trail_point(
                    price,asset,p["entry"],tick,p["activation"],p["distance"],
                    side,p["best"],p["active"],stop)
                if abs(new_stop-stop)>tick/2:
                    p["changes"]+=1
                    p["stop_edits"].append([str(t),round(new_stop,4)])
                    stop=new_stop
                prev_mark=price
            p["stop"]=stop
            if why is not None:
                slip=(extra_slip_ticks*tick)*(-side)
                # Counterfactual market fill: approx basis from minute OPEN,
                # not guaranteed traded execution or historical tick.
                fill=round((stop_mark+basis+slip)/tick)*tick
        if why is None:continue
        gross=(fill-p["entry"])*side*p["qty"]
        entry_fee=p["entry"]*p["qty"]*TAKER_FEE
        exit_fee=fill*p["qty"]*TAKER_FEE
        gst=(entry_fee+exit_fee)*GST
        net=gross-entry_fee-exit_fee-gst
        wallet+=net
        ledger.append(dict(
            side="long" if side==1 else "short",
            entry_ist=str(p["entry_time"].tz_convert(TZ)),
            exit_ist=str(t.tz_convert(TZ)),
            entry_proxy=round(p["entry"],4),
            exit_proxy=round(fill,4),
            mark_stop_trigger=round(stop_mark,4) if stop_mark is not None else None,
            initial_stop=round(p["initial"],4),
            final_stop=round(p["stop"],4),
            activation=p["activation"],trail_distance=p["distance"],
            trailing_active=p["active"],stop_updates=p["changes"],
            quantity=p["qty"],contracts=p["contracts"],
            gross=round(gross,4),fees_gst=round(entry_fee+exit_fee+gst,4),
            net=round(net,4),balance_after=round(wallet,4),exit_reason=why))
        position=None
    gains=sum(x["net"] for x in ledger if x["net"]>0)
    losses=-sum(x["net"] for x in ledger if x["net"]<0)
    if position is not None:
        open_trade=dict(entry_ist=str(position["entry_time"].tz_convert(TZ)),
            entry_proxy=position["entry"],last_mark_close=float(mark.iloc[-1].close),
            current_stop=position["stop"],note="UNREALIZED, no imputed closing fill")
    else:open_trade=None
    return pd.DataFrame(ledger),dict(
        asset=asset,scenario={"entry_timing":entry_timing,"mark_path":path_order,
                            "adverse_fill_ticks":extra_slip_ticks,
                            "uptime":uptime},
        starting_equity=INITIAL,
        ending_realized_equity=round(wallet,4),
        net_realized=round(wallet-INITIAL,4),
        signals_in_window=candidates,
        completed_trades=len(ledger),
        wins=sum(x["net"]>0 for x in ledger),
        losses=sum(x["net"]<0 for x in ledger),
        profit_factor=round(gains/losses,4) if losses>0 else None,
        total_modeled_fees_gst=round(sum(x["fees_gst"] for x in ledger),4),
        skips=skips,open_trade=open_trade)

def unit_tests():
    assert iscross(105,95,100,1)
    assert not iscross(95,105,100,1)
    assert iscross(95,105,100,-1)
    assert not iscross(105,95,100,-1)
    assert trail_point(59900,"BTC",60000,.1,100,50,-1,60000,False,61000)[:2]==(59900,True)
    assert abs(trail_point(59900,"BTC",60000,.1,100,50,-1,60000,False,61000)[2]-59950)<.001
    # A new favorable extreme tightens the short stop, never loosens:
    _,_,stop=trail_point(59900,"BTC",60000,.1,100,50,-1,59900,True,59950)
    assert stop<=59950.01

def main():
    unit_tests()
    full=json.loads((SOURCE/"summary.json").read_text())
    results={"day_ist":"2026-11-20",
        "strategy":"DEMO 1h EMA20 Supertrend10,3; trailing BTC activation100 distance50; ETH price normalized",
        "execution_warning":"1m OHLC path order and +10s entry timing unobserved; no simulation is exact; mark and traded execution not identical",
        "fee_assumptions":"0.05% taker each side, 18% GST, funding excluded and not presumed zero",
        "model_assumptions":"1m mark OHLC and hypothetical high-low order with instantaneous edit; fill mark trigger + first-minute traded-mark basis + optional adverse tick",
        "real_bot_3second_poll_reproduced":False,
        "delta_exchange_actual_fill_reproduced":False,"scenarios":{}}
    for asset in ("BTC","ETH"):
        h=load(asset,"demo_1h_source")
        trade=load(asset,"demo_traded_1m_source")
        mark=load(asset,"demo_mark_1m_source")
        specs=full["dataset"][asset]["product"]
        assert float(specs["tick"])>0 and float(specs["value"])>0
        for entry_mode in ("early_open","late_close"):
            for price_path in ("OHLC","OLHC"):
                for slip in (0,1):
                    for uptime in ("whole_day","after_1723"):
                        label=f"{asset.lower()}_{entry_mode}_{price_path}_{slip}tick_{uptime}"
                        ledger,summary=simulate(asset,h,trade,mark,specs,
                            entry_mode,price_path,slip,uptime)
                        ledger.to_csv(OUT/f"{label}_trades.csv",index=False)
                        results["scenarios"][label]=summary
                        print("TRAIL_1M_SCENARIO",label,json.dumps({
                          k:summary[k] for k in ("net_realized","completed_trades","wins","losses","total_modeled_fees_gst","skips")
                        }),flush=True)
    (OUT/"summary.json").write_text(json.dumps(results,indent=2)+"\n")
    print("TRAILING_1M_REPLAY_FINISHED",OUT)

if __name__=="__main__":
    main()
