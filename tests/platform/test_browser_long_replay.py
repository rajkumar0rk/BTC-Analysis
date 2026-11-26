import gzip,json,tempfile,unittest
from pathlib import Path
from hashlib import sha256
from datetime import datetime,timezone
from btc_analysis.service.browser_long_replay import replay_archive,plan_archive
from btc_analysis.service.browser_replay import replay

class LongBrowserTest(unittest.TestCase):
    def test_cross_partition_matches_continuous_short_replay(self):
        root=Path(__file__).resolve().parents[2]/"data/delta_india/BTCUSD/1m"
        m=json.loads((root/"manifest.json").read_text())
        selected=[p for p in m["partitions"] if p["file"] in ("2025-01.csv.gz","2025-02.csv.gz")]
        graph=json.dumps({"signal_timeframe":300,"execution_timeframe":60,"exposure_pct":"20","stop_loss_pct":"1","take_profit_pct":"2","long_entry":{"enabled":True,"groups":[{"conditions":[{"left":{"kind":"price","timeframe":300,"field":"close"},"op":"cross_up","right":{"kind":"indicator","timeframe":300,"name":"ema.value","parameters":{"period":3}}}]}]},"long_exit":{"enabled":False,"groups":[]},"short_entry":{"enabled":False,"groups":[]},"short_exit":{"enabled":False,"groups":[]}})
        settings={"initial_equity":"100","maker_bps":"2","taker_bps":"5","tax_rate":"0.18","slippage_bps":"0","tick_size":"0.1","lot_size":"0.001","multiplier":"1"}
        manifest=json.dumps(m);plan=plan_archive(manifest,"BTCUSD","2025-01-31","2025-02-01")
        with tempfile.TemporaryDirectory() as tmp:
            rows=[]
            for p in selected:
                raw=(root/p["file"]).read_bytes();(Path(tmp)/(p["sha256_gzip"]+".bin")).write_bytes(raw)
                rows.extend(line for line in gzip.decompress(raw).decode().splitlines()[1:] if plan["start"]<=int(line.split(",")[0])<plan["end"])
            long=replay_archive(manifest,"2025-01-31","2025-02-01",graph,"BTCUSD",settings,True,tmp)
            short=replay("time,open,high,low,close,volume\n"+"\n".join(rows)+"\n",graph,"BTCUSD",settings,True)
            self.assertEqual(long["worst_path"],short["worst_path"])
            for a,b in zip(long["scenarios"],short["scenarios"]):
                self.assertEqual(a["bars"],2880)
                for k in ("final_equity","fees","taxes","monthly"):self.assertEqual(a[k],b[k],k)
                for k in ("account_net","trades","wins","losses","profit_factor","max_event_drawdown_pct"):self.assertEqual(a["metrics"][k],b["metrics"][k],k)
                self.assertEqual(len(a["yearly"]),1)
                self.assertEqual(a["yearly"][0]["pnl"],a["metrics"]["account_net"])
            (Path(tmp)/(selected[0]["sha256_gzip"]+".bin")).write_bytes(b"bad")
            with self.assertRaisesRegex(ValueError,"checksum"):
                replay_archive(manifest,"2025-01-31","2025-02-01",graph,"BTCUSD",settings,True,tmp)
