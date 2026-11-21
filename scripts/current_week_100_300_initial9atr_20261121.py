#!/usr/bin/env python3
"""Current IST week Nov16-21 2026, activation 100 / EXTRA stop points 300 / initial 9ATR14.

Unfiltered 1H EMA20+ST10,3 entries, 1H Supertrend flip exit ON, fixed
Trailing Distance OFF, 1m stop updates at each COMPLETED 1m bar effective
NEXT 1m bar. Both MARK-trigger and traded-trigger point-stop models. The
core compute() function is reused without changes. Fixed ~$1k target
notional, historical taker 0.05% EACH side + GST18%; no funding/slippage,
spread/orderbook, liquidations, or funded small-account execution modeling.

Source archives in research branch are stale in November. Refresh ONLY the
local runner copy of each November partition from Delta India PUBLIC
/v2/history/candles (BTCUSD, ETHUSD, MARK:BTCUSD, MARK:ETHUSD), preserving
existing rows and SHA-verified full-history months, rejecting any missing
minute. DO NOT git-add price archive changes. Git output is reporting only.
Target end 2026-11-21 02:00 UTC (07:30 IST), comfortably before 09:00 IST
current time. Week start Monday 2026-11-16 00:00 IST / Sunday 18:30 UTC.
End is exclusive. Open positions are excluded from realized net PnL.
"""
from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

import numpy as np
import pandas as pd

from extra_trailing_stop_100_300_initial9atr_full22_20261121 import (
    ACTIVATION_POINTS, TRAIL_STOP_POINTS, INIT_STOP_SCALE, unit_tests
)
from optimize_1h_additional_trailing_stop_points_20261121 import (
    compute, prepare, frame_rows, metrics
)

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"analysis"/"current_week_100_300_initial9atr_20261121"
OUT.mkdir(parents=True,exist_ok=True)
NOV_START=int(pd.Timestamp("2026-11-01T00:00:00Z").timestamp())
WEEK_START=int(pd.Timestamp("2026-11-16T00:00:00+05:30").timestamp())
END=int(pd.Timestamp("2026-11-21T02:00:00Z").timestamp())
assert WEEK_START<END
BASE_URL="https://api.india.delta.exchange/v2/history/candles"
HEADERS={"Accept":"application/json","User-Agent":"BTC-Analysis-backtest-weekly-100-300-9ATR/1.0"}
CHUNK_MINUTES=1000

def fetch_window(symbol,start_inclusive,stop_exclusive):
    rows={}
    for begin in range(start_inclusive,stop_exclusive,CHUNK_MINUTES*60):
        stop=min(stop_exclusive,begin+CHUNK_MINUTES*60)
        params=urlencode({"symbol":symbol,"resolution":"1m","start":begin,
                           "end":stop-60})
        url=BASE_URL+"?"+params
        last_exc=None
        for attempt in range(6):
            try:
                req=Request(url,headers=HEADERS)
                with urlopen(req,timeout=40) as response:
                    j=json.load(response)
                if not isinstance(j,dict) or j.get("success") is not True or not isinstance(j.get("result"),list):
                    raise RuntimeError(f"Delta API unexpected response {symbol} {begin}: {str(j)[:350]}")
                for x in j["result"]:
                    ts=int(x["time"])
                    if not begin<=ts<stop:
                        continue
                    if ts%60:
                        raise ValueError(f"Non-minute {symbol}: {ts}")
                    vals={k:float(x[k]) for k in ("open","high","low","close")}
                    if vals["low"]<=0 or vals["high"]<max(vals["open"],vals["close"]) or vals["low"]>min(vals["open"],vals["close"]):
                        raise ValueError(f"Invalid OHLC {symbol} at {ts}")
                    if not symbol.startswith("MARK:"):
                        vals["volume"]=float(x["volume"])
                        if vals["volume"]<0:raise ValueError(f"Negative volume {symbol} at {ts}")
                    vals["time"]=ts
                    rows[ts]=vals
                last_exc=None
                break
            except (HTTPError,URLError,OSError,TimeoutError,ValueError,RuntimeError) as exc:
                last_exc=exc
                if isinstance(exc,HTTPError) and exc.code not in (408,429,500,502,503,504):
                    raise
                if attempt<5:time.sleep(min(20,2**attempt))
        if last_exc is not None:
            raise RuntimeError(f"Historical Delta API retrieval failed: {symbol} interval {begin}..{stop}: {last_exc}") from last_exc
        expected=(stop-begin)//60
        observed=sum(1 for ts in rows if begin<=ts<stop)
        if observed!=expected:
            present=set(ts for ts in rows if begin<=ts<stop)
            missing=[x for x in range(begin,stop,60) if x not in present][:8]
            raise RuntimeError(f"{symbol} API incomplete for {datetime.fromtimestamp(begin,timezone.utc)}: "
                               f"{observed}/{expected}, missing epochs {missing} -- no fabricated candles.")
        print("DELTA_API_WINDOW_COMPLETE",symbol,str(pd.Timestamp(begin,unit="s",tz="UTC")),
              observed,flush=True)
        time.sleep(.12)
    return rows

