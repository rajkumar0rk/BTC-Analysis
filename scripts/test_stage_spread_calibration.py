import unittest
from pathlib import Path
from stage_spread_calibration import collect,quote
class Tests(unittest.TestCase):
    def test_actual(self):
        r=collect(Path("analysis/forward_microstructure/snapshots"))
        self.assertEqual(r["symbol"],"BTCUSD")
        self.assertGreaterEqual(len(r["samples"]),10)
        self.assertEqual(len({x["received_utc"] for x in r["samples"]}),len(r["samples"]))
        self.assertTrue(all(x["sha256"] for x in r["files"]))
    def test_wrong_source(self):
        with self.assertRaises(ValueError):quote({"schema_version":2},"2026-11-17")
if __name__=="__main__":unittest.main()
