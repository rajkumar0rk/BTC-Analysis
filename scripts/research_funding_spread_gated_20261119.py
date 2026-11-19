#!/usr/bin/env python3
"""PREDECLARED economic-edge test: same-venue BTCUSD/ETHUSD perpetual funding
differential, dollar-neutral initial notional, NOT optimized indicator signals.

Hypothesis: large, PERSISTENT observed funding differential between BTC and ETH
can compensate two-leg fees before dispersion/hedge error destroys the carry.
Long lower-rate perp, short higher-rate perp; no spot or cross-venue transfer.
Same Delta India venue, but not BTC-beta neutral (two assets can diverge).

All trade signals at 01:00/09:00/17:00 UTC use 72 COMPLETED 1h funding
observations; next-hour open executable price proxy, not order-book fills.
Historical FUNDING: close is a rate INDICATOR, not settled cash; hourly rate
snapshots are imperfect 8h settlement proxies. Conservative mark-price funding
proxy only at assumed 00/08/16 UTC. Rates interpreted percent /100.
If no verified settlement ledger, this cannot prove a live funding arbitrage.

PRIMARY rule: predicted next 14d funding difference (42 settlements), computed
from prior 72h equal-weight mean, >= 2x estimated roundtrip two-leg costs.
Hold max 14d, or exit if 72h predicted spread flips after one day, or an
observed -2% portfolio NAV loss. No intraday/wick fill claims.
Three PREDECLARED diagnostics: 1x fee hurdle, ungated positive spread, and
optimistic hypothetical maker fill envelope. Plus 5bp per-side slip stress.
No parameter optimization, no explicit 2025/2026 tuning.
2026 research-exposed historical check, NOT pristine OOS.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd

BASE=Path("data/delta_india")
OUT=Path("analysis/institutional_funding_spread_20261119")
OUT.mkdir(parents=True,exist_ok=True)
START="2025-01-01"
END="2026-11-18"
INITIAL=1000.
NOTIONAL_FRACTION=.5  # EACH LEG; one-times total initial gross notional.
FUT_TAKER=.0005*1.18
FUT_MAKER=.0002*1.18
BASE_SLIP=.0002
STRESS_SLIP=.0005
STOP_ACCOUNT=.02
FORECAST_HOURS=72
FORECAST_HOLD=14*24
CASH_SETTLEMENT_INTERVAL=8
SETTLEMENTS_IN_HOLD=FORECAST_HOLD//CASH_SETTLEMENT_INTERVAL
SCENARIOS=(
    ("primary_2x_cost_taker",2.0,FUT_TAKER,BASE_SLIP),
    ("diagnostic_1x_cost_taker",1.0,FUT_TAKER,BASE_SLIP),
    ("diagnostic_no_cost_gate_taker",0.0,FUT_TAKER,BASE_SLIP),
    ("stress_2x_cost_taker_5bp_slip",2.0,FUT_TAKER,STRESS_SLIP),
    ("optimistic_maker_envelope_UNVERIFIED",2.0,FUT_MAKER,0.),
)
def read(sym,subdir,columns,step):
    folder=BASE/sym/subdir
    files=sorted(folder.glob("20??-??.csv.gz"))
    if len(files)!=23:raise RuntimeError(f"{sym} {subdir}: expected 23 monthly archives, got {len(files)}")
    frames=[pd.read_csv(f,compression="gzip",usecols=columns) for f in files]
    x=pd.concat(frames,ignore_index=True).sort_values("time").reset_index(drop=True)
    t=x.time.to_numpy(dtype=np.int64)
    expected=np.arange(
        int(pd.Timestamp(START,tz="UTC").timestamp()),
        int(pd.Timestamp(END,tz="UTC").timestamp()),step,dtype=np.int64)
    if not np.array_equal(t,expected):
        raise RuntimeError(f"{sym} {subdir}: missing, duplicate or out-of-order UTC intervals")
    if not np.isfinite(x[[c for c in columns if c!="time"]].to_numpy(dtype=float)).all():
        raise RuntimeError(f"{sym} {subdir}: nonfinite source")
    return x,dict(symbol=sym,series=subdir,source_files=len(files),
        records=len(t),missing_intervals=0,first_utc=str(pd.to_datetime(t[0],unit="s",utc=True)),
        last_utc=str(pd.to_datetime(t[-1],unit="s",utc=True)))
def hourly_asset(sym):
    future,fq=read(sym,"1m",["time","open","close"],60)
    mark,mq=read(sym,"institutional/history/mark_1m",["time","close"],60)
    funding,rq=read(sym,"institutional/history/funding_1h",["time","close"],3600)
    if not np.array_equal(future.time.to_numpy(),mark.time.to_numpy()):
        raise RuntimeError("Mark/perp timestamps mismatch: "+sym)
    if (future.open<=0).any() or (mark.close<=0).any():raise RuntimeError(sym+" nonpositive prices")
    m=len(funding)
    if len(future)!=m*60:raise RuntimeError("Hourly data not aligned")
    p=future.open.to_numpy(dtype=float).reshape(m,60)[:,0]
    last=future.close.to_numpy(dtype=float).reshape(m,60)[:,-1]
    funding_mark=mark.close.to_numpy(dtype=float).reshape(m,60)[:,-1]
    fr=funding.close.to_numpy(dtype=float)
    if not np.all(np.abs(fr)<1.0):
        raise RuntimeError("Funding snapshot units unexpected: >= 1 percent; audit")
    return dict(open=p,close=last,mark=funding_mark,rate=fr,
        time=funding.time.to_numpy(dtype=np.int64),
        quality=[fq,mq,rq],
        funding_rate_percent_quantiles=np.round(np.quantile(fr,[0,.01,.25,.5,.75,.99,1]),8).tolist())
def run(assets,scenario):
    name,hurdle_mult,fee,slip=scenario
    btc=assets["BTCUSD"];eth=assets["ETHUSD"]
    t=btc["time"];n=len(t)
    # Signal rate for trading at hour i is the 72 previous, COMPLETED 1h observations.
    differential=btc["rate"]-eth["rate"]
    trailing=pd.Series(differential).shift(1).rolling(FORECAST_HOURS,min_periods=FORECAST_HOURS).mean().to_numpy()
    cash=INITIAL;pos=None
    daily=[];trades=[];hourly_nav=[];total_funding=0.;total_entry_fee=0.;total_exit_fee=0.
    total_slip=0.;day_active=0;entrycount=0
    for i in range(n):
        utc=pd.Timestamp(int(t[i]),unit="s",tz="UTC")
        rate_diff=trailing[i]
        bprice=btc["open"][i];eprice=eth["open"][i]
        closed_here=False
        if pos is not None and utc.hour%8==0 and i>pos["i"]:
            # PRIOR hour's rate/mark as a CARRY ESTIMATE, not a verified cash ledger.
            fund=-pos["bside"]*pos["bqty"]*btc["mark"][i-1]*btc["rate"][i-1]/100
            fund-=pos["eside"]*pos["eqty"]*eth["mark"][i-1]*eth["rate"][i-1]/100
            cash+=fund
            pos["fund"]+=fund;total_funding+=fund
        if pos is not None:
            pnl=(pos["bside"]*pos["bqty"]*(bprice-pos["bfill"])
                +pos["eside"]*pos["eqty"]*(eprice-pos["efill"]))
            nav=cash+pnl
            spread_flipped=(i-pos["i"]>=24 and
                np.isfinite(rate_diff) and np.sign(rate_diff)!=pos["direction"])
            stop_hit=nav<=pos["start_equity"]*(1-STOP_ACCOUNT)
            due=i-pos["i"]>=FORECAST_HOLD
            terminal=i==n-1
            if spread_flipped or stop_hit or due or terminal:
                # Exit at hourly open; last record uses last completed 1m close.
                exit_b=btc["close"][i] if terminal else bprice
                exit_e=eth["close"][i] if terminal else eprice
                b_closefill=exit_b*(1-pos["bside"]*slip)
                e_closefill=exit_e*(1-pos["eside"]*slip)
                realized=(pos["bside"]*pos["bqty"]*(b_closefill-pos["bfill"])
                    +pos["eside"]*pos["eqty"]*(e_closefill-pos["efill"]))
                out_fee=fee*(pos["bqty"]*b_closefill+pos["eqty"]*e_closefill)
                cash+=realized-out_fee
                total_exit_fee+=out_fee
                total_slip+=slip*(pos["bqty"]*exit_b+pos["eqty"]*exit_e)
                trades.append(dict(scenario=name,entry_time_utc=pos["ts"],exit_time_utc=str(utc),
                    hours_held=i-pos["i"],short_asset="BTCUSD" if pos["bside"]<0 else "ETHUSD",
                    entry_equity=round(pos["start_equity"],6),
                    gross_pair_price_pnl=round(realized,6),funding_proxy_net=round(pos["fund"],6),
                    entry_fees=round(pos["fee"],6),exit_fees=round(out_fee,6),
                    modeled_net_cash_pnl=round(realized+pos["fund"]-pos["fee"]-out_fee,6),
                    reason="spread_flip" if spread_flipped else "loss_guard" if stop_hit else "max_hold" if due else "end_of_data"))
                pos=None;closed_here=True
        # Enter at hour H after last completed 1h rates, 1h after assumed 8h settlement.
        if pos is None and not closed_here and i>=FORECAST_HOURS and utc.hour in (1,9,17) and i+1<n:
            if np.isfinite(rate_diff) and rate_diff!=0:
                # Both legs each receive 0.5x equity notional; fee/slippage each leg
                # at entry & exit -> all four fills costs.
                expected_yield_per_one_leg_notional=abs(rate_diff)/100*SETTLEMENTS_IN_HOLD
                expected_round_trip_per_one_leg_notional=4*(fee+slip)
                if expected_yield_per_one_leg_notional>hurdle_mult*expected_round_trip_per_one_leg_notional:
                    direction=int(np.sign(rate_diff))
                    bside=-direction;eside=direction
                    bqty=(cash*NOTIONAL_FRACTION)/bprice
                    eqty=(cash*NOTIONAL_FRACTION)/eprice
                    bfill=bprice*(1+bside*slip)
                    efill=eprice*(1+eside*slip)
                    in_fee=fee*(bqty*bfill+eqty*efill)
                    before=cash
                    cash-=in_fee
                    total_entry_fee+=in_fee
                    total_slip+=slip*(bqty*bprice+eqty*eprice)
                    pos=dict(ts=str(utc),i=i,start_equity=before,bside=bside,
                        eside=eside,bqty=bqty,eqty=eqty,bfill=bfill,
                        efill=efill,fee=in_fee,fund=0.,direction=direction)
                    entrycount+=1
        if pos is not None:
            day_active+=1
            marknav=cash+pos["bside"]*pos["bqty"]*(bprice-pos["bfill"])+pos["eside"]*pos["eqty"]*(eprice-pos["efill"])
        else:marknav=cash
        hourly_nav.append(marknav)
        if utc.hour==23:
            if pos is not None:
                nav=cash+pos["bside"]*pos["bqty"]*(btc["close"][i]-pos["bfill"])+pos["eside"]*pos["eqty"]*(eth["close"][i]-pos["efill"])
            else:nav=cash
            daily.append(dict(day=utc.strftime("%Y-%m-%d"),year=utc.year,month=utc.strftime("%Y-%m"),
                nav=nav,active_hours=day_active,has_exposure=bool(day_active),
                new_trade_count=entrycount))
            day_active=0;entrycount=0
    if pos is not None:raise RuntimeError("Unclosed terminal position")
    dt=pd.DataFrame(daily)
    dt["daily_pnl"]=dt.nav.diff().fillna(dt.nav-INITIAL)
    return dt,pd.DataFrame(trades),dict(scenario=name,fee_model=fee,slip_each_fill=slip,
        entry_fees=total_entry_fee,exit_fees=total_exit_fee,funding_proxy_net=total_funding,
        estimated_slippage_dollars=total_slip,model_is_executable=False)

def yearly(d,tr,scenario,y):
    x=d[d.year==y]
    pnl=x.daily_pnl.to_numpy(float)
    positives=pnl[pnl>1e-6];losses=pnl[pnl<-1e-6]
    nav=np.r_[INITIAL if y==2025 else float(d[d.year==2025].nav.iloc[-1]),x.nav.to_numpy(float)]
    pf=(float(positives.sum()/-losses.sum()) if len(losses) else None)
    years_tr=tr[pd.to_datetime(tr.entry_time_utc,utc=True).dt.year==y] if len(tr) else tr
    trade_positive=(years_tr.modeled_net_cash_pnl>1e-6).sum() if len(years_tr) else 0
    return dict(scenario=scenario,year=y,calendar_days=len(x),
        profitable_calendar_days=len(positives),losing_calendar_days=len(losses),
        no_position_days=int((~x.has_exposure).sum()),
        positive_calendar_day_pct=round(100*len(positives)/len(x),3),
        new_entries=int(x.new_trade_count.sum()),
        realized_trades=len(years_tr),realized_positive_trades=int(trade_positive),
        average_daily_net_usd=round(float(pnl.mean()),5),
        median_daily_net_usd=round(float(np.median(pnl)),5),
        worst_daily_net_usd=round(float(pnl.min()),5),
        max_dayclose_drawdown_pct=round(100*float(np.min(nav/np.maximum.accumulate(nav)-1)),4),
        daily_net_profit_factor=round(pf,4) if pf is not None else None,
        net_return_pct=round(100*(nav[-1]/nav[0]-1),5),
        profitable_months=int((x.groupby("month").daily_pnl.sum()>0).sum()),
        year_months=x.month.nunique())
def main():
    data={};quality=[]
    for sym in ("BTCUSD","ETHUSD"):
        a=hourly_asset(sym);data[sym]=a
        quality.extend(a["quality"])
    if not np.array_equal(data["BTCUSD"]["time"],data["ETHUSD"]["time"]):
        raise RuntimeError("BOTH assets hourly timestamps diverge")
    summary=[];monthly=[];traces=[];scenario_metas=[]
    for scenario in SCENARIOS:
        dt,ledger,meta=run(data,scenario)
        scenario_metas.append(meta)
        for year in (2025,2026):summary.append(yearly(dt,ledger,scenario[0],year))
        for (y,m),g in dt.groupby(["year","month"],sort=True):
            previous=INITIAL if m=="2025-01" else float(dt[dt.day<g.day.iloc[0]].nav.iloc[-1])
            monthly.append(dict(scenario=scenario[0],month_utc=m,
                net_return_pct=round(100*(g.nav.iloc[-1]/previous-1),5),
                net_pnl_usd=round(float(g.daily_pnl.sum()),5),
                profitable_days=int((g.daily_pnl>1e-6).sum()),
                losing_days=int((g.daily_pnl<-1e-6).sum()),
                no_position_days=int((~g.has_exposure).sum()),
                entries=int(g.new_trade_count.sum())))
        if len(ledger):traces.append(ledger)
        print("SCENARIO",scenario[0],summary[-2:],flush=True)
    pd.DataFrame(summary).to_csv(OUT/"summary.csv",index=False)
    pd.DataFrame(monthly).to_csv(OUT/"monthly.csv",index=False)
    if traces:pd.concat(traces,ignore_index=True).to_csv(OUT/"trade_ledger.csv.gz",index=False,compression="gzip")
    meta=dict(hypothesis="Cashflow: selectively short higher-funding BTC/ETH perp, long lower-funding asset at same Delta venue",
        NOT_ARBITRAGE=True,
        economic_edge="Funding dispersion must exceed fees *before* assuming beta-neutral pricing",
        predeclared_base="Primary 72 completed hourly rate snapshots, 14d horizon, expected carry >= 2x two-leg roundtrip taker fee + 2bp/side slippage, 1x gross leverage, 2% equity loss guard, exit on funding-spread sign reversal",
        differential_rate_signal="Prior 72 hourly FUNDING close observations at entry time; next-hour futures open",
        settlement_proxy="Most recent fully closed FUNDING: 1h rate * prior hourly MARK close at assumed 00/08/16 UTC; NOT confirmed cash-settlement ledger",
        settlement_rate_units="Source FUNDING rate values interpreted as percent; divide by 100",
        checks=dict(no_missing_hourly_data=True,no_imputed_records=True,
            years_2025_and_2026_not_pristine=True,source_complete_to="2026-11-17 23:59 UTC"),
        prior_overlap="Existing institutional_carry_stage1 tested long Binance BTC spot/short Delta BTC perp fixed periods. This is distinct same-venue dynamic BTC/ETH relative-funding two-perp strategy, but cross-asset dispersion and correlated losses remain.",
        input_data=quality,rate_quantiles={sym:data[sym]["funding_rate_percent_quantiles"] for sym in data},
        scenario_costs=scenario_metas,
        constraints=["No historical orderbook; fills at 1h OPEN with 2bp adverse slippage are only a proxy",
            "Funding 1h close series does NOT establish actual settlement cashflows or transfer timing",
            "Two crypto assets are imperfect hedge; BTC-ETH correlation and beta change",
            "No exact exchange settlement/contract denominations, tick/lot, maker fill certainty, maintenance margin, liquidation model",
            "1h entry/exit and risk stops can miss intrahour adverse excursion",
            "Fees and slippage on both legs BOTH sides; stress 5bp each; all calendar days included",
            "No independent forward data; 2026 previously research exposed",
            "No model is qualified for live trade without verified reconciled settlement cashflows, margin and actual fill confirmation"])
    (OUT/"quality.json").write_text(json.dumps(meta,indent=2)+"\n")
    s=pd.DataFrame(summary)
    report=["# Institutional mechanism-first BTC/ETH funding spread study","","## PREDECLARED hypothesis",
      "When persistent funding rate difference is large enough to amortize two-leg roundtrip execution cost, a short-high / long-low same-exchange perp pair may collect net funding without needing BTC's absolute direction. This is NOT guaranteed delta-neutral or risk-free.",
      "","## Base and diagnostics: years 2025, 2026",s.to_string(index=False),"",
      "## Data and capital integrity","Source: Delta India 1-minute traded BTCUSD/ETHUSD prices, MARK: 1-minute and FUNDING: 1-hour price/rate observations, 2025-01-01 to 2026-11-17 UTC, no missing candles. Historical funding rate is not a settlement receipt.",
      "","## Mandatory caveats"]+["- "+z for z in meta["constraints"]]
    (OUT/"REPORT.md").write_text("\n".join(report)+"\n")
    print("COMPLETE",len(s),"year rows",flush=True)
if __name__=="__main__": main()
