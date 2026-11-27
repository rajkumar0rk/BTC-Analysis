import json,os,tempfile,unittest
from pathlib import Path
from publish_backtest_bundles import validate,publish
from dashboard_archive import dump

def fixture(run=11,net=-5):
    start="2025-01-01T00:00:00+00:00";end="2025-01-02T00:00:00+00:00"
    rows=[] if net==0 else [dict(entry_utc=start,exit_utc=end,side=1,entry_price=100,exit_price=95,net_points=net,exit_reason="stop",signal_context={})]
    return dict(schema=1,family="test",symbol="BTCUSD",unit="account USD",start_utc=start,end_utc=end,execution_timeframe_minutes=1,signal_timeframe_minutes=15,costs="recorded costs",source_commit="a"*40,source_run_id=run,source_attempt=1,data_provenance={},indicator_definitions=[dict(id="a",name="custom",timeframe_minutes=15,panel="price",parameters={})],indicator_series={"a":[[1735689600,100],[1735690500,101]]},variants=[dict(key="one",name="Test",parameters={},summary={"trades":len(rows),"net":net,"open_position":None,"wins":0},trades=rows)])

class TestBundles(unittest.TestCase):
    def test_versions_and_zero(self):
        with tempfile.TemporaryDirectory() as p:
            root=Path(p);cache=root/"cache";data=root/"data";cache.mkdir();dump(data/"index.json",{"runs":[]})
            for i,b in enumerate([fixture(),fixture(12,0)]):dump(cache/f"{i+1}.json",dict(artifact_id=i+1,completed_at=f"2025-01-0{i+1}T00:00:00Z",branch="research",bundle=b))
            publish(cache,data);index=json.loads((data/"index.json").read_text());r=index["runs"]
            self.assertEqual(index["automatic_run_count"],2);self.assertEqual([x["net"] for x in r],[0,-5]);self.assertTrue(r[0]["latest_version"]);self.assertFalse(r[1]["latest_version"])
            self.assertEqual(json.loads((data/"runs"/r[0]["id"]/"2025-01.json").read_text()),[])
    def test_reject(self):
        b=fixture();b["variants"][0]["summary"]["net"]=10
        with self.assertRaises(ValueError):validate(b)
        b=fixture();b["indicator_series"]["a"].reverse()
        with self.assertRaises(ValueError):validate(b)
if __name__=="__main__":unittest.main()
