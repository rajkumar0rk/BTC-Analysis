import unittest, json
import pandas as pd
import research_daily_200_500_points as e

class AuditTest(unittest.TestCase):
    def test_stop_first_and_logging(self):
        ix=pd.date_range("2025-01-02",periods=120,freq="min",tz="UTC")
        d=pd.DataFrame(dict(open=80000.,high=80600.,low=79500.,close=80000.,volume=1.),index=ix)
        ev=pd.DataFrame([dict(entry_utc=ix[0],trigger_utc=str(ix[0]-pd.Timedelta(minutes=1)),date_ny="2025-01-01",side=1,strategy="test",entry_reason="observed",signal_context=json.dumps({"close":80000}),signal_tf=1)])
        tr=e.trade_sim(d,ev)
        self.assertEqual(len(tr),6)
        self.assertTrue((tr.result=="stop").all())
        self.assertTrue(tr.exit_reason.str.contains("stop-first").all())
        self.assertTrue((tr.entry_reason=="observed").all())
        self.assertTrue((tr.exit_utc==str(ix[0])).all())
        self.assertTrue((tr.exit_price==tr.entry_price-tr.stop_points).all())
        self.assertTrue((tr.net_points<tr.gross_points).all())
    def test_target_and_timeout(self):
        ix=pd.date_range("2025-01-02",periods=120,freq="min",tz="UTC")
        d=pd.DataFrame(dict(open=80000.,high=80600.,low=80000.,close=80000.,volume=1.),index=ix)
        ev=pd.DataFrame([dict(entry_utc=ix[0],trigger_utc=str(ix[0]-pd.Timedelta(minutes=1)),date_ny="2025-01-01",side=1,strategy="test",entry_reason="observed",signal_context="{}",signal_tf=1)])
        self.assertTrue((e.trade_sim(d,ev).result=="target").all())
        d["high"]=80001.
        result=e.trade_sim(d,ev)
        self.assertTrue((result.result=="time").all())
        self.assertTrue((result.exit_utc==str(ix[-1])).all())

if __name__=="__main__": unittest.main()
