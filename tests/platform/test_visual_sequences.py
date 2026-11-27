import unittest
from decimal import Decimal as D
from datetime import timedelta
from btc_analysis.visual import Graph,compile_graph,recover_graph
from btc_analysis.service.historical import GraphStrategy,frames
from btc_analysis.service.optimization import Search,variants
from test_visual import graph,rule
from test_backtest_engine import T,cfg,bars,run

def setup():
    return {**graph(),"advanced":{"exit_mode":"points","stop_points":"10","target_points":"20"},
            "long_sequence":{"stages":[rule("gt","100"),rule("lt","100")],"expiry_bars":3}}

class SequenceTests(unittest.TestCase):
    def test_order_and_generated_parity(self):
        raw=setup()
        raw["long_entry"]=rule("gt","80")
        g=Graph.model_validate(raw)
        c=compile_graph(g);ns={}
        exec(compile(c["source"],"<trusted-generated>","exec"),ns)
        self.assertEqual(recover_graph(c["source"]),c)
        d=bars([(90,90,90,90),(110,110,110,110),(95,95,95,95),(95,120,95,115)])
        a=run(cfg(initial_equity=D(10000)),lambda:GraphStrategy(g),d)
        b=run(cfg(initial_equity=D(10000)),ns["VisualStrategy"],d)
        self.assertEqual(a.scenarios,b.scenarios)
        for s in a.scenarios:
            self.assertEqual(len(s.closed_trades),1)
            self.assertEqual(s.fills[0].event_utc,T+timedelta(minutes=3))
            self.assertEqual(s.fills[-1].price,D(115))

    def test_reset_expiry_and_one_stage_per_candle(self):
        raw=setup();raw["long_sequence"]["reset"]=rule("lt","80")
        obj=GraphStrategy(Graph.model_validate(raw))
        class C:
            position_quantity=D(0)
        ctx=C()
        flags=[True,True];reset=False
        obj.sequence_stage=lambda c,d,i:flags[i]
        obj.sequence_reset=lambda c,d:reset
        def step():
            obj.signal_count+=1
            return obj.sequence_ready(ctx,1)
        self.assertFalse(step())
        self.assertTrue(step())
        reset=True;self.assertFalse(step())
        self.assertEqual(obj.sequence_state[1],(0,None))
        reset=False;flags[1]=False
        self.assertFalse(step())
        for _ in range(3):self.assertFalse(step())
        flags[1]=True
        self.assertFalse(step()) # expired, restarts first stage
        self.assertTrue(step())
        ctx.position_quantity=D(1);self.assertFalse(step())
        self.assertEqual(obj.sequence_state[1],(0,None))

    def test_validate_and_optimize(self):
        raw=setup()
        raw["long_sequence"]["stages"][0]["groups"][0]["conditions"][0]["left"]={"kind":"indicator","timeframe":300,"name":"ema.value","parameters":{"period":3}}
        g=Graph.model_validate(raw);self.assertEqual(frames(g),(60,300))
        c=compile_graph(g)
        options=variants(c["graph"],Search.model_validate({"axes":[{"key":"ema.value@300:period","values":["3","4"]},{"key":"sequence:long.expiry_bars","values":["3","4"]}]}))
        self.assertEqual(len(options),4)
        for patch in ({"expiry_bars":0},{"stages":[rule()]},{"reset":{"enabled":False,"groups":[]}}):
            bad=setup();bad["long_sequence"].update(patch)
            with self.assertRaises(ValueError):Graph.model_validate(bad)
        bad=setup();bad["advanced"]=None
        with self.assertRaises(ValueError):Graph.model_validate(bad)
        old=compile_graph(Graph.model_validate(graph()))
        self.assertNotIn("long_sequence",old["graph"])
        self.assertEqual(recover_graph(old["source"]),old)

if __name__=="__main__":unittest.main()
