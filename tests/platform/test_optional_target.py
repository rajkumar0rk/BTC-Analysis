import unittest
from decimal import Decimal as D
from btc_analysis.backtest import BaseStrategy
from btc_analysis.service.strategy_authoring import validate_source
from btc_analysis.visual import Graph,compile_graph,recover_graph
from test_visual import graph
from test_backtest_engine import cfg,bars,run,submit

class StopOnly(BaseStrategy):
    fixed_point_bracket=(D(100),None)
    def on_start(self,c):submit(c,"entry")

class OptionalTargetTests(unittest.TestCase):
    def test_stop_only(self):
        d=bars([(1000,1500,950,1400),(1400,1400,850,900),(900,900,900,900),(900,900,900,900)])
        for s in run(cfg(),StopOnly,d).scenarios:
            self.assertEqual(len(s.closed_trades),1)
            self.assertEqual(s.fills[-1].price,D(900))
            self.assertEqual(s.fills[-1].reason,"fixed_point_stop")
            self.assertFalse(any(o.intent and o.intent.reason=="fixed_point_target" for o in s.orders))
    def test_source_and_graph(self):
        source='''from decimal import Decimal as D
from btc_analysis.strategy import PythonStrategy
class Strategy(PythonStrategy):
    fixed_point_bracket = (D("100"), None)
    trailing_stop_points = (D("150"), D("50"))
    def on_signal(self, ctx):
        pass
'''
        self.assertTrue(validate_source(source)["valid"])
        raw={**graph(),"advanced":{"exit_mode":"points","target_enabled":False}}
        c=compile_graph(Graph.model_validate(raw))
        self.assertEqual(recover_graph(c["source"]),c)
        raw["advanced"]["exit_mode"]="percent"
        with self.assertRaises(ValueError):Graph.model_validate(raw)

if __name__=="__main__":unittest.main()
