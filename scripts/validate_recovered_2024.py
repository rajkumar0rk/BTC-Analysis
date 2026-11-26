"""Validate all 15 candidate month archives before retaining the branch."""
import json,sys
from pathlib import Path
from recover_delta_2024 import SERIES,seed_btc,gaps,equal,ROOT
from stage_repository_history import source_rows,month_bounds

def verify(root):
    expected={("BTCUSD",m) for m in ("2024-01","2024-02","2024-12")}|{("ETHUSD",f"2024-{i:02d}") for i in range(1,13)}
    actual={(p.parent.parent.name,p.parent.name) for p in root.glob("*/*/manifest.json")}
    if actual!=expected:raise ValueError("missing or unexpected archive months")
    summary=[]
    for symbol,month in sorted(expected):
        out=root/symbol/month;doc=json.loads((out/"manifest.json").read_text());a,b=month_bounds(month)
        if doc["symbol"]!=symbol or doc["month"]!=month or doc["funding_is_settlement"] is not False or {x["series"] for x in doc["series"]}!=set(SERIES) or len(doc["series"])!=3:raise ValueError("archive identity")
        for x in doc["series"]:
            kind=x["series"];step=SERIES[kind][2]
            if x["file"]!=kind+".csv.gz" or x["synthetic_rows"]!=0:raise ValueError("invalid source file")
            _,data=source_rows(out/x["file"],x["sha256"],x["observed"],step=step,signed=kind=="funding_1h",blank_volume=kind!="trade_1m")
            rows={int(r[0]):r for r in data}
            if any(not a<=t<b for t in rows) or x["expected"]!=(b-a)//step or x["missing"]!=x["expected"]-len(rows) or x["gaps_exclusive"]!=gaps(rows,a,b,step):raise ValueError("coverage mismatch")
            seed=seed_btc(ROOT,month,kind) if symbol=="BTCUSD" else {}
            if x["seed_rows"]!=len(seed) or x["recovered"]!=len(rows)-len(seed) or any(t not in rows or rows[t]!=r for t,r in seed.items()):raise ValueError("original row changed")
            summary.append({"symbol":symbol,**{k:x[k] for k in ("month","series","expected","observed","missing","recovered","overlap_conflicts")},"request_error_count":len(x["request_errors"])})
    return summary
if __name__=="__main__":
    root=Path(sys.argv[1]);summary=verify(root)
    (root/"coverage.json").write_text(json.dumps(summary,indent=2)+"\n")
    print("Validated candidate partitions:",len(summary),"Missing intervals:",sum(x["missing"] for x in summary))
