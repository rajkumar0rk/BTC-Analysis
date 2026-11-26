import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
from btc_analysis.contracts import *
from btc_analysis.backtest import BaseStrategy, run_backtest

T=datetime(2025,1,1,tzinfo=timezone.utc)
I=Instrument("fixture","BTCUSD",AssetClass.CRYPTO_PERPETUAL,"USD","USD",D("1"),D("1"),D("1"))
H="a"*64
MIN=Timeframe(60)
def cfg(n=4,signal=60,policy=IntrabarPolicy.BOTH_PATHS,**changes):
    end=T+timedelta(minutes=n)
    ds=DatasetRef("fixture",I,DataKind.OHLCV,MIN,T,end,H,"synthetic",0,True)
    cost=CostModel(D(0),D(0),D(0),D(0),False,False,False,"fixture")
    c=BacktestConfig(StrategyRef("test","1",H,H),I,(ds,),T,end,Timeframe(signal),MIN,D(1000),"USD",
        D(1),MarginMode.ISOLATED,cost,policy,"Asia/Kolkata","crypto-24x7")
    return replace(c,**changes)
def bars(values):
    return tuple(Candle(I,MIN,T+timedelta(minutes=i),T+timedelta(minutes=i+1),
            *(D(str(x)) for x in row),D(1)) for i,row in enumerate(values))
def submit(ctx,id,side=Side.BUY,qty=1,kind=OrderType.MARKET,limit=None,stop=None,reduce=False):
    ctx.submit(OrderIntent(id,I,ctx.now_utc,side,kind,D(qty),id,
        None if limit is None else D(limit),None if stop is None else D(stop),reduce))
def run(c,f,data):
    return run_backtest(c,f,lambda:iter(data),linear_contract=True,dataset_manifest_sha256=H)
FLAT=bars([(100,100,100,100)]*4)

class RoundTrip(BaseStrategy):
    def on_signal(self,ctx):
        if ctx.now_utc==T+timedelta(minutes=1):submit(ctx,"entry")
        if ctx.now_utc==T+timedelta(minutes=2):submit(ctx,"exit",Side.SELL,reduce=True)

