import unittest,json
from btc_analysis.service.browser_replay import replay
from test_browser_replay import SETTINGS
from test_visual import graph

T=1735689600
def inputs(mark_low="99",fund=True,scalp=False,preliq="0",leverage="10",mode="isolated"):
    trade="time,open,high,low,close,volume\n"
    mark="time,open,high,low,close\n"
    for n in range(4):
        t=T+n*60
        trade+=f"{t},100,103,99,102,1\n"
        low=mark_low if n==2 else "99"
        mark+=f"{t},100,103,{low},102\n"
    risk=dict(leverage=leverage,margin_mode=mode,initial_rate_floor="0.01",maintenance_rate="0.005",max_notional="100000",
              liquidation_fee_bps="5",profile_start=str(T),profile_end=str(T+240),profile_source="synthetic fixed tier",
              preliq_points=preliq,scalp_enabled=scalp,scalp_start=str(T-60),scalp_end=str(T+240),
              mark_csv=mark,funding_enabled=fund,funding_interval_seconds=120,funding_anchor_epoch=T,
              funding_csv=f"time,rate,reference_mark\n{T},0.001,100\n{T+120},0.001,100\n" if fund else "",acknowledge=True)
    return trade,risk

class LeveragedTests(unittest.TestCase):
    def run_risk(self,**kwargs):
        csv,risk=inputs(**kwargs);g=graph()
        g["take_profit_pct"]="50";g["stop_loss_pct"]="50"
        return replay(csv,json.dumps(g),"BTCUSD",SETTINGS,True,risk=risk)
    def test_actual_funding_and_leverage(self):
        a=self.run_risk()
        self.assertTrue(all(float(s["funding_paid"])>0 for s in a["scenarios"]))
        self.assertTrue(all(s["liquidation_count"]==0 for s in a["scenarios"]))
        self.assertEqual(a["risk"]["leverage"],"10")
    def test_isolated_liquidation_gap_and_cross_difference(self):
        iso=self.run_risk(mark_low="80",fund=False,preliq="1")
        cross=self.run_risk(mark_low="80",fund=False,preliq="1",mode="cross")
        self.assertTrue(all(s["liquidation_count"]==1 and s["preliq_count"]==0 for s in iso["scenarios"]))
        self.assertTrue(all(s["liquidation_count"]==0 for s in cross["scenarios"]))
    def test_protective_buffer(self):
        a=self.run_risk(mark_low="90.8",fund=False,preliq="1")
        self.assertTrue(all(s["preliq_count"]==1 and s["liquidation_count"]==0 for s in a["scenarios"]))
    def test_missing_risk_fails(self):
        csv,r=inputs();r["funding_csv"]="time,rate,reference_mark\n"
        with self.assertRaises(ValueError):replay(csv,json.dumps(graph()),"BTCUSD",SETTINGS,True,risk=r)
        csv,r=inputs();r["mark_csv"]=r["mark_csv"].replace(f"{T+60},",f"{T+120},")
        with self.assertRaises(ValueError):replay(csv,json.dumps(graph()),"BTCUSD",SETTINGS,True,risk=r)
    def test_fee_waiver(self):
        csv,r=inputs(fund=False,scalp=False)
        g=graph();g["long_exit"]=g["long_entry"];g["take_profit_pct"]="50";g["stop_loss_pct"]="50"
        a=replay(csv,json.dumps(g),"BTCUSD",SETTINGS,True,risk=r)
        b=replay(csv,json.dumps(g),"BTCUSD",SETTINGS,True,risk={**r,"scalp_enabled":True})
        self.assertTrue(all(float(x["fees"])>float(y["fees"]) for x,y in zip(a["scenarios"],b["scenarios"])))

    def test_tiered_adapter(self):
        csv,r=inputs(fund=False)
        r["tiers_json"]=json.dumps([{"upper_notional":"50000","initial_rate_floor":"0.01","maintenance_rate":"0.005"},{"upper_notional":"100000","initial_rate_floor":"0.02","maintenance_rate":"0.01"}])
        out=replay(csv,json.dumps(graph()),"BTCUSD",SETTINGS,True,risk=r)
        self.assertEqual(out["risk"]["profile"]["profile_id"],"user-whole-notional-tiers-v1")
        self.assertEqual(len(out["risk"]["profile"]["tiers"]),2)
        r["tiers_json"]="[]"
        with self.assertRaises(ValueError):replay(csv,json.dumps(graph()),"BTCUSD",SETTINGS,True,risk=r)

    def test_single_position_stress_adapter(self):
        csv,r=inputs(fund=False,mode="portfolio")
        r.update(initial_shock="0.1",maintenance_shock="0.08")
        out=replay(csv,json.dumps(graph()),"BTCUSD",SETTINGS,True,risk=r)
        self.assertEqual(out["risk"]["profile"]["profile_id"],"user-single-position-stress-v1")
        self.assertEqual(out["risk"]["margin_mode"],"portfolio")
        with self.assertRaises(ValueError):replay(csv,json.dumps(graph()),"BTCUSD",SETTINGS,True,risk={**r,"margin_mode":"cross"})
        with self.assertRaises(ValueError):replay(csv,json.dumps(graph()),"BTCUSD",SETTINGS,True,risk={**r,"tiers_json":"[]"})
