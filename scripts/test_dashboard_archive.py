import unittest
from dashboard_archive import normalize,stats,curve,SCHEMAS
ETH_SCHEMA=next(s for s in SCHEMAS if s['symbol']=='ETHUSD')
class ArchiveTest(unittest.TestCase):
    def test_missing_fields_not_inferred(self):
        row=dict(model="test",direction="LONG",entry_unix=1735689600,exit_unix=1735689660,entry_price_usd=3300,net_eth_price_points=-1,result="SL",pattern="ema20_pullback")
        t=normalize(row,ETH_SCHEMA)
        self.assertIsNone(t["exit_price"])
        self.assertIsNone(t["stop_price"])
        self.assertEqual(t["entry_reason"],"ema20_pullback")
        self.assertEqual(stats([t])["drawdown"],1)
        self.assertEqual(curve([t])[-1][1:],[-1,1])
    def test_invalid_row_rejected(self):
        self.assertIsNone(normalize({},ETH_SCHEMA))
if __name__=="__main__":unittest.main()
