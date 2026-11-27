import unittest
from decimal import Decimal as D
from btc_analysis.visual import Graph,compile_graph,recover_graph
from btc_analysis.service.historical import GraphStrategy
from btc_analysis.service.optimization import Search,variants
from test_visual import graph,rule
from test_backtest_engine import cfg,bars,run

def setup():
    raw=graph()
    raw["advanced"]={"exit_mode":"points","stop_points":"20","target_points":"30","entry_mode":"once_per_true_run"}
    raw["long_partial"]={"pct":"50","rule":rule("gt","105")}
    return raw

class PartialTests(unittest.TestCase):
    def test_native_generated_and_residual_stop(self):
        g=Graph.model_validate(setup());c=compile_graph(g);ns={}
        exec(compile(c["source"],"<trusted-generated>","exec"),ns)
        self.assertEqual(recover_graph(c["source"]),c)
        data=bars([(102,102,102,102),(102,110,102,110),(110,112,108,110),(110,111,80,85)])
        a=run(cfg(initial_equity=D(10000)),lambda:GraphStrategy(g),data)
        b=run(cfg(initial_equity=D(10000)),ns["VisualStrategy"],data)
        self.assertEqual(a.scenarios,b.scenarios)
        for s in a.scenarios:
            self.assertEqual(len(s.closed_trades),1)
            entry,part,stop=s.fills
            self.assertEqual(part.reason,"visual_long_partial_exit")
            self.assertEqual(stop.reason,"fixed_point_stop")
            self.assertEqual(part.quantity,D(9))
            self.assertEqual(entry.quantity,part.quantity+stop.quantity)
            self.assertEqual(s.open_quantity,D(0))
    def test_full_exit_priority(self):
        raw=setup();raw["long_exit"]=rule("gt","105")
        g=Graph.model_validate(raw)
        data=bars([(102,102,102,102),(102,110,102,110),(110,112,108,110),(110,110,110,110)])
        a=run(cfg(initial_equity=D(10000)),lambda:GraphStrategy(g),data)
        for s in a.scenarios:
            self.assertEqual(len(s.closed_trades),1)
            self.assertEqual(s.fills[-1].reason,"visual_long_rule_exit")
            self.assertFalse(any(f.reason=="visual_long_partial_exit" for f in s.fills))
    def test_validation_and_axes(self):
        for pct in ("0","100","-1"):
            raw=setup();raw["long_partial"]["pct"]=pct
            with self.assertRaises(ValueError):Graph.model_validate(raw)
        c=compile_graph(Graph.model_validate(setup()))
        opts=variants(c["graph"],Search.model_validate({"axes":[{"key":"partial:long.pct","values":["25","50"]}]}))
        self.assertEqual(len(opts),2)
        self.assertNotIn("long_partial",compile_graph(Graph.model_validate(graph()))["graph"])

if __name__=="__main__":unittest.main()