def append_source(asset,kind):
    assetdir=ROOT/"data"/"delta_india"/(asset+"USD")
    if kind=="traded":
        dir=assetdir/"1m";symbol=asset+"USD"
    else:
        dir=assetdir/"institutional"/"history"/"mark_1m";symbol="MARK:"+asset+"USD"
    path=dir/"2026-11.csv.gz"
    old=pd.read_csv(path,compression="gzip")
    times=old.time.to_numpy(dtype=np.int64)
    assert times[0]==NOV_START and len(times)>0 and np.all(np.diff(times)==60)
    last_old=int(times[-1])
    assert last_old<END-60,f"Old November partition extends beyond chosen cutoff {symbol}"
    # Re-fetch last 3 already archived bars as a continuity check.
    first_fetch=last_old-120
    latest=fetch_window(symbol,first_fetch,END)
    for ts in range(first_fetch,last_old+60,60):
        if ts not in latest:raise AssertionError("API overlap missing")
        row=old.loc[old.time==ts].iloc[0]
        for c in ("open","high","low","close"):
            # preserve known archived data even if the exchange later revises it.
            # Minor revision is logged, never silently substituted.
            if abs(float(row[c])-latest[ts][c])>max(.1,abs(float(row[c]))*.000001):
                print("WARN_ARCHIVE_API_OVERLAP_DIFF",symbol,ts,c,float(row[c]),latest[ts][c],flush=True)
    newrows=[latest[ts] for ts in range(last_old+60,END,60)]
    update=pd.DataFrame(newrows)
    # Mark candles often omit a volume field; preserve original schema.
    for c in old.columns:
        if c not in update.columns:
            update[c]=np.nan
    for c in update.columns:
        if c not in old.columns:
            old[c]=np.nan
    update=update[old.columns]
    allrows=pd.concat([old,update],ignore_index=True)
    t=allrows.time.to_numpy(dtype=np.int64)
    assert t[0]==NOV_START and t[-1]==END-60
    assert len(t)==(END-NOV_START)//60 and np.all(np.diff(t)==60)
    allrows.to_csv(path,index=False,compression={"method":"gzip","compresslevel":6,"mtime":0})
    return {
      "symbol":symbol,"archived_end_utc":str(pd.Timestamp(last_old,unit="s",tz="UTC")),
      "fresh_end_inclusive_utc":str(pd.Timestamp(END-60,unit="s",tz="UTC")),
      "source":"Delta India PUBLIC v2/history/candles API",
      "fresh_minutes":len(newrows),"total_nov_minutes":len(t),
      "path":str(path.relative_to(ROOT)),
      "sha256":hashlib.sha256(path.read_bytes()).hexdigest()
    }

def refresh_nov():
    evidence={}
    for asset in ("BTC","ETH"):
        traded=append_source(asset,"traded")
        mark=append_source(asset,"mark")
        assert traded["total_nov_minutes"]==mark["total_nov_minutes"]
        man_path=ROOT/"data"/"delta_india"/(asset+"USD")/"1m"/"manifest.json"
        j=json.loads(man_path.read_text())
        rec=j["partitions"][-1]
        assert rec["file"]=="2026-11.csv.gz"
        rec["utc_end_exclusive"]=str(pd.Timestamp(END,unit="s",tz="UTC"))
        rec["observed_candles"]=traded["total_nov_minutes"]
        rec["expected_minutes"]=traded["total_nov_minutes"]
        rec["missing_minutes"]=0
        rec["sha256_gzip"]=traded["sha256"]
        j["requested_through_utc"]="2026-11-21"
        j["generated_at_utc"]=str(pd.Timestamp.now(tz="UTC"))
        man_path.write_text(json.dumps(j,indent=2)+"\n")
        evidence[asset]={"traded":traded,"mark":mark}
    return evidence

