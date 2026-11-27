import unittest,json
from copy import deepcopy
from btc_analysis.service.walkforward import Study,plan,evaluate_fold,browser_fold
from btc_analysis.visual import Graph,compile_graph
from test_browser_replay import SETTINGS,csv_text
from test_visual import graph
T=1735689600
def study():
    return dict(start=T,train_minutes=20,test_minutes=10,folds=2,mode="rolling",
        search=dict(method="grid",axes=[dict(key="stop_loss_pct",values=["2","5"])],max_drawdown_pct="100",min_trades=1),
        objective="net_return",acknowledge=True)
class WalkForwardTests(unittest.TestCase):
    def test_training_selection_independent_of_future(self):
        g=json.dumps(graph());s=study();csv=csv_text()
        a=browser_fold(csv,g,"BTCUSD",SETTINGS,True,s,1)
        rows=csv.splitlines()
        for i in range(21,31):
            t=rows[i].split(",")[0];rows[i]=t+",200,210,190,205,1"
        b=browser_fold("\n".join(rows)+"\n",g,"BTCUSD",SETTINGS,True,s,1)
        self.assertEqual(a["training"],b["training"])
        self.assertEqual(a["winner_graph_sha256"],b["winner_graph_sha256"])
        self.assertEqual(a["window"]["train_end"],a["window"]["test_start"])
        self.assertIsNotNone(a["winner_graph_sha256"])
        self.assertEqual(len(a["tests"]),5)
        self.assertEqual(a["tests"][0]["graph_sha256"],a["winner_graph_sha256"])
        self.assertNotEqual(a["tests"][-1]["graph_sha256"],a["winner_graph_sha256"])
    def test_plan_rejects_budget_and_alignment(self):
        b=compile_graph(Graph.model_validate(graph()))
        with self.assertRaises(ValueError):plan(b,Study.model_validate(study()),budget=10)
        s=study();s["start"]=T+1
        with self.assertRaises(ValueError):Study.model_validate(s)
        s=study();s["mode"]="expanding"
        _,w,_=plan(b,Study.model_validate(s),budget=10000)
        self.assertEqual(w[0]["train_start"],w[1]["train_start"])
        self.assertEqual(w[0]["test_end"],w[1]["test_start"])
    def test_random_reproducibility_and_month_objective(self):
        s=study();s["search"].update(method="random",samples=2,seed=42);s["objective"]="monthly_consistency"
        a=browser_fold(csv_text(),json.dumps(graph()),"BTCUSD",SETTINGS,True,s,2)
        b=browser_fold(csv_text(),json.dumps(graph()),"BTCUSD",SETTINGS,True,s,2)
        self.assertEqual(a,b)

    def test_repository_fold_matches_short_selection_and_metrics(self):
        import gzip,tempfile
        from pathlib import Path
        from hashlib import sha256
        from datetime import datetime,timezone
        from btc_analysis.service.browser_archive_study import repository_fold
        text=csv_text();lines=text.splitlines();start=int(lines[1].split(",")[0])
        # Pad the fixture to a complete day using observed fixture rows repeated
        # with new timestamps. This is explicitly synthetic test data only.
        data=lines[1:];rows=[lines[0]]
        for j in range(1440):
            rows.append(str(start+j*60)+","+data[j%len(data)].split(",",1)[1])
        raw=gzip.compress(("\n".join(rows)+"\n").encode());h=sha256(raw).hexdigest()
        m=json.dumps({"symbol":"BTCUSD","resolution":"1m","timestamp_unit":"unix_seconds_utc","partitions":[{"file":"2025-01.csv.gz","utc_start":datetime.fromtimestamp(start,timezone.utc).isoformat(),"utc_end_exclusive":datetime.fromtimestamp(start+86400,timezone.utc).isoformat(),"expected_minutes":1440,"observed_candles":1440,"missing_minutes":0,"sha256_gzip":h}]})
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp)/(h+".bin")).write_bytes(raw)
            short=browser_fold(text,json.dumps(graph()),"BTCUSD",SETTINGS,True,study(),1)
            long=repository_fold(m,"BTCUSD","2025-01-01","2025-01-01",json.dumps(graph()),study(),1,SETTINGS,True,tmp)
            self.assertEqual(short["winner_graph_sha256"],long["winner_graph_sha256"])
            self.assertEqual(short["winner_parameters"],long["winner_parameters"])
            self.assertEqual(len(short["tests"]),len(long["tests"]))
            for a,b in zip(short["tests"],long["tests"]):
                for key in ("test","worst_return_pct","max_drawdown_pct","min_trades","passed"):self.assertEqual(a[key],b[key])
            with self.assertRaisesRegex(ValueError,"outside selected"):
                repository_fold(m,"BTCUSD","2025-01-01","2025-01-01",json.dumps(graph()),{**study(),"train_minutes":1440},1,SETTINGS,True,tmp)

    def test_leveraged_candidates_and_funding_stress(self):
        from btc_analysis.service.study_risk import StudyRisk
        s=study();s["leverage_values"]=["2","5"]
        text=csv_text()
        mark="time,open,high,low,close\n"+"\n".join(x.rsplit(",",1)[0] for x in text.splitlines()[1:])+"\n"
        r=dict(leverage="2",margin_mode="cross",initial_rate_floor="0.01",maintenance_rate="0.005",max_notional="100000",
            liquidation_fee_bps="5",profile_start=str(T),profile_end=str(T+3600),profile_source="synthetic fixture",
            preliq_points="0",scalp_enabled=False,scalp_start="",scalp_end="",mark_csv=mark,funding_enabled=True,
            funding_interval_seconds=600,funding_anchor_epoch=T,funding_csv="time,rate,reference_mark\n"+"".join(f"{T+i*600},0.001,100\n" for i in range(6)),acknowledge=True)
        sliced=StudyRisk(r,True).window(T+1200,T+1800,"5","funding_negative","2")
        self.assertIn(", -0.002,".replace(" ",""),sliced["funding_csv"])
        self.assertEqual(sliced["funding_provenance"],"stress_synthetic")
        out=browser_fold(text,json.dumps(graph()),"BTCUSD",SETTINGS,True,s,1,risk=r)
        self.assertEqual(len(out["training"]),4)
        self.assertEqual({x["parameters"]["leverage"] for x in out["training"]},{"2","5"})
        self.assertIsNotNone(out["winner_parameters"])
        self.assertEqual(len(out["tests"]),9)
        self.assertTrue(all(x["leverage"]==out["winner_parameters"]["leverage"] for x in out["tests"] if x["test"]!="parameter_neighbor"))
        with self.assertRaises(ValueError):browser_fold(text,json.dumps(graph()),"BTCUSD",SETTINGS,True,s,1)
