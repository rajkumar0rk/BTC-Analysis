import unittest
import tempfile
import gzip
import json
import os
from pathlib import Path
from fastapi.testclient import TestClient
from btc_analysis.service.api import create_app
from btc_analysis.service.store import Store
from btc_analysis.service.worker import work_once
from btc_analysis.service.historical import GraphStrategy
from btc_analysis.visual import Graph,compile_graph
from btc_analysis.data.store import ingest_delta,sha_file,SOURCE
from test_visual import graph
from test_backtest_engine import cfg,bars,run

TOKEN="z"*40
AUTH={"Authorization":"Bearer "+TOKEN}

class HistoricalTests(unittest.TestCase):
    def test_runtime_matches_generated(self):
        g=Graph.model_validate(graph())
        ns={};exec(compile(compile_graph(g)["source"],"<trusted-test>","exec"),ns)
        data=bars([(100,103,99,102),(102,104,101,103),(103,110,90,103),(103,103,103,103)])
        self.assertEqual(run(cfg(),lambda:GraphStrategy(g),data).scenarios,run(cfg(),ns["VisualStrategy"],data).scenarios)

    def test_real_archive_job(self):
        source=os.environ.get("PLATFORM_TEST_REAL_HISTORY")
        if not source:self.skipTest("actual archive integration is a dedicated CI step")
        self.exercise(Path(source),real=True)

    def test_synthetic_partition_job(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);src=root/"source";src.mkdir();file=src/"2025-01.csv.gz"
            start=1735689600
            with gzip.open(file,"wt") as f:
                f.write("time,open,high,low,close,volume\n")
                for n in range(120):
                    p=100+n%10;f.write(f"{start+n*60},{p},{p+2},{p-1},{p+1},1\n")
            (src/"manifest.json").write_text(json.dumps(dict(source=SOURCE,symbol="BTCUSD",resolution="1m",timestamp_unit="unix_seconds_utc",
                partitions=[dict(file=file.name,utc_start="2025-01-01T00:00:00+00:00",utc_end_exclusive="2025-01-01T02:00:00+00:00",
                    expected_minutes=120,observed_candles=120,missing_minutes=0,sha256_gzip=sha_file(file))])))
            ingest_delta(src,root/"history","BTCUSD")
            self.exercise(root/"history")

    def exercise(self,history,real=False):
        with tempfile.TemporaryDirectory() as d:
            db=Path(d)/"db.sqlite"
            with TestClient(create_app(db,{"owner":TOKEN,"other":"y"*40},history)) as client:
                datasets=client.get("/v1/datasets",headers=AUTH).json()
                data=next(x for x in datasets if x["symbol"]=="BTCUSD")
                self.assertTrue(client.get("/v1/capabilities",headers=AUTH).json()["historical_runs"])
                c=compile_graph(Graph.model_validate(graph()))
                r=client.post("/v1/strategies",headers=AUTH,json={"name":"visual","source":c["source"]}).json()
                start=data["start"]
                body=dict(kind="historical_visual",strategy_id=r["id"],version=1,symbol="BTCUSD",manifest_sha256=data["manifest_sha256"],
                          start=start,end=start+60*60,assume_open=True,acknowledge_reference=True)
                def submit(payload,key="job",auth=AUTH):
                    return client.post("/v1/jobs/historical",headers={**auth,"Idempotency-Key":key},json=payload)
                self.assertEqual(submit({**body,"assume_open":False},"strict").status_code,422)
                self.assertEqual(submit(body,"other",{"Authorization":"Bearer "+"y"*40}).status_code,404)
                job=submit(body);self.assertEqual(job.status_code,202,job.text)
                jid=job.json()["id"]
                self.assertEqual(submit(body).json()["id"],jid)
                self.assertTrue(work_once(Store(db),history_root=history))
                result=client.get("/v1/jobs/"+jid,headers=AUTH).json()
                self.assertEqual(result["status"],"succeeded",result)
                self.assertFalse(result["result"]["synthetic"])
                self.assertTrue(result["result"]["research_only"])
                self.assertFalse(result["result"]["timestamp_label_verified"])
                self.assertEqual(result["result"]["dataset_manifest_sha256"],data["manifest_sha256"])
                self.assertEqual(result["result"]["result"]["scenarios"][0]["bars"],60)
                if real:print("Actual BTCUSD archive job result hash:",result["result"]["result_sha256"])

if __name__=="__main__":unittest.main()
