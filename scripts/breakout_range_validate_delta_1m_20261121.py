#!/usr/bin/env python3
"""Read-only verification of authentic Delta India BTCUSD minute archive.

Verifies each gzip against the repository's original compressed SHA256,
timestamp continuity, 1-minute boundaries, no duplicates, OHLC and volume.
Writes evidence to an isolated research report; never repairs missing data.
"""
import csv, gzip, hashlib, io, json
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT=Path("data/delta_india/BTCUSD/1m")
OUT=Path("analysis/breakout_range_20261121/archive_validation_20261121.json")

def utc(s):
    return datetime.fromisoformat(s.replace("Z","+00:00"))

def main():
    manifest=json.loads((ROOT/"manifest.json").read_text())
    assert manifest["exchange"]=="Delta Exchange India"
    assert manifest["symbol"]=="BTCUSD" and manifest["resolution"]=="1m"
    output={"source_manifest":str(ROOT/"manifest.json"),"partitions":[],"pass":False}
    failures=[]
    for p in manifest["partitions"]:
        if not ("2025-01"<=p["file"][:7]<="2026-11"):
            continue
        path=ROOT/p["file"]
        row={"file":p["file"],"manifest_sha256":p["sha256_gzip"]}
        try:
            payload=path.read_bytes()
            digest=hashlib.sha256(payload).hexdigest()
            assert digest==p["sha256_gzip"],"gzip sha256 mismatch"
            raw=gzip.decompress(payload).decode("utf-8")
            reader=csv.DictReader(io.StringIO(raw))
            columns=reader.fieldnames or []
            def key(*options):
                for option in options:
                    if option in columns:return option
                raise ValueError("Missing columns "+repr(options)+": "+repr(columns))
            tkey=key("time","timestamp","start","ts")
            o,h,l,c,v=[key(k) for k in ("open","high","low","close","volume")]
            start=int(utc(p["utc_start"]).timestamp())
            end=int(utc(p["utc_end_exclusive"]).timestamp())
            prev=None
            count=0
            for bar in reader:
                t=int(float(bar[tkey]))
                if t>10**11:t//=1000
                if count==0:assert t==start,"first candle not UTC start"
                if prev is not None:assert t-prev==60,"gap or duplicate minute"
                assert t<end and t%60==0,"bad minute timestamp"
                op,hi,lo,cl,vol=(float(bar[k]) for k in (o,h,l,c,v))
                assert min(op,hi,lo,cl)>0 and vol>=0,"invalid prices/volume"
                assert lo<=min(op,cl)<=max(op,cl)<=hi,"OHLC inconsistency"
                prev=t
                count+=1
            assert prev==end-60,"last candle not UTC end-1m"
            assert count==p["observed_candles"]==p["expected_minutes"],"missing rows"
            row.update(status="PASS",actual_sha256=digest,rows=count)
        except Exception as exc:
            row.update(status="FAIL",reason=str(exc))
            failures.append(p["file"]+": "+str(exc))
        output["partitions"].append(row)
    output["pass"]=not failures and len(output["partitions"])==23
    output["failures"]=failures
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(output,indent=2)+"\n")
    print(json.dumps({"pass":output["pass"],"partition_count":len(output["partitions"]),"failures":failures},indent=2))
    if not output["pass"]:raise SystemExit(1)

if __name__=="__main__":main()
