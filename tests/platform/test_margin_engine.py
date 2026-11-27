import unittest
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal as D
from btc_analysis.contracts import *
from btc_analysis.margin import MarginProfile,MarginTier,TieredMarginProfile,RiskBar,FundingSettlement,funding_payment
from btc_analysis.backtest import BaseStrategy,run_backtest
from test_backtest_engine import T,I,H,MIN,cfg,bars,FLAT,submit

M="b"*64
F="c"*64
def setup(mode=MarginMode.ISOLATED,funding=False):
    c=cfg()
    mark=replace(c.datasets[0],dataset_id="mark",kind=DataKind.MARK,manifest_sha256=M)
    ds=(c.datasets[0],mark)
    if funding:ds+=(replace(mark,dataset_id="funding",kind=DataKind.FUNDING,manifest_sha256=F,timeframe=None),)
    c=replace(c,datasets=ds,leverage=D(10),margin_mode=mode,
              costs=replace(c.costs,include_liquidation=True,include_funding=funding))
    p=MarginProfile("synthetic-fixed-tier",I,T,c.end_utc,"synthetic fixture",D(".1"),D(".05"),
                    D(100000),D(25),60 if funding else 0)
    return c,p

def execute(c,p,strategy,marks=FLAT,trades=FLAT,funding=False):
    risk=tuple(RiskBar(m,FundingSettlement(m.open_utc,D(".01"),m.open,"fixture") if funding else None) for m in marks)
    return run_backtest(c,strategy,lambda:trades,linear_contract=True,dataset_manifest_sha256=H,
                       margin_profile=p,risk_factory=lambda:risk,risk_manifest_sha256s=tuple(d.manifest_sha256 for d in c.datasets[1:]))

class Long(BaseStrategy):
    def on_start(self,c):submit(c,"long",qty=20)

class MarginTests(unittest.TestCase):
    def test_leverage_and_mark_equity(self):
        c,p=setup()
        d=bars([(100,100,100,100),(105,105,105,105),(105,105,105,105),(105,105,105,105)])
        r=execute(c,p,Long,marks=d).scenarios[0]
        self.assertEqual(r.open_quantity,D(20))
        self.assertEqual(r.final_equity,D(1100))
        self.assertEqual(r.open_unrealized_pnl,D(100))
        self.assertFalse(r.liquidations)

    def test_isolated_vs_cross(self):
        d=bars([(100,100,100,100),(95,95,90,95),(95,95,95,95),(95,95,95,95)])
        c,p=setup()
        a=execute(c,p,Long,marks=d).scenarios[0]
        self.assertEqual(len(a.liquidations),1)
        self.assertEqual(a.open_quantity,0)
        self.assertEqual(a.fills[-1].reason,"modeled_liquidation")
        self.assertEqual(a.fills[-1].price,D(90))
        self.assertEqual(a.fees,D("4.5"))
        self.assertEqual(a.net_pnl,D("-204.5"))
        self.assertEqual(a.closed_trades[0].net_pnl,a.net_pnl)
        c,p=setup(MarginMode.CROSS)
        b=execute(c,p,Long,marks=d).scenarios[0]
        self.assertFalse(b.liquidations)
        self.assertEqual(b.open_quantity,D(20))
        self.assertEqual(b.final_equity,D(900))

    def test_short_mark_liquidation_and_halt(self):
        class S(BaseStrategy):
            def on_start(self,c):submit(c,"short",Side.SELL,qty=20)
            def on_signal(self,c):
                if c.position_quantity==0:submit(c,"retry-"+str(c.now_utc.timestamp()))
        c,p=setup()
        d=bars([(100,100,100,100),(100,110,100,105),(105,105,105,105),(105,105,105,105)])
        a=execute(c,p,S,marks=d).scenarios[0]
        self.assertEqual(a.open_quantity,0)
        self.assertEqual(a.fills[-1].price,D(110))
        self.assertTrue(any(o.detail=="liquidation_halt" for o in a.orders))

    def test_initial_margin_and_max_leverage(self):
        class S(BaseStrategy):
            def on_start(self,c):submit(c,"oversize",qty=101)
        c,p=setup()
        r=execute(c,p,S).scenarios[0]
        self.assertFalse(r.fills)
        self.assertTrue(any(o.detail=="initial_margin_or_notional_cap" for o in r.orders))
        with self.assertRaises(ValueError):execute(replace(c,leverage=D(11)),p,Long)

    def test_funding_reconciliation(self):
        class S(BaseStrategy):
            def on_start(self,c):submit(c,"entry",qty=2)
            def on_signal(self,c):
                if c.now_utc==T+timedelta(minutes=2):submit(c,"exit",Side.SELL,qty=2,reduce=True)
        c,p=setup(funding=True)
        r=execute(c,p,S,funding=True).scenarios[0]
        # At t0 flat; t1 and t2 pay before exit at t2 open; t3 flat.
        self.assertEqual([x.paid for x in r.funding_records],[D(0),D(2),D(2),D(0)])
        self.assertEqual(r.funding_paid,D(4))
        self.assertEqual(r.net_pnl,D(-4))
        self.assertEqual(r.closed_trades[0].funding_paid,D(4))
        self.assertEqual(r.closed_trades[0].net_pnl,D(-4))
        self.assertEqual(funding_payment(D(-2),D(1),D(".01"),D(100)),D(-2))

    def test_missing_misaligned_and_extra_risk(self):
        c,p=setup()
        for m in (FLAT[:-1],FLAT[1:],FLAT+(FLAT[-1],)):
            with self.assertRaises(ValueError):execute(c,p,Long,marks=m)
        c,p=setup(funding=True)
        with self.assertRaisesRegex(ValueError,"funding settlement"):execute(c,p,Long)

    def test_manifest_profile_provenance(self):
        c,p=setup()
        with self.assertRaisesRegex(ValueError,"manifest mismatch"):
            run_backtest(c,Long,lambda:FLAT,linear_contract=True,dataset_manifest_sha256=H,
                         margin_profile=p,risk_factory=lambda:(),risk_manifest_sha256s=())
        with self.assertRaises(ValueError):execute(c,replace(p,effective_end=T+timedelta(minutes=1)),Long)
        r=execute(c,p,Long)
        self.assertEqual(r.result_sha256,execute(c,p,Long).result_sha256)
        self.assertEqual(len(r.margin_profile_sha256),64)
        self.assertEqual(len(r.scenarios[0].risk_stream_sha256),64)

