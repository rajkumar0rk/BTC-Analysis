"""Trusted Python reference engine for local browser replay. No source eval/exec."""
import csv,io,json,re
from datetime import datetime,timezone,timedelta
from decimal import Decimal as D
from hashlib import sha256
from ..contracts import (Instrument,AssetClass,Timeframe,Candle,DatasetRef,DataKind,
                         StrategyRef,BacktestConfig,CostModel,MarginMode,IntrabarPolicy)
from ..visual import Graph,compile_graph,recover_graph
from .historical import GraphStrategy,frames
from .analytics import summarize
from ..serialization import to_wire
from ..backtest import run_backtest

MAX_ROWS=10080
MAX_CSV=4*1024*1024

def replay(csv_text,graph_text,symbol,settings,assume_open,progress=lambda p:True):
    if assume_open is not True:raise ValueError("acknowledge CSV timestamps as UTC candle opens")
    if symbol not in ("BTCUSD","ETHUSD"):raise ValueError("unsupported instrument")
    if len(csv_text.encode())>MAX_CSV or len(graph_text.encode())>65536:raise ValueError("input too large")
    if graph_text.startswith("# btc-visual-v1 "):
        compiled=recover_graph(graph_text)
    else:compiled=compile_graph(Graph.model_validate_json(graph_text))
    g=Graph.model_validate(compiled["graph"])
    if g.execution_timeframe!=60:raise ValueError("execution timeframe must be 1m")
    bounds={"initial_equity":("1","1000000"),"maker_bps":("0","100"),"taker_bps":("0","100"),
        "tax_rate":("0","1"),"slippage_bps":("0","100"),"tick_size":("0.00000001","1000"),
        "lot_size":("0.00000001","1000"),"multiplier":("0.00000001","1000")}
    if set(settings)!=set(bounds):raise ValueError("invalid settings")
    for k,(lo,hi) in bounds.items():
        if not isinstance(settings[k],str) or not re.fullmatch(r"[0-9]{1,12}(?:\.[0-9]{1,8})?",settings[k]) or not D(lo)<=D(settings[k])<=D(hi):
            raise ValueError("invalid "+k)
    v={k:D(x) for k,x in settings.items()}
    i=Instrument("local-csv",symbol,AssetClass.CRYPTO_PERPETUAL,"USD","USD",v["tick_size"],v["lot_size"],v["multiplier"])
    tf=Timeframe(60);rows=[]
    r=csv.reader(io.StringIO(csv_text,newline=""))
    if next(r,None)!=["time","open","high","low","close","volume"]:raise ValueError("CSV header must be time,open,high,low,close,volume")
    for row in r:
        if len(rows)>=MAX_ROWS:raise ValueError("maximum 10080 candles (7 days)")
        if len(row)!=6 or not re.fullmatch(r"[0-9]{1,10}",row[0]) or any(not re.fullmatch(r"[0-9]{1,18}(?:\.[0-9]{1,18})?",x) for x in row[1:]):
            raise ValueError("invalid CSV row")
        epoch=int(row[0])
        if not 0<=epoch<=4102444800 or epoch%60:raise ValueError("invalid UTC minute timestamp")
        t=datetime.fromtimestamp(epoch,timezone.utc)
        if rows and t!=rows[-1].close_utc:raise ValueError("CSV contains gaps, duplicates or reversed timestamps")
        rows.append(Candle(i,tf,t,t+timedelta(minutes=1),*(D(x) for x in row[1:])))
    if len(rows)<2:raise ValueError("at least two candles required")
    start,end=rows[0].open_utc,rows[-1].close_utc
    if any(int(t.timestamp())%f for f in frames(g) for t in (start,end)):raise ValueError("CSV boundaries must align to all graph timeframes")
    h=sha256(csv_text.encode()).hexdigest();code=sha256(compiled["source"].encode()).hexdigest()
    ds=DatasetRef("local-csv",i,DataKind.OHLCV,tf,start,end,h,"user-provided CSV; label assumed",0,True)
    cfg=BacktestConfig(StrategyRef("local-visual","1",code,compiled["graph_sha256"]),i,(ds,),start,end,
        Timeframe(g.signal_timeframe),tf,v["initial_equity"],"USD",D(1),MarginMode.ISOLATED,
        CostModel(v["maker_bps"],v["taker_bps"],v["tax_rate"],v["slippage_bps"],False,False,False,"local-assumptions"),
        IntrabarPolicy.BOTH_PATHS,"Asia/Kolkata","crypto-24x7")
    count=0
    def stream():
        nonlocal count
        for b in rows:
            count+=1
            if count%128==0:progress(min(99,count*99//(len(rows)*2)))
            yield b
    result=run_backtest(cfg,lambda:GraphStrategy(g),stream,linear_contract=True,dataset_manifest_sha256=h)
    scenarios=[]
    for s in result.scenarios:
        wire=to_wire(s)
        scenarios.append({"path":s.path,"bars":s.bars,"metrics":summarize(wire),"monthly":wire["monthly"],
                          "final_equity":wire["final_equity"],"fees":wire["fees"],"taxes":wire["taxes"]})
    return {"source":"user CSV (unverified provenance)","research_only":True,"data_sha256":h,"graph_sha256":compiled["graph_sha256"],
            "result_sha256":result.result_sha256,"worst_path":result.worst_path,"scenarios":scenarios,
            "limitations":list(result.limitations)+["No warmup outside CSV; entry candle protection starts on next minute."]}
