import unittest
from datetime import timedelta
from decimal import Decimal as D
from types import SimpleNamespace as NS
from btc_analysis.visual import Graph,compile_graph,recover_graph
from btc_analysis.service.historical import GraphStrategy
from btc_analysis.contracts import Side
from test_visual import graph
from test_backtest_engine import T,I,cfg,bars,run

def advanced(**kwargs):
    return Graph.model_validate({**graph(),"advanced":kwargs})

class AdvancedVisualTests(unittest.TestCase):
    def test_legacy_source_and_hash_unchanged(self):
        original=compile_graph(Graph.model_validate(graph()))
        self.assertNotIn("advanced",original["graph"])
        self.assertEqual(original,compile_graph(Graph.model_validate({**graph(),"advanced":None})))
        self.assertEqual(recover_graph(original["source"]),original)

    def test_config_and_exact_generated_parity(self):
        g=advanced(exit_mode="points",stop_points="10",target_points="20",confirmation_bars=2,entry_mode="once_per_true_run")
        a=compile_graph(g)
        self.assertEqual(a,recover_graph(a["source"]))
        ns={};exec(compile(a["source"],"<trusted-compiler-fixture>","exec"),ns)
        d=bars([(1000,1001,999,1000),(1000,1001,999,1000),(1000,1025,985,1000),(1000,1001,999,1000)])
        # Fixture lot size is one whole unit. At 20% exposure and a
        # 1000-point entry, 1000 equity would round quantity down to zero.
        # Fund two units explicitly so this actually exercises the bracket.
        config=cfg(initial_equity=D(10000))
        x=run(config,lambda:GraphStrategy(g),d)
        y=run(config,ns["VisualStrategy"],d)
        self.assertEqual(x.scenarios,y.scenarios)
        for s in x.scenarios:
            self.assertEqual(len(s.closed_trades),1)
            self.assertEqual(len(s.fills),2)
            self.assertEqual(s.fills[0].quantity,D(2))
            self.assertEqual(s.fills[0].price,D(1000))
            self.assertEqual(s.fills[0].event_utc,T+timedelta(minutes=2))
            self.assertEqual(s.fills[-1].event_utc,T+timedelta(minutes=3))
            self.assertEqual(s.open_quantity,D(0))
            self.assertEqual(s.fills[-1].reason,"fixed_point_target" if s.path=="O-H-L-C" else "fixed_point_stop")
            self.assertEqual(s.fills[-1].price,D(1020 if s.path=="O-H-L-C" else 990))

    def test_cycle_confirmation_cooldown_weekdays(self):
        g=advanced(entry_mode="once_per_true_run",confirmation_bars=2,cooldown_bars=2,weekdays_ist=[0,1,2,3,4])
        obj=GraphStrategy(g)
        class C:
            now_utc=T
            instrument=I
            equity=D(10000)
            position_quantity=D(0)
            active=True
            def candles(self,tf,limit):
                return (NS(close=D(1000),close_utc=self.now_utc),)
            def submit(self,o):orders.append(o)
        ctx=C();orders=[]
        obj.long_entry=lambda c:c.active
        obj.short_entry=lambda c:False
        def step():
            obj.on_signal(ctx);ctx.now_utc+=timedelta(minutes=1)
        step();self.assertEqual(len(orders),0)
        step();self.assertEqual(len(orders),1)
        obj.on_fill(ctx,NS(reason="visual_long_entry"))
        obj.on_fill(ctx,NS(reason="visual_stop_loss"))
        step();step();step();self.assertEqual(len(orders),1)
        ctx.active=False;step()
        ctx.active=True;step();self.assertEqual(len(orders),1)
        step();self.assertEqual(len(orders),2)
        ctx.now_utc=T+timedelta(days=3)
        ctx.active=False;step();ctx.active=True;step();step()
        self.assertEqual(len(orders),2)
        ctx.now_utc=T+timedelta(days=5);step()
        self.assertEqual(len(orders),3)

    def test_bad_controls_fail_closed(self):
        for kw in (dict(weekdays_ist=[]),dict(weekdays_ist=[1,1]),dict(confirmation_bars=0),dict(cooldown_bars=-1),dict(stop_points="0")):
            with self.assertRaises(ValueError):advanced(**kw)

if __name__=="__main__":unittest.main()
