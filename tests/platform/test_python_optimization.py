import unittest
from btc_analysis.service.walkforward import Study,compiled_source,plan,browser_fold
from btc_analysis.service.optimization import Search,variants
from btc_analysis.visual import Graph,compile_graph
from test_walkforward import study
from test_browser_replay import SETTINGS,csv_text
from test_visual import graph
from test_python_strategy import SOURCE

PARAM=SOURCE.replace('    exposure = D("0.5")','    exposure = D("0.5")\n    size = parameter(D("0.1"), D("0.01"), D("1"))').replace('self.buy(ctx, D("0.1"),','self.buy(ctx, self.size,')

class PythonOptimizationTests(unittest.TestCase):
    def test_python_train_only_and_frozen_winner(self):
        s=study()
        s["search"]["axes"]=[dict(key="python:size",values=["0.1","0.2"])]
        choices,windows,total=plan(compiled_source(PARAM),Study.model_validate(s),budget=120000)
        self.assertEqual(len(choices),2)
        self.assertNotEqual(choices[0][1]["graph_sha256"],choices[1][1]["graph_sha256"])
        a=browser_fold(csv_text(),PARAM,"BTCUSD",SETTINGS,True,s,1)
        self.assertEqual(len(a["training"]),2)
        self.assertIsNotNone(a["winner_parameters"])
        self.assertEqual(a["tests"][0]["graph_sha256"],a["winner_graph_sha256"])
        self.assertNotEqual(a["tests"][-1]["graph_sha256"],a["winner_graph_sha256"])
        rows=csv_text().splitlines()
        for i in range(21,31):
            t=rows[i].split(",")[0];rows[i]=t+",200,210,190,205,1"
        b=browser_fold("\n".join(rows)+"\n",PARAM,"BTCUSD",SETTINGS,True,s,1)
        self.assertEqual(a["training"],b["training"])
        self.assertEqual(a["winner_parameters"],b["winner_parameters"])

    def test_invalid_or_inactive_axes(self):
        for key,vals in (("python:unknown",["1","2"]),("python:size",["1","2"]),("stop_loss_pct",["1","2"])):
            s=study();s["search"]["axes"]=[dict(key=key,values=vals)]
            with self.assertRaises(ValueError):plan(compiled_source(PARAM),Study.model_validate(s),budget=120000)
        g=compile_graph(Graph.model_validate({**graph(),"advanced":{"exit_mode":"points","target_enabled":False,"trailing":{"activation":"100","distance":"50"}}}))["graph"]
        for key in ("advanced:target_points","stop_loss_pct","python:size","advanced:profit_lock.locked"):
            with self.assertRaises(ValueError):variants(g,Search.model_validate(dict(axes=[dict(key=key,values=["1","2"])])))
        c=variants(g,Search.model_validate(dict(axes=[dict(key="advanced:trailing.distance",values=["25","50"])])))
        self.assertEqual([x[1]["graph"]["advanced"]["trailing"]["distance"] for x in c],["25","50"])

if __name__=="__main__":unittest.main()
