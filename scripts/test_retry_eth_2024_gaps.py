import unittest
import tempfile
from pathlib import Path
from retry_eth_2024_gaps import retry_rows, retry_until_complete
from recover_delta_2024 import validate
from stage_repository_history import month_bounds


class RetryTest(unittest.TestCase):
    def test_resume_without_mutation_or_fabrication(self):
        a, b = month_bounds("2024-02")
        step = 3600
        def bar(t, price=1):
            return dict(time=t, open=price, high=price, low=price, close=price)
        seed = {t: validate(bar(t), "funding_1h", step)
                for t in range(a,b,step) if t not in (a+step,a+2*step)}
        def api(symbol, resolution, lo, hi):
            self.assertEqual(symbol, "FUNDING:ETHUSD")
            return [bar(a,2), bar(a+step)]
        rows, stats = retry_rows("ETHUSD","2024-02","funding_1h",seed,0,
                                 request=api,pause=lambda _:None)
        self.assertEqual(len(rows),len(seed)+1)
        self.assertNotIn(a+2*step,rows)
        self.assertEqual(rows[a],seed[a])
        self.assertGreater(stats["overlap_conflicts"],0)
        rows2, stats2 = retry_rows("ETHUSD","2024-02","funding_1h",rows,1,
                                   request=lambda *args:[bar(a+2*step)],pause=lambda _:None)
        self.assertEqual(len(rows2),(b-a)//step)
        self.assertTrue(all(rows2[t]==row for t,row in rows.items()))
        _, done = retry_rows("ETHUSD","2024-02","funding_1h",rows2,2,
                              request=lambda *args: self.fail("complete series requested"))
        self.assertEqual(done["requests"],0)

    def test_keeps_retrying_even_without_progress(self):
        outcomes = iter([
            {"complete":False,"new_rows":0,"missing":{"trade_1m":2}},
            {"complete":False,"new_rows":1,"missing":{"trade_1m":1}},
            {"complete":True,"new_rows":1,"missing":{"trade_1m":0}},
        ])
        rounds = []
        checkpoints = []
        def fake_pass(root, round_id, budget):
            rounds.append(round_id)
            return next(outcomes)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = retry_until_complete(root, 3, 90, root/"result.json",
                     checkpoint=checkpoints.append, run_pass=fake_pass,
                     pause=lambda _:None)
            self.assertTrue(result["complete"])
            self.assertEqual(result["passes"],3)
            self.assertEqual(result["total_new_rows"],2)
            self.assertEqual(rounds,[3000,3001,3002])
            self.assertEqual(checkpoints,[root,root])

    def test_incomplete_runtime_exit_is_explicit(self):
        ticks = iter([0, 10, 10])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = retry_until_complete(root,0,90,root/"result.json",max_runtime=1,
                      run_pass=lambda *args:{"complete":False,"new_rows":0,"missing":{"trade_1m":1}},
                      clock=lambda:next(ticks))
            self.assertFalse(result["complete"])
            self.assertEqual(result["exit_reason"],"runtime_limit_resume_required")

if __name__ == "__main__":
    unittest.main()
