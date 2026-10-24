import datetime as dt
import unittest
from zoneinfo import ZoneInfo

from quality import classify_headline, stock_session, liquidity

class RWAQualityTests(unittest.TestCase):
    def test_weekend_closed(self):
        instant = dt.datetime(2026, 10, 24, 14, tzinfo=dt.timezone.utc)
        s = stock_session(int(instant.timestamp()))
        self.assertFalse(s["active"])

    def test_regular_session(self):
        instant = dt.datetime(2026, 10, 26, 14, tzinfo=dt.timezone.utc)
        s = stock_session(int(instant.timestamp()))
        self.assertTrue(s["active"])

    def test_nyse_holiday(self):
        instant = dt.datetime(2026, 12, 25, 15, tzinfo=dt.timezone.utc)
        self.assertFalse(stock_session(int(instant.timestamp()))["active"])

    def test_positive_headline(self):
        self.assertEqual(classify_headline("Nvidia shares jump after revenue beats estimates",
                                           "NVIDIA", "NVDA"), "positive_candidate")

    def test_negative_overrides_positive(self):
        self.assertEqual(classify_headline("Nvidia shares slump despite strong sales",
                                           "NVIDIA", "NVDA"), "negative_or_mixed")

    def test_unrelated_positive_headline(self):
        self.assertEqual(classify_headline("Tesla shares jump after revenue beats estimates",
                                           "NVIDIA", "NVDA"), "unrelated")

    def test_liquidity_missing_book(self):
        result = liquidity("NVDAXUSD", 999999,
                           lambda path, params: {"buy": [], "sell": []})
        self.assertFalse(result["pass"])
        self.assertTrue(result["reasons"])

    def test_liquidity_spread(self):
        result = liquidity("NVDAXUSD", 999999, lambda path, params:
            {"buy": [{"price": "100", "size": "5"}],
             "sell": [{"price": "102", "size": "5"}]})
        self.assertFalse(result["pass"])
        self.assertTrue(any("spread" in x for x in result["reasons"]))

if __name__ == "__main__":
    unittest.main()
