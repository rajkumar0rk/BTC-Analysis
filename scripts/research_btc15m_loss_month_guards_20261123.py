#!/usr/bin/env python3
"""BTCUSD 15m ONLY: genuine EMA20 break/reclaim with 1m execution sensitivity.

All signal and risk indicators are 15m. No 1h signals, data or filters.
Predeclared variants inspect entry quality and independently ATR-scale risk/TP.
22 completed IST months Jan 2025-Oct 2026. Fee/slip same as BTC-Analysis baseline.
"""
from pathlib import Path
import bisect
import json
import numpy as np
import pandas as pd
from research_ema20_second_touch import read_source, MONTHS, FEE, SLIP
from research_st_firsttouch_ema20_tp2r_stflip_1h15m import st_and_ema, ts_iso
from research_btc_15m_touch_reclaim_20261123 import make_signals

OUT = Path("analysis/btc15m_loss_month_guards_20261123")
TF=15
LOSS_CAPS=[2,3,4,5,6,8,10,12,15]
ACTIVATIONS=[2,3,4,5,6,7]
INITIAL=1000.0
PATHS=("O-H-L-C","O-L-H-C")
# tuple = (reclaim wait in 15m bars, entry filter, R definition, scale, TP/R, profit-lock)
# Valid entries always: confirmed ST flip, first post-flip EMA20 interaction closes WRONG side,
# later 15m closes on trend side. The flip candle never enters.
CONFIGS={
 "reclaim_NOFLIP_SL300_NONE_TP3R":(4,"any","PCT",3.0,3.0,"none"),
 "reclaim_NOFLIP_MCAP2_SL300_TP3R":(4,"any","PCT",3.0,3.0,"none"),
 "reclaim_NOFLIP_MCAP3_SL300_TP3R":(4,"any","PCT",3.0,3.0,"none"),
 "reclaim_NOFLIP_MCAP4_SL300_TP3R":(4,"any","PCT",3.0,3.0,"none"),
 "reclaim_NOFLIP_MCAP5_SL300_TP3R":(4,"any","PCT",3.0,3.0,"none"),
 "reclaim_NOFLIP_MCAP6_SL300_TP3R":(4,"any","PCT",3.0,3.0,"none"),
 "reclaim_NOFLIP_MCAP8_SL300_TP3R":(4,"any","PCT",3.0,3.0,"none"),
 "reclaim_NOFLIP_MCAP10_SL300_TP3R":(4,"any","PCT",3.0,3.0,"none"),
 "reclaim_NOFLIP_MCAP12_SL300_TP3R":(4,"any","PCT",3.0,3.0,"none"),
 "reclaim_NOFLIP_MCAP15_SL300_TP3R":(4,"any","PCT",3.0,3.0,"none"),
 "reclaim_NOFLIP_LATE_A200_L000_I050_SL300_TP3R":(4,"any","PCT",3.0,3.0,"LATE:2:0:2:0.5"),
 "reclaim_NOFLIP_LATE_A200_L000_I100_SL300_TP3R":(4,"any","PCT",3.0,3.0,"LATE:2:0:2:1"),
 "reclaim_NOFLIP_LATE_A200_L050_I050_SL300_TP3R":(4,"any","PCT",3.0,3.0,"LATE:2:0.5:2:0.5"),
 "reclaim_NOFLIP_LATE_A200_L050_I100_SL300_TP3R":(4,"any","PCT",3.0,3.0,"LATE:2:0.5:2:1"),
 "reclaim_NOFLIP_LATE_A200_L100_I050_SL300_TP3R":(4,"any","PCT",3.0,3.0,"LATE:2:1:2:0.5"),
 "reclaim_NOFLIP_LATE_A200_L100_I100_SL300_TP3R":(4,"any","PCT",3.0,3.0,"LATE:2:1:2:1"),
 "reclaim_NOFLIP_LATE_A300_L000_I050_SL300_TP3R":(4,"any","PCT",3.0,3.0,"LATE:3:0:2:0.5"),
 "reclaim_NOFLIP_LATE_A300_L000_I100_SL300_TP3R":(4,"any","PCT",3.0,3.0,"LATE:3:0:2:1"),
 "reclaim_NOFLIP_LATE_A300_L050_I050_SL300_TP3R":(4,"any","PCT",3.0,3.0,"LATE:3:0.5:2:0.5"),
 "reclaim_NOFLIP_LATE_A300_L050_I100_SL300_TP3R":(4,"any","PCT",3.0,3.0,"LATE:3:0.5:2:1"),
 "reclaim_NOFLIP_LATE_A300_L100_I050_SL300_TP3R":(4,"any","PCT",3.0,3.0,"LATE:3:1:2:0.5"),
 "reclaim_NOFLIP_LATE_A300_L100_I100_SL300_TP3R":(4,"any","PCT",3.0,3.0,"LATE:3:1:2:1"),
 "reclaim_NOFLIP_LATE_A400_L000_I050_SL300_TP3R":(4,"any","PCT",3.0,3.0,"LATE:4:0:2:0.5"),
 "reclaim_NOFLIP_LATE_A400_L000_I100_SL300_TP3R":(4,"any","PCT",3.0,3.0,"LATE:4:0:2:1"),
 "reclaim_NOFLIP_LATE_A400_L050_I050_SL300_TP3R":(4,"any","PCT",3.0,3.0,"LATE:4:0.5:2:0.5"),
 "reclaim_NOFLIP_LATE_A400_L050_I100_SL300_TP3R":(4,"any","PCT",3.0,3.0,"LATE:4:0.5:2:1"),
 "reclaim_NOFLIP_LATE_A400_L100_I050_SL300_TP3R":(4,"any","PCT",3.0,3.0,"LATE:4:1:2:0.5"),
 "reclaim_NOFLIP_LATE_A400_L100_I100_SL300_TP3R":(4,"any","PCT",3.0,3.0,"LATE:4:1:2:1"),
 "reclaim_NOFLIP_LATE_A500_L000_I050_SL300_TP3R":(4,"any","PCT",3.0,3.0,"LATE:5:0:2:0.5"),
 "reclaim_NOFLIP_LATE_A500_L000_I100_SL300_TP3R":(4,"any","PCT",3.0,3.0,"LATE:5:0:2:1"),
 "reclaim_NOFLIP_LATE_A500_L050_I050_SL300_TP3R":(4,"any","PCT",3.0,3.0,"LATE:5:0.5:2:0.5"),
 "reclaim_NOFLIP_LATE_A500_L050_I100_SL300_TP3R":(4,"any","PCT",3.0,3.0,"LATE:5:0.5:2:1"),
 "reclaim_NOFLIP_LATE_A500_L100_I050_SL300_TP3R":(4,"any","PCT",3.0,3.0,"LATE:5:1:2:0.5"),
 "reclaim_NOFLIP_LATE_A500_L100_I100_SL300_TP3R":(4,"any","PCT",3.0,3.0,"LATE:5:1:2:1"),
 "reclaim_NOFLIP_LATE_A600_L000_I050_SL300_TP3R":(4,"any","PCT",3.0,3.0,"LATE:6:0:2:0.5"),
 "reclaim_NOFLIP_LATE_A600_L000_I100_SL300_TP3R":(4,"any","PCT",3.0,3.0,"LATE:6:0:2:1"),
 "reclaim_NOFLIP_LATE_A600_L050_I050_SL300_TP3R":(4,"any","PCT",3.0,3.0,"LATE:6:0.5:2:0.5"),
 "reclaim_NOFLIP_LATE_A600_L050_I100_SL300_TP3R":(4,"any","PCT",3.0,3.0,"LATE:6:0.5:2:1"),
 "reclaim_NOFLIP_LATE_A600_L100_I050_SL300_TP3R":(4,"any","PCT",3.0,3.0,"LATE:6:1:2:0.5"),
 "reclaim_NOFLIP_LATE_A600_L100_I100_SL300_TP3R":(4,"any","PCT",3.0,3.0,"LATE:6:1:2:1"),
 "reclaim_NOFLIP_LATE_A700_L000_I050_SL300_TP3R":(4,"any","PCT",3.0,3.0,"LATE:7:0:2:0.5"),
 "reclaim_NOFLIP_LATE_A700_L000_I100_SL300_TP3R":(4,"any","PCT",3.0,3.0,"LATE:7:0:2:1"),
 "reclaim_NOFLIP_LATE_A700_L050_I050_SL300_TP3R":(4,"any","PCT",3.0,3.0,"LATE:7:0.5:2:0.5"),
 "reclaim_NOFLIP_LATE_A700_L050_I100_SL300_TP3R":(4,"any","PCT",3.0,3.0,"LATE:7:0.5:2:1"),
 "reclaim_NOFLIP_LATE_A700_L100_I050_SL300_TP3R":(4,"any","PCT",3.0,3.0,"LATE:7:1:2:0.5"),
 "reclaim_NOFLIP_LATE_A700_L100_I100_SL300_TP3R":(4,"any","PCT",3.0,3.0,"LATE:7:1:2:1"),
 "reclaim_NOFLIP_MCAP4_LATE_A300_L000_I100_SL300_TP3R":(4,"any","PCT",3.0,3.0,"LATE:3:0:2:1"),
 "reclaim_NOFLIP_MCAP4_LATE_A300_L100_I100_SL300_TP3R":(4,"any","PCT",3.0,3.0,"LATE:3:1:2:1"),
 "reclaim_NOFLIP_MCAP4_LATE_A400_L000_I100_SL300_TP3R":(4,"any","PCT",3.0,3.0,"LATE:4:0:2:1"),
 "reclaim_NOFLIP_MCAP4_LATE_A400_L100_I100_SL300_TP3R":(4,"any","PCT",3.0,3.0,"LATE:4:1:2:1"),
 "reclaim_NOFLIP_MCAP4_LATE_A500_L000_I100_SL300_TP3R":(4,"any","PCT",3.0,3.0,"LATE:5:0:2:1"),
 "reclaim_NOFLIP_MCAP4_LATE_A500_L100_I100_SL300_TP3R":(4,"any","PCT",3.0,3.0,"LATE:5:1:2:1"),
 "reclaim_NOFLIP_MCAP6_LATE_A300_L000_I100_SL300_TP3R":(4,"any","PCT",3.0,3.0,"LATE:3:0:2:1"),
 "reclaim_NOFLIP_MCAP6_LATE_A300_L100_I100_SL300_TP3R":(4,"any","PCT",3.0,3.0,"LATE:3:1:2:1"),
 "reclaim_NOFLIP_MCAP6_LATE_A400_L000_I100_SL300_TP3R":(4,"any","PCT",3.0,3.0,"LATE:4:0:2:1"),
 "reclaim_NOFLIP_MCAP6_LATE_A400_L100_I100_SL300_TP3R":(4,"any","PCT",3.0,3.0,"LATE:4:1:2:1"),
 "reclaim_NOFLIP_MCAP6_LATE_A500_L000_I100_SL300_TP3R":(4,"any","PCT",3.0,3.0,"LATE:5:0:2:1"),
 "reclaim_NOFLIP_MCAP6_LATE_A500_L100_I100_SL300_TP3R":(4,"any","PCT",3.0,3.0,"LATE:5:1:2:1"),
 "reclaim_NOFLIP_MCAP8_LATE_A300_L000_I100_SL300_TP3R":(4,"any","PCT",3.0,3.0,"LATE:3:0:2:1"),
 "reclaim_NOFLIP_MCAP8_LATE_A300_L100_I100_SL300_TP3R":(4,"any","PCT",3.0,3.0,"LATE:3:1:2:1"),
 "reclaim_NOFLIP_MCAP8_LATE_A400_L000_I100_SL300_TP3R":(4,"any","PCT",3.0,3.0,"LATE:4:0:2:1"),
 "reclaim_NOFLIP_MCAP8_LATE_A400_L100_I100_SL300_TP3R":(4,"any","PCT",3.0,3.0,"LATE:4:1:2:1"),
 "reclaim_NOFLIP_MCAP8_LATE_A500_L000_I100_SL300_TP3R":(4,"any","PCT",3.0,3.0,"LATE:5:0:2:1"),
 "reclaim_NOFLIP_MCAP8_LATE_A500_L100_I100_SL300_TP3R":(4,"any","PCT",3.0,3.0,"LATE:5:1:2:1"),
 "reclaim_NOFLIP_MCAP10_LATE_A300_L000_I100_SL300_TP3R":(4,"any","PCT",3.0,3.0,"LATE:3:0:2:1"),
 "reclaim_NOFLIP_MCAP10_LATE_A300_L100_I100_SL300_TP3R":(4,"any","PCT",3.0,3.0,"LATE:3:1:2:1"),
 "reclaim_NOFLIP_MCAP10_LATE_A400_L000_I100_SL300_TP3R":(4,"any","PCT",3.0,3.0,"LATE:4:0:2:1"),
 "reclaim_NOFLIP_MCAP10_LATE_A400_L100_I100_SL300_TP3R":(4,"any","PCT",3.0,3.0,"LATE:4:1:2:1"),
 "reclaim_NOFLIP_MCAP10_LATE_A500_L000_I100_SL300_TP3R":(4,"any","PCT",3.0,3.0,"LATE:5:0:2:1"),
 "reclaim_NOFLIP_MCAP10_LATE_A500_L100_I100_SL300_TP3R":(4,"any","PCT",3.0,3.0,"LATE:5:1:2:1"),
}

