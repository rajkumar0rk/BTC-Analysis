#!/usr/bin/env python3
"""Aggregate repaired ETH scripts, separating process success from strategy profitability."""
from pathlib import Path
import json
from collections import Counter
R=Path("analysis/eth_failed10_recovery")
EXPECTED={
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
def main():
    parts={}
    for name in ("chain","calendar"):
        path=R/f"status_{name}.json"
        if path.exists():parts[name]=json.loads(path.read_text())
    allruns=[dict(row,part=part) for part,payload in parts.items() for row in payload["scripts"]]
    target=[x for x in allruns if x["script"] in EXPECTED]
    seen=Counter(x["script"] for x in target)
    duplicates={k:v for k,v in seen.items() if v>1}
    missing=sorted(EXPECTED-set(seen))
    recovered=sorted(x["script"] for x in target if x["status"]=="success")
    failures=[dict(script=x["script"],status=x["status"],
                    error=x.get("error") or x.get("stderr_tail","")[-900:])
              for x in target if x["status"]!="success"]
    dependencies=[dict(script=x["script"],status=x["status"]) for x in allruns if x["script"] not in EXPECTED]
    payload=dict(
        market="ETHUSD Delta Exchange India original 1m",
        original_failed_script_total=10,attempted=len(target),
        verified_rerun_success=len(recovered),still_unresolved=len(failures),
        missing_targets=missing,duplicate_target_attempts=duplicates,
        dependencies=dependencies,
        target_months=[str(x) for x in __import__("pandas").period_range("2025-01","2026-10",freq="M")],
        include_partial_november_2026_for_original_diagnostic_splits=True,
        exclude_partial_november_from_profitable_month_target=True,
        current_status="ALL_10_RERUN_SUCCESS" if len(recovered)==10 and not missing and not duplicates else "PARTIAL_OR_BLOCKED",
        earlier_btc_results_used_as_inputs=False,
        original_source_modified_in_main=False,
        fixed_point_conversion="ETH OHLC translated to constant Jan2025 BTC price-index units for original BTC-model point distance sensitivity",
        caveats=[
          "Original research variants can overlap, and each script may have many distinct models",
          "Script executed successfully != every monthly return is positive",
          "Stages 12 and 22 use fresh ETH source counts rather than hardcoded BTC counts; model entry/exit code unchanged",
          "Portfolio variants are not proved valid until ledger reconciliations pass",
          "Native ETH portfolio margin, funding and real-world bid/ask are not independently verified",
          "2026 November is only a partial diagnostics period; target ends October 2026"
        ],
        failures=failures,successful_scripts=recovered)
    R.mkdir(parents=True,exist_ok=True)
    (R/"FINAL_STATUS.json").write_text(json.dumps(payload,indent=2)+"\n")
    lines=["# ETHUSD failed-script recovery audit","",
      "**"+payload["current_status"]+"**","",
      f"Originally blocked scripts: **10**. Recovered and successfully rerun: **{len(recovered)}**.",
      f"Still failed: **{len(failures)}**. Missing: **{len(missing)}**.","",
      "## Each script's status","",
      "| Script | Status | Part |",
      "|:--|:--|:--|"]
    for name in sorted(EXPECTED):
        x=next((r for r in target if r["script"]==name),None)
        lines.append(f"| {name} | {x['status'] if x else 'NOT RUN'} | {x['part'] if x else '-'} |")
    lines.extend(["","## Remaining failures",""])
    for x in failures:lines.append(f"- {x['script']}: {x['status']}, {x['error'][-300:]}")
    lines.extend(["","## Method","",
      "Each strategy still uses its original entry and exit source rules.",
      "Only ETH market mapping, diagnostic sample coverage, required artifact paths,",
      "and historical BTC-only fixed count expectations were adjusted.",
      "Upstream stage ledgers are generated fresh from ETH, not copied from BTC.",
      "No previous BTC data analysis or schedules modified.",
      "The successful ETH raw native 205-model cross-family audit resides separately",
      "on the source branch: analysis/eth_native_crossfamily_v2.",
      "A process-complete audit does not imply any strategy achieves 22/22 months profitable.",
      "NOV 2026 source is partial and excluded from every 22-month target."
    ])
    (R/"RESEARCH_REPORT.md").write_text("\n".join(lines)+"\n")
    print(json.dumps({k:payload[k] for k in ("current_status","attempted","verified_rerun_success","still_unresolved","missing_targets")},indent=2))
if __name__=="__main__":main()
