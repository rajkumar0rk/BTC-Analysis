import tempfile
import unittest
import json
from pathlib import Path
from btc_analysis.markets import Spec,import_bundle,load_bundle,run_reference,rollover_plan,catalog
from btc_analysis.visual import Graph
from test_visual import graph
from fastapi.testclient import TestClient
from btc_analysis.service.api import create_app

T=1735689600

def spec(**patch):
    return Spec.model_validate({"venue":"fixture_venue","symbol":"FUT-A","underlying":"FIXTURE","market":"index","asset_class":"future",
        "currency":"INR","tick_size":"1","lot_size":"1","multiplier":"2","expiry":T+86400,"effective_start":T,"effective_end":T+86400,
        "source":"synthetic test fixture","timestamp_evidence":"fixture open labels","specification_evidence":"fixture specs",
        "calendar_evidence":"fixture sessions","calendar_start":T,"calendar_end":T+86400,
        "sessions":[(T,T+240),(T+360,T+600)],"linear":True,**patch})

class MarketsTests(unittest.TestCase):
    def setUp(self):
        d=tempfile.TemporaryDirectory();self.addCleanup(d.cleanup);self.root=Path(d.name)
        self.csv=self.root/"data.csv"
        self.csv.write_text("time,open,high,low,close,volume\n"+"".join(f"{t},102,110,90,103,10\n" for t in list(range(T,T+240,60))+list(range(T+360,T+600,60))))
    def test_import_gap_calendar_and_run(self):
        k=import_bundle(self.root,self.csv,spec(),T,T+600)
        self.assertEqual(len(load_bundle(self.root,k)[0]["rows"]),8)
        self.assertEqual(catalog(self.root)[0]["currency"],"INR")
        g=Graph.model_validate(graph())
        r=run_reference(self.root,k,g,T,T+240)
        self.assertEqual(r["currency"],"INR")
        self.assertEqual(len(r["result"]["scenarios"]),2)
        self.assertEqual(r["result"]["scenarios"][0]["bars"],4)
        with self.assertRaises(ValueError):run_reference(self.root,k,g,T,T+600)
        self.csv.write_text(self.csv.read_text().replace(f"{T+60},102,110,90,103,10\n",""))
        with self.assertRaises(ValueError):import_bundle(self.root,self.csv,spec(),T,T+600)
    def test_roll_plan_and_tamper(self):
        a=import_bundle(self.root,self.csv,spec(),T,T+600)
        b=import_bundle(self.root,self.csv,spec(symbol="FUT-B",expiry=T+172800),T,T+600)
        self.assertFalse(rollover_plan(self.root,[a,b],[T+60])["execution_supported"])
        with self.assertRaises(ValueError):rollover_plan(self.root,[a,b],[T+240])
        p=self.root/"objects"/(a+".json");obj=json.loads(p.read_text());obj["rows"][0]["close"]="104";p.write_text(json.dumps(obj))
        with self.assertRaises(ValueError):load_bundle(self.root,a)
    def test_options_catalog_only_and_auth(self):
        k=import_bundle(self.root,self.csv,spec(asset_class="option",strike="100",option_right="call"),T,T+600)
        with self.assertRaises(ValueError):run_reference(self.root,k,Graph.model_validate(graph()),T,T+240)
        with TestClient(create_app(self.root/"db.sqlite",{"owner":"a"*40},market_root=self.root)) as c:
            self.assertEqual(c.get("/v1/markets").status_code,401)
            result=c.get("/v1/markets",headers={"Authorization":"Bearer "+"a"*40}).json()
            self.assertEqual(result[0]["bundle_sha256"],k)
            self.assertFalse(result[0]["reference_eligible"])
