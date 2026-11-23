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

OUT = Path("analysis/btc15m_immediate_015_lock_20261123")
TF=15
INITIAL=1000.0
PATHS=("O-H-L-C","O-L-H-C")
# tuple = (reclaim wait in 15m bars, entry filter, R definition, scale, TP/R, profit-lock)
# Valid entries always: confirmed ST flip, first post-flip EMA20 interaction closes WRONG side,
# later 15m closes on trend side. The flip candle never enters.
CONFIGS={
 "touch_BASE_ST3R":(4,"any","ST",1.0,3.0,"none"),
 "touch_015_020_030_050_FIRST015_PREV_TP3R":(4,"any","ST",1.0,3.0,"LADDER:0.15,0.2,0.3,0.5:FIRST015_PREV"),
 "touch_015_020_030_050_FIRST015_PREV_TP_OFF":(4,"any","ST",1.0,0.0,"LADDER:0.15,0.2,0.3,0.5:FIRST015_PREV"),
 "touch_015_020_030_050_FIRST015_STEP005_TP3R":(4,"any","ST",1.0,3.0,"LADDER:0.15,0.2,0.3,0.5:FIRST015_STEP005"),
 "touch_015_020_030_050_FIRST015_STEP005_TP_OFF":(4,"any","ST",1.0,0.0,"LADDER:0.15,0.2,0.3,0.5:FIRST015_STEP005"),
 "touch_015_020_030_050_FIRST015_STEP010_TP3R":(4,"any","ST",1.0,3.0,"LADDER:0.15,0.2,0.3,0.5:FIRST015_STEP010"),
 "touch_015_020_030_050_FIRST015_STEP010_TP_OFF":(4,"any","ST",1.0,0.0,"LADDER:0.15,0.2,0.3,0.5:FIRST015_STEP010"),
 "touch_015_020_030_050_FIRST015_TIGHT005_TP3R":(4,"any","ST",1.0,3.0,"LADDER:0.15,0.2,0.3,0.5:FIRST015_TIGHT005"),
 "touch_015_020_030_050_FIRST015_TIGHT005_TP_OFF":(4,"any","ST",1.0,0.0,"LADDER:0.15,0.2,0.3,0.5:FIRST015_TIGHT005"),
 "touch_015_018_030_050_1_2_3_FIRST015_PREV_TP3R":(4,"any","ST",1.0,3.0,"LADDER:0.15,0.18,0.3,0.5,1,2,3:FIRST015_PREV"),
 "touch_015_018_030_050_1_2_3_FIRST015_PREV_TP_OFF":(4,"any","ST",1.0,0.0,"LADDER:0.15,0.18,0.3,0.5,1,2,3:FIRST015_PREV"),
 "touch_015_018_030_050_1_2_3_FIRST015_STEP005_TP3R":(4,"any","ST",1.0,3.0,"LADDER:0.15,0.18,0.3,0.5,1,2,3:FIRST015_STEP005"),
 "touch_015_018_030_050_1_2_3_FIRST015_STEP005_TP_OFF":(4,"any","ST",1.0,0.0,"LADDER:0.15,0.18,0.3,0.5,1,2,3:FIRST015_STEP005"),
 "touch_015_018_030_050_1_2_3_FIRST015_STEP010_TP3R":(4,"any","ST",1.0,3.0,"LADDER:0.15,0.18,0.3,0.5,1,2,3:FIRST015_STEP010"),
 "touch_015_018_030_050_1_2_3_FIRST015_STEP010_TP_OFF":(4,"any","ST",1.0,0.0,"LADDER:0.15,0.18,0.3,0.5,1,2,3:FIRST015_STEP010"),
 "touch_015_018_030_050_1_2_3_FIRST015_TIGHT005_TP3R":(4,"any","ST",1.0,3.0,"LADDER:0.15,0.18,0.3,0.5,1,2,3:FIRST015_TIGHT005"),
 "touch_015_018_030_050_1_2_3_FIRST015_TIGHT005_TP_OFF":(4,"any","ST",1.0,0.0,"LADDER:0.15,0.18,0.3,0.5,1,2,3:FIRST015_TIGHT005"),
 "touch_015_020_050_1_3_FIRST015_PREV_TP3R":(4,"any","ST",1.0,3.0,"LADDER:0.15,0.2,0.5,1,3:FIRST015_PREV"),
 "touch_015_020_050_1_3_FIRST015_PREV_TP_OFF":(4,"any","ST",1.0,0.0,"LADDER:0.15,0.2,0.5,1,3:FIRST015_PREV"),
 "touch_015_020_050_1_3_FIRST015_STEP005_TP3R":(4,"any","ST",1.0,3.0,"LADDER:0.15,0.2,0.5,1,3:FIRST015_STEP005"),
 "touch_015_020_050_1_3_FIRST015_STEP005_TP_OFF":(4,"any","ST",1.0,0.0,"LADDER:0.15,0.2,0.5,1,3:FIRST015_STEP005"),
 "touch_015_020_050_1_3_FIRST015_STEP010_TP3R":(4,"any","ST",1.0,3.0,"LADDER:0.15,0.2,0.5,1,3:FIRST015_STEP010"),
 "touch_015_020_050_1_3_FIRST015_STEP010_TP_OFF":(4,"any","ST",1.0,0.0,"LADDER:0.15,0.2,0.5,1,3:FIRST015_STEP010"),
 "touch_015_020_050_1_3_FIRST015_TIGHT005_TP3R":(4,"any","ST",1.0,3.0,"LADDER:0.15,0.2,0.5,1,3:FIRST015_TIGHT005"),
 "touch_015_020_050_1_3_FIRST015_TIGHT005_TP_OFF":(4,"any","ST",1.0,0.0,"LADDER:0.15,0.2,0.5,1,3:FIRST015_TIGHT005"),
 "touch_015_018_025_040_060_1_2_FIRST015_PREV_TP3R":(4,"any","ST",1.0,3.0,"LADDER:0.15,0.18,0.25,0.4,0.6,1,2:FIRST015_PREV"),
 "touch_015_018_025_040_060_1_2_FIRST015_PREV_TP_OFF":(4,"any","ST",1.0,0.0,"LADDER:0.15,0.18,0.25,0.4,0.6,1,2:FIRST015_PREV"),
 "touch_015_018_025_040_060_1_2_FIRST015_STEP005_TP3R":(4,"any","ST",1.0,3.0,"LADDER:0.15,0.18,0.25,0.4,0.6,1,2:FIRST015_STEP005"),
 "touch_015_018_025_040_060_1_2_FIRST015_STEP005_TP_OFF":(4,"any","ST",1.0,0.0,"LADDER:0.15,0.18,0.25,0.4,0.6,1,2:FIRST015_STEP005"),
 "touch_015_018_025_040_060_1_2_FIRST015_STEP010_TP3R":(4,"any","ST",1.0,3.0,"LADDER:0.15,0.18,0.25,0.4,0.6,1,2:FIRST015_STEP010"),
 "touch_015_018_025_040_060_1_2_FIRST015_STEP010_TP_OFF":(4,"any","ST",1.0,0.0,"LADDER:0.15,0.18,0.25,0.4,0.6,1,2:FIRST015_STEP010"),
 "touch_015_018_025_040_060_1_2_FIRST015_TIGHT005_TP3R":(4,"any","ST",1.0,3.0,"LADDER:0.15,0.18,0.25,0.4,0.6,1,2:FIRST015_TIGHT005"),
 "touch_015_018_025_040_060_1_2_FIRST015_TIGHT005_TP_OFF":(4,"any","ST",1.0,0.0,"LADDER:0.15,0.18,0.25,0.4,0.6,1,2:FIRST015_TIGHT005"),
 "reclaim_BASE_ST3R":(4,"any","ST",1.0,3.0,"none"),
 "reclaim_015_020_030_050_FIRST015_PREV_TP3R":(4,"any","ST",1.0,3.0,"LADDER:0.15,0.2,0.3,0.5:FIRST015_PREV"),
 "reclaim_015_020_030_050_FIRST015_PREV_TP_OFF":(4,"any","ST",1.0,0.0,"LADDER:0.15,0.2,0.3,0.5:FIRST015_PREV"),
 "reclaim_015_020_030_050_FIRST015_STEP005_TP3R":(4,"any","ST",1.0,3.0,"LADDER:0.15,0.2,0.3,0.5:FIRST015_STEP005"),
 "reclaim_015_020_030_050_FIRST015_STEP005_TP_OFF":(4,"any","ST",1.0,0.0,"LADDER:0.15,0.2,0.3,0.5:FIRST015_STEP005"),
 "reclaim_015_020_030_050_FIRST015_STEP010_TP3R":(4,"any","ST",1.0,3.0,"LADDER:0.15,0.2,0.3,0.5:FIRST015_STEP010"),
 "reclaim_015_020_030_050_FIRST015_STEP010_TP_OFF":(4,"any","ST",1.0,0.0,"LADDER:0.15,0.2,0.3,0.5:FIRST015_STEP010"),
 "reclaim_015_020_030_050_FIRST015_TIGHT005_TP3R":(4,"any","ST",1.0,3.0,"LADDER:0.15,0.2,0.3,0.5:FIRST015_TIGHT005"),
 "reclaim_015_020_030_050_FIRST015_TIGHT005_TP_OFF":(4,"any","ST",1.0,0.0,"LADDER:0.15,0.2,0.3,0.5:FIRST015_TIGHT005"),
 "reclaim_015_018_030_050_1_2_3_FIRST015_PREV_TP3R":(4,"any","ST",1.0,3.0,"LADDER:0.15,0.18,0.3,0.5,1,2,3:FIRST015_PREV"),
 "reclaim_015_018_030_050_1_2_3_FIRST015_PREV_TP_OFF":(4,"any","ST",1.0,0.0,"LADDER:0.15,0.18,0.3,0.5,1,2,3:FIRST015_PREV"),
 "reclaim_015_018_030_050_1_2_3_FIRST015_STEP005_TP3R":(4,"any","ST",1.0,3.0,"LADDER:0.15,0.18,0.3,0.5,1,2,3:FIRST015_STEP005"),
 "reclaim_015_018_030_050_1_2_3_FIRST015_STEP005_TP_OFF":(4,"any","ST",1.0,0.0,"LADDER:0.15,0.18,0.3,0.5,1,2,3:FIRST015_STEP005"),
 "reclaim_015_018_030_050_1_2_3_FIRST015_STEP010_TP3R":(4,"any","ST",1.0,3.0,"LADDER:0.15,0.18,0.3,0.5,1,2,3:FIRST015_STEP010"),
 "reclaim_015_018_030_050_1_2_3_FIRST015_STEP010_TP_OFF":(4,"any","ST",1.0,0.0,"LADDER:0.15,0.18,0.3,0.5,1,2,3:FIRST015_STEP010"),
 "reclaim_015_018_030_050_1_2_3_FIRST015_TIGHT005_TP3R":(4,"any","ST",1.0,3.0,"LADDER:0.15,0.18,0.3,0.5,1,2,3:FIRST015_TIGHT005"),
 "reclaim_015_018_030_050_1_2_3_FIRST015_TIGHT005_TP_OFF":(4,"any","ST",1.0,0.0,"LADDER:0.15,0.18,0.3,0.5,1,2,3:FIRST015_TIGHT005"),
 "reclaim_015_020_050_1_3_FIRST015_PREV_TP3R":(4,"any","ST",1.0,3.0,"LADDER:0.15,0.2,0.5,1,3:FIRST015_PREV"),
 "reclaim_015_020_050_1_3_FIRST015_PREV_TP_OFF":(4,"any","ST",1.0,0.0,"LADDER:0.15,0.2,0.5,1,3:FIRST015_PREV"),
 "reclaim_015_020_050_1_3_FIRST015_STEP005_TP3R":(4,"any","ST",1.0,3.0,"LADDER:0.15,0.2,0.5,1,3:FIRST015_STEP005"),
 "reclaim_015_020_050_1_3_FIRST015_STEP005_TP_OFF":(4,"any","ST",1.0,0.0,"LADDER:0.15,0.2,0.5,1,3:FIRST015_STEP005"),
 "reclaim_015_020_050_1_3_FIRST015_STEP010_TP3R":(4,"any","ST",1.0,3.0,"LADDER:0.15,0.2,0.5,1,3:FIRST015_STEP010"),
 "reclaim_015_020_050_1_3_FIRST015_STEP010_TP_OFF":(4,"any","ST",1.0,0.0,"LADDER:0.15,0.2,0.5,1,3:FIRST015_STEP010"),
 "reclaim_015_020_050_1_3_FIRST015_TIGHT005_TP3R":(4,"any","ST",1.0,3.0,"LADDER:0.15,0.2,0.5,1,3:FIRST015_TIGHT005"),
 "reclaim_015_020_050_1_3_FIRST015_TIGHT005_TP_OFF":(4,"any","ST",1.0,0.0,"LADDER:0.15,0.2,0.5,1,3:FIRST015_TIGHT005"),
 "reclaim_015_018_025_040_060_1_2_FIRST015_PREV_TP3R":(4,"any","ST",1.0,3.0,"LADDER:0.15,0.18,0.25,0.4,0.6,1,2:FIRST015_PREV"),
 "reclaim_015_018_025_040_060_1_2_FIRST015_PREV_TP_OFF":(4,"any","ST",1.0,0.0,"LADDER:0.15,0.18,0.25,0.4,0.6,1,2:FIRST015_PREV"),
 "reclaim_015_018_025_040_060_1_2_FIRST015_STEP005_TP3R":(4,"any","ST",1.0,3.0,"LADDER:0.15,0.18,0.25,0.4,0.6,1,2:FIRST015_STEP005"),
 "reclaim_015_018_025_040_060_1_2_FIRST015_STEP005_TP_OFF":(4,"any","ST",1.0,0.0,"LADDER:0.15,0.18,0.25,0.4,0.6,1,2:FIRST015_STEP005"),
 "reclaim_015_018_025_040_060_1_2_FIRST015_STEP010_TP3R":(4,"any","ST",1.0,3.0,"LADDER:0.15,0.18,0.25,0.4,0.6,1,2:FIRST015_STEP010"),
 "reclaim_015_018_025_040_060_1_2_FIRST015_STEP010_TP_OFF":(4,"any","ST",1.0,0.0,"LADDER:0.15,0.18,0.25,0.4,0.6,1,2:FIRST015_STEP010"),
 "reclaim_015_018_025_040_060_1_2_FIRST015_TIGHT005_TP3R":(4,"any","ST",1.0,3.0,"LADDER:0.15,0.18,0.25,0.4,0.6,1,2:FIRST015_TIGHT005"),
 "reclaim_015_018_025_040_060_1_2_FIRST015_TIGHT005_TP_OFF":(4,"any","ST",1.0,0.0,"LADDER:0.15,0.18,0.25,0.4,0.6,1,2:FIRST015_TIGHT005"),
 "combined_BASE_ST3R":(4,"any","ST",1.0,3.0,"none"),
 "combined_015_020_030_050_FIRST015_PREV_TP3R":(4,"any","ST",1.0,3.0,"LADDER:0.15,0.2,0.3,0.5:FIRST015_PREV"),
 "combined_015_020_030_050_FIRST015_PREV_TP_OFF":(4,"any","ST",1.0,0.0,"LADDER:0.15,0.2,0.3,0.5:FIRST015_PREV"),
 "combined_015_020_030_050_FIRST015_STEP005_TP3R":(4,"any","ST",1.0,3.0,"LADDER:0.15,0.2,0.3,0.5:FIRST015_STEP005"),
 "combined_015_020_030_050_FIRST015_STEP005_TP_OFF":(4,"any","ST",1.0,0.0,"LADDER:0.15,0.2,0.3,0.5:FIRST015_STEP005"),
 "combined_015_020_030_050_FIRST015_STEP010_TP3R":(4,"any","ST",1.0,3.0,"LADDER:0.15,0.2,0.3,0.5:FIRST015_STEP010"),
 "combined_015_020_030_050_FIRST015_STEP010_TP_OFF":(4,"any","ST",1.0,0.0,"LADDER:0.15,0.2,0.3,0.5:FIRST015_STEP010"),
 "combined_015_020_030_050_FIRST015_TIGHT005_TP3R":(4,"any","ST",1.0,3.0,"LADDER:0.15,0.2,0.3,0.5:FIRST015_TIGHT005"),
 "combined_015_020_030_050_FIRST015_TIGHT005_TP_OFF":(4,"any","ST",1.0,0.0,"LADDER:0.15,0.2,0.3,0.5:FIRST015_TIGHT005"),
 "combined_015_018_030_050_1_2_3_FIRST015_PREV_TP3R":(4,"any","ST",1.0,3.0,"LADDER:0.15,0.18,0.3,0.5,1,2,3:FIRST015_PREV"),
 "combined_015_018_030_050_1_2_3_FIRST015_PREV_TP_OFF":(4,"any","ST",1.0,0.0,"LADDER:0.15,0.18,0.3,0.5,1,2,3:FIRST015_PREV"),
 "combined_015_018_030_050_1_2_3_FIRST015_STEP005_TP3R":(4,"any","ST",1.0,3.0,"LADDER:0.15,0.18,0.3,0.5,1,2,3:FIRST015_STEP005"),
 "combined_015_018_030_050_1_2_3_FIRST015_STEP005_TP_OFF":(4,"any","ST",1.0,0.0,"LADDER:0.15,0.18,0.3,0.5,1,2,3:FIRST015_STEP005"),
 "combined_015_018_030_050_1_2_3_FIRST015_STEP010_TP3R":(4,"any","ST",1.0,3.0,"LADDER:0.15,0.18,0.3,0.5,1,2,3:FIRST015_STEP010"),
 "combined_015_018_030_050_1_2_3_FIRST015_STEP010_TP_OFF":(4,"any","ST",1.0,0.0,"LADDER:0.15,0.18,0.3,0.5,1,2,3:FIRST015_STEP010"),
 "combined_015_018_030_050_1_2_3_FIRST015_TIGHT005_TP3R":(4,"any","ST",1.0,3.0,"LADDER:0.15,0.18,0.3,0.5,1,2,3:FIRST015_TIGHT005"),
 "combined_015_018_030_050_1_2_3_FIRST015_TIGHT005_TP_OFF":(4,"any","ST",1.0,0.0,"LADDER:0.15,0.18,0.3,0.5,1,2,3:FIRST015_TIGHT005"),
 "combined_015_020_050_1_3_FIRST015_PREV_TP3R":(4,"any","ST",1.0,3.0,"LADDER:0.15,0.2,0.5,1,3:FIRST015_PREV"),
 "combined_015_020_050_1_3_FIRST015_PREV_TP_OFF":(4,"any","ST",1.0,0.0,"LADDER:0.15,0.2,0.5,1,3:FIRST015_PREV"),
 "combined_015_020_050_1_3_FIRST015_STEP005_TP3R":(4,"any","ST",1.0,3.0,"LADDER:0.15,0.2,0.5,1,3:FIRST015_STEP005"),
 "combined_015_020_050_1_3_FIRST015_STEP005_TP_OFF":(4,"any","ST",1.0,0.0,"LADDER:0.15,0.2,0.5,1,3:FIRST015_STEP005"),
 "combined_015_020_050_1_3_FIRST015_STEP010_TP3R":(4,"any","ST",1.0,3.0,"LADDER:0.15,0.2,0.5,1,3:FIRST015_STEP010"),
 "combined_015_020_050_1_3_FIRST015_STEP010_TP_OFF":(4,"any","ST",1.0,0.0,"LADDER:0.15,0.2,0.5,1,3:FIRST015_STEP010"),
 "combined_015_020_050_1_3_FIRST015_TIGHT005_TP3R":(4,"any","ST",1.0,3.0,"LADDER:0.15,0.2,0.5,1,3:FIRST015_TIGHT005"),
 "combined_015_020_050_1_3_FIRST015_TIGHT005_TP_OFF":(4,"any","ST",1.0,0.0,"LADDER:0.15,0.2,0.5,1,3:FIRST015_TIGHT005"),
 "combined_015_018_025_040_060_1_2_FIRST015_PREV_TP3R":(4,"any","ST",1.0,3.0,"LADDER:0.15,0.18,0.25,0.4,0.6,1,2:FIRST015_PREV"),
 "combined_015_018_025_040_060_1_2_FIRST015_PREV_TP_OFF":(4,"any","ST",1.0,0.0,"LADDER:0.15,0.18,0.25,0.4,0.6,1,2:FIRST015_PREV"),
 "combined_015_018_025_040_060_1_2_FIRST015_STEP005_TP3R":(4,"any","ST",1.0,3.0,"LADDER:0.15,0.18,0.25,0.4,0.6,1,2:FIRST015_STEP005"),
 "combined_015_018_025_040_060_1_2_FIRST015_STEP005_TP_OFF":(4,"any","ST",1.0,0.0,"LADDER:0.15,0.18,0.25,0.4,0.6,1,2:FIRST015_STEP005"),
 "combined_015_018_025_040_060_1_2_FIRST015_STEP010_TP3R":(4,"any","ST",1.0,3.0,"LADDER:0.15,0.18,0.25,0.4,0.6,1,2:FIRST015_STEP010"),
 "combined_015_018_025_040_060_1_2_FIRST015_STEP010_TP_OFF":(4,"any","ST",1.0,0.0,"LADDER:0.15,0.18,0.25,0.4,0.6,1,2:FIRST015_STEP010"),
 "combined_015_018_025_040_060_1_2_FIRST015_TIGHT005_TP3R":(4,"any","ST",1.0,3.0,"LADDER:0.15,0.18,0.25,0.4,0.6,1,2:FIRST015_TIGHT005"),
 "combined_015_018_025_040_060_1_2_FIRST015_TIGHT005_TP_OFF":(4,"any","ST",1.0,0.0,"LADDER:0.15,0.18,0.25,0.4,0.6,1,2:FIRST015_TIGHT005"),
}

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
        locked=0.15+0.10*(n-1)
    elif method=="FIRST015_TIGHT005":
        locked=reached-0.05
    elif method=="FIRST015_TIGHT010":
        locked=reached-0.10
    else:
        raise AssertionError(("Unknown protection method",method))
    # Do not allow the lock to exceed reached favorable movement.
    # Stop only moves in favorable direction, so small steps are fine.
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

