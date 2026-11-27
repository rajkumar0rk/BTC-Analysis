import unittest
from dataclasses import replace
from decimal import Decimal as D
from btc_analysis.visual import Graph,compile_graph,recover_graph
from btc_analysis.service.historical import GraphStrategy
from test_visual import rule,disabled
from test_visual_conditional_lock import setup
from test_backtest_engine import cfg,bars,run

def config(n=4):
    c=cfg(n=n,initial_equity=D(10000))
    return replace(c,costs=replace(c.costs,taker_bps=D(10),tax_rate=D("0.18"),slippage_bps=D(50)))

class NetLockTests(unittest.TestCase):
    def test_long_costs_slippage_tick_and_parity(self):
        raw=setup();raw["long_lock"]["cost_adjusted"]=True
        g=Graph.model_validate(raw);c=compile_graph(g);ns={}
        exec(compile(c["source"],"<trusted-generated>","exec"),ns)
        self.assertEqual(recover_graph(c["source"]),c)
        data=bars([(102,102,102,102),(102,115,99,115),(115,116,100,101),(101,101,101,101)])
        a=run(config(),lambda:GraphStrategy(g),data)
        b=run(config(),ns["VisualStrategy"],data)
        self.assertEqual(a.scenarios,b.scenarios)
        for s in a.scenarios:
            self.assertEqual(len(s.closed_trades),1)
            self.assertEqual(s.fills[-1].reason,"conditional_net_profit_lock_stop")
            self.assertGreaterEqual(s.closed_trades[0].net_pnl,0)
            self.assertGreater(s.fills[-1].price,s.fills[0].price)
    def test_short_costs(self):
        raw=setup();raw.pop("long_lock");raw["long_entry"]=disabled();raw["short_entry"]=rule("lt","105")
        raw["short_lock"]={"locked_points":"0","cost_adjusted":True,"rule":rule("lt","95")}
        g=Graph.model_validate(raw)
        data=bars([(102,102,102,102),(102,105,89,90),(90,102,89,101),(101,101,101,101)])
        a=run(config(),lambda:GraphStrategy(g),data)
        for s in a.scenarios:
            self.assertEqual(s.fills[-1].reason,"conditional_net_profit_lock_stop")
            self.assertGreaterEqual(s.closed_trades[0].net_pnl,0)
            self.assertLess(s.fills[-1].price,s.fills[0].price)
    def test_realized_partial_and_gap(self):
        raw=setup();raw["long_partial"]={"pct":"50","rule":rule("gt","105")}
        raw["long_lock"]={"locked_points":"0","cost_adjusted":True,"rule":rule("gte","1")}
        # Delay until partial fill confirmed by remaining quantity.
        raw["long_lock"]["rule"]["groups"][0]["conditions"][0].update(left={"kind":"position","field":"position_quantity"},op="lt",right={"kind":"constant","value":"15"})
        g=Graph.model_validate(raw)
        data=bars([(102,102,102,102),(102,115,99,115),(115,116,109,110),(110,111,85,90),(90,90,90,90)])
        a=run(config(5),lambda:GraphStrategy(g),data)
        for s in a.scenarios:
            self.assertEqual(s.fills[1].reason,"visual_long_partial_exit")
            self.assertEqual(s.fills[-1].reason,"conditional_net_profit_lock_stop")
            self.assertLess(s.fills[-1].price,s.fills[0].price)
            self.assertGreaterEqual(s.closed_trades[0].net_pnl,0)
        gap=bars([(102,102,102,102),(102,115,99,115),(115,116,109,110),(85,86,84,85),(85,85,85,85)])
        a=run(config(5),lambda:GraphStrategy(g),gap)
        self.assertTrue(all(s.closed_trades[0].net_pnl<0 for s in a.scenarios))
    def test_legacy_source_and_gross_mode(self):
        raw=setup();g=Graph.model_validate(raw)
        c=compile_graph(g)
        self.assertNotIn("cost_adjusted",c["graph"]["long_lock"])
        self.assertEqual(g.lock_config(),{1:"0"})

if __name__=="__main__":unittest.main()
