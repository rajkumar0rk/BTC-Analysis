"""Build-time public archive extension; never invent or fill source candles."""
import csv,gzip,hashlib,io,json,re
from datetime import datetime,timedelta,timezone
from decimal import Decimal
from pathlib import Path

UTC=timezone.utc
HEADER=["time","open","high","low","close","volume"]
def digest(raw):return hashlib.sha256(raw).hexdigest()
def dt(t):return datetime.fromtimestamp(t,UTC)
def stamp(t):return int(datetime.fromisoformat(t).timestamp())
def month_bounds(month):
    y,m=map(int,month.split("-"))
    a=datetime(y,m,1,tzinfo=UTC);b=datetime(y+(m==12),m%12+1,1,tzinfo=UTC)
    return int(a.timestamp()),int(b.timestamp())
def source_rows(path,expected_hash=None,expected_count=None,step=60,signed=False,blank_volume=False):
    raw=path.read_bytes()
    if len(raw)>4*1024*1024 or (expected_hash and digest(raw)!=expected_hash):raise ValueError("source checksum/size: "+str(path))
    with gzip.GzipFile(fileobj=io.BytesIO(raw)) as gz:
        decoded=gz.read(12*1024*1024+1)
    if len(decoded)>12*1024*1024:raise ValueError("decompressed archive too large")
    reader=csv.reader(io.StringIO(decoded.decode("utf-8")))
    header=next(reader,None)
    if header!=HEADER and not (blank_volume and header==HEADER[:5]):raise ValueError("unexpected archive schema: "+str(path))
    rows=[];previous=-1
    for row in reader:
        if header==HEADER[:5] and len(row)==5:row.append("")
        if len(row)!=6 or not re.fullmatch(r"[0-9]{1,10}",row[0]):raise ValueError("invalid timestamp")
        t=int(row[0])
        if t<=previous or t%step:raise ValueError("unordered or unaligned archive: "+str(path))
        previous=t
        vals=[Decimal(v) for v in row[1:5]]
        if not all(v.is_finite() for v in vals):raise ValueError("nonfinite OHLC")
        o,h,l,c=vals
        if l>min(o,c) or h<max(o,c) or (not signed and l<=0):raise ValueError("invalid OHLC")
        if row[5] or not blank_volume:
            v=Decimal(row[5])
            if not v.is_finite() or v<0:raise ValueError("invalid volume")
        rows.append(row)
    if expected_count is not None and len(rows)!=expected_count:raise ValueError("row count mismatch: "+str(path))
    return raw,rows
