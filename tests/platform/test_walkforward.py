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
