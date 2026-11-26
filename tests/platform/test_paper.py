import unittest
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
from btc_analysis.service.store import Store,Conflict
from btc_analysis.service.api import create_app
from btc_analysis.service.paper import PaperStore,PaperRequest,poll_once
from btc_analysis.visual import Graph,compile_graph
from test_visual import graph

class PaperTests(unittest.TestCase):
    def setUp(self):
        d=tempfile.TemporaryDirectory();self.addCleanup(d.cleanup)
        self.store=Store(Path(d.name)/"db.sqlite");self.paper=PaperStore(self.store)
        self.strategy=self.store.create_strategy("owner","paper",compile_graph(Graph.model_validate(graph()))["source"])
        self.req=PaperRequest(strategy_id=self.strategy["id"],version=1,symbol="BTCUSD",duration_minutes=4,acknowledge_assumptions=True)
    def freeze(self):
        self.store.transition("owner",self.strategy["id"],"freeze",0,1)
    def test_forward_capture_and_restart(self):
        with self.assertRaises(Conflict):self.paper.create("owner","first",self.req,clock=1735689600)
        self.freeze();s=self.paper.create("owner","first",self.req,clock=1735689600)
        self.assertEqual(s["start"],1735689660)
        self.assertEqual(self.paper.create("owner","first",self.req,clock=1735689700)["id"],s["id"])
        def fetch(symbol,t):
            self.assertEqual(symbol,"BTCUSD")
            return dict(time=t,open="102",high="104",low="101",close="103",volume="1")
        poll_once(self.paper,fetch,lambda:s["start"]+60)
        self.assertEqual(self.paper.get("owner",s["id"])["cursor"],s["start"])
        for i in range(4):
            paper=PaperStore(Store(self.store.path))
            poll_once(paper,fetch,lambda:s["start"]+(i+1)*60+10)
        result=self.paper.get("owner",s["id"])
        self.assertEqual(result["status"],"completed",result)
        self.assertEqual(result["cursor"],s["end"])
        self.assertEqual(len(result["checkpoint"]["scenarios"]),2)
        self.assertFalse(result["live_order_submission"])
    def test_stale_and_stop_fence(self):
        self.freeze();s=self.paper.create("owner","first",self.req,clock=1735689600)
        poll_once(self.paper,lambda *_:self.fail("must not fetch stale candle"),lambda:s["start"]+181)
        self.assertEqual(self.paper.get("owner",s["id"])["status"],"halted")
        s=self.paper.create("owner","second",self.req,clock=1735689900)
        row=self.paper.active()[0];self.paper.stop("owner",s["id"])
        self.assertFalse(self.paper.advance(row,dict(time=s["start"],open="102",high="104",low="101",close="103",volume="1"),s["start"]+70))
    def test_api_ownership(self):
        self.freeze()
        with TestClient(create_app(self.store.path,{"owner":"a"*40,"other":"b"*40})) as c:
            a={"Authorization":"Bearer "+"a"*40,"Idempotency-Key":"paper"}
            b={"Authorization":"Bearer "+"b"*40}
            s=c.post("/v1/paper",headers=a,json=self.req.model_dump())
            self.assertEqual(s.status_code,201,s.text);sid=s.json()["id"]
            self.assertEqual(c.get("/v1/paper/"+sid,headers=b).status_code,404)
            self.assertEqual(c.post("/v1/paper/"+sid+"/stop",headers=b).status_code,404)
            self.assertEqual(c.get("/v1/paper",headers=b).json(),[])
            self.assertEqual(c.post("/v1/paper/"+sid+"/stop",headers=a).json()["status"],"stopped")
