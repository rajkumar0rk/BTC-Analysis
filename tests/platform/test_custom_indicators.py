import unittest
from decimal import Decimal as D
from datetime import timedelta
from btc_analysis.contracts import Timeframe,Candle
from btc_analysis.service.python_strategy import prepare_python
from btc_analysis.service.strategy_authoring import validate_source,apply_parameters
from btc_analysis.service.browser_replay import replay
from test_browser_replay import SETTINGS,csv_text
from test_backtest_engine import T,I

SOURCE="""from decimal import Decimal as D
from btc_analysis.strategy import PythonStrategy
from btc_analysis.contracts import Timeframe

class Strategy(PythonStrategy):
    signal_seconds = 60
    period = parameter(3, 2, 10)
    weight = parameter(D("0.5"), D("0.1"), D("1"))

    def custom_indicators(self):
        return (
            ("rolling", Timeframe(60), self.period, "rolling_formula"),
            ("recursive", Timeframe(900), 1, "recursive_formula"),
        )

    def rolling_formula(self, bars, previous):
        return mean(series(bars, "close"))

    def recursive_formula(self, bars, previous):
        close = bars[-1].close
        if previous is None:
            return close
        return previous + self.weight * (close - previous)

    def on_signal(self, ctx):
        value = self.custom_value("rolling")
        if value is not None and ctx.position_quantity == 0:
            self.buy(ctx, D("0.1"), "custom_entry")
        elif ctx.position_quantity > 0:
            self.close_position(ctx, "custom_exit")
"""

def candle(index,seconds,price):
    start=T+timedelta(seconds=index*seconds)
    v=D(price)
    return Candle(I,Timeframe(seconds),start,start+timedelta(seconds=seconds),v,v,v,v,D(1))

class CustomIndicatorsTests(unittest.TestCase):
    def test_declarations_and_completed_bar_values(self):
        report=validate_source(SOURCE)
        self.assertTrue(report["valid"],report)
        self.assertEqual(report["timeframes"],[60,900])
        self.assertEqual([x["name"] for x in report["custom_indicators"]],["rolling","recursive"])
        program,_,_=prepare_python(SOURCE)
        a=program.make();b=program.make()
        for i,v in enumerate((10,20,30,40)):
            a.on_completed_candle(candle(i,60,v))
        self.assertEqual(tuple(a.custom["rolling"][3]),(None,None,D(20),D(30)))
        self.assertEqual(tuple(a.custom["recursive"][3]),())
        a.on_completed_candle(candle(0,900,40));a.on_completed_candle(candle(1,900,60))
        self.assertEqual(tuple(a.custom["recursive"][3]),(D(40),D(50)))
        self.assertEqual(tuple(b.custom["rolling"][3]),())
        with self.assertRaises(ValueError):a.on_completed_candle(candle(3,60,40))
        changed=apply_parameters(SOURCE,{"period":"4"})["source"]
        q,_,_=prepare_python(changed)
        self.assertEqual(q.make().custom["rolling"][2].maxlen,4)

    def test_replay_causal_and_deterministic(self):
        r=replay(csv_text(),SOURCE,"BTCUSD",SETTINGS,True,details=True)
        self.assertEqual(r,replay(csv_text(),SOURCE,"BTCUSD",SETTINGS,True,details=True))
        for s in r["scenarios"]:
            self.assertGreater(s["metrics"]["trades"],0)
            first=s["details"]["trades"][0]["entry_fills"][0]
            # 3 completed minutes before next-open entry. No warmup/future access.
            from datetime import datetime
            t=datetime.fromisoformat(first["event_utc"].replace("Z","+00:00"))
            start=datetime.fromtimestamp(int(csv_text().splitlines()[1].split(",")[0]),t.tzinfo)
            self.assertGreaterEqual(t,start+timedelta(minutes=3))

    def test_formula_isolation_and_validation(self):
        for changed in (
            SOURCE.replace('return mean(series(bars, "close"))','self.period = 4\n        return D("1")'),
            SOURCE.replace('return mean(series(bars, "close"))','return self.custom_value("recursive")'),
            SOURCE.replace('return mean(series(bars, "close"))','return self.position'),
            SOURCE.replace('return mean(series(bars, "close"))','self.buy(bars, D("1"), "bad")\n        return D("1")'),
            SOURCE.replace('"rolling_formula"),','"on_signal"),'),
            SOURCE.replace('Timeframe(60), self.period','Timeframe(60), 4097'),
        ):
            self.assertFalse(validate_source(changed)["valid"],changed)
        changed=SOURCE.replace('return mean(series(bars, "close"))','return "invalid"')
        with self.assertRaisesRegex(ValueError,"number or None"):
            replay(csv_text(),changed,"BTCUSD",SETTINGS,True)

if __name__=="__main__":unittest.main()
