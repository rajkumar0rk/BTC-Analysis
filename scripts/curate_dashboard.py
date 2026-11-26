"""Publish one eligible full-replay configuration per comparable signal family.
Frozen summaries are separate; no inferred ledger or approval.
The current comparison period is the 22 completed historical months Jan25-Oct26.
"""
import json, shutil
from pathlib import Path
from dashboard_archive import dump
MONTHS=[f"{y}-{m:02d}" for y in (2025,2026) for m in range(1,13) if y==2025 or m<=10]
def select(runs):
    best={}; reasons={}
    for r in runs:
        monthly={m["month"]:m["net"] for m in r["months"]}
        values=[monthly.get(m,0) for m in MONTHS]
        if r["net"]<=0 or sum(values)<=0 or (r.get("profit_factor") or 0)<=1:
            reasons[r["id"]]="Nonpositive net or PF <= 1";continue
        if r.get("detail_available",True) is False:
            reasons[r["id"]]="No full replay";continue
        # Group by economic signal pattern, not parameter variations.
        family=(r["symbol"],r["source"],r["strategy"].split("|",1)[0].split(" / mult=",1)[0])
        rank=(sum(v>0 for v in values),sum(values),r["profit_factor"],-r["drawdown"],r["id"])
        if family not in best or rank>best[family][0]:
            if family in best:reasons[best[family][1]["id"]]="Lower-ranked parameter variant"
            best[family]=(rank,r)
        else:reasons[r["id"]]="Lower-ranked parameter variant"
    return [v[1] for _,v in sorted(best.items())],reasons
def curate(root,out):
    data=out/"data"
    index=json.loads((data/"index.json").read_text())
    all_runs=index["runs"]
    chosen,reasons=select(all_runs)
    if not chosen:raise ValueError("No eligible replay configurations; keep last valid publication")
    keep={r["id"] for r in chosen}
    for r in all_runs:
        if r["id"] not in keep:shutil.rmtree(data/"runs"/r["id"])
    index["runs"]=chosen
    index["full_configurations"]=len(chosen)
    index["archive_configurations"]=sum(r.get("audit")!="execution-time" for r in chosen)
    index["selection_policy"]={"version":1,"window":"2025-01–2026-10 (entry month UTC; descriptive only)","before":len(all_runs),"retained":len(chosen),"excluded":len(all_runs)-len(chosen),"method":"Positive total and completed-window net; PF > 1; full replay; one per signal family ranked by profitable months then net, PF and drawdown."}
    dump(data/"index.json",index)
    frozen=json.loads((root/"dashboard/frozen-strategies.json").read_text())
    dump(data/"frozen.json",frozen)
    coverage=json.loads((data/"coverage.json").read_text())
    coverage.append(dict(path="dashboard/frozen-strategies.json",status=f"Curated {len(chosen)} of {len(all_runs)} configurations; {len(frozen)} frozen summaries separate"))
    dump(data/"coverage.json",coverage)
    print(f"CURATED {len(chosen)} of {len(all_runs)} replay configurations; {len(frozen)} frozen summaries")
