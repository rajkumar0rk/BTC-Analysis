import unittest
import tempfile
import json
import sqlite3
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient
from btc_analysis.service.api import create_app
from btc_analysis.service.store import Store,Conflict
from btc_analysis.service.worker import work_once

A="a"*40;B="b"*40
def auth(t=A):return {"Authorization":"Bearer "+t}
def jobheaders(key="job",t=A):return {**auth(t),"Idempotency-Key":key}

class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/"queue.sqlite"
        self.store=Store(self.path)
        self.client=TestClient(create_app(self.path,{"alice":A,"bob":B}))
        self.addCleanup(self.client.close)

    def submit(self,key="job",t=A,body=None):
        return self.client.post("/v1/jobs",headers=jobheaders(key,t),json=body or {"bars":60,"signal_minutes":5})

    def test_auth_required(self):
        self.assertEqual(self.client.get("/v1/jobs").status_code,401)
        self.assertEqual(self.client.get("/v1/jobs",headers=auth("bad")).status_code,401)
        self.assertEqual(self.client.get("/health").json()["custom_python_execution"],False)
        self.assertEqual(self.client.get("/v1/capabilities",headers=auth()).json()["historical_runs"],False)
        self.assertEqual(self.client.get("/v1/jobs",headers=auth()).headers["Cache-Control"],"no-store")

    def test_revision_ownership_and_inert_source(self):
        source="raise RuntimeError('must never execute')"
        r=self.client.post("/v1/strategies",headers=auth(),json={"name":"test","source":source})
        self.assertEqual(r.status_code,201);s=r.json();sid=s["id"]
        self.assertEqual(self.client.get(f"/v1/strategies/{sid}/versions/1",headers=auth(B)).status_code,404)
        self.assertEqual(self.client.get("/v1/strategies",headers=auth(B)).json(),[])
        r=self.client.post(f"/v1/strategies/{sid}/versions",headers=auth(),json={"source":"pass","expected_version":1})
        self.assertEqual(r.status_code,201);self.assertEqual(r.json()["version"],2)
        self.assertEqual(self.client.get(f"/v1/strategies/{sid}/versions/1",headers=auth()).json()["source"],source)
        r=self.client.post(f"/v1/strategies/{sid}/versions",headers=auth(),json={"source":"pass","expected_version":1})
        self.assertEqual(r.status_code,409)

    def test_idempotent_submit_and_owner(self):
        a=self.submit();b=self.submit()
        self.assertEqual(a.status_code,202);self.assertEqual(a.json()["id"],b.json()["id"])
        jid=a.json()["id"]
        self.assertEqual(self.submit(body={"bars":120,"signal_minutes":5}).status_code,409)
        self.assertEqual(self.client.get(f"/v1/jobs/{jid}",headers=auth(B)).status_code,404)
        self.assertEqual(self.client.post(f"/v1/jobs/{jid}/cancel",headers=auth(B)).status_code,404)
        self.assertNotEqual(self.submit(t=B).json()["id"],jid)

    def test_custom_job_and_unknown_fields_rejected(self):
        for body in ({"kind":"python","source":"print(1)"},{"bars":601},{"bars":True},{"bars":61,"signal_minutes":5},
                     {"bars":60,"strategy_id":"untrusted"}):
            self.assertEqual(self.submit(body=body).status_code,422)

    def test_body_limit(self):
        r=self.client.post("/v1/strategies",headers=auth(),json={"name":"x","source":"x"*110000})
        self.assertEqual(r.status_code,413)

    def test_queue_cancel(self):
        jid=self.submit().json()["id"]
        r=self.client.post(f"/v1/jobs/{jid}/cancel",headers=auth())
        self.assertEqual(r.json()["status"],"cancelled")
        self.assertIsNone(self.store.claim())

    def test_running_cancel_wins_finish(self):
        jid=self.submit().json()["id"];j,token,p=self.store.claim()
        self.assertEqual(j,jid)
        self.assertTrue(self.store.heartbeat(j,token,40))
        self.assertTrue(self.store.heartbeat(j,token,10))
        self.assertEqual(self.store.job("alice",j)["progress"],40)
        self.store.cancel("alice",j)
        self.assertFalse(self.store.heartbeat(j,token,50))
        self.assertTrue(self.store.finish(j,token,result={"ignored":True}))
        self.assertEqual(self.store.job("alice",j)["status"],"cancelled")
        self.assertIsNone(self.store.job("alice",j)["result"])

    def test_claim_concurrency_and_stale_lease(self):
        self.submit("a");self.submit("b")
        with ThreadPoolExecutor(max_workers=2) as pool:
            claims=list(pool.map(lambda _:self.store.claim(),range(2)))
        self.assertEqual(sum(x is not None for x in claims),1)
        j,token,p=next(x for x in claims if x is not None)
        with self.store.connection(True) as c:c.execute("UPDATE jobs SET lease_until=0 WHERE id=?",(j,))
        self.assertFalse(self.store.finish(j,token,result={"stale":True}))
        self.assertIsNotNone(self.store.claim())
        self.assertEqual(self.store.job("alice",j)["error"],"worker_lease_expired")

    def test_active_quota(self):
        for i in range(8):self.assertEqual(self.submit(str(i)).status_code,202)
        self.assertEqual(self.submit("overflow").status_code,409)

    def test_worker_end_to_end_and_persistence(self):
        jid=self.submit().json()["id"]
        self.assertTrue(work_once(self.store))
        r=self.client.get(f"/v1/jobs/{jid}",headers=auth()).json()
        self.assertEqual(r["status"],"succeeded",r)
        self.assertEqual(r["progress"],100);self.assertTrue(r["result"]["synthetic"])
        self.assertEqual(len(r["result"]["result_sha256"]),64)
        self.assertEqual(Store(self.path).job("alice",jid),r)
        self.assertFalse(work_once(self.store))

if __name__=="__main__":unittest.main()
