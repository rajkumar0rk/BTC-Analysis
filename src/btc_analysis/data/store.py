"""Manifest-verified Delta OHLCV ingestion and bounded Parquet streaming.

Storage is content-addressed; ingestion never alters the source repository.
A manifest is atomically published only after every partition passes validation.
Unverified candle labels require explicit opt-in before time-causal access.
"""
from __future__ import annotations
import csv
import gzip
import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from collections import OrderedDict
from dataclasses import dataclass

import pyarrow as pa
import pyarrow.parquet as pq

from ..contracts import Candle, DatasetRef, Instrument, Timeframe, DataKind
from ..serialization import fingerprint
from .calendar import Calendar, ContinuousCalendar, grid

SOURCE = "https://api.india.delta.exchange/v2/history/candles"
COLS = ("time", "open", "high", "low", "close", "volume")
VALUE_TYPE = pa.decimal128(38, 18)
SCHEMA = pa.schema([("time", pa.int64()), *[(k, VALUE_TYPE) for k in COLS[1:]]])
SCHEMA_VERSION = 1
STEP = 60
BATCH = 4096
MAX_QUERY_ROWS = 100_000
MONTH_FILE = re.compile(r"\d{4}-(?:0[1-9]|1[0-2])\.csv\.gz")
SHA = re.compile(r"[a-f0-9]{64}")