SL_PERCENT_VALUES=[0.1,0.15,0.2,0.3,0.4,0.5,0.75,1,1.25,1.5,2,3]
STOP_CHOICES_BY_MODE={"touch":[0.2,0.5,0.75,1.25],"reclaim":[0.1,0.15,0.2,0.3,0.4,0.5,0.75,1,1.25,1.5,2,3],"combined":[0.2,0.5,0.75,1.25]}
MILESTONE_SEQUENCES={"015_018_025_040_060_1_2":[0.15,0.18,0.25,0.4,0.6,1,2],"015_020_030_050_1_2_3":[0.15,0.2,0.3,0.5,1,2,3]}
METHODS=["FIRST015_STEP005","FIRST015_STEP010"]

def rung_lock_pct(favorable_pct,levels,method):
    """First milestone locks precisely +0.15% raw BTC price move.

    Following milestones use:
    FIRST015_PREV:       previous favorable price rung
    FIRST015_STEP005:    first +0.15%, +0.05 percentage points per later rung
    FIRST015_STEP010:    first +0.15%, +0.10 percentage points per later rung
    FIRST015_TIGHT005:  first +0.15%, later rung minus 0.05 points
    FIRST015_TIGHT010:  first +0.15%, later rung minus 0.10 points
    Extend the last inter-rung interval after last explicit milestone.
    Stops are based on raw entry price and account for slip/fees at fills.
    """
    if favorable_pct+1e-10<levels[0]:
        return None
    assert len(levels)>=2 and all(0<x<y for x,y in zip(levels,levels[1:]))
    interval=levels[-1]-levels[-2]
    if favorable_pct+1e-10>=levels[-1]:
        n_extra=max(0,int((favorable_pct-levels[-1]+1e-10)/interval))
        n=len(levels)+n_extra
        reached=levels[-1]+n_extra*interval
        prev=levels[-2] if n_extra==0 else levels[-1]+(n_extra-1)*interval
    else:
        n=int(np.searchsorted(levels,favorable_pct+1e-10,side="right"))
        reached=levels[n-1]
        prev=levels[n-2] if n>=2 else None
    if n==1:
        locked=0.15
    elif method=="FIRST015_PREV":
        locked=prev
    elif method=="FIRST015_STEP005":
        locked=0.15+0.05*(n-1)
    elif method=="FIRST015_STEP010":
        locked=0.15 if n==1 else 0.20+0.10*(n-2)
    elif method=="FIRST015_TIGHT005":
        locked=reached-0.05
    elif method=="FIRST015_TIGHT010":
        locked=reached-0.10
    else:
        raise AssertionError(("Unknown protection method",method))
    # Do not allow the lock to exceed reached favorable movement.
    # Stop only moves in favorable direction, so small steps are fine.
    # Stop must never be above currently observed favorable raw price.
    locked=min(locked,reached)
    assert locked<=reached+1e-9,(locked,reached,method)
    return locked

