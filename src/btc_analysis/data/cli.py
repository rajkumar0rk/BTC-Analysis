"""Local/CI data import and audit CLI; does not execute strategies."""
import argparse
import json
from pathlib import Path
from .store import HistoryStore, ingest_delta, iso_epoch, dt

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source-root",type=Path,default=Path("data/delta_india"))
    p.add_argument("--store",type=Path,default=Path(".platform-local/history"))
    p.add_argument("--symbol",choices=["BTCUSD","ETHUSD"],action="append",required=True)
    p.add_argument("--start");p.add_argument("--end")
    p.add_argument("--report",type=Path)
    a=p.parse_args()
    if bool(a.start)!=bool(a.end):p.error("start and end must be supplied together")
    report=[]
    for symbol in a.symbol:
        m=ingest_delta(a.source_root/symbol/"1m",a.store,symbol)
        with HistoryStore(a.store,symbol,m["manifest_sha256"]) as h:
            lo=iso_epoch(a.start) if a.start else m["start"]
            hi=iso_epoch(a.end) if a.end else m["end"]
            c=h.coverage(lo,hi)
            streamed=sum(b.num_rows for b in h.iter_batches(lo,hi,strict=False,assume_open=True))
            if streamed!=c.observed_rows:raise ValueError("coverage/read parity mismatch")
            report.append(dict(symbol=symbol,manifest_sha256=h.key,partitions=len(m["partitions"]),
                               start=dt(lo).isoformat(),end_exclusive=dt(hi).isoformat(),
                               expected=c.expected_rows,observed=streamed,missing=c.missing_rows,
                               gaps=c.gaps,timestamp_label_verified=m["label_verified"]))
    result=json.dumps(report,indent=2)
    print(result)
    if a.report:
        a.report.parent.mkdir(parents=True,exist_ok=True)
        a.report.write_text(result+"\n")

if __name__=="__main__":main()
