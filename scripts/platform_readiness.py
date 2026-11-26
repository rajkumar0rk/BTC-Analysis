"""Bounded service smoke/latency report, not production load certification."""
import argparse,json,resource,statistics,tempfile,time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient
from btc_analysis.service.api import create_app
from btc_analysis.service.store import Store
from btc_analysis.service.worker import work_once
from btc_analysis.service.backup import backup,restore

def run():
    with tempfile.TemporaryDirectory() as d:
        p=Path(d);db=p/"bench.sqlite";token="x"*48;auth={"Authorization":"Bearer "+token}
        with TestClient(create_app(db,{"bench":token})) as c:
            def request(_):
                t=time.perf_counter();r=c.get("/v1/jobs",headers=auth);dt=time.perf_counter()-t
                if r.status_code!=200:raise RuntimeError("API request failed")
                return dt*1000
            t=time.perf_counter()
            with ThreadPoolExecutor(max_workers=4) as pool:latencies=sorted(pool.map(request,range(100)))
            elapsed=time.perf_counter()-t
            j=c.post("/v1/jobs",headers={**auth,"Idempotency-Key":"benchmark"},json={"bars":600,"signal_minutes":5})
            j.raise_for_status();jid=j.json()["id"]
            t=time.perf_counter();assert work_once(Store(db));worker=time.perf_counter()-t
            out=c.get("/v1/jobs/"+jid,headers=auth).json()
            assert out["status"]=="succeeded" and out["result"]["synthetic"] is True
            b=backup(db,p/"backup.sqlite");restore(p/"backup.sqlite",p/"restore.sqlite",b["sha256"])
            assert Store(p/"restore.sqlite").job("bench",jid)==out
            return {"scope":"local synthetic smoke, four concurrent threads, not network load test",
                "requests":len(latencies),"errors":0,"elapsed_seconds":round(elapsed,4),
                "median_ms":round(statistics.median(latencies),3),"p95_ms":round(latencies[94],3),
                "max_ms":round(latencies[-1],3),"fixture_600_bars_seconds":round(worker,4),
                "process_peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                "child_peak_rss_kib":resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
                "backup_restore":"pass","custom_python_execution":False,"production_approved":False}

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--output",required=True);a=p.parse_args()
    result=run();Path(a.output).write_text(json.dumps(result,indent=2)+"\n");print(json.dumps(result,indent=2))
