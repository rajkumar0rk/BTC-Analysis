#!/usr/bin/env python3
"""First-hit analysis of 15m EMA20 + Supertrend on actual Delta India 1m bars.

Exactly reuse the previous 15m signal generator: ST(10,3), EMA20 reclaim,
exclude the ST flip candle, ATR14 expansion >= 1, volume ratio >= 1.5.
Confirmed 15m signal fills at NEXT 1m OPEN (the next 15m boundary).
Then ONLY a fixed TP +900 / SL -300 (BTC) or ETH percentage equivalents
(+1.125% / -0.375% of per-trade ETH entry) can close the position.
The next eligible signal after exit may start a new exclusive position.
No artificial max hold, flip-exit, ATR stop, leverage, trailing, or fees;
this is a first-touch classification, not a live P&L forecast.

Same-1m hits without a conclusive open-crossing are reported as ambiguous.
For sequencing only, exit that ambiguous trade conservatively at its stop.
All signals up to Nov 1, 2026 UTC; test until the archived Nov 19 minute
to let trades entered at the end of October finish.
"""
from pathlib import Path
import json
import sys
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT / "scripts"))
from replay_ema_st_15m_entries_1m_exits_20261121 import load, decisions

OUT=ROOT / "analysis" / "first_hit_15m_tp900_sl300_20261121"
CUTOFF=int(pd.Timestamp("2026-11-01",tz="UTC").timestamp())
START=int(pd.Timestamp("2025-01-01",tz="UTC").timestamp())
OUT.mkdir(parents=True,exist_ok=True)

def entries_unfiltered(bars,n):
    e=np.zeros(n,dtype=np.int8)
    direction=bars["dir"].to_numpy()
    ema=bars["ema"].to_numpy()
    low=bars["low"].to_numpy()
    high=bars["high"].to_numpy()
    close=bars["close"].to_numpy()
    for i in range(36,len(bars)-1):
        if not np.isfinite(ema[i]): continue
        j=(i+1)*15
        if direction[i]==direction[i-1]==-1 and low[i]<=ema[i] and close[i]>ema[i]:
            e[j]=1
        elif direction[i]==direction[i-1]==1 and high[i]>=ema[i] and close[i]<ema[i]:
            e[j]=-1
    return e