def make_indicators(df):
    n=len(df)//TF
    assert n*TF==len(df), "Incomplete 15m data"
    H=df.high.to_numpy(float).reshape(n,TF).max(axis=1)
    L=df.low.to_numpy(float).reshape(n,TF).min(axis=1)
    O=df.open.to_numpy(float).reshape(n,TF)[:,0]
    C=df.close.to_numpy(float).reshape(n,TF)[:,-1]
    V=df.volume.to_numpy(float).reshape(n,TF).sum(axis=1)
    prev=np.r_[C[0],C[:-1]]
    TR=np.maximum(H-L,np.maximum(abs(H-prev),abs(L-prev)))
    ATR=np.full(n,np.nan)
    ATR[9]=np.mean(TR[:10])
    for j in range(10,n):
        ATR[j]=(ATR[j-1]*9+TR[j])/10
    return dict(O=O,H=H,L=L,C=C,V=V,ATR=ATR)

def check_filter(filter_name,side,j,ema,ind):
    c=float(ind["C"][j]);o=float(ind["O"][j])
    h=float(ind["H"][j]);l=float(ind["L"][j])
    a=float(ind["ATR"][j])
    if filter_name=="any":return True
    if filter_name=="slope4":return j>=4 and side*(ema[j]-ema[j-4])>0
    if filter_name=="slope8":return j>=8 and side*(ema[j]-ema[j-8])>0
    if filter_name=="body35":return side*(c-o)>=.35*(h-l)
    if filter_name=="body55":return side*(c-o)>=.55*(h-l)
    if filter_name=="margin10":return side*(c-ema[j])>=.10*a
    if filter_name=="margin20":return side*(c-ema[j])>=.20*a
    if filter_name=="volume120":return j>=20 and ind["V"][j] >= 1.2*float(np.mean(ind["V"][j-20:j]))
    if filter_name=="volume150":return j>=20 and ind["V"][j] >= 1.5*float(np.mean(ind["V"][j-20:j]))
    raise ValueError("Unknown filter "+filter_name)

