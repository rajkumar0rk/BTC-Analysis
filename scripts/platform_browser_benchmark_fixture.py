"""Private CI-only 31-day actual archive fixture; never bundled into Pages."""
import sys,json,time
from pathlib import Path
from btc_analysis.data import HistoryStore
from btc_analysis.service.browser_replay import replay
root,symbol,dest=sys.argv[1:]
with HistoryStore(root,symbol) as h:
    start=h.manifest["start"]
    rows=h.query(start,start+31*86400,assume_open=True).to_pylist()
assert len(rows)==44640
csv="time,open,high,low,close,volume\n"+"".join(",".join(str(row[k]) if k=="time" else format(row[k],"f") for k in ("time","open","high","low","close","volume"))+"\n" for row in rows)
def rule(op):
    return {"enabled":True,"groups":[{"conditions":[{"left":{"kind":"price","timeframe":900,"field":"close"},"op":op,"right":{"kind":"indicator","timeframe":900,"name":"ema.value","parameters":{"period":20}}}]}]}
off={"enabled":False,"groups":[]}
g={"signal_timeframe":900,"execution_timeframe":60,"exposure_pct":"20","stop_loss_pct":"1","take_profit_pct":"2","long_entry":rule("cross_up"),"long_exit":rule("cross_down"),"short_entry":off,"short_exit":off}
settings=dict(initial_equity="1000",maker_bps="2",taker_bps="5",tax_rate="0.18",slippage_bps="0",tick_size="0.1",lot_size="0.0001",multiplier="1")
t=time.perf_counter();r=replay(csv,json.dumps(g),symbol,settings,True)
assert all(s["bars"]==44640 for s in r["scenarios"])
Path(dest).write_text(json.dumps({"csv":csv,"graph":json.dumps(g),"settings":settings,"symbol":symbol,"assume":True,"expected":r["result_sha256"],"native_seconds":time.perf_counter()-t}))
