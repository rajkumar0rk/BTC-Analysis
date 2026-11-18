#!/usr/bin/env python3
"""Independent ETHUSD normalized index portability suite for prior BTC research.

Original model code from main is cloned to a temporary module directory and
ONLY source market paths and output paths are changed; entry logic, risk and
absolute price-point thresholds are not tuned. Imported helper modules are
also patched to use ETH data. A script must not read prior BTC result files.

Every script is classified as completed, failed, timed out, or non-standalone.
NEVER classify descriptive outputs as a +10%-monthly trading edge.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
from datetime import datetime, timezone
import pandas as pd

ROOT=Path.cwd()
SOURCE=ROOT/"scripts"
RESULT_ROOT=Path("analysis/eth_normalized_execution_results")
AUDIT=Path("analysis/eth_normalized_all_v2")
GROUPS={
  "structure":[
    "research_big_trend_stage1.py",
    "research_previous_day_range_swing.py",
    "research_mtf_swing_range_long.py",
    "research_mtf_swing_range_fixed3r.py",
    "research_mtf_swing_range_long_fixed2r.py",
    "research_mtf_swing_range_short_fixed2r.py",
    "research_mtf_swing_range_short_fixed3r.py",
    "research_mtf_uptrend_short_fixed3r.py"
  ],
  "intraday":[
    "research_daily_200_500_points.py",
    "research_one_trade_every_day_200.py",
    "research_every_candle_200.py",
    "research_anytime_volume_volatility_patterns.py",
    "research_time_day_volume_200.py",
    "research_price_action_time_day.py",
    "research_time_day_strategies.py"
  ],
  "signals":[
    "research_dynamic_exit_stage10.py",
    "research_structure_rr_stage11.py",
    "research_pretrend_market_state_stage12.py",
    "research_stage12_monthly.py",
    "research_trend_pullback_breakout_stage13.py",
    "research_monthly_regime_stage14.py",
    "research_monthly_regime_switch_stage16.py"
  ],
  "later":[
    "research_swing_donchian_stage17.py",
    "research_new_1h_patterns_stage19.py",
    "research_monthly_10pct_stage19.py",
    "research_signal_inversion_stage20.py",
    "research_stage24_failed_auction.py",
    "research_failed_auction_stage24.py",
    "research_trade_counts_stage22.py"
  ],
  "institutional":[
    "research_selective_big_moves.py",
    "research_behavioral_discovery.py",
    "research_adaptive_anytime_entries_stage9.py",
    "research_directional_acceptance.py",
    "research_retest_reclaim_stage4.py",
    "research_volatility_scaled_exits_stage5.py",
    "analyze_institutional_regimes.py",
    "research_intraday_spread.py"
  ],
  "legacy":[
    "research_v7_1_retest_2025.py",
    "research_v7_2_daily_4h_2025.py",
    "research_v8_1_2025_exits.py",
    "research_v8_2025_big_moves.py",
    "analyze_1m_exit_methods.py",
    "analyze_delta_mtf_institutional.py",
    "research_july_drawdown_stage15.py"
  ],
  "research_branches":[
    "eth_transfer_stage24.py",
    "eth_transfer_stage25.py"
  ],
  "portfolio":[
    "research_monthly_portfolio_stage18.py",
    "research_three_sleeve_stage20.py",
    "research_monthly_fixed_weight_stage21.py",
    "research_wide_monthly_stage23.py"
  ]
}
ALL_LIST=[s for group in GROUPS.values() for s in group]
assert len(ALL_LIST)==len(set(ALL_LIST))

def transform(t):
    # No change to trading logic, thresholds, exits, model selection or cost rates.
    # Textual substitutions intentionally make imported helper modules read ETH.
    z=t.replace("BTCUSDT","ETHUSDT").replace("BTCUSD","ETHUSD")
    # Redirect all original ETH sources into causal Jan2025-anchored equivalent
    # BTC price units, so an old 200 point strategy never uses 200 ETH points.
    # No change to entry logic, absolute thresholds, or exit model.
    z=z.replace("data/delta_india/ETHUSD", "data/eth_normalized_2025_anchor")
    z=z.replace("analysis/","analysis/eth_normalized_execution_results/")
    if "data/delta_india/BTCUSD" in z:
        raise ValueError("BTC market source path remains after port")
    if re.search(r'(?<!eth_all_original_rules/)analysis/(?:institutional|delta|big_|mtf_|research)',z):
        raise ValueError("Original BTC analysis output reference remains")
    return z

def manifest_check():
    raw=ROOT/"data/delta_india/ETHUSD/1m"
    j=json.loads((raw/"manifest.json").read_text())
    parts={p["file"]:p for p in j["partitions"]}
    complete=[]
    for mm in pd.period_range("2025-01","2026-10",freq="M"):
        file=str(mm)+".csv.gz"
        p=parts.get(file)
        if p is None or p["missing_minutes"]!=0 or p["expected_minutes"]!=p["observed_candles"]:
            raise ValueError(f"ETH month data missing/partial: {file}")
        digest=hashlib.sha256((raw/file).read_bytes()).hexdigest()
        if digest!=p["sha256_gzip"]: raise ValueError("ETH source hash mismatch "+file)
        complete.append(file)
    return {"source":j.get("source"),"symbol":"ETHUSD","periods":complete,
            "total_utc_minutes":sum(parts[p]["observed_candles"] for p in complete),
            "first_IST_month_unavailable_hours":5.5,
            "source_manifest_time":j.get("generated_at_utc")}

def call_script(file,workdir,timeout_s):
    orig=(SOURCE/file).read_text()
    rewritten=transform(orig)
    executable=workdir/file
    executable.write_text(rewritten)
    # Explicit checks: ensure every script's results go to the ETH-specific root.
    if "analysis/" in orig and "analysis/eth_normalized_execution_results/" not in rewritten:
        raise ValueError("ETH output isolation failed")
    t0=time.monotonic()
    entry={
        "script":file,"source_sha256":hashlib.sha256(orig.encode()).hexdigest(),
        "port_sha256":hashlib.sha256(rewritten.encode()).hexdigest(),
        "modifications":"BTCUSD source to 2025-reference CONSTANT normalized ETH index, isolated reports. Strategy rules unchanged",
        "costs_in_original_model":"unchanged; must inspect individual report",
        "point_thresholds":"Original BTC index thresholds now ETH pts = BTC index pts / constant Jan2025 BTC/ETH price ratio",
        "run_time_seconds":0,
        "status":"unknown",
    }
    # Do not write giant logs into Git; include short stderr/stdout tails only.
    try:
        env=dict(os.environ)
        env["PYTHONPATH"]=str(workdir)+os.pathsep+str(SOURCE)
        result=subprocess.run(
            [sys.executable,str(executable)],
            cwd=str(ROOT),env=env,capture_output=True,text=True,timeout=timeout_s)
        entry["run_time_seconds"]=round(time.monotonic()-t0,2)
        entry["return_code"]=result.returncode
        entry["stdout_tail"]=result.stdout[-2000:]
        entry["stderr_tail"]=result.stderr[-4500:]
        entry["status"]="success" if result.returncode==0 else "failed"
    except subprocess.TimeoutExpired as ex:
        entry["run_time_seconds"]=round(time.monotonic()-t0,2)
        entry["status"]="timeout"
        entry["error"]=f"Exceeded {timeout_s}s per script."
    except Exception as ex:
        entry["run_time_seconds"]=round(time.monotonic()-t0,2)
        entry["status"]="error"
        entry["error"]=repr(ex)
    # Locate files from the reported subfolder, keeping only lightweight
    # verified output pointers and selected month-metrics in persisted report.
    outputs=list((ROOT/RESULT_ROOT).rglob("*"))
    entry["output_dir_count_after"]=sum(o.is_dir() for o in outputs)
    return entry

def small_results_manifest():
    # Actual produced file metadata; no BTC artifacts can be accessed here
    # because only ETH-specific translated paths count.
    out=[]
    for p in sorted((ROOT/RESULT_ROOT).rglob("*")):
        if p.is_file():
            rel=str(p.relative_to(ROOT))
            out.append({"path":rel,"bytes":p.stat().st_size})
    return out

def save_small_reports():
    # Preserve compact results and monthly tables only; full historical
    # ledgers remain accessible as GitHub Action artifacts, not auto-committed.
    for p in (ROOT/RESULT_ROOT).rglob("*"):
        if not p.is_file():continue
        if p.stat().st_size>160_000:continue
        if not (p.name.endswith(".json") or
                p.name in ("RESEARCH_REPORT.md","monthly_results.csv",
                           "month_by_month.csv","monthly_net_account_returns.csv",
                           "monthly_mark_to_market.csv","selected_month_by_month.csv",
                           "selected_monthly.csv","monthly_2025_2026.csv")):
            continue
        rel=p.relative_to(ROOT/RESULT_ROOT)
        dest=ROOT/AUDIT/"excerpts"/rel
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(p,dest)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--group",required=True,choices=GROUPS)
    ap.add_argument("--per-script-timeout",type=int,default=240)
    args=ap.parse_args()
    (ROOT/AUDIT).mkdir(parents=True,exist_ok=True)
    source_check=manifest_check()
    from eth_btc_equivalent_data import prepare
    normalized=prepare()
    source_check["normalization"]={
      "btc_open_reference":normalized["btc_first_open"],
      "eth_open_reference":normalized["eth_first_open"],
      "constant_index_scale":normalized["synthetic_multiplier_btc_index_per_eth_price_point"],
      "eth_points_for_200_btc_index":normalized["equivalent_eth_price_points_per_200_btc_index_points"],
      "eth_slippage_for_5_btc_index":normalized["equivalent_eth_slippage_price_points_per_5_index_points"],
      "not_time_local":True
    }
    (ROOT/AUDIT/"NORMALIZATION.json").write_text(json.dumps(
        {k:v for k,v in normalized.items() if k!="partitions"},indent=2)+"\n")
    group=GROUPS[args.group]
    results=[]
    with tempfile.TemporaryDirectory(prefix="eth_scripts_") as tmp:
        patch_dir=Path(tmp)
        # Every project Python module is transformed, not only the entrypoint.
        # Internal imports therefore never load BTC-price arrays from main.
        files=list(SOURCE.glob("*.py"))
        for f in files:
            (patch_dir/f.name).write_text(transform(f.read_text()))
        for i,name in enumerate(group):
            if not (SOURCE/name).exists():
                results.append({"script":name,"status":"missing","error":"Source absent"});continue
            print("ETH_RUN",args.group,i+1,len(group),name,flush=True)
            result=call_script(name,patch_dir,args.per_script_timeout)
            print("ETH_STATUS",name,result["status"],result["run_time_seconds"],flush=True)
            results.append(result)
            (ROOT/AUDIT/f"status_{args.group}.json").write_text(
                json.dumps({"group":args.group,"source":source_check,
                            "runs":results},indent=2)+"\n")
    inventory=small_results_manifest()
    save_small_reports()
    (ROOT/AUDIT/f"inventory_{args.group}.json").write_text(
      json.dumps(inventory,indent=2)+"\n")
    successful=sum(x["status"]=="success" for x in results)
    print("ETH_GROUP_DONE",args.group,"success",successful,"of",len(results),flush=True)

if __name__=="__main__":main()
