import unittest
from decimal import Decimal as D
from datetime import timedelta
from btc_analysis.visual import Graph,compile_graph,recover_graph
from btc_analysis.service.historical import GraphStrategy
from btc_analysis.service.optimization import Search,variants
from test_visual import graph,rule,disabled
from test_backtest_engine import cfg,bars,run,T

def setup(mode="extend"):
    raw=graph()
    raw["advanced"]={"exit_mode":"points","stop_points":"20","target_points":"20","entry_mode":"once_per_true_run"}
    raw["long_target"]={"target_points":"40" if mode=="extend" else "12","mode":mode,"rule":rule("gt","105")}
    return raw

class ConditionalTargetTests(unittest.TestCase):
    def test_extend_and_parity(self):
        g=Graph.model_validate(setup());c=compile_graph(g);ns={}
        exec(compile(c["source"],"<trusted-generated>","exec"),ns)
        self.assertEqual(recover_graph(c["source"]),c)
        data=bars([(102,102,102,102),(102,110,98,110),(110,130,108,125),(125,145,124,140)])
        a=run(cfg(initial_equity=D(10000)),lambda:GraphStrategy(g),data)
        b=run(cfg(initial_equity=D(10000)),ns["VisualStrategy"],data)
        self.assertEqual(a.scenarios,b.scenarios)
        for s in a.scenarios:
            self.assertEqual(s.fills[-1].reason,"conditional_target_extend")
            self.assertEqual(s.fills[-1].price,D(142))
            self.assertEqual(len([x for x in s.orders if x.status=="amended"]),1)
    def test_closer_and_protection(self):
        g=Graph.model_validate(setup("bring_closer"))
        data=bars([(102,102,102,102),(102,118,98,110),(110,115,108,114),(114,114,114,114)])
        a=run(cfg(initial_equity=D(10000)),lambda:GraphStrategy(g),data)
        for s in a.scenarios:
            self.assertEqual(s.fills[-1].reason,"conditional_target_bring_closer")
            self.assertEqual(s.fills[-1].price,D(114))
        data=bars([(102,102,102,102),(102,110,98,110),(110,112,80,85),(85,85,85,85)])
        a=run(cfg(initial_equity=D(10000)),lambda:GraphStrategy(g),data)
        self.assertTrue(all(s.fills[-1].reason=="fixed_point_stop" for s in a.scenarios))
    def test_short_and_residual(self):
        raw=setup();raw.pop("long_target");raw["long_entry"]=disabled();raw["short_entry"]=rule("lt","105")
        raw["short_target"]={"target_points":"40","mode":"extend","rule":rule("lt","95")}
        raw["short_partial"]={"pct":"50","rule":rule("lt","95")}
        g=Graph.model_validate(raw)
        data=bars([(102,102,102,102),(102,105,89,90),(90,92,88,90),(90,92,60,62)])
        a=run(cfg(initial_equity=D(10000)),lambda:GraphStrategy(g),data)
        for s in a.scenarios:
            entry,part,target=s.fills
            self.assertEqual(part.reason,"visual_short_partial_exit")
            self.assertEqual(target.reason,"conditional_target_extend")
            self.assertEqual(target.price,D(62))
            self.assertEqual(entry.quantity,part.quantity+target.quantity)
    def test_infeasible_and_axes(self):
        raw=setup("bring_closer");raw["long_target"]["target_points"]="5"
        g=Graph.model_validate(raw)
        data=bars([(102,102,102,102),(102,110,98,110),(110,112,108,110),(110,112,108,110)])
        a=run(cfg(initial_equity=D(10000)),lambda:GraphStrategy(g),data)
        self.assertTrue(all(not any(o.status=="amended" for o in s.orders) for s in a.scenarios))
        raw=setup();raw["advanced"]["target_enabled"]=False
        with self.assertRaises(ValueError):Graph.model_validate(raw)
        c=compile_graph(Graph.model_validate(setup()))
        self.assertEqual(len(variants(c["graph"],Search.model_validate({"axes":[{"key":"target:long.target_points","values":["30","40"]}]}))),2)
        self.assertNotIn("long_target",compile_graph(Graph.model_validate(graph()))["graph"])

if __name__=="__main__":unittest.main()
