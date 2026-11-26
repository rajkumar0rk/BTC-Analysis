import unittest
from recover_delta_2024 import recover,validate,gaps,seed_btc
from stage_repository_history import month_bounds
from pathlib import Path

class RecoveryTests(unittest.TestCase):
    def test_preserve_seed_and_never_fill_missing(self):
        a,b=month_bounds("2024-02")
        step=3600
        def row(t,price=1):return dict(time=t,open=price,high=price,low=price,close=price)
        seed={t:validate(row(t),"funding_1h",step) for t in range(a,b,step) if t not in (a+step,a+2*step)}
        def api(symbol,res,lo,hi):
            self.assertEqual(symbol,"FUNDING:BTCUSD")
            return [row(a+step),row(a,2)]
        rows,m=recover("BTCUSD","2024-02","funding_1h",seed,api,pause=lambda _:None)
        self.assertEqual(m["recovered"],1);self.assertEqual(m["missing"],1);self.assertEqual(m["synthetic_rows"],0)
        self.assertEqual(rows[a],seed[a]);self.assertGreater(m["overlap_conflicts"],0)
        self.assertEqual(m["gaps_exclusive"],[[a+2*step,a+3*step]])
    def test_actual_btc_seed(self):
        root=Path(__file__).resolve().parents[1]
        a,b=month_bounds("2024-12")
        mark=seed_btc(root,"2024-12","mark_1m")
        funding=seed_btc(root,"2024-12","funding_1h")
        self.assertEqual(len(mark),(b-a)//60-330)
        self.assertEqual(len(funding),(b-a)//3600-6)
    def test_invalid_bar(self):
        with self.assertRaises(ValueError):validate(dict(time=0,open=10,high=9,low=8,close=10,volume=1),"trade_1m",60)
if __name__=="__main__":unittest.main()
