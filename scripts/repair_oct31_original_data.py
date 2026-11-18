#!/usr/bin/env python3
"""Try to repair the missing 2026-10-31 UTC Delta BTCUSD minute archive.

Never synthesize or interpolate a bar. Leave raw archive unchanged on error.
Run on isolated research branch. Existing historical files not touched.
"""
from pathlib import Path
from datetime import date, datetime, timezone
import hashlib
import json
from sync_delta_btcusd_1m import unix_day, fetch_month, load_month, write_month, validate_bar

ROOT=Path("data/delta_india/BTCUSD/1m")
TARGET=ROOT/"2026-10.csv.gz"
MANIFEST=ROOT/"manifest.json"
START=unix_day(date(2026,10,1))
DAY=unix_day(date(2026,10,31))
END=unix_day(date(2026,11,1))
UTC=timezone.utc

def main():
    existing=load_month(TARGET,START,END)
    expected=set(range(START,END,60))
    oldkeys=set(existing)
    if oldkeys-expected:raise ValueError("Archive contains timestamps outside month")
    missing=sorted(expected-oldkeys)
    if not missing:
        print("October 2026 already complete and timestamp-unique, no changes")
        return
    print("Existing",len(existing),"Missing",len(missing))
    if missing!=list(range(DAY,END,60)):
        raise ValueError("Expected only Oct31 UTC missing; other gaps found")
    fetched=fetch_month(DAY,END)
    print("Authentic Oct31 candles returned",len(fetched))
    if set(fetched)!=set(missing):
        raise RuntimeError(
            f"Delta API Oct31 incomplete. Returned {len(fetched)}/{len(missing)}. "
            "No synthetic fill and no overwrite")
    combined={**existing,**fetched}
    if len(combined)!=44640 or set(combined)!=expected:
        raise RuntimeError("Post-merge October minute completeness failed")
    # Update partition and manifest only after complete, valid recovery.
    manifest=json.loads(MANIFEST.read_text())
    parts=manifest["partitions"]
    item=next((p for p in parts if p["file"]==TARGET.name),None)
    if item is None:raise RuntimeError("Original October manifest entry missing")
    oldsha=hashlib.sha256(TARGET.read_bytes()).hexdigest()
    if oldsha!=item["sha256_gzip"]:
        raise RuntimeError("Original October file hash mismatches manifest")
    newsha=write_month(TARGET,combined)
    item.update({"observed_candles":44640,"missing_minutes":0,"sha256_gzip":newsha})
    manifest["generated_at_utc"]=datetime.now(UTC).isoformat()
    manifest["oct31_repair"]="2026-10-31T00:00Z to 2026-11-01T00:00Z recovered from genuine Delta Exchange India API on isolated research branch"
    MANIFEST.write_text(json.dumps(manifest,indent=2)+"\n")
    print("VALIDATED_OCTOBER_COMPLETE",newsha)

if __name__=="__main__":
    main()
