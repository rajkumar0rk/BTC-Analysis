#!/usr/bin/env python3
"""Merge independent ETH cross-market research experiment status/artifacts."""
from pathlib import Path
import json
OUT=Path("analysis/eth_all_validation")
def main():
    runs=[]
    for f in sorted(OUT.glob("status_*.json")):
        j=json.loads(f.read_text())
        for z in j["runs"]:
            runs.append(dict(z,group=j["group"]))
    if not runs:raise RuntimeError("Missing all ETH statuses")
    n_ok=sum(x["status"]=="success" for x in runs)
    n_failed=len(runs)-n_ok
    report={
      "instrument":"ETHUSD Delta Exchange India perpetual futures",
      "scope":"Source-based ETH translation of prior BTC-Analysis strategies, original rules kept unchanged",
      "source_history":"Main branch ETHUSD 1m compressed Delta public API 2025-01 through 2026-10",
      "all_groups_reported":sorted(set(x["group"] for x in runs)),
      "strategy_scripts_attempted":len(runs),
      "completed_successfully":n_ok,
      "not_completed":n_failed,
      "statuses":[{"script":x["script"],"group":x["group"],"status":x["status"],
                    "run_time_seconds":x.get("run_time_seconds"),
                    "error":x.get("error"),
                    "stderr_tail":x.get("stderr_tail","")[-1200:]} for x in runs],
      "important":"Completed script execution is not equivalent to positive 22/22 monthly returns. Many existing scripts are descriptive market studies, account portfolio dependencies, or BTC point-target models with nontransferable absolute thresholds.",
      "fees":"Original code fee, GST and slippage constants unchanged. Exact ETH execution costs may differ. Full bid/ask, funding, impact, lot/margin are not assured.",
      "source_transfer":"Only textual BTCUSD->ETHUSD market path and isolated analysis output remapping; original trade signal and numeric thresholds unchanged; no BTC result files consulted.",
      "recheck":"Full UTC Jan25-Oct26 1m data complete, but Jan 2025 first 5.5 IST hours absent and 2026 history previously analyzed. In-sample historical results do not guarantee returns.",
      "btc_stage26_crossmarket":"A separate completed ETH audit exists on research/eth-stage26-crossmarket; not counted among main research scripts.",
      "nov25_status":"November 2026 incomplete; excluded from 22-month profitability gate."
    }
    (OUT/"TOTAL_SUMMARY.json").write_text(json.dumps(report,indent=2)+"\n")
    lines=["# ETHUSD — cross-market replay of existing BTC strategy code","",
      "**This test is independent of the BTC results and scheduled research tasks.**",
      "ETH 1-minute files from main were SHA-256 checked. The runner translated",
      "original source market paths and report paths while keeping signal logic",
      "and absolute numeric parameters unchanged. The original BTC-to-ETH 5-point",
      "slippage and price-point thresholds **may not be economically suitable for ETH**.","",
      f"**Main-branch research scripts attempted: {len(runs)}. Completed successfully: {n_ok}. Not completed: {n_failed}.**",
      "",
      "Success here means the script executed, not that it achieved positive monthly returns.",
      "Do not assume every script produces a 22-row after-cost compounded account-return series.",
      "",
      "## Script execution audit","",
      "| Script | Group | Execution | Notes |",
      "|:--|:--|:--|:--|"]
    for row in runs:
        note=row.get("error") or row.get("stderr_tail","").splitlines()[-1:] or [""]
        if isinstance(note,list):note=" ".join(note)
        note=str(note).replace("|","/").replace("\n"," ")[:140]
        lines.append(f"| {row['script']} | {row['group']} | {row['status']} | {note} |")
    lines.extend(["","## Method and limitations","",
       "- Entirely new ETH market data, not BTC trade ledgers or BTC fitted monthly results.",
       "- Original absolute stops and profit points were left alone. Their scale may be inappropriate for ETH.",
       "- Market scans, distribution reports, and audits are not automatically executable trading strategies.",
       "- Scripts with data dependencies may fail rather than silently consume old BTC strategy result files.",
       "- All 22 target months are Jan 2025–Oct 2026; incomplete November 2026 is excluded.",
       "- Funding, actual bid/ask, contract precision, liquidation, and spread are not independently verified.",
       "- Until independently audited 22-month net account returns are available, never claim 22/22 profitability.",
       "- Stage24/25 research-branch strategies and Stage26 are handled in additional independent cross-market evaluations.",
       "",
       "## Detailed outputs","",
       "Small report excerpts and source checks are inside analysis/eth_all_validation/excerpts/.",
       "Original full trade ledgers are generated ephemerally by GitHub Actions; use the exact script and",
       "original ETH market data to reproduce them. GitHub Actions artifact retention is not permanent.",
       ])
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(lines)+"\n")
    print("ETH_TOTAL",len(runs),"SUCCESS",n_ok,"INCOMPLETE",n_failed)
if __name__=="__main__":main()
