#!/usr/bin/env python3
"""Exact 1H-signal adaptation of the prior 15M EMA20/Supertrend first-touch runs.

Same pre-existing indicator implementation and filters, now computed on completed
H1 candles. Actual archived Delta India 1M OHLC decides which fixed level hits
first. One exclusive position, no early ST flip, trailing, ATR stop, hold cap,
leverage, funding, spread, or fee deductions (classification, NOT P&L).

ETH targets are entry-relative BTC equivalents: BTC points / 80,000.
When TP and SL both touch in the same 1M candle and the open resolves neither,
report ambiguous; for sequencing treat that minute as an exit, conservatively
SL-first if implementing a portfolio backtest. No optimistic path assumption.

Signal window 2025-01-01 through 2026-10-31 UTC, 22 complete months; later
archived 1M candles available into mid-Nov 2026 for resolving late entries.
"""
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from replay_ema_st_15m_entries_1m_exits_20261121 import load
from replay_btc_ema_st_screenshot import indicators

OUT=ROOT/"analysis"/"one_hour_first_hit_four_pairs_20261121"
OUT.mkdir(parents=True,exist_ok=True)
START=int(pd.Timestamp("2025-01-01",tz="UTC").timestamp())
ENTRY_END=int(pd.Timestamp("2026-11-01",tz="UTC").timestamp())
PAIRS=((200,100),(300,100),(600,200),(900,300))

def hourly_from_minutes(m):
    h=m.resample("1h",origin="epoch",label="left",closed="left").agg({
        "open":"first","high":"max","low":"min","close":"last",
        "volume":"sum","time":"count"})
    assert (h["time"]==60).all(), "Partial 1H candle!"
    assert len(h)*60==len(m)
    return indicators(h.drop(columns="time"))

def signal_index(h,n_minutes,filtered):
    entry=np.zeros(n_minutes,dtype=np.int8)
    direct=h.dir.to_numpy()
    ema=h.ema.to_numpy()
    atr=h.atr14.to_numpy()
    ar=h.atr_ratio.to_numpy()
    vr=h.volume_ratio.to_numpy()
    low=h.low.to_numpy()
    high=h.high.to_numpy()
    close=h.close.to_numpy()
    for i in range(36,len(h)-1):
        if not (np.isfinite(ema[i]) and np.isfinite(atr[i])):
            continue
        if filtered and (not np.isfinite(ar[i]) or not np.isfinite(vr[i])
                         or ar[i]<1.0 or vr[i]<1.5):
            continue
        j=(i+1)*60
        if direct[i]==direct[i-1]==-1 and low[i]<=ema[i] and close[i]>ema[i]:
            entry[j]=1
        elif direct[i]==direct[i-1]==1 and high[i]>=ema[i] and close[i]<ema[i]:
            entry[j]=-1
    return entry

