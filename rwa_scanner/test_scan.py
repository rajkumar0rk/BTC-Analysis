import unittest
from scan import breakout, numeric

class ScannerTests(unittest.TestCase):
    def test_numeric(self):
        self.assertIsNone(numeric("bad"))
        self.assertEqual(numeric("1.25"), 1.25)

    def test_no_data(self):
        self.assertFalse(breakout([], 1000)["signal"])

    def test_confirmed_pullback(self):
        now = 1000000
        candles = []
        for i in range(30):
            o = 100.0
            c = 100.5
            h = 100.6
            l = 99.9
            if i in (26,27,28):
                o,c,h,l = 100+(i-26),101+(i-26),101.2+(i-26),99.8+(i-26)
            if i == 29:
                o,c,h,l = 103,102.5,103.1,102.4
            candles.append({"time": now-30*60+i*60,"open":o,"close":c,"high":h,"low":l,"volume":100})
        self.assertFalse(breakout(candles, now)["signal"])

if __name__ == "__main__":
    unittest.main()
