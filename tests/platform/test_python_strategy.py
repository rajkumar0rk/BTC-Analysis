import unittest
from btc_analysis.service.python_strategy import Program,prepare_python
from btc_analysis.service.browser_replay import replay
from test_browser_replay import SETTINGS,csv_text

SOURCE="""from decimal import Decimal as D
from btc_analysis.strategy import PythonStrategy
from btc_analysis.contracts import Timeframe

class Strategy(PythonStrategy):
    signal_seconds = 60
    exposure = D("0.5")

    def __init__(self):
        self.entered = False

    def on_signal(self, ctx):
        if not self.entered:
            self.buy(ctx, D("0.1"), "custom_entry")
            self.entered = True
        elif ctx.position_quantity > 0:
            self.close_position(ctx, "custom_exit")
"""

class PythonStrategyTests(unittest.TestCase):
    def test_paste_plain_python_runs(self):
        r=replay(csv_text(),SOURCE,"BTCUSD",SETTINGS,True,details=True)
        self.assertTrue(all(s["metrics"]["trades"]==1 for s in r["scenarios"]))
        self.assertTrue(all(s["details"]["trades"][0]["entry_reason"]=="custom_entry" for s in r["scenarios"]))
        self.assertEqual(r,replay(csv_text(),SOURCE,"BTCUSD",SETTINGS,True,details=True))
        changed=SOURCE.replace('D("0.1")','D("0.2")')
        self.assertNotEqual(r["graph_sha256"],replay(csv_text(),changed,"BTCUSD",SETTINGS,True)["graph_sha256"])

    def test_reject_unsafe_or_unbounded_source(self):
        for src in ("import os\n"+SOURCE, SOURCE.replace("self.entered = False","self.entered = self.__class__"),
                    SOURCE.replace("self.entered = False","self.entered = open('/tmp/test')"),
                    SOURCE.replace("self.entered = False","while True:\n            pass"),
                    SOURCE.replace("self.entered = False","self.entered = 10 ** 100000")):
            with self.assertRaises((ValueError,SyntaxError)):prepare_python(src)
        with self.assertRaises(ValueError):replay(csv_text(),SOURCE.replace('self.buy(ctx, D("0.1"), "custom_entry")','ctx._sim'),"BTCUSD",SETTINGS,True)
        with self.assertRaises(ValueError):replay(csv_text(),SOURCE.replace('self.buy(ctx, D("0.1"), "custom_entry")','open("secret")'),"BTCUSD",SETTINGS,True)

    def test_indicator_and_state(self):
        src=SOURCE.replace("    def __init__(self):", """    def indicators(self):
        return (spec("ema", Timeframe(60), period=3),)

    def __init__(self):""").replace("if not self.entered:","if not self.entered and ctx.indicator('ema', Timeframe(60), {'period': 3}) is not None:")
        r=replay(csv_text(),src,"BTCUSD",SETTINGS,True)
        self.assertTrue(all(s["metrics"]["trades"]==1 for s in r["scenarios"]))

if __name__=="__main__":unittest.main()
