import unittest
from decimal import Decimal as D
from btc_analysis.visual import Graph,compile_graph,recover_graph
from btc_analysis.service.historical import GraphStrategy
from btc_analysis.service.optimization import Search,variants
from test_visual import graph,rule
from test_backtest_engine import cfg,bars,run

def setup():
    raw=graph()
    raw["advanced"]={"exit_mode":"points","stop_points":"10","target_points":"20"}
    raw["long_machine"]={"state_count":4,"expiry_bars":3,"transitions":[
        {"source":0,"target":1,"rule":rule("gt","100")},
        {"source":0,"target":2,"rule":rule("lt","90")},
        {"source":1,"target":3,"rule":rule("lt","100")},
        {"source":2,"target":0,"rule":rule("gt","100")},
        {"source":2,"target":3,"rule":rule("gt","80")}],
        "reset":rule("lt","70")}
    raw["long_entry"]=rule("gt","80")
    return raw

class MachineTests(unittest.TestCase):
    def test_generated_and_native_parity(self):
        g=Graph.model_validate(setup());c=compile_graph(g);ns={}
        exec(compile(c["source"],"<trusted-generated>","exec"),ns)
        self.assertEqual(recover_graph(c["source"]),c)
        data=bars([(90,90,90,90),(110,110,110,110),(95,95,95,95),(95,120,95,115)])
        a=run(cfg(initial_equity=D(10000)),lambda:GraphStrategy(g),data)
        b=run(cfg(initial_equity=D(10000)),ns["VisualStrategy"],data)
        self.assertEqual(a.scenarios,b.scenarios)
        self.assertTrue(a.scenarios[0].closed_trades)
    def test_priority_reset_expiry_and_loops(self):
        obj=GraphStrategy(Graph.model_validate(setup()))
        class C:position_quantity=D(0)
        ctx=C();flags=set();reset=False
        obj.machine_transition=lambda c,d,i:i in flags
        obj.machine_reset=lambda c,d:reset
        def step():
            obj.signal_count+=1
            return obj.sequence_ready(ctx,1)
        flags={0,1,2}
        self.assertFalse(step());self.assertEqual(obj.machine_state[1][0],1)
        self.assertTrue(step());self.assertEqual(obj.machine_state[1][0],3)
        reset=True;self.assertFalse(step());self.assertEqual(obj.machine_state[1],(0,None))
        reset=False;flags={1};self.assertFalse(step());self.assertEqual(obj.machine_state[1][0],2)
        flags={3,4};self.assertFalse(step());self.assertEqual(obj.machine_state[1],(0,None))
        flags={0};self.assertFalse(step())
        flags=set()
        for _ in range(4):self.assertFalse(step())
        self.assertEqual(obj.machine_state[1],(0,None))
        flags={0};self.assertFalse(step())
        ctx.position_quantity=D(1);self.assertFalse(step());self.assertEqual(obj.machine_state[1],(0,None))
    def test_validation_axes_and_legacy(self):
        raw=setup();c=compile_graph(Graph.model_validate(raw))
        opts=variants(c["graph"],Search.model_validate({"axes":[{"key":"machine:long.expiry_bars","values":["3","4"]}]}))
        self.assertEqual(len(opts),2)
        for mutate in (
            lambda m:m.update(state_count=5),
            lambda m:m["transitions"].append(m["transitions"][0]),
            lambda m:m["transitions"].append({"source":3,"target":0,"rule":rule()}),
            lambda m:m["transitions"][0].update(target=0)):
            bad=setup();mutate(bad["long_machine"])
            with self.assertRaises(ValueError):Graph.model_validate(bad)
        bad=setup();bad["long_sequence"]={"stages":[rule(),rule()],"expiry_bars":3}
        with self.assertRaises(ValueError):Graph.model_validate(bad)
        self.assertNotIn("long_machine",compile_graph(Graph.model_validate(graph()))["graph"])

if __name__=="__main__":unittest.main()
