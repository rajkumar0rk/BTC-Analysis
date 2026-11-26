"""Verify actual produced artifact integrity and bounded page data."""
import json
from pathlib import Path
import math
ROOT=Path("dashboard-dist/data")
def read(p): return json.loads(p.read_text())
def main():
    index=read(ROOT/"index.json")
    runs=index["runs"]
    assert len(runs)>=30 and len({r["id"] for r in runs})==len(runs)
    assert any(r["symbol"]=="BTCUSD" for r in runs)
    eth_source=Path("analysis/ethusd_native_atr_price_action/full_trade_ledger.csv.gz")
    if eth_source.exists():
        assert any(r["symbol"]=="ETHUSD" and r.get("detail_available",True) for r in runs), "ETH artifact exists but no full ETH import"
    for r in runs:
        assert math.isfinite(r["net"])
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
