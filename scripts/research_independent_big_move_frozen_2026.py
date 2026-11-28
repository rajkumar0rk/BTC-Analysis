"""Single frozen holdout evaluation, no new strategy search."""
import csv,gzip,json,hashlib,math
from pathlib import Path
from datetime import datetime
from decimal import Decimal as D
import numpy as np
import research_independent_big_move_2024_2025 as base
import research_independent_big_move_mtf_2024_2025 as mtf
import research_independent_big_move_risk_2024_2025 as risk
import research_independent_big_move_audit_2024_2025 as audit
ROOT=Path("data/delta_india/BTCUSD/1m")
OUT=Path("scratch/independent_big_move_frozen_2026")
START=int(datetime.fromisoformat("2026-01-01T00:00:00+00:00").timestamp())
END=int(datetime.fromisoformat("2026-11-27T00:00:00+00:00").timestamp())
KEY="ema-pullback|1h|1h-atr|fresh-cross|original"
def candles():
    m=json.loads((ROOT/"manifest.json").read_text())
    parts=[p for p in m["partitions"] if p["file"].startswith("2026-")]
    assert len(parts)==11
    expected=START
    for p in parts:
        path=ROOT/p["file"]
        assert hashlib.sha256(path.read_bytes()).hexdigest()==p["sha256_gzip"]
        assert p["missing_minutes"]==0
        assert int(datetime.fromisoformat(p["utc_start"]).timestamp())==expected
        n=0
        with gzip.open(path,"rt") as f:
            for row in csv.DictReader(f):
                t=int(row["time"]);assert t==expected
                expected+=60;n+=1
                o,h,l,c,v=(D(row[k]) for k in ("open","high","low","close","volume"))
                assert all(x.is_finite() for x in (o,h,l,c,v))
                assert 0<l<=min(o,c)<=max(o,c)<=h and v>=0
                yield t,o,h,l,c,v
        assert n==p["expected_minutes"]==p["observed_candles"]
        assert expected==int(datetime.fromisoformat(p["utc_end_exclusive"]).timestamp())
    assert expected==END

def evaluate(bars,start,end):
    f=base.features(bars,15);ss=base.signals(f)["ema-pullback"];align=mtf.filters(bars)["1h"]
    sig=np.where(ss==align,ss,0).astype(np.int8)
    h1=base.features(bars,60)
    c4=bars[3,239::240];e20=base.ema(c4,20);e50=base.ema(c4,50)
    h4=np.where(e20>e50,1,np.where(e20<e50,-1,0)).astype(np.int8)
    schedules={"fresh-cross":audit.cross_schedule(h4)}
    s,ts=risk.replay(bars,f,sig,"1h-atr","fresh-cross","original",start,end,h1,h4,risk.swing_levels(f),schedules)
    # The shared annual replay initializes all 12 months; retain only covered months.
    months=[f"{base.dt(start).year}-{m:02d}" for m in range(base.dt(start).month,base.dt(end-1).month+1)]
    s=risk.risk_summary(ts,months)
    return s,ts

def run():
    risk.tests();mtf.tests()
    # Reproduce exact training-year results to verify frozen configuration.
    for y,start,end,reader,expected,n in (
        (2024,base.data24.START,base.data24.END,base.data24.candles_2024,34986.80262,None),
        (2025,base.data25.START,base.data25.END,base.data25.candles,13698.83091,None)):
        bars=base.read_bars(reader,start,end)
        s,_=evaluate(bars,start,end)
        assert math.isclose(s["net"],expected,abs_tol=1e-6),(y,s["net"],expected)
        print("BASELINE_VERIFIED",y,s["net"],s["trades"])
    bars=base.read_bars(candles,START,END)
    s,ts=evaluate(bars,START,END)
    print("RESULT",json.dumps(s,separators=(",",":"),allow_nan=False))
    print("COVERAGE",base.dt(START).isoformat(),base.dt(END).isoformat(),bars.shape[1])
    print("TRADES",json.dumps(ts,separators=(",",":"),allow_nan=False))
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"result.json").write_text(json.dumps(dict(key=KEY,summary=s,trades=ts,
       period_start=base.dt(START).isoformat(),period_end_exclusive=base.dt(END).isoformat(),
       verified_input_minutes=bars.shape[1],manifest_sha256=hashlib.sha256((ROOT/"manifest.json").read_bytes()).hexdigest(),
       rules="Frozen 15M EMA20 reclaim aligned EMA20/50, 1H EMA20/50 filter, initial 2 H1 ATR14, fresh adverse H4 EMA20/50 crossover exit, original warmup, no TP",
       costs="0.05% taker each side +18% GST; no offer; zero extra slippage; no funding or liquidation",
       accounting="one position, 1m execution, UTC entry month, annual indicator reset, forced close at coverage end; November partial; no 2026 fitting"),indent=2,allow_nan=False))
    with (OUT/"trades.csv").open("w",newline="") as f:
        if ts:
            w=csv.DictWriter(f,fieldnames=list(ts[0]));w.writeheader();w.writerows(ts)
if __name__=="__main__":run()
