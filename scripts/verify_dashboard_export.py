"""Verify actual produced artifact integrity and bounded page data."""
import json
from pathlib import Path
import math
ROOT=Path("dashboard-dist/data")
def read(p): return json.loads(p.read_text())
def main():
    index=read(ROOT/"index.json")
    runs=index["runs"]
    assert runs and len({r["id"] for r in runs})==len(runs)
    assert index["selection_policy"]["version"]==3 and index["selection_policy"]["excluded"]==0
    catalog=index["catalog"]; evidence=index["legacy_evidence"]
    assert len(catalog)==index["catalog_count"] and len(evidence)==index["legacy_evidence_count"]
    assert len({r["id"] for r in catalog})==len(catalog)
    assert {c["run_id"] for c in catalog if c["run_id"] is not None}=={r["id"] for r in runs}
    assert {c["evidence"]["id"] for c in catalog if c.get("evidence")}=={e["id"] for e in evidence}
    assert all(c["run_id"] is not None or not c["detail_available"] for c in catalog)
    assert len(catalog)==len(runs)+sum(not e.get("replay_id") for e in evidence)
    for c in catalog:
        if c["run_id"] is not None:
            r=next(r for r in runs if r["id"]==c["run_id"])
            assert (c["net"],c["unit"],c["trades"],c["detail_available"])==(r["net"],r["unit"],r["trades"],r.get("detail_available",True))
        else:
            assert c["evidence"]["unit"]==c["unit"]
    assert index["full_configurations"]==sum(r.get("detail_available",True) for r in runs)
    automatic=[r for r in runs if r.get("automatic_version")]
    assert len(automatic)==index.get("automatic_run_count",0)
    registry=index.get("backtest_number_registry",{})
    assert all(type(n) is int and n>0 for n in registry.values())
    assert len(set(registry.values()))==len(registry)
    for r in automatic:
        assert r["backtest_number"]==registry[r["id"]]
        assert r["strategy"]==f'BT-{r["backtest_number"]:04d} | {r["original_strategy"]}'
    assert len({(r["source_run_id"],r["source_attempt"],r["family"],r["variant_key"]) for r in automatic})==len(automatic)
    for k in {(r["symbol"],r["family"],r["variant_key"]) for r in automatic}:
        assert sum(r["latest_version"] for r in automatic if (r["symbol"],r["family"],r["variant_key"])==k)==1
    assert {p.name for p in (ROOT/"runs").iterdir()}=={r["id"] for r in runs}
    eth_source=Path("analysis/ethusd_native_atr_price_action/full_trade_ledger.csv.gz")
    if eth_source.exists():
        assert any(r["symbol"]=="ETHUSD" and r.get("detail_available",True) for r in runs), "ETH artifact exists but no full ETH import"
    for r in runs:
        assert math.isfinite(r["net"])
        declared=r.get("indicator_definitions")
        if declared is not None:
            assert isinstance(declared,list) and len(declared)<=64
            ids=[d["id"] for d in declared]
            assert len(ids)==len(set(ids)) and all(isinstance(i,str) and i for i in ids)
            assert all(isinstance(d["name"],str) and type(d["timeframe_minutes"]) is int and d["timeframe_minutes"]>0 and d["panel"] in ("price","panel") and isinstance(d.get("parameters",{}),dict) for d in declared)
            days=r.get("indicator_days",[])
            assert days==sorted(set(days))
            for day in days:
                series=read(ROOT/"runs"/r["id"]/"indicators"/(day+".json"))
                assert set(series)==set(ids)
                for points in series.values():
                    assert len(points)<=1441
                    assert all(type(p[0]) is int and (p[1] is None or (type(p[1]) in (int,float) and math.isfinite(p[1]))) for p in points)
                    assert all(a[0]<b[0] for a,b in zip(points,points[1:]))
        assert sum(m["trades"] for m in r["months"])==r["trades"]
        assert abs(sum(m["net"] for m in r["months"])-r["net"])<.1
        cv=read(ROOT/"runs"/r["id"]/"curve.json")
        assert len(cv)<=1000 and abs(cv[-1][1]-r["net"])<.01
        if not r.get("detail_available",True): continue
        for m in r["months"]:
            rows=read(ROOT/"runs"/r["id"]/(m["month"]+".json"))
            assert len(rows)==m["trades"]
            assert all(t["entry_utc"]<=t["exit_utc"] and math.isfinite(t["net_points"]) for t in rows)
            assert len({t["id"] for t in rows})==len(rows)
            for t in rows:
                for field in ("indicator_series","indicator_values"):
                    if field not in t:continue
                    assert declared is not None and isinstance(t[field],dict) and set(t[field])<=set(ids)
                    for val in t[field].values():
                        if field=="indicator_values":assert val is None or (type(val) in (int,float) and math.isfinite(val))
                        else:
                            assert isinstance(val,list) and len(val)<=100000
                            assert all(isinstance(p,list) and len(p)==2 and type(p[0]) is int and (p[1] is None or (type(p[1]) in (int,float) and math.isfinite(p[1]))) for p in val)
                            assert all(a[0]<b[0] for a,b in zip(val,val[1:]))
    for symbol,days in index["candle_days"].items():
        assert days==sorted(set(days))
        for day in days:
            p=ROOT/"candles"/symbol/(day+".json")
            rows=read(p)
            assert 0<len(rows)<=1440 and p.stat().st_size<300000
            assert all(rows[i][0]<rows[i+1][0] for i in range(len(rows)-1))
    size=sum(p.stat().st_size for p in ROOT.rglob("*.json"))
    assert size<900*1024**2, size
    print(f"VERIFIED {len(runs)} configurations, {index['full_configurations']} full, {size/1024**2:.1f} MiB")
if __name__=="__main__": main()
