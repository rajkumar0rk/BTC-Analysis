"""Full pinned BTC/ETH replay using explicit sample graph; no strategy recommendation."""
import argparse,json,time,resource
from pathlib import Path
from btc_analysis.data import HistoryStore
from btc_analysis.service.longrun import run

def main():
    p=argparse.ArgumentParser();p.add_argument("--history",required=True);p.add_argument("--output",required=True)
    p.add_argument("--symbol",choices=["BTCUSD","ETHUSD"],required=True);a=p.parse_args()
    output=Path(a.output);output.mkdir(parents=True,exist_ok=True)
    with HistoryStore(a.history,a.symbol) as h:
        start,end=h.manifest["start"],h.manifest["end"]
        assert start%900==end%900==0
        request=dict(kind="historical_visual",strategy_id="a"*32,version=1,symbol=a.symbol,manifest_sha256=h.key,
            start=start,end=end,assume_open=True,acknowledge_reference=True,initial_equity="1000",lot_size="0.0001")
    def rule(op):
        return {"enabled":True,"mode":"any","groups":[{"mode":"all","conditions":[{"left":{"kind":"price","timeframe":900,"field":"close"},
            "op":op,"right":{"kind":"indicator","timeframe":900,"name":"ema.value","parameters":{"period":20}}}]}]}
    disabled={"enabled":False,"groups":[]}
    graph=dict(signal_timeframe=900,execution_timeframe=60,exposure_pct="20",stop_loss_pct="1",take_profit_pct="2",
        long_entry=rule("cross_up"),long_exit=rule("cross_down"),short_entry=disabled,short_exit=disabled)
    t=time.perf_counter();result=run(a.history,request,graph,output/a.symbol)
    expected=(end-start)//60;scenarios=result["result"]["scenarios"]
    assert len(scenarios)==2 and all(s["bars"]==expected for s in scenarios)
    assert all(s["summary"]["trades"]>0 for s in scenarios)
    report=dict(symbol=a.symbol,expected_bars=expected,paths=2,elapsed_seconds=round(time.perf_counter()-t,3),
        peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,result_sha256=result["result_sha256"],
        timestamp_label_verified=result["timestamp_label_verified"])
    (output/(a.symbol+"-benchmark.json")).write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report))
if __name__=="__main__":main()