class EngineTests(unittest.TestCase):
    def test_next_open_and_actual_reasons(self):
        data=bars([(100,120,90,110),(105,115,100,112),(120,130,119,125),(130,130,130,130)])
        r=run(cfg(),RoundTrip,data).scenarios[0]
        self.assertEqual([f.price for f in r.fills],[D(105),D(120)])
        self.assertEqual([f.event_utc for f in r.fills],[T+timedelta(minutes=1),T+timedelta(minutes=2)])
        self.assertEqual(r.net_pnl,D(15))
        self.assertEqual((r.closed_trades[0].entry_reason,r.closed_trades[0].exit_reason),("entry","exit"))
        self.assertEqual(r.open_quantity,0)

    def test_no_future_2m_signal(self):
        class S(BaseStrategy):
            def on_start(self,c):assert c.candles(MIN,10)==()
            def on_signal(self,c):
                x=c.candles(Timeframe(120),10)
                assert all(b.close_utc<=c.now_utc for b in x)
                assert x[-1].close_utc==c.now_utc
                if len(x)==1:submit(c,"entry")
        r=run(cfg(signal=120),S,FLAT).scenarios[0]
        self.assertEqual(r.fills[0].event_utc,T+timedelta(minutes=2))

    def test_bracket_paths_and_stale_cancel(self):
        class S(BaseStrategy):
            def on_start(self,c):submit(c,"entry")
            def on_fill(self,c,f):
                if f.reason=="entry":
                    submit(c,"stop",Side.SELL,kind=OrderType.STOP_MARKET,stop=90,reduce=True)
                    submit(c,"target",Side.SELL,kind=OrderType.LIMIT,limit=110,reduce=True)
        d=bars([(100,100,100,100),(100,115,85,100),(100,100,100,100),(100,100,100,100)])
        r=run(cfg(),S,d)
        self.assertEqual([x.net_pnl for x in r.scenarios],[D(10),D(-10)])
        self.assertEqual(r.worst_path,"O-L-H-C")
        self.assertTrue(all(x.open_quantity==0 and len(x.fills)==2 for x in r.scenarios))
        self.assertTrue(any(x.status=="cancelled" and x.intent_id=="target" for x in r.scenarios[1].orders))
        a=run(cfg(policy=IntrabarPolicy.STOP_FIRST),S,d)
        self.assertEqual(a.scenarios[0].net_pnl,D(-10))

    def test_gap_stop_and_slippage(self):
        class S(BaseStrategy):
            def on_start(self,c):submit(c,"entry")
            def on_fill(self,c,f):
                if f.reason=="entry":submit(c,"stop",Side.SELL,kind=OrderType.STOP_MARKET,stop=90,reduce=True)
        d=bars([(100,100,100,100),(80,82,79,81),(80,80,80,80),(80,80,80,80)])
        c=cfg();c=replace(c,costs=replace(c.costs,slippage_bps=D(100)))
        r=run(c,S,d).scenarios[0]
        self.assertEqual([x.price for x in r.fills],[D(101),D(79)])
        self.assertEqual(r.net_pnl,D(-22))

    def test_stop_limit_trigger_then_retrace(self):
        class S(BaseStrategy):
            def on_start(self,c):
                submit(c,"breakout",kind=OrderType.STOP_LIMIT,stop=110,limit=105)
        d=bars([(100,115,100,104),(104,104,104,104),(104,104,104,104),(104,104,104,104)])
        r=run(cfg(),S,d).scenarios[0]
        self.assertEqual(r.fills[0].price,D(105))
        self.assertTrue(any(x.status=="triggered" for x in r.orders))

    def test_stop_limit_not_filled_if_no_retrace(self):
        class S(BaseStrategy):
            def on_start(self,c):submit(c,"breakout",kind=OrderType.STOP_LIMIT,stop=110,limit=105)
        d=bars([(100,115,100,112),(112,112,112,112),(112,112,112,112),(112,112,112,112)])
        r=run(cfg(),S,d).scenarios[1]
        self.assertFalse(r.fills)
        self.assertTrue(any(x.status=="expired" for x in r.orders))

    def test_limit_gap_improvement(self):
        class S(BaseStrategy):
            def on_start(self,c):submit(c,"limit",kind=OrderType.LIMIT,limit=110)
        r=run(cfg(),S,FLAT).scenarios[0]
        self.assertEqual(r.fills[0].price,D(100))

    def test_fees_tax_and_short(self):
        class S(BaseStrategy):
            def on_start(self,c):submit(c,"short",Side.SELL)
            def on_signal(self,c):
                if c.now_utc==T+timedelta(minutes=1):submit(c,"cover",reduce=True)
        d=bars([(100,100,100,100),(80,80,80,80),(80,80,80,80),(80,80,80,80)])
        c=cfg();c=replace(c,costs=replace(c.costs,taker_bps=D(5),tax_rate=D(".18")))
        r=run(c,S,d).scenarios[0]
        self.assertEqual(r.gross_realized_pnl,D(20))
        self.assertEqual(r.fees,D(".09"))
        self.assertEqual(r.taxes,D(".0162"))
        self.assertEqual(r.net_pnl,D("19.8938"))

    def test_partial_exit_and_scale_in_fifo(self):
        class S(BaseStrategy):
            def on_start(self,c):submit(c,"entry",qty=2)
            def on_signal(self,c):
                i=int((c.now_utc-T).total_seconds()/60)
                if i==1:submit(c,"partial",Side.SELL,reduce=True)
                if i==2:submit(c,"scale")
                if i==3:submit(c,"close",Side.SELL,qty=2,reduce=True)
        d=bars([(100,100,100,100),(110,110,110,110),(120,120,120,120),(130,130,130,130)])
        r=run(cfg(),S,d).scenarios[0]
        self.assertEqual(r.net_pnl,D(50))
        self.assertEqual(len(r.closed_trades[0].entry_fills),2)
        self.assertEqual(len(r.closed_trades[0].exit_fills),2)

    def test_reduce_only_and_no_reversal(self):
        class S(BaseStrategy):
            def on_start(self,c):submit(c,"bad",Side.SELL,reduce=True);submit(c,"entry")
            def on_signal(self,c):
                i=int((c.now_utc-T).total_seconds()/60)
                if i==1:submit(c,"reverse",Side.SELL,qty=2)
                if i==2:submit(c,"clip",Side.SELL,qty=2,reduce=True)
        r=run(cfg(),S,FLAT).scenarios[0]
        self.assertEqual(len(r.fills),2)
        self.assertTrue(any(o.detail=="reversal_not_supported" for o in r.orders))
        self.assertEqual(r.open_quantity,0)

    def test_collateral_reject(self):
        class S(BaseStrategy):
            def on_start(self,c):submit(c,"huge",qty=11)
        r=run(cfg(),S,FLAT).scenarios[0]
        self.assertFalse(r.fills)
        self.assertTrue(any(o.detail=="baseline_collateral_cap" for o in r.orders))

    def test_open_mark_and_drawdown(self):
        class S(BaseStrategy):
            def on_start(self,c):submit(c,"entry")
        d=bars([(100,120,80,110),(110,110,110,110),(110,110,110,110),(110,110,110,110)])
        r=run(cfg(),S,d).scenarios[0]
        self.assertEqual(r.final_equity,D(1010));self.assertEqual(r.balance,D(1000))
        self.assertEqual(r.open_unrealized_pnl,D(10));self.assertEqual(r.open_quantity,D(1))
        self.assertGreater(r.max_event_drawdown_pct,D(3))
        self.assertFalse(r.closed_trades)
        self.assertEqual(sum(m.pnl for m in r.monthly),r.net_pnl)

    def test_cancel_and_end_expiry(self):
        class S(BaseStrategy):
            def on_start(self,c):
                submit(c,"cancel",kind=OrderType.LIMIT,limit=90);c.cancel("cancel")
                submit(c,"rest",kind=OrderType.LIMIT,limit=90)
            def on_finish(self,c):submit(c,"late")
        r=run(cfg(),S,FLAT).scenarios[0]
        self.assertFalse(r.fills)
        self.assertTrue(any(o.status=="expired" for o in r.orders))
        self.assertTrue(any(o.detail=="run_finished" for o in r.orders))

    def test_data_identity_and_gaps(self):
        for d in (FLAT[:-1],(FLAT[0],FLAT[2],FLAT[3]),(FLAT[0],)*4):
            with self.assertRaises(ValueError):run(cfg(),BaseStrategy,d)
        with self.assertRaises(ValueError):
            run_backtest(cfg(),BaseStrategy,lambda:FLAT,linear_contract=True,dataset_manifest_sha256="b"*64)

    def test_unsupported_and_linear_attestation(self):
        for c in (replace(cfg(),leverage=D(2)),replace(cfg(),allow_data_gaps=True)):
            with self.assertRaises(ValueError):run(c,BaseStrategy,FLAT)
        with self.assertRaises(ValueError):
            run_backtest(cfg(),BaseStrategy,lambda:FLAT,dataset_manifest_sha256=H)

    def test_reproducible_fresh_factory(self):
        r=run(cfg(),RoundTrip,FLAT)
        self.assertEqual(r.result_sha256,run(cfg(),RoundTrip,FLAT).result_sha256)
        s=RoundTrip()
        with self.assertRaises(ValueError):run(cfg(),lambda:s,FLAT)

    def test_different_scenario_streams_rejected(self):
        d=iter((FLAT,bars([(101,101,101,101)]*4)))
        with self.assertRaisesRegex(ValueError,"streams differ"):
            run_backtest(cfg(),BaseStrategy,lambda:next(d),linear_contract=True,dataset_manifest_sha256=H)

if __name__=="__main__":unittest.main()
