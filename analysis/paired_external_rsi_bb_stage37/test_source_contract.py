"""Independent, stdlib-only source-semantics preflight. NOT a backtest."""
import unittest

ROI_TIERS = ((0, 0.05), (20, 0.04), (30, 0.03), (60, 0.01))

def roi_threshold(minutes):
    return next(value for age, value in reversed(ROI_TIERS) if minutes >= age)

def entry(rsi, slowk, close, lower_bb, hammer):
    return rsi < 30 and slowk < 20 and close < lower_bb and hammer == 100

def exit_signal(sar, close, fisher, unrealized_profit):
    return sar > close and fisher > 0.3 and unrealized_profit > 0

class SourceContract(unittest.TestCase):
    def test_roi_tiers(self):
        for t, expected in ((0,.05),(19,.05),(20,.04),(29,.04),(30,.03),(59,.03),(60,.01),(100,.01)):
            self.assertEqual(roi_threshold(t), expected)
    def test_strict_entry_boundaries(self):
        self.assertTrue(entry(29,19,99,100,100))
        self.assertFalse(entry(30,19,99,100,100))
        self.assertFalse(entry(29,20,99,100,100))
        self.assertFalse(entry(29,19,100,100,100))
        self.assertFalse(entry(29,19,99,100,0))
    def test_exit_profit_only(self):
        self.assertTrue(exit_signal(101,100,.31,.01))
        self.assertFalse(exit_signal(101,100,.31,-.01))
        self.assertFalse(exit_signal(101,100,.30,.01))
        self.assertFalse(exit_signal(100,100,.31,.01))

if __name__ == "__main__":
    unittest.main()
