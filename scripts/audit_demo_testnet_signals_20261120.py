#!/usr/bin/env python3
"""Audit whether actual Delta Demo TESTNET creates the previously simulated 20-Nov IST signals.

Read-only REST; no account authentication and no orders. Uses the same
15m/1h OHLC candles and exact EMA20/ST indicator implementation as the
Delta-Algo-Demo code. Reports both live-production and testnet public
market data, demonstrating why production replay is not DEMO order history.
A public signal does NOT prove that a VPS bot executed or was running.
"""
import json, math, time, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import numpy as np
from replay_btc_ema_st_screenshot import indicators

OUT=Path("analysis/demo_testnet_signal_audit_20261120")
OUT.mkdir(parents=True,exist_ok=True)
TZ="Asia/Kolkata"
BASES={"demo_testnet":"https://cdn-ind.testnet.deltaex.org","production":"https://api.india.delta.exchange"}
START=int(datetime(2026,11,12,tzinfo=timezone.utc).timestamp())
END=int(pd.Timestamp("2026-11-21 00:00",tz=TZ).tz_convert("UTC").timestamp())
DAY_START=pd.Timestamp("2026-11-20 00:00",tz=TZ)
DAY_END=pd.Timestamp("2026-11-21 00:00",tz=TZ)

def fetch(base,symbol,res):
    u=BASES[base]+"/v2/history/candles?"+urllib.parse.urlencode(
        {"symbol":symbol,"resolution":res,"start":START,"end":END-1})
    request=urllib.request.Request(u,headers={"Accept":"application/json","User-Agent":"BTC-Analysis-testnet-signal-audit"})
    with urllib.request.urlopen(request,timeout=45) as response:
        d=json.load(response)
    if d.get("success") is not True or not isinstance(d.get("result"),list):
        raise RuntimeError("bad candle response "+str(d)[:400])
    a=pd.DataFrame(d["result"])
    if len(a)<105: raise RuntimeError(f"Only {len(a)} bars from {u}")
    a=a[["time","open","high","low","close","volume"]].copy()
    for col in a.columns:
        a[col]=pd.to_numeric(a[col],errors="raise")
    a=a.drop_duplicates("time").sort_values("time").reset_index(drop=True)
    bar=900 if res=="15m" else 3600
    assert (a.time.astype("int64").diff().iloc[1:]==bar).all(),f"noncontiguous {res}"
    assert (a.high>=a[["open","close","low"]].max(axis=1)).all()
    assert (a.low<=a[["open","close","high"]].min(axis=1)).all()
    a["dt"]=pd.to_datetime(a.time,unit="s",utc=True)
    # Filter out any partial bar extending beyond IST midnight.
    a=a.loc[a.time+bar<=END].copy().set_index("dt")
    return a

def scan(asset,base,res,profile):
    a=fetch(base,asset+"USD",res)
    f=indicators(a[["open","high","low","close","volume"]])
    found=[]
    for i in range(1,len(f)):
        x=f.iloc[i];prior=f.iloc[i-1]
        if x.name+pd.Timedelta(minutes=15 if res=="15m" else 60)>DAY_END.tz_convert("UTC"):continue
        entry_time=x.name+pd.Timedelta(minutes=15 if res=="15m" else 60)
        if not (DAY_START<=entry_time.tz_convert(TZ)<DAY_END):continue
        if not all(np.isfinite(float(x[k])) for k in ("ema","atr14","atr_ratio","volume_ratio")):continue
        gate=(x.atr_ratio>=1.0 and x.volume_ratio>=1.5) if profile=="legacy_15m" else True
        if not gate:continue
        direction=int(x["dir"])
        side=("buy" if direction==int(prior["dir"])==-1 and x.low<=x.ema and x.close>x.ema
              else "sell" if direction==int(prior["dir"])==1 and x.high>=x.ema and x.close<x.ema
              else None)
        if side:
            found.append({
                "entry_ist":entry_time.tz_convert(TZ).isoformat(),
                "side":side,"signal_close":round(float(x.close),3),
                "signal_ema20":round(float(x.ema),3),
                "atr_ratio":round(float(x.atr_ratio),3),
                "volume_ratio":round(float(x.volume_ratio),3),
            })
    # Persist price candles, so source can be compared with user.
    a.to_csv(OUT/f"{base}_{asset}_{res}_candles.csv.gz",compression="gzip")
    return {
        "source":BASES[base], "instrument":asset+"USD", "resolution":res,
        "first_utc":str(a.index[0]),"last_utc":str(a.index[-1]),
        "first_close":float(a.close.iloc[0]),"last_close":float(a.close.iloc[-1]),
        "signal_count_on_20nov_ist":len(found),"signals":found,
        "caveat":"Signals only: ignores actual VPS mode/config, previous position, API failures, order/paper status, or exchange account fills."
    }

def main():
    output={"date_ist":"2026-11-20","source_warning":"Production and Delta Demo testnet candles may differ; public signals are not executed trades", "results":{}}
    for host in BASES:
        for asset in ("BTC","ETH"):
            for res,profile in (("15m","legacy_15m"),("1h","ema20_st_1h_100_50")):
                label=f"{host}_{asset.lower()}_{res}"
                try:
                    output["results"][label]=scan(asset,host,res,profile)
                    print("AUDIT",label,json.dumps(output["results"][label]),flush=True)
                except Exception as e:
                    output["results"][label]={"error":f"{type(e).__name__}: {e}"}
                    print("AUDIT_ERROR",label,str(e),flush=True)
    (OUT/"summary.json").write_text(json.dumps(output,indent=2)+"\n",encoding="utf-8")
    if not any("signals" in v for k,v in output["results"].items() if k.startswith("demo_testnet")):
        print("NO_USABLE_TESTNET_HISTORY: do not claim demo signal parity", flush=True)
    print("DONE",OUT,flush=True)

if __name__=="__main__":
    main()
