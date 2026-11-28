"""Regression checks for elapsed-time warmup on nonuniform five-second samples."""
import collections, unittest
from research_order_flow_v4 import NS, signals, trim_signal_history
class WarmupTest(unittest.TestCase):
    def history(self, count):
        rows=collections.deque();t=0
        for i in range(count):
            t=int(i*5.1*NS)
            # Positive microprice, rising mid; zero aggressive volume isolates microprice.
            rows.append((t,100000+i*4,.5,100,100,0,0,0,0,0,0,10,10))
            trim_signal_history(rows,t)
        return rows,t
    def test_irregular_sampling_ready(self):
        rows,t=self.history(150);stats=collections.Counter()
        self.assertLess(len(rows),120)
        self.assertGreaterEqual(t-rows[0][0],600*NS)
        self.assertEqual(signals(rows,collections.deque(),t,stats)['MICROPRICE_MOMENTUM'],1)
        self.assertEqual(stats['signal_evaluations_ready'],1)
    def test_short_history_not_ready(self):
        rows,t=self.history(90);stats=collections.Counter()
        self.assertFalse(any(signals(rows,collections.deque(),t,stats).values()))
        self.assertEqual(stats['warmup_elapsed_block'],1)
    def test_stale_anchor_not_ready(self):
        rows,t=self.history(150);stats=collections.Counter()
        first=rows.popleft();rows.appendleft((first[0]-20*NS,*first[1:]))
        self.assertFalse(any(signals(rows,collections.deque(),t,stats).values()))
        self.assertEqual(stats['warmup_anchor_stale'],1)
if __name__=='__main__':unittest.main()
