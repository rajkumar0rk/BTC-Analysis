"""Explicit user-supplied mark/funding adapter for single-position research."""
import csv,io,re,json
from datetime import datetime,timezone,timedelta
from decimal import Decimal as D
from hashlib import sha256
from ..contracts import Candle,DatasetRef,DataKind,MarginMode
from ..margin import MarginProfile,MarginTier,TieredMarginProfile,FundingSettlement,RiskBar
from ..serialization import fingerprint,to_wire

MAX_BYTES=16*1024*1024
def epoch(v):
    if not isinstance(v,str) or not re.fullmatch(r"[0-9]{1,10}",v) or int(v)%60 or int(v)>4102444800:raise ValueError("invalid UTC epoch minute")
    return datetime.fromtimestamp(int(v),timezone.utc)
def decimal(v,lo,hi):
    if not isinstance(v,str) or not re.fullmatch(r"-?[0-9]{1,18}(?:\.[0-9]{1,18})?",v) or not D(lo)<=D(v)<=D(hi):raise ValueError("invalid decimal risk input")
    return D(v)
def csv_rows(text,header):
    if not isinstance(text,str) or len(text.encode())>MAX_BYTES:raise ValueError("risk CSV too large")
    r=csv.reader(io.StringIO(text,newline=""))
    if next(r,None)!=header:raise ValueError("invalid risk CSV header: "+",".join(header))
    for row in r:
        if len(row)!=len(header):raise ValueError("invalid risk CSV row")
        yield row
def parse_tiers(text):
    if not isinstance(text,str) or len(text.encode())>16384:raise ValueError("invalid margin tiers JSON size")
    raw=json.loads(text)
    if not isinstance(raw,list) or not 1<=len(raw)<=32:raise ValueError("select 1–32 explicit margin tiers")
    out=[]
    for item in raw:
        if not isinstance(item,dict) or set(item)!={"upper_notional","initial_rate_floor","maintenance_rate"}:raise ValueError("invalid margin tier fields")
        out.append(MarginTier(decimal(item["upper_notional"],"1","999999999999999999"),
                              decimal(item["initial_rate_floor"],"0.00000001","1"),
                              decimal(item["maintenance_rate"],"0.00000001","1")))
    return tuple(out)
def make_profile(risk,*args):
    if "tiers_json" in risk:
        return TieredMarginProfile("user-whole-notional-tiers-v1",*args,tiers=parse_tiers(risk["tiers_json"]))
    return MarginProfile("user-fixed-tier-v1",*args)
def prepare_risk(risk,rows,i,tf):
    keys={"leverage","margin_mode","initial_rate_floor","maintenance_rate","max_notional","liquidation_fee_bps",
          "profile_start","profile_end","profile_source","preliq_points","scalp_enabled","scalp_start","scalp_end",
          "mark_csv","funding_enabled","funding_interval_seconds","funding_anchor_epoch","funding_csv","acknowledge"}
    if not isinstance(risk,dict) or set(risk)-{"funding_provenance","tiers_json"}!=keys or risk["acknowledge"] is not True:raise ValueError("explicit risk assumptions required")
    if type(risk["funding_enabled"]) is not bool or type(risk["scalp_enabled"]) is not bool:raise ValueError("invalid switches")
    provenance=risk.get("funding_provenance","operator_supplied")
    if provenance not in ("operator_supplied","estimated_previous_hour_mark_open") or ("funding_provenance" in risk and not risk["funding_enabled"]):raise ValueError("invalid funding provenance")
    leverage=decimal(risk["leverage"],"1","100")
    if risk["margin_mode"] not in ("isolated","cross"):raise ValueError("unsupported margin mode")
    mode=MarginMode(risk["margin_mode"])
    source=risk["profile_source"]
    if not isinstance(source,str) or not source.strip() or len(source)>150:raise ValueError("profile evidence/source required")
    start,end=rows[0].open_utc,rows[-1].close_utc
    marks=[]
    for idx,row in enumerate(csv_rows(risk["mark_csv"],["time","open","high","low","close"])):
        if idx>=len(rows) or epoch(row[0])!=rows[idx].open_utc:raise ValueError("mark data must align one-to-one with execution")
        t=rows[idx].open_utc
        marks.append(Candle(i,tf,t,t+timedelta(minutes=1),*(decimal(x,"0.000000000000000001","999999999999999999") for x in row[1:]),D(0)))
    if len(marks)!=len(rows):raise ValueError("missing mark candles")
    interval=0;anchor=0;funding={}
    if risk["funding_enabled"]:
        interval=risk["funding_interval_seconds"];anchor=risk["funding_anchor_epoch"]
        if type(interval) is not int or not 60<=interval<=86400 or interval%60 or type(anchor) is not int or anchor%60:raise ValueError("invalid funding schedule")
        for row in csv_rows(risk["funding_csv"],["time","rate","reference_mark"]):
            t=epoch(row[0])
            if t in funding or not start<=t<end or len(funding)>=len(rows):raise ValueError("duplicate/out-of-range funding")
            funding[t]=FundingSettlement(t,decimal(row[1],"-0.1","0.1"),decimal(row[2],"0.000000000000000001","999999999999999999"),"estimated-funding-proxy" if provenance=="estimated_previous_hour_mark_open" else "user-funding-csv")
        required={b.open_utc for b in rows if (int(b.open_utc.timestamp())-anchor)%interval==0}
        if set(funding)!=required:raise ValueError("funding settlements incomplete or unexpected")
    elif risk["funding_csv"]:raise ValueError("funding data supplied but disabled")
    scalp=risk["scalp_enabled"]
    profile=make_profile(risk,i,epoch(risk["profile_start"]),epoch(risk["profile_end"]),source,
        decimal(risk["initial_rate_floor"],"0.00000001","1"),decimal(risk["maintenance_rate"],"0.00000001","1"),
        decimal(risk["max_notional"],"1","999999999999999999"),decimal(risk["liquidation_fee_bps"],"0","9999"),
        interval,anchor,decimal(risk["preliq_points"],"0","1000000"),1800 if scalp else 0,
        epoch(risk["scalp_start"]) if scalp else None,epoch(risk["scalp_end"]) if scalp else None)
    refs=[DatasetRef("local-mark",i,DataKind.MARK,tf,start,end,sha256(risk["mark_csv"].encode()).hexdigest(),"user-supplied mark CSV",0,True)]
    if risk["funding_enabled"]:
        refs.append(DatasetRef("local-funding",i,DataKind.FUNDING,tf,start,end,sha256(risk["funding_csv"].encode()).hexdigest(),"estimated prior hourly observation and mark-open proxy" if provenance=="estimated_previous_hour_mark_open" else "user-supplied funding CSV; not independently attested",0,True))
    stream=tuple(RiskBar(m,funding.get(m.open_utc)) for m in marks)
    metadata={"leverage":to_wire(leverage),"margin_mode":mode.value,"profile":to_wire(profile),
              "risk_dataset_sha256s":[d.manifest_sha256 for d in refs],"funding_enabled":risk["funding_enabled"]}
    metadata["funding_provenance"]=provenance if risk["funding_enabled"] else "excluded"
    return leverage,mode,profile,tuple(refs),stream,metadata
