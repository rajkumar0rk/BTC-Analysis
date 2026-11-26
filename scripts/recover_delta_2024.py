"""Acquire genuine Delta India 2024 UTC data into a separate candidate archive.
Preserve retained BTC source rows. Missing observations remain gaps.
Funding observations are not settlement events. No exchange authentication.
"""
import argparse,csv,gzip,hashlib,io,json,re,time
from decimal import Decimal
from pathlib import Path
from urllib.request import Request,urlopen,HTTPRedirectHandler,build_opener
from urllib.parse import urlencode
from urllib.error import HTTPError,URLError
from stage_repository_history import month_bounds,source_rows,HEADER,dt

ROOT=Path(__file__).resolve().parents[1]
BASE="https://api.india.delta.exchange/v2/history/candles"
SERIES={"trade_1m":("", "1m",60),"mark_1m":("MARK:","1m",60),"funding_1h":("FUNDING:","1h",3600)}
class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None
def fetch(symbol,resolution,start,end):
    url=BASE+"?"+urlencode(dict(symbol=symbol,resolution=resolution,start=start,end=end-1))
    for attempt in range(3):
        try:
            with build_opener(NoRedirect()).open(Request(url,headers={"Accept":"application/json","User-Agent":"BTC-Analysis-2024-recovery/1.0"}),timeout=20) as res:
                raw=res.read(4*1024*1024+1)
            if len(raw)>4*1024*1024:raise ValueError("response size")
            body=json.loads(raw,parse_float=Decimal)
            if body.get("success") is not True or not isinstance(body.get("result"),list) or len(body["result"])>2000:raise ValueError("invalid API response")
            return body["result"]
        except HTTPError as e:
            if e.code not in (408,429,500,502,503,504):raise
            if attempt==2:raise
        except (URLError,TimeoutError,OSError):
            if attempt==2:raise
        time.sleep(2**attempt*2)
    raise RuntimeError("unreachable")

def validate(raw,kind,step):
    if not isinstance(raw,dict) or type(raw.get("time")) is not int or raw["time"]%step:raise ValueError("timestamp")
    values=[]
    for k in HEADER[1:]:
        value=raw.get(k)
        if k=="volume" and value is None and kind!="trade_1m":values.append("");continue
        if not isinstance(value,(str,int,Decimal)) or isinstance(value,bool):raise ValueError("invalid decimal")
        d=Decimal(str(value))
        if not d.is_finite() or abs(d)>Decimal("1e15") or d.as_tuple().exponent < -30:raise ValueError("decimal bounds")
        values.append(format(d,"f"))
    o,h,l,c=map(Decimal,values[:4])
    if l>min(o,c) or h<max(o,c) or l>h or (kind!="funding_1h" and l<=0):raise ValueError("OHLC")
    if values[4] and Decimal(values[4])<0:raise ValueError("volume")
    return [str(raw["time"]),*values]

def gaps(rows,a,b,step):
    result=[];start=None
    for t in range(a,b,step):
        if t not in rows:
            if start is None:start=t
        elif start is not None:result.append([start,t]);start=None
    if start is not None:result.append([start,b])
    return result

def seed_btc(root,month,kind):
    src=root/"data/delta_india/BTCUSD/2024_verified_archive"
    m=json.loads((src/"manifest.json").read_text())
    if m["synthetic_rows"]!=0 or m["original_trade_rows_preserved"] is not True:raise ValueError("untrusted source manifest")
    a,b=month_bounds(month);step=SERIES[kind][2];result={}
    for item in m["months"]:
        if item["series"]!=kind:continue
        lo,hi=month_bounds(item["month"])
        lo=(lo-19800)//step*step;hi=(hi-19800)//step*step
        if kind=="funding_1h" and item["month"]=="2024-01":lo-=step
        if lo>=b or hi<=a:continue
        _,rows=source_rows(src/kind/(item["month"]+".csv.gz"),item["sha256"],item["observed"],step=step,signed=kind=="funding_1h",blank_volume=kind!="trade_1m")
        for row in rows:
            t=int(row[0])
            if not lo<=t<hi:raise ValueError("source partition bounds")
            if a<=t<b:
                if t in result:raise ValueError("duplicate source")
                result[t]=row
    return result

