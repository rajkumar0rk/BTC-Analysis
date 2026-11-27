import unittest
from decimal import Decimal as D
from datetime import timedelta
from btc_analysis.visual import Graph,compile_graph,recover_graph
from btc_analysis.service.historical import GraphStrategy
from btc_analysis.service.optimization import Search,variants
from test_visual import graph,rule
from test_backtest_engine import cfg,bars,run,T

def setup():
    raw=graph()
    raw["advanced"]={"exit_mode":"points","stop_points":"30","target_points":"100"}
    raw["long_exit"]=rule("lt","105")
    raw["long_exit_machine"]={"state_count":3,"expiry_bars":4,"transitions":[
        {"source":0,"target":1,"rule":rule("gt","110")},
        {"source":1,"target":2,"rule":rule("lt","105")}],
        "reset":rule("lt","80")}
    return raw

class ExitMachineTests(unittest.TestCase):
    def test_rule_exit_and_generated_parity(self):
        g=Graph.model_validate(setup());c=compile_graph(g);ns={}
        exec(compile(c["source"],"<trusted-generated>","exec"),ns)
        self.assertEqual(recover_graph(c["source"]),c)
        data=bars([(102,102,102,102),(102,103,101,102),(102,112,102,112),(112,112,104,104),(104,104,104,104)])
        a=run(cfg(n=5,initial_equity=D(10000)),lambda:GraphStrategy(g),data)
        b=run(cfg(n=5,initial_equity=D(10000)),ns["VisualStrategy"],data)
        self.assertEqual(a.scenarios,b.scenarios)
        for s in a.scenarios:
            self.assertEqual(len(s.closed_trades),1)
            self.assertEqual(s.fills[-1].reason,"visual_long_rule_exit")
            self.assertEqual(s.fills[-1].event_utc,T+timedelta(minutes=4))
    def test_protective_stop_not_gated(self):
        g=Graph.model_validate(setup())
        data=bars([(102,102,102,102),(102,103,101,102),(102,102,60,60),(60,60,60,60)])
        a=run(cfg(initial_equity=D(10000)),lambda:GraphStrategy(g),data)
        for s in a.scenarios:
            self.assertEqual(len(s.closed_trades),1)
            self.assertNotEqual(s.fills[-1].reason,"visual_long_rule_exit")
            self.assertEqual(s.open_quantity,D(0))
    def test_lifecycle_direction_and_reset(self):
        obj=GraphStrategy(Graph.model_validate(setup()))
        class C:position_quantity=D(0)
        ctx=C();flags={0,1};reset=False
        obj.exit_machine_transition=lambda c,d,i:i in flags
        obj.exit_machine_reset=lambda c,d:reset
        def step():
            obj.signal_count+=1
            return obj.machine_ready(ctx,1,position_exit=True)
        self.assertFalse(step())
        ctx.position_quantity=D(-1);self.assertFalse(step())
        ctx.position_quantity=D(1);self.assertFalse(step());self.assertTrue(step())
        reset=True;self.assertFalse(step())
        reset=False;self.assertFalse(step());self.assertTrue(step())
        ctx.position_quantity=D(0);self.assertFalse(step())
        ctx.position_quantity=D(1);self.assertFalse(step())
        flags=set()
        for _ in range(5):self.assertFalse(step())
        self.assertEqual(obj.exit_machine_state[1],(0,None))
    def test_validation_axes_and_legacy(self):
        raw=setup();c=compile_graph(Graph.model_validate(raw))
        opts=variants(c["graph"],Search.model_validate({"axes":[{"key":"exit_machine:long.expiry_bars","values":["3","4"]}]}))
        self.assertEqual(len(opts),2)
        raw["long_exit"]["enabled"]=False
        with self.assertRaises(ValueError):Graph.model_validate(raw)
        self.assertNotIn("long_exit_machine",compile_graph(Graph.model_validate(graph()))["graph"])

if __name__=="__main__":unittest.main()
