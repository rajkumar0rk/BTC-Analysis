import unittest,tempfile,json
from pathlib import Path
from hashlib import sha256
from btc_analysis.backtest import run_backtest
from btc_analysis.backtest.archive import ScenarioArchive
from btc_analysis.serialization import to_wire
from btc_analysis.service.historical import HistoricalRequest,LongHistoricalRequest
from test_backtest_engine import cfg,bars,RoundTrip,H

class LongRunTests(unittest.TestCase):
    def test_exact_archive_parity(self):
        data=bars([(100,120,90,110),(105,115,100,112),(120,130,119,125),(130,130,130,130)])
        args=(cfg(),RoundTrip,lambda:iter(data))
        kwargs=dict(linear_contract=True,dataset_manifest_sha256=H)
        full=run_backtest(*args,**kwargs)
        with tempfile.TemporaryDirectory() as d:
            archived=run_backtest(*args,**kwargs,archive_factory=lambda p:ScenarioArchive(d,p))
            self.assertEqual(full.worst_path,archived.worst_path)
            for a,b in zip(full.scenarios,archived.scenarios):
                self.assertEqual(a.final_equity,b.final_equity)
                self.assertEqual(a.observed_candle_sha256,b.observed_candle_sha256)
                self.assertEqual(a.monthly,b.monthly)
                self.assertEqual(a.max_event_drawdown_pct,b.summary["max_event_drawdown_pct"])
                for key,ref in b.files.items():
                    raw=(Path(d)/b.path/ref["file"]).read_bytes()
                    self.assertEqual(sha256(raw).hexdigest(),ref["sha256"])
                    self.assertEqual([json.loads(l) for l in raw.splitlines()],to_wire(getattr(a,key)))
    def test_long_request_limit_without_relaxing_api(self):
        start=1735689600
        body=dict(kind="historical_visual",strategy_id="a"*32,version=1,symbol="BTCUSD",manifest_sha256=H,
            start=start,end=start+2*86400,assume_open=True,acknowledge_reference=True)
        with self.assertRaises(ValueError):HistoricalRequest.model_validate(body)
        self.assertEqual(LongHistoricalRequest.model_validate(body).end,body["end"])
        with self.assertRaises(ValueError):LongHistoricalRequest.model_validate({**body,"end":start+1099*86400})
        with self.assertRaises(ValueError):LongHistoricalRequest.model_validate({**body,"taker_bps":"101"})