def simulate(df,ema,stline,trend,ind,name,cfg,signals,path_name):
    wait,fil,risk_mode,riskmult,tpR,lock=cfg
    if lock.startswith("LADDER:"):
        _,seq_str,method=lock.split(":")
        lock_levels=tuple(map(float,seq_str.split(",")))
        assert 2<=len(lock_levels)<=12 and all(0<a<b for a,b in zip(lock_levels,lock_levels[1:]))
        lock_method=method
    else:
        assert lock=="none"
        lock_levels=None
        lock_method=None
    tp_off=tpR==0
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
    seen_epochs=set()
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
        nonlocal position,cash
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
        if position is not None:
            # Only confirmed 15m ST reversal (never a line touch).
            if i%TF==0 and trend[done]!=position["side"]:
                close_trade(raw_open,sec,"SUPERTREND_FLIP")
            elif position["side"]*(raw_open-position["target"])>=0:
                close_trade(position["target"],sec,"TP")
            elif position["side"]*(raw_open-position["stop"])<=0:
                close_trade(raw_open,sec,"PROTECTION_GAP" if position["active"] else "STOP_GAP")
        if i in signal_indices and position is None and cash>0:
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
        if position is not None and lock_levels is not None:
            p=position
            favorable_pct=100*p["side"]*(raw_open-p["raw_entry"])/p["raw_entry"]
            locked_pct=rung_lock_pct(favorable_pct,lock_levels,lock_method)
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
            if side*(dest-p["target"])>=0:
                mark(p["target"])
                close_trade(p["target"],sec,"TP")
            elif side*(dest-p["stop"])<=0:
                mark(p["stop"])
                close_trade(p["stop"],sec,"PROTECTION_STOP" if p["active"] else "STOP")
            else:
                # Update stop only AFTER the favorable segment reaches the trigger.
                # A later adverse segment can then hit it in the same 1-minute bar.
                # A target or existing stop encountered first exits without lookahead.
                if lock_levels is not None and side*(dest-float(path[k]))>0:
                    favorable_pct=100*side*(dest-p["raw_entry"])/p["raw_entry"]
                    locked_pct=rung_lock_pct(favorable_pct,lock_levels,lock_method)
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
            month_rows.append(dict(month_ist=monthends[i],equity_usd=mark(float(c[i])),
                        position_open=position is not None))
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
    signal_cache={}
    results=[];monthly=[];trades=[]
    for name,cfg in CONFIGS.items():
        mode=name.split("_")[0]
        wait=cfg[0]
        key=(mode,wait)
        if key not in signal_cache:
            signal_cache[key]=make_signals(df,ema,trend,valid,mode,wait)[0]
        for path in PATHS:
            print("RUN",name,path,flush=True)
            row,mon,ledger=simulate(df,ema,stline,trend,ind,name,cfg,signal_cache[key],path)
            results.append(row);monthly.append(mon);trades.append(ledger)
            print("RESULT",json.dumps(row,sort_keys=True),flush=True)
    result_df=pd.DataFrame(results)
    # Must reproduce the complete established original 15m-only configuration.
    reference=[("touch_BASE_ST3R",809,-69.4444),
               ("reclaim_BASE_ST3R",434,-44.5322),
               ("combined_BASE_ST3R",1243,-83.0515)]
    for name,trades_expected,net_expected in reference:
        for path in PATHS:
            row=result_df[(result_df.config==name)&(result_df.path_assumption==path)].iloc[0]
            assert int(row.trades)==trades_expected and abs(row.net_return_pct-net_expected)<0.001,("BASELINE_PARITY_FAILED",name,path,row.to_dict())
    print("BASELINE_PARITY_OK",flush=True)
    assert (result_df.trades>=1).all()
    assert (result_df.activated_trades<=result_df.trades).all()
    assert (result_df.protected_exits_winning+result_df.protected_exits_losing==result_df.protected_exit_trades).all()
    # A protected stop can still lose after fees if its raw locked level is too close.
    print("PROTECTION_METRIC_VALIDATION_OK",flush=True)
    result_df.to_csv(OUT/"summary.csv",index=False)
    pd.concat(monthly,ignore_index=True).to_csv(OUT/"monthly_mark_to_market.csv",index=False)
    pd.concat(trades,ignore_index=True).to_csv(OUT/"trades.csv.gz",index=False,compression="gzip")
    (OUT/"quality.json").write_text(json.dumps(dict(BTCUSD=quality,configurations=CONFIGS,
        signal_timeframe="15m",higher_timeframe_features=False,execution_timeframe="1m",
        supertrend="Wilder ATR10 factor3",ema20=True,
        one_trade_per_cycle=True,flip_candle_excluded=True,
        initial_stop="1R entry-to-previous-closed-Supertrend-line",
        TP="3R fixed or truly disabled with sign-correct infinite target; both LONG and SHORT retained",
        stop_on_confirmed_15m_ST_flip=True,
        milestone_sequences_pct={"015_020_030_050":[0.15,0.2,0.3,0.5],"015_018_030_050_1_2_3":[0.15,0.18,0.3,0.5,1,2,3],"015_020_050_1_3":[0.15,0.2,0.5,1,3],"015_018_025_040_060_1_2":[0.15,0.18,0.25,0.4,0.6,1,2]},
        protection_methods=["FIRST015_PREV","FIRST015_STEP005","FIRST015_STEP010","FIRST015_TIGHT005"],
        profit_lock_activation_pct="first milestone reached by favorable market move from raw entry open",
        profit_lock_pct="all first lock exactly +0.15% from raw entry; later locks previous milestone or +0.05/+0.10 step or new rung minus .05/.10%",
        after_final_rung="continue increasing at interval between final two milestones",
        target_execution="no lookahead; update only after favorable 1m OHLC subsegment, then check subsequent path; gap stop checked first",
        separate_paths_compared=True,
        stop_never_loosen=True,
        minute_path_model="O-H-L-C and O-L-H-C hypothetical monotone segments; activation never before favorable segment; stop can be touched later in same minute",
        fee_incl_GST_per_side=FEE,slippage_per_side=SLIP,
        notional="1x evolving $1000 equity", no_volume_filter=True,
        limitations="22 months already used for research; historical in-sample optimized, no external OOS, no funding, tick data, spread, depth, margin/liquidation or latency"),indent=2,default=str)+"\n")
    display=result_df[result_df.path_assumption=="O-H-L-C"].sort_values(
      "net_return_pct",ascending=False)
    shortlist=display[["config","trades","wins","win_rate_pct","profit_factor",
      "net_return_pct","profitable_months","profitable_2025_months",
      "profitable_2026_months","return_2025_pct","return_2026_pct",
      "max_floating_drawdown_pct","activated_trades",
      "protected_exit_trades","protected_exits_winning","protected_exits_losing"]]
    report=[
        "# BTCUSD 15M — IMMEDIATE +0.15% activation and +0.15% lock staircase protection",
        "",
        "Signal: **BTCUSD 15m ST(ATR10 x3) + EMA20** with first post-flip touch-close, first break/reclaim, or combined entry; one trade maximum per ST cycle.",
        "No 1h filter, no volume filter. LONG and SHORT mirrored. 1m intrabar replay only for exits.",
        "Jan 2025–Oct 2026 IST, 22 completed months. $1000 initial equity, 1x evolving capital notional.",
        "Fees 0.05% each-side taker, GST18%, adverse slippage 0.02% per side.",
        "Initial stop 1R from previous completed 15m ST line. TP 3R or genuinely OFF, retaining both LONG and SHORT. Exit on confirmed opposite 15m ST flip.",
        "CORRECTED first trigger at exactly +0.15%, NOT +0.18%: [0.15,0.20,0.30,0.50], [0.15,0.18,0.30,0.50,1,2,3], [0.15,0.20,0.50,1,3], [0.15,0.18,0.25,0.40,0.60,1,2]. All percentages of BTC raw market entry.",
        "EVERY test immediately arms a +0.15% raw market stop at the exact +0.15% favorable trigger. Subsequent rungs either lock previous rung, increase +0.05/+0.10 percentage points, or lock reached rung minus 0.05 points; stop never loosens.",
        "Lock never loosens; fills include taker/GST and adverse slippage. A gross 0.118% lock can still be net losing.",
        "Lock percentages are **gross BTC price moves**, not guaranteed net returns. Price gaps may bypass stops; net return accounts for taker/GST/slippage.",
        "Two 1m OHLC paths show the uncertainty of 1m candle internal tick sequence; reported results are hypothetical.",
        "The tested months have been repeatedly used for research and **are not fresh out-of-sample validation**.",
        "TP OFF is correctly unbounded for LONG and SHORT. First lock at +0.15% is below roughly +0.158% modeled round-trip break-even, so a protected exit may still be slightly net-negative.",
        "","## All configurations sorted by full 22-month net return",
        "",shortlist.to_markdown(index=False),"",
        "Additional monthly mark-to-market, trade-level ledgers, and alternate intraminute path in CSV artifacts.",
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    # Essential parity and fairness: no-TP configurations must not drop shorts
    # just because an unreachable target was used.
    for mode,expected in (("touch",809),("reclaim",434),("combined",1243)):
        for pth in PATHS:
            rows=result_df[(result_df.config.str.startswith(mode+"_"))&
                           (result_df.config.str.endswith("_TP_OFF"))&
                           (result_df.path_assumption==pth)]
            assert len(rows)==16,(mode,pth,len(rows))
            assert rows.trades.min()>0,(mode,pth)
            # On the same first-touch confirmed ST cycle, all should be
            # available if they have not already held a position across cycles.
            assert rows.trades.max()<=expected,(mode,pth)
    print("NO_TP_BOTH_DIRECTIONS_OK",flush=True)
    for mode in ("touch","reclaim","combined"):
        config_names=[name for name in CONFIGS if name.startswith(mode+"_") and name!="%s_BASE_ST3R"%mode]
        assert len(config_names)==32,(mode,len(config_names))
    # Verify the first activation is exactly 0.15% and no +0.18% wait remains.
    for mode in ("touch","reclaim","combined"):
        for name,cfg in CONFIGS.items():
            if not name.startswith(mode+"_") or "BASE" in name:continue
            levels=tuple(map(float,cfg[5].split(":")[1].split(",")))
            assert levels[0]==0.15,(name,levels)
            assert rung_lock_pct(.15,levels,cfg[5].split(":")[2])==.15
            assert rung_lock_pct(.149999,levels,cfg[5].split(":")[2]) is None
    print("IMMEDIATE_015_ACTIVATION_OK",flush=True)
    print("BACKTEST_DONE",len(result_df),flush=True)

if __name__=="__main__":
    main()
