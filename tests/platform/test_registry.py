import unittest
import sqlite3
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
from btc_analysis.service.api import create_app
from btc_analysis.service.store import Store,Conflict

A={"Authorization":"Bearer "+"a"*40}
B={"Authorization":"Bearer "+"b"*40}

class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/"db.sqlite"
        self.store=Store(self.path)
        self.client=TestClient(create_app(self.path,{"alice":"a"*40,"bob":"b"*40}))
        self.addCleanup(self.client.close)
        self.a=self.store.create_strategy("alice","original","pass")
        self.sid=self.a["id"]
        self.url="/v1/strategies/"+self.sid
    def post(self,route,body,headers=A):return self.client.post(self.url+route,headers=headers,json=body)
    def transition(self,action,state,version,headers=A):
        return self.post("/state",{"action":action,"expected_state":state,"expected_version":version},headers)

    def test_freeze_archive_restore_clone_and_owner(self):
        r=self.store.add_revision("alice",self.sid,"x=1",1)
        self.assertEqual(self.transition("freeze",0,1).status_code,409)
        self.assertEqual(self.transition("freeze",0,2,B).status_code,404)
        f=self.transition("freeze",0,2)
        self.assertEqual(f.status_code,200);self.assertEqual(f.json()["frozen_version"],2)
        self.assertEqual(self.post("/versions",{"source":"x=2","expected_version":2}).status_code,409)
        self.assertEqual(self.transition("archive",0,2).status_code,409)
        self.assertEqual(self.transition("archive",1,2).status_code,200)
        self.assertEqual(self.transition("restore",2,2).status_code,200)
        self.assertEqual(self.store.revision("alice",self.sid,1)["source"],"pass")
        self.assertEqual(self.store.revision("alice",self.sid,2)["frozen_version"],2)
        self.assertEqual(self.post("/clone",{"version":1,"name":"clone"},B).status_code,404)
        c=self.post("/clone",{"version":1,"name":"clone"})
        self.assertEqual(c.status_code,201);x=c.json()
        self.assertEqual(x["parent_strategy_id"],self.sid)
        self.assertEqual(x["parent_version"],1);self.assertEqual(x["parent_code_sha256"],self.a["code_sha256"])
        self.assertEqual(x["source"],"pass");self.assertIsNone(x["frozen_version"])
        self.store.add_revision("alice",x["id"],"y=2",1)
        history=self.client.get(self.url+"/versions",headers=A).json()
        self.assertEqual([v["version"] for v in history["versions"]],[2,1])
        self.assertEqual([e["action"] for e in history["events"]],["restore","archive","freeze","revision_created","created"])

    def test_job_link_and_archive_atomic_gate(self):
        p={"kind":"historical_visual","strategy_id":self.sid,"version":1,"code_sha256":self.a["code_sha256"]}
        j=self.store.submit("alice","run",p)
        self.assertEqual(self.transition("archive",0,1).status_code,200)
        with self.assertRaises(Conflict):self.store.submit("alice","new",p)
        self.assertEqual(self.store.submit("alice","run",p)["id"],j["id"])
        job,token,_=self.store.claim()
        self.store.finish(job,token,result={"result_sha256":"b"*64})
        rows=self.client.get(self.url+"/jobs",headers=A).json()
        self.assertEqual(rows["jobs"][0]["result_sha256"],"b"*64)
        self.assertEqual(rows["jobs"][0]["request"],p)
        self.assertEqual(self.client.get(self.url+"/jobs",headers=B).status_code,404)
        self.assertEqual(self.client.get(self.url+"/versions",headers=B).status_code,404)

    def test_frozen_version_pin(self):
        r=self.store.add_revision("alice",self.sid,"x=1",1)
        self.transition("freeze",0,2)
        p={"kind":"historical_visual","strategy_id":self.sid,"version":1,"code_sha256":self.a["code_sha256"]}
        with self.assertRaises(Conflict):self.store.submit("alice","old",p)
        j=self.store.submit("alice","new",{**p,"version":2,"code_sha256":r["code_sha256"]})
        self.assertEqual(j["status"],"queued")

    def test_additive_migration(self):
        # Emulate a pre-M12 database with source preserved.
        with self.store.connection(True) as c:
            c.execute("DROP TABLE registry_events")
            c.execute("DROP TABLE strategy_registry")
        s=Store(self.path)
        self.assertEqual(s.revision("alice",self.sid,1)["source"],"pass")
        self.assertEqual(s.versions("alice",self.sid)["events"],[])
        self.assertFalse(s.strategies("alice")[0]["archived"])
