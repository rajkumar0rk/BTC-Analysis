#!/usr/bin/env python3
"""Read-only THIS WEEK (Mon Nov 16 through most recent complete data) research.

Compare BTC and ETH latest FULL-HISTORY point-trailing stop study:
  original activation100 stop500; best-22-month activation100 stop3000 BTC,
  activation100 stop8000 ETH. Fixed Trailing Distance always OFF.
  Optional whole-grid-best BTC activation200 stop3000, ETH activation50 stop8000.

Append actual newer public Delta India production TRADED and MARK 1m history
to same source archives IN MEMORY ONLY; do not modify historical files.
Require STRICT gap-free price+mark alignment. 1H EMA20+Supertrend signals,
2xATR14 initial SL, completed 1m candle trailing stop updates effective
next minute. MARK stop trigger; traded minute CLOSE as modeled market fill.
NOT Demo testnet and NOT true tick or order-book fills. Fees 0.05% taker
each side + GST18%; funding, spread, slippage, PM liquidation excluded.

Weekly realized P&L here is *calendar exit dated* Asia/Kolkata Nov16-Nov21;
unrealized P&L not invented. Full series used for indicator and position state.
"""
from __future__ import annotations
import json
import time
from pathlib import Path
from datetime import datetime,timezone,timedelta
from urllib.parse import urlencode
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError

import numpy as np
import pandas as pd

from full_history_1h_trailing_100_50_2025_2026 import read_asset,signal_map
from optimize_1h_additional_trailing_stop_points_20261121 import (
    compute,frame_rows,checks
)

OUTPUT=Path(__file__).resolve().parents[1]/"analysis"/"weekly_nov16_21_2026_stop_points"
OUTPUT.mkdir(parents=True,exist_ok=True)
API="https://api.india.delta.exchange/v2/history/candles"
IST="Asia/Kolkata"
WEEK_BEGIN=pd.Timestamp("2026-11-16 00:00:00",tz=IST)
DAY_ORDER=[str(x.date()) for x in pd.date_range("2026-11-16","2026-11-21")]
UTC=timezone.utc
HEADERS={"Accept":"application/json","User-Agent":"BTC-Analysis-weekly-stop-research/1.0"}
CONFIG={
  "BTC":[("requested_100_500",100,500),("best_fixed100_100_3000",100,3000),("best_grid_200_3000",200,3000)],
  "ETH":[("requested_100_500",100,500),("best_fixed100_100_8000",100,8000),("best_grid_50_8000",50,8000)]
}

def query(symbol,start,end):
    url=API+"?"+urlencode({"symbol":symbol,"resolution":"1m",
                           "start":start,"end":end-1})
    last=None
    for attempt in range(5):
        try:
            req=Request(url,headers=HEADERS)
            with urlopen(req,timeout=35) as x:
                p=json.load(x)
            if not isinstance(p,dict) or p.get("success") is not True or not isinstance(p.get("result"),list):
                raise ValueError(f"Delta historical API unsuccessful for {symbol}: {str(p)[:220]}")
            return p["result"]
        except (HTTPError,URLError,TimeoutError,OSError,ValueError) as exc:
            last=exc
            if attempt<4:time.sleep(min(2**attempt,8))
    raise RuntimeError(f"Unable to fetch {symbol} [{start},{end}): {last}")

