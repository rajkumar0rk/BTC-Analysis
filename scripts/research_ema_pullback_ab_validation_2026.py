"""Frozen A/B continuous indicator validation Jan-Oct 2026; no retuning."""
import csv,gzip,hashlib,json,math
from datetime import datetime
from decimal import Decimal as D
from pathlib import Path
import numpy as np
import research_independent_big_move_2024_2025 as base
import research_independent_big_move_risk_2024_2025 as risk
import research_ema_pullback_robustness_2024_2025 as rob
ROOT=Path("data/delta_india/BTCUSD/1m")
OUT=Path("scratch/ema_pullback_ab_validation")
def ts(s):return int(datetime.fromisoformat(s).timestamp())
START=ts("2026-01-01T00:00:00+00:00")
END=ts("2026-11-01T00:00:00+00:00")
MONTHS=[f"2026-{m:02d}" for m in range(1,11)]
def candles():
    manifest=json.loads((ROOT/"manifest.json").read_text())
    parts=[p for p in manifest["partitions"] if p["file"][:7] in MONTHS]
    assert len(parts)==10
    expected=START
    for p in parts:
        path=ROOT/p["file"]
        assert hashlib.sha256(path.read_bytes()).hexdigest()==p["sha256_gzip"]
        assert p["missing_minutes"]==0 and p["observed_candles"]==p["expected_minutes"]
        assert ts(p["utc_start"])==expected
        with gzip.open(path,"rt") as f:
            for row in csv.DictReader(f):
                t=int(row["time"]);assert t==expected;expected+=60
                o,h,l,c,v=(D(row[k]) for k in ("open","high","low","close","volume"))
                assert all(x.is_finite() for x in (o,h,l,c,v))
                assert 0<l<=min(o,c)<=max(o,c)<=h and v>=0
                yield t,o,h,l,c,v
        assert expected==ts(p["utc_end_exclusive"])
    assert expected==END
def run():
    rob.tests()
    assert base.data24.END==base.data25.START and base.data25.END==START
    b24=base.read_bars(base.data24.candles_2024,base.data24.START,base.data24.END)
    b25=base.read_bars(base.data25.candles,base.data25.START,base.data25.END)
    b26=base.read_bars(candles,START,END)
    history=np.concatenate([b24,b25,b26],axis=1);offset=b24.shape[1]+b25.shape[1]
    pack=rob.indicator_pack(history,(20,50))
    prefix=rob.indicator_pack(history[:,:offset],(20,50))
    for a,b in zip(pack,prefix):assert np.allclose(a[:len(b)],b,equal_nan=True)
    p25=rob.slice_pack(pack,b24.shape[1],b25.shape[1])
    f25=rob.funding_proxy(2025,b25,base.data25.START,base.data25.END)
    for candidate,expected in (("A",12163.06097),("B",16349.35202)):
        s,_=rob.replay(b25,p25,candidate,2.,"all",0,base.data25.START,base.data25.END,f25)
        assert math.isclose(s["net"],expected,abs_tol=1e-6),(candidate,s["net"],expected)
    p26=rob.slice_pack(pack,offset,b26.shape[1])
    f26=rob.funding_proxy(2026,b26,START,END)
    OUT.mkdir(parents=True,exist_ok=True);rows=[]
    with gzip.open(OUT/"ledgers.jsonl.gz","wt") as ledger:
        for candidate in ("A","B"):
            for slip in (0,50):
                _,trades=rob.replay(b26,p26,candidate,2.,"all",slip,START,END,f26)
                s=risk.risk_summary(trades,MONTHS);fs=rob.funded(trades,MONTHS)
                row=dict(candidate=candidate,slippage_per_side=slip,summary=s,proxy_summary=fs,
                    forced_end_trades=sum(t["exit_reason"]=="End of yearly evaluation" for t in trades))
                # All criteria announced before this run. DD and concentration reported,
                # no invented drawdown threshold; no claim of entirely untouched 2026.
                row["checks"]=dict(positive=fs["net"]>0 if fs else None,pf_above_1_2=fs["profit_factor"]>1.2 if fs and fs["profit_factor"] is not None else None,
                    profitable_months_at_least_7=fs["profitable_months"]>=7 if fs else None,
                    positive_without_top3=fs["points_without_top3"]>0 if fs else None)
                rows.append(row)
                print("RESULT",json.dumps(row,separators=(",",":"),allow_nan=False,default=rob.json_scalar),flush=True)
                ledger.write(json.dumps(dict(**row,trades=trades),separators=(",",":"),allow_nan=False,default=rob.json_scalar)+"\n")
    (OUT/"results.json").write_text(json.dumps(rows,indent=2,allow_nan=False,default=rob.json_scalar))
    (OUT/"provenance.json").write_text(json.dumps(dict(training_run=46105354842,prior_2026_A_cold_start_run=46103814721,period="Jan 1 to Oct 31 2026 UTC",candidates=["A","B"],ema=[20,50],initial_stop="1H ATR14 x 2",days="all",warmup="continuous since Feb 2024, positions flat at annual boundary",slippage_per_side=[0,50],costs="taker .05% each side plus GST; separate 8h funding proxy, not settled funding; no liquidation",selection="no retuning; A previously evaluated on this period using annual cold start; not wholly untouched",drawdown="realized trade-close points and R, no predefined numerical cutoff"),indent=2))
    print("TOTAL",len(rows),flush=True)
if __name__=="__main__":run()
