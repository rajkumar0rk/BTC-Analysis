"""Continuous repository replay; compressed inputs and digest-only event summaries.

Uses the same trusted simulator and archive accounting as native longrun. No
arbitrary Python, network access in Python, or full-history candle/event lists.
"""
import csv,gzip,json,re
from collections import deque
from dataclasses import replace
from datetime import date,datetime,timedelta,timezone
from decimal import Decimal as D,localcontext
from hashlib import sha256
from pathlib import Path
from ..contracts import (Instrument,AssetClass,Timeframe,Candle,DatasetRef,DataKind,
                         StrategyRef,BacktestConfig,CostModel,MarginMode,IntrabarPolicy)
from ..visual import Graph,compile_graph,recover_graph
from ..serialization import to_wire
from ..backtest import run_backtest
from ..backtest.archive import Series,ScenarioArchive,MAX_PENDING
from .historical import frames,GraphStrategy,LongHistoricalRequest
from .leveraged_replay import decimal as risk_decimal,epoch as risk_epoch,csv_rows,make_profile
from ..margin import MarginProfile,FundingSettlement,RiskBar

DAY=86400
MAX_DAYS=1098
MAX_GZIP=4*1024*1024
MAX_TOTAL=64*1024*1024
HEADER=["time","open","high","low","close","volume"]
HASH=re.compile(r"[a-f0-9]{64}")
NUMBER=re.compile(r"[0-9]{1,18}(?:\.[0-9]{1,18})?")
def dt(t):return datetime.fromtimestamp(t,timezone.utc)
def epoch(text):
    t=datetime.fromisoformat(text)
    if t.utcoffset()!=timedelta(0) or t.microsecond or t.second:raise ValueError("invalid archive minute")
    return int(t.timestamp())
def utc_day(text):
    d=date.fromisoformat(text)
    if d.isoformat()!=text:raise ValueError("invalid UTC date")
    return int(datetime(d.year,d.month,d.day,tzinfo=timezone.utc).timestamp())
def plan_archive(manifest_text,symbol,from_date,to_date):
    return plan_archive_range(manifest_text,symbol,utc_day(from_date),utc_day(to_date)+DAY)

