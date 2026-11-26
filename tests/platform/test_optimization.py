import unittest
from decimal import Decimal as D
from btc_analysis.service.optimization import Search,variants,rank_candidate
from btc_analysis.visual import Graph,compile_graph
from test_visual import graph

class OptimizationTests(unittest.TestCase):
    def test_grid_and_random(self):
        g=compile_graph(Graph.model_validate(graph()))["graph"]
        axes=[{"key":"stop_loss_pct","values":["1","2","3"]},{"key":"take_profit_pct","values":["2","4"]}]
        s=Search(axes=axes)
        self.assertEqual(len(variants(g,s)),6)
        random=Search(axes=axes,method="random",samples=3,seed=12)
        self.assertEqual(variants(g,random),variants(g,random))
        self.assertEqual(len(variants(g,random)),3)
        self.assertEqual(g,compile_graph(Graph.model_validate(graph()))["graph"])
        with self.assertRaises(ValueError):variants(g,Search(axes=axes+[{"key":"exposure_pct","values":["10","20"]}]))
    def test_axis_validation(self):
        g=compile_graph(Graph.model_validate(graph()))["graph"]
        for a in ({"key":"stop_loss_pct","values":["0"]},{"key":"ema.value@900:period","values":["5"]}):
            with self.assertRaises(ValueError):variants(g,Search(axes=[a]))
        with self.assertRaises(ValueError):Search(axes=[{"key":"stop_loss_pct","values":["1","1.0"]}])
    def test_conservative_ranking(self):
        s=Search(axes=[{"key":"stop_loss_pct","values":["1"]}],min_trades=2,max_drawdown_pct="10")
        m=[{"max_event_drawdown_pct":"5","trades":3,"account_return_pct":"7"},
           {"max_event_drawdown_pct":"12","trades":1,"account_return_pct":"-2"}]
        score,dd,trades,reasons=rank_candidate(m,s)
        self.assertEqual((score,dd,trades),(D(-2),D(12),1))
        self.assertEqual(reasons,["drawdown","minimum_trades"])