def recent(symbol,start,end):
    events={}
    for lo in range(start,end,1000*60):
        hi=min(lo+1000*60,end)
        rows=query(symbol,lo,hi)
        for r in rows:
            t=int(r["time"])
            if lo<=t<hi:
                if t in events:
                    raise RuntimeError(f"Duplicate {symbol} time {t}")
                events[t]=r
        print("RECENT",symbol,"UTC",datetime.fromtimestamp(lo,UTC).isoformat(),
              datetime.fromtimestamp(hi,UTC).isoformat(),"API rows",len(rows),flush=True)
        time.sleep(.15)
    expected=np.arange(start,end,60,dtype=np.int64)
    got=np.asarray(sorted(events),dtype=np.int64)
    if not np.array_equal(expected,got):
        missing=np.setdiff1d(expected,got)
        raise RuntimeError(f"Missing/incomplete {symbol} candles; {len(missing)} missing. "
                           f"Example {missing[:8].tolist()} (STOP; never invent)")
    use=["time","open","high","low","close"]+(["volume"] if not symbol.startswith("MARK:") else [])
    df=pd.DataFrame([{k:float(events[int(t)][k]) if k!="time" else int(t) for k in use}
                     for t in expected])
    if (df[["open","high","low","close"]]<=0).any().any():
        raise RuntimeError(f"Invalid prices in {symbol}")
    if (df["high"]<df[["open","close","low"]].max(axis=1)).any() or (df["low"]>df[["open","close","high"]].min(axis=1)).any():
        raise RuntimeError(f"Invalid OHLC order {symbol}")
    df.index=pd.to_datetime(df.time.astype("int64"),unit="s",utc=True)
    return df

def prepare(asset,end_exclusive):
    traded,mark,info=read_asset(asset)
    last_ts=int(traded.time.iloc[-1])
    assert last_ts==int(mark.time.iloc[-1])
    first_add=last_ts+60
    assert first_add<end_exclusive
    new_traded=recent(asset+"USD",first_add,end_exclusive)
    new_mark=recent("MARK:"+asset+"USD",first_add,end_exclusive)
    assert np.array_equal(new_traded.time.to_numpy(),new_mark.time.to_numpy())
    trade=pd.concat((traded,new_traded),axis=0)
    m=pd.concat((mark,new_mark),axis=0)
    assert np.array_equal(trade.time.to_numpy(),m.time.to_numpy())
    assert np.all(np.diff(trade.time.to_numpy(dtype=np.int64))==60)
    assert trade.time.iloc[-1]==end_exclusive-60
    events,meta=signal_map(trade,asset)
    n=len(trade)
    ts=trade.time.to_numpy(dtype=np.int64)
    side=np.zeros(n,dtype=np.int8);flip=np.zeros(n,dtype=np.int8)
    close=np.zeros(n,dtype=np.float64);dist=np.zeros(n,dtype=np.float64)
    begin=int(ts[0])
    for t,e in events.items():
        if t>end_exclusive-60:continue
        i=(int(t)-begin)//60
        if i<0 or i>=n or int(ts[i])!=int(t):
            raise RuntimeError("Indicator signal index misalignment")
        side[i]=int(e["side"]);flip[i]=int(e["flip"])
        close[i]=float(e["close"]);dist[i]=float(e["stopdist"])
    args=[
      ts,
      trade.open.to_numpy(dtype=np.float64),trade.high.to_numpy(dtype=np.float64),
      trade.low.to_numpy(dtype=np.float64),trade.close.to_numpy(dtype=np.float64),
      m.open.to_numpy(dtype=np.float64),m.high.to_numpy(dtype=np.float64),
      m.low.to_numpy(dtype=np.float64),m.close.to_numpy(dtype=np.float64),
      side,flip,close,dist
    ]
    summary={**info,**meta,"fetched_traded_1m":len(new_traded),
             "fetched_mark_1m":len(new_mark),
             "most_recent_traded_utc":str(trade.index[-1]),
             "most_recent_mark_utc":str(m.index[-1])}
    return args,summary

