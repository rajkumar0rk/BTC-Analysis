import unittest
from decimal import Decimal as D
from btc_analysis.backtest import BaseStrategy
from btc_analysis.contracts import Timeframe,Side
from btc_analysis.service.python_strategy import prepare_python
from btc_analysis.service.strategy_authoring import validate_source
from btc_analysis.service.historical import GraphStrategy
from btc_analysis.service.optimization import Search,variants
from btc_analysis.visual import Graph,compile_graph,recover_graph
from test_backtest_engine import cfg,bars,run,submit
from test_visual import graph

class PercentLong(BaseStrategy):
    fixed_point_bracket=(D(100),None)
    trailing_stop_pct=(D(10),D(5))
    def on_start(self,c):submit(c,"entry")
class PercentShort(PercentLong):
    def on_start(self,c):submit(c,"entry",side=Side.SELL)
class ATRLong(BaseStrategy):
    fixed_point_bracket=(D(100),None)
    trailing_stop_atr=(D(10),Timeframe(60),1,D(2))
    def on_start(self,c):submit(c,"entry")
class ATRShort(ATRLong):
    def on_start(self,c):submit(c,"entry",side=Side.SELL)

class DynamicTrailingTests(unittest.TestCase):
    def test_percentage_long_and_short(self):
        d=bars([(1000,1150,850,1000)]+[(1000,1000,1000,1000)]*3)
        for s in run(cfg(),PercentLong,d).scenarios:
            first=s.path=="O-H-L-C"
            self.assertEqual(s.fills[-1].price,D(1092 if first else 900))
            self.assertEqual(s.fills[-1].reason,"trailing_percent_stop" if first else "fixed_point_stop")
        for s in run(cfg(),PercentShort,d).scenarios:
            first=s.path=="O-L-H-C"
            self.assertEqual(s.fills[-1].price,D(893 if first else 1100))
            self.assertEqual(s.fills[-1].reason,"trailing_percent_stop" if first else "fixed_point_stop")

    def test_completed_atr_not_current_candle(self):
        # First candle ATR=20, known only after its close. Second candle
        # range is 160, which must NOT be used for the intrabar stop.
        for cls,high,low,expected in ((ATRLong,1150,990,1110),(ATRShort,1010,850,890)):
            d=bars([(1000,1010,990,1000),(1000,high,low,1000),(1000,1000,1000,1000),(1000,1000,1000,1000)])
            for s in run(cfg(),cls,d).scenarios:
                self.assertEqual(s.fills[-1].price,D(expected))
                self.assertEqual(s.fills[-1].reason,"trailing_atr_stop")
                self.assertEqual(s.open_quantity,0)
        # ATR not initialized at entry: first-minute high must not activate
        # a trailing stop from an unfinished candle.
        d=bars([(1000,1150,850,1000)]+[(1000,1000,1000,1000)]*3)
        for s in run(cfg(),ATRLong,d).scenarios:
            self.assertEqual(s.fills[-1].price,D(900))
            self.assertEqual(s.fills[-1].reason,"fixed_point_stop")

    def test_python_declaration_and_validation(self):
        source='''from decimal import Decimal as D
from btc_analysis.strategy import PythonStrategy
from btc_analysis.contracts import Timeframe
class Strategy(PythonStrategy):
    fixed_point_bracket = (D("100"), None)
    trailing_stop_atr = (D("10"), Timeframe(300), 14, D("2"))
    def on_signal(self, ctx):
        pass
'''
        self.assertTrue(validate_source(source)["valid"])
        _,_,frames=prepare_python(source)
        self.assertEqual(frames,(60,300))
        for bad in (source.replace('D("2")','D("0")'),
                    source.replace('14, D','0, D'),
                    source.replace('    def on_signal','    trailing_stop_pct = (D("1"), D("0.5"))\n    def on_signal')):
            self.assertFalse(validate_source(bad)["valid"])

    def test_generated_visual_parity_and_optimization(self):
        raw={**graph(),"advanced":{"exit_mode":"points","entry_mode":"once_per_true_run","stop_points":"100","target_enabled":False,
                "trailing_atr":{"activation":"10","timeframe":60,"period":1,"multiplier":"2"}}}
        g=Graph.model_validate(raw)
        c=compile_graph(g);ns={}
        exec(compile(c["source"],"<trusted-generated-fixture>","exec"),ns)
        self.assertEqual(recover_graph(c["source"]),c)
        d=bars([(1000,1010,990,1000),(1000,1150,990,1000)]+[(1000,1000,1000,1000)]*2)
        config=cfg(initial_equity=D(10000))
        a=run(config,lambda:GraphStrategy(g),d)
        b=run(config,ns["VisualStrategy"],d)
        self.assertEqual(a.scenarios,b.scenarios)
        self.assertEqual([s.fills[-1].price for s in a.scenarios],[D(1110),D(1110)])
        choices=variants(c["graph"],Search.model_validate({"axes":[{"key":"advanced:trailing_atr.period","values":["1","2"]}]}))
        self.assertEqual([x[1]["graph"]["advanced"]["trailing_atr"]["period"] for x in choices],[1,2])
        raw["advanced"]["trailing_percent"]={"activation":"1","distance":"1"}
        with self.assertRaises(ValueError):Graph.model_validate(raw)

if __name__=="__main__":unittest.main()
