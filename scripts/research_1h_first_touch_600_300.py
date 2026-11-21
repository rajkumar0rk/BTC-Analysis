#!/usr/bin/env python3
"""Reproducible 1H Supertrend(10,3) + EMA20 first-touch sensitivity study.

Uses closed 1H candles for signals and Delta India 1-minute candles for the
path from next-hour open. No guessed within-1H OHLC path. Signal windows
are independent; no extra trend flip, trading fees, or margin model.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd

START = pd.Timestamp("2025-01-01", tz="UTC")
END = pd.Timestamp("2026-11-01", tz="UTC")
TP_SL = ((200, 100), (400, 200), (600, 300))
HORIZONS = (60, 240, 1440)
BASE = Path("data/delta_india")
OUT = Path("analysis/one_hour_first_touch_600_300")

def load(asset):
    frames = []
    for p in sorted((BASE / asset / "1m").glob("20??-??.csv.gz")):
        if p.name >= "2026-11":
            continue
        x = pd.read_csv(p, compression="gzip")
        x["time"] = pd.to_datetime(x["time"].astype("int64"), unit="s", utc=True)
        frames.append(x[["time", "open", "high", "low", "close", "volume"]])
    d = pd.concat(frames, ignore_index=True).sort_values("time").set_index("time")
    d = d[(d.index >= START) & (d.index < END)]
    if d.empty or d.index.has_duplicates or not d.index.to_series().diff().iloc[1:].eq(pd.Timedelta(minutes=1)).all():
        raise ValueError(f"{asset}: empty/duplicates/missing minutes")
    return d

def supertrend(h):
    high, low, close = [h[x].to_numpy(dtype=float) for x in ("high","low","close")]
    n = len(h)
    prev_c = np.r_[close[0], close[:-1]]
    tr = np.maximum(high-low, np.maximum(np.abs(high-prev_c), np.abs(low-prev_c)))
    atr = np.full(n, np.nan)
    length, factor = 10, 3.0
    atr[length-1] = np.mean(tr[:length])
    for i in range(length,n):
        atr[i] = (atr[i-1]*(length-1)+tr[i])/length
    upper = (high+low)/2 + factor*atr
    lower = (high+low)/2 - factor*atr
    direction = np.zeros(n,dtype=np.int8)
    final_u = np.full(n,np.nan)
    final_l = np.full(n,np.nan)
    final_u[length-1],final_l[length-1] = upper[length-1],lower[length-1]
    direction[length-1] = 1
    for i in range(length,n):
        final_u[i] = upper[i] if (upper[i]<final_u[i-1] or close[i-1]>final_u[i-1]) else final_u[i-1]
        final_l[i] = lower[i] if (lower[i]>final_l[i-1] or close[i-1]<final_l[i-1]) else final_l[i-1]
        if direction[i-1] == 1:
            direction[i] = -1 if close[i] > final_u[i] else 1
        else:
            direction[i] = 1 if close[i] < final_l[i] else -1
    return direction

def signals(d):
    h = d.resample("1h", label="left", closed="left").agg(
        {"open":"first","high":"max","low":"min","close":"last","volume":"sum"})
    ema = h["close"].ewm(span=20,adjust=False).mean()
    dr = supertrend(h)
    same = np.r_[False, dr[:-1]==dr[1:]]
    long = (dr == -1) & same & (h["low"].to_numpy() <= ema.to_numpy()) & (h["close"].to_numpy() > ema.to_numpy())
    short= (dr == 1) & same & (h["high"].to_numpy() >= ema.to_numpy()) & (h["close"].to_numpy() < ema.to_numpy())
    a=np.flatnonzero(long | short)
    return h.index[a],np.where(long[a],1,-1)

def test(d,times,sides,asset):
    ts = d.index.to_numpy(dtype='datetime64[s]').astype(np.int64)
    op,hi,lo = [d[c].to_numpy(dtype=float) for c in ("open","high","low")]
    totals=[]
    print("ENTRY_DEBUG",asset,"numsignals",len(times),"numsides",len(sides),"first_time",str(times[0]),"when",int(times[0].timestamp())+3600,"tsfirst",int(ts[0]),"tslast",int(ts[-1]),"search",int(np.searchsorted(ts,int(times[0].timestamp())+3600)),"len",len(d),flush=True)
    for horizon in HORIZONS:
        for btc_tp,btc_sl in TP_SL:
            tp,sl,tie,neither=0,0,0,0
            for signal_time,side in zip(times,sides):
                when=int(signal_time.timestamp())+3600
                j=int(np.searchsorted(ts,when))
                if j >= len(d): continue
                entry=op[j]
                end=min(j+horizon,len(d))
                if end-j<horizon: continue
                tp_dist=btc_tp if asset=="BTCUSD" else entry*(btc_tp/80000.0)
                sl_dist=btc_sl if asset=="BTCUSD" else entry*(btc_sl/80000.0)
                if side==1:
                    target=hi[j:end]>=entry+tp_dist
                    stop=lo[j:end]<=entry-sl_dist
                else:
                    target=lo[j:end]<=entry-tp_dist
                    stop=hi[j:end]>=entry+sl_dist
                ti=np.flatnonzero(target)
                si=np.flatnonzero(stop)
                ti=int(ti[0]) if len(ti) else horizon+1
                si=int(si[0]) if len(si) else horizon+1
                if ti==si and ti<=horizon:
                    tie+=1;sl+=1
                elif ti<si:
                    tp+=1
                elif si<ti:
                    sl+=1
                else:
                    neither+=1
            decided=tp+sl
            row=dict(asset=asset,horizon_minutes=horizon,
                    btc_equiv_tp=btc_tp,btc_equiv_sl=btc_sl,
                    tp_first=tp,sl_first=sl,unknown_same_minute=tie,
                    neither=neither,total=decided+neither,
                    tp_first_pct_decided=round(100*tp/decided,2) if decided else None,
                    sl_first_pct_decided=round(100*sl/decided,2) if decided else None,
                    tp_first_pct_all=round(100*tp/(decided+neither),2) if decided+neither else None)
            totals.append(row)
            print("TOUCH_RESULT",json.dumps(row),flush=True)
    return totals

def main():
    allrows=[]
    OUT.mkdir(parents=True,exist_ok=True)
    for asset in ("BTCUSD","ETHUSD"):
        d=load(asset)
        times,sides=signals(d)
        print("SIGNALS",asset,len(times),"bars",len(d),flush=True)
        allrows.extend(test(d,times,sides,asset))
    pd.DataFrame(allrows).to_csv(OUT/"comparison.csv",index=False)
    (OUT/"methodology.md").write_text(
        "# First touch sensitivity\n\nSource Delta India BTCUSD/ETHUSD true 1m 2025-01 to 2026-10. "
        "Signal 1h Supertrend 10,3 (Wilder ATR) established trend plus EMA20 candle wick touch and close back. "
        "Entry next hourly open; first 1m high/low touch within horizon; simultaneous 1m touches SL-first "
        "(conservative). BTC thresholds literal USD points; ETH distance = entry price x BTC-equivalent/80000. "
        "No fees (outcome classification only), no overlapping-position suppression, no trend-flip early exits. "
        "Independent entry signals can overlap. This is a reconstruction; compare prior trade ledger before "
        "attributing it to any exact TradingView backtest.\n",encoding="utf8")
    print("COMPLETE",len(allrows))
if __name__=="__main__":
    main()