def summarize_week(frame):
    full=frame.copy()
    full["exit_epoch"]=pd.to_datetime(full["exit_utc"],utc=True).astype("int64")//1_000_000_000
    within=full.loc[(full.exit_epoch>=WEEK_START)&(full.exit_epoch<END)].copy()
    gains=float(within.loc[within.net_usd>0,"net_usd"].sum())
    losses=-float(within.loc[within.net_usd<0,"net_usd"].sum())
    cum=np.r_[0.,within.net_usd.cumsum().to_numpy(dtype=np.float64)]
    dd=float(np.max(np.maximum.accumulate(cum)-cum))
    within["exit_day_ist"]=pd.to_datetime(within.exit_utc,utc=True).dt.tz_convert(
       "Asia/Kolkata").dt.strftime("%Y-%m-%d")
    daily=[]
    days=pd.date_range("2026-11-16","2026-11-21",freq="D")
    for day in days:
        z=within.loc[within.exit_day_ist==str(day.date())]
        p=float(z.loc[z.net_usd>0,"net_usd"].sum())
        l=-float(z.loc[z.net_usd<0,"net_usd"].sum())
        daily.append({"date_ist":str(day.date()),"trades":int(len(z)),
                      "net_usd":round(float(z.net_usd.sum()),4),
                      "profit_factor":round(p/l,4) if l else None})
    return {
      "net_usd":round(float(within.net_usd.sum()),4),
      "gross_usd":round(float(within.gross_usd.sum()),4),
      "fees_gst_usd":round(float(within.fees_gst_usd.sum()),4),
      "trades":int(len(within)),
      "wins":int((within.net_usd>0).sum()),
      "losses":int((within.net_usd<0).sum()),
      "profit_factor":round(gains/losses,4) if losses else None,
      "win_rate_pct":round(100*float((within.net_usd>0).mean()),2) if len(within) else None,
      "max_closed_trade_drawdown_usd":round(dd,4),
      "daily_ist":daily,
      "trades_exiting_week":within
    }

def main():
    unit_tests()
    evidence=refresh_nov()
    prev=json.loads((ROOT/"analysis"/"extra_trailing_stop_100_300_initial9atr_full22_20261121"/"summary.json").read_text())
    report={
      "start_ist":"2026-11-16T00:00:00+05:30",
      "end_exclusive_ist":"2026-11-21T07:30:00+05:30",
      "window_status":"current week INCOMPLETE; through verified 1m historical archive UTC 2026-11-21 01:59",
      "settings":{
        "activation_btc_equiv_points":ACTIVATION_POINTS,
        "extra_trailing_stop_btc_equiv_points":TRAIL_STOP_POINTS,
        "fixed_trailing_distance_enabled":False,
        "initial_stop":"9x ATR(14) 1H, 1m monitored",
        "supertrend_flip_enabled":True,
        "entry_signal":"1H EMA20 touch/reclaim continuing Supertrend(10,3)",
        "volume_filter":False,"volatility_filter":False,
        "eth_point_scaling":"entry/80000, tick rounded",
      },
      "fee_model":"0.05% taker each leg, +GST18%; funding/spread/slippage/liquidation excluded",
      "reference_notional_usd":1000,
      "source_verification":evidence,
      "weekly_attribution":"count only trades REALIZED by an exit inside IST week; open PnL excluded",
      "scenarios":{}
    }
    for asset in ("BTC","ETH"):
        args,info=prepare(asset)
        assert args[0][-1]==END-60 and int(args[0][0])==int(pd.Timestamp("2025-01-01",tz="UTC").timestamp())
        cfg=[x.copy() for x in args]
        cfg[12]*=INIT_STOP_SCALE
        report["source_verification"][asset]["full_history"]=info
        for name,mode in (("mark",0),("traded",1)):
            trades,skips,wallet,openpos=compute(
                *cfg,float(ACTIVATION_POINTS),float(TRAIL_STOP_POINTS),
                int(asset=="ETH"),mode,False)
            df=frame_rows(trades)
            # The 2025-Oct2026 realized PnL must match the original run
            # EXACTLY; this is a regression test for matching strategy rules.
            former=prev["scenarios"][f"{asset.lower()}_{name}_walletguard_false"]
            old=metrics(df,[str(x) for x in pd.period_range("2025-01","2026-10",freq="M")])
            assert old["trades"]==former["full22"]["trades"], (asset,name,old["trades"],former["full22"]["trades"])
            assert abs(old["net_usd"]-former["full22"]["net_usd"])<.0002,(asset,name,old["net_usd"],former["full22"]["net_usd"])
            wk=summarize_week(df)
            weektrades=wk.pop("trades_exiting_week")
            wk["open_at_cutoff"]=bool(openpos)
            wk["regression_match_22months"]=True
            wk["wallet_guard_enabled"]=False
            wk["skips_prior_full_history"]={
                 "already_open":int(skips[0]),"entry_deviation":int(skips[1]),
                 "wallet_gate":int(skips[2]),"quantity":int(skips[3]),
                 "invalid_initial_stop":int(skips[4])
            }
            key=f"{asset.lower()}_{name}"
            report["scenarios"][key]=wk
            weektrades.to_csv(OUT/f"{key}_weekly_trades.csv",index=False)
            pd.DataFrame(wk["daily_ist"]).to_csv(OUT/f"{key}_daily_ist.csv",index=False)
            print("CURRENT_WEEK_100_300_SL9ATR",key,json.dumps({
                "trades":wk["trades"],"net":wk["net_usd"],"pf":wk["profit_factor"],
                "wins":wk["wins"],"fee":wk["fees_gst_usd"],"open":wk["open_at_cutoff"]
            }),flush=True)
    (OUT/"summary.json").write_text(json.dumps(report,indent=2)+"\n")
    print("CURRENT_WEEK_100_300_SL9ATR_VERIFIED",str(OUT),flush=True)

if __name__=="__main__":
    main()
