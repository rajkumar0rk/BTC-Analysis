#!/usr/bin/env python3
"""Replay Friday 2026-11-20 IST, using REAL Delta India 1m mark and futures candles.

The previous 2025-2026 dataset ended before yesterday; this script explicitly
fetches the required UTC dates for fresh 1m traded/mark data from Delta.
Starts fresh $100 portfolio at IST 2026-11-20 00:00.
Signals may use earlier completed 15m bars as warmup.
Signals only enter within IST 2026-11-20; no entries before or after.
Open positions at 23:59 IST remain open: their unrealized P&L is separately
estimated but NOT counted as realized profits/losses.

No future intraminute path assumption and NO change to running VPS bot.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from collect_delta_institutional_data import http_get, validate_ohlc
from replay_btc_ema_st_screenshot import indicators
from replay_ema_st_demo_mark_1m_20261121 import evaluate, unit_test

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "analysis" / "demo_yesterday_2026_11_20_ist"
OUT.mkdir(parents=True,exist_ok=True)
TZ = "Asia/Kolkata"
DAY_START = pd.Timestamp("2026-11-20 00:00:00",tz=TZ).tz_convert("UTC")
DAY_END = pd.Timestamp("2026-11-21 00:00:00",tz=TZ).tz_convert("UTC")
DATA_START = pd.Timestamp("2026-11-18 00:00:00",tz="UTC")
STOP = DAY_END
FIELDS=("time","open","high","low","close","volume")

def obtain(symbol, mark):
    first=int(DATA_START.timestamp())
    stop=int(STOP.timestamp())
    allrows={}
    for beg in range(first,stop,1200*60):
        finish=min(beg+1200*60,stop)
        raw=http_get("/v2/history/candles",{
            "symbol":("MARK:"+symbol) if mark else symbol,
            "resolution":"1m","start":beg,"end":finish-1,
        })
        z=validate_ohlc(raw,60,beg,finish)
        allrows.update(z)
        print("FETCHED",("MARK:" if mark else "")+symbol,
              datetime.fromtimestamp(beg,timezone.utc).isoformat(),
              len(z),"/",(finish-beg)//60,flush=True)
        time.sleep(0.20)
    expected=np.arange(first,stop,60,dtype="int64")
    observed=np.array(sorted(allrows),dtype="int64")
    if len(expected)!=len(observed) or not np.array_equal(expected,observed):
        missing=np.setdiff1d(expected,observed)
        raise RuntimeError(f"{symbol} {'mark' if mark else 'traded'} 1m series has {len(missing)} missing minutes: {missing[:30]}")
    frame=pd.DataFrame([allrows[t] for t in observed])
    for col in FIELDS: frame[col]=pd.to_numeric(frame[col],errors="coerce")
    if not mark and frame[list(FIELDS)].isna().any().any():
        raise RuntimeError(f"Bad non-finite traded OHLCV for {symbol}")
    if mark and frame[["time","open","high","low","close"]].isna().any().any():
        raise RuntimeError(f"Bad non-finite MARK OHLC for {symbol}")
    frame["time"]=frame["time"].astype("int64")
    assert (frame.high>=frame[["open","close","low"]].max(axis=1)).all()
    assert (frame.low<=frame[["open","close","high"]].min(axis=1)).all()
    frame["dt"]=pd.to_datetime(frame.time,unit="s",utc=True)
    frame.to_csv(OUT/f"{symbol.lower()}_{'mark' if mark else 'traded'}_1m_source.csv.gz",
                 index=False,compression="gzip")
    return frame


def build_bars(traded):
    minute=traded.set_index("dt")[["time","open","high","low","close","volume"]]
    x=minute.resample("15min",origin="epoch",label="left",closed="left").agg({
        "open":"first","high":"max","low":"min","close":"last","volume":"sum",
        "time":"count",
    })
    assert (x.time==15).all(), "Inconsistent 15m candle aggregation"
    f=indicators(x.drop(columns="time"))
    assert len(minute)==len(f)*15
    return minute,f


def main():
    unit_test()
    results={
        "date_ist":"2026-11-20",
        "timezone":TZ,
        "entry_start_utc":str(DAY_START),
        "entry_end_exclusive_utc":str(DAY_END),
        "warmup_start_utc":str(DATA_START),
        "history_source":"https://api.india.delta.exchange/v2/history/candles",
        "source_execution":"1m MARK:SYMBOL OHLC, next-minute mark-close trailing updates; actual three-second observations unavailable",
        "equity": "Fresh $100 separate for each asset and scenario, not equity carried from Jan 2025",
        "funding": "excluded; unverified historical actual payment",
        "spread": "excluded; no bid/ask history",
        "data":{},"scenarios":{},
    }
    for asset in ("BTC","ETH"):
        symbol=f"{asset}USD"
        traded=obtain(symbol,mark=False)
        mark=obtain(symbol,mark=True)
        minute,bars=build_bars(traded)
        assert (minute.time.to_numpy()==mark.time.to_numpy()).all()
        mark=mark[["open","high","low","close"]]
        results["data"][asset]={
            "minutes":len(minute),
            "first_utc":str(minute.index[0]),
            "last_utc":str(minute.index[-1]),
            "signal_bars":len(bars),
            "entry_window_minutes":int((DAY_END-DAY_START).total_seconds()/60),
            "observed_traded_minutes_in_window":int(((minute.index>=DAY_START)&(minute.index<DAY_END)).sum()),
        }
        assert results["data"][asset]["observed_traded_minutes_in_window"]==1440
        for sample in ("close","extreme"):
            for offer in (False,True):
                for slip in (0.,.5 if asset=="BTC" else .05):
                    label=f'{asset.lower()}_{sample}_{"offer" if offer else "nooffer"}_{"onetick" if slip else "noslip"}'
                    transactions,monthly,report=evaluate(
                        asset,minute,mark,bars,sample,offer,slip,
                        entry_start=DAY_START,entry_end=DAY_END)
                    # Every generated position has entered today; if 0 trades,
                    # still report any pending open position separately.
                    if len(transactions):
                        stamps=pd.to_datetime(transactions.entry_utc,utc=True)
                        assert ((stamps>=DAY_START)&(stamps<DAY_END)).all()
                        assert (pd.to_datetime(transactions.exit_utc,utc=True)<DAY_END).all()
                    transactions.to_csv(OUT/f"{label}_trades.csv",index=False)
                    report["date_ist"]="2026-11-20"
                    report["total_opened"]=len(transactions)+int(report["open_at_end"] is not None)
                    report["realized_pnl_usd"]=report["net_usd"]
                    report["fresh_starting_balance_usd"]=100.
                    report["closed_trade_count"]=len(transactions)
                    report["mark_to_market_estimated_equity_usd"]=round(
                        report["ending_usd"]+(report["open_at_end"]["hypothetical_net_if_closed_usd"]
                        if report["open_at_end"] is not None else 0),4)
                    results["scenarios"][label]=report
                    print("YESTERDAY_IST_REPLAY",label,json.dumps(report),flush=True)
    (OUT/"summary.json").write_text(json.dumps(results,indent=2)+"\n",encoding="utf-8")
    print("DONE_YESTERDAY_IST",OUT,flush=True)


if __name__=="__main__":
    main()
