"""Generate deterministic native-Python oracle for browser CI."""
import json
from pathlib import Path
from btc_analysis.service.browser_replay import replay
g={"signal_timeframe":60,"execution_timeframe":60,"exposure_pct":"20","stop_loss_pct":"5","take_profit_pct":"5",
    "long_entry":{"enabled":True,"groups":[{"conditions":[{"left":{"kind":"price","timeframe":60,"field":"close"},"op":"gt","right":{"kind":"constant","value":"100"}}]}]},
    "short_entry":{"enabled":False,"groups":[]},"long_exit":{"enabled":False,"groups":[]},"short_exit":{"enabled":False,"groups":[]}}
csv="time,open,high,low,close,volume\n"+"".join(f"{1735689600+i*60},{100+i%10},{103+i%10},{99+i%10},{102+i%10},1\n" for i in range(60))
settings=dict(initial_equity="100",maker_bps="2",taker_bps="5",tax_rate="0.18",slippage_bps="0",tick_size="0.1",lot_size="0.001",multiplier="1")
r=replay(csv,json.dumps(g),"BTCUSD",settings,True)
changed={**g,"stop_loss_pct":"2"}
changed_result=replay(csv,json.dumps(changed),"BTCUSD",settings,True)
assert changed_result["result_sha256"]!=r["result_sha256"]
from btc_analysis.service.walkforward import browser_fold
study=dict(start=1735689600,train_minutes=20,test_minutes=10,folds=2,mode="rolling",
    search=dict(method="grid",axes=[dict(key="stop_loss_pct",values=["2","5"])],max_drawdown_pct="100",min_trades=1),
    objective="net_return",acknowledge=True)
folds=[browser_fold(csv,json.dumps(g),"BTCUSD",settings,True,study,n) for n in (1,2)]
Path("apps/web/tests/browser-oracle.json").write_text(json.dumps({"csv":csv,"graph":g,"result":r,"changed_graph":changed,"changed_result":changed_result,"walkforward":folds}))
