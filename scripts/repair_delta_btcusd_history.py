#!/usr/bin/env python3
"""Repair BTCUSD futures gaps and extend mark/OI/funding, without touching analyses.

Read archived monthly partitions, request ONLY absent Delta candles, validate each
timestamp and OHLCV row, then update monthly manifests. Historical mark/OI/funding
rates are observations, NOT realized settlement cashflows.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import sync_delta_btcusd_1m as price
import collect_delta_institutional_data as institution

ROOT = Path("data/delta_india/BTCUSD")
UTC = timezone.utc
OCT = date(2026, 10, 1)

def utc_start(day: date) -> int:
    return price.unix_day(day)

def next_month(day: date) -> date:
    return price.next_month(day)

def repair_price(through: date):
    manifest_path = ROOT / "1m" / "manifest.json"
    existing = json.loads(manifest_path.read_text())
    if existing["symbol"] != "BTCUSD":
        raise RuntimeError("Incorrect price symbol")
    prior = {p["file"]: p for p in existing["partitions"]}
    first_day = OCT
    while first_day <= through:
        stop_day = next_month(first_day)
        begin, end = utc_start(first_day), min(utc_start(stop_day), utc_start(through + timedelta(days=1)))
        filename = f"{first_day.year}-{first_day.month:02d}.csv.gz"
        path = ROOT / "1m" / filename
        rows = price.load_month(path, begin, end) if path.exists() else {}
        missing_before = (end - begin) // 60 - len(rows)
        if missing_before < 0:
            raise RuntimeError(f"Duplicate rows or invalid dates in {filename}")
        requests = 0
        # Skip complete 1200-minute slices instead of downloading the whole archive.
        for lo in range(begin, end, price.WINDOW * 60):
            hi = min(end - 60, lo + (price.WINDOW - 1) * 60)
            if all(t in rows for t in range(lo, hi + 60, 60)):
                continue
            candles = price.read_window(lo, hi)
            requests += 1
            for c in candles:
                t = price.validate_bar(c)
                if lo <= t <= hi and t not in rows:
                    rows[t] = {k: c[k] for k in price.COLUMNS}
        expected = (end - begin) // 60
        missing_after = expected - len(rows)
        if missing_after:
            raise RuntimeError(f"{filename} still missing {missing_after}/{expected} 1m candles")
        if missing_before or not path.exists():
            sha = price.write_month(path, rows)
        else:
            sha = hashlib.sha256(path.read_bytes()).hexdigest()
        prior[filename] = {
            "file": filename,
            "utc_start": datetime.fromtimestamp(begin, UTC).isoformat(),
            "utc_end_exclusive": datetime.fromtimestamp(end, UTC).isoformat(),
            "expected_minutes": expected,
            "observed_candles": len(rows),
            "missing_minutes": missing_after,
            "sha256_gzip": sha,
        }
        print("BTCUSD_1M", json.dumps({
            "month": filename[:7], "expected": expected, "observed": len(rows),
            "missing_before": missing_before, "missing_after": missing_after,
            "api_requests": requests, "sha256": sha,
        }), flush=True)
        first_day = stop_day
    existing["requested_through_utc"] = through.isoformat()
    existing["generated_at_utc"] = datetime.now(UTC).isoformat()
    existing["partitions"] = [prior[k] for k in sorted(prior) if prior[k]["utc_start"] < datetime.fromtimestamp(utc_start(through+timedelta(days=1)), UTC).isoformat()]
    # Verify every advertised price partition's SHA, continuity, and count.
    for p in existing["partitions"]:
        file = ROOT / "1m" / p["file"]
        sha = hashlib.sha256(file.read_bytes()).hexdigest()
        if sha != p["sha256_gzip"]:
            raise RuntimeError(f"Checksum mismatch: {file}")
        rows = price.load_month(file, int(datetime.fromisoformat(p["utc_start"]).timestamp()), int(datetime.fromisoformat(p["utc_end_exclusive"]).timestamp()))
        if len(rows) != p["observed_candles"]:
            raise RuntimeError(f"Manifest count mismatch: {file}")
    manifest_path.write_text(json.dumps(existing, indent=2) + "\n")
    print("PRICE_TOTAL", json.dumps({
        "months": len(existing["partitions"]),
        "observed": sum(x["observed_candles"] for x in existing["partitions"]),
        "missing": sum(x["missing_minutes"] for x in existing["partitions"]),
        "through": through.isoformat()
    }), flush=True)
    return existing

def repair_institutional(through: date):
    # The existing collector already fetches only missing windows. Prevent
    # recompressing historical monthly files when their decoded rows did not change.
    original = institution.write_csv_gzip
    def skip_unchanged(path, rows):
        path = Path(path)
        if path.exists():
            existing = institution.read_csv_gzip(path)
            if existing == rows:
                return
        original(path, rows)
    institution.write_csv_gzip = skip_unchanged
    end = datetime.combine(through + timedelta(days=1), datetime.min.time(), tzinfo=UTC)
    out = institution.backfill(end, force=False)
    for name, series in out["series"].items():
        if series["missing_dense_intervals"]:
            raise RuntimeError(f"Missing {name} observations: {series['missing_dense_intervals']}")
        print("BTCUSD_INSTITUTIONAL", json.dumps({
            "series": name, "observed": series["rows_saved"],
            "expected": series["expected_dense_intervals"],
            "missing": series["missing_dense_intervals"],
            "last": series["latest_utc"], "requests": series["api_requests"]
        }), flush=True)
    return out

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--through", help="Last UTC day inclusive; default previous complete UTC day")
    parser.add_argument("--price-only", action="store_true")
    args = parser.parse_args()
    through = date.fromisoformat(args.through) if args.through else (datetime.now(UTC).date() - timedelta(days=1))
    if through < OCT:
        parser.error("--through must include October 2026")
    repair_price(through)
    if not args.price_only:
        repair_institutional(through)
    print("BTCUSD_HISTORY_REPAIR_COMPLETE", through.isoformat(), flush=True)
if __name__ == "__main__":
    main()
