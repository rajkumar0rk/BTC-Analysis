"""Publish sparse observed Delta BTCUSD quote samples, not reconstructed ticks."""
import hashlib,json,re
from datetime import datetime,timezone
from decimal import Decimal,ROUND_CEILING,localcontext
from pathlib import Path

MAX_FILE=8*1024*1024
MAX_SAMPLES=20000
def stamp(value):
    d=datetime.fromisoformat(value.replace("Z","+00:00"))
    if d.utcoffset()!=timezone.utc.utcoffset(d):raise ValueError("non-UTC receipt")
    return d
def positive(value):
    if isinstance(value,bool):raise ValueError("invalid price")
    d=Decimal(str(value))
    if not d.is_finite() or not 0<d<Decimal("1e10"):raise ValueError("invalid price")
    return d
def quote(row,day):
    if row.get("schema_version")!=1 or row.get("snapshot_type")!="forward_observed_rest_sample":raise ValueError("invalid snapshot")
    q=row["books"]["delta_india_perp"]
    if q["source_url"]!="https://api.india.delta.exchange/v2/l2orderbook/BTCUSD?depth=20":raise ValueError("wrong source")
    received,requested,captured=map(stamp,(q["received_at_utc"],q["requested_at_utc"],row["captured_at_utc"]))
    if captured.date().isoformat()!=day or not captured<=requested<=received or (received-requested).total_seconds()>5:raise ValueError("invalid/slow receipt")
    latency=q["http_latency_ms"]
    if type(latency) is not int or not 0<=latency<=5000:raise ValueError("invalid latency")
    bid,ask=positive(q["best_bid"]),positive(q["best_ask"])
    if not bid<ask or bid!=max(positive(x[0]) for x in q["bids"]) or ask!=min(positive(x[0]) for x in q["asks"]):raise ValueError("crossed or inconsistent book")
    with localcontext() as ctx:
        ctx.prec=40
        # Half the full relative spread, conservatively rounded upwards.
        half=((ask-bid)*Decimal(10000)/(bid+ask)).quantize(Decimal("0.00000001"),rounding=ROUND_CEILING)
    return {"received_utc":received.isoformat(timespec="milliseconds"),"bid":str(bid),"ask":str(ask),"half_spread_bps":str(half)}
def collect(source):
    samples={};files=[];rejected=0;conflicts=set()
    for path in sorted(source.glob("????-??-??.jsonl")):
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}\.jsonl",path.name):raise ValueError("bad source filename")
        if path.stat().st_size>MAX_FILE:raise ValueError("source file too large")
        raw=path.read_bytes()
        files.append({"file":path.name,"sha256":hashlib.sha256(raw).hexdigest()})
        for line in raw.splitlines():
            try:
                r=quote(json.loads(line,parse_float=Decimal),path.stem)
                key=r["received_utc"]
                if key in samples and samples[key]!=r:conflicts.add(key)
                else:samples[key]=r
            except (ValueError,KeyError,TypeError,IndexError,ArithmeticError,AttributeError):
                rejected+=1
    for key in conflicts:samples.pop(key,None)
    if len(samples)>MAX_SAMPLES:raise ValueError("sample count exceeds bound")
    return {"schema":1,"symbol":"BTCUSD","source":"Delta India public REST L2 observations; receipt time, not verified exchange-event time","rejected":rejected,"conflicting_receipts":len(conflicts),"files":files,"samples":[samples[k] for k in sorted(samples)]}
def stage(root,history):
    obj=collect(root/"analysis/forward_microstructure/snapshots")
    raw=(json.dumps(obj,sort_keys=True,separators=(",",":"))+"\n").encode()
    if len(raw)>4*1024*1024:raise ValueError("spread report too large")
    out=history/"BTCUSD"/"spread-calibration.json"
    out.write_bytes(raw)
    print("Sparse spread observations",len(obj["samples"]),"rejected",obj["rejected"],"conflicting receipts",obj["conflicting_receipts"])