def stats(frame,cutoff):
    if frame.empty:
        z=frame.copy()
    else:
        dt=pd.to_datetime(frame.exit_utc,utc=True)
        z=frame[(dt>=WEEK_BEGIN.tz_convert("UTC")) & (dt<cutoff)].copy()
    if not z.empty:
        z["entry_ist"]=pd.to_datetime(z.entry_utc,utc=True).dt.tz_convert(IST).astype(str)
        z["exit_ist"]=pd.to_datetime(z.exit_utc,utc=True).dt.tz_convert(IST).astype(str)
        z["day_ist"]=pd.to_datetime(z.exit_utc,utc=True).dt.tz_convert(IST).dt.strftime("%Y-%m-%d")
    positive=float(z.loc[z.net_usd>0,"net_usd"].sum())
    negative=float(-z.loc[z.net_usd<0,"net_usd"].sum())
    result={
       "net_realized_usd":round(float(z.net_usd.sum()),4),
       "gross_realized_usd":round(float(z.gross_usd.sum()),4),
       "assumed_fees_gst_usd":round(float(z.fees_gst_usd.sum()),4),
       "completed_trades":len(z),"wins":int((z.net_usd>0).sum()),
       "losses":int((z.net_usd<0).sum()),
       "win_rate_pct":round((z.net_usd>0).sum()/max(1,len(z))*100,2),
       "profit_factor":round(positive/negative,4) if negative>0 else None,
       "daily_exit_ist":[{
           "date":day,
           "net_usd":round(float(z.loc[z.day_ist==day,"net_usd"].sum()),4) if len(z) else 0,
           "trades":int((z.day_ist==day).sum()) if len(z) else 0
       } for day in DAY_ORDER]
    }
    return z,result

def main():
    checks()
    now=datetime.now(UTC)
    end=int((now-timedelta(minutes=12)).timestamp())//60*60
    cutoff=pd.Timestamp(end,unit="s",tz="UTC")
    assert pd.Timestamp("2026-11-21 00:00",tz="UTC")<=cutoff<pd.Timestamp("2026-11-23",tz="UTC"),f"Unexpected runner date {cutoff}"
    output={
       "research_week_start_ist":WEEK_BEGIN.isoformat(),
       "cutoff_utc_exclusive":str(cutoff),
       "cutoff_ist_exclusive":str(cutoff.tz_convert(IST)),
       "week_end_not_complete":True,
       "historical_venue":"Delta India production, NOT Delta Demo testnet",
       "signal":"1H EMA20+Supertrend(10,3), 2xATR(14) initial stop, native mark-price trigger proxy",
       "modeled_execution":"1m MARK high/low checks old stop, trailing stop tightened only at completed candle for next minute",
       "fill_model":"in-candle mark-trigger at that candle's traded CLOSE (PROXY); gaps and 1H ST flips at minute OPEN",
       "costs":"0.05% taker entry, 0.05% taker exit, 18% GST. Funding, bid/ask slippage, true PM liquidation excluded",
       "data_quality":"require minute-for-minute exact traded/MARK timestamps; no interpolation",
       "position_sizing":"fixed notional max $1000 reference, not fundable by $100 account if depleted",
       "configs":{"BTC":CONFIG["BTC"],"ETH":CONFIG["ETH"]},"dataset":{},"results":{}
    }
    for asset in ("BTC","ETH"):
        args,meta=prepare(asset,end)
        output["dataset"][asset]=meta
        for name,activation,stop in CONFIG[asset]:
            for mode in ("mark","traded"):
                rows,skips,wallet,openpos=compute(
                    *args,float(activation),float(stop),
                    1 if asset=="ETH" else 0,
                    0 if mode=="mark" else 1,
                    False)
                f=frame_rows(rows)
                weekly,d=stats(f,cutoff)
                d.update({"asset":asset,"mode":mode,
                          "activation_points":activation,"trailing_stop_points":stop,
                          "fixed_trailing_distance_enabled":False,
                          "open_position_at_cutoff":bool(openpos),
                          "sensitivity_vs_other_mode":"traded vs mark outcomes not exact execution bounds",
                          "running_reference_wallet_balance_usd":round(float(wallet),4)})
                key=f"{asset.lower()}_{mode}_{name}"
                output["results"][key]=d
                weekly.to_csv(OUTPUT/(key+"_this_week_trades.csv"),index=False)
                print("WEEK_RESULT",key,json.dumps(d),flush=True)
        del args
    (OUTPUT/"summary.json").write_text(json.dumps(output,indent=2)+"\n")
    print("WEEK_REPLAY_FINISHED",OUTPUT,flush=True)

if __name__=="__main__":
    main()