def plan_archive_range(manifest_text,symbol,start,end):
    if symbol not in ("BTCUSD","ETHUSD") or len(manifest_text.encode())>262144:raise ValueError("invalid archive input")
    if type(start) is not int or type(end) is not int or start%60 or end%60 or not 0<=start<end<=4102444800 or not 0<end-start<=MAX_DAYS*DAY:raise ValueError("select 1–1098 calendar days (inclusive UTC)")
    m=json.loads(manifest_text)
    if (m["symbol"],m["resolution"],m["timestamp_unit"])!=(symbol,"1m","unix_seconds_utc") or not isinstance(m["partitions"],list) or len(m["partitions"])>500:raise ValueError("invalid archive manifest")
    selected=[]
    for p in m["partitions"]:
        a,b=epoch(p["utc_start"]),epoch(p["utc_end_exclusive"])
        n=p["observed_candles"];h=p["sha256_gzip"]
        if (not re.fullmatch(r"[0-9]{4}-[0-9]{2}\.csv\.gz",p["file"]) or not HASH.fullmatch(h)
            or not 0<b-a<=31*DAY or type(n) is not int or not 0<=n<=(b-a)//60
            or p["expected_minutes"]!=(b-a)//60 or p["missing_minutes"]!=p["expected_minutes"]-n):
            raise ValueError("invalid archive partition")
        if a<end and b>start:selected.append({"start":a,"end":b,"rows":n,"sha256":h})
    selected.sort(key=lambda p:p["start"])
    if not selected or len(selected)>38 or selected[0]["start"]>start or selected[-1]["end"]<end:raise ValueError("selected dates outside published archive coverage")
    if any(a["end"]!=b["start"] for a,b in zip(selected,selected[1:])):raise ValueError("archive partitions overlap or have missing dates")
    if len({p["sha256"] for p in selected})!=len(selected):raise ValueError("duplicate archive digest")
    return {"start":start,"end":end,"parts":selected,"manifest_sha256":sha256(manifest_text.encode()).hexdigest()}

class Discard:
    def write(self,data):return len(data)
class DigestSeries(Series):
    def __init__(self,name,tail=0):
        self.name=name+".ndjson";self.file=Discard()
        self.digest=sha256();self.count=0;self.bytes=0;self.tail=deque(maxlen=tail)
        self.gain=D(0);self.loss=D(0);self.wins=0;self.losses=0;self.preliq=0
    def append(self,value):
        super().append(value)
        if self.name=="fills.ndjson" and value.reason=="modeled_preliquidation_stop":self.preliq+=1
    def ref(self):
        return {"rows":self.count,"bytes":self.bytes,"sha256":self.digest.hexdigest()}

class DigestArchive(ScenarioArchive):
    def __init__(self,path):self.path=path
    def __enter__(self):return self
    def __exit__(self,*args):return False
    def bind(self,sim):
        self.series={}
        for attr,name in (("orders","orders"),("fills","fills"),("evidence","execution_evidence"),("trades","closed_trades"),("curve","equity_curve")):
            s=DigestSeries(name,MAX_PENDING+1 if attr=="fills" else 0);self.series[name]=s;setattr(sim,attr,s)

class RiskDigestArchive(DigestArchive):
    supports_risk=True
    def bind(self,sim):
        super().bind(sim)
        for attr in ("funding_records","liquidations"):
            s=DigestSeries(attr);self.series[attr]=s;setattr(sim,attr,s)
    def finish(self,s,e,unreal):
        result=super().finish(s,e,unreal)
        summary={**result.summary,"funding_paid":s.funding,"liquidation_count":len(s.liquidations),"preliq_count":self.series["fills"].preliq}
        return replace(result,summary=summary,risk_stream_sha256=s.risk_digest.hexdigest())

def verify_files(plan,root):
    size=0
    for p in plan["parts"]:
        path=root/(p["sha256"]+".bin")
        n=path.stat().st_size;size+=n
        if n>MAX_GZIP or size>MAX_TOTAL or sha256(path.read_bytes()).hexdigest()!=p["sha256"]:raise ValueError("archive checksum or compressed size mismatch")
    return size

def mark_stream(plan,root,i,tf):
    expected=plan["start"]
    for p in plan["parts"]:
        seen=0;previous=p["start"]-60
        with gzip.open(root/(p["sha256"]+".bin"),"rt",encoding="utf-8",newline="") as f:
            reader=csv.reader(f)
            if next(reader,None)!=HEADER:raise ValueError("mark archive schema mismatch")
            for row in reader:
                seen+=1
                if seen>p["rows"] or len(row)!=6 or not re.fullmatch(r"[0-9]{1,10}",row[0]):raise ValueError("invalid mark row/count")
                t=int(row[0])
                if t%60 or not p["start"]<=t<p["end"] or t<=previous:raise ValueError("unordered mark row")
                previous=t
                if plan["start"]<=t<plan["end"]:
                    if t!=expected:raise ValueError("missing or duplicate mark candle at "+dt(expected).isoformat())
                    expected+=60
                    prices=[]
                    for v in row[1:5]:
                        if len(v)>48:raise ValueError("invalid mark decimal")
                        d=D(v)
                        if not d.is_finite() or not D("0.000000000000000001")<=d<=D("999999999999999999"):raise ValueError("invalid mark price")
                        prices.append(d)
                    yield Candle(i,tf,dt(t),dt(t+60),*prices,D(0))
            if seen!=p["rows"]:raise ValueError("mark row count mismatch")
    if expected!=plan["end"]:raise ValueError("incomplete mark archive")

def long_risk(risk,plan,mark_manifest,symbol,from_date,to_date,root,i,tf):
    keys={"leverage","margin_mode","initial_rate_floor","maintenance_rate","max_notional","liquidation_fee_bps","profile_start","profile_end","profile_source","preliq_points","scalp_enabled","scalp_start","scalp_end","funding_enabled","funding_interval_seconds","funding_anchor_epoch","funding_csv","acknowledge"}
    if not isinstance(risk,dict) or set(risk)-{"funding_provenance","tiers_json","initial_shock","maintenance_shock"}!=keys or risk["acknowledge"] is not True:raise ValueError("explicit risk assumptions required")
    if type(risk["funding_enabled"]) is not bool or type(risk["scalp_enabled"]) is not bool:raise ValueError("invalid risk switches")
    provenance=risk.get("funding_provenance","operator_supplied")
    if provenance not in ("operator_supplied","estimated_previous_hour_mark_open") or ("funding_provenance" in risk and not risk["funding_enabled"]):raise ValueError("invalid funding provenance")
    if risk["margin_mode"] not in ("isolated","cross","portfolio"):raise ValueError("unsupported margin mode")
    lev=risk_decimal(risk["leverage"],"1","100");mode=MarginMode(risk["margin_mode"])
    source=risk["profile_source"]
    if not isinstance(source,str) or not source.strip() or len(source)>150:raise ValueError("profile evidence/source required")
    start,end=plan["start"],plan["end"]
    if not isinstance(mark_manifest,str) or json.loads(mark_manifest).get("series")!="mark_1m":raise ValueError("native mark archive required")
    mp=plan_archive_range(mark_manifest,symbol,start,end)
    if verify_files(plan,root)+verify_files(mp,root)>MAX_TOTAL:raise ValueError("combined compressed archive exceeds 64 MiB")
    refs=[DatasetRef("repository-mark:"+mp["manifest_sha256"][:16],i,DataKind.MARK,tf,dt(start),dt(end),mp["manifest_sha256"],"published Delta native mark archive; timestamps assumed",0,True)]
    funding={};interval=0;anchor=0
    if risk["funding_enabled"]:
        interval=risk["funding_interval_seconds"];anchor=risk["funding_anchor_epoch"]
        if type(interval) is not int or not 60<=interval<=86400 or interval%60 or type(anchor) is not int or anchor%60:raise ValueError("invalid funding schedule")
        for row in csv_rows(risk["funding_csv"],["time","rate","reference_mark"]):
            when=risk_epoch(row[0]);t=int(when.timestamp())
            if not start<=t<end or (t-anchor)%interval or t in funding:raise ValueError("duplicate or unexpected funding settlement")
            funding[t]=FundingSettlement(when,risk_decimal(row[1],"-0.1","0.1"),risk_decimal(row[2],"0.000000000000000001","999999999999999999"),"estimated-funding-proxy" if provenance=="estimated_previous_hour_mark_open" else "user-funding-csv")
        first=start+(anchor-start)%interval
        required=max(0,(end-1-first)//interval+1)
        if len(funding)!=required:raise ValueError("funding settlements incomplete")
        refs.append(DatasetRef("local-funding",i,DataKind.FUNDING,tf,dt(start),dt(end),sha256(risk["funding_csv"].encode()).hexdigest(),"estimated prior hourly observation and mark-open proxy" if provenance=="estimated_previous_hour_mark_open" else "user-supplied settlement CSV; not independently attested",0,True))
    elif risk["funding_csv"]:raise ValueError("funding data supplied but disabled")
    scalp=risk["scalp_enabled"]
    profile=make_profile(risk,i,risk_epoch(risk["profile_start"]),risk_epoch(risk["profile_end"]),source,
        risk_decimal(risk["initial_rate_floor"],"0.00000001","1"),risk_decimal(risk["maintenance_rate"],"0.00000001","1"),
        risk_decimal(risk["max_notional"],"1","999999999999999999"),risk_decimal(risk["liquidation_fee_bps"],"0","9999"),interval,anchor,
        risk_decimal(risk["preliq_points"],"0","1000000"),1800 if scalp else 0,risk_epoch(risk["scalp_start"]) if scalp else None,risk_epoch(risk["scalp_end"]) if scalp else None)
    def factory():
        for bar in mark_stream(mp,root,i,tf):
            yield RiskBar(bar,funding.get(int(bar.open_utc.timestamp())))
    meta={"leverage":lev,"margin_mode":mode.value,"profile":profile,"funding_enabled":risk["funding_enabled"],"risk_dataset_sha256s":[d.manifest_sha256 for d in refs],"funding_provenance":provenance if risk["funding_enabled"] else "excluded"}
    return lev,mode,profile,tuple(refs),factory,meta

def yearly(monthly):
    with localcontext() as ctx:
        ctx.prec=50
        years={}
        for m in monthly:
            y=m.month[:4]
            if y not in years:years[y]=[m.opening_equity,m.closing_equity,D(0)]
            years[y][1]=m.closing_equity;years[y][2]+=m.pnl
        return [{"year":y,"pnl":p,"return_pct":p/a*100 if a>0 else None,"opening_equity":a,"closing_equity":b} for y,(a,b,p) in years.items()]

def replay_archive(manifest_text,from_date,to_date,graph_text,symbol,settings,assume_open,folder,progress=lambda p:True,risk=None,mark_manifest=None,window=None):
    if assume_open is not True:raise ValueError("acknowledge unverified candle-open timestamps")
    if len(graph_text.encode())>65536:raise ValueError("graph too large")
    plan=plan_archive(manifest_text,symbol,from_date,to_date) if window is None else plan_archive_range(manifest_text,symbol,*window)
    start,end=plan["start"],plan["end"];h=plan["manifest_sha256"]
    expected_keys={"initial_equity","maker_bps","taker_bps","tax_rate","slippage_bps","tick_size","lot_size","multiplier"}
    if set(settings)!=expected_keys:raise ValueError("invalid settings")
    r=LongHistoricalRequest.model_validate(dict(kind="historical_visual",strategy_id="0"*32,version=1,symbol=symbol,manifest_sha256=h,start=start,end=end,assume_open=True,acknowledge_reference=True,**settings))
    c=recover_graph(graph_text) if graph_text.startswith("# btc-visual-v1 ") else compile_graph(Graph.model_validate_json(graph_text))
    g=Graph.model_validate(c["graph"])
    if g.execution_timeframe!=60 or any(t%f for f in frames(g) for t in (start,end)):raise ValueError("range must align with all graph timeframes; 1m execution required")
    i=Instrument("delta_india",symbol,AssetClass.CRYPTO_PERPETUAL,"USD","USD",D(r.tick_size),D(r.lot_size),D(r.multiplier))
    tf=Timeframe(60);root=Path(folder)
    verify_files(plan,root)
    lev=D(1);mode=MarginMode.ISOLATED;profile=None;refs=();factory=None;meta=None
    if risk is not None:lev,mode,profile,refs,factory,meta=long_risk(risk,plan,mark_manifest,symbol,from_date,to_date,root,i,tf)
    elif mark_manifest is not None:raise ValueError("unexpected mark manifest")
    ds=DatasetRef("repository-history:"+h[:16],i,DataKind.OHLCV,tf,dt(start),dt(end),h,"published Delta India archive; timestamp label assumed",0,True)
    cfg=BacktestConfig(StrategyRef("repository-visual","1",sha256(c["source"].encode()).hexdigest(),c["graph_sha256"]),i,(ds,)+refs,dt(start),dt(end),Timeframe(g.signal_timeframe),tf,D(r.initial_equity),"USD",lev,mode,CostModel(D(r.maker_bps),D(r.taker_bps),D(r.tax_rate),D(r.slippage_bps),bool(meta and meta["funding_enabled"]),False,profile is not None,"local-assumptions"),IntrabarPolicy.BOTH_PATHS,"Asia/Kolkata","crypto-24x7")
    count=0;total=2*((end-start)//60)
    def stream():
        nonlocal count
        expected=start
        for p in plan["parts"]:
            seen=0;previous=p["start"]-60
            with gzip.open(root/(p["sha256"]+".bin"),"rt",encoding="utf-8",newline="") as f:
                reader=csv.reader(f)
                if next(reader,None)!=HEADER:raise ValueError("archive schema mismatch")
                for row in reader:
                    seen+=1
                    if seen>p["rows"] or len(row)!=6 or not re.fullmatch(r"[0-9]{1,10}",row[0]) or any(not NUMBER.fullmatch(x) for x in row[1:]):raise ValueError("invalid archive row or count")
                    t=int(row[0])
                    if t%60 or not p["start"]<=t<p["end"] or t<=previous:raise ValueError("unordered archive row")
                    previous=t
                    if start<=t<end:
                        if t!=expected:raise ValueError("missing or duplicate candle at "+dt(expected).isoformat())
                        expected+=60;count+=1
                        if count%4096==0 and not progress(min(99,count*99//total)):raise ValueError("cancelled")
                        yield Candle(i,tf,dt(t),dt(t+60),*(D(x) for x in row[1:]))
                if seen!=p["rows"]:raise ValueError("archive row count mismatch")
        if expected!=end:raise ValueError("incomplete archive range")
    def strategy():
        obj=GraphStrategy(g);obj.exposure*=lev;return obj
    result=run_backtest(cfg,strategy,stream,linear_contract=True,dataset_manifest_sha256=h,archive_factory=RiskDigestArchive if profile is not None else DigestArchive,margin_profile=profile,risk_factory=factory,risk_manifest_sha256s=tuple(d.manifest_sha256 for d in refs))
    scenarios=[]
    for s in result.scenarios:
        q=s.summary
        metrics={**q,"account_net":q["net_pnl"]}
        with localcontext() as ctx:
            ctx.prec=50
            metrics["account_return_pct"]=q["net_pnl"]/q["initial_equity"]*100
        scenarios.append(dict(path=s.path,bars=s.bars,metrics=metrics,monthly=s.monthly,yearly=yearly(s.monthly),final_equity=s.final_equity,fees=q["fees"],taxes=q["taxes"],observed_candle_sha256=s.observed_candle_sha256,event_digests=s.files,risk_stream_sha256=s.risk_stream_sha256,funding_paid=q.get("funding_paid",D(0)),liquidation_count=q.get("liquidation_count",0),preliq_count=q.get("preliq_count",0)))
    return to_wire(dict(engine_version=result.engine_version,source="repository leveraged long replay" if profile is not None else "repository long replay",risk=meta,research_only=True,data_sha256=h,graph_sha256=c["graph_sha256"],result_sha256=result.result_sha256,worst_path=result.worst_path,scenarios=scenarios,limitations=list(result.limitations)+["Manifest SHA-256 identifies the published snapshot; observed candle and event digests are separate.","Monthly and yearly performance use Asia/Kolkata accounting; date selection is UTC.","No external warmup; entry candle protection starts on next minute.","Summary only; event records are hashed and discarded. Order-ID memory and event quotas remain bounded by engine limits."]))
