import unittest,json
from datetime import timedelta
from decimal import Decimal as D
from pathlib import Path
from types import SimpleNamespace as NS
from btc_analysis.examples.mtf_pullback import MTFPullbackStrategy,SOURCES,recover_pullback,touch,reclaim,MIN,M15,H1
from btc_analysis.backtest import BaseStrategy,run_backtest
from btc_analysis.contracts import Side
from test_backtest_engine import T,I,H,cfg,bars,submit

class ImmediateBracket(BaseStrategy):
    fixed_point_bracket=(D(100),D(200))
    def on_start(self,c):submit(c,"entry")

class PullbackTests(unittest.TestCase):
    def test_wrappers_exact_and_reject_edits(self):
        root=Path(__file__).resolve().parents[2]
        for mode,source in SOURCES.items():
            self.assertEqual(recover_pullback(source)["mode"],mode)
            self.assertEqual((root/"strategies"/"cloud"/f"mtf_supertrend_ema20_{mode}_100_200.py").read_text(),source)
            with self.assertRaises(ValueError):recover_pullback(source+"\n# edit")
        ts=(root/"apps/web/src/cloudStrategyTemplates.ts").read_text()
        templates=json.loads(ts.split("export const mtfPullbackTemplates=",1)[1].rsplit(" as const;",1)[0])
        self.assertEqual({x["mode"]:x["source"] for x in templates},SOURCES)

    def test_touch_and_reclaim_sides(self):
        above=NS(close=D(101));below=NS(close=D(99))
        long=NS(open=D(101),low=D(98),high=D(103),close=D(102))
        short=NS(open=D(99),low=D(97),high=D(102),close=D(98))
        self.assertTrue(touch(1,above,long,D(100)))
        self.assertTrue(touch(-1,below,short,D(100)))
        self.assertFalse(touch(1,below,long,D(100)))
        self.assertTrue(reclaim(1,above,long,D(100)))
        self.assertTrue(reclaim(-1,below,short,D(100)))
        self.assertFalse(reclaim(1,above,short,D(100)))

    def test_same_entry_minute_both_paths(self):
        # Exact 100/200 point brackets from 1000 entry.
        data=bars([(1000,1250,850,1000)]+[(1000,1000,1000,1000)]*3)
        result=run_backtest(cfg(),ImmediateBracket,lambda:data,linear_contract=True,dataset_manifest_sha256=H)
        for s in result.scenarios:
            self.assertEqual(s.open_quantity,0)
            self.assertEqual(s.fills[-1].event_utc,T+timedelta(minutes=1))
            self.assertEqual(s.fills[-1].price,D(1200 if s.path=="O-H-L-C" else 900))
            self.assertEqual(s.fills[-1].reason,"mtf_fixed_target" if s.path=="O-H-L-C" else "mtf_fixed_stop")
            self.assertEqual(len(s.closed_trades),1)

    def test_weekday_cycle_and_no_overlap(self):
        class C:
            instrument=I
            equity=D(10000)
            position_quantity=D(0)
            now_utc=T
            side=D(1)
            def candles(self,tf,n):
                return [NS(close=D(1001)),NS(open=D(1001),low=D(999),high=D(1002),close=D(1001))]
            def indicator(self,name,tf,params):return D(1000) if name=="ema.value" else self.side
        ctx=C()
        obj=MTFPullbackStrategy("touch")
        calls=[]
        obj.buy=lambda c,q,r:calls.append(r)
        obj.sell=lambda c,q,r:calls.append(r)
        obj.minutes=5999;obj.aligned=1;obj.ema=D(1000)
        obj.on_execution(ctx);self.assertEqual(calls,["mtf_pullback_long"])
        obj.on_fill(ctx,NS(reason="mtf_pullback_long"))
        obj.on_execution(ctx);self.assertEqual(len(calls),1)
        ctx.side=D(-1);obj.on_execution(ctx)
        ctx.side=D(1);obj.on_execution(ctx)
        ctx.now_utc=T+timedelta(days=3)  # Saturday IST
        obj.on_execution(ctx);self.assertEqual(len(calls),1)
        ctx.now_utc=T+timedelta(days=5)  # Monday IST
        ctx.position_quantity=D(1);obj.on_execution(ctx);self.assertEqual(len(calls),1)
        ctx.position_quantity=D(0);obj.on_execution(ctx);self.assertEqual(len(calls),2)

if __name__=="__main__":unittest.main()
