#!/usr/bin/env python3
"""Authentic 2024 December 1m Delta India BTC/ETH prewarm dataset.
No interpolation; source-verified 1m continuity and duplicate detection.
Run in GitHub Actions, publish audit artifact; no changes to primary data.
"""
import json,hashlib,urllib.request,urllib.parse,time
from pathlib import Path
from datetime import datetime,timezone
import pandas as pd
START=int(datetime(2024,12,1,tzinfo=timezone.utc).timestamp())
END=int(datetime(2025,1,1,tzinfo=timezone.utc).timestamp())
OUT=Path("analysis/external_github_profit_hunt/december_2024_warmup")
OUT.mkdir(parents=True,exist_ok=True)
summary={}
for sym in ("BTCUSD","ETHUSD"):
    bars={}
    # Delta candles may impose result caps; request short 6-hour chunks.
    for begin in range(START,END,6*3600):
        stop=min(begin+6*3600,END)
        q=urllib.parse.urlencode(dict(symbol=sym,resolution="1m",start=begin,end=stop))
        url="https://api.india.delta.exchange/v2/history/candles?"+q
        err=None
        for attempt in range(5):
            try:
                req=urllib.request.Request(url,headers={"User-Agent":"BTCAnalysis-Independent-Research/1.0","Accept":"application/json"})
                with urllib.request.urlopen(req,timeout=30) as r: data=json.load(r)
                if not data.get("success"):raise ValueError("Delta API returned non-success: "+str(data.get("error")))
                result=data.get("result")
                if not isinstance(result,list):raise ValueError("Malformed result")
                seen=set()
                for b in result:
                    t=int(b["time"])
                    if t<begin or t>=stop:continue
                    if t in seen:raise ValueError("Duplicate candle within request")
                    seen.add(t)
                    if t in bars:raise ValueError("Duplicate candle across requests")
                    item={k:float(b[k]) for k in ("open","high","low","close")}
                    item["volume"]=float(b.get("volume",0))
                    if not (0<item["low"]<=item["open"]<=item["high"] and item["low"]<=item["close"]<=item["high"] and item["volume"]>=0):
                        raise ValueError("Invalid candle OHLCV")
                    bars[t]=item
                missing=set(range(begin,stop,60))-seen
                if missing:raise ValueError(f"Missing {len(missing)} 1m candles in {begin}-{stop}")
                break
            except Exception as e:
                # Discard partial chunk on retry, to avoid silently retaining incomplete results.
                for t in range(begin,stop,60):bars.pop(t,None)
                err=repr(e)
                if attempt==4:raise RuntimeError(f"{sym} {begin}-{stop} failed: {err}") from e
                time.sleep(min(2**attempt,10))
        if (begin-START)%(24*3600)==0:
            print("PROGRESS",sym,datetime.fromtimestamp(begin,timezone.utc).isoformat(),len(bars),flush=True)
    expected=(END-START)//60
    assert len(bars)==expected,(sym,len(bars),expected)
    ts=sorted(bars)
    assert ts==list(range(START,END,60))
    df=pd.DataFrame([{"time":t,**bars[t]} for t in ts])
    dest=OUT/(sym+"_2024-12-1m.csv.gz")
    df.to_csv(dest,index=False,compression="gzip")
    summary[sym]=dict(source="https://api.india.delta.exchange/v2/history/candles",
       first_utc=datetime.fromtimestamp(ts[0],timezone.utc).isoformat(),
       last_utc=datetime.fromtimestamp(ts[-1],timezone.utc).isoformat(),
       observed=len(df),expected=expected,complete=True,
       sha256=hashlib.sha256(dest.read_bytes()).hexdigest())
    print("WARMUP_COMPLETE",json.dumps({"symbol":sym,**summary[sym]}),flush=True)
(OUT/"manifest.json").write_text(json.dumps(summary,indent=2)+"\n")
