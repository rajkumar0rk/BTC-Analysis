#!/usr/bin/env python3
"""Repair and rerun only the six previously failed ETH historical backtest engines.

Preserves all BTC code and all existing ETH reports. Creates temporary
BTC-legacy-compatible paths containing ONLY ETH market observations. ETH mark
OHLC is multiplied by exactly the same fixed ex-ante factor as ETH futures;
OI/funding are copied from native ETH sources unchanged (never use BTC OI).
Legacy BTC literal point thresholds are interpreted solely as VIRTUAL price
units; they are not literal ETH dollar stops or targets.

Stage18 has no candidate meeting its 2025 eligibility filter. Its original
source does not handle an empty pool and raises IndexError. An ETH-only
temporary patched COPY selects the best 2025-ranked *unqualified* candidate
for diagnostic reporting, while retaining the empty qualified-list finding.
That is a code robustness repair, NOT a profitable strategy discovery.

No live orders. No automations or original BTC source are modified.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
import pandas as pd
import numpy as np

from research_eth_all_strategies_replay import (
    ROOT, prepare_data, copy_result_summaries, score_months,
    run_one
)

OUTROOT=ROOT/"analysis/ethusd_failed_engine_repairs"
REPAIRS={
    "high_frequency":[
        "research_adaptive_anytime_entries_stage9.py",
    ],
    "institutional":[
        "research_behavioral_discovery.py",
        "research_directional_acceptance.py",
        "research_retest_reclaim_stage4.py",
        "research_volatility_scaled_exits_stage5.py",
    ],
    "portfolio":[
        "research_monthly_regime_stage14.py",
        "research_july_drawdown_stage15.py",
        "research_swing_donchian_stage17.py",
        "research_monthly_portfolio_stage18.py",
    ]
}
ORIGINAL_FAILED={
    "high_frequency":["research_adaptive_anytime_entries_stage9.py"],
    "institutional":[
       "research_behavioral_discovery.py",
       "research_directional_acceptance.py",
       "research_retest_reclaim_stage4.py",
       "research_volatility_scaled_exits_stage5.py"],
    "portfolio":["research_monthly_portfolio_stage18.py"]
}
PROVENANCE_NOTES=[
    "All BTC strategy engines and original results remain unchanged",
    "ETH futures and mark OHLC scaled by the SAME fixed Jan 1 2025 BTC/ETH price ratio; ETH open interest and funding copied without price scaling",
    "BTC-coded 200 price-point exits are VIRTUAL scaled points, NOT $200 ETHUSD exits; native ETH ATR reports are separate",
    "No OI, mark or funding series is taken from BTC history; no fake market data",
    "Fee model of original engines: modeled Delta India taker 0.05% per leg + 18% GST and 5 VIRTUAL points slippage per leg",
    "Additional actual ETH order-book spread, funding paid over held trades, liquidation and market impact are not fully simulated",
    "Months January 2025–October 2026 only; November incomplete and excluded from claims",
    "January 2025 IST begins five and a half hours before the January 1 UTC archive and is not fully covered",
    "Rerun engine completed != trade profitable; monthly consistency requires positive after-cost returns in all 22 months",
]

def stage_eth_institutional_sources(work,quality):
    source=ROOT/"data/delta_india/ETHUSD/institutional/history"
    manifest=json.loads((ROOT/"data/delta_india/ETHUSD/institutional/history_manifest.json").read_text())
    dest=work/"data/delta_india/BTCUSD/institutional/history"
    categories={"mark_1m":60,"open_interest_5m":300,"funding_1h":3600}
    ratio=float(quality["fixed_multiplier"])
    report={}
    for category,seconds in categories.items():
        series=manifest["series"][category]
        if series.get("native_source_symbol") not in ("MARK:ETHUSD","ETHUSD"):
            # The manifest sometimes uses a non-ETH symbol for OI/funding;
            # require its actual source explicitly to contain ETHUSD.
            label=str(series.get("native_source_symbol",""))
            if "ETHUSD" not in label.upper():
                raise AssertionError(f"Wrong source symbol for {category}: {label}")
        records=series["partitions"]
        files=[]
        for rec in records:
            name=Path(rec["partition"]).name
            if not name.endswith(".csv.gz"):continue
            src=source/category/name
            if not src.is_file():raise FileNotFoundError("Missing ETH "+str(src))
            if src.stat().st_size != rec["compressed_bytes"]:
                raise AssertionError(f"ETH archive compressed byte mismatch {src}")
            df=pd.read_csv(src,compression="gzip")
            if not set(["time","open","high","low","close","volume"]).issubset(df.columns):
                raise AssertionError(f"ETH institutional series schema mismatch {src}")
            if len(df)!=int(rec["rows"]):raise AssertionError(f"Wrong ETH count in {src}")
            ts=df.time.to_numpy(np.int64)
            if np.any(np.diff(ts)!=seconds):
                raise AssertionError(f"Nonconsecutive source timestamps in {src}")
            files.append(name)
            d=dest/category/name
            d.parent.mkdir(parents=True,exist_ok=True)
            if category=="mark_1m":
                # Mark series MUST share the same virtual USD ratio as
                # futures for basis to remain meaningful.
                for field in ["open","high","low","close"]:
                    df[field]=df[field].astype(float)*ratio
                df.to_csv(d,index=False,compression="gzip",float_format="%.10f")
            else:
                shutil.copyfile(src,d)
        if len(files)!=23:raise AssertionError("Expected 23 ETH series partitions")
        report[category]=dict(partitions=len(files),
            observations=int(series["rows_saved"]),
            coverage_pct=series.get("coverage_pct"),
            original_symbol=series.get("native_source_symbol"),
            price_scaled=(category=="mark_1m"),
            prices_from="ETHUSD, never BTCUSD")
    return report

def run_patched_stage18(work,timeout_s):
    """Change only a temporary ETH copy of Stage18, never the canonical script."""
    sfile=ROOT/"scripts/research_monthly_portfolio_stage18.py"
    source=sfile.read_text()
    old="    chosen=train.iloc[0].to_dict()"
    if source.count(old)!=1:raise AssertionError("Stage18 source no longer matches fallback patch")
    new="""    if train.empty:
        # ETH diagnostic fallback, NOT a 2025-qualified strategy.
        # 2026 returns are not used to select a model.
        chosen=pairs.sort_values(
          ["positive_months_2025","losing_months_2025","return_2025_pct"],
          ascending=[False,True,False],kind="stable").iloc[0].to_dict()
        selected_without_qualifying_2025=True
    else:
        chosen=train.iloc[0].to_dict()
        selected_without_qualifying_2025=False
