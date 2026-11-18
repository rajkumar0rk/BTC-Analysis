#!/usr/bin/env python3
"""Independent ETHUSD replay of BTC-Analysis research scripts.

Only reads ETHUSD archived exchange data. Executes copies of source scripts
in a private working directory, never importing existing BTC research outputs.
Absolute BTC price-point experiments are mapped using an explicitly disclosed
fixed 0.04 ETH quote-points per BTC quote-point sensitivity assumption; these
are *ported research variants*, not original BTC backtest parity. No hindsight
selection is advertised as tradable. November partial is excluded from any
22-month goal qualification.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import traceback
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "delta_india" / "ETHUSD"
OUT = ROOT / "eth_strategy_replay"
QUOTE_POINT_SCALE = 0.04
SLIP_ETH = 0.20  # assumed adverse ETHUSD price units per execution side
COMPLETE_MONTHS = tuple(f"{year}-{month:02d}" for year, first, last in ((2025, 1, 12), (2026, 1, 10))
                        for month in range(first, last+1))
STAGE = [
    "research_every_candle_200.py",
    "research_behavioral_discovery.py",
    "research_directional_acceptance.py",
    "research_retest_reclaim_stage4.py",
    "research_volatility_scaled_exits_stage5.py",
    "research_time_day_volume_200.py",
    "research_anytime_volume_volatility_patterns.py",
    "research_adaptive_anytime_entries_stage9.py",
    "research_dynamic_exit_stage10.py",
    "research_structure_rr_stage11.py",
    "research_pretrend_market_state_stage12.py",
    "research_trend_pullback_breakout_stage13.py",
    "research_monthly_regime_stage14.py",
    "research_july_drawdown_stage15.py",
    "research_monthly_regime_switch_stage16.py",
    "research_swing_donchian_stage17.py",
    "research_monthly_portfolio_stage18.py",
    "research_new_1h_patterns_stage19.py",
    "research_monthly_10pct_stage19.py",
    "research_signal_inversion_stage20.py",
    "research_three_sleeve_stage20.py",
    "research_monthly_fixed_weight_stage21.py",
    "research_trade_counts_stage22.py",
    "research_wide_monthly_stage23.py",
    "research_failed_auction_stage24.py",
    "research_stage24_failed_auction.py",
]
SKIP = {
    "analyze_first_forward_arbitrage.py": "Forward-only order-book event research; ETH historical microstructure tape is unavailable",
    "research_market_neutral_carry.py": "Requires matching ETHUSDT spot historical hedge data and verified settlement transfers; ETHUSD candles alone cannot reproduce this",
}
# Targeted price-point conversions where sources encode BTC-specific fixed
# dollar targets rather than ATR/percentage rules. All other numeric constants
# are preserved and require post-run per-strategy review before use.
POINT_PATCHES = {
    "research_every_candle_200.py": [
        ("STOP = np.array([0.5, 25., 50., 100., 150., 200., 300., 500.]", "STOP = np.array([0.02, 1., 2., 4., 6., 8., 12., 20.]"),
        ("(200. + 2.*5. + 2.*0.00059*entry)", "(8. + 2.*0.2 + 2.*0.00059*entry)"),
        ("good >= 200.", "good >= 8."),
        ("exit_mid=entry_mid+side*200.", "exit_mid=entry_mid+side*8."),
        ("for stop in (25,50,100,200,300):", "for stop in (1,2,4,8,12):"),
        ("((100,30),(100,60),(200,30),(200,60),(None,60))", "((4,30),(4,60),(8,30),(8,60),(None,60))"),
    ],
    "research_time_day_volume_200.py": [
        ("STOP == 100", "STOP == 4"),
        ("STOP == 200", "STOP == 8"),
        ("((100,30),(200,30),(100,60),(200,60))", "((4,30),(8,30),(4,60),(8,60))"),
    ],
    "research_monthly_10pct_stage19.py": [
        ("MIN_STOP=120.", "MIN_STOP=4.8"),
        ("MAX_STOP=1400.", "MAX_STOP=56."),
    ],
    "research_one_trade_every_day_200.py": [
        ("STOPS=(150,250,400)", "STOPS=(6,10,16)"),
        ("take=p+side*200", "take=p+side*8"),
        ("price_at_net_target(p,side,200)", "price_at_net_target(p,side,8)"),
        ("r.net_points.ge(199.9)", "r.net_points.ge(7.99)"),
        ("(summary.stop==250)", "(summary.stop==10)"),
        ("stop=250,max_hold_min=180", "stop=10,max_hold_min=180"),
    ],
    "research_time_day_strategies.py": [
        ("(z>=200).mean()", "(z>=8).mean()"),
        ("(z>=500).mean()", "(z>=20).mean()"),
        ("for stop in (250,500,800):", "for stop in (10,20,32):"),
        ("for target in (0,500,1000):", "for target in (0,20,40):"),
        ("after.stop_points==500", "after.stop_points==20"),
    ],
    "research_daily_200_500_points.py": [
        ("TARGETS=[200,300,500]", "TARGETS=[8,12,20]"),
        ("STOPS=[150,250]", "STOPS=[6,10]"),
        ("SLIP_POINTS_PER_SIDE=5.0", "SLIP_POINTS_PER_SIDE=0.20"),
        ("both.range_points>=200", "both.range_points>=8"),
        ("both.range_points>=500", "both.range_points>=20"),
    ],
    "research_v7_1_retest_2025.py": [
        ("TARGET = 1000.0", "TARGET = 40.0"),
        ("STOP = 500.0", "STOP = 20.0"),
    ],
    "research_mtf_swing_range_fixed3r.py": [
        ("EXIT_PAIRS=((200,600),(100,300),(300,900),(400,1200))",
         "EXIT_PAIRS=((8,24),(4,12),(12,36),(16,48))"),
    ],
}
REQUIRES_MANUAL_PRICE_REVIEW = set([
    "research_every_candle_200.py", "research_time_day_volume_200.py",
    "research_monthly_10pct_stage19.py", "research_one_trade_every_day_200.py",
    "research_time_day_strategies.py", "research_daily_200_500_points.py",
    "research_v7_1_retest_2025.py", "research_mtf_swing_range_fixed3r.py",
])

def now() -> str:
    return datetime.now(timezone.utc).isoformat()

def source_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def manifest_quality():
    p = json.loads((DATA / "1m" / "manifest.json").read_text())
    if p.get("symbol") != "ETHUSD":
        raise ValueError("Unexpected ETH instrument manifest")
    months = {x["file"][:7]: x for x in p["partitions"]}
    for ym in COMPLETE_MONTHS:
        if ym not in months or months[ym]["missing_minutes"] != 0:
            raise ValueError(f"Not fully covered ETHUSD month: {ym}")
    i = json.loads((DATA / "institutional" / "history_manifest.json").read_text())
    if i.get("symbol") != "ETHUSD":
        raise ValueError("Unexpected ETH institutional manifest")
    return {
        "price_months": len(p["partitions"]),
        "complete_22_months": len(COMPLETE_MONTHS),
        "complete_months": list(COMPLETE_MONTHS),
        "price_rows": sum(x["observed_candles"] for x in p["partitions"]),
        "price_gaps": sum(x["missing_minutes"] for x in p["partitions"]),
        "institutional": {key: {
            "rows": value["rows_saved"], "gaps": value["missing_dense_intervals"]
        } for key,value in i["series"].items()},
    }

def rewrite(text: str, name: str):
    changed = []
    # Rewrite only the original BTC instrument reference; leave script and
    # strategy identifier names unchanged so dependencies remain valid.
    text = text.replace("data/delta_india/BTCUSD", "data/delta_india/ETHUSD")
    text = text.replace("MARK:BTCUSD", "MARK:ETHUSD")
    text = text.replace("OI:BTCUSD", "OI:ETHUSD")
    text = text.replace("FUNDING:BTCUSD", "FUNDING:ETHUSD")
    text = re.sub(r"(?m)^(\s*)(SLIPPAGE|SLIP)\s*=\s*5(?:\.0?)?(\s*(?:#.*)?)$",
                  lambda m: f"{m.group(1)}{m.group(2)} = {SLIP_ETH}{m.group(3)}", text)
    if name in POINT_PATCHES:
        for before, after in POINT_PATCHES[name]:
            n = text.count(before)
            if n != 1:
                raise ValueError(f"Expected exactly one price-point replacement in {name}: {before!r}, found {n}")
            text = text.replace(before, after)
            changed.append(before + " -> " + after)
    compile(text, name, "exec")
    return text, changed

def setup(group: str):
    quality = manifest_quality()
    groupdir = OUT / group
    work = groupdir / "workspace"
    if groupdir.exists():
        shutil.rmtree(groupdir)
    scripts = work / "scripts"
    scripts.mkdir(parents=True)
    (work / "analysis").mkdir(parents=True)
    destdata = work / "data" / "delta_india" / "ETHUSD"
    (destdata / "1m").mkdir(parents=True)
    for src in sorted((DATA / "1m").glob("????-??.csv.gz")):
        (destdata / "1m" / src.name).symlink_to(src.resolve())
    shutil.copy2(DATA / "1m" / "manifest.json", destdata / "1m" / "manifest.json")
    hist = DATA / "institutional" / "history"
    for typ in ["mark_1m", "open_interest_5m", "funding_1h"]:
        (destdata / "institutional" / "history" / typ).mkdir(parents=True)
        for src in sorted((hist / typ).glob("????-??.csv.gz")):
            (destdata / "institutional" / "history" / typ / src.name).symlink_to(src.resolve())
    shutil.copy2(DATA / "institutional" / "history_manifest.json",
                 destdata / "institutional" / "history_manifest.json")
    patches = {}
    for src in sorted((ROOT / "scripts").glob("*.py")):
        if src.name == Path(__file__).name: continue
        p, edits = rewrite(src.read_text(), src.name)
        (scripts / src.name).write_text(p, encoding="utf-8")
        if edits: patches[src.name] = edits
    (groupdir / "patches.json").write_text(json.dumps(patches, indent=2)+"\n")
    (groupdir / "dataset_quality.json").write_text(json.dumps(quality, indent=2)+"\n")
    return groupdir, work

def jobs(group: str):
    present = {p.name for p in (ROOT/"scripts").glob("*.py")}
    eligible = {name for name in present if
                (name.startswith("research_") or name.startswith("analyze_")
                 or name.startswith("v7_")) and name not in SKIP}
    stage = [name for name in STAGE if name in eligible]
    if group == "stage": return stage
    if group == "independent": return sorted(eligible.difference(stage))
    raise ValueError(group)

def execute(group: str, timeout: int):
    groupdir, work = setup(group)
    manifest = []
    env = os.environ.copy()
    env.update({
        "PYTHONPATH": str(work / "scripts"),
        "PYTHONDONTWRITEBYTECODE": "1",
        "NUMBA_CACHE_DIR": str(groupdir / "numba_cache"),
        "OPENBLAS_NUM_THREADS": "1",
        "OMP_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
    })
    (groupdir / "logs").mkdir(parents=True)
    for script in jobs(group):
        output = work / "analysis"
        before = {str(p.relative_to(output)) for p in output.rglob("*") if p.is_file()}
        started = time.monotonic()
        outlog = groupdir / "logs" / (script + ".stdout.log")
        errlog = groupdir / "logs" / (script + ".stderr.log")
        status, code, reason = "failed", None, ""
        print(f"ETH_REPLAY_START {script} {now()}", flush=True)
        with outlog.open("w") as so, errlog.open("w") as se:
            try:
                p = subprocess.run([sys.executable, str(work/"scripts"/script)],
                                   cwd=str(work), env=env, stdout=so, stderr=se,
                                   timeout=timeout, check=False)
                code = p.returncode
                status = "completed" if code == 0 else "failed"
            except subprocess.TimeoutExpired:
                status = "timeout"
                reason = f"Per-study timeout {timeout}s"
            except Exception as exc:
                reason = type(exc).__name__ + ": " + str(exc)
        after = {str(p.relative_to(output)) for p in output.rglob("*") if p.is_file()}
        new_files = sorted(after.difference(before))
        if status == "completed" and not new_files:
            status = "no_new_output"
        if status != "completed" and not reason:
            try:
                reason = errlog.read_text(errors="replace")[-2500:]
            except Exception:
                reason = "No readable error"
        model_kind = ("scaled_price_point_variant" if script in REQUIRES_MANUAL_PRICE_REVIEW else
                      "ported_signals_may_contain_unscaled_price_units")
        rec = {
            "script": script, "status": status, "exit_code": code,
            "seconds": round(time.monotonic()-started,1),
            "output_file_count": len(new_files), "output_sample": new_files[:8],
            "price_port": model_kind,
            "cost_assumption": "0.05% taker each side + 18% GST, 0.20 ETH price points adverse slippage per side when source exposes SLIP",
            "limitations": "Funding settlements, historical bid/ask spread, liquidation and true L1 impact not verified; original research may contain additional BTC-specific thresholds",
            "reason": reason[:2500],
        }
        manifest.append(rec)
        (groupdir / "status.json").write_text(json.dumps(manifest,indent=2)+"\n")
        print("ETH_REPLAY_DONE "+json.dumps({k:rec[k] for k in ("script","status","seconds","output_file_count")}),flush=True)
    for name,msg in SKIP.items():
        if group == "independent":
            manifest.append({"script":name,"status":"not_reproducible","reason":msg})
    (groupdir/"status.json").write_text(json.dumps(manifest,indent=2)+"\n")
    cols=["script","status","seconds","output_file_count","price_port","reason"]
    with (groupdir/"status.csv").open("w",newline="") as fp:
        w=csv.DictWriter(fp,fieldnames=cols,extrasaction="ignore")
        w.writeheader();w.writerows(manifest)
    summarize_group(groupdir, group, manifest)
    return manifest

def summarize_group(groupdir: Path, group: str, manifest: list):
    counts = {label:sum(x["status"]==label for x in manifest)
              for label in sorted({x["status"] for x in manifest})}
    lines=[
        f"# ETHUSD independent research replay — {group}",
        "",
        f"Generated UTC: {now()}",
        f"Historical ETHUSD source: Delta Exchange India; 2025-01 through 2026-11-17 (November incomplete).",
        f"Only 22 completed months 2025-01 through 2026-10 qualify for full-month claims.",
        f"Execution status: {json.dumps(counts)}",
        "",
        "## Critical assumptions",
        "- Runs original study implementation in a separate working tree using ETHUSD candles, not BTC price archives or previously computed BTC analysis results.",
        "- Fee assumption is 0.05% taker per side + GST 18% on fee; slippage assumption 0.20 ETH price units per side where supported.",
        "- Fixed BTC price-point studies require ETH normalization. The explicitly patched 0.04 point scale is a provisional sensitivity assumption, NOT a calibrated ETH contract equivalence.",
        "- Other hardcoded BTC absolute prices may remain. No completed script is automatically approved for live use.",
        "- Some studies use in-sample tuning or 2026-exposed research; do not treat profitable configurations as validated edge.",
        "- Funding observations are NOT a record of settled funding transfers; actual spread, order-book impact and liquidations are not included.",
        "- Scripts with failed outputs are NOT counted as completed ETH backtests.",
        "",
        "## Executed scripts",
        "| Script | Status | Seconds | New files |",
        "|---|---|---:|---:|",
    ]
    for x in manifest:
        lines.append(f"| {x['script']} | {x['status']} | {x.get('seconds','')} | {x.get('output_file_count','')} |")
    (groupdir/"REPLAY_REPORT.md").write_text("\n".join(lines)+"\n")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--group",choices=["stage","independent"],required=True)
    p.add_argument("--timeout",type=int,default=660)
    args=p.parse_args()
    if args.timeout < 30: p.error("timeout too short")
    result=execute(args.group,args.timeout)
    success=sum(x["status"]=="completed" for x in result)
    print("ETH_REPLAY_GROUP_RESULT",json.dumps({
        "group":args.group,"attempted":len(result),
        "completed":success,
        "failed":sum(x["status"] in ("failed","timeout") for x in result),
        "blocked":sum(x["status"] in ("not_reproducible","no_new_output") for x in result),
    }),flush=True)
    if success==0: raise SystemExit("No ETH studies completed; inspect logs")
if __name__=="__main__":main()
