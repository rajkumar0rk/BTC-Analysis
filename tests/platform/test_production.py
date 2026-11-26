import tempfile
import unittest
import os
import asyncio
from pathlib import Path
from fastapi.testclient import TestClient
from btc_analysis.service.api import create_app,BodyLimit
from btc_analysis.service.store import Store
from btc_analysis.service.paper import PaperStore,PaperRequest
from btc_analysis.service.backup import backup,restore
from btc_analysis.service.worker import work_once
from btc_analysis.execution_policy import execute_custom_strategy
from btc_analysis.visual import Graph,compile_graph
from test_visual import graph

class ProductionTests(unittest.TestCase):
    def test_backup_restore_and_fencing(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);s=Store(p/"live.sqlite");paper=PaperStore(s)
            r=s.create_strategy("owner","frozen",compile_graph(Graph.model_validate(graph()))["source"])
            s.transition("owner",r["id"],"freeze",0,1)
            session=paper.create("owner","paper",PaperRequest(strategy_id=r["id"],version=1,symbol="BTCUSD",duration_minutes=4,acknowledge_assumptions=True))
            done=s.submit("owner","done",{"kind":"reference_fixture","bars":60,"signal_minutes":5})
            self.assertTrue(work_once(s));original=s.job("owner",done["id"])
            s.submit("owner","running",{"kind":"reference_fixture","bars":60,"signal_minutes":5})
            j,token,_=s.claim()
            queued=s.submit("owner","queued",{"kind":"reference_fixture","bars":60,"signal_minutes":5})
            b=backup(s.path,p/"backup.sqlite")
            self.assertEqual(os.stat(p/"backup.sqlite").st_mode&0o777,0o600)
            with self.assertRaises((ValueError,FileExistsError)):backup(s.path,p/"backup.sqlite")
            with self.assertRaises(ValueError):restore(p/"backup.sqlite",p/"bad.sqlite","0"*64)
            result=restore(p/"backup.sqlite",p/"recovered.sqlite",b["sha256"])
            self.assertFalse(result["active_work_resumed"])
            recovered=Store(p/"recovered.sqlite")
            self.assertEqual(recovered.job("owner",done["id"]),original)
            self.assertEqual(recovered.revision("owner",r["id"],1)["code_sha256"],r["code_sha256"])
            self.assertEqual(recovered.job("owner",j)["status"],"failed")
            self.assertEqual(recovered.job("owner",queued["id"])["status"],"cancelled")
            self.assertFalse(recovered.finish(j,token,result={"stale":True}))
            self.assertIsNone(recovered.claim())
            self.assertEqual(PaperStore(recovered).get("owner",session["id"])["status"],"halted")
            self.assertEqual(s.job("owner",j)["status"],"running")
            self.assertEqual(paper.get("owner",session["id"])["status"],"scheduled")
    def test_security_headers_and_redaction(self):
        with tempfile.TemporaryDirectory() as d,TestClient(create_app(Path(d)/"db.sqlite",{"owner":"a"*40})) as c:
            a={"Authorization":"Bearer "+"a"*40}
            secret="do_not_echo_this_source"
            r=c.post("/v1/jobs",headers={**a,"Idempotency-Key":"x"},json={"kind":secret})
            self.assertEqual(r.status_code,422);self.assertNotIn(secret,r.text)
            self.assertEqual(r.headers["X-Frame-Options"],"DENY")
            self.assertEqual(r.headers["Cross-Origin-Resource-Policy"],"same-origin")
            self.assertEqual(r.headers["Cache-Control"],"no-store")
            self.assertEqual(c.post("/v1/jobs",headers={**a,"Idempotency-Key":"x"},json={"kind":"custom_python","source":"pass"}).status_code,422)
            with self.assertRaises(NotImplementedError):execute_custom_strategy("pass")
    def test_fragmented_body(self):
        async def test():
            sent=[]
            async def downstream(*_):self.fail("body reached application")
            async def receive():return {"type":"http.request","body":b"","more_body":True}
            async def send(message):sent.append(message)
            await BodyLimit(downstream)({"type":"http","method":"POST","headers":[]},receive,send)
            self.assertEqual(sent[0]["status"],413)
        asyncio.run(test())