class TierTests(unittest.TestCase):
    def profile(self,base):
        return TieredMarginProfile(base.profile_id,base.instrument,base.effective_start,base.effective_end,base.source,
            base.initial_rate_floor,base.maintenance_rate,base.max_notional,base.liquidation_fee_bps,
            tiers=(MarginTier(D(2050),D(".1"),D(".05")),MarginTier(base.max_notional,D(".2"),D(".15"))))
    def test_tier_boundaries_and_buffer(self):
        c,p=setup();p=self.profile(p)
        self.assertEqual(p.maintenance(D(2050)),D("102.5"))
        self.assertEqual(p.maintenance(D(2051)),D("307.65"))
        self.assertFalse(p.allows_leverage(D(2051),D(10)))
        self.assertEqual(p.initial(D(2051),D(10)),D("410.2"))
        with self.assertRaises(ValueError):p.maintenance(p.max_notional+1)
        with self.assertRaises(ValueError):replace(p,tiers=tuple(reversed(p.tiers)))
        q=replace(p,preliquidation_buffer_points=D(1))
        self.assertGreater(q.protective_surplus(D(-20),D(1),D(102)),D(100))
    def test_mark_transition_triggers_short_liquidation(self):
        class Short(BaseStrategy):
            def on_start(self,c):submit(c,"short",Side.SELL,qty=20)
        c,p=setup()
        marks=bars([(100,100,100,100),(103,103,103,103),(103,103,103,103),(103,103,103,103)])
        baseline=execute(c,p,Short,marks=marks)
        result=execute(c,self.profile(p),Short,marks=marks)
        self.assertFalse(baseline.scenarios[0].liquidations)
        self.assertEqual(len(result.scenarios[0].liquidations),1)
        self.assertEqual(result.scenarios[0].liquidations[0].maintenance,D(309))
        self.assertNotEqual(result.margin_profile_sha256,baseline.margin_profile_sha256)
        self.assertEqual(result.result_sha256,execute(c,self.profile(p),Short,marks=marks).result_sha256)
    def test_entry_above_bracket_leverage_rejected(self):
        class Large(BaseStrategy):
            def on_start(self,c):submit(c,"large",qty=21)
        for mode in (MarginMode.ISOLATED,MarginMode.CROSS):
            c,p=setup(mode)
            r=execute(c,self.profile(p),Large).scenarios[0]
            self.assertFalse(r.fills)
            self.assertTrue(any(o.detail=="initial_margin_or_notional_cap" for o in r.orders))
    def test_position_above_last_cap_fails_closed(self):
        c,p=setup()
        p=replace(self.profile(p),max_notional=D(2050),tiers=(MarginTier(D(2050),D(".1"),D(".05")),))
        marks=bars([(100,100,100,100),(103,103,103,103),(103,103,103,103),(103,103,103,103)])
        with self.assertRaisesRegex(ValueError,"notional cap"):execute(c,p,Long,marks=marks)

if __name__=="__main__":unittest.main()
