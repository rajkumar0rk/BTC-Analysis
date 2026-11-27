import unittest
from decimal import Decimal as D
from datetime import timedelta
from btc_analysis.visual import Graph,compile_graph,recover_graph
from btc_analysis.service.historical import GraphStrategy
from btc_analysis.service.optimization import Search,variants
from test_visual import graph,rule,disabled
from test_backtest_engine import cfg,bars,run,T

def setup(short=False):
    raw=graph()
    raw["advanced"]={"exit_mode":"points","stop_points":"20","target_points":"50","entry_mode":"once_per_true_run"}
    if short:
        raw["long_entry"]=disabled();raw["short_entry"]=rule("lt","105")
        raw["short_partial_levels"]=[{"pct":"50","rule":rule("lt","95")},{"pct":"50","rule":rule("lt","95")}]
    else:
        raw["long_partial_levels"]=[{"pct":"50","rule":rule("gt","105")},{"pct":"50","rule":rule("gt","105")}]
    return raw

class PartialLevelsTests(unittest.TestCase):
    def test_ordered_native_generated_and_residual_stop(self):
        g=Graph.model_validate(setup());c=compile_graph(g);ns={}
        exec(compile(c["source"],"<trusted-generated>","exec"),ns)
        self.assertEqual(recover_graph(c["source"]),c)
        data=bars([(102,102,102,102),(102,110,102,110),(110,112,108,110),(110,111,109,110),(110,111,80,85)])
        a=run(cfg(n=5,initial_equity=D(10000)),lambda:GraphStrategy(g),data)
        b=run(cfg(n=5,initial_equity=D(10000)),ns["VisualStrategy"],data)
        self.assertEqual(a.scenarios,b.scenarios)
        for s in a.scenarios:
            self.assertEqual(len(s.closed_trades),1)
            self.assertEqual([f.reason for f in s.fills],["visual_long_entry","visual_long_partial_level_1","visual_long_partial_level_2","fixed_point_stop"])
            self.assertEqual([f.quantity for f in s.fills],[D(19),D(9),D(5),D(5)])
            self.assertEqual([f.event_utc for f in s.fills[1:3]],[T+timedelta(minutes=2),T+timedelta(minutes=3)])
            self.assertEqual(s.open_quantity,0)
    def test_short_and_full_exit_priority(self):
        raw=setup(True);g=Graph.model_validate(raw)
        data=bars([(102,102,102,102),(102,102,90,90),(90,92,89,90),(90,92,89,90),(90,123,90,122)])
        a=run(cfg(n=5,initial_equity=D(10000)),lambda:GraphStrategy(g),data)
        for s in a.scenarios:
            self.assertEqual([f.reason for f in s.fills],["visual_short_entry","visual_short_partial_level_1","visual_short_partial_level_2","fixed_point_stop"])
            self.assertEqual(s.open_quantity,0)
        raw["short_exit"]=rule("lt","95");g=Graph.model_validate(raw)
        a=run(cfg(n=5,initial_equity=D(10000)),lambda:GraphStrategy(g),data)
        self.assertTrue(all(not any("partial_level" in f.reason for f in s.fills) for s in a.scenarios))
    def test_validation_and_axes(self):
        raw=setup();raw["long_partial"]={"pct":"25","rule":rule()}
        with self.assertRaises(ValueError):Graph.model_validate(raw)
        raw=setup();raw["long_partial_levels"]=raw["long_partial_levels"][:1]
        with self.assertRaises(ValueError):Graph.model_validate(raw)
        c=compile_graph(Graph.model_validate(setup()))
        opts=variants(c["graph"],Search.model_validate({"axes":[{"key":"partial_level:long.2.pct","values":["25","50"]}]}))
        self.assertEqual(len(opts),2)
        self.assertNotIn("long_partial_levels",compile_graph(Graph.model_validate(graph()))["graph"])

if __name__=="__main__":unittest.main()
