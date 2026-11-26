"""Bounded forward candle paper sessions. No exchange credentials or order API."""
from datetime import datetime,timezone
from decimal import Decimal as D
from hashlib import sha256
from math import lcm
from typing import Annotated,Literal
from urllib.request import build_opener,HTTPRedirectHandler,Request,ProxyHandler
from urllib.parse import urlencode
import json
import time
import uuid
from pydantic import BaseModel,ConfigDict,Field,model_validator
from ..visual import Graph,recover_graph,compile_graph,DecimalText
from ..contracts import (Instrument,AssetClass,Timeframe,Candle,DatasetRef,DataKind,
    StrategyRef,BacktestConfig,CostModel,MarginMode,IntrabarPolicy)
from ..backtest import run_backtest
from ..serialization import fingerprint,to_wire
from .historical import GraphStrategy,frames,Id
from .analytics import summarize
from .store import Missing,Conflict,canonical

SOURCE="https://api.india.delta.exchange/v2/history/candles"
MAX_DELAY=120
CLOSE_GRACE=10
MAX_SESSIONS=100
ACTIVE=("scheduled","running")
FIELDS=("open","high","low","close","volume")

class PaperRequest(BaseModel):
    model_config=ConfigDict(extra="forbid",strict=True)
    strategy_id:Id
    version:Annotated[int,Field(ge=1,le=100)]
    symbol:Literal["BTCUSD","ETHUSD"]
    duration_minutes:Annotated[int,Field(ge=1,le=120)]=60
    initial_equity:DecimalText="100"
    maker_bps:DecimalText="2"
    taker_bps:DecimalText="5"
    tax_rate:DecimalText="0.18"
    slippage_bps:DecimalText="0"
    tick_size:DecimalText="0.1"
    lot_size:DecimalText="0.001"
    multiplier:DecimalText="1"
    max_drawdown_pct:DecimalText="10"
    acknowledge_assumptions:Literal[True]
    @model_validator(mode="after")
    def check(self):
        for k,lo,hi in (("initial_equity","1","1000000"),("maker_bps","0","100"),("taker_bps","0","100"),
                        ("tax_rate","0","1"),("slippage_bps","0","100"),("tick_size","0.00000001","1000"),
                        ("lot_size","0.00000001","1000"),("multiplier","0.00000001","1000"),
                        ("max_drawdown_pct","0.01","100")):
            if not D(lo)<=D(getattr(self,k))<=D(hi):raise ValueError("invalid "+k)
        return self

def dt(t):return datetime.fromtimestamp(t,timezone.utc)

def instrument(p):
    return Instrument("delta_india",p["symbol"],AssetClass.CRYPTO_PERPETUAL,"USD","USD",
                      D(p["tick_size"]),D(p["lot_size"]),D(p["multiplier"]))

def candle(p,row):
    t=row["time"]
    if type(t) is not int or t%60:raise ValueError("invalid candle label")
    return Candle(instrument(p),Timeframe(60),dt(t),dt(t+60),**{k:D(row[k]) for k in FIELDS})

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None

def fetch_public(symbol,t):
    """One exact candle; fixed HTTPS GET endpoint, no redirect, proxy or credentials."""
    if symbol not in ("BTCUSD","ETHUSD") or type(t) is not int or t%60:
        raise ValueError("invalid public request")
    url=SOURCE+"?"+urlencode({"symbol":symbol,"resolution":"1m","start":t,"end":t+60})
    opener=build_opener(ProxyHandler({}),NoRedirect())
    with opener.open(Request(url,headers={"Accept":"application/json","User-Agent":"BTC-Analysis-paper/1"}),timeout=8) as r:
        raw=r.read(65537)
    if len(raw)>65536:raise ValueError("oversized response")
    result=json.loads(raw,parse_float=D)
    if result.get("success") is not True or not isinstance(result.get("result"),list):
        raise ValueError("invalid market response")
    match=[x for x in result["result"] if x.get("time")==t]
    if len(match)!=1:raise ValueError("expected exactly one matching candle")
    return {"time":t,**{k:str(match[0][k]) for k in FIELDS}}

