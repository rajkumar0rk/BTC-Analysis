#!/usr/bin/env python3
"""Recover ten ETH-only replay scripts blocked by arguments, dependencies or diagnostics.

No original source code or signal logic in main is edited. Runs transformed
ETH source in an ephemeral folder, with dependent scripts in chronological
sequence, building fresh ETH ledgers instead of reusing BTC research artifacts.
All scripts read actual Delta ETH candles normalized into Jan2025
BTC-equivalent points. 2026 November remains PARTIAL DIAGNOSTIC ONLY.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import traceback

ROOT=Path.cwd()
SRC=ROOT/"scripts"
OUTPUT=ROOT/"analysis/eth_normalized_execution_results"
AUDIT=ROOT/"analysis/eth_failed10_recovery"
sys.path.insert(0,str(SRC))
from eth_all_prior_strategy_runner import transform
from eth_btc_equivalent_data import prepare

S12=OUTPUT/"institutional_discovery_stage12_pretrend"
S14=OUTPUT/"institutional_discovery_stage14_monthly_regimes"
S15=OUTPUT/"institutional_discovery_stage15_july_loss_controls"
S16=OUTPUT/"institutional_discovery_stage16_monthly_regime_switch"
S17=OUTPUT/"institutional_discovery_stage17_swing_breakout"
S18=OUTPUT/"institutional_discovery_stage18_monthly_dual_strategy"
S19=OUTPUT/"institutional_discovery_stage19_new_1h_patterns"
S20=OUTPUT/"institutional_discovery_stage20_three_sleeve"
S22=OUTPUT/"institutional_discovery_stage22_trade_audit"
CHAIN=[
 ("research_pretrend_market_state_stage12.py",[],False),
 ("research_monthly_regime_stage14.py",[],False),
 ("research_swing_donchian_stage17.py",[],False),
 ("research_new_1h_patterns_stage19.py",[],False),
 ("research_monthly_10pct_stage19.py",[],False),
 ("research_signal_inversion_stage20.py",[],False),
 ("research_stage12_monthly.py",["--ledger",str(S12/"trade_ledger.csv.gz")],True),
 ("research_monthly_regime_switch_stage16.py",["--original-artifact",str(S14)],True),
 ("research_july_drawdown_stage15.py",["--original-artifact",str(S14)],True),
 ("research_monthly_portfolio_stage18.py",["--stage15-ledger",str(S15/"variant_trade_ledger.csv.gz")],True),
 ("research_three_sleeve_stage20.py",[],True),
 ("research_monthly_fixed_weight_stage21.py",[],True),
 ("research_wide_monthly_stage23.py",[],True),
 ("research_trade_counts_stage22.py",[
    "--stage15",str(S15/"variant_trade_ledger.csv.gz"),
    "--stage17",str(S17/"trade_ledger.csv.gz"),
    "--stage19",str(S19/"trade_ledger.csv.gz")],True)
]
CALENDAR=[
 ("research_every_candle_200.py",[],True),
 ("research_time_day_volume_200.py",[],True),
]
TARGETS={
 "research_stage12_monthly.py",
 "research_monthly_regime_switch_stage16.py",
 "research_july_drawdown_stage15.py",
 "research_monthly_portfolio_stage18.py",
 "research_three_sleeve_stage20.py",
 "research_monthly_fixed_weight_stage21.py",
 "research_wide_monthly_stage23.py",
 "research_trade_counts_stage22.py",
 "research_every_candle_200.py",
 "research_time_day_volume_200.py"
}

def patched_source(name,orig):
    s=transform(orig)
    if name=="research_stage12_monthly.py":
        # BTC-only frozen sample-count/mean expectations must be derived from
        # the freshly replayed ETH Stage12 model summary, not BTC artifacts.
        needle='    for period,(expected_count,expected_mean) in zip(PERIODS,EXPECTED):'
        replacement=(
          '    EXPECTED = [(int(ref[ref.period==per].trades.iloc[0]),'
          ' float(ref[ref.period==per].avg_net_pts.iloc[0])) for per in PERIODS]\n'
          +needle)
        if needle not in s:raise ValueError("Stage12 expected-check source changed")
        s=s.replace(needle,replacement)
        s=s.replace('"source_action_run": 44108340139',
                    '"source_action_run": "ETH recovery current GitHub Actions run"')
        s=s.replace('"source_artifact_id": 14339268107',
                    '"source_artifact_id": "fresh ETH Stage12 result"')
    if name=="research_trade_counts_stage22.py":
        # Remove BTC historical exact counts 64,24,119; use nonempty and
        # preserve monthly NET R reconciliation checks below.
        for col,num in (("a",64),("b",24),("c",119)):
            needle=f"if len({col})!={num}:"
            if needle not in s:raise ValueError("Stage22 BTC-only trade-count guard missing")
            s=s.replace(needle,f"if len({col})<1:")
        s=s.replace('stage15="GH Actions 44120459865 Stage15 original full ledger"',
                    'stage15="Fresh ETH Stage15 source ledger"')
        s=s.replace('stage17="GH Actions 44128535269 Stage17 original full ledger"',
                    'stage17="Fresh ETH Stage17 source ledger"')
        s=s.replace('stage19="GH Actions 44234824670 Stage19 original full ledger"',
                    'stage19="Fresh ETH Stage19 source ledger"')
    if name=="research_monthly_portfolio_stage18.py":
        # ETH 2025 had no candidate satisfying BOTH >=9 active months and
        # positive total 2025 profit; the original Stage18 code did train.iloc[0]
        # and crashed. Keep all 105 candidate return series and model rules.
        # Select a 2025-only fallback explicitly flagged as UNQUALIFIED.
        anchor='    top=train.head(12)'
        if anchor not in s:raise ValueError("Stage18 selection source changed")
        s=s.replace(anchor,'''
    original_2025_qualified_count=int(len(train))
    if train.empty:
        train=pairs[pairs.active_months_2025>=9].copy()
        if train.empty:
            train=pairs.copy()
        # Crucially: tie-break uses 2025 only; no 2026 NAV/drawdown.
        train=train.sort_values(
            ["positive_months_2025","losing_months_2025","return_2025_pct"],
            ascending=[False,True,False],kind="stable")
    '''+anchor)
        status='        selection_only_on="2025 monthly positive count, then losing count and 2025 return",'
        if status not in s:raise ValueError("Stage18 meta source changed")
        s=s.replace(status,status+'''
        original_2025_qualified_count=original_2025_qualified_count,
        original_2025_gate_met=bool(original_2025_qualified_count),
        unqualified_fallback_selected_for_audit_only=not bool(original_2025_qualified_count),
''')
    if name=="research_trade_counts_stage22.py":
        # Stage20's selected ETH model may differ from a hardcoded BTC
        # momentum model and may use auxiliary weights 10%,15% or 20%.
        # Audit its ACTUAL stored selection from independently generated ETH
        # Stage20 metadata rather than assuming BTC's original 10% blend.
        anchor='S19_MODEL="strong_momentum_6h__4h_adx_le20__3R__480min"'
        if anchor not in s:raise ValueError("Stage22 source model anchor changed")
        s=s.replace(anchor,'''S20_ETH_SELECTED=json.loads((BASE20/"quality.json").read_text())["selected"]
S19_MODEL=str(S20_ETH_SELECTED["stage19_model"])
S20_AUX_WEIGHT=float(S20_ETH_SELECTED["new_pattern_weight"])''')
        formula='expected20=.9*expected18+.1*h_r'
        if formula not in s:raise ValueError("Stage22 fixed BTC weighting anchor missing")
        s=s.replace(formula,
            'expected20=(1.-S20_AUX_WEIGHT)*expected18+S20_AUX_WEIGHT*h_r')
        anchor='stage20_definition="67.5% quiet-volume / 22.5% Daily20 Donchian / 10% 1H strong momentum breakout",'
        s=s.replace(anchor,'stage20_definition=f"Blend {(1-S20_AUX_WEIGHT):.0%} Stage18 baseline / {S20_AUX_WEIGHT:.0%} Stage19 selected model: {S19_MODEL}",')
    return s

def prepare_sources(temp):
    for f in SRC.glob("*.py"):
        (temp/f.name).write_text(patched_source(f.name,f.read_text()))

def result(name,args,workdir,limit):
    source=SRC/name
    target=workdir/name
    original=source.read_text()
    s=patched_source(name,original)
    target.write_text(s)
    env=dict(os.environ)
    env["PYTHONPATH"]=str(workdir)+os.pathsep+str(SRC)
    began=time.monotonic()
    d=dict(script=name,arguments=args,
         original_source_sha256=hashlib.sha256(original.encode()).hexdigest(),
         translated_sha256=hashlib.sha256(s.encode()).hexdigest(),
         status="not-run")
    try:
        cp=subprocess.run([sys.executable,str(target),*args],
                          cwd=str(ROOT),env=env,text=True,
                          capture_output=True,timeout=limit)
        d.update(status="success" if cp.returncode==0 else "failed",
                 returncode=int(cp.returncode),
                 stdout_tail=cp.stdout[-3000:],stderr_tail=cp.stderr[-11000:])
    except subprocess.TimeoutExpired as ex:
        d.update(status="timeout",error="Timeout exceeded "+str(limit)+"s",
                 stdout_tail=str(ex.stdout)[-2000:],stderr_tail=str(ex.stderr)[-3000:])
    except Exception as ex:
        d.update(status="error",error=repr(ex),
                 stderr_tail=traceback.format_exc()[-5000:])
    d["duration_s"]=round(time.monotonic()-began,2)
    print("ETH_RETRY",name,d["status"],d["duration_s"],flush=True)
    if d["status"]!="success":
        print("ETH_RETRY_ERROR",name,d.get("stderr_tail",d.get("error",""))[-1000:],flush=True)
    return d

def target_months_check():
    return [str(x) for x in __import__("pandas").period_range("2025-01","2026-10",freq="M")]

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--part",choices=("chain","calendar"),required=True)
    parser.add_argument("--timeout",type=int,default=620)
    args=parser.parse_args()
    AUDIT.mkdir(parents=True,exist_ok=True)
    norm=prepare()
    if not norm["diagnostic_only_partial_november_2026"]:
        raise RuntimeError("Expected partial Nov data as diagnostics, never as target month")
    if norm["target_months"]!=target_months_check():
        raise RuntimeError("Nov leakage into 22-month ETH score")
    inventory=dict(part=args.part,source="ETHUSD Delta historical, normalized with predeclared Jan2025 anchor",
                   target_months=norm["target_months"],partial_november_for_diagnostics=True,
                   btc_first_open=norm["btc_first_open"],eth_first_open=norm["eth_first_open"],
                   native_eth_point_value_for_btc_200=norm["equivalent_eth_price_points_per_200_btc_index_points"])
    cmds=CHAIN if args.part=="chain" else CALENDAR
    results=[]
    with tempfile.TemporaryDirectory(prefix="eth_fix10_") as tmp:
        workdir=Path(tmp)
        prepare_sources(workdir)
        for name,params,is_target in cmds:
            item=result(name,params,workdir,args.timeout)
            item["was_previous_failure"]=is_target
            results.append(item)
            (AUDIT/f"status_{args.part}.json").write_text(
                json.dumps({**inventory,"scripts":results},indent=2)+"\n")
    # Do not conflate 'script successfully launched' with valid 22-month
    # account performance. Keep source-validated audit outputs and read
    # actual PnL from separately generated monthly tables.
    targeted=[x for x in results if x["was_previous_failure"]]
    stats={
      "originally_failed_scripts_in_part":len(targeted),
      "recovered":sum(x["status"]=="success" for x in targeted),
      "still_failed":sum(x["status"]!="success" for x in targeted),
      "dependencies_run":len(results)-len(targeted),
      "dependencies_failed":[x["script"] for x in results if not x["was_previous_failure"] and x["status"]!="success"],
      "failures":[x["script"] for x in targeted if x["status"]!="success"]
    }
    (AUDIT/f"summary_{args.part}.json").write_text(json.dumps({**inventory,**stats},indent=2)+"\n")
    (AUDIT/f"result_sources_{args.part}.json").write_text(json.dumps([
      dict(path=str(p.relative_to(ROOT)),bytes=p.stat().st_size) for p in sorted(OUTPUT.rglob("*"))
      if p.is_file() and (p.suffix in (".json",".md",".csv") or p.name.endswith(".csv.gz"))
    ],indent=2)+"\n")

    # Save compact ETH-only reports, never any old BTC outputs. Large
    # per-signal ledgers remain reproducible from these scripts and the
    # checked historical market data; don't commit gigabytes to Git.
    import shutil
    for p in sorted(OUTPUT.rglob("*")):
        if not p.is_file() or p.stat().st_size>350_000:continue
        if not (p.suffix in (".json",".md") or p.name in
            ("monthly_results.csv","month_by_month.csv","selected_monthly_results.csv",
             "monthly_blended_returns.csv","selected_month_by_month.csv",
             "monthly_inside_bar_2R_IST.csv","monthly_trade_win_loss_audit.csv",
             "monthly_consistency.csv","period_results.csv","strategy_comparison.csv",
             "selected_monthly_returns.csv","config_comparison.csv",
             "trade_summary.csv","all_scenarios.csv","monthly_mark_to_market.csv")):
            continue
        dest=AUDIT/"excerpts"/args.part/p.relative_to(OUTPUT)
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(p,dest)

    print("ETH_FAILED10_RECOVERY",args.part,json.dumps(stats),flush=True)
    # Don't hide unsuccessful sub-scripts under a green GitHub workflow.
    if stats["still_failed"] or stats["dependencies_failed"]:sys.exit(1)
if __name__=="__main__":main()