def simulate(asset,minute,signals,mode):
    op=minute["open"].to_numpy(dtype=np.float64)
    hi=minute["high"].to_numpy(dtype=np.float64)
    lo=minute["low"].to_numpy(dtype=np.float64)
    time=minute["time"].to_numpy(dtype=np.int64)
    assert len(time)==len(signals) and np.all(np.diff(time)==60)
    assert time[0]==START, time[0]
    trades=[]
    position=None
    signals_total=0
    skipped_busy=0
    for j in range(len(signals)):
        signal=int(signals[j])
        if signal and time[j]<CUTOFF:
            signals_total += 1
            if position is not None:
                skipped_busy += 1
            else:
                ep=float(op[j])
                disttp = 900.0 if asset=="BTC" else ep*(900.0/80000.0)
                distsl = 300.0 if asset=="BTC" else ep*(300.0/80000.0)
                position=dict(entry_index=j,entry_epoch=int(time[j]),side=signal,
                              entry=ep, tp=ep+signal*disttp, sl=ep-signal*distsl)
        if position is None: continue
        side=position["side"]
        opening=float(op[j])
        if side==1:
            open_tp=opening>=position["tp"]
            open_sl=opening<=position["sl"]
            hit_tp=hi[j]>=position["tp"]
            hit_sl=lo[j]<=position["sl"]
        else:
            open_tp=opening<=position["tp"]
            open_sl=opening>=position["sl"]
            hit_tp=lo[j]<=position["tp"]
            hit_sl=hi[j]>=position["sl"]
        cause=None
        if open_tp: cause="TP_first"
        elif open_sl: cause="SL_first"
        elif hit_tp and hit_sl: cause="ambiguous_same_1m"
        elif hit_tp: cause="TP_first"
        elif hit_sl: cause="SL_first"
        if cause is not None:
            trades.append(dict(asset=asset,variant=mode,
                  entry_epoch=position["entry_epoch"],exit_epoch=int(time[j]),
                  entry_utc=pd.Timestamp(position["entry_epoch"],unit="s",tz="UTC").isoformat(),
                  exit_utc=pd.Timestamp(time[j],unit="s",tz="UTC").isoformat(),
                  side="long" if side==1 else "short",
                  entry_price=position["entry"],
                  target_price=position["tp"],stop_price=position["sl"],
                  result=cause,hold_minutes=j-position["entry_index"]))
            position=None

    status={}
    n=len(trades)
    for result in ("TP_first","SL_first","ambiguous_same_1m"):
        status[result]=sum(x["result"]==result for x in trades)
    status["unresolved_at_data_end"]=int(position is not None)
    status["trades_closed"]=n
    status["trades_opened"]=n+status["unresolved_at_data_end"]
    status["total_strategy_signals"]=signals_total
    status["ignored_signals_during_position"]=skipped_busy
    resolved=status["TP_first"]+status["SL_first"]
    status["resolved_first_touches"]=resolved
    status["TP_first_percent_resolved"]=round(100*status["TP_first"]/resolved,2) if resolved else None
    status["SL_first_percent_resolved"]=round(100*status["SL_first"]/resolved,2) if resolved else None
    status["TP_first_percent_all_opened"]=round(100*status["TP_first"]/status["trades_opened"],2) if status["trades_opened"] else None
    status["all_signals_date_range_UTC"]="2025-01-01 to 2026-10-31 inclusive (22 complete months)"
    status["archive_end"]=str(minute.index[-1])
    if position:
        status["unresolved_entry"]=pd.Timestamp(position["entry_epoch"],unit="s",tz="UTC").isoformat()
    return trades,status

def main():
    summary={"parameters":{
        "entry_timeframe":"15m","execution_timeframe":"1m",
        "strategy":"EMA20 touch-and-reclaim in established Supertrend(10,3); filtered scenario also requires 15m ATR14/current-vs-prior20 >=1 and volume/current-vs-prior20 >=1.5",
        "BTC_tp_points":900,"BTC_sl_points":300,
        "ETH_tp_percent":1.125,"ETH_sl_percent":0.375,
        "no_signal_at_flip_candle":True,
        "max_holding_minutes":None,
        "opposite_ST_flip_exit":False,"trailing_stop":False,
        "position_policy":"one exclusive position; ignore entry signals while in position",
        "ambiguous_minute_treatment":"count as ambiguous; stop-first for portfolio sequencing only",
        "fees":"not applied; purely first-hit count",
        "entry_cutoff_UTC":"2026-11-01"},
        "source":"archived verified Delta Exchange India BTCUSD ETHUSD 1m OHLC",
        "results":{}}
    details=[]
    for asset in ("BTC","ETH"):
        m,bars,manifest=load(asset)
        assert len(m)>963360 and m.index[0]==pd.Timestamp("2025-01-01T00:00:00Z")
        strict,_,_=decisions(bars,len(m))
        plain=entries_unfiltered(bars,len(m))
        for mode,sig in (("strict_ATR_volume_filters",strict),("no_ATR_volume_filters",plain)):
            tr,stats=simulate(asset,m,sig,mode)
            details.extend(tr)
            summary["results"][f"{asset}_{mode}"]=stats
            print("FIRST_TOUCH_15M",asset,mode,json.dumps(stats),flush=True)
    pd.DataFrame(details).to_csv(OUT/"trade_first_touches.csv.gz",index=False,compression="gzip")
    (OUT/"summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf8")
    print("FIRST_TOUCH_15M_TP900_SL300_COMPLETE",flush=True)

if __name__=="__main__":
    main()
