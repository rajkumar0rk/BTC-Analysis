"""Local reference replay for visual graphs and bounded SDK Python. No source eval/exec."""
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

MAX_ROWS=44640
MAX_CSV=16*1024*1024

def replay(csv_text,graph_text,symbol,settings,assume_open,progress=lambda p:True,cache=None,risk=None,details=False):
    if assume_open is not True:raise ValueError("acknowledge CSV timestamps as UTC candle opens")
    if symbol not in ("BTCUSD","ETHUSD"):raise ValueError("unsupported instrument")
    if len(csv_text.encode())>MAX_CSV or len(graph_text.encode())>65536:raise ValueError("input too large")
    custom=not graph_text.startswith("# btc-visual-v1 ") and not graph_text.lstrip().startswith("{")
    if custom:
        from .python_strategy import prepare_python
        program,signal_seconds,frame_seconds=prepare_python(graph_text)
        compiled={"source":graph_text,"graph_sha256":program.hash}
        g=None
    else:
        if graph_text.startswith("# btc-visual-v1 "):compiled=recover_graph(graph_text)
        else:compiled=compile_graph(Graph.model_validate_json(graph_text))
        g=Graph.model_validate(compiled["graph"])
        if g.execution_timeframe!=60:raise ValueError("execution timeframe must be 1m")
        signal_seconds=g.signal_timeframe;frame_seconds=frames(g)
    bounds={"initial_equity":("1","1000000"),"maker_bps":("0","100"),"taker_bps":("0","100"),
        "tax_rate":("0","1"),"slippage_bps":("0","100"),"tick_size":("0.00000001","1000"),
        "lot_size":("0.00000001","1000"),"multiplier":("0.00000001","1000")}
    if set(settings)!=set(bounds):raise ValueError("invalid settings")
    for k,(lo,hi) in bounds.items():
        if not isinstance(settings[k],str) or not re.fullmatch(r"[0-9]{1,12}(?:\.[0-9]{1,8})?",settings[k]) or not D(lo)<=D(settings[k])<=D(hi):
            raise ValueError("invalid "+k)
    v={k:D(x) for k,x in settings.items()}
    i=Instrument("local-csv",symbol,AssetClass.CRYPTO_PERPETUAL,"USD","USD",v["tick_size"],v["lot_size"],v["multiplier"])
    tf=Timeframe(60);h=sha256(csv_text.encode()).hexdigest()
    rows=cache.select((h,i)) if cache is not None else None
    if rows is None:
        rows=[]
        r=csv.reader(io.StringIO(csv_text,newline=""))
        if next(r,None)!=["time","open","high","low","close","volume"]:raise ValueError("CSV header must be time,open,high,low,close,volume")
        for row in r:
            if len(rows)>=MAX_ROWS:raise ValueError("maximum 44640 candles (31 days)")
            if len(row)!=6 or not re.fullmatch(r"[0-9]{1,10}",row[0]) or any(not re.fullmatch(r"[0-9]{1,18}(?:\.[0-9]{1,18})?",x) for x in row[1:]):
                raise ValueError("invalid CSV row")
            epoch=int(row[0])
            if not 0<=epoch<=4102444800 or epoch%60:raise ValueError("invalid UTC minute timestamp")
            t=datetime.fromtimestamp(epoch,timezone.utc)
            if rows and t!=rows[-1].close_utc:raise ValueError("CSV contains gaps, duplicates or reversed timestamps")
            rows.append(Candle(i,tf,t,t+timedelta(minutes=1),*(D(x) for x in row[1:])))
        if len(rows)<2:raise ValueError("at least two candles required")
        rows=tuple(rows)
        if cache is not None:cache.rows=rows
    start,end=rows[0].open_utc,rows[-1].close_utc
    if any(int(t.timestamp())%f for f in frame_seconds for t in (start,end)):raise ValueError("CSV boundaries must align to all graph timeframes")
    code=sha256(compiled["source"].encode()).hexdigest()
    ds=DatasetRef("local-csv",i,DataKind.OHLCV,tf,start,end,h,"user-provided CSV; label assumed",0,True)
    leverage=D(1);mode=MarginMode.ISOLATED;profile=None;risk_refs=();risk_rows=();risk_meta=None
    if risk is not None:
        from .leveraged_replay import prepare_risk
        leverage,mode,profile,risk_refs,risk_rows,risk_meta=prepare_risk(risk,rows,i,tf)
    cfg=BacktestConfig(StrategyRef("local-visual","1",code,compiled["graph_sha256"]),i,(ds,)+risk_refs,start,end,
        Timeframe(signal_seconds),tf,v["initial_equity"],"USD",leverage,mode,
        CostModel(v["maker_bps"],v["taker_bps"],v["tax_rate"],v["slippage_bps"],bool(risk_meta and risk_meta["funding_enabled"]),False,profile is not None,"local-assumptions"),
        IntrabarPolicy.BOTH_PATHS,"Asia/Kolkata","crypto-24x7")
    if type(details) is not bool:raise ValueError("invalid details switch")
    indicator_samples=[]
    count=0
    def stream():
        nonlocal count
        for b in rows:
            count+=1
            if count%128==0:progress(min(99,count*99//(len(rows)*2)))
            yield b
    def strategy():
        if custom:obj=program.make(leverage)
        else:
            obj=GraphStrategy(g)
            # Exposure is percentage of account equity allocated to initial margin.
            obj.exposure*=leverage
        if details:
            runtime=obj if custom else obj.formula_runtime
            series=[]
            indicator_samples.append(series)
            if runtime is not None and runtime.custom:
                records={}
                for name,(frame,method,bars,history) in runtime.custom.items():
                    total=len(rows)*60//frame.seconds
                    record={"name":name,"timeframe":frame.seconds,"total":0,"points":[]}
                    series.append(record)
                    records[name]=(record,max(1,(total+598)//599))
                original=obj.on_completed_candle
                def observe(candle):
                    original(candle)
                    for name,(frame,method,bars,history) in runtime.custom.items():
                        if candle.timeframe!=frame:continue
                        record,stride=records[name]
                        record["total"]+=1
                        if (record["total"]-1)%stride==0 or candle.close_utc==end:
                            record["points"].append({"event_utc":to_wire(candle.close_utc),
                                "value":to_wire(history[-1]) if history else None,
                                "close":to_wire(candle.close)})
                obj.on_completed_candle=observe
        return obj
    result=run_backtest(cfg,strategy,stream,linear_contract=True,dataset_manifest_sha256=h,
        indicator_book_factory=cache.book if cache is not None else None,margin_profile=profile,
        risk_factory=(lambda:iter(risk_rows)) if profile is not None else None,
        risk_manifest_sha256s=tuple(d.manifest_sha256 for d in risk_refs))
    scenarios=[]
    for scenario_index,s in enumerate(result.scenarios):
        wire=to_wire(s)
        scenarios.append({"path":s.path,"bars":s.bars,"metrics":summarize(wire),"monthly":wire["monthly"],
                          "final_equity":wire["final_equity"],"fees":wire["fees"],"taxes":wire["taxes"],
                          "funding_paid":wire["funding_paid"],"liquidation_count":len(s.liquidations),
                          "preliq_count":sum(f.reason=="modeled_preliquidation_stop" for f in s.fills),"partial_liquidation_count":sum(f.reason=="modeled_partial_liquidation" for f in s.fills),"full_liquidation_count":sum(f.reason=="modeled_liquidation" for f in s.fills),"remaining_quantity":wire["open_quantity"]})
        if details:
            # Presentation data only: the canonical simulator result hash is unchanged.
            curve=wire["equity_curve"];stride=max(1,(len(curve)+599)//600)
            sampled=curve[::stride]
            if sampled[-1]!=curve[-1]:sampled.append(curve[-1])
            trades=wire["closed_trades"][-500:]
            ids={f["fill_id"] for t in trades for f in t["entry_fills"]+t["exit_fills"]}
            evidence=[e for e in wire["execution_evidence"] if e["fill_id"] in ids]
            scenarios[-1]["details"]={"equity":[{"event_utc":x["event_utc"],"equity":x["equity"]} for x in sampled],"equity_total":len(curve),"closed_trade_total":len(wire["closed_trades"]),"trades":trades,"evidence":evidence}
            if indicator_samples[scenario_index]:scenarios[-1]["details"]["custom_indicators"]=indicator_samples[scenario_index]
            audit=[{"event_utc":x["event_utc"],"detail":x["detail"]} for x in wire["orders"] if x["status"]=="strategy_audit"]
            if audit:
                scenarios[-1]["details"]["strategy_audit"]=audit[:500]
                scenarios[-1]["details"]["strategy_audit_total"]=len(audit)
    return {"engine_version":result.engine_version,"source":"user CSV (unverified provenance)","research_only":True,"data_sha256":h,"graph_sha256":compiled["graph_sha256"],
            "result_sha256":result.result_sha256,"worst_path":result.worst_path,"scenarios":scenarios,"risk":risk_meta,
            "limitations":list(result.limitations)+(["Restricted SDK Python interpreted locally; unsupported syntax or calls fail. No arbitrary Python runtime or external warmup."] if custom else ["No warmup outside CSV; fixed-point protection active on entry minute." if g.advanced is not None and g.advanced.exit_mode=="points" else "No warmup outside CSV; entry candle percentage protection starts on next minute."])}
