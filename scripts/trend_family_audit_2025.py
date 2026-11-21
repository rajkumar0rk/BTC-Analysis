#!/usr/bin/env python3
"""Read-only verification of Delta India BTCUSD 2025 1m OHLCV before trend replay."""
from pathlib import Path
import gzip, csv, json, hashlib
from datetime import datetime, timezone, timedelta
ROOT=Path("data/delta_india/BTCUSD/1m")
def run():
    report={"source":"Delta India BTCUSD 1m repository archive","months":[],"errors":[]}
    previous=None
    for month in range(1,13):
        p=ROOT/f"2025-{month:02d}.csv.gz"
        if not p.is_file():
            report["errors"].append(f"Missing {p}");continue
        h=hashlib.sha256(); rows=0; bad=0; missing=0; first=None; last=None
        with p.open("rb") as raw:
            for chunk in iter(lambda:raw.read(1024*1024),b""):h.update(chunk)
        with gzip.open(p,"rt",newline="") as f:
            reader=csv.DictReader(f)
            required={"time","open","high","low","close","volume"}
            if not required.issubset(set(reader.fieldnames or [])):
                report["errors"].append(f"{p}: missing required headers");continue
            for row in reader:
                rows+=1
                try:
                    ts=int(row["time"])
                    o,hi,lo,c,v=(float(row[k]) for k in ("open","high","low","close","volume"))
                    if not (lo<=min(o,c)<=max(o,c)<=hi and v>=0 and lo>0):
                        bad+=1
                    if previous is not None:
                        if ts<=previous: bad+=1
                        elif ts-previous!=60: missing+=(ts-previous)//60-1
                    if first is None:first=ts
                    last=ts;previous=ts
                except (ValueError,TypeError,KeyError):
                    bad+=1
        start=int(datetime(2025,month,1,tzinfo=timezone.utc).timestamp())
        nextmonth=datetime(2026,1,1,tzinfo=timezone.utc) if month==12 else datetime(2025,month+1,1,tzinfo=timezone.utc)
        expected=int((nextmonth-datetime(2025,month,1,tzinfo=timezone.utc)).total_seconds()/60)
        record={"file":str(p),"sha256_gzip":h.hexdigest(),"rows":rows,"expected_rows":expected,"first_utc":first,"last_utc":last,"bad_rows_or_order":bad,"missing_minutes":missing,"starts_at_expected_utc":first==start,"ends_at_expected_utc":last==int(nextmonth.timestamp())-60}
        report["months"].append(record)
        if rows!=expected or bad or missing or not record["starts_at_expected_utc"] or not record["ends_at_expected_utc"]:
            report["errors"].append(f"{p}: failed row/time/OHLC checks")
    report["ok"]=not report["errors"] and len(report["months"])==12
    report["total_rows"]=sum(x["rows"] for x in report["months"])
    out=Path("analysis/trend_following_family_20261121/data_audit_2025.json")
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({"ok":report["ok"],"total_rows":report["total_rows"],"errors":report["errors"]},indent=2))
    if not report["ok"]:raise SystemExit(1)
if __name__=="__main__":run()