class PaperStore:
    def __init__(self,store):
        self.store=store
        with store.connection() as c:
            c.executescript("""
            CREATE TABLE IF NOT EXISTS paper_sessions(
              id TEXT PRIMARY KEY, owner TEXT NOT NULL, request_key TEXT NOT NULL,
              config TEXT NOT NULL, config_sha TEXT NOT NULL, status TEXT NOT NULL,
              start INTEGER NOT NULL, end INTEGER NOT NULL, cursor INTEGER NOT NULL,
              created INTEGER NOT NULL, updated INTEGER NOT NULL, reason TEXT,
              checkpoint TEXT, revision INTEGER NOT NULL DEFAULT 0,
              UNIQUE(owner,request_key));
            CREATE TABLE IF NOT EXISTS paper_candles(
              session_id TEXT NOT NULL REFERENCES paper_sessions(id), time INTEGER NOT NULL,
              received INTEGER NOT NULL, data TEXT NOT NULL, PRIMARY KEY(session_id,time));
            """)

    def _public(self,r):
        if r is None:raise Missing("paper session not found")
        p=json.loads(r["config"])
        return {**{k:r[k] for k in ("id","status","start","end","cursor","created","updated","reason")},
            "config":{k:v for k,v in p.items() if k!="graph"},"config_sha256":r["config_sha"],
            "checkpoint":json.loads(r["checkpoint"]) if r["checkpoint"] else None,
            "execution":"paper_only","live_order_submission":False}

    def create(self,owner,key,request,clock=None):
        now=int(time.time()) if clock is None else clock
        p=request.model_dump()
        with self.store.connection(True) as c:
            old=c.execute("SELECT * FROM paper_sessions WHERE owner=? AND request_key=?",(owner,key)).fetchone()
            if old:
                if json.loads(old["config"])["request"]!=p:raise Conflict("idempotency key reused")
                return self._public(old)
            state=self.store._registry(c,owner,request.strategy_id)
            if state["archived"] or state["frozen_version"]!=request.version:
                raise Conflict("paper sessions require an active frozen visual revision")
            row=c.execute("SELECT * FROM revisions WHERE strategy_id=? AND version=?",(request.strategy_id,request.version)).fetchone()
            if row is None:raise Missing("revision not found")
            compiled=recover_graph(row["source"])
            if sha256(compiled["source"].encode()).hexdigest()!=row["code_sha"]:raise ValueError("source hash mismatch")
            g=Graph.model_validate(compiled["graph"])
            alignment=lcm(*frames(g))
            if g.execution_timeframe!=60 or alignment>900 or request.duration_minutes*60%alignment:
                raise ValueError("require 1m execution, aligned frames <=15m and divisible duration")
            if c.execute("SELECT COUNT(*) FROM paper_sessions WHERE owner=?",(owner,)).fetchone()[0]>=MAX_SESSIONS:
                raise Conflict("paper history quota reached")
            if c.execute("SELECT 1 FROM paper_sessions WHERE owner=? AND status IN ('scheduled','running')",(owner,)).fetchone():
                raise Conflict("one active paper session per owner")
            if c.execute("SELECT COUNT(*) FROM paper_sessions WHERE status IN ('scheduled','running')").fetchone()[0]>=4:
                raise Conflict("paper service capacity reached")
            start=(now//alignment+1)*alignment;end=start+request.duration_minutes*60
            config={**p,"request":p,"graph":compiled["graph"],"graph_sha256":compiled["graph_sha256"],
                    "code_sha256":row["code_sha"],"alignment":alignment,"source":SOURCE,
                    "timestamp_label_verified":False}
            sid=uuid.uuid4().hex
            c.execute("""INSERT INTO paper_sessions(id,owner,request_key,config,config_sha,status,start,end,cursor,created,updated)
                      VALUES(?,?,?,?,?,'scheduled',?,?,?,?,?)""",
                      (sid,owner,key,canonical(config),fingerprint(config),start,end,start,now,now))
            return self._public(c.execute("SELECT * FROM paper_sessions WHERE id=?",(sid,)).fetchone())

    def list(self,owner):
        with self.store.connection() as c:
            return [self._public(r) for r in c.execute("SELECT * FROM paper_sessions WHERE owner=? ORDER BY created DESC,id LIMIT 100",(owner,))]

    def get(self,owner,sid):
        with self.store.connection() as c:return self._public(c.execute("SELECT * FROM paper_sessions WHERE owner=? AND id=?",(owner,sid)).fetchone())

    def stop(self,owner,sid):
        with self.store.connection(True) as c:
            r=c.execute("SELECT * FROM paper_sessions WHERE owner=? AND id=?",(owner,sid)).fetchone()
            if r is None:raise Missing("paper session not found")
            if r["status"] in ACTIVE:
                c.execute("UPDATE paper_sessions SET status='stopped',reason='operator_stop',revision=revision+1,updated=? WHERE id=?",(int(time.time()),sid))
            return self._public(c.execute("SELECT * FROM paper_sessions WHERE id=?",(sid,)).fetchone())

    def active(self):
        with self.store.connection() as c:
            return [dict(r) for r in c.execute("SELECT * FROM paper_sessions WHERE status IN ('scheduled','running') ORDER BY created,id")]

    def halt(self,r,reason,now):
        with self.store.connection(True) as c:
            c.execute("UPDATE paper_sessions SET status='halted',reason=?,revision=revision+1,updated=? WHERE id=? AND revision=? AND status IN ('scheduled','running')",
                      (reason,now,r["id"],r["revision"]))

    def advance(self,r,row,received):
        p=json.loads(r["config"]);t=r["cursor"]
        if fingerprint(p)!=r["config_sha"] or row["time"]!=t:
            raise ValueError("paper configuration/cursor mismatch")
        candle(p,row)
        if not t+60+CLOSE_GRACE<=received<=t+60+MAX_DELAY:raise ValueError("stale or premature candle")
        with self.store.connection() as c:
            rows=[json.loads(x["data"]) for x in c.execute("SELECT data FROM paper_candles WHERE session_id=? ORDER BY time",(r["id"],))]
        if len(rows)!=(t-r["start"])//60:raise ValueError("paper candle continuity mismatch")
        rows.append(row);end=t+60
        checkpoint=None
        if end%p["alignment"]==0:
            checkpoint=evaluate(p,r["start"],end,rows)
            if r["checkpoint"]:
                prev=json.loads(r["checkpoint"])
                for a,b in zip(prev["scenarios"],checkpoint["scenarios"]):
                    if a["path"]!=b["path"] or a["fills"]!=b["fills"][:len(a["fills"])]:
                        raise ValueError("paper prefix fill reconciliation failed")
        with self.store.connection(True) as c:
            current=c.execute("SELECT * FROM paper_sessions WHERE id=?",(r["id"],)).fetchone()
            if current["revision"]!=r["revision"] or current["status"] not in ACTIVE:return False
            state=self.store._registry(c,r["owner"],p["strategy_id"])
            if state["archived"] or state["frozen_version"]!=p["version"]:
                c.execute("UPDATE paper_sessions SET status='halted',reason='registry_state_changed',revision=revision+1,updated=? WHERE id=?",(received,r["id"]))
                return False
            status="completed" if end==r["end"] else "running";reason=None
            if checkpoint and any(D(x["metrics"]["max_event_drawdown_pct"])>=D(p["max_drawdown_pct"]) for x in checkpoint["scenarios"]):
                status="halted";reason="modeled_drawdown_limit"
            c.execute("INSERT INTO paper_candles VALUES(?,?,?,?)",(r["id"],t,received,canonical(row)))
            c.execute("""UPDATE paper_sessions SET cursor=?,status=?,reason=?,updated=?,revision=revision+1,
                      checkpoint=COALESCE(?,checkpoint) WHERE id=?""",
                      (end,status,reason,received,canonical(checkpoint) if checkpoint else None,r["id"]))
            return True

def evaluate(p,start,end,rows):
    g=Graph.model_validate(p["graph"]);compiled=compile_graph(g)
    if compiled["graph_sha256"]!=p["graph_sha256"] or sha256(compiled["source"].encode()).hexdigest()!=p["code_sha256"]:
        raise ValueError("paper source changed")
    i=instrument(p);bars=tuple(candle(p,row) for row in rows)
    digest=fingerprint(rows)
    ds=DatasetRef("paper:"+digest[:16],i,DataKind.OHLCV,Timeframe(60),dt(start),dt(end),digest,SOURCE,0,True)
    cfg=BacktestConfig(StrategyRef(p["strategy_id"],str(p["version"]),p["code_sha256"],p["graph_sha256"]),
        i,(ds,),dt(start),dt(end),Timeframe(g.signal_timeframe),Timeframe(60),D(p["initial_equity"]),"USD",D(1),
        MarginMode.ISOLATED,CostModel(D(p["maker_bps"]),D(p["taker_bps"]),D(p["tax_rate"]),D(p["slippage_bps"]),False,False,False,"paper-reference"),
        IntrabarPolicy.BOTH_PATHS,"Asia/Kolkata","crypto-24x7")
    result=run_backtest(cfg,lambda:GraphStrategy(g),lambda:iter(bars),linear_contract=True,dataset_manifest_sha256=digest)
    wire=to_wire(result)
    return {"through":end,"candle_sha256":digest,"result_sha256":result.result_sha256,
        "scenarios":[{"path":s["path"],"balance":s["balance"],"equity":s["final_equity"],
            "open_quantity":s["open_quantity"],"unrealized_pnl":s["open_unrealized_pnl"],
            "metrics":summarize(s),"fills":s["fills"],"closed_trades":s["closed_trades"]} for s in wire["scenarios"]]}

def poll_once(store,fetch=fetch_public,clock=time.time):
    for r in store.active():
        now=int(clock());t=r["cursor"]
        if now<t+60+CLOSE_GRACE:continue
        if now>t+60+MAX_DELAY:
            store.halt(r,"stale_or_missing_candle",now);continue
        p=json.loads(r["config"])
        try:row=fetch(p["symbol"],t)
        except (OSError,ValueError,KeyError,TypeError):
            # Retry only within bounded receipt window. Never backfill stale bars.
            continue
        received=int(clock())
        try:store.advance(r,row,received)
        except Exception:store.halt(r,"paper_data_or_reconciliation_failure",received)

def main():
    import argparse
    from .store import Store
    parser=argparse.ArgumentParser();parser.add_argument("--db",required=True);parser.add_argument("--once",action="store_true")
    args=parser.parse_args();store=PaperStore(Store(args.db))
    while True:
        poll_once(store)
        if args.once:return
        time.sleep(5)

if __name__=="__main__":main()
