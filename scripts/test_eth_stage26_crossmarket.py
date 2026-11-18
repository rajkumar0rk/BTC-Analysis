#!/usr/bin/env python3
"""ETHUSD cross-market verification of UNCHANGED Stage26 BTC signal/risk rules."""
import gzip, hashlib, json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path("data/delta_india/ETHUSD/1m")
OUT=Path("analysis/independent_eth_stage26_crossmarket")
UTC=pd.Timestamp("2025-01-01",tz="UTC")
END=pd.Timestamp("2026-11-01",tz="UTC")
IST="Asia/Kolkata"
FEE=.0005*1.18
SLIP=5.
START_EQUITY=1000.
MONTHS=pd.period_range("2025-01","2026-10",freq="M").astype(str).tolist()

def read():
    manifest=json.loads((ROOT/"manifest.json").read_text())
    parts={x["file"]:x for x in manifest["partitions"]}
    chunks=[]
    for period in pd.period_range("2025-01","2026-10",freq="M"):
        name=str(period)+".csv.gz"
        p=ROOT/name
        assert p.exists(),name
        assert hashlib.sha256(p.read_bytes()).hexdigest()==parts[name]["sha256_gzip"],name+" checksum"
        d=pd.read_csv(p,compression="gzip",usecols=["time","open","high","low","close","volume"])
        assert len(d)==parts[name]["expected_minutes"]==parts[name]["observed_candles"],name+" missing minutes"
        d["time"]=pd.to_datetime(d.time,unit="s",utc=True)
        chunks.append(d)
    x=pd.concat(chunks,ignore_index=True).set_index("time").sort_index()
    assert not x.index.has_duplicates
    assert len(x)==len(pd.date_range(UTC,END,freq="min",inclusive="left"))
    assert (x.index.to_series().diff().dropna()==pd.Timedelta(minutes=1)).all()
    assert (x.low>0).all() and (x.high>=x[["open","close","low"]].max(axis=1)).all()
    assert (x.low<=x[["open","close"]].min(axis=1)).all()
    return x

def make_signals(x,ratio):
    b=x.resample("15min",label="left",closed="left").agg(
        open=("open","first"),high=("high","max"),low=("low","min"),close=("close","last"),n=("close","size"))
    b=b[b.n==15].copy()
    ret=b.close.pct_change()
    up=ret.clip(lower=0).pow(2).rolling(32,min_periods=32).sum().shift(1)
    dn=(-ret.clip(upper=0)).pow(2).rolling(32,min_periods=32).sum().shift(1)
    prev=b.close.shift(1)
    tr=pd.concat([(b.high-b.low),(b.high-prev).abs(),(b.low-prev).abs()],axis=1).max(axis=1)
    b["atr"]=tr.rolling(14,min_periods=14).mean()
    # A signal becomes known only at its bar close (index + 15m).
    b["side"]=np.select([
        (dn>ratio*up)&(b.close<b.open),
        (up>ratio*dn)&(b.close>b.open)
    ],[1,-1],default=0)
    b=b[(b.side!=0)&(b.atr>0)].copy()
    b.index=b.index+pd.Timedelta(minutes=15)
    return b

