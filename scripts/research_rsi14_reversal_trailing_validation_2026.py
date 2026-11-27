"""Frozen 2024-25 monthly-consistency winner; 2026 Jan-Oct validation."""
import csv,gzip,hashlib,json,math
from decimal import Decimal as D
from pathlib import Path
import research_rsi14_reversal_risk_grid_2024_2025 as grid
import research_rsi14_reversal_regimes_2025 as regimes
import research_rsi14_80_20_2025 as source
from research_rsi14_reversal_regimes_2025 import dt,load_data,entry_sets,tests,export_bundle
START=1767225600
END=int(__import__("datetime").datetime.fromisoformat("2026-11-01T00:00:00+00:00").timestamp())
OUT=Path("scratch/rsi14_reversal_trailing_validation_2026")
KEY="liquidity-sweep-sl1.5-tp2.5R-trail-1-0.5"
def candles_2026():
    manifest=json.loads((source.ROOT/"manifest.json").read_text())
    parts=[p for p in manifest["partitions"] if p["file"] in [f"2026-{m:02d}.csv.gz" for m in range(1,11)]]
    assert [p["file"] for p in parts]==[f"2026-{m:02d}.csv.gz" for m in range(1,11)]
    expected=START
    for p in parts:
        path=source.ROOT/p["file"]
        assert p["missing_minutes"]==0 and hashlib.sha256(path.read_bytes()).hexdigest()==p["sha256_gzip"]
        with gzip.open(path,"rt") as f:
            for row in csv.DictReader(f):
                t=int(row["time"]);assert t==expected,(t,expected)
                expected+=60
                o,h,l,c,v=(D(row[k]) for k in ("open","high","low","close","volume"))
                assert all(x.is_finite() for x in (o,h,l,c,v)) and 0<l<=min(o,c)<=max(o,c)<=h and v>=0
                yield t,o,h,l,c,v
    assert expected==END

def run():
    tests();grid.managed_tests()
    plans=[p for p in grid.plans() if p["key"]==KEY]
    assert len(plans)==1
    config=plans[0]
    assert config["sl"]==1.5 and config["tp"]==2.5 and config["management"]=="trail" and config["activation"]==1 and config["distance"]==.5
    grid.START,grid.END=START,END
    regimes.START,regimes.END,regimes.candles=START,END,candles_2026
    bars,rows,signals,rec=load_data()
    entries=entry_sets(rows,signals)["liquidity-sweep"]
    variant=grid.replay(bars,rows,entries,config,rec)
    s=variant["summary"]
    # Shared yearly replay initializes all 12 months. Remove out-of-window months.
    for m in ("2026-11","2026-12"):
        assert s["monthly_entry_attribution"].pop(m)==0
    assert len(s["monthly_entry_attribution"])==10
    assert math.isclose(sum(s["monthly_entry_attribution"].values()),s["net"],abs_tol=1e-6)
    variant["name"]="RSI14 Reversal | frozen 1.5 ATR SL / 2.5R TP / 1R trailing activation / 0.5R distance | 2026 validation"
    print("RESULT",KEY,json.dumps(s,allow_nan=False,separators=(",",":")))
    OUT.mkdir(parents=True,exist_ok=True)
    with gzip.open(OUT/"all_ledgers.json.gz","wt") as f:json.dump([variant],f,allow_nan=False,separators=(",",":"))
    row=dict(key=KEY,**variant["parameters"],**{k:v for k,v in s.items() if k!="monthly_entry_attribution"},**s["monthly_entry_attribution"])
    with (OUT/"all_results.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(row));w.writeheader();w.writerow(row)
    export_bundle(OUT/"backtest.json",family="rsi14-reversal-trailing-validation-2026",symbol="BTCUSD",unit="price points",start_utc=dt(START).isoformat(),end_utc=dt(END).isoformat(),execution_timeframe_minutes=1,signal_timeframe_minutes=15,
        costs="0.05% taker each side +18% GST; no Scalper Offer; additional slippage zero; funding/liquidation excluded; 1m Color.",
        variants=[variant],recorder=rec,data_provenance=dict(
            manifest=str(source.ROOT/"manifest.json"),manifest_sha256=hashlib.sha256((source.ROOT/"manifest.json").read_bytes()).hexdigest(),
            frozen_training_run=46022555632,frozen_training_commit="0fb3b39c5ebba85d51b5d4fea9dd90eadfd603c8",frozen_variant=KEY,
            training_net_points=6791.657785,training_profitable_months=15,training_months=23,
            selection="One frozen monthly-consistency leader selected using 2024-2025 only; Jan-Oct 2026 validation, no retuning.",
            entry="unchanged liquidity sweep, 15m completed candles and next 1m open",
            attribution="UTC entry month, realized trade-close drawdown; indicator reset at Jan 1; end-period accounting close"))
if __name__=="__main__":run()
