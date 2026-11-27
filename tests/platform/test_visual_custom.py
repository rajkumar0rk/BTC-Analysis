import unittest
from decimal import Decimal as D
from btc_analysis.visual import Graph,compile_graph,recover_graph
from btc_analysis.service.historical import GraphStrategy,frames
from btc_analysis.service.optimization import Search,variants
from btc_analysis.service.strategy_authoring import validate_source
from test_visual import graph
from test_backtest_engine import cfg,bars,run

def custom_graph():
    raw=graph()
    raw["custom_formulas"]=[dict(name="avg",timeframe=60,lookback=2,expression='mean(series(bars, "close"))')]
    raw["long_entry"]["groups"][0]["conditions"][0]["left"]=dict(kind="custom",name="avg",timeframe=60)
    return raw

class CustomVisualTests(unittest.TestCase):
    def test_parity_and_recovery(self):
        g=Graph.model_validate(custom_graph())
        c=compile_graph(g);ns={}
        exec(compile(c["source"],"<trusted-generated>","exec"),ns)
        self.assertEqual(recover_graph(c["source"]),c)
        self.assertTrue(validate_source(c["source"])["valid"])
        self.assertEqual(frames(g),(60,))
        d=bars([(90,90,90,90),(120,120,120,120),(120,120,120,120),(120,130,120,130)])
        a=run(cfg(initial_equity=D(10000)),lambda:GraphStrategy(g),d)
        b=run(cfg(initial_equity=D(10000)),ns["VisualStrategy"],d)
        self.assertEqual(a.scenarios,b.scenarios)
        self.assertTrue(a.scenarios[0].fills)
    def test_warmup_recursive_and_independence(self):
        raw=custom_graph()
        raw["custom_formulas"][0]["expression"]="bars[-1].close if previous is None else (previous + bars[-1].close) / 2"
        g=Graph.model_validate(raw);a=GraphStrategy(g);b=GraphStrategy(g)
        d=bars([(90,90,90,90),(110,110,110,110),(130,130,130,130)])
        for candle in d:a.on_completed_candle(candle)
        self.assertEqual(a.custom_pair("avg"),(D(110),D(120)))
        self.assertEqual(b.custom_pair("avg"),(None,None))
    def test_validation_and_optimization(self):
        for expression in ("__import__('os')","bars[-1].__class__","ctx.equity","open('x')","1\\nimport os"):
            raw=custom_graph();raw["custom_formulas"][0]["expression"]=expression
            with self.assertRaises(ValueError):Graph.model_validate(raw)
        raw=custom_graph();raw["custom_formulas"][0]["timeframe"]=300
        with self.assertRaises(ValueError):Graph.model_validate(raw)
        c=compile_graph(Graph.model_validate(custom_graph()))
        options=variants(c["graph"],Search.model_validate({"axes":[{"key":"custom:avg.lookback","values":["2","3"]}]}))
        self.assertEqual(len(options),2)
        self.assertEqual({v["graph"]["custom_formulas"][0]["lookback"] for _,v in options},{2,3})
        self.assertNotIn("custom_formulas",compile_graph(Graph.model_validate(graph()))["graph"])

if __name__=="__main__":unittest.main()