def replay(x,signals,mult):
    idx=x.index
    opens=x.open.to_numpy(); highs=x.high.to_numpy(); lows=x.low.to_numpy(); closes=x.close.to_numpy()
    eq=START_EQUITY; ledger=[]; monthly=[]
    # Monthly equity accounting includes mark-to-market only on closed trades; positions
    # forcibly close at IST month boundary, so calendar-month equity is unambiguous.
    for month in MONTHS:
        month_start=pd.Timestamp(month+"-01",tz=IST).tz_convert("UTC")
        month_end=(pd.Timestamp(month+"-01",tz=IST)+pd.offsets.MonthBegin(1)).tz_convert("UTC")
        start_eq=eq
        ss=signals[(signals.index>=month_start)&(signals.index<month_end)]
        busy_until=-1
        for t,z in ss.iterrows():
            k=int(idx.searchsorted(t))
            if k>=len(idx) or idx[k]!=t or k<=busy_until:continue
            if idx[k]>=month_end:continue
            side=int(z.side); entry=float(opens[k])+side*SLIP
            dist=float(z.atr)*mult
            if dist<=0 or entry<=0:continue
            qty=min(eq*.01/dist,eq*3/entry)
            if qty<=0:continue
            stop=entry-side*dist; target=entry+side*2*dist
            exit_limit=int(idx.searchsorted(month_end))
            maxj=min(k+239,exit_limit-1,len(idx)-1)
            if maxj<k:continue
            # Initial stop/target cannot fill on signal candle; first checked entry minute.
            xp=None;why="timeout";j=maxj
            for v in range(k,maxj+1):
                if side==1:
                    if lows[v]<=stop:xp=stop;why="stop";j=v;break
                    if highs[v]>=target:xp=target;why="target";j=v;break
                else:
                    if highs[v]>=stop:xp=stop;why="stop";j=v;break
                    if lows[v]<=target:xp=target;why="target";j=v;break
            if xp is None:xp=float(closes[j])
            # Exit slippage worsens stop, target and timed exits.
            exit_price=xp-side*SLIP
            gross=side*(exit_price-entry)*qty
            fees=(abs(entry)+abs(exit_price))*qty*FEE
            net=gross-fees
            before=eq;eq+=net
            ledger.append(dict(month_ist=month,entry_utc=str(t),exit_utc=str(idx[j]),side=side,
                qty_eth=qty,entry_price=entry,exit_price=exit_price,reason=why,
                gross_usd=gross,fees_gst_usd=fees,net_usd=net,equity_before=before,equity_after=eq))
            busy_until=j
            if eq<=0:break
        rows=[z for z in ledger if z["month_ist"]==month]
        monthly.append(dict(month_ist=month,return_pct=100*(eq/start_eq-1) if start_eq>0 else -100,
            start_equity=start_eq,end_equity=eq,trades=len(rows),
            wins=sum(z["net_usd"]>0 for z in rows),
            losses=sum(z["net_usd"]<0 for z in rows),
            net_usd=sum(z["net_usd"] for z in rows)))
        if eq<=0:break
    return pd.DataFrame(monthly),pd.DataFrame(ledger)


