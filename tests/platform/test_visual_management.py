import unittest
from decimal import Decimal as D
from btc_analysis.visual import Graph,compile_graph,recover_graph
from btc_analysis.service.historical import GraphStrategy
from test_visual import graph,rule
from test_backtest_engine import cfg,bars,run
from test_visual_machine import setup as machine_setup

def setup():
    raw=graph()
    raw["advanced"]={"exit_mode":"points","stop_points":"20","target_points":"30","entry_mode":"once_per_true_run"}
    raw["long_lock"]={"locked_points":"0","rule":rule("gt","105")}
    raw["long_target"]={"target_points":"50","mode":"extend","rule":rule("gt","105")}
    raw["long_partial"]={"pct":"50","rule":rule("gt","105")}
    raw["management"]={"priority":["partial","target","lock"],"mode":"first_success","audit":True}
    return raw

class ManagementTests(unittest.TestCase):
    def test_first_success_and_parity(self):
        raw=setup();g=Graph.model_validate(raw);c=compile_graph(g);ns={}
        exec(compile(c["source"],"<trusted-generated>","exec"),ns)
        self.assertEqual(recover_graph(c["source"]),c)
        data=bars([(102,102,102,102),(102,110,99,110),(110,112,109,110),(110,112,109,110),(110,111,90,95)])
        a=run(cfg(n=5,initial_equity=D(10000)),lambda:GraphStrategy(g),data)
        b=run(cfg(n=5,initial_equity=D(10000)),ns["VisualStrategy"],data)
        self.assertEqual(a.scenarios,b.scenarios)
        for s in a.scenarios:
            actions=[o.detail for o in s.orders if o.status=="strategy_audit" and o.detail.startswith("management:")]
            self.assertEqual(actions,["management:long:partial:requested","management:long:target:amended","management:long:lock:amended"])
            self.assertEqual(s.fills[-1].reason,"conditional_profit_lock_stop")
            self.assertEqual(s.open_quantity,0)
    def test_all_and_full_exit_priority(self):
        raw=setup();raw["management"]["mode"]="all"
        data=bars([(102,102,102,102),(102,110,99,110),(110,112,109,110),(110,112,109,110)])
        a=run(cfg(initial_equity=D(10000)),lambda:GraphStrategy(Graph.model_validate(raw)),data)
        for s in a.scenarios:
            actions=[o for o in s.orders if o.status=="strategy_audit" and o.detail.startswith("management:")]
            self.assertEqual(len(actions),3)
            self.assertEqual(len({o.event_utc for o in actions}),1)
        raw["long_exit"]=rule("gt","105")
        a=run(cfg(initial_equity=D(10000)),lambda:GraphStrategy(Graph.model_validate(raw)),data)
        self.assertTrue(all(not any(o.detail.startswith("management:") for o in s.orders) for s in a.scenarios))
    def test_machine_audit_and_validation(self):
        raw=machine_setup();raw["management"]={"priority":["lock","target","partial"],"audit":True}
        data=bars([(90,90,90,90),(110,110,110,110),(95,95,95,95),(95,120,95,115)])
        a=run(cfg(initial_equity=D(10000)),lambda:GraphStrategy(Graph.model_validate(raw)),data)
        for s in a.scenarios:
            self.assertTrue(any(o.status=="strategy_audit" and o.detail.startswith("entry_machine:long:0->1:") for o in s.orders))
        raw["management"]["priority"]=["lock","lock","partial"]
        with self.assertRaises(ValueError):Graph.model_validate(raw)
        self.assertNotIn("management",compile_graph(Graph.model_validate(graph()))["graph"])

if __name__=="__main__":unittest.main()
