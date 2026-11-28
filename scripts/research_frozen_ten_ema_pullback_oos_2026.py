"""One-time frozen validation of the ten previously listed EMA pullback configurations."""
import csv,gzip,json,math,hashlib
from pathlib import Path
from datetime import datetime,timezone
from decimal import Decimal as D
import numpy as np
import research_independent_big_move_2024_2025 as base
import research_independent_big_move_mtf_2024_2025 as mtf
import research_independent_big_move_exits_2024_2025 as exits
import research_independent_big_move_audit_2024_2025 as audit
import research_independent_big_move_risk_2024_2025 as risk
import research_ema_pullback_slow_exits_2024_2025 as slow
import research_ema_pullback_profit_protection_2024_2025 as protect
OUT=Path("scratch/frozen_ten_ema_pullback_oos_2026")
ROOT=base.data25.ROOT
START=int(datetime(2026,1,1,tzinfo=timezone.utc).timestamp())
END=int(datetime(2026,11,1,tzinfo=timezone.utc).timestamp())
MONTHS=[f"2026-{m:02d}" for m in range(1,11)]
# Original ranks, fixed before any validation results. No validation-based selection.
# rank, filter, exit, warmup, Chandelier delay, protection trigger, lock, 2024 net, 2025 net
PLANS=[
(1,"none","chandelier","ready",3,2,0,22191.38321,30671.64686),
(2,"1h","fresh-cross","original",0,0,0,34986.80262,13698.83091),
(3,"1h","fresh-cross","ready",0,0,0,31511.67895,12681.484125),
(4,"none","fresh-cross","original",0,0,0,23191.083645,18094.06149),
(5,"none","chandelier","ready",2,2,0,11250.782555,29865.941055),
(6,"1h-4h","chandelier","ready",3,5,1,26149.274475,12714.076515),
(7,"1h-4h","chandelier","ready",3,5,0,26149.274475,12096.441135),
(8,"1h-4h","chandelier","ready",3,0,0,26149.274475,11425.33732),
(9,"none","fresh-cross","ready",0,0,0,20392.73849,16581.102135),
(10,"1h","unfavorable","original",0,0,0,20346.806545,10641.95453),
]
def candles26():
    manifest=json.loads((ROOT/"manifest.json").read_text())
    parts=sorted((p for p in manifest["partitions"] if p["file"][:7] in MONTHS),key=lambda p:p["file"])
    assert len(parts)==10 and [p["file"][:7] for p in parts]==MONTHS
    expected=START
    for p in parts:
        path=ROOT/p["file"]
        assert hashlib.sha256(path.read_bytes()).hexdigest()==p["sha256_gzip"],path
        assert p["missing_minutes"]==0,path
        count=0
        with gzip.open(path,"rt") as f:
            for row in csv.DictReader(f):
                t=int(row["time"]);assert t==expected,(t,expected)
                expected+=60;count+=1
                o,h,l,c,v=(D(row[k]) for k in ("open","high","low","close","volume"))
                assert all(x.is_finite() for x in (o,h,l,c,v))
                assert 0<l<=min(o,c)<=max(o,c)<=h and v>=0
                yield t,o,h,l,c,v
        assert count==p["expected_minutes"]==p["observed_candles"]
    assert expected==END
def run_year(year,start,end,reader,months):
    bars=base.read_bars(reader,start,end);f=base.features(bars,15)
    sig0=base.signals(f)["ema-pullback"];align=mtf.filters(bars)
    h1=base.features(bars,60);f4=base.features(bars,240)
    h4=np.where(f4["e20"]>f4["e50"],1,np.where(f4["e20"]<f4["e50"],-1,0)).astype(np.int8)
    st=exits.supertrend(f4);lo,hi=slow.chandelier(f4);swing=risk.swing_levels(f)
    schedules={"fresh-cross":audit.cross_schedule(h4),"unfavorable":{d:(np.flatnonzero(h4==-d)+1)*240 for d in (1,-1)}}
    results=[]
    for rank,flt,mode,warm,delay,act,lock,net24,net25 in PLANS:
        sig=sig0 if flt=="none" else np.where(sig0==align[flt],sig0,0).astype(np.int8)
        if mode=="chandelier":
            s,ts=protect.replay(bars,sig,h1,h4,st,lo,hi,f4["c"],("chandelier",2,delay),(act,lock),start,end)
        else:
            s,ts=risk.replay(bars,f,sig,"1h-atr",mode,warm,start,end,h1,h4,swing,schedules)
        s=risk.risk_summary(ts,months)
        if year==2025:
            assert math.isclose(s["net"],net25,abs_tol=1e-6),(rank,s["net"],net25)
        elif year==2024:
            assert math.isclose(s["net"],net24,abs_tol=1e-6),(rank,s["net"],net24)
        results.append(dict(rank=rank,filter=flt,exit=mode,warmup=warm,delay=delay,protect=act,lock=lock,training_2024=net24,training_2025=net25,summary=s,trades=ts))
    print("YEAR_COMPLETE",year,len(results),flush=True)
    return results
def run():
    protect.tests()
    # Verify frozen implementations reproduce the previous results exactly before OOS.
    for year,start,end,reader in ((2024,base.data24.START,base.data24.END,base.data24.candles_2024),(2025,base.data25.START,base.data25.END,base.data25.candles)):
        run_year(year,start,end,reader,[f"{year}-{m:02d}" for m in range(base.dt(start).month,13)])
    results=run_year(2026,START,END,candles26,MONTHS)
    OUT.mkdir(parents=True,exist_ok=True)
    fields=("trades","trades_per_month","net","profit_factor","profitable_months","fee_months","fee_R","fee_pf","realized_drawdown_points","fee_dd_R","win_rate","winners_5R","winners_10R","best_trade_R","points_without_top3","fee_R_without_top3","gross_points","fees","monthly_entry_attribution","monthly_fee_R","monthly_trade_counts")
    rows=[]
    for v in results:
        row={k:x for k,x in v.items() if k not in ("summary","trades")}
        row.update({k:v["summary"][k] for k in fields});rows.append(row)
        print("RESULT",json.dumps(row,separators=(",",":"),allow_nan=False))
    with (OUT/"results.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    with gzip.open(OUT/"results_and_ledgers.json.gz","wt") as f:json.dump(results,f,separators=(",",":"),allow_nan=False)
    (OUT/"provenance.json").write_text(json.dumps(dict(period="2026-01-01 UTC to 2026-11-01 UTC exclusive",minutes=(END-START)//60,manifest_sha256=hashlib.sha256((ROOT/"manifest.json").read_bytes()).hexdigest(),
        original_ranks=PLANS,entry="frozen 15m EMA pullback; H1 ATR14 x2 stop; original indicator startup policy per rank",execution="1m, annual independent reset, final open position closed at last candle close, month attributed to entry, all days",
        costs="0.05% taker each side plus 18% GST; additional slippage, funding, liquidation excluded",
        status="2026 validation only; no parameter changes or re-selection; November excluded; prior 2024/2025 reproduction asserted"),indent=2))
    print("TOTAL",len(rows),"PROFITABLE_POINTS",sum(r["net"]>0 for r in rows),"PROFITABLE_FEE_R",sum(r["fee_R"]>0 for r in rows))
if __name__=="__main__":run()
