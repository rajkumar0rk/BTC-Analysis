import unittest,json
from btc_analysis.service.browser_replay import replay
from btc_analysis.visual import compile_graph,Graph
from test_visual import graph

SETTINGS=dict(initial_equity="100",maker_bps="2",taker_bps="5",tax_rate="0.18",slippage_bps="0",tick_size="0.1",lot_size="0.001",multiplier="1")
def csv_text():
    return "time,open,high,low,close,volume\n"+"".join(f"{1735689600+i*60},{100+i%10},{103+i%10},{99+i%10},{102+i%10},1\n" for i in range(60))

class BrowserReplayTests(unittest.TestCase):
    def test_generated_source_and_graph_exact_parity(self):
        g=graph();c=compile_graph(Graph.model_validate(g))
        a=replay(csv_text(),json.dumps(g),"BTCUSD",SETTINGS,True)
        b=replay(csv_text(),c["source"],"BTCUSD",SETTINGS,True)
        self.assertEqual(a,b)
        self.assertEqual([s["bars"] for s in a["scenarios"]],[60,60])
        self.assertTrue(a["research_only"])
        self.assertTrue(any(s["metrics"]["trades"] for s in a["scenarios"]))
        print("Native browser replay reference hash:",a["result_sha256"])
    def test_bad_source_and_gaps_fail(self):
        c=compile_graph(Graph.model_validate(graph()))
        for source in ("import os",c["source"]+"\nraise RuntimeError('inert')"):
            with self.assertRaises(ValueError):replay(csv_text(),source,"BTCUSD",SETTINGS,True)
        with self.assertRaises(ValueError):replay(csv_text().replace("1735689660,","1735689720,"),json.dumps(graph()),"BTCUSD",SETTINGS,True)
        with self.assertRaises(ValueError):replay(csv_text(),json.dumps(graph()),"BTCUSD",SETTINGS,False)
