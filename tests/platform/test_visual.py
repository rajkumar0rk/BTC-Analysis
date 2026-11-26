import unittest
import tempfile
from pathlib import Path
from copy import deepcopy
from decimal import Decimal as D
from fastapi.testclient import TestClient
from btc_analysis.service.api import create_app
from btc_analysis.visual import Graph,compile_graph,recover_graph
from btc_analysis.visual_runtime import compare,constant,VisualStrategyBase
from test_backtest_engine import cfg,bars,run

def price():return {"kind":"price","timeframe":60,"field":"close"}
def number(v):return {"kind":"constant","value":str(v)}
def rule(op="gt",v="100"):
    return {"enabled":True,"mode":"any","groups":[{"mode":"all","conditions":[{"left":price(),"op":op,"right":number(v)}]}]}
def disabled():return {"enabled":False,"groups":[]}
def graph():
    return {"signal_timeframe":60,"execution_timeframe":60,"exposure_pct":"20","stop_loss_pct":"5",
            "take_profit_pct":"5","long_entry":rule(),"short_entry":disabled(),
            "long_exit":disabled(),"short_exit":disabled()}

class VisualTests(unittest.TestCase):
    def test_compile_deterministic_and_recover(self):
        g=graph();a=compile_graph(Graph.model_validate(g))
        g["exposure_pct"]="20.00"
        b=compile_graph(Graph.model_validate(g))
        self.assertEqual(a,b);self.assertEqual(recover_graph(a["source"]),a)
        self.assertFalse(a["execution_allowed"])
        compile(a["source"],"<generated>","exec")
        with self.assertRaises(ValueError):recover_graph(a["source"]+"# edited\n")
        with self.assertRaises(ValueError):recover_graph("pass")

    def test_validation(self):
        for patch in ({"stop_loss_pct":"0"},{"exposure_pct":"101"},{"signal_timeframe":60,"execution_timeframe":300},
                      {"long_entry":disabled()},{"long_entry":{"enabled":True,"groups":[]}},{"unknown":1}):
            with self.subTest(patch=patch),self.assertRaises(ValueError):Graph.model_validate({**graph(),**patch})
        g=graph();g["long_entry"]["groups"][0]["conditions"][0]["right"]=number("1; import os")
        with self.assertRaises(ValueError):Graph.model_validate(g)

    def test_indicator_defaults_and_crossing(self):
        g=graph();c=g["long_entry"]["groups"][0]["conditions"][0]
        c["right"]={"kind":"indicator","timeframe":60,"name":"ema.value","parameters":{}}
        a=compile_graph(Graph.model_validate(g))
        self.assertEqual(a["graph"]["long_entry"]["groups"][0]["conditions"][0]["right"]["parameters"],{"period":20})
        c["op"]="cross_up";c["right"]["timeframe"]=300
        with self.assertRaises(ValueError):Graph.model_validate(g)
        self.assertFalse(compare("gt",(None,None),constant("1")))
        self.assertTrue(compare("cross_up",(D(1),D(3)),constant("2")))

    def test_generated_python_and_handwritten_engine_parity(self):
        # Only compiler-produced test fixture source is executed here, not user source.
        source=compile_graph(Graph.model_validate(graph()))["source"]
        namespace={};exec(compile(source,"<trusted-test-generated>","exec"),namespace)
        generated=namespace["VisualStrategy"]
        class Reference(VisualStrategyBase):
            signal_seconds=60;execution_seconds=60
            exposure=D(".2");stop_loss=D(".05");take_profit=D(".05")
            def extra_timeframes(self):
                from btc_analysis.contracts import Timeframe
                return (Timeframe(60),)
            def long_entry(self,ctx):
                from btc_analysis.contracts import Timeframe
                return ctx.candles(Timeframe(60),1)[-1].close>D(100)
        d=bars([(100,103,99,102),(102,104,101,103),(103,110,90,103),(103,103,103,103)])
        a=run(cfg(),generated,d);b=run(cfg(),Reference,d)
        self.assertEqual(a.scenarios,b.scenarios)
        self.assertTrue(a.scenarios[0].closed_trades)
        self.assertEqual(a.scenarios[0].fills[0].reason,"visual_long_entry")
        self.assertIn(a.scenarios[0].fills[1].reason,("visual_stop_loss","visual_take_profit"))

    def test_authenticated_compile_save_recover(self):
        with tempfile.TemporaryDirectory() as d:
            with TestClient(create_app(Path(d)/"db.sqlite",{"owner":"a"*40})) as c:
                h={"Authorization":"Bearer "+"a"*40}
                self.assertEqual(c.post("/v1/visual/compile",json=graph()).status_code,401)
                a=c.post("/v1/visual/compile",headers=h,json=graph())
                self.assertEqual(a.status_code,200,a.text)
                source=a.json()["source"]
                r=c.post("/v1/strategies",headers=h,json={"name":"visual","source":source})
                self.assertEqual(r.status_code,201)
                self.assertEqual(c.post("/v1/visual/recover",headers=h,json={"source":r.json()["source"]}).json(),a.json())
                self.assertEqual(c.post("/v1/visual/recover",headers=h,json={"source":source+"# changed"}).status_code,422)

if __name__=="__main__":unittest.main()
