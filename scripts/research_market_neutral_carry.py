#!/usr/bin/env python3
"""Non-directional, hedged BTC funding-carry feasibility; no signal optimization."""
import io, json, urllib.request, zipfile
from pathlib import Path
import numpy as np
import pandas as pd
OUT=Path("analysis/institutional_carry_stage1")
ROOT=Path("data/delta_india/BTCUSD")
QTY=.001
FUT_TAKER=.0005*1.18
FUT_MAKER=.0002*1.18
SPOT_FEE=.001
MONTHS=pd.period_range("2025-10","2026-09",freq="M")
DURATIONS=[8,24,168,336,720]
def local(folder,field="open"):
    paths=sorted(folder.glob("20??-??.csv.gz"))
    if not paths: raise RuntimeError("Missing genuine exchange archive "+str(folder))
    frames=[]
    for p in paths:
        x=pd.read_csv(p,compression="gzip",usecols=["time",field])
        x["time"]=pd.to_datetime(x["time"].astype("int64"),unit="s",utc=True)
        frames.append(x.set_index("time")[[field]])
    y=pd.concat(frames).sort_index()
    if not y.index.is_unique:raise RuntimeError("duplicate timestamps "+str(folder))
    return y[field].astype(float)
def binance_spot():
    pieces=[]; provenance=[]
    for m in MONTHS:
        key=str(m)
        url=f"https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1h/BTCUSDT-1h-{key}.zip"
        req=urllib.request.Request(url,headers={"User-Agent":"BTC-Analysis Research bot/1.0"})
        with urllib.request.urlopen(req,timeout=70) as response:
            archive=response.read()
        with zipfile.ZipFile(io.BytesIO(archive)) as z:
            name=next((n for n in z.namelist() if n.endswith(".csv")),None)
            if name is None:raise RuntimeError("No spot CSV "+url)
            raw=pd.read_csv(io.BytesIO(z.read(name)),header=None)
        times=pd.to_numeric(raw.iloc[:,0],errors="raise").astype("int64")
        # Binance public data migrated to microseconds after Jan 2025 in some distributions.
        unit="us" if times.iloc[0]>10**14 else "ms"
        idx=pd.to_datetime(times,unit=unit,utc=True)
        frame=pd.Series(pd.to_numeric(raw.iloc[:,1],errors="raise").to_numpy(float),index=idx)
        expected=pd.date_range(m.start_time.tz_localize("UTC"),(m+1).start_time.tz_localize("UTC"),freq="1h",inclusive="left")
        if not frame.index.equals(expected) or frame.isna().any():
            raise RuntimeError(f"Non-dense official Binance monthly BTCUSDT spot 1h data: {key}")
        provenance.append({"month":key,"url":url,"sha256_not_recorded":True,"rows":len(frame)})
        pieces.append(frame)
    s=pd.concat(pieces).sort_index()
    return s,provenance
