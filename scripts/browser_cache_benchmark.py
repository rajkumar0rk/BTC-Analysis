"""Measure cold and warm actual-archive browser-adapter workload in native Python."""
import json,time,sys
from pathlib import Path
from btc_analysis.data import HistoryStore
from btc_analysis.service.browser_replay import replay
from btc_analysis.service.browser_cache import ReplayCache

def main():
    root,output=sys.argv[1:]
    reports=[]
    for symbol in ("BTCUSD","ETHUSD"):
        with HistoryStore(root,symbol) as h:
            lo=h.manifest["start"];hi=lo+31*86400
            rows=h.query(lo,hi,assume_open=True).to_pylist()
        csv="time,open,high,low,close,volume\n"+"".join(",".join((str(row[k]) if k=="time" else format(row[k],"f")) for k in ("time","open","high","low","close","volume"))+"\n" for row in rows)
        def rule(op):
            return {"enabled":True,"groups":[{"conditions":[{"left":{"kind":"price","timeframe":900,"field":"close"},"op":op,"right":{"kind":"indicator","timeframe":900,"name":"ema.value","parameters":{"period":20}}}]}]}
        off={"enabled":False,"groups":[]}
        g={"signal_timeframe":900,"execution_timeframe":60,"exposure_pct":"20","stop_loss_pct":"1","take_profit_pct":"2","long_entry":rule("cross_up"),"long_exit":rule("cross_down"),"short_entry":off,"short_exit":off}
        settings=dict(initial_equity="1000",maker_bps="2",taker_bps="5",tax_rate="0.18",slippage_bps="0",tick_size="0.1",lot_size="0.0001",multiplier="1")
        cache=ReplayCache()
        def timed(cache):
            t=time.perf_counter();r=replay(csv,json.dumps(g),symbol,settings,True,cache=cache);return r,round(time.perf_counter()-t,4)
        a,cold=timed(cache);b,warm=timed(cache);c,uncached=timed(None)
        assert a==b==c and a["scenarios"][0]["bars"]==44640
        reports.append({"symbol":symbol,"bars":44640,"cold_seconds":cold,"warm_seconds":warm,"uncached_seconds":uncached,"cache":cache.stats,"result_sha256":a["result_sha256"],"runtime":"native Python, not browser"})
    print(json.dumps(reports,indent=2));Path(output).write_text(json.dumps(reports,indent=2))
if __name__=="__main__":main()
