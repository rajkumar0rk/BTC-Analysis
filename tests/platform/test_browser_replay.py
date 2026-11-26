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

    def test_cache_reuse_and_parameter_invalidation(self):
        from btc_analysis.service.browser_cache import ReplayCache
        from copy import deepcopy
        g=graph()
        g["long_entry"]["groups"][0]["conditions"][0]["right"]={"kind":"indicator","name":"ema.value","timeframe":60,"parameters":{"period":3}}
        cache=ReplayCache()
        def run(g,settings=SETTINGS,data=None,use_cache=True):
            return replay(data or csv_text(),json.dumps(g),"BTCUSD",settings,True,cache=cache if use_cache else None)
        a=run(g);self.assertEqual(a,run(g,use_cache=False))
        self.assertFalse(cache.stats["candle_hit"]);self.assertEqual(cache.stats["indicator_misses"],1)
        self.assertEqual(cache.stats["indicator_hits"],1)
        b=run(g);self.assertEqual(a,b);self.assertTrue(cache.stats["candle_hit"])
        self.assertEqual(cache.stats["indicator_hits"],2);self.assertEqual(cache.stats["indicator_misses"],0)
        changed=deepcopy(g);changed["stop_loss_pct"]="2"
        self.assertEqual(run(changed),run(changed,use_cache=False));self.assertEqual(cache.stats["indicator_misses"],0)
        changed["long_entry"]["groups"][0]["conditions"][0]["right"]["parameters"]["period"]=7
        self.assertEqual(run(changed),run(changed,use_cache=False));self.assertEqual(cache.stats["indicator_misses"],1)
        self.assertEqual(run(g,data=csv_text().replace(",1\n",",2\n")),run(g,data=csv_text().replace(",1\n",",2\n"),use_cache=False))
        self.assertFalse(cache.stats["candle_hit"])
