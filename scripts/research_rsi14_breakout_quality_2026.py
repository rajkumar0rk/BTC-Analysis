"""Frozen validation, no parameter search. Primary: fixed trailing + breakout quality."""
import json,gzip,math
from pathlib import Path
import numpy as np
import research_rsi14_2026_loader as y
import research_rsi14_regime_filters as r
from research_rsi14_depth_stability import q,checks
OUT=Path("scratch/rsi14_breakout_quality_2026")
def run():
    checks();OUT.mkdir(parents=True,exist_ok=True)
    q.candles=y.candles
    bars,signals,snapshots,extra,rec=y.load()
    ind=q.indicators(bars,snapshots)
    all_results={}
    for period,end in (("jan-oct",y.CUTOFF),("through-nov26",y.END)):
        y.MONTHS=[f"2026-{m:02d}" for m in range(1,11 if end==y.CUTOFF else 12)]
        n=(end-y.START)//60
        bb=bars[:,:n]
        ii=tuple(x[:n] if k<2 else x[:n//60+1] if k==4 else x[:n//15+1] for k,x in enumerate(ind))
        ss=[s for s in signals if s[0]<n]
        setups=q.setup_rows(bb,ss,snapshots,extra)
        dummy=np.full(len(ii[-1]),np.nan)
        all_results[period]={}
        for idea in ("baseline","breakout-quality"):
            ts=r.replay(bb,ii,setups,y.START,end,"80-retest-invalidation",idea,snapshots,extra,dummy,dummy,dummy,dummy,dummy)
            assert all(y.EVAL<=int(y.datetime.fromisoformat(t["entry_utc"]).timestamp())<end for t in ts)
            s=y.summarize(ts);st=y.summarize(ts,50)
            s["stress"]=dict(net=st["net"],months=st["profitable_months"],pf=st["profit_factor"],dd=st["realized_drawdown_points"],monthly=st["monthly_entry_attribution"])
            s["minutes"]=(end-y.EVAL)//60
            s["meaningful_wins_over_50"]=sum(t["net_points"]>50 for t in ts)
            s["exit_counts"]={reason:sum(t["exit_reason"]==reason for t in ts) for reason in sorted({t["exit_reason"] for t in ts})}
            print("VALIDATION",json.dumps(dict(period=period,idea=idea,**s),allow_nan=False))
            all_results[period][idea]=dict(summary=s,trades=ts)
    with gzip.open(OUT/"all_results.json.gz","wt") as f:json.dump(all_results,f,allow_nan=False,separators=(",",":"))
if __name__=="__main__":run()
