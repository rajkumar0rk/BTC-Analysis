"""Conservative OHLCV limit-order approximation; NOT observed order-book fills.

A buy limit submitted after bar close may fill only on a later bar that trades
strictly THROUGH its limit. Touch-only and gap-through-without-trade are not
assumed to fill. Never use the signal bar's low. Unfilled orders expire.
This intentionally undercounts uncertain fills; it does not establish parity
with Freqtrade's live exchange order matching.
"""
from dataclasses import dataclass
import unittest

@dataclass(frozen=True)
class Bar:
    open: float
    high: float
    low: float
    close: float

    def valid(self):
        return (self.low > 0 and self.low <= min(self.open, self.close)
                and self.high >= max(self.open, self.close)
                and self.high >= self.low)

def buy_limit_fill(limit, subsequent_bars, max_wait_bars=1):
    """Return (index, price) or None. Index zero is FIRST POST-SIGNAL bar."""
    if limit <= 0 or max_wait_bars < 1:
        raise ValueError("invalid limit or timeout")
    for index, bar in enumerate(subsequent_bars):
        if index >= max_wait_bars:
            break
        if not bar.valid():
            raise ValueError("invalid OHLC")
        # Strict trade-through, not touch. Gap below is ambiguous: exclude.
        if bar.low < limit and bar.open >= limit:
            return index, limit
    return None

def sell_limit_fill(limit, subsequent_bars, max_wait_bars=1):
    if limit <= 0 or max_wait_bars < 1:
        raise ValueError("invalid limit or timeout")
    for index, bar in enumerate(subsequent_bars):
        if index >= max_wait_bars:
            break
        if not bar.valid():
            raise ValueError("invalid OHLC")
        if bar.high > limit and bar.open <= limit:
            return index, limit
    return None

class ConservativeFillContract(unittest.TestCase):
    def test_next_bar_only(self):
        self.assertEqual(buy_limit_fill(100, [Bar(101,102,99,100)]), (0,100))
        self.assertIsNone(buy_limit_fill(100, [Bar(101,102,100,101)]))
    def test_no_optimistic_gap_fill(self):
        self.assertIsNone(buy_limit_fill(100, [Bar(98,99,97,98)]))
        self.assertIsNone(sell_limit_fill(100, [Bar(102,103,101,102)]))
    def test_sell_strict(self):
        self.assertEqual(sell_limit_fill(100,[Bar(99,101,98,100)]),(0,100))
        self.assertIsNone(sell_limit_fill(100,[Bar(99,100,98,99)]))
    def test_timeout_and_invalid(self):
        self.assertIsNone(buy_limit_fill(100,[Bar(101,102,100,101),Bar(101,102,99,100)],1))
        self.assertEqual(buy_limit_fill(100,[Bar(101,102,100,101),Bar(101,102,99,100)],2),(1,100))
        with self.assertRaises(ValueError):
            buy_limit_fill(100,[Bar(100,99,101,100)])

if __name__ == "__main__":
    unittest.main()
