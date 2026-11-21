"""Stage37 deterministic futures fee/GST and equity accounting primitives.

Not a strategy replay, not historical fills, and not a funding model.
Keep gross, commission, GST and adverse slippage separately auditable.
"""
from dataclasses import dataclass
from math import isfinite
import unittest

TAKER_FEE = 0.0005
GST_RATE = 0.18

@dataclass(frozen=True)
class RoundTrip:
    side: int
    quantity: float
    entry_reference: float
    exit_reference: float
    slippage_points_per_side: float = 0.0

    def calculate(self):
        if self.side not in (-1, 1):
            raise ValueError("side must be +1 long or -1 short")
        vals = (self.quantity, self.entry_reference, self.exit_reference,
                self.slippage_points_per_side)
        if not all(isfinite(v) for v in vals) or min(vals[:3]) <= 0 or vals[3] < 0:
            raise ValueError("invalid quantity, price or slippage")
        entry = self.entry_reference + self.side * self.slippage_points_per_side
        exit_ = self.exit_reference - self.side * self.slippage_points_per_side
        if entry <= 0 or exit_ <= 0:
            raise ValueError("nonpositive executable price")
        gross_reference = self.side * (self.exit_reference - self.entry_reference) * self.quantity
        slip_cost = 2 * self.slippage_points_per_side * self.quantity
        commission = (entry + exit_) * self.quantity * TAKER_FEE
        gst = commission * GST_RATE
        net = gross_reference - slip_cost - commission - gst
        assert abs(net - (self.side * (exit_ - entry) * self.quantity - commission - gst)) < 1e-7
        return dict(gross=gross_reference, commission=commission, gst=gst,
                    assumed_slippage=slip_cost, net=net,
                    funding="UNMODELED", entry_fill=entry, exit_fill=exit_)

class CostAccountingContract(unittest.TestCase):
    def test_zero_slip_both_sides_fee_and_gst(self):
        a = RoundTrip(1, 1, 100000, 101000).calculate()
        self.assertAlmostEqual(a["gross"], 1000)
        self.assertAlmostEqual(a["commission"], 100.5)
        self.assertAlmostEqual(a["gst"], 18.09)
        self.assertAlmostEqual(a["net"], 881.41)
        self.assertEqual(a["assumed_slippage"], 0)
    def test_adverse_slip_long_and_short(self):
        for side, entry, exit_ in [(1, 100000, 101000),(-1, 101000,100000)]:
            base = RoundTrip(side, 2, entry, exit_).calculate()
            for points in (0.5, 5):
                stress = RoundTrip(side, 2, entry, exit_, points).calculate()
                self.assertAlmostEqual(stress["assumed_slippage"], 4 * points)
                self.assertAlmostEqual(base["net"] - stress["net"], 4 * points)
    def test_invalid_inputs(self):
        for item in [RoundTrip(0,1,100,101),RoundTrip(1,0,100,101),
                     RoundTrip(1,1,100,101,-1),RoundTrip(1,1,float("nan"),101)]:
            with self.assertRaises(ValueError): item.calculate()

if __name__ == "__main__":
    unittest.main()
