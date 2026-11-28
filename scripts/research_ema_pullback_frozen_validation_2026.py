"""Frozen top six from run 46103629931. Validation only; no parameter search."""
import csv,gzip,hashlib,json,math
from datetime import datetime
from decimal import Decimal as D
from pathlib import Path
import numpy as np
import research_independent_big_move_2024_2025 as base
import research_independent_big_move_mtf_2024_2025 as mtf
import research_independent_big_move_exits_2024_2025 as exits
import research_independent_big_move_risk_2024_2025 as risk
import research_ema_pullback_slow_exits_2024_2025 as slow
import research_ema_pullback_profit_protection_2024_2025 as frozen
ROOT=Path("data/delta_india/BTCUSD/1m")
OUT=Path("scratch/ema_pullback_frozen_validation_2026")
def ts(s):return int(datetime.fromisoformat(s).timestamp())
START=ts("2026-01-01T00:00:00+00:00")
PRIMARY=ts("2026-11-01T00:00:00+00:00")
END=ts("2026-11-27T00:00:00+00:00")
# Predeclared in the preceding training result, order preserved.
PLANS=(
 ("none",("chandelier",2,3),(2,0),52863.03007,15),
 ("1h",("ema",0,0),(0,0),44193.163075,13),
 ("none",("chandelier",2,2),(2,0),41116.72361,15),
 ("1h-4h",("chandelier",2,3),(5,1),38863.35099,13),
 ("1h-4h",("chandelier",2,3),(5,0),38245.71561,13),
 ("1h-4h",("chandelier",2,3),(0,0),37574.611795,13),
)
def candles():
    manifest=json.loads((ROOT/"manifest.json").read_text())
    parts=[p for p in manifest["partitions"] if p["file"].startswith("2026-")]
    assert len(parts)==11
    expected=START
    for p in parts:
        path=ROOT/p["file"]
        assert hashlib.sha256(path.read_bytes()).hexdigest()==p["sha256_gzip"]
        assert p["missing_minutes"]==0 and p["observed_candles"]==p["expected_minutes"]
        assert ts(p["utc_start"])==expected
        with gzip.open(path,"rt") as f:
            for row in csv.DictReader(f):
                t=int(row["time"]);assert t==expected
                expected+=60
                o,h,l,c,v=(D(row[k]) for k in ("open","high","low","close","volume"))
                assert all(x.is_finite() for x in (o,h,l,c,v))
                assert 0<l<=min(o,c)<=max(o,c)<=h and v>=0
                yield t,o,h,l,c,v
        assert expected==ts(p["utc_end_exclusive"])
    assert expected==END
def evaluate(bars,end,months,label):
    f=base.features(bars,15);sig0=base.signals(f)["ema-pullback"];align=mtf.filters(bars)
    h1=base.features(bars,60);f4=base.features(bars,240)
    h4=np.where(f4["e20"]>f4["e50"],1,np.where(f4["e20"]<f4["e50"],-1,0)).astype(np.int8)
    st=exits.supertrend(f4);lo,hi=slow.chandelier(f4)
    reports=[]
    for n,(flt,plan,protection,training,training_months) in enumerate(PLANS,1):
        assert plan in frozen.EXITS and protection in frozen.PROTECTION
        sig=sig0 if flt=="none" else np.where(sig0==align[flt],sig0,0).astype(np.int8)
        _,trades=frozen.replay(bars,sig,h1,h4,st,lo,hi,f4["c"],plan,protection,START,end)
        # Frozen replay labels all months through December; use only observed months.
        s=risk.risk_summary(trades,months)
        key=f"{flt}|{plan[0]}|delay{plan[2]}|protect{protection[0]}|lock{protection[1]}"
        row=dict(id=n,key=key,period=label,training_points=training,training_profitable_months=training_months,
            summary=s,forced_end_trades=sum(t["exit_reason"]=="Year-end" for t in trades),trades=trades)
        reports.append(row)
        print("RESULT",json.dumps({k:v for k,v in row.items() if k!="trades"},separators=(",",":"),allow_nan=False),flush=True)
    return reports
def run():
    frozen.tests();bars=base.read_bars(candles,START,END)
    assert bars.shape[1]==(END-START)//60
    months=[f"2026-{i:02d}" for i in range(1,11)]
    # The primary complete-month holdout is fixed before viewing results.
    primary=evaluate(bars[:,: (PRIMARY-START)//60],PRIMARY,months,"jan-oct")
    # Additional chronological extension, separately reported; November is partial.
    extended=evaluate(bars,END,months+["2026-11"],"jan-nov26")
    OUT.mkdir(parents=True,exist_ok=True)
    with gzip.open(OUT/"all_ledgers.json.gz","wt") as f:json.dump(primary+extended,f,separators=(",",":"),allow_nan=False)
    fields=("trades","trades_per_month","net","profit_factor","profitable_months","fee_R","fee_pf","fee_months","realized_drawdown_points","fee_dd_R","winners_5R","winners_10R","best_trade_R","points_without_top3","fee_R_without_top3")
    rows=[dict(id=r["id"],key=r["key"],period=r["period"],training_points=r["training_points"],**{k:r["summary"][k] for k in fields},**r["summary"]["monthly_entry_attribution"],forced_end_trades=r["forced_end_trades"]) for r in primary+extended]
    keys=list(dict.fromkeys(k for r in rows for k in r))
    with (OUT/"results.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)
    (OUT/"provenance.json").write_text(json.dumps(dict(training_run=46103629931,plans=PLANS,primary="2026 Jan 1 through Oct 31 UTC",extension="through Nov 26 UTC; November partial",manifest_sha256=hashlib.sha256((ROOT/"manifest.json").read_bytes()).hexdigest(),minutes=bars.shape[1],
        method="same frozen replay, annual cold start and mandatory readiness, endpoint forced liquidation for accounting only, UTC entry-month attribution; fixed quantity points and fee-inclusive risk R; no selection or retuning",
        costs="0.05% taker each side +18% GST; no offer; funding, liquidation and extra slippage excluded"),indent=2))
    print("TOTAL",len(primary),"PRIMARY_POSITIVE",sum(r["summary"]["net"]>0 for r in primary),"EXTENDED_POSITIVE",sum(r["summary"]["net"]>0 for r in extended))
if __name__=="__main__":run()