def labels(t):
    if t.year==2025:return "2025_Q4"
    if t<pd.Timestamp("2026-07-01",tz="UTC"):return "2026_H1"
    return "2026_Q3"
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    spot,prov=binance_spot()
    perp=local(ROOT/"1m","open").resample("1h").first().reindex(spot.index)
    mark=local(ROOT/"institutional/history/mark_1m","close").resample("1h").last().reindex(spot.index)
    funding=local(ROOT/"institutional/history/funding_1h","close")
    if perp.isna().any() or mark.isna().any():raise RuntimeError("Incomplete Delta 1m futures/mark pairing")
    # Funding rate close in prior completed hour. It is NOT a cash transfer ledger.
    rate=funding.shift(1,freq="1h").reindex(spot.index)
    settlement=(spot.index.hour % 8==0)
    rate=rate.where(settlement)
    # Track quote-price and timing limitations, never substitute missing rates.
    all_records=[]; excluded=[]
    for duration in DURATIONS:
        for entry in range(0,len(spot)-duration,duration):
            end=entry+duration
            st=spot.index[entry]; et=spot.index[end]
            inner=np.arange(entry+1,end)
            pay=inner[(spot.index[inner].hour % 8)==0]
            if len(pay)==0:
                excluded.append(dict(duration_hours=duration,start_utc=str(st),reason="no_internal_funding"))
                continue
            values=rate.iloc[pay]
            if values.isna().any():
                excluded.append(dict(duration_hours=duration,start_utc=str(st),reason="missing_rate_proxy"))
                continue
            fs,fe=float(perp.iloc[entry]),float(perp.iloc[end])
            ss,se=float(spot.iloc[entry]),float(spot.iloc[end])
            # Short perp receives positive funding. Source displays percentages, not fractions.
            fund=QTY*float(np.dot(values.to_numpy(float)/100,perp.iloc[pay].to_numpy(float)))
            gross_basis=QTY*((se-ss)-(fe-fs))
            fcost=QTY*FUT_TAKER*(fs+fe)
            scost=QTY*SPOT_FEE*(ss+se)
            maker_cost=QTY*FUT_MAKER*(fs+fe)
            slip=4*QTY*5 # two entry and two exit fills; all adverse
            stress_slip=4*QTY*15
            initial=QTY*ss
            base=fund+gross_basis-fcost-scost-slip
            optimistic=fund+gross_basis-maker_cost
            for scenario, net in [
                ("baseline_no_financing",base),
                ("baseline_5pct_financing",base-initial*.05*duration/(365*24)),
                ("baseline_10pct_financing",base-initial*.10*duration/(365*24)),
                ("stress_15point_slip_5pct_financing",fund+gross_basis-fcost-scost-stress_slip-initial*.05*duration/(365*24)),
                ("optimistic_non_executable_envelope",optimistic),
            ]:
                all_records.append(dict(period=labels(st),scenario=scenario,duration_hours=duration,
                    start_utc=str(st),end_utc=str(et),settlements=len(pay),
                    spot_start=round(ss,2),perp_start=round(fs,2),
                    funding_usd_proxy=round(fund,6),basis_change_usd_proxy=round(gross_basis,6),
                    futures_fee_usd_proxy=round(fcost if scenario!="optimistic_non_executable_envelope" else maker_cost,6),
                    spot_fee_usd_proxy=round(scost if scenario!="optimistic_non_executable_envelope" else 0,6),
                    net_usd_proxy=round(net,6),net_pct_spot_capital=round(net/initial*100,5)))
    tr=pd.DataFrame(all_records)
    if tr.empty: raise RuntimeError("No eligible funding carry trials")
    summ=[]
    for keys,g in tr.groupby(["duration_hours","scenario","period"],sort=True):
        v=g.net_usd_proxy.to_numpy(float)
        c=np.r_[0,v.cumsum()]
        gp=v[v>0].sum(); gl=-v[v<0].sum()
        summ.append(dict(duration_hours=keys[0],scenario=keys[1],period=keys[2],n=len(v),
                         mean_net_usd_proxy=round(float(v.mean()),5),
                         mean_net_pct=round(float(g.net_pct_spot_capital.mean()),5),
                         median_net_usd_proxy=round(float(np.median(v)),5),
                         positive_pct=round(float(100*np.mean(v>0)),2),
                         profit_factor=round(float(gp/gl),3) if gl else None,
                         max_drawdown_usd_proxy=round(float((np.maximum.accumulate(c)-c).max()),4),
                         mean_funding_usd_proxy=round(float(g.funding_usd_proxy.mean()),5),
                         mean_basis_change_usd_proxy=round(float(g.basis_change_usd_proxy.mean()),5)))
    results=pd.DataFrame(summ)
    tr.to_csv(OUT/"carry_trial_ledger.csv",index=False)
    results.to_csv(OUT/"carry_summary.csv",index=False)
    pd.DataFrame(excluded,columns=["duration_hours","start_utc","reason"]).to_csv(OUT/"excluded_trials.csv",index=False)
    qual={"venue_pair":"Long Binance BTCUSDT spot / short Delta India BTCUSD perp",
        "spot_source":prov,"spot_rows":len(spot),"spot_first":str(spot.index[0]),"spot_last":str(spot.index[-1]),
        "trials_rows_including_scenarios":len(tr),"excluded_trial_count":len(excluded),
        "settlement_assumption":"00:00/08:00/16:00 UTC; previous completed funding hourly observation proxy",
        "rate_unit_assumption":"API 0.01 is 0.01% (divide by 100)",
        "funding_proxy_coverage_pct":round(float(rate.dropna().shape[0]/max(settlement.sum(),1)*100),2),
        "warning":"Funding 1h series is NOT settled funding and mark is not hedge cashflow. This is a research feasibility approximation, not a valid executable backtest.",
        "risk":"Binance USDT not identical to Delta USD; hedge availability/Indian access/capital transfers/margin risk not reconstructed"}
    (OUT/"quality.json").write_text(json.dumps(qual,indent=2)+"\n")
    def md(z):return z.to_markdown(index=False)
    lines=["# Market-neutral BTC carry research — Stage 4A","",
    "Long Binance BTCUSDT spot, short equivalent Delta India BTCUSD perpetual, fixed calendar scheduling; NO BTC-direction prediction.",
    "",
    "## Data provenance and limits",
    json.dumps({k:v for k,v in qual.items() if k!="spot_source"},indent=2),"",
    "Binance source monthly downloads are recorded in quality.json; fund snapshots are **historical rates, NOT confirmed payment transactions**. All results are USD/USDT-equivalent model estimates.",
    "",
    "## Calendar carry performance, all durations and cost scenarios",
    md(results),"",
    "## Exclusion audit",
    md(pd.DataFrame(excluded).groupby(["duration_hours","reason"]).size().reset_index(name="n")) if excluded else "None", "",
    "## Rejection criteria",
    "An actual, market-neutral executable edge is NOT established even if any modeled net mean is positive. Require venue-available hedging, rate/payment reconciliation, real fills and order-book spreads, margin/liquidations, USD/USDT conversion and independent forward evaluation.",
    "",
    "Results are exploratory, known-date historical observations; scenario comparisons reuse observations and cannot be combined as independent portfolio returns."]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(lines)+"\n")
    print("CARRY_STUDY_COMPLETED",json.dumps({k:v for k,v in qual.items() if k!="spot_source"}))
    print(results.to_string(index=False))
if __name__=="__main__":main()
