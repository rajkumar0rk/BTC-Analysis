"""Resume ETH 2024 candidate recovery without replacing any retained source row."""
import argparse
import json
import os
import time
from pathlib import Path

from recover_delta_2024 import BASE, SERIES, equal, fetch, gaps, validate, write_series
from stage_repository_history import month_bounds, source_rows
from validate_recovered_2024 import verify

ROOT = Path(__file__).resolve().parents[1] / "data/delta_india/2024_recovery_candidates"


def retry_rows(symbol, month, kind, seed, round_id, budget=90, request=fetch,
               clock=time.monotonic, pause=time.sleep):
    a, b = month_bounds(month)
    prefix, resolution, step = SERIES[kind]
    rows = dict(seed)
    end = clock() + budget
    errors = []
    conflicts = requests = 0
    # Rotate both request sizes and window order between scheduled runs so
    # unavailable early windows cannot permanently starve later timestamps.
    widths = (1200, 997, 600, 311)
    for pass_id in range(2):
        width = widths[(round_id + pass_id) % len(widths)]
        windows = []
        for lo, hi in gaps(rows, a, b, step):
            for x in range(lo, hi, width * step):
                windows.append((max(a, x - 2 * step),
                                min(b, min(hi, x + width * step) + 2 * step)))
        if not windows or clock() >= end:
            break
        offset = (round_id * 17 + pass_id * 7) % len(windows)
        for lo, hi in windows[offset:] + windows[:offset]:
            if clock() >= end:
                break
            requests += 1
            try:
                observed = {}
                for raw in request(prefix + symbol, resolution, lo, hi):
                    row = validate(raw, kind, step)
                    t = int(row[0])
                    if not lo <= t < hi:
                        continue
                    if t in observed and not equal(observed[t], row):
                        raise ValueError("conflicting response duplicate")
                    observed[t] = row
                for t, row in observed.items():
                    if t in rows:
                        if not equal(rows[t], row):
                            conflicts += 1
                    else:
                        rows[t] = row
            except Exception as exc:
                errors.append({"type": type(exc).__name__,
                               "http_status": getattr(exc, "code", None),
                               "from": lo, "to": hi})
            pause(0.5)
    assert all(rows[t] == row for t, row in seed.items())
    return rows, {"requests": requests, "request_errors": errors,
                  "overlap_conflicts": conflicts}


def run(root, round_id, budget):
    verify(root)
    report = []
    for path in sorted((root / "ETHUSD").glob("2024-*/manifest.json")):
        doc = json.loads(path.read_text())
        if doc["source"] != BASE or doc["funding_is_settlement"] is not False:
            raise ValueError("invalid source provenance")
        month = doc["month"]
        a, b = month_bounds(month)
        changed = False
        for meta in doc["series"]:
            kind = meta["series"]
            step = SERIES[kind][2]
            before = meta["missing"]
            if not before:
                report.append({"month": month, "series": kind, "missing": 0,
                               "new_rows": 0, "requests": 0, "errors": 0})
                continue
            target = path.parent / meta["file"]
            _, data = source_rows(target, meta["sha256"], meta["observed"],
                                  step=step, signed=kind == "funding_1h",
                                  blank_volume=kind != "trade_1m")
            seed = {int(row[0]): row for row in data}
            rows, stats = retry_rows("ETHUSD", month, kind, seed, round_id, budget)
            gained = len(rows) - len(seed)
            remaining = gaps(rows, a, b, step)
            missing = sum((hi - lo) // step for lo, hi in remaining)
            if gained:
                checksum = write_series(target, rows)
                meta.update(observed=len(rows), recovered=len(rows)-meta["seed_rows"],
                            missing=missing, gaps_exclusive=remaining, sha256=checksum,
                            requests=meta["requests"]+stats["requests"],
                            request_errors=stats["request_errors"],
                            overlap_conflicts=meta["overlap_conflicts"]+stats["overlap_conflicts"])
                changed = True
            item = {"month": month, "series": kind, "missing": missing,
                    "new_rows": gained, "requests": stats["requests"],
                    "errors": len(stats["request_errors"]),
                    "overlap_conflicts": stats["overlap_conflicts"]}
            report.append(item)
            print(json.dumps(item), flush=True)
        if changed:
            path.write_text(json.dumps(doc, indent=2) + "\n")
    summary = verify(root)
    coverage = root / "coverage.json"
    if any(row["new_rows"] for row in report):
        coverage.write_text(json.dumps(summary, indent=2) + "\n")
    totals = {kind: sum(x["missing"] for x in report if x["series"] == kind)
              for kind in SERIES}
    result = {"complete": not any(totals.values()), "missing": totals,
              "new_rows": sum(x["new_rows"] for x in report), "partitions": report}
    print(json.dumps(result, indent=2), flush=True)
    if os.getenv("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
            f.write("## ETH 2024 recovery\n\n")
            f.write(f"New genuine rows: {result['new_rows']}\n\n")
            for kind, count in totals.items():
                f.write(f"- {kind}: {count} missing\n")
            f.write("\n" + ("All requested candle intervals present." if result["complete"]
                    else "Incomplete: scheduled retries continue; exchange may not provide old data.") + "\n")
            f.write("\nFunding candles are not actual funding settlements.\n")
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--round", type=int, default=0)
    p.add_argument("--budget", type=int, default=90)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if not 1 <= args.budget <= 120 or args.round < 0:
        p.error("invalid retry budget or round")
    result = run(ROOT, args.round, args.budget)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