class CoverageError(ValueError):
    pass


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as src:
        for part in iter(lambda: src.read(1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()


def iso_epoch(s: str) -> int:
    t = datetime.fromisoformat(s.replace("Z", "+00:00"))
    if t.tzinfo is None or t.utcoffset().total_seconds() != 0 or t.microsecond:
        raise ValueError("manifest timestamps must be whole UTC seconds")
    return int(t.timestamp())


def dt(t: int) -> datetime:
    return datetime.fromtimestamp(t, timezone.utc)


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".manifest-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(value, f, sort_keys=True, separators=(",", ":"), allow_nan=False)
            f.write("\n")
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def check_hash(v):
    if not isinstance(v, str) or SHA.fullmatch(v) is None:
        raise ValueError("bad SHA256")
    return v


def decimal_value(s):
    try:
        value = Decimal(s)
    except (InvalidOperation, TypeError) as exc:
        raise ValueError("invalid decimal") from exc
    if not value.is_finite():
        raise ValueError("non-finite decimal")
    # Decimal128 scale fixed; reject unrepresentable data rather than round.
    if value and (value.adjusted() >= 20 or
                  (value.as_tuple().exponent < -18 and any(value.as_tuple().digits[
                      value.as_tuple().exponent + 18:]))):
        raise ValueError("source exceeds exact decimal128(38,18) storage")
    return value


def read_csv_rows(path, start, end):
    """Yield exact decimal values; duplicates, ordering and boundary errors are fatal."""
    prev = start - STEP
    with gzip.open(path, "rt", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if tuple(reader.fieldnames or ()) != COLS:
            raise ValueError(f"unexpected CSV schema {path.name}")
        for row in reader:
            if None in row or any(row[k] is None for k in COLS):
                raise ValueError("malformed CSV row")
            if not re.fullmatch(r"\d+", row["time"]):
                raise ValueError("noninteger timestamp")
            t = int(row["time"])
            if t % STEP or not start <= t < end or t <= prev:
                raise ValueError(f"duplicate, unsorted, off-grid or out-of-range time: {t}")
            o, h, l, c, v = (decimal_value(row[k]) for k in COLS[1:])
            if not (0 < l <= min(o, c) <= max(o, c) <= h and v >= 0):
                raise ValueError(f"invalid OHLCV at {t}")
            prev = t
            yield (t, o, h, l, c, v)


def _batch(rows):
    return pa.RecordBatch.from_arrays(
        [pa.array([r[i] for r in rows], type=field.type)
         for i, field in enumerate(SCHEMA)], schema=SCHEMA)


def build_partition(source, dest, start, end):
    """One partition at a time; bounded memory independent of full history size."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    fd, tmpname = tempfile.mkstemp(prefix=".partition-", suffix=".parquet", dir=dest.parent)
    os.close(fd)
    tmp = Path(tmpname)
    gaps, rows, count = [], [], 0
    expected = start
    try:
        with pq.ParquetWriter(tmp, SCHEMA, compression="zstd", write_statistics=True) as writer:
            for row in read_csv_rows(source, start, end):
                if row[0] > expected:
                    gaps.append([expected, row[0]])
                expected = row[0] + STEP
                count += 1
                rows.append(row)
                if len(rows) >= BATCH:
                    writer.write_batch(_batch(rows))
                    rows.clear()
            if rows:
                writer.write_batch(_batch(rows))
        if expected < end:
            gaps.append([expected, end])
        if not count:
            raise ValueError("empty source partition")
        result = dict(rows=count, gaps=gaps, parquet_sha256=sha_file(tmp))
        os.replace(tmp, dest)
        return result
    finally:
        tmp.unlink(missing_ok=True)


def ingest_delta(source_dir: Path, store_dir: Path, symbol: str, *,
                 timestamp_label: str = "unverified", label_evidence: str = "",
                 label_verified: bool = False) -> dict:
    """Import documented source manifests. Label attestation is explicit, not inferred.
    Raw timestamps are preserved; closed-label conversion is not enabled in v1.
    """
    if symbol not in ("BTCUSD", "ETHUSD"):
        raise ValueError("unsupported Delta v1 symbol")
    if timestamp_label not in ("unverified", "open"):
        raise ValueError("unsupported timestamp convention")
    if type(label_verified) is not bool or (label_verified and
            (timestamp_label != "open" or not label_evidence.strip())):
        raise ValueError("verified label needs open convention and external evidence")
    source_dir, store_dir = Path(source_dir), Path(store_dir)
    raw = json.loads((source_dir / "manifest.json").read_text())
    if (raw.get("source") != SOURCE or raw.get("symbol") != symbol
            or raw.get("resolution") != "1m" or raw.get("timestamp_unit") != "unix_seconds_utc"):
        raise ValueError("unexpected source provenance")
    dest = store_dir / "delta_india" / symbol / "1m"
    pointer = dest / "latest.json"
    prior = {}
    if pointer.exists():
        try:
            previous = load_manifest(dest, json.loads(pointer.read_text())["manifest_sha256"])
            prior = {p["source_sha256"]: p for p in previous["partitions"]}
        except (ValueError, OSError, KeyError):
            prior = {}  # never trust corrupted cache metadata
    entries = raw["partitions"]
    if not isinstance(entries, list) or not entries:
        raise ValueError("missing manifest partitions")
    entries = sorted(entries, key=lambda x: x["utc_start"])
    parts, seen = [], set()
    last = None
    for e in entries:
        filename = e["file"]
        if MONTH_FILE.fullmatch(filename) is None or filename in seen:
            raise ValueError("invalid or repeated source partition name")
        seen.add(filename)
        a, b = iso_epoch(e["utc_start"]), iso_epoch(e["utc_end_exclusive"])
        grid(a, b, STEP)
        if (dt(a).strftime("%Y-%m") != filename[:7] or
                dt(b - STEP).strftime("%Y-%m") != filename[:7] or
                (last is not None and a < last)):
            raise ValueError("overlapping or mispartitioned source")
        last = b
        digest = check_hash(e["sha256_gzip"])
        path = source_dir / filename
        if sha_file(path) != digest:
            raise ValueError(f"source checksum mismatch {filename}")
        obj = dest / "objects" / (digest + ".parquet")
        old = prior.get(digest)
        if (old and old["start"] == a and old["end"] == b and obj.exists()
                and sha_file(obj) == old["parquet_sha256"]):
            result = {k: old[k] for k in ("rows", "gaps", "parquet_sha256")}
        else:
            result = build_partition(path, obj, a, b)
        expected = (b-a)//STEP
        missing = sum((y-x)//STEP for x,y in result["gaps"])
        if (expected != e["expected_minutes"] or result["rows"] != e["observed_candles"]
                or missing != e["missing_minutes"] or missing + result["rows"] != expected):
            raise ValueError(f"manifest counts disagree with source {filename}")
        parts.append(dict(file=filename, source_sha256=digest, start=a, end=b, **result))
    extras = {p.name for p in source_dir.glob("*.csv.gz")} - seen
    if extras:
        raise ValueError("unmanifested source partitions: " + ", ".join(sorted(extras)))
    manifest = dict(schema=SCHEMA_VERSION, venue="delta_india", symbol=symbol,
                    kind="ohlcv", step=STEP, source=SOURCE,
                    source_manifest_sha256=sha_file(source_dir/"manifest.json"),
                    timestamp_label=timestamp_label, label_verified=label_verified,
                    label_evidence=label_evidence, raw_timestamp_label=raw.get("timestamp_label"),
                    start=parts[0]["start"], end=parts[-1]["end"], partitions=parts)
    key = fingerprint(manifest)
    target = dest / "manifests" / (key + ".json")
    if not target.exists():
        atomic_json(target, manifest)
    if load_manifest(dest, key) != manifest:
        raise ValueError("manifest integrity failure")
    atomic_json(pointer, {"schema": SCHEMA_VERSION, "manifest_sha256": key})
    return {**manifest, "manifest_sha256": key}


def load_manifest(root, key):
    check_hash(key)
    value = json.loads((root/"manifests"/(key+".json")).read_text())
    if value.get("schema") != SCHEMA_VERSION or fingerprint(value) != key:
        raise ValueError("manifest integrity failure")
    return value


@dataclass(frozen=True, slots=True)
class Coverage:
    start: int
    end: int
    expected_rows: int
    observed_rows: int
    gaps: tuple[tuple[int, int], ...]
    calendar_id: str

    @property
    def missing_rows(self):
        return self.expected_rows - self.observed_rows

    @property
    def complete(self):
        return not self.gaps


class HistoryStore:
    """Pinned snapshot reader. No automatic switch to newer data mid-backtest.
    Cache holds at most cache_partitions validated Parquet handles, not entire arrays.
    """
    def __init__(self, root: Path, symbol: str, manifest_sha256=None, *, cache_partitions=2):
        if symbol not in ("BTCUSD", "ETHUSD") or type(cache_partitions) is not int or not 0 <= cache_partitions <= 8:
            raise ValueError("invalid symbol or cache size")
        self.root = Path(root)/"delta_india"/symbol/"1m"
        self.key = manifest_sha256 or json.loads((self.root/"latest.json").read_text())["manifest_sha256"]
        self.manifest = load_manifest(self.root, self.key)
        if self.manifest["symbol"] != symbol or self.manifest["step"] != STEP:
            raise ValueError("manifest identity mismatch")
        self.cache_size = cache_partitions
        self.cache = OrderedDict()

    def _open(self, p):
        key = check_hash(p["source_sha256"])
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        path = self.root/"objects"/(key+".parquet")
        if sha_file(path) != p["parquet_sha256"]:
            raise ValueError("derived partition checksum mismatch")
        f = pq.ParquetFile(path)
        if not f.schema_arrow.equals(SCHEMA) or f.metadata.num_rows != p["rows"]:
            raise ValueError("derived partition schema/count mismatch")
        if self.cache_size:
            self.cache[key] = f
            if len(self.cache) > self.cache_size:
                _, old = self.cache.popitem(last=False)
                old.close()
        return f

    def close(self):
        for f in self.cache.values():
            f.close()
        self.cache.clear()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def coverage(self, start, end, calendar: Calendar | None = None):
        calendar = calendar or ContinuousCalendar()
        windows = calendar.intervals(start, end, STEP)
        # Invert actual partition ranges minus recorded internal gaps.
        present = []
        for p in self.manifest["partitions"]:
            cursor = p["start"]
            for a,b in p["gaps"]:
                if cursor < a:
                    present.append((cursor,a))
                cursor = b
            if cursor < p["end"]:
                present.append((cursor,p["end"]))
        gaps, expected = [], 0
        for a,b in windows:
            expected += (b-a)//STEP
            cursor = a
            for x,y in present:
                if y <= cursor:
                    continue
                if x >= b:
                    break
                if x > cursor:
                    gaps.append((cursor,min(x,b)))
                cursor = max(cursor,min(y,b))
                if cursor >= b:
                    break
            if cursor < b:
                gaps.append((cursor,b))
        missing = sum((b-a)//STEP for a,b in gaps)
        return Coverage(start,end,expected,expected-missing,tuple(gaps),calendar.calendar_id)

    def _label(self, assume_open):
        if not (self.manifest["timestamp_label"] == "open" and self.manifest["label_verified"]):
            if assume_open is not True:
                raise CoverageError("candle timestamp label not verified; explicitly assume_open for research only")

    def iter_batches(self, start, end, *, strict=True, batch_size=BATCH, calendar=None,
                     assume_open=False):
        self._label(assume_open)
        grid(start,end,STEP)
        if type(batch_size) is not int or not 1 <= batch_size <= BATCH:
            raise ValueError("batch size outside bound")
        cal = calendar or ContinuousCalendar()
        cov = self.coverage(start,end,cal)
        if strict and not cov.complete:
            raise CoverageError(f"{cov.missing_rows} missing expected candles")
        import pyarrow.compute as pc
        for p in self.manifest["partitions"]:
            if p["end"] <= start or p["start"] >= end:
                continue
            f = self._open(p)
            try:
                windows = cal.intervals(max(start,p["start"]),min(end,p["end"]),STEP)
                if not windows:
                    continue
                # Row-group pruning using min/max statistics.
                for i in range(f.num_row_groups):
                    stats = f.metadata.row_group(i).column(0).statistics
                    if stats and not any(stats.min < b and stats.max >= a for a,b in windows):
                        continue
                    for batch in f.iter_batches(batch_size=batch_size,row_groups=[i]):
                        times = batch.column(0)
                        keep = None
                        for a,b in windows:
                            mask = pc.and_(pc.greater_equal(times,a),pc.less(times,b))
                            keep = mask if keep is None else pc.or_(keep,mask)
                        cut = batch.filter(keep)
                        if cut.num_rows:
                            yield cut
            finally:
                if not self.cache_size:
                    f.close()

    def iter_candles(self, instrument: Instrument, start, end, *, as_of=None, **kwargs):
        if instrument.venue != self.manifest["venue"] or instrument.symbol != self.manifest["symbol"]:
            raise ValueError("instrument mismatch")
        # Complete bars only at as_of; no future partial candle.
        if as_of is not None:
            if type(as_of) is not int:
                raise ValueError("as_of must be UTC epoch seconds")
            end = min(end,as_of//STEP*STEP)
        if end <= start:
            return
        for batch in self.iter_batches(start,end,**kwargs):
            for row in batch.to_pylist():
                t = row.pop("time")
                yield Candle(instrument,Timeframe(STEP),dt(t),dt(t+STEP),**row)

    def query(self, start, end, **kwargs):
        """Bounded convenience materialization; use iter_batches for multi-year history."""
        grid(start,end,STEP)
        if (end-start)//STEP > MAX_QUERY_ROWS:
            raise ValueError("query too large; use streaming iterator")
        return pa.Table.from_batches(list(self.iter_batches(start,end,**kwargs)),schema=SCHEMA)

    def dataset_ref(self,instrument,start,end,calendar=None):
        """Only independently attested open labels can issue strict M1 coverage refs."""
        self._label(False)
        if instrument.venue != self.manifest["venue"] or instrument.symbol != self.manifest["symbol"]:
            raise ValueError("instrument mismatch")
        cov = self.coverage(start,end,calendar)
        # Verify all relevant partition checksums before attesting.
        for p in self.manifest["partitions"]:
            if p["start"] < end and p["end"] > start:
                f = self._open(p)
                if not self.cache_size:
                    f.close()
        return DatasetRef(f"{instrument.symbol}:1m:{self.key[:16]}:{start}:{end}",instrument,
                          DataKind.OHLCV,Timeframe(STEP),dt(start),dt(end),self.key,
                          SOURCE,cov.missing_rows,True)