def main():
    # This experiment validates original BTC-selected parameters on ETH.
    # Never select a better ETH variant in place of the BTC-selected model.
    OUT.mkdir(parents=True,exist_ok=True)
    x=read()
    validation=dict(
      instrument="ETHUSD Delta Exchange India perpetual futures",
      purpose="Out-of-market replication of Stage26 BTC-selected semivariance signal; not a newly optimized strategy",
      source_main_eth="data/delta_india/ETHUSD/1m",
      source_btc_rule="research/independent-stage26-semivariance:scripts/research_stage26_semivariance.py",
      primary_fixed_config="ratio3_stop2.5",
      ratio=3.0,stop_mult=2.5,target_R=2.0,max_hold_minutes=240,
      risk_per_trade_pct=1.0,leverage_cap=3.0,
      original_1m_candle_count=len(x),
      complete_UTC_1m_months=22,
      first_IST_month_unavailable_hours=5.5,
      fees_per_side_before_gst=0.0005,
      gst_rate_on_exchange_fees=0.18,
      warning="ETH slippage scenarios are assumptions (not actual fill observations); funding/spread/liquidation/lot-size omitted",
      future_data_included=False,
      original_BTC_config_unchanged=True,
    )
    summary=[];primary_monthly=None;primary_ledger=None
    selected="ratio3_stop2.5"
    global SLIP
    # Explicit source-BTC 5 point slip and lower ETH-specific hypotheses.
    # These are NOT optimized by looking at ETH's historical returns.
    for slip in (5.0, 1.0, 0.5, 0.25):
        SLIP=slip
        for ratio in (2.,3.):
            signals=make_signals(x,ratio)
            for mult in (1.5,2.5):
                key=f"ratio{ratio:g}_stop{mult:g}"
                m,l=replay(x,signals,mult)
                train=m[m.month_ist<"2026-01"]
                test=m[m.month_ist>="2026-01"]
                curve=np.r_[START_EQUITY,l.equity_after.to_numpy()] if len(l) else np.array([START_EQUITY])
                dd=float((curve/np.maximum.accumulate(curve)-1).min()*100)
                is_complete=(len(m)==22)
                final_eq=float(m.end_equity.iloc[-1]) if len(m) else START_EQUITY
                row=dict(
                    instrument="ETHUSD",slippage_points_per_side=slip,
                    config=key,btc_selected=(key==selected),
                    complete_months=int(len(m)),positive_months=int((m.return_pct>0).sum()),
                    months_ge10=int((m.return_pct>=10).sum()),
                    positives_2025=int((train.return_pct>0).sum()),
                    positives_2026=int((test.return_pct>0).sum()),
                    months_ge10_2025=int((train.return_pct>=10).sum()),
                    months_ge10_2026=int((test.return_pct>=10).sum()),
                    all_22_profitable=bool(is_complete and (m.return_pct>0).all()),
                    all_22_ge10=bool(is_complete and (m.return_pct>=10).all()),
                    total_trades=int(len(l)),
                    wins=int((l.net_usd>0).sum()) if len(l) else 0,
                    losses=int((l.net_usd<0).sum()) if len(l) else 0,
                    win_rate_pct=float((l.net_usd>0).mean()*100) if len(l) else 0.,
                    final_equity_usd=final_eq,
                    net_account_return_pct=100*(final_eq/START_EQUITY-1),
                    max_closed_trade_drawdown_pct=dd,
                    min_month_return_pct=float(m.return_pct.min()) if len(m) else 0.,
                    fees_gst_usd_total=float(l.fees_gst_usd.sum()) if len(l) else 0.,
                )
                summary.append(row)
                if key==selected:
                    ms=m.copy()
                    ms.insert(1,"slippage_points_per_side",slip)
                    ms.to_csv(OUT/f"fixed_btc_strategy_monthly_slip_{str(slip).replace('.','p')}.csv",index=False)
                    if slip==5.0:
                        primary_monthly=m;primary_ledger=l
    r=pd.DataFrame(summary)
    r.to_csv(OUT/"all_fixed_config_slippage_scenarios.csv",index=False)
    if primary_monthly is None:raise AssertionError("BTC-selected original model missing")
    primary_monthly.to_csv(OUT/"primary_monthly_2025_2026.csv",index=False)
    primary_ledger.to_csv(OUT/"primary_trade_ledger.csv",index=False)
    validation["source_checksum_verified"]=True
    validation["all_scenarios"]=r.to_dict(orient="records")
    primary_row=r[(r.btc_selected)&(r.slippage_points_per_side==5.)].iloc[0].to_dict()
    validation["primary_result"]=primary_row
    (OUT/"quality.json").write_text(json.dumps(validation,indent=2,default=str)+"\n")
    lines=[
        "# ETHUSD independent cross-market backtest: Stage 26 semivariance exhaustion",
        "",
        "Same BTC Stage26 rules and fixed **ratio3_stop2.5** parameter; on ETHUSD raw 1m candles from main.",
        "No ETH-optimized parameter selection or previous result blending. One trade at a time.",
        "15m 32-bar signed squared-return imbalance, opposite-direction 15m confirmation; next minute OPEN.",
        "2.5 × 15m ATR initial stop, 2R target, 240m max hold; 1m stop-first execution.",
        "1% risk-based position size limited to 3× notional. Month-end IST flattening.",
        "",
        "## Slippage and fees",
        "Base BTC cost model: 0.05% taker per side + 18% GST; 5 ETHUSD price points adverse slippage per side.",
        "Because 5 ETH points is proportionally much larger than 5 BTC points, 1, 0.5, 0.25 ETH-price-point",
        "slippage sensitivities are also shown; these are hypotheses, NOT independently verified fills.",
        "Funding, real bid/ask, contract quantity granularity, margin/liquidation and order impact not modeled.",
        "Jan 2025 IST initial 5.5h unavailable. Nov 2026 omitted (incomplete month).",
        "",
        "## Cross-market results (original BTC config flagged, all variations shown only as sensitivities)",
        "",
        r[["slippage_points_per_side","config","btc_selected","positive_months","months_ge10",
           "total_trades","wins","losses","net_account_return_pct",
           "max_closed_trade_drawdown_pct","all_22_profitable","all_22_ge10"]].to_markdown(index=False),
        "",
        "## Original BTC-selected parameters: 5 ETH price-point slippage / side",
        "",
        primary_monthly.to_markdown(index=False),
        "",
        "## All 4 ETH slippage-sensitivity months",
        "",
    ]
    for slip in (1.,0.5,0.25):
        mm=pd.read_csv(OUT/f"fixed_btc_strategy_monthly_slip_{str(slip).replace('.','p')}.csv")
        lines.extend([f"### {slip:g} ETH points / side", "",mm.to_markdown(index=False),""])
    lines.extend(["## Data quality and disclosures","",
                 "Real original ETHUSD compressed CSVs verified against main branch SHA256 manifest; 22 full UTC months.",
                 "This is a retrospective cross-market check, not forward validation, and not evidence of live profitability.",
                 "Cannot guarantee month-by-month profit or executable realized returns."])
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(lines)+"\n")
    print("ETH_STAGE26_DONE "+json.dumps(primary_row,default=str))
    print("FIXED_BTC_RULE_ALL_COST_CASES")
    print(r[r.btc_selected].to_string(index=False))
    print("PRIMARY_MONTHLY")
    print(primary_monthly.to_string(index=False))

if __name__=="__main__":
    main()
