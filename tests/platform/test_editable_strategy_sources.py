"""Ordinary Python source fixtures run through the public generic interpreter."""
import unittest
from pathlib import Path
from decimal import Decimal as D
from datetime import timedelta
from btc_analysis.service.python_strategy import prepare_python
from btc_analysis.contracts import Candle,Fill,Timeframe,Side
from test_backtest_engine import T,I

ROOT=Path(__file__).resolve().parents[2]
def source(mode):
    return (ROOT/"strategies"/"cloud"/f"mtf_supertrend_ema20_{mode}_100_200.py").read_text()

class ContextFixture:
    instrument=I
    equity=D(10000)
    position_quantity=D(0)
    now_utc=T
    side=D(1)
    def __init__(self):self.orders=[]
    def submit(self,o):self.orders.append(o)
    def candles(self,tf,n):
        close=D(1001) if self.side>0 else D(999)
        dt=timedelta(seconds=tf.seconds)
        return (Candle(I,tf,self.now_utc-2*dt,self.now_utc-dt,close,close,close,close,D(1)),
                Candle(I,tf,self.now_utc-dt,self.now_utc,close,D(1002),D(998),close,D(1)))
    def indicator(self,name,tf,params):return D(1000) if name=="ema.value" else self.side
    def indicator_history(self,name,tf,params,limit=2):return (D(1000),D(1000))

class EditableSourcesTests(unittest.TestCase):
    def test_sources_not_pinned_or_hardcoded(self):
        for mode in ("touch","reclaim"):
            p,signal,frames=prepare_python(source(mode))
            self.assertEqual(signal,60 if mode=="touch" else 900)
            self.assertEqual(frames,(60,900,3600))
            self.assertEqual(p.make().fixed_point_bracket,(D(100),D(200)))
            changed,_,_=prepare_python(source(mode).replace('D("100"), D("200")','D("75"), D("150")'))
            self.assertEqual(changed.make().fixed_point_bracket,(D(75),D(150)))
            self.assertNotEqual(p.hash,changed.hash)

    def test_entry_weekday_cycle_and_no_overlap(self):
        for mode in ("touch","reclaim"):
            with self.subTest(mode=mode):
                p,_,_=prepare_python(source(mode))
                obj=p.make();ctx=ContextFixture()
                obj.state.update(minutes=5999,aligned=1,ema=D(1000))
                obj.on_execution(ctx)
                self.assertEqual([o.reason for o in ctx.orders],["pullback_long"])
                order=ctx.orders[-1]
                obj.on_fill(ctx,Fill("fill-1",order.intent_id,I,T,Side.BUY,order.quantity,D(1001),D(0),D(0),"USD",order.reason))
                obj.on_execution(ctx)
                self.assertEqual(len(ctx.orders),1)
                # End the aligned cycle, then wait through the weekend.
                ctx.now_utc=T+timedelta(days=3)
                ctx.side=D(0);obj.on_execution(ctx)
                ctx.side=D(-1);obj.on_execution(ctx);obj.on_execution(ctx)
                self.assertEqual(len(ctx.orders),1)
                ctx.now_utc=T+timedelta(days=5)
                ctx.position_quantity=D(1);obj.on_execution(ctx)
                self.assertEqual(len(ctx.orders),1)
                ctx.position_quantity=D(0);obj.on_execution(ctx)
                self.assertEqual([o.reason for o in ctx.orders],["pullback_long","pullback_short"])

if __name__=="__main__":unittest.main()
