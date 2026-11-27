"""Same ETH 15m replay, week starting 23 Nov 2026 IST. Fail closed on gaps."""
import argparse, hashlib, json, time
from pathlib import Path
import numpy as np
import pandas as pd
from recover_delta_2024 import fetch, validate, equal, gaps
from replay_eth_legacy15m_2026 import ROOT, indicators, replay

START=pd.Timestamp("2026-11-23 00:00",tz="Asia/Kolkata").tz_convert("UTC")
WARM=pd.Timestamp("2026-11-01",tz="UTC")
ARCHIVE_END=pd.Timestamp("2026-11-18",tz="UTC")
def epoch(x):return int(x.timestamp())
def load(end,output):
    base=ROOT/"ETHUSD/1m"
    p=next(x for x in json.loads((base/"manifest.json").read_text())["partitions"] if x["file"]=="2026-11.csv.gz")
    archive=base/p["file"]
    assert p["missing_minutes"]==0 and hashlib.sha256(archive.read_bytes()).hexdigest()==p["sha256_gzip"]
    warm=pd.read_csv(archive)
    warm.index=pd.to_datetime(warm.time,unit="s",utc=True)
    assert warm.index.equals(pd.date_range(WARM,ARCHIVE_END,freq="min",inclusive="left"))
    def download(symbol,kind,start):
        a,b=epoch(start),epoch(end);rows={}
        for attempt in range(6):
            missing=gaps(rows,a,b,60)
            if not missing:break
            width=(1000,720,311)[attempt%3]*60
            for lo,hi in missing:
                for x in range(lo,hi,width):
                    stop=min(x+width,hi)
                    try:
                        for raw in fetch(symbol,"1m",x,stop):
                            row=validate(raw,kind,60);t=int(row[0])
                            if x<=t<stop:
                                if t in rows and not equal(rows[t],row):raise RuntimeError("source conflict")
                                rows[t]=row
                    except RuntimeError:raise
                    except Exception as exc:print("FETCH_RETRY",symbol,x,stop,type(exc).__name__,flush=True)
                    time.sleep(.25)
            print("COVERAGE",symbol,"attempt",attempt+1,"observed",len(rows),"expected",(b-a)//60,flush=True)
            if gaps(rows,a,b,60):time.sleep(min(20,2**attempt))
        if gaps(rows,a,b,60):raise RuntimeError(f"{symbol} missing {(b-a)//60-len(rows)} minutes; refusing incomplete replay")
        f=pd.DataFrame([rows[t] for t in sorted(rows)],columns=["time","open","high","low","close","volume"])
        f["time"]=f.time.astype(int)
        for col in ("open","high","low","close","volume"):f[col]=pd.to_numeric(f[col],errors="coerce")
        f.index=pd.to_datetime(f.time,unit="s",utc=True)
        assert f.index.equals(pd.date_range(start,end,freq="min",inclusive="left"))
        assert np.isfinite(f[["open","high","low","close"]]).all().all()
        f.to_csv(output/f"{kind}.csv.gz",index=False,compression="gzip")
        return f
    recent=download("ETHUSD","trade_1m",ARCHIVE_END)
    mark=download("MARK:ETHUSD","mark_1m",START)
    full=pd.concat([warm,recent])
    assert full.index.equals(pd.date_range(WARM,end,freq="min",inclusive="left"))
    assert np.isfinite(full.volume).all()
    t=full.loc[full.index>=START,["open","high","low","close","volume"]]
    m=mark[["open","high","low","close"]]
    assert t.index.equals(m.index)
    bars=full.resample("15min").agg(dict(open="first",high="max",low="min",close="last",volume="sum"))
    return t,m,indicators(bars)
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);args=p.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    # Latest fully finalized 15-minute boundary, with 2-minute source lag allowance.
    end=(pd.Timestamp.now(tz="UTC")-pd.Timedelta(minutes=2)).floor("15min")
    end=min(end,pd.Timestamp("2026-11-27 09:30",tz="Asia/Kolkata").tz_convert("UTC"))
    assert end>START
    t,m,b=load(end,args.output)
    print("WEEK_DATA "+json.dumps(dict(start_ist=str(START.tz_convert("Asia/Kolkata")),end_exclusive_ist=str(end.tz_convert("Asia/Kolkata")),trade_candles=len(t),mark_candles=len(m))),flush=True)
    results=[]
    for spread in (0.,):
        for path in ("DIRECTION",):
            result,trades=replay(t,m,b,path,spread)
            ledger=pd.DataFrame(trades)
            ledger.to_csv(args.output/f"trades-{path}-{spread}.csv",index=False)
            days=[]
            if len(ledger):
                ledger["day_ist"]=pd.to_datetime(ledger.exit_utc,utc=True).dt.tz_convert("Asia/Kolkata").dt.strftime("%Y-%m-%d")
            for day in pd.date_range(START.tz_convert("Asia/Kolkata").normalize(),(end-pd.Timedelta(seconds=1)).tz_convert("Asia/Kolkata").normalize(),freq="D"):
                key=day.strftime("%Y-%m-%d")
                g=ledger[ledger.day_ist==key] if len(ledger) else ledger
                days.append(dict(day=key,trades=len(g),realized_net=float(g.net.sum()) if len(g) else 0.))
            result["days_realized"]=days
            results.append(result)
            print("ETH_WEEK_RESULT "+json.dumps(result),flush=True)
    (args.output/"summary.json").write_text(json.dumps(dict(start_utc=str(START),end_exclusive_utc=str(end),trade_candles=len(t),mark_candles=len(m),results=results),indent=2))
