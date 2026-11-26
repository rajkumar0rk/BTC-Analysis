"""Analytics over stored results; never rerun strategies or infer reasons."""
from datetime import datetime
from decimal import Decimal as D, localcontext
from ..serialization import to_wire

ZERO=D(0)
MAX_REPLAY=240

def epoch(s):
    return int(datetime.fromisoformat(s.replace("Z","+00:00")).timestamp())

def scenario(job,path):
    if job["status"]!="succeeded" or not job["result"]:
        raise ValueError("completed result required")
    for s in job["result"]["result"]["scenarios"]:
        if s["path"]==path:return s
    raise ValueError("unknown scenario")

def summarize(s):
    with localcontext() as ctx:
        ctx.prec=50
        pnls=[D(t["net_pnl"]) for t in s["closed_trades"]]
        wins=[x for x in pnls if x>0];losses=[x for x in pnls if x<0]
        gain=sum(wins,ZERO);loss=-sum(losses,ZERO);n=len(pnls)
        start=D(s["initial_equity"]);net=D(s["net_pnl"]);closed=sum(pnls,ZERO)
        months=[D(m["pnl"]) for m in s["monthly"]]
        return to_wire(dict(trades=n,wins=len(wins),losses=len(losses),breakeven=n-len(wins)-len(losses),
            win_rate_pct=D(len(wins))*100/n if n else None,profit_factor=gain/loss if loss else None,
            profit_factor_status="finite" if loss else "no_losses" if gain else "undefined",
            closed_trade_net=closed,account_net=net,account_return_pct=net/start*100 if start else None,
            account_minus_closed=net-closed,expectancy=closed/n if n else None,
            average_win=gain/len(wins) if wins else None,average_loss=-loss/len(losses) if losses else None,
            best_trade=max(pnls) if pnls else None,worst_trade=min(pnls) if pnls else None,
            positive_months=sum(x>0 for x in months),negative_months=sum(x<0 for x in months),
            flat_months=sum(x==0 for x in months),max_event_drawdown_pct=D(s["max_event_drawdown_pct"])))

def analytics(job):
    if job.get("request",{}).get("kind") in ("optimization","validation"):raise ValueError("optimization has candidate summaries, not trade analytics")
    if job["status"]!="succeeded" or not job["result"]:raise ValueError("completed result required")
    return {"result_sha256":job["result"]["result_sha256"],
            "scenarios":[{"path":s["path"],"metrics":summarize(s)} for s in job["result"]["result"]["scenarios"]]}

def trade_replay(job,path,trade_id,root,offset=0):
    s=scenario(job,path);r=job["request"]
    if r["kind"]!="historical_visual" or job["result"]["synthetic"] or root is None:
        raise ValueError("historical replay unavailable for this result")
    if job["result"]["dataset_manifest_sha256"]!=r["manifest_sha256"]:
        raise ValueError("dataset provenance mismatch")
    t=next((t for t in s["closed_trades"] if t["trade_id"]==trade_id),None)
    if t is None:raise ValueError("unknown closed trade")
    fills=t["entry_fills"]+t["exit_fills"]
    evidence={e["fill_id"]:e for e in s["execution_evidence"]}
    if any(x["fill_id"] not in evidence for x in fills):raise ValueError("missing fill evidence")
    start=max(r["start"],min(epoch(evidence[x["fill_id"]]["bar_open_utc"]) for x in fills)-300)
    end=min(r["end"],max(epoch(evidence[x["fill_id"]]["bar_close_utc"]) for x in fills)+300)
    total=(end-start)//60
    if type(offset) is not int or not 0<=offset<total:raise ValueError("invalid replay offset")
    lo=start+offset*60;hi=min(end,lo+MAX_REPLAY*60)
    from ..data import HistoryStore
    with HistoryStore(root,r["symbol"],r["manifest_sha256"]) as h:
        rows=h.query(lo,hi,assume_open=r["assume_open"]).to_pylist()
        if len(rows)!=(hi-lo)//60:raise ValueError("replay coverage incomplete")
        candles=to_wire(rows)
    markers=[]
    for fill in fills:
        e=evidence[fill["fill_id"]];t0=epoch(e["bar_open_utc"])
        if lo<=t0<hi:
            markers.append({"bar_open":t0,"bar_close":epoch(e["bar_close_utc"]),
                "phase":e["phase"],"path":e["path"],"fill":fill,
                "role":"entry" if fill in t["entry_fills"] else "exit"})
    return {"symbol":r["symbol"],"dataset_manifest_sha256":r["manifest_sha256"],
        "timestamp_label_verified":job["result"]["timestamp_label_verified"],
        "scenario":path,"trade_id":trade_id,"offset":offset,"total":total,
        "next_offset":offset+len(rows) if offset+len(rows)<total else None,
        "previous_offset":max(0,offset-MAX_REPLAY) if offset else None,
        "candles":candles,"markers":markers}
