"""Unified catalog. Migrate previously verified archives, never rerun or infer trades.
The previous published snapshot supplies historical evidence once; later
publications carry forward the same generic records and immutable source links.
"""
import json
import shutil
from pathlib import Path
from dashboard_archive import dump

def read(path):return json.loads(path.read_text())

def legacy_evidence(previous,old):
    if "legacy_evidence" in old:return old["legacy_evidence"]
    # One-time compatibility migration of the two previous serialized feeds.
    # The inputs are data, not strategy declarations or selection rules.
    result=[]
    for filename in ("frozen.json","supertrend.json"):
        path=previous/filename
        if not path.is_file():raise ValueError("Verified legacy snapshot missing "+filename)
        for raw in read(path):
            r=dict(raw)
            if "net_usd_min" in r:
                r.update(unit="account USD",source=f"https://github.com/rajkumar0rk/BTC-Analysis/blob/{r['sha']}/{r['path']}",frozen=True)
            else:r["frozen"]=str(r.get("status","")).upper()=="LOCKED" or str(r.get("status","")).lower().startswith("frozen ")
            # All rows in the old feeds referred to the archived BTC research.
            r.setdefault("symbol","BTCUSD");result.append(r)
    return result

def migrate(data,previous):
    data,previous=Path(data),Path(previous)
    idx=read(data/"index.json");old=read(previous/"index.json")
    evidence=legacy_evidence(previous,old)
    rows={r["id"]:r for r in idx["runs"]}
    for r in old["runs"]:
        if r.get("automatic_version"):continue
        existing=rows.get(r["id"])
        if existing is not None and (existing.get("detail_available",True) or not r.get("detail_available",True)):continue
        source=previous/"runs"/r["id"];dest=data/"runs"/r["id"]
        if not source.is_dir():raise ValueError("Historical replay missing "+r["id"])
        if dest.exists():shutil.rmtree(dest)
        shutil.copytree(source,dest)
        rows[r["id"]]=r
    idx["runs"]=list(rows.values())
    idx["legacy_evidence"]=evidence
    # Compatibility for the previous deployed UI during the transition only.
    for filename in ("frozen.json","supertrend.json"):
        if (previous/filename).is_file():shutil.copyfile(previous/filename,data/filename)
    idx["supertrend_replay_count"]=sum(bool(r.get("research_reference")) for r in idx["runs"])
    count=len(idx["runs"])-idx["supertrend_replay_count"]
    idx["selection_policy"]={"version":3,"before":count,"retained":count,"excluded":0,"method":"All available archive configurations; no profitability or rank exclusion"}
    idx["full_configurations"]=sum(r.get("detail_available",True) for r in idx["runs"])
    dump(data/"index.json",idx)

def build_catalog(data):
    data=Path(data);idx=read(data/"index.json");evidence=idx.get("legacy_evidence",[])
    by_replay={e["replay_id"]:e for e in evidence if e.get("replay_id")}
    ids={r["id"] for r in idx["runs"]}
    if not set(by_replay)<=ids:raise ValueError("Historical evidence would lose its replay")
    catalog=[]
    for r in idx["runs"]:
        e=by_replay.get(r["id"])
        auto=bool(r.get("automatic_version"))
        status=e.get("status") if e else r.get("status") or ("Published research" if auto else "Archived research")
        # Source accounting may differ from entry-month realized totals.
        row=dict(id=r["id"],run_id=r["id"],strategy=r["strategy"],symbol=r["symbol"],unit=r["unit"],net=r["net"],trades=r["trades"],status=status,frozen=bool(e and e.get("frozen") or r.get("frozen")),version=("latest" if r.get("latest_version") else "previous") if auto else "archived",detail_available=r.get("detail_available",True),source=r.get("source"),source_run_id=r.get("source_run_id"),source_attempt=r.get("source_attempt"),completed_at=r.get("completed_at"),signal_timeframe_minutes=r.get("signal_timeframe_minutes"),execution_timeframe_minutes=r.get("execution_timeframe_minutes"),period=(e or {}).get("window") or ((r["months"][0]["month"]+" – "+r["months"][-1]["month"]) if r.get("months") else None),evidence=e,source_summary=r.get("source_summary"))
        catalog.append(row)
    for e in evidence:
        if e.get("replay_id"):continue
        catalog.append(dict(id="summary:"+e["id"],run_id=None,strategy=e["name"],symbol=e["symbol"],unit=e["unit"],net=e.get("net"),net_min=e.get("net_usd_min"),net_max=e.get("net_usd_max"),trades=e.get("trades"),status=e.get("status"),frozen=bool(e.get("frozen")),version="archived",detail_available=False,source=e.get("source"),period=e.get("window"),evidence=e))
    if len({r["id"] for r in catalog})!=len(catalog):raise ValueError("Duplicate catalog identities")
    idx["catalog"]=catalog;idx["catalog_count"]=len(catalog)
    idx["legacy_evidence_count"]=len(evidence)
    dump(data/"index.json",idx)
    print("Unified catalog:",len(catalog),"entries;",len(evidence),"historical evidence records preserved")