def entry(name,a,b,n,h,step=60):
    return {"file":name,"utc_start":dt(a).isoformat(),"utc_end_exclusive":dt(b).isoformat(),
            "expected_minutes":(b-a)//step,"observed_candles":n,"missing_minutes":(b-a)//step-n,"sha256_gzip":h}
def stage_retained_trade(root,history):
    source=root/"data/delta_india/BTCUSD/2024_verified_archive"
    original=json.loads((source/"manifest.json").read_text())
    if original["synthetic_rows"]!=0 or original["original_trade_rows_preserved"] is not True:raise ValueError("unexpected retained archive provenance")
    out=history/"BTCUSD";current=json.loads((out/"manifest.json").read_text())
    prior=[];pending={};last=-1
    # Source partitions are IST months. Normalize real observed rows to UTC months.
    for meta in sorted((m for m in original["months"] if m["series"]=="trade_1m"),key=lambda m:m["month"]):
        _,rows=source_rows(source/"trade_1m"/(meta["month"]+".csv.gz"),meta["sha256"],meta["observed"])
        a,b=month_bounds(meta["month"])
        for row in rows:
            t=int(row[0])
            if not a-19800<=t<b-19800 or t<=last:raise ValueError("invalid retained IST partition")
            last=t
            if dt(t).year==2024:pending.setdefault(dt(t).strftime("%Y-%m"),[]).append(row)
        for key in sorted(k for k in pending if k<meta["month"]):
            prior.append(publish_trade(out,key,pending.pop(key)))
    for key,rows in sorted(pending.items()):prior.append(publish_trade(out,key,rows))
    if len(prior)!=12:raise ValueError("retained archive missing a month")
    current["partitions"]=prior+current["partitions"]
    current["retained_2024_source"]="cda60e8e4aa0808469db5d07304dbaed52e190bb; IST partitions normalized to UTC; no synthetic rows"
    current["note"]+=" 2024 UTC archive has gaps including any uncovered year-end minutes."
    (out/"manifest.json").write_text(json.dumps(current,sort_keys=True,separators=(",",":"))+"\n")
def publish_trade(out,key,rows,step=60):
    a,b=month_bounds(key)
    buf=io.StringIO(newline="");w=csv.writer(buf,lineterminator="\n");w.writerow(HEADER);w.writerows(rows)
    raw=gzip.compress(buf.getvalue().encode(),mtime=0);h=digest(raw);(out/(h+".bin")).write_bytes(raw)
    return entry(key+".csv.gz",a,b,len(rows),h,step)
def retained_risk(root,out,kind,step):
    source=root/"data/delta_india/BTCUSD/2024_verified_archive"
    original=json.loads((source/"manifest.json").read_text())
    if original["synthetic_rows"]!=0:raise ValueError("unexpected retained risk provenance")
    metas=sorted((m for m in original["months"] if m["series"]==kind),key=lambda m:m["month"])
    if [m["month"] for m in metas]!=[f"2024-{i:02d}" for i in range(1,13)]:raise ValueError("retained risk archive missing months")
    pending={};prior=[];last=-1
    for m in metas:
        _,rows=source_rows(source/kind/(m["month"]+".csv.gz"),m["sha256"],m["observed"],step=step,signed=kind=="funding_1h",blank_volume=True)
        a,b=month_bounds(m["month"])
        # Match the retained acquisition script exactly: floor both IST
        # endpoints for hourly funding; January includes one preceding hour.
        lo=(a-19800)//step*step
        hi=(b-19800)//step*step
        if kind=="funding_1h" and m["month"]=="2024-01":lo-=step
        if m["expected"]!=(hi-lo)//step or m["missing"]!=m["expected"]-m["observed"]:
            raise ValueError("retained risk metadata mismatch: "+kind+" "+m["month"])
        for row in rows:
            t=int(row[0])
            if not lo<=t<hi or t<=last:raise ValueError("invalid or overlapping retained risk partition: "+kind+" "+m["month"]+" timestamp="+str(t))
            last=t
            if dt(t).year==2024:pending.setdefault(dt(t).strftime("%Y-%m"),[]).append(row)
        for key in sorted(k for k in pending if k<m["month"]):
            prior.append(publish_trade(out,key,pending.pop(key),step))
    for key,rows in sorted(pending.items()):prior.append(publish_trade(out,key,rows,step))
    if len(prior)!=12:raise ValueError("retained risk UTC month missing")
    return prior

def stage_risk(root,history,symbol):
    source=root/"data/delta_india"/symbol/"institutional"
    m=json.loads((source/"history_manifest.json").read_text())
    if m["symbol"]!=symbol:raise ValueError("risk manifest symbol mismatch")
    for kind,step in (("mark_1m",60),("funding_1h",3600)):
        series=m["series"][kind];out=history/symbol/kind;out.mkdir()
        entries=retained_risk(root,out,kind,step) if symbol=="BTCUSD" else []
        for p in series["partitions"]:
            name=Path(p["partition"]).name
            if not re.fullmatch(r"[0-9]{4}-[0-9]{2}\.csv\.gz",name):raise ValueError("bad risk partition name")
            raw,rows=source_rows(source/"history"/kind/name,expected_count=p["rows"],step=step,signed=kind=="funding_1h",blank_volume=True)
            if not rows or len(raw)!=p["compressed_bytes"] or int(rows[0][0])!=stamp(p["first_utc"]) or int(rows[-1][0])!=stamp(p["last_utc"]):raise ValueError("risk partition metadata mismatch")
            a,b=month_bounds(name[:7]);a=max(a,stamp(m["requested_start_utc"]));b=min(b,stamp(m["requested_end_exclusive_utc"]))
            if not a<=int(rows[0][0])<=int(rows[-1][0])<b:raise ValueError("risk outside partition")
            h=digest(raw);(out/(h+".bin")).write_bytes(raw);entries.append(entry(name,a,b,len(rows),h,step))
        # All staged UTC partitions retain the true observed intervals and counts.
        obj={"symbol":symbol,"resolution":"1m" if step==60 else "1h","timestamp_unit":"unix_seconds_utc","timestamp_label":"as_returned_by_API","requested_through_utc":dt(stamp(m["requested_end_exclusive_utc"])-1).date().isoformat(),"partitions":entries,"series":kind,"note":"Funding observations, not settlements." if step==3600 else "Native mark candles, not executable prices."}
        if symbol=="BTCUSD":obj["retained_2024_source"]="cda60e8e4aa0808469db5d07304dbaed52e190bb; original source hashes checked; UTC month normalization; no synthetic rows"
        (out/"manifest.json").write_text(json.dumps(obj,sort_keys=True,separators=(",",":"))+"\n")
def stage_extended_history(root,history):
    stage_retained_trade(root,history)
    for symbol in ("BTCUSD","ETHUSD"):stage_risk(root,history,symbol)
    print("Staged normalized retained BTC 2024 trade/mark/funding observations and checked 2025–2026 risk series.")