def delayed_protection_pct(favorable_pct, late):
    if late is None:
        return None
    activation, first_lock, step_distance, increment=late
    if favorable_pct + 1e-10 < activation:
        return None
    advances=max(0,int((favorable_pct-activation+1e-10)/step_distance))
    return min(favorable_pct,first_lock+advances*increment)

def simulate(df,ema,stline,trend,ind,name,cfg,signals,path_name):
    wait,fil,risk_mode,riskmult,tpR,lock=cfg
    lock_levels=None;lock_method=None;late=None
    if lock.startswith("LATE:"):
        late=tuple(map(float,lock.split(":")[1:]))
        assert len(late)==4
        assert 0<=late[1]<=late[0] and late[2]>0 and late[3]>0
    else:
        assert lock=="none"
    month_cap=float(name.split("_MCAP")[1].split("_")[0]) if "_MCAP" in name else None
    tp_off=tpR==0
    # All newly tested percent-SL strategies explicitly IGNORE Supertrend reversals
    # after entry. Historic ST baselines and a fixed-SL FLIPON control retain old exit.
    flip_exit_enabled=("_BASE_ST3R" in name) or ("_FLIPON_" in name)
    tm=df.time.to_numpy(np.int64)
    op=df.open.to_numpy(float);h=df.high.to_numpy(float)
    l=df.low.to_numpy(float);c=df.close.to_numpy(float)
    monthends={}
    for month in MONTHS:
        end=(pd.Period(month,freq="M")+1).start_time.tz_localize("Asia/Kolkata").tz_convert("UTC")-pd.Timedelta(minutes=1)
        sec=int(end.timestamp())
        i=int(np.searchsorted(tm,sec,side="right")-1)
        assert i>=0 and tm[i]==sec,(month,sec)
        monthends[i]=month
    signal_indices=set(signals)
    event_indices=sorted(signal_indices|set(monthends))
    cash=INITIAL;position=None;trade_rows=[];month_rows=[]
    eq_high=INITIAL;max_dd=0.;eq_low=INITIAL;filtered=0;badR=0
    signal_used=0
    skipped_entries_due_to_open_position=0
    seen_epochs=set()
    month_end_indices=sorted(monthends)
    current_month_index=0
    month_reference=INITIAL
    previous_month_end_equity=INITIAL
    monthly_halted=False
    monthly_halt_events=0
    def quote_equity(raw):
        eq=cash
        if position is not None:
            proxy=raw*(1-position["side"]*SLIP)
            eq+=position["side"]*position["qty"]*(proxy-position["entry"])-FEE*position["qty"]*proxy
        return eq
    def monthly_guard_price(p):
        if month_cap is None or monthly_halted:
            return None
        threshold=month_reference*(1-month_cap/100.0)
        # Exact price where liquidation net equity crosses monthly loss cap.
        # The equity function is affine in raw BTC price at fixed position size.
        side=p["side"];qty=p["qty"]
        slope=qty*(side-FEE)*(1-side*SLIP)
        value=(threshold-cash+side*qty*p["entry"])/slope
        return value if np.isfinite(value) and value>0 else None
    def lock_at(raw_favorable):
        return delayed_protection_pct(raw_favorable,late)
    def mark(raw):
        nonlocal eq_high,eq_low,max_dd
        eq=cash
        if position is not None:
            proxy=raw*(1-position["side"]*SLIP)
            eq+=position["side"]*position["qty"]*(proxy-position["entry"])-FEE*position["qty"]*proxy
        eq_high=max(eq_high,eq)
        eq_low=min(eq_low,eq)
        if eq_high>0:
            max_dd=max(max_dd,100*(eq_high-eq)/eq_high)
        return eq
    def close_trade(raw,sec,reason):
        nonlocal position,cash,monthly_halted,monthly_halt_events
        if reason in ("MONTHLY_GUARD","MONTHLY_GAP"):
            monthly_halted=True
            monthly_halt_events+=1
        p=position
        assert p is not None
        fill=raw*(1-p["side"]*SLIP)
        gross=p["side"]*p["qty"]*(fill-p["entry"])
        fee_out=FEE*p["qty"]*fill
        net=gross-fee_out-p["fee_in"]
        cash+=gross-fee_out
        trade_rows.append(dict(config=name,path_assumption=path_name,
           activation_count=p["activation_count"],
           lock_increase_count=p["lock_increase_count"],
           max_locked_market_move_pct=round(p["highest_locked_pct"],4),
           protected_exit=bool(p["active"] and reason in ("PROTECTION_STOP","PROTECTION_GAP")),
           originally_baseline_stop=bool(reason in ("STOP","STOP_GAP")),
           entry_time_utc=ts_iso(p["entry_sec"]),exit_time_utc=ts_iso(sec),
           exit_month_ist=pd.Timestamp(sec,unit="s",tz="UTC").tz_convert("Asia/Kolkata").strftime("%Y-%m"),
           direction="LONG" if p["side"]==1 else "SHORT",entry=p["entry"],exit=fill,
           R=p["R"],initial_stop=p["initial_stop"],target=p["target"],
           exit_reason=reason,net_usd=net,fee_gst_usd=p["fee_in"]+fee_out,
           equity_after_usd=cash,epoch=p["epoch"]))
        position=None
    i=0
    while i<len(df):
        if position is None and i not in signal_indices and i not in monthends:
            next_event=bisect.bisect_left(event_indices,i)
            if next_event==len(event_indices):
                break
            i=event_indices[next_event]
        done=i//TF-1
        if done<100:
            i+=1
            continue
        sec=int(tm[i]);raw_open=float(op[i])
        new_month_idx=bisect.bisect_left(month_end_indices,i)
        if new_month_idx!=current_month_index:
            assert new_month_idx==current_month_index+1,(i,current_month_index,new_month_idx)
            current_month_index=new_month_idx
            month_reference=previous_month_end_equity
            monthly_halted=False
        # Cap is based only on contemporaneously observable marked-to-market equity.
        if month_cap is not None and not monthly_halted:
            threshold=month_reference*(1-month_cap/100)
            if quote_equity(raw_open)<=threshold:
                if position is not None:
                    close_trade(raw_open,sec,"MONTHLY_GAP")
                else:
                    monthly_halted=True
                    monthly_halt_events+=1
        if position is not None:
            # For NOFLIP: no exit on ST reversal or opposing signal.
            # Existing ST regime still controls when future entry signals form.
            if flip_exit_enabled and i%TF==0 and trend[done]!=position["side"]:
                close_trade(raw_open,sec,"SUPERTREND_FLIP")
            elif position["side"]*(raw_open-position["target"])>=0:
                close_trade(position["target"],sec,"TP")
            elif position["side"]*(raw_open-position["stop"])<=0:
                close_trade(raw_open,sec,"PROTECTION_GAP" if position["active"] else "STOP_GAP")
        if i in signal_indices and position is not None:
            skipped_entries_due_to_open_position+=1
        if i in signal_indices and position is None and cash>0 and not monthly_halted:
            sig=signals[i]
            side=int(sig["side"]); j=int(sig["signal_close_bar"])
            if not check_filter(fil,side,j,ema,ind):
                filtered+=1
            else:
                assert side==int(trend[done]), ("Unexpected trend after reclaim",name,i)
                entry=raw_open*(1+side*SLIP)
                R_ST=side*(entry-float(stline[done]))
                R_ATR=float(ind["ATR"][j])
                if risk_mode=="ST":R=R_ST*riskmult
                elif risk_mode=="ATR":R=R_ATR*riskmult
                elif risk_mode=="CAP":R=min(R_ST,R_ATR*riskmult)
                elif risk_mode=="PCT":R=entry*riskmult/100.0
                else:raise ValueError(risk_mode)
                # Important: no-TP is not 9999R. For shorts, this makes a
                # negative target, invalidating short entries. Use infinity
                # with the correct sign so BOTH directions remain eligible.
                target=(float("inf") if side>0 else float("-inf")) if tp_off else entry+side*tpR*R
                stop=entry-side*R
                valid_target=tp_off or (np.isfinite(target) and target>0)
                if not (np.isfinite(R) and R>0 and stop>0 and valid_target and R_ST>0):
                    badR+=1
                else:
                    assert sig["epoch"] not in seen_epochs, "Cycle duplicate"
                    seen_epochs.add(sig["epoch"])
                    qty=cash/entry
                    fee_in=FEE*qty*entry
                    cash-=fee_in
                    position=dict(side=side,entry=entry,raw_entry=raw_open,R=R,qty=qty,fee_in=fee_in,
                                  stop=stop,initial_stop=stop,target=target,entry_sec=sec,epoch=sig["epoch"],
                                  active=False,activation_count=0,lock_increase_count=0,highest_locked_pct=-1.0)
                    signal_used+=1
        # An overnight/minute opening price may already cross a rung.
        # Arm the protection at this observed open (after checking old gap
        # stop and flip), avoiding use of later highs/lows.
        if position is not None and late is not None:
            p=position
            favorable_pct=100*p["side"]*(raw_open-p["raw_entry"])/p["raw_entry"]
            locked_pct=lock_at(favorable_pct)
            if locked_pct is not None:
                candidate=p["raw_entry"]*(1+p["side"]*locked_pct/100)
                if p["side"]*(candidate-p["stop"])>1e-8:
                    if not p["active"]:p["activation_count"]+=1
                    else:p["lock_increase_count"]+=1
                    p["active"]=True;p["stop"]=candidate
                    p["highest_locked_pct"]=max(p["highest_locked_pct"],locked_pct)
        path=(raw_open,h[i],l[i],c[i]) if path_name=="O-H-L-C" else (raw_open,l[i],h[i],c[i])
        mark(path[0])
        for k in range(3):
            dest=float(path[k+1])
            if position is None:
                mark(dest)
                continue
            p=position;side=p["side"]
            # The first barrier along an adverse price segment is the *closer*
            # of the ordinary SL/protective stop and this month's equity guard.
            guard=monthly_guard_price(p)
            effective_stop=p["stop"]
            monthly_barrier=False
            if guard is not None and side*(guard-effective_stop)>0:
                effective_stop=guard
                monthly_barrier=True
            if side*(dest-p["target"])>=0:
                mark(p["target"])
                close_trade(p["target"],sec,"TP")
            elif side*(dest-effective_stop)<=0:
                mark(effective_stop)
                close_trade(effective_stop,sec,"MONTHLY_GUARD" if monthly_barrier else ("PROTECTION_STOP" if p["active"] else "STOP"))
            else:
                # Update stop only AFTER the favorable segment reaches the trigger.
                # A later adverse segment can then hit it in the same 1-minute bar.
                # A target or existing stop encountered first exits without lookahead.
                if late is not None and side*(dest-float(path[k]))>0:
                    favorable_pct=100*side*(dest-p["raw_entry"])/p["raw_entry"]
                    locked_pct=lock_at(favorable_pct)
                    if locked_pct is not None:
                        # Price stop is derived from original market entry,
                        # but fills include adverse slip and fee+GST.
                        new_stop=p["raw_entry"]*(1+side*locked_pct/100)
                        if side*(new_stop-p["stop"])>1e-8:
                            if not p["active"]:
                                p["activation_count"]+=1
                            else:
                                p["lock_increase_count"]+=1
                            p["active"]=True
                            p["stop"]=new_stop
                            p["highest_locked_pct"]=max(p["highest_locked_pct"],locked_pct)
                mark(dest)
        if i in monthends:
            previous_month_end_equity=mark(float(c[i]))
            month_rows.append(dict(month_ist=monthends[i],equity_usd=previous_month_end_equity,
                        position_open=position is not None,
                        monthly_halt_triggered=monthly_halted,
                        month_cap_pct=month_cap))
        i+=1
    if position is not None:
        close_trade(float(c[-1]),int(tm[-1]),"SAMPLE_END_ACCOUNTING_ONLY")
        month_rows[-1]["equity_usd"]=cash
    assert len(month_rows)==22,("wrong month count",len(month_rows),name)
    ledger=pd.DataFrame(trade_rows)
    assert not ledger.empty,(name,path_name)
    assert not ledger.epoch.duplicated().any()
    assert abs(ledger.net_usd.sum()-(cash-INITIAL))<0.02,"Ledger/cash mismatch"
    month_df=pd.DataFrame(month_rows)
    month_df["monthly_return_pct"]=100*(month_df.equity_usd/month_df.equity_usd.shift(1,fill_value=INITIAL)-1)
    y25=float(month_df.loc[month_df.month_ist=="2025-12","equity_usd"].iloc[0])
    positive=ledger.net_usd>0
    gain=float(ledger.loc[positive,"net_usd"].sum())
    loss=-float(ledger.loc[~positive,"net_usd"].sum())
    summary=dict(symbol="BTCUSD",timeframe="15m",config=name,path_assumption=path_name,
        trades=len(ledger),wins=int(positive.sum()),losses=int((~positive).sum()),
        win_rate_pct=round(100*float(positive.mean()),3),
        profit_factor=round(gain/loss,4) if loss>0 else None,
        net_return_pct=round(100*(cash/INITIAL-1),4),
        net_profit_usd=round(cash-INITIAL,4),
        profitable_months=int((month_df.monthly_return_pct>0).sum()),
        profitable_2025_months=int((month_df.iloc[:12].monthly_return_pct>0).sum()),
        profitable_2026_months=int((month_df.iloc[12:].monthly_return_pct>0).sum()),
        return_2025_pct=round(100*(y25/INITIAL-1),3),
        return_2026_pct=round(100*(cash/y25-1),3),
        max_floating_drawdown_pct=round(max_dd,3),
        fees_gst_usd=round(float(ledger.fee_gst_usd.sum()),4),
        tp_exits=int((ledger.exit_reason=="TP").sum()),
        stop_exits=int(ledger.exit_reason.isin(["STOP","STOP_GAP"]).sum()),
        flip_exits=int((ledger.exit_reason=="SUPERTREND_FLIP").sum()),
        signal_candidates=len(signals),signals_filtered=filtered,invalid_risk=badR,
        month_cap_pct=month_cap,monthly_guard_hits=monthly_halt_events,
        supertrend_flip_exit_enabled=flip_exit_enabled,
        potential_entries_skipped_while_open=skipped_entries_due_to_open_position,
        activated_trades=int((ledger.activation_count>0).sum()),
        protection_increase_events=int(ledger.lock_increase_count.sum()),
        protected_exit_trades=int(ledger.protected_exit.sum()),
        protected_exits_winning=int((ledger.protected_exit & (ledger.net_usd>0)).sum()),
        protected_exits_losing=int((ledger.protected_exit & (ledger.net_usd<=0)).sum()))
    month_df.insert(0,"config",name)
    month_df.insert(0,"symbol","BTCUSD")
    month_df.insert(0,"path_assumption",path_name)
    return summary,month_df,ledger

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    df,quality=read_source("BTCUSD")
    ema,stline,trend,valid=st_and_ema(df,TF)
    ind=make_indicators(df)
    signals=make_signals(df,ema,trend,valid,"reclaim",4)[0]
    summaries=[];months=[];trades=[]
    for name,cfg in CONFIGS.items():
        for path in PATHS:
            print("RUN",name,path,flush=True)
            row,mon,ledger=simulate(df,ema,stline,trend,ind,name,cfg,signals,path)
            assert row["flip_exits"]==0,(name,path)
            assert row["supertrend_flip_exit_enabled"]==False,(name,path)
            summaries.append(row);months.append(mon);trades.append(ledger)
            print("RESULT",json.dumps(row,sort_keys=True),flush=True)
    summary=pd.DataFrame(summaries)
    months=pd.concat(months,ignore_index=True)
    trades=pd.concat(trades,ignore_index=True)
    original=pd.read_csv("analysis/btc15m_reclaim_sl3_tp9_monthly_20261123/monthly_ohlc.csv")
    baseline=months[(months.config=="reclaim_NOFLIP_SL300_NONE_TP3R")&(months.path_assumption=="O-H-L-C")].sort_values("month_ist")
    expected=original.sort_values("month_ist")
    assert len(baseline)==22
    assert np.allclose(baseline.equity_usd,expected.equity_usd,atol=.001)
    assert np.allclose(baseline.monthly_return_pct,expected.monthly_return_pct,atol=.00001)
    b=summary[(summary.config=="reclaim_NOFLIP_SL300_NONE_TP3R")&(summary.path_assumption=="O-H-L-C")].iloc[0]
    assert b.trades==75 and abs(b.net_return_pct-97.5183)<.001
    assert b.profitable_months==16 and b.flip_exits==0
    print("ORIGINAL_MONTHLY_22_PARITY_OK",flush=True)
    orig=baseline.set_index("month_ist").monthly_return_pct
    profitable=orig>1e-9
    lossmonths=orig<0
    ranked=[]
    for _,r in summary.iterrows():
        sub=months[(months.config==r.config)&(months.path_assumption==r.path_assumption)]
        series=sub.set_index("month_ist").monthly_return_pct.reindex(orig.index)
        assert len(series)==22 and series.notna().all()
        positive_deltas=series[profitable]-orig[profitable]
        losing_deltas=series[lossmonths]-orig[lossmonths]
        # Strict: every one of the existing 16 winning months remains at least
        # as profitable as the baseline. Month-end mark-to-market, no lookahead
        # is used by trade simulation or risk guard.
        keep_all=bool((positive_deltas>=-0.00001).all())
        data=r.to_dict()
        data.update(keep_all_16_profit_months=keep_all,
            preserved_positive_month_count=int((positive_deltas>=-0.00001).sum()),
            profitable_month_return_shortfall_pp=round(float((-positive_deltas.clip(upper=0)).sum()),5),
            improved_6_original_loss_months=int((losing_deltas>0.00001).sum()),
            sum_negative_month_returns_pct=round(float(series.clip(upper=0).sum()),4),
            worst_month_pct=round(float(series.min()),4),
            worst_month_name=str(series.idxmin()),
            month_2025_03_pct=round(float(series.loc["2025-03"]),4),
            month_2025_12_pct=round(float(series.loc["2025-12"]),4),
            month_2026_04_pct=round(float(series.loc["2026-04"]),4),
            month_2026_07_pct=round(float(series.loc["2026-07"]),4))
        ranked.append(data)
    detail=pd.DataFrame(ranked)
    detail.to_csv(OUT/"scored_summary.csv",index=False)
    summary.to_csv(OUT/"summary.csv",index=False)
    months.to_csv(OUT/"monthly_mark_to_market.csv",index=False)
    trades.to_csv(OUT/"trades.csv.gz",index=False,compression="gzip")
    chosen=detail[detail.path_assumption=="O-H-L-C"].sort_values(
         ["keep_all_16_profit_months","net_return_pct"],ascending=[False,False])
    cols=["config","trades","net_return_pct","profitable_months","preserved_positive_month_count","improved_6_original_loss_months",
      "profitable_month_return_shortfall_pp","sum_negative_month_returns_pct","worst_month_pct",
      "max_floating_drawdown_pct","monthly_guard_hits"]
    baseline_loss=float(orig.clip(upper=0).sum())
    strict=chosen[(chosen.keep_all_16_profit_months)&(chosen.config!="reclaim_NOFLIP_SL300_NONE_TP3R")&
                 (chosen.sum_negative_month_returns_pct>baseline_loss+0.00001)]
    report=[
      "# BTCUSD 15M Reclaim — Reduce losing months without affecting positive months",
      "",
      "Fixed unchanged strategy entry and 3% initial SL / 9% TP, no ST flip exit.",
      "No volume or 1h filters. Jan2025-Oct2026 IST, 22 months, 1x equity notional.",
      "Taker fees 0.05% per side+18% GST, 0.02% adverse slippage each side.",
      "Strict pass: each of the 16 historically positive monthly percent returns MUST remain at least as high as baseline. A new worse month also counts against improved losing-month consistency.",
      "Loss-month interventions are determined only by prices and account equity OBSERVED SO FAR, not hindsight.",
      "Tests monthly drawdown circuit breaker at 2-15% of equity from previous month's close, delayed activation locks at +2 to +7% raw price move, or combination.",
      "Original 3%/9% model reverified against archived exact 22 monthly results.",
      "Stop-limit guards assume ideal trigger fills at 1m OHLC interpolation, but market gaps filled at bar open; real execution could be worse.",
      "Historical sample has already been repeatedly optimized; any selected threshold is IN-SAMPLE and unproven prospectively.",
      "All pricing models exclude real funding, latency, liquidation and exchange order-book depth.",
      "",
      "## Strict criterion results",
      "Strictly improving non-baseline configs: "+str(len(strict)),
      "",
      "## Every O-H-L-C strategy ranked by preserving all 16 profit months and total return",
      "",chosen[cols].to_markdown(index=False),"",
      "## Exact baseline losing months",
      "",orig[lossmonths].to_string(),"",
      "## Strict improvements (if any)",
      "",strict[cols].to_markdown(index=False) if len(strict) else "None passed.",
      ""
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    (OUT/"quality.json").write_text(json.dumps(dict(BTCUSD=quality,configurations=CONFIGS,
        strict_16_profit_months_preserved_requirement=True,
        historical_monthly_source="analysis/btc15m_reclaim_sl3_tp9_monthly_20261123/monthly_ohlc.csv",
        original_net_return_pct=97.5183,original_win_months=16,
        original_sum_loss_months_pct=baseline_loss,
        trading_cost_model=dict(taker_each_side=.05,gst_on_fee=.18,slippage_each_side=.02),
        monthly_circuit_breakers_pct=LOSS_CAPS,
        delayed_lock_activation_pct=ACTIVATIONS,
        future_data_used=False,signal_timeframe="15m",execution_timeframe="1m",
        supertrend_reverse_exit=False,initial_SL_pct=3,TP_pct=9,
        exclusions=["funding","orderbook","real fills","liquidation"],
        known_optimization_limitation="these 22 months previously explored extensively"),default=str,indent=2)+"\n")
    print("STRICT_MONTHLY_RESULTS_DONE",len(detail),int(len(strict)),flush=True)

if __name__=="__main__":
    main()
