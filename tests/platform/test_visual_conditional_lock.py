import unittest
from decimal import Decimal as D
from datetime import timedelta
from btc_analysis.visual import Graph,compile_graph,recover_graph
from btc_analysis.service.historical import GraphStrategy
from btc_analysis.service.optimization import Search,variants
from test_visual import graph,rule,disabled
from test_backtest_engine import cfg,bars,run,T

def setup():
    raw=graph()
    raw["advanced"]={"exit_mode":"points","stop_points":"20","target_points":"50","entry_mode":"once_per_true_run"}
    raw["long_lock"]={"locked_points":"0","rule":rule("gt","105")}
    return raw

class ConditionalLockTests(unittest.TestCase):
    def test_causal_amendment_and_generated_parity(self):
        g=Graph.model_validate(setup());c=compile_graph(g);ns={}
        exec(compile(c["source"],"<trusted-generated>","exec"),ns)
        self.assertEqual(recover_graph(c["source"]),c)
        data=bars([(102,102,102,102),(102,110,95,110),(110,111,100,101),(101,101,101,101)])
        a=run(cfg(initial_equity=D(10000)),lambda:GraphStrategy(g),data)
        b=run(cfg(initial_equity=D(10000)),ns["VisualStrategy"],data)
        self.assertEqual(a.scenarios,b.scenarios)
        for s in a.scenarios:
            self.assertEqual(len(s.closed_trades),1)
            self.assertEqual(s.fills[-1].reason,"conditional_profit_lock_stop")
            self.assertEqual(s.fills[-1].price,D(102))
            amended=[o for o in s.orders if o.status=="amended"]
            self.assertEqual(len(amended),1)
            self.assertEqual(amended[0].event_utc,T+timedelta(minutes=2))
    def test_gap_and_residual_protection(self):
        raw=setup();raw["long_partial"]={"pct":"50","rule":rule("gt","105")}
        g=Graph.model_validate(raw)
        data=bars([(102,102,102,102),(102,110,95,110),(110,111,109,110),(99,100,98,99)])
        a=run(cfg(initial_equity=D(10000)),lambda:GraphStrategy(g),data)
        for s in a.scenarios:
            entry,part,stop=s.fills
            self.assertEqual(part.reason,"visual_long_partial_exit")
            self.assertEqual(stop.reason,"conditional_profit_lock_stop")
            self.assertEqual(stop.price,D(99))
            self.assertEqual(entry.quantity,part.quantity+stop.quantity)
            self.assertEqual(s.open_quantity,0)
    def test_short_symmetry(self):
        raw=setup();raw.pop("long_lock");raw["long_entry"]=disabled();raw["short_entry"]=rule("lt","105")
        raw["short_lock"]={"locked_points":"2","rule":rule("lt","95")}
        g=Graph.model_validate(raw)
        data=bars([(102,102,102,102),(102,110,90,90),(90,101,89,101),(101,101,101,101)])
        a=run(cfg(initial_equity=D(10000)),lambda:GraphStrategy(g),data)
        for s in a.scenarios:
            self.assertEqual(s.fills[-1].reason,"conditional_profit_lock_stop")
            self.assertEqual(s.fills[-1].price,D(100))
    def test_no_impossible_or_looser_stop(self):
        raw=setup();raw["long_lock"]["locked_points"]="20"
        g=Graph.model_validate(raw)
        data=bars([(102,102,102,102),(102,110,95,110),(110,111,109,110),(110,111,109,110)])
        a=run(cfg(initial_equity=D(10000)),lambda:GraphStrategy(g),data)
        self.assertTrue(all(not any(o.status=="amended" for o in s.orders) for s in a.scenarios))
        raw=setup();raw["advanced"]["profit_lock"]={"activation":"5","locked":"3"}
        g=Graph.model_validate(raw)
        a=run(cfg(initial_equity=D(10000)),lambda:GraphStrategy(g),data)
        self.assertTrue(all(not any(o.detail=="conditional_profit_lock_stop" for o in s.orders) for s in a.scenarios))
    def test_validation_axes(self):
        raw=setup();raw["advanced"]["exit_mode"]="percent"
        with self.assertRaises(ValueError):Graph.model_validate(raw)
        raw=setup();raw["long_lock"]["locked_points"]="-1"
        with self.assertRaises(ValueError):Graph.model_validate(raw)
        c=compile_graph(Graph.model_validate(setup()))
        opts=variants(c["graph"],Search.model_validate({"axes":[{"key":"lock:long.locked_points","values":["0","5"]}]}))
        self.assertEqual(len(opts),2)
        self.assertNotIn("long_lock",compile_graph(Graph.model_validate(graph()))["graph"])

if __name__=="__main__":unittest.main()
