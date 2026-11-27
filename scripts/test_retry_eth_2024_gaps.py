import unittest
from retry_eth_2024_gaps import retry_rows
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

if __name__ == "__main__":
    unittest.main()
