import unittest
from datetime import timedelta
from dataclasses import replace
from decimal import Decimal as D
from btc_analysis.contracts import Timeframe
from btc_analysis.backtest import BaseStrategy,run_backtest
from btc_analysis.indicators import spec
from btc_analysis.examples.ema_supertrend import EMASupertrendExample
from test_backtest_engine import T,H,MIN,cfg,bars,run,FLAT,submit

class SDKTests(unittest.TestCase):
    def test_multiframe_declaration_and_causality(self):
        class S(BaseStrategy):
            def indicators(self):return (spec("ema",Timeframe(120),period=2),)
            def extra_timeframes(self):return (Timeframe(240),)
            def on_execution(self,c):
                i=int((c.now_utc-T).total_seconds()/60)
                x=c.indicator("ema",Timeframe(120),{"period":2})
                assert (x is None)==(i<4)
                assert len(c.candles(Timeframe(240),10))==(i//4)
                if i==4:assert x==D(100)
        r=run(cfg(),S,FLAT)
        self.assertEqual(len(r.scenarios[0].indicator_specs),1)

    def test_warmup_before_start_and_no_trades(self):
        warm=tuple(replace(c,open_utc=c.open_utc-timedelta(minutes=4),close_utc=c.close_utc-timedelta(minutes=4)) for c in FLAT)
        c=cfg();c=replace(c,datasets=(replace(c.datasets[0],start_utc=T-timedelta(minutes=4)),))
        class S(BaseStrategy):
            def indicators(self):return (spec("ema",MIN,period=3),)
            def on_start(self,ctx):
                assert ctx.indicator("ema",MIN,{"period":3})==D(100)
                assert ctx.candles(MIN,10)[-1].close_utc==T
                submit(ctx,"start")
            def on_signal(self,ctx):
                assert ctx.now_utc>T
        r=run_backtest(c,S,lambda:FLAT,linear_contract=True,dataset_manifest_sha256=H,
                       warmup_start_utc=T-timedelta(minutes=4),warmup_factory=lambda:warm)
        for s in r.scenarios:
            self.assertEqual(s.warmup_bars,4)
            self.assertEqual(s.bars,4)
            self.assertEqual(len(s.warmup_candle_sha256),64)
            self.assertEqual(s.fills[0].event_utc,T)
            self.assertEqual(s.initial_equity,D(1000))
        with self.assertRaises(ValueError):
            run_backtest(c,S,lambda:FLAT,linear_contract=True,dataset_manifest_sha256=H,
                         warmup_start_utc=T-timedelta(minutes=4),warmup_factory=lambda:warm[:-1])

    def test_undeclared_and_incompatible_frames(self):
        class S(BaseStrategy):
            def on_start(self,c):c.indicator("ema",MIN)
        with self.assertRaisesRegex(ValueError,"declared"):run(cfg(),S,FLAT)
        class Bad(BaseStrategy):
            def extra_timeframes(self):return (Timeframe(180),)
        with self.assertRaises(ValueError):run(cfg(),Bad,FLAT)

    def test_example_replay(self):
        d=bars([(100,102,99,101),(101,105,100,104),(104,115,103,112),(112,114,110,113),
                (113,114,90,91),(91,92,85,87),(87,88,83,84),(84,86,83,85)])
        f=lambda:EMASupertrendExample(MIN,ema_period=2,atr_period=1,multiplier=D(1),exposure=D(".2"))
        r=run(cfg(n=8),f,d)
        self.assertEqual(r.result_sha256,run(cfg(n=8),f,d).result_sha256)
        for s in r.scenarios:
            self.assertTrue(s.fills)
            self.assertTrue(all(f.reason.startswith(("ema_supertrend_","long_trend_","short_trend_")) for f in s.fills))

if __name__=="__main__":unittest.main()