def equal(a,b):
    return all(x==y or (x!="" and y!="" and Decimal(x)==Decimal(y)) for x,y in zip(a,b))

def recover(symbol,month,kind,seed,request=fetch,deadline=None,pause=time.sleep):
    a,b=month_bounds(month);prefix,res,step=SERIES[kind]
    rows=dict(seed);requests=0;errors=[];conflicts=0
    # Two bounded passes: exact missing runs, then alternate padded windows.
    for width,pad in ((1200,0),(997,2)):
        missing=gaps(rows,a,b,step)
        if not missing:break
        windows=[]
        for lo,hi in missing:
            for x in range(lo,hi,width*step):
                windows.append((max(a,x-pad*step),min(b,hi,x+width*step)+pad*step))
        for lo,hi in windows:
            if deadline is not None and time.monotonic()>deadline:
                errors.append({"type":"time_budget","from":lo,"to":hi});break
            hi=min(b,hi);requests+=1
            try:
                observed={}
                for raw in request(prefix+symbol,res,lo,hi):
                    row=validate(raw,kind,step);t=int(row[0])
                    if not lo<=t<hi:continue
                    if t in observed and not equal(observed[t],row):raise ValueError("conflicting response duplicate")
                    observed[t]=row
                for t,row in observed.items():
                    if t in rows:
                        if not equal(rows[t],row):conflicts+=1
                    else:rows[t]=row
            except Exception as e:
                errors.append({"type":type(e).__name__,"http_status":getattr(e,"code",None),"from":lo,"to":hi})
            pause(.25)
        if deadline is not None and time.monotonic()>deadline:break
    missing=gaps(rows,a,b,step)
    return rows,{"series":kind,"month":month,"utc_start":dt(a).isoformat(),"utc_end_exclusive":dt(b).isoformat(),"expected":(b-a)//step,"seed_rows":len(seed),"observed":len(rows),"recovered":len(rows)-len(seed),"missing":sum((hi-lo)//step for lo,hi in missing),"gaps_exclusive":missing,"requests":requests,"request_errors":errors,"overlap_conflicts":conflicts,"synthetic_rows":0}

def write_series(path,rows):
    buf=io.StringIO(newline="");w=csv.writer(buf,lineterminator="\n");w.writerow(HEADER);w.writerows(rows[t] for t in sorted(rows))
    raw=gzip.compress(buf.getvalue().encode(),mtime=0);path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--symbol",required=True,choices=["BTCUSD","ETHUSD"]);p.add_argument("--month",required=True);p.add_argument("--out",required=True)
    args=p.parse_args()
    if not re.fullmatch(r"2024-(0[1-9]|1[0-2])",args.month):p.error("select a 2024 UTC month")
    out=Path(args.out)/args.symbol/args.month
    out.mkdir(parents=True,exist_ok=False)
    report={"symbol":args.symbol,"month":args.month,"source":BASE,"source_timestamp_label":"as_returned_by_API","funding_is_settlement":False,"series":[]}
    for kind in SERIES:
        seed=seed_btc(ROOT,args.month,kind) if args.symbol=="BTCUSD" else {}
        rows,meta=recover(args.symbol,args.month,kind,seed,deadline=time.monotonic()+240)
        meta["file"]=kind+".csv.gz";meta["sha256"]=write_series(out/meta["file"],rows)
        report["series"].append(meta)
        print(args.symbol,args.month,kind,"observed",meta["observed"],"missing",meta["missing"],"recovered",meta["recovered"],"errors",len(meta["request_errors"]),"conflicts",meta["overlap_conflicts"],flush=True)
    (out/"manifest.json").write_text(json.dumps(report,indent=2)+"\n")
if __name__=="__main__":main()
