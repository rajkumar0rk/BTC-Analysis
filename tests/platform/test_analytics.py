import unittest
from decimal import Decimal as D
from btc_analysis.service.analytics import summarize,analytics,trade_replay

def scenario(pnls):
    return {"path":"O-H-L-C","closed_trades":[{"net_pnl":str(x)} for x in pnls],"initial_equity":"100",
            "net_pnl":"7","max_event_drawdown_pct":"4","monthly":[{"pnl":"8"},{"pnl":"-1"},{"pnl":"0"}]}

class AnalyticsTests(unittest.TestCase):
    def test_net_closed_account_and_months(self):
        m=summarize(scenario([10,-5,0]))
        self.assertEqual((m["wins"],m["losses"],m["breakeven"]),(1,1,1))
        self.assertEqual(D(m["profit_factor"]),2)
        self.assertEqual(D(m["closed_trade_net"]),5)
        self.assertEqual(D(m["account_minus_closed"]),2)
        self.assertEqual((m["positive_months"],m["negative_months"],m["flat_months"]),(1,1,1))
    def test_undefined_and_no_loss(self):
        self.assertIsNone(summarize(scenario([]))["win_rate_pct"])
        self.assertEqual(summarize(scenario([1]))["profit_factor_status"],"no_losses")
        self.assertIsNone(summarize(scenario([0]))["profit_factor"])
        self.assertEqual(D(summarize(scenario([-1]))["profit_factor"]),0)
    def test_completed_only(self):
        with self.assertRaises(ValueError):analytics({"status":"queued","result":None})
    def test_synthetic_replay_rejected(self):
        j={"status":"succeeded","request":{"kind":"reference_fixture"},"result":{"synthetic":True,"result":{"scenarios":[scenario([1])]}}}
        with self.assertRaises(ValueError):trade_replay(j,"O-H-L-C","trade-1",None)
