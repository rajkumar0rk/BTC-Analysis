#!/usr/bin/env python3
"""Download genuine Delta Exchange India ETHUSD 1m futures candles, by UTC month.

Public API, no API key. Does not synthesize missing candles.
Run: python scripts/sync_delta_btcusd_1m.py --start 2025-01-01
"""
import argparse
import csv
import gzip
import hashlib
import io
import json
import math
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

BASE = "https://api.india.delta.exchange/v2/history/candles"
HEADERS = {"Accept": "application/json", "User-Agent": "BTC-Analysis-research/1.0"}
COLUMNS = ("time", "open", "high", "low", "close", "volume")
UTC = timezone.utc
WINDOW = 1200  # below the documented 2,000-candle maximum


def unix_day(day: date) -> int:
    return int(datetime(day.year, day.month, day.day, tzinfo=UTC).timestamp())


def next_month(day: date) -> date:
    return date(day.year + (day.month == 12), day.month % 12 + 1, 1)


def read_window(start: int, end_inclusive: int):
    params = urllib.parse.urlencode({
        "symbol": "ETHUSD", "resolution": "1m",
        "start": start, "end": end_inclusive,
    })
    url = BASE + "?" + params
    last_error = None
    for attempt in range(8):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=35) as response:
                payload = json.load(response)
            if not isinstance(payload, dict) or not payload.get("success") or not isinstance(payload.get("result"), list):
                raise ValueError("Invalid Delta response: " + str(payload)[:300])
            return payload["result"]
        except urllib.error.HTTPError as exc:
            if exc.code not in (429, 500, 502, 503, 504):
                raise
            reset = exc.headers.get("X-RATE-LIMIT-RESET")
            wait = 2 ** attempt
            if exc.code == 429 and reset:
                try:
                    wait = max(wait, min(90, float(reset) / 1000 + 1))
                except ValueError:
                    pass
            last_error = exc
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            last_error = exc
            wait = min(60, 2 ** attempt)
        if attempt < 7:
            print(f"Retry {attempt + 1}/7 after {wait:.1f}s: {last_error}", flush=True)
            time.sleep(wait)
    raise RuntimeError(f"Delta API failed for {start}..{end_inclusive}: {last_error}")


def validate_bar(bar: dict) -> int:
    stamp = int(bar["time"])
    if stamp % 60:
        raise ValueError(f"Non-minute candle timestamp: {stamp}")
    o, h, l, c, v = (float(bar[k]) for k in COLUMNS[1:])
    if not all(math.isfinite(x) for x in (o, h, l, c, v)):
        raise ValueError(f"Non-finite OHLCV at {stamp}")
    if l <= 0 or min(o, c) < l - 1e-7 or max(o, c) > h + 1e-7 or v < 0:
        raise ValueError(f"Invalid OHLCV at {stamp}: {bar}")
    return stamp


def fetch_month(start: int, stop: int) -> dict:
    rows = {}
    for lo in range(start, stop, WINDOW * 60):
        hi = min(stop - 60, lo + (WINDOW - 1) * 60)
        for bar in read_window(lo, hi):
            stamp = validate_bar(bar)
            if start <= stamp < stop and stamp <= hi:
                rows[stamp] = {k: bar[k] for k in COLUMNS}
        time.sleep(0.12)
    return rows


def write_month(path: Path, rows: dict) -> str:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=COLUMNS, lineterminator="\n")
    writer.writeheader()
    for stamp in sorted(rows):
        writer.writerow(rows[stamp])
    raw = output.getvalue().encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    with open(temp, "wb") as f:
        with gzip.GzipFile(filename="", mode="wb", fileobj=f, mtime=0, compresslevel=6) as compressed:
            compressed.write(raw)
    os.replace(temp, path)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_month(path: Path, start: int, stop: int):
    rows = {}
    with gzip.open(path, "rt", newline="") as f:
        for bar in csv.DictReader(f):
            stamp = validate_bar(bar)
            if start <= stamp < stop:
                rows[stamp] = bar
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="2025-01-01", help="First UTC day, YYYY-MM-DD")
    parser.add_argument("--through", help="Last UTC day (inclusive); default yesterday UTC")
    parser.add_argument("--force", action="store_true", help="Redownload completed months")
    parser.add_argument("--output-dir", default="data/delta_india/ETHUSD/1m")
    args = parser.parse_args()
    start_day = date.fromisoformat(args.start)
    through = date.fromisoformat(args.through) if args.through else datetime.now(UTC).date() - timedelta(days=1)
    if start_day > through:
        parser.error("Start day is later than final UTC day")
    stop_all = unix_day(through + timedelta(days=1))
    output_dir = Path(args.output_dir)
    entries = []
    cursor = date(start_day.year, start_day.month, 1)
    while unix_day(cursor) < stop_all:
        next_day = next_month(cursor)
        lo = max(unix_day(start_day), unix_day(cursor))
        hi = min(unix_day(next_day), stop_all)
        path = output_dir / f"{cursor.year}-{cursor.month:02d}.csv.gz"
        is_closed_month = hi == unix_day(next_day)
        if path.exists() and is_closed_month and not args.force and lo == unix_day(cursor):
            rows = load_month(path, lo, hi)
            source = "existing verified month"
            sha = hashlib.sha256(path.read_bytes()).hexdigest()
        else:
            print(f"Downloading {cursor:%Y-%m} UTC: {datetime.fromtimestamp(lo, UTC)} to {datetime.fromtimestamp(hi, UTC)} (exclusive)", flush=True)
            rows = fetch_month(lo, hi)
            source = "Delta Exchange India public API"
            sha = write_month(path, rows)
        expected = (hi - lo) // 60
        missing = expected - len(rows)
        if not rows:
            raise RuntimeError(f"No candles returned for {cursor:%Y-%m}; refusing to mark month complete")
        if missing > expected * 0.1:
            raise RuntimeError(f"Excessive missing data in {cursor:%Y-%m}: {missing}/{expected} one-minute candles")
        entry = {
            "file": path.name, "utc_start": datetime.fromtimestamp(lo, UTC).isoformat(),
            "utc_end_exclusive": datetime.fromtimestamp(hi, UTC).isoformat(),
            "expected_minutes": expected, "observed_candles": len(rows),
            "missing_minutes": missing, "sha256_gzip": sha,
        }
        entries.append(entry)
        print(f"{cursor:%Y-%m}: {len(rows)}/{expected} candles; missing={missing}; {source}", flush=True)
        cursor = next_day
    manifest = {
        "source": BASE, "exchange": "Delta Exchange India", "symbol": "ETHUSD",
        "instrument": "ETH perpetual futures", "resolution": "1m",
        "timestamp_unit": "unix_seconds_utc", "timestamp_label": "as_returned_by_API",
        "requested_through_utc": through.isoformat(),
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "note": "Missing candles are reported but never fabricated; OHLCV is not bid/ask/order book.",
        "partitions": entries,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    total = sum(e["observed_candles"] for e in entries)
    print(f"SUCCESS: {total:,} real 1m candles in {len(entries)} UTC-month files, through {through}", flush=True)


if __name__ == "__main__":
    main()
