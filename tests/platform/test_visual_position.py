import unittest
from decimal import Decimal as D
from datetime import timedelta
from btc_analysis.visual import Graph,compile_graph,recover_graph
from btc_analysis.service.historical import GraphStrategy,frames
from btc_analysis.backtest.engine import Context
from test_visual import graph,rule
from test_backtest_engine import cfg,bars,run,T

def setup():
    raw=graph()
    raw["advanced"]={"exit_mode":"points","stop_points":"30","target_points":"100"}
    raw["long_exit"]=rule("gte","1")
    raw["long_exit"]["groups"][0]["conditions"][0]["left"]={"kind":"position","field":"position_holding_minutes"}
    return raw

class PositionTests(unittest.TestCase):
    def test_native_generated_parity(self):
        g=Graph.model_validate(setup());c=compile_graph(g);ns={}
        exec(compile(c["source"],"<trusted-generated>","exec"),ns)
        self.assertEqual(recover_graph(c["source"]),c)
        self.assertEqual(frames(g),(60,))
        data=bars([(102,102,102,102),(102,103,101,102),(102,102,102,102),(102,102,102,102)])
        raw=setup();raw["long_entry"]=rule("gt","101")
        # Allow just one entry, so final closed trade and timestamps are unambiguous.
        raw["advanced"]["entry_mode"]="once_per_true_run"
        g=Graph.model_validate(raw);c=compile_graph(g);ns={}
        exec(compile(c["source"],"<trusted-generated>","exec"),ns)
        a=run(cfg(initial_equity=D(10000)),lambda:GraphStrategy(g),data)
        b=run(cfg(initial_equity=D(10000)),ns["VisualStrategy"],data)
        self.assertEqual(a.scenarios,b.scenarios)
        for s in a.scenarios:
            self.assertEqual(len(s.closed_trades),1)
            self.assertEqual(s.fills[0].event_utc,T+timedelta(minutes=1))
            self.assertEqual(s.fills[-1].event_utc,T+timedelta(minutes=2))
            self.assertEqual(s.fills[-1].reason,"visual_long_rule_exit")
    def test_snapshots_close_sampling_and_flat(self):
        snapshots=[]
        class Probe(GraphStrategy):
            def on_signal(self,ctx):
                if ctx.position_quantity:
                    snapshots.append((ctx.position_entry_price,ctx.position_return_pct,ctx.position_holding_minutes,
                                      ctx.position_mfe_points,ctx.position_mae_points,ctx.position_unrealized_pnl))
                else:
                    self.assert_flat(ctx)
                super().on_signal(ctx)
            @staticmethod
            def assert_flat(ctx):
                assert ctx.position_entry_price is None and ctx.position_mfe_points is None and ctx.position_unrealized_pnl is None
        raw=setup();raw["long_exit"]["enabled"]=False
        g=Graph.model_validate(raw)
        data=bars([(102,102,102,102),(102,120,95,110),(110,112,90,100),(100,100,100,100)])
        run(cfg(initial_equity=D(10000)),lambda:Probe(g),data)
        self.assertTrue(snapshots)
        self.assertEqual(snapshots[0][0],D(102))
        self.assertEqual(snapshots[0][2:5],(D(1),D(8),D(0)))
        self.assertEqual(snapshots[1][3:5],(D(8),D(2)))
        self.assertGreater(snapshots[0][-1],0)
        self.assertLess(snapshots[1][-1],0)
    def test_crossovers_rejected_and_old_graph_unchanged(self):
        raw=setup();raw["long_exit"]["groups"][0]["conditions"][0]["op"]="cross_up"
        with self.assertRaises(ValueError):Graph.model_validate(raw)
        c=compile_graph(Graph.model_validate(graph()))
        self.assertEqual(recover_graph(c["source"]),c)

if __name__=="__main__":unittest.main()
