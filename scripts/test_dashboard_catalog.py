import tempfile,unittest
from pathlib import Path
from dashboard_archive import dump
from dashboard_catalog import migrate,build_catalog,read
class CatalogTests(unittest.TestCase):
    def test_migration(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);old=p/"old";data=p/"data"
            oldrun=dict(id="historical",strategy="Old",symbol="BTCUSD",unit="account USD",net=-10,trades=1,months=[],detail_available=True,research_reference=True)
            newrun=dict(id="new",strategy="New",symbol="ETHUSD",unit="account USD",net=0,trades=0,months=[],detail_available=True,automatic_version=True,latest_version=True)
            dump(old/"index.json",{"runs":[oldrun]});dump(old/"runs/historical/curve.json",[["2025-01-01T00:00:00+00:00",-10,10]])
            dump(old/"frozen.json",[dict(id="f",name="Frozen",sha="a"*40,path="locked.json",net_usd_min=2,net_usd_max=3,status="Frozen research",trades=4)])
            dump(old/"supertrend.json",[dict(id="historical",name="Old summary",replay_id="historical",unit="account return %",net=-20,status="Failed",monthly=[])])
            dump(data/"index.json",{"runs":[newrun]});migrate(data,old);build_catalog(data)
            idx=read(data/"index.json");self.assertEqual(idx["catalog_count"],3)
            self.assertEqual(idx["selection_policy"]["excluded"],0)
            rows={r["id"]:r for r in idx["catalog"]};self.assertEqual(rows["historical"]["evidence"]["net"],-20);self.assertEqual(rows["historical"]["net"],-10)
            self.assertTrue(rows["summary:f"]["frozen"]);self.assertEqual(rows["summary:f"]["net_min"],2);self.assertIsNone(rows["summary:f"]["run_id"]);self.assertEqual(rows["new"]["net"],0)
            self.assertTrue((data/"runs/historical/curve.json").exists())
            second=p/"second";dump(second/"index.json",{"runs":[]});migrate(second,data);build_catalog(second)
            self.assertEqual(read(second/"index.json")["legacy_evidence"],idx["legacy_evidence"])
if __name__=="__main__":unittest.main()
