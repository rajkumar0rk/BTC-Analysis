"""Generic managed exits: causal path, gaps, isolation, both authoring paths."""
import unittest
from decimal import Decimal as D
from dataclasses import replace
from datetime import timedelta
from btc_analysis.backtest import BaseStrategy
from btc_analysis.contracts import Side
from btc_analysis.visual import Graph,compile_graph,recover_graph
from btc_analysis.service.historical import GraphStrategy
from btc_analysis.service.python_strategy import prepare_python
from btc_analysis.service.strategy_authoring import validate_source
from test_backtest_engine import T,cfg,bars,run,submit
from test_visual import graph

class LongTrail(BaseStrategy):
    fixed_point_bracket=(D(100),D(300))
    trailing_stop_points=(D(100),D(50))
    def on_start(self,c):submit(c,"entry")

class ShortTrail(LongTrail):
    def on_start(self,c):submit(c,"entry",side=Side.SELL)

class LockOnly(LongTrail):
    trailing_stop_points=None
    profit_lock_points=(D(100),D(20))

class Combined(LongTrail):
    trailing_stop_points=(D(100),D(90))
    profit_lock_points=(D(100),D(50))

class ManagedExitTests(unittest.TestCase):
    def test_entry_minute_long_path_order(self):
        d=bars([(1000,1150,850,1000)]+[(1000,1000,1000,1000)]*3)
        result=run(cfg(),LongTrail,d)
        for s in result.scenarios:
            self.assertEqual(len(s.closed_trades),1)
            high_first=s.path=="O-H-L-C"
            self.assertEqual(s.fills[-1].price,D(1100 if high_first else 900))
            self.assertEqual(s.fills[-1].reason,"trailing_point_stop" if high_first else "fixed_point_stop")
            self.assertEqual(s.fills[-1].event_utc,T+timedelta(minutes=1))
            self.assertEqual(s.open_quantity,0)

    def test_entry_minute_short_path_order(self):
        d=bars([(1000,1150,850,1000)]+[(1000,1000,1000,1000)]*3)
        for s in run(cfg(),ShortTrail,d).scenarios:
            low_first=s.path=="O-L-H-C"
            self.assertEqual(s.fills[-1].price,D(900 if low_first else 1100))
            self.assertEqual(s.fills[-1].reason,"trailing_point_stop" if low_first else "fixed_point_stop")
            self.assertEqual(s.open_quantity,0)

    def test_ratchet_then_gap(self):
        d=bars([(1000,1120,990,1110),(1110,1150,1105,1140),(1050,1050,1050,1050),(1050,1050,1050,1050)])
        for s in run(cfg(),LongTrail,d).scenarios:
            # High-first first candle reaches 1120 before 990, so that
            # scenario closes at 1070 immediately; low-first survives.
            if s.path=="O-H-L-C":
                self.assertEqual(s.fills[-1].price,D(1070))
            else:
                self.assertEqual(s.fills[-1].price,D(1050))
                self.assertEqual(s.fills[-1].event_utc,T+timedelta(minutes=2))
                stops=[x.intent.stop_price for x in s.orders if x.status=="amended"]
                self.assertEqual(stops,[D(1070),D(1100)])
            self.assertEqual(s.fills[-1].reason,"trailing_point_stop")

    def test_lock_and_stronger_policy(self):
        d=bars([(1000,1120,990,1110),(1110,1110,1010,1010)]+[(1010,1010,1010,1010)]*2)
        for strategy,expected,reason in ((LockOnly,D(1020),"profit_lock_stop"),(Combined,D(1050),"profit_lock_stop")):
            for s in run(cfg(),strategy,d).scenarios:
                self.assertEqual(s.fills[-1].price,expected)
                self.assertEqual(s.fills[-1].reason,reason)

    def test_target_wins_on_favorable_traversal(self):
        d=bars([(1000,1350,990,1300)]+[(1300,1300,1300,1300)]*3)
        for s in run(cfg(),LongTrail,d).scenarios:
            self.assertEqual(s.fills[-1].price,D(1300))
            self.assertEqual(s.fills[-1].reason,"fixed_point_target")

    def test_validation_and_python_source(self):
        source='''from decimal import Decimal as D
from btc_analysis.strategy import PythonStrategy
class Strategy(PythonStrategy):
    fixed_point_bracket = (D("100"), D("300"))
    trailing_stop_points = (D("100"), D("50"))
    profit_lock_points = (D("100"), D("20"))
    def on_start(self, ctx):
        self.buy(ctx, D("1"), "entry")
'''
        self.assertTrue(validate_source(source)["valid"])
        p,_,_=prepare_python(source)
        d=bars([(1000,1150,850,1000)]+[(1000,1000,1000,1000)]*3)
        self.assertEqual([s.fills[-1].price for s in run(cfg(),p.make,d).scenarios],[D(1100),D(900)])
        self.assertFalse(validate_source(source.replace('D("100"), D("20")','D("100"), D("100")'))["valid"])
        self.assertFalse(validate_source(source.replace('    fixed_point_bracket = (D("100"), D("300"))\n',''))["valid"])
        bad=source.replace('D("100"), D("50")','D("100"), D("50.5")')
        p,_,_=prepare_python(bad)
        with self.assertRaisesRegex(ValueError,"tick multiples"):run(cfg(),p.make,d)

    def test_visual_parity_and_legacy_recovery(self):
        legacy=compile_graph(Graph.model_validate({**graph(),"advanced":{"exit_mode":"points"}}))
        self.assertNotIn("trailing",legacy["graph"]["advanced"])
        self.assertEqual(recover_graph(legacy["source"]),legacy)
        raw={**graph(),"advanced":{"exit_mode":"points","entry_mode":"once_per_true_run","stop_points":"100","target_points":"300","trailing":{"activation":"100","distance":"50"}}}
        g=Graph.model_validate(raw)
        c=compile_graph(g);ns={}
        exec(compile(c["source"],"<trusted-generated-fixture>","exec"),ns)
        self.assertEqual(recover_graph(c["source"]),c)
        d=bars([(1000,1000,1000,1000),(1000,1150,850,1000)]+[(1000,1000,1000,1000)]*2)
        config=cfg(initial_equity=D(10000))
        a=run(config,lambda:GraphStrategy(g),d)
        b=run(config,ns["VisualStrategy"],d)
        self.assertEqual(a.scenarios,b.scenarios)
        self.assertEqual([s.fills[-1].price for s in a.scenarios],[D(1100),D(900)])
        raw["advanced"]["exit_mode"]="percent"
        with self.assertRaises(ValueError):Graph.model_validate(raw)

if __name__=="__main__":unittest.main()
