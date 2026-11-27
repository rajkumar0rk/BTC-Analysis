import unittest
from btc_analysis.service.strategy_authoring import validate_source,apply_parameters
from btc_analysis.service.browser_replay import replay
from test_browser_replay import SETTINGS,csv_text
from test_python_strategy import SOURCE

PARAM=SOURCE.replace('    exposure = D("0.5")','    exposure = D("0.5")\n    size = parameter(D("0.1"), D("0.01"), D("1"))\n    period = parameter(3, 2, 50)').replace('self.buy(ctx, D("0.1"),','self.buy(ctx, self.size,')

class AuthoringTests(unittest.TestCase):
    def test_validate_edit_and_replay(self):
        r=validate_source(PARAM)
        self.assertTrue(r["valid"],r)
        self.assertEqual([x["name"] for x in r["parameters"]],["size","period"])
        a=apply_parameters(PARAM,{"size":"0.25","period":"5"})
        self.assertTrue(a["validation"]["valid"])
        self.assertIn("size = parameter(D('0.25'),",a["source"])
        self.assertIn("period = parameter(5,",a["source"])
        old=replay(csv_text(),PARAM,"BTCUSD",SETTINGS,True)
        new=replay(csv_text(),a["source"],"BTCUSD",SETTINGS,True)
        self.assertNotEqual(old["graph_sha256"],new["graph_sha256"])
        self.assertNotEqual(old["scenarios"][0]["final_equity"],new["scenarios"][0]["final_equity"])
        for bad in ({"size":"10"},{"period":"2.5"},{"unknown":"3"},{"size":"1+1"}):
            with self.assertRaises(ValueError):apply_parameters(PARAM,bad)

    def test_error_in_unreached_callback_and_syntax(self):
        r=validate_source(SOURCE.replace("self.close_position(ctx, \"custom_exit\")","open('secret')"))
        self.assertFalse(r["valid"])
        self.assertGreater(r["diagnostics"][0]["line"],1)
        self.assertIn("allowlist",r["diagnostics"][0]["message"])
        self.assertFalse(validate_source("def broken(:")["valid"])
        self.assertFalse(validate_source(PARAM.replace("parameter(3, 2, 50)","parameter(100, 2, 50)"))["valid"])

    def test_runtime_error_points_to_source(self):
        broken=SOURCE.replace('self.buy(ctx, D("0.1"), "custom_entry")','self.buy(ctx, D("1") / D("0"), "custom_entry")')
        self.assertTrue(validate_source(broken)["valid"])
        with self.assertRaisesRegex(ValueError,"Python strategy line [0-9]+"):
            replay(csv_text(),broken,"BTCUSD",SETTINGS,True)

    def test_unicode_crlf_edits_and_readonly_parameter(self):
        s=PARAM.replace("    size =", "    # π example\n    size =").replace("\n","\r\n")
        a=apply_parameters(s,{"size":"0.3"})
        self.assertIn("# π example\r\n",a["source"])
        self.assertIn("size = parameter(D('0.3'),",a["source"])
        bad=PARAM.replace("self.entered = False","self.period = 4")
        self.assertFalse(validate_source(bad)["valid"])

if __name__=="__main__":unittest.main()
