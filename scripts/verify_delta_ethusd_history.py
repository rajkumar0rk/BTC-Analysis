#!/usr/bin/env python3
"""Verify ETHUSD monthly source archives without fabricating missing observations."""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("data/delta_india/ETHUSD")
FREQ = {"mark_1m": 60, "open_interest_5m": 300, "funding_1h": 3600}

def timestamp(value: str) -> int:
    return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp())

def inspect_gzip(path: Path, period_start: int, period_end: int, step: int):
    total, first, last, prev = 0, None, None, None
    with gzip.open(path, "rt", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        expected_fields = {"time", "open", "high", "low", "close", "volume"}
        if not expected_fields.issubset(reader.fieldnames or []):
            raise ValueError(f"{path}: missing required columns")
        for r in reader:
            t = int(r["time"])
            if t < period_start or t >= period_end or t % step:
                raise ValueError(f"{path}: timestamp out of range / alignment: {t}")
            if prev is not None and t <= prev:
                raise ValueError(f"{path}: duplicated or unordered timestamp {t}")
            for k in ("open", "high", "low", "close"):
                float(r[k])
            total += 1
            first = t if first is None else first
            last = t
            prev = t
    return {"observed": total, "first": first, "last": last, "expected": (period_end-period_start)//step,
            "missing": (period_end-period_start)//step-total}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--output", default="reports/ethusd_data_quality/summary.json")
    args = ap.parse_args()
    root=Path(args.root)
    price_manifest=root/"1m"/"manifest.json"
    history_manifest=root/"institutional"/"history_manifest.json"
    if not price_manifest.exists():
        raise SystemExit("No ETHUSD 1m manifest: download price history first")
    data=json.loads(price_manifest.read_text())
    if data.get("symbol")!="ETHUSD":
        raise SystemExit("Unexpected price symbol")
    result={"exchange":"Delta Exchange India","instrument":"ETHUSD","price":{},"institutional":{},
            "caveats":["OHLCV is not bid/ask order flow",
                       "FUNDING:ETHUSD historical rate candles are not a ledger of settled cash funding transfers",
                       "Open interest and mark candles are not trade executions"],
            "checked_utc":datetime.now(timezone.utc).isoformat()}
    records=[]
    for part in data["partitions"]:
        path=root/"1m"/part["file"]
        if not path.exists():
            raise FileNotFoundError(path)
        sha=hashlib.sha256(path.read_bytes()).hexdigest()
        if sha!=part["sha256_gzip"]:
            raise ValueError(f"SHA-256 differs: {path}")
        a=timestamp(part["utc_start"])
        b=timestamp(part["utc_end_exclusive"])
        inspected=inspect_gzip(path,a,b,60)
        if inspected["observed"]!=part["observed_candles"] or inspected["expected"]!=part["expected_minutes"]:
            raise ValueError(f"Manifest row/count mismatch: {path}")
        records.append({"file":part["file"],"checksum_valid":True,**inspected})
    result["price"]={"files":len(records),"observed":sum(x["observed"] for x in records),
                     "expected":sum(x["expected"] for x in records),
                     "missing":sum(x["missing"] for x in records),"monthly":records,
                     "complete_calendar_months":[]}
    # The completeness list above means complete within the requested partition range;
    # November and other partial boundary months must not be counted as complete calendar months.
    complete=[]
    for part, row in zip(data["partitions"], records):
        begin=datetime.fromtimestamp(timestamp(part["utc_start"]),timezone.utc)
        stop=datetime.fromtimestamp(timestamp(part["utc_end_exclusive"]),timezone.utc)
        last_day=(begin.year+(begin.month==12), begin.month%12+1,1)
        if begin.day==1 and begin.hour==0 and begin.minute==0 and (stop.year,stop.month,stop.day)==last_day and row["missing"]==0:
            complete.append(part["file"][:7])
    result["price"]["complete_calendar_months"]=complete
    result["price"]["missing_months"]=[x["file"][:7] for x in records if x["missing"]]
    if history_manifest.exists():
        other=json.loads(history_manifest.read_text())
        if other.get("symbol")!="ETHUSD":
            raise ValueError("Unexpected institutional symbol")
        for name,entry in other.get("series",{}).items():
            freq=FREQ[name]
            total=0
            for part in entry["partitions"]:
                path=Path(part["partition"])
                if not path.exists():
                    path=root/"institutional"/"history"/name/(Path(part["partition"]).name)
                ym=path.name[:7]
                y,m=map(int,ym.split("-"))
                a=int(datetime(y,m,1,tzinfo=timezone.utc).timestamp())
                ny,nm=y+(m==12),m%12+1
                b=int(datetime(ny,nm,1,tzinfo=timezone.utc).timestamp())
                inspect=inspect_gzip(path,a,b,freq)
                if inspect["observed"]!=part["rows"]:
                    raise ValueError(f"Historical series mismatch: {path}")
                total+=inspect["observed"]
            if total!=entry["rows_saved"]:
                raise ValueError(f"{name}: series total differs")
            result["institutional"][name]={"rows":total,"files":len(entry["partitions"]),
                                            "source_symbol":entry["native_source_symbol"],
                                            "note":entry["note"]}
    dest=Path(args.output)
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,indent=2)+"\n")
    print("ETHUSD_DATA_AUDIT",json.dumps({"price_files":result["price"]["files"],
           "price_rows":result["price"]["observed"],"missing":result["price"]["missing"],
           "calendar_months":len(complete),"institutional":list(result["institutional"])}),flush=True)

if __name__=="__main__":main()
