#!/usr/bin/env python3
"""Retrieve genuinely missing early-IST January candles from Delta India.
Read-only public market API. Never fabricate, interpolate or forward-fill.
Writes separately checksummed diagnostic artifact; does not modify market history.
"""
from datetime import datetime,timezone
from pathlib import Path
import hashlib,json,time,urllib.parse,urllib.request
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"analysis/external_github_profit_hunt/january_2025_ist_backfill"
START=int(datetime(2024,12,31,18,30,tzinfo=timezone.utc).timestamp())
END=int(datetime(2025,1,1,0,0,tzinfo=timezone.utc).timestamp())
assert (END-START)//60==330
OUT.mkdir(parents=True,exist_ok=True)
rows={}
for symbol in ("BTCUSD","ETHUSD"):
    query=urllib.parse.urlencode(dict(resolution="1m",symbol=symbol,start=START,end=END))
    url="https://api.india.delta.exchange/v2/history/candles?"+query
    last_error=None
    for attempt in range(4):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"BTCAnalysis-Research/1.0","Accept":"application/json"})
            with urllib.request.urlopen(req,timeout=30) as r:
                payload=json.load(r)
            if not payload.get("success",False):
                raise RuntimeError("API success is false: "+str(payload.get("error")))
            candles=payload.get("result",[])
            assert isinstance(candles,list),type(candles)
            by_time={}
            for item in candles:
                t=int(item["time"])
                if START<=t<END:
                    assert t not in by_time,"duplicate candle"
                    by_time[t]=dict(time=t,open=float(item["open"]),high=float(item["high"]),
                       low=float(item["low"]),close=float(item["close"]),volume=float(item.get("volume",0)))
            expected=set(range(START,END,60))
            assert set(by_time)==expected,("missing",len(expected-set(by_time)),"extra",len(set(by_time)-expected))
            for row in by_time.values():
                assert 0<row["low"]<=row["high"]
                assert row["low"]<=row["open"]<=row["high"]
                assert row["low"]<=row["close"]<=row["high"]
                assert row["volume"]>=0
            df=pd.DataFrame([by_time[t] for t in sorted(by_time)])
            dest=OUT/(symbol+"_2024-12-31T1830Z_2025-01-01T0000Z.csv.gz")
            df.to_csv(dest,index=False,compression="gzip")
            rows[symbol]=dict(symbol=symbol,source=url,candles=len(df),
              first_utc=str(pd.to_datetime(df.time.iloc[0],unit="s",utc=True)),
              last_utc=str(pd.to_datetime(df.time.iloc[-1],unit="s",utc=True)),
              sha256_gzip=hashlib.sha256(dest.read_bytes()).hexdigest(),
              fully_contiguous=True)
            print("BACKFILL_SUCCESS "+json.dumps(rows[symbol]),flush=True)
            break
        except Exception as err:
            last_error=repr(err)
            if attempt<3:time.sleep(2*(attempt+1))
    if symbol not in rows:
        print("BACKFILL_FAILED "+symbol+" "+last_error,flush=True)
        rows[symbol]=dict(symbol=symbol,fully_contiguous=False,error=last_error)
(OUT/"status.json").write_text(json.dumps(rows,indent=2)+"\n")
assert all(x["fully_contiguous"] for x in rows.values()),"Real missing January IST candles NOT verified"