def replay(asset,m,signals,tp_points,sl_points):
    op=m.open.to_numpy(dtype=np.float64)
    hi=m.high.to_numpy(dtype=np.float64)
    lo=m.low.to_numpy(dtype=np.float64)
    t=m.time.to_numpy(dtype=np.int64)
    assert len(t)==len(signals) and t[0]==START
    assert (np.diff(t)==60).all()
    p=None
    rows=[]
    nsignals=0
    skipped=0
    for j in range(len(t)):
        sd=int(signals[j])
        if sd and t[j]<ENTRY_END:
            nsignals+=1
            if p is not None:
                skipped+=1
            else:
                ep=float(op[j])
                factor=1.0 if asset=="BTC" else ep/80000.0
                tp_distance=float(tp_points)*factor
                sl_distance=float(sl_points)*factor
                p=(j,ep,sd,ep+sd*tp_distance,ep-sd*sl_distance)
        if p is None:
            continue
        entry_index,ep,side,tp,sl=p
        if side>0:
            gap_tp=op[j]>=tp
            gap_sl=op[j]<=sl
            touch_tp=hi[j]>=tp
            touch_sl=lo[j]<=sl
        else:
            gap_tp=op[j]<=tp
            gap_sl=op[j]>=sl
            touch_tp=lo[j]<=tp
            touch_sl=hi[j]>=sl
        result=None
        if gap_tp:
            result="TP_first"
        elif gap_sl:
            result="SL_first"
        elif touch_tp and touch_sl:
            result="ambiguous_same_1m"
        elif touch_tp:
            result="TP_first"
        elif touch_sl:
            result="SL_first"
        if result:
            rows.append((asset,tp_points,sl_points,entry_index,j,int(t[entry_index]),
                int(t[j]),"LONG" if side>0 else "SHORT",ep,tp,sl,result,j-entry_index))
            p=None
    count={k:sum(x[-2]==k for x in rows) for k in ("TP_first","SL_first","ambiguous_same_1m")}
    count["unresolved_at_data_end"]=int(p is not None)
    count["trades_closed"]=len(rows)
    count["trades_opened"]=len(rows)+int(p is not None)
    count["total_strategy_signals"]=nsignals
    count["ignored_signals_during_position"]=skipped
    count["resolved_first_touches"]=count["TP_first"]+count["SL_first"]
    resolved=count["resolved_first_touches"]
    count["TP_first_percent_resolved"]=round(100*count["TP_first"]/resolved,2) if resolved else None
    count["SL_first_percent_resolved"]=round(100*count["SL_first"]/resolved,2) if resolved else None
    count["TP_first_percent_all_opened"]=round(100*count["TP_first"]/count["trades_opened"],2) if count["trades_opened"] else None
    return rows,count

def main():
    result={"strategy":"1H closed candle EMA20 touch-and-reclaim with established Supertrend(10,3); filtered variant 1H ATR14 expansion >=1x previous20 mean and 1H volume >=1.5x previous20 mean",
            "data":"archived genuine Delta India 1m traded OHLC",
            "entry_interval":"2025-01-01 to 2026-10-31 UTC 22 complete months",
            "fill":"next 1m open after fully closed hourly signal",
            "exit":"fixed TP/SL first 1m touch; gap-aware; simultaneous 1m hit ambiguous",
            "no_maximum_holding_time":True,
            "no_other_exits":True,
            "exclusivity":"one open trade per asset at a time; ignore fresh signals while holding",
            "ETH_mapping":"each BTC-equivalent TP or SL is entry_price * (BTC_points / 80000)",
            "costs":"not included (first touch, not real-money profit)",
            "results":{}}
    trades=[]
    for asset in ("BTC","ETH"):
        minutes,_,manifest=load(asset)
        hours=hourly_from_minutes(minutes)
        assert len(hours)*60==len(minutes)
        print("DATA_1H_FIRST_TOUCH",asset,len(minutes),len(hours),
              str(minutes.index[0]),str(minutes.index[-1]),flush=True)
        for name,filtered in (("strict_ATR_volume_filters",True),("no_ATR_volume_filters",False)):
            signals=signal_index(hours,len(minutes),filtered)
            for tp,sl in PAIRS:
                rows,stat=replay(asset,minutes,signals,tp,sl)
                result["results"][f"{asset}_{name}_{tp}_{sl}"]=stat
                trades.extend(rows)
                print("RESULT_1H_FIRST_TOUCH",asset,name,tp,sl,json.dumps(stat),flush=True)
    cols=("asset","tp_points_btc_equivalent","sl_points_btc_equivalent",
          "entry_minute_index","exit_minute_index","entry_epoch","exit_epoch",
          "side","entry_price","target_price","stop_price","result","hold_minutes")
    pd.DataFrame(trades,columns=cols).to_csv(OUT/"first_touches.csv.gz",index=False,compression="gzip")
    (OUT/"summary.json").write_text(json.dumps(result,indent=2)+"\n")
    print("COMPLETE_1H_FIRST_TOUCH_FOUR_PAIRS",flush=True)

if __name__=="__main__":
    main()
