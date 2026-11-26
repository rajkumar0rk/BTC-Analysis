import unittest
from btc_analysis.service.validation import ValidationRequest,gate,prefix_matches
from test_visual import graph

def request(**patch):
    return ValidationRequest.model_validate({"optimization_job_id":"a"*32,"optimization_result_sha256":"b"*64,
        "windows":[{"start":3600,"end":7200}],"acknowledge_holdout":True,**patch})

class ValidationTests(unittest.TestCase):
    def test_chronology_and_stress(self):
        for patch in ({"windows":[{"start":3600,"end":7200},{"start":7140,"end":10800}]},
                      {"fee_multiplier":"1"},{"extra_slippage_bps":"0"},{"acknowledge_holdout":False}):
            with self.assertRaises(ValueError):request(**patch)
    def test_conservative_acceptance(self):
        m=[{"account_return_pct":"3","max_event_drawdown_pct":"4","trades":3},
           {"account_return_pct":"-1","max_event_drawdown_pct":"21","trades":0}]
        r=gate(m,request())
        self.assertFalse(r["passed"])
        self.assertEqual(r["failures"],["minimum_return","drawdown","minimum_trades"])
    def test_prefix_detects_changed_fills(self):
        e={"fill_id":"f1","bar_open_utc":"1970-01-01T00:00:00Z"}
        def result(price):
            return {"scenarios":[{"path":"O-H-L-C","fills":[{"fill_id":"f1","price":price}],"execution_evidence":[e]}]}
        self.assertTrue(prefix_matches(result("1"),result("1"),60))
        self.assertFalse(prefix_matches(result("1"),result("2"),60))
