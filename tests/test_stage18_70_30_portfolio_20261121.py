"""Unit-level invariants for Stage18 research-only monthly portfolio."""
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

import research_stage18_70_30_portfolio_20261121 as model


class Stage18PortfolioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg=model.load_config(model.CONFIG_DEFAULT)

    def test_config_research_only_and_fixed_weights(self):
        self.assertEqual(self.cfg["execution_mode"],"BACKTEST_ONLY")
        self.assertAlmostEqual(self.cfg["allocation"]["core"],.70)
        self.assertAlmostEqual(self.cfg["allocation"]["donchian"],.30)
        self.assertEqual(self.cfg["allocation"]["rebalance"],"monthly_end_synthetic")
        self.assertEqual(self.cfg["donchian"]["max_hold_days"],30)
        self.assertEqual(self.cfg["core"]["max_structural_stop_points"],700)

    def test_blend_is_monthly_not_annual_average(self):
        core=np.array([10.,-10.])
        swing=np.array([-5.,20.])
        out=model.blend_monthly(core,swing,.7)
        np.testing.assert_allclose(out,[5.5,-1.0])
        end=np.prod(1+out/100)-1
        self.assertAlmostEqual(model.metrics(out)["total_return_pct"],end*100)

    def test_no_data_mismatch_or_invalid_values(self):
        with self.assertRaises(ValueError):
            model.blend_monthly([1,2],[3],.7)
        with self.assertRaises(ValueError):
            model.blend_monthly([1,float("nan")],[2,3],.7)
        with self.assertRaises(ValueError):
            model.blend_monthly([1],[2],1.2)
        with self.assertRaises(ValueError):
            model.blend_monthly([-100.1],[1],.7)

    def test_profitable_flat_losing_months(self):
        stats=model.metrics([1.0,0.0,-.5])
        self.assertEqual((stats["positive_months"],stats["negative_months"],
                          stats["flat_months"]),(1,1,1))
        self.assertAlmostEqual(stats["total_return_pct"],.495)

    def test_config_rejects_live_order_mode(self):
        bad=dict(self.cfg)
        bad["execution_mode"]="LIVE"
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"bad.json"
            p.write_text(json.dumps(bad))
            with self.assertRaisesRegex(ValueError,"BACKTEST_ONLY"):
                model.load_config(p)

    def test_config_rejects_misrepresented_transaction_costs(self):
        bad=json.loads(json.dumps(self.cfg))
        bad["costs"]["gst_rate"]=0
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"bad.json"
            p.write_text(json.dumps(bad))
            with self.assertRaisesRegex(ValueError,"Fee/GST/slippage"):
                model.load_config(p)

    def test_config_rejects_unbalanced_allocations(self):
        bad=json.loads(json.dumps(self.cfg))
        bad["allocation"]["donchian"]=.31
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"bad.json"
            p.write_text(json.dumps(bad))
            with self.assertRaisesRegex(ValueError,"add to 1"):
                model.load_config(p)

    def test_core_and_donchian_separate_fixed_rules(self):
        c=model.make_core_config(self.cfg)
        d=model.make_donchian_config(self.cfg)
        self.assertEqual(c["maxrisk"],700.)
        self.assertEqual(c["reward"],5.)
        self.assertEqual(c["hold"],240)
        self.assertEqual(d["days"],55)
        self.assertEqual(d["hold_days"],30)
        self.assertEqual(d["initial_atr"],2.)
        self.assertEqual(d["trail_atr"],3.)


if __name__=="__main__":
    unittest.main()
