"""Actual archive walk-forward integration, not strategy endorsement."""
import json,sys,time
from pathlib import Path
from btc_analysis.data import HistoryStore
from btc_analysis.service.walkforward_cli import run_study
root,symbol,output=sys.argv[1:]
with HistoryStore(root,symbol) as h:
    start=h.manifest["start"];end=start+44*86400
    request=dict(kind="historical_visual",strategy_id="a"*32,version=1,symbol=symbol,manifest_sha256=h.key,start=start,end=end,
        assume_open=True,acknowledge_reference=True,initial_equity="1000",lot_size="0.0001")
def rule(op):
    return {"enabled":True,"groups":[{"conditions":[{"left":{"kind":"price","timeframe":900,"field":"close"},"op":op,
        "right":{"kind":"indicator","timeframe":900,"name":"ema.value","parameters":{"period":20}}}]}]}
off={"enabled":False,"groups":[]}
graph=dict(signal_timeframe=900,execution_timeframe=60,exposure_pct="20",stop_loss_pct="1",take_profit_pct="2",
    long_entry=rule("cross_up"),long_exit=rule("cross_down"),short_entry=off,short_exit=off)
study=dict(start=start,train_minutes=30*1440,test_minutes=7*1440,folds=2,mode="rolling",objective="monthly_consistency",
    search=dict(method="grid",axes=[dict(key="stop_loss_pct",values=["1","2"])],max_drawdown_pct="100"),acknowledge=True)
if __name__=="__main__":
    t=time.perf_counter();r=run_study(root,request,graph,study,workers=2)
    assert len(r["folds"])==2 and all(len(f["training"])==2 for f in r["folds"])
    assert all(len(f["tests"])==5 for f in r["folds"])
    Path(output).write_text(json.dumps(r,indent=2))
    print(json.dumps(dict(symbol=symbol,folds=2,candidate_minutes=r["candidate_minutes"],elapsed_seconds=round(time.perf_counter()-t,3),
        modeled_checks_passed=r["modeled_checks_passed"],study_sha256=r["study_sha256"])))