"""
    patched=source.replace(old,new)
    # Add explicit machine-readable metadata declaring selection failure.
    oldmeta="        selected=chosen,\n"
    if patched.count(oldmeta)!=1:raise AssertionError("Stage18 metadata signature changed")
    patched=patched.replace(oldmeta,"        selected=chosen,\n        eth_qualified_2025_models=int(len(train)),\n        eth_selected_is_unqualified_fallback=selected_without_qualifying_2025,\n")
    script=work/"scripts/research_monthly_portfolio_stage18_ETH_ONLY.py"
    script.parent.mkdir(parents=True,exist_ok=True)
    script.write_text(patched)
    log_start=time.monotonic()
    cmd=[sys.executable,str(script),"--stage15-ledger",str(
        work/"analysis/institutional_discovery_stage15_july_loss_controls/variant_trade_ledger.csv.gz")]
    env=os.environ.copy()
    env["PYTHONUNBUFFERED"]="1"
    try:
        p=subprocess.run(cmd,cwd=work,text=True,stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,timeout=timeout_s,env=env)
        return dict(script="research_monthly_portfolio_stage18.py",
            executed_sandbox_copy=script.name,
            status="completed" if p.returncode==0 else "failed",
            reason="" if p.returncode==0 else f"exit_code={p.returncode}",
            elapsed_seconds=round(time.monotonic()-log_start,2),
            log_tail=p.stdout[-8000:])
    except subprocess.TimeoutExpired as e:
        z=e.stdout or b""
        return dict(script="research_monthly_portfolio_stage18.py",
            executed_sandbox_copy=script.name,
            status="timed_out",reason=f"Exceeded {timeout_s}s",
            elapsed_seconds=round(time.monotonic()-log_start,2),
            log_tail=z.decode(errors="replace")[-8000:] if isinstance(z,bytes) else str(z)[-8000:])

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--suite",choices=sorted(REPAIRS),required=True)
    p.add_argument("--per-script-timeout-seconds",type=int,default=1800)
    args=p.parse_args()
    output=OUTROOT/args.suite
    output.mkdir(parents=True,exist_ok=True)
    logs=[]
    work=Path(tempfile.mkdtemp(prefix="eth_repair_"))
    try:
        quality=prepare_data(work,output)
        institutional=stage_eth_institutional_sources(work,quality)
        (output/"ETH_INSTITUTIONAL_ALIAS_AUDIT.json").write_text(
            json.dumps(institutional,indent=2)+"\n")
        for name in REPAIRS[args.suite]:
            print("ETH_REPAIR_START "+name,flush=True)
            if args.suite=="portfolio" and name=="research_monthly_portfolio_stage18.py":
                result=run_patched_stage18(work,args.per_script_timeout_seconds)
            else:
                result=run_one(work,name,args.per_script_timeout_seconds)
            logs.append(result)
            print("ETH_REPAIR_FINISH "+name+" "+result["status"],flush=True)
            (output/"execution_results.json").write_text(json.dumps(logs,indent=2))
            copy_result_summaries(work,output,name)
        summaries=score_months(work,output)
        actual=[z for z in logs if z["script"] in ORIGINAL_FAILED[args.suite]]
        if len(actual)!=len(ORIGINAL_FAILED[args.suite]):
            raise AssertionError("Missing original failed strategy attempts")
        flag={}
        if args.suite=="portfolio":
            meta=work/"analysis/institutional_discovery_stage18_monthly_dual_strategy/quality.json"
            if meta.exists():
                m=json.loads(meta.read_text())
                flag=dict(stage18_qualified_2025_models=m.get("eth_qualified_2025_models"),
                    stage18_selected_unqualified_fallback=m.get("eth_selected_is_unqualified_fallback"))
                if m.get("eth_selected_is_unqualified_fallback"):
                    # Never report a completed run as a qualifying Stage18.
                    print("STAGE18_NO_2025_ELIGIBLE_ETH_PORTFOLIOS",flush=True)
        report=dict(
            instrument="ETHUSD",original_failures_rerun=len(actual),
            repaired_success_count=sum(z["status"]=="completed" for z in actual),
            suite=args.suite,run_results=logs,actual_failed_engines=actual,
            status="all_repaired" if all(z["status"]=="completed" for z in actual) else "remaining_failures",
            monthly_summaries=summaries,source=quality,
            true_eth_institutional_sources=institutional,
            stage18_qualification=flag,
            limitations=PROVENANCE_NOTES)
        (output/"RUN_REPORT.json").write_text(json.dumps(report,indent=2,default=str)+"\n")
        lines=[
            f"# ETHUSD six-failed-engine repair — {args.suite}","",
            "All source market data genuinely comes from ETHUSD; canonical BTC code untouched.",
            "ETH prices are price-normalized for legacy rules; NOT native ETH 200-USD exits.",
            "This is a repair of six failed engines, not 6 profitable strategies.",
            "",
            f"Previously failed engines rerun: {len(actual)}",
            f"Repaired engines completed: {report['repaired_success_count']}","",
            "## Execution outcomes",
            *[f"- {v['script']}: **{v['status']}**, {v['elapsed_seconds']} seconds, {v['reason']}"
              for v in logs],
            "",
            "## Source verification",
            f"- ETH mark / OI / funding source manifests: {json.dumps(institutional)}",
            "",
            "## Stage18 selection audit",
            str(flag),
            "If Stage18 eligibility is 0, it is NOT a qualifying monthly-profitable selection.",
            "",
            "## Model/monthly summaries",
            *[str(v) for v in summaries],
            "",
            "## Limitations",
            *["- "+v for v in PROVENANCE_NOTES]]
        (output/"RESEARCH_REPORT.md").write_text("\n".join(lines)+"\n")
        print("ETH_REPAIR_SUITE_RESULT "+json.dumps(dict(suite=args.suite,
            failures_rerun=len(actual),completed=report["repaired_success_count"],
            status=report["status"],stage18=flag)),flush=True)
    finally:
        shutil.rmtree(work,ignore_errors=True)

if __name__=="__main__":
    main()
