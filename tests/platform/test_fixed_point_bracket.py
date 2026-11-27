"""Generic engine contract; no application-specific strategy dependency."""
import unittest
from datetime import timedelta
from decimal import Decimal as D
from btc_analysis.backtest import BaseStrategy,run_backtest
from btc_analysis.contracts import Side
from test_backtest_engine import T,H,cfg,bars,submit

class BracketFixture(BaseStrategy):
    fixed_point_bracket=(D(100),D(200))
    def on_start(self,c):submit(c,"entry")

class ShortBracketFixture(BaseStrategy):
    fixed_point_bracket=(D(100),D(200))
    def on_start(self,c):submit(c,"entry",side=Side.SELL)

class FixedBracketTests(unittest.TestCase):
    def test_long_same_entry_minute_both_paths(self):
        data=bars([(1000,1250,850,1000)]+[(1000,1000,1000,1000)]*3)
        r=run_backtest(cfg(),BracketFixture,lambda:data,linear_contract=True,dataset_manifest_sha256=H)
        for s in r.scenarios:
            self.assertEqual(s.open_quantity,0)
            self.assertEqual(s.fills[-1].event_utc,T+timedelta(minutes=1))
            self.assertEqual(s.fills[-1].price,D(1200 if s.path=="O-H-L-C" else 900))
            self.assertEqual(s.fills[-1].reason,"fixed_point_target" if s.path=="O-H-L-C" else "fixed_point_stop")
            self.assertEqual(len(s.closed_trades),1)

    def test_short_same_entry_minute_both_paths(self):
        data=bars([(1000,1150,750,1000)]+[(1000,1000,1000,1000)]*3)
        r=run_backtest(cfg(),ShortBracketFixture,lambda:data,linear_contract=True,dataset_manifest_sha256=H)
        for s in r.scenarios:
            self.assertEqual(s.open_quantity,0)
            self.assertEqual(s.fills[-1].event_utc,T+timedelta(minutes=1))
            self.assertEqual(s.fills[-1].price,D(1100 if s.path=="O-H-L-C" else 800))
            self.assertEqual(s.fills[-1].reason,"fixed_point_stop" if s.path=="O-H-L-C" else "fixed_point_target")
            self.assertEqual(len(s.closed_trades),1)

if __name__=="__main__":unittest.main()
