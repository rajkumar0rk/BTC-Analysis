#!/usr/bin/env python3
"""RESET Step 1: 1 trade EVERY IST WEEKDAY; percent stop x reward × fixed-hour.

A test of DAILY PROFIT CONSISTENCY, not rare setups. No +0.2% fixed target.
For each candidate, 477 entry days = 477 positions, never Sat/Sun.
1x notional account, no leverage; stop-first 1m execution; 5pt slip per side;
regular taker fee +18% GST; hypothetical 30m Scalper Offer cost sensitivity.
Preselect 2025 only, 2026 research-exposed recheck (NOT pristine holdout).
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from numba import njit

SOURCE=Path("data/delta_india/BTCUSD/1m")
OUT=Path("analysis/btc_every_weekday_reset_step1")
MONTHS=pd.period_range("2025-01","2026-10",freq="M").astype(str).tolist()
DAYS=pd.date_range("2025-01-02","2026-10-30",freq="B",tz="Asia/Kolkata")
COST=0.0005*1.18
SLIP=5.0
STOPS=np.array([0.1,0.2,0.3,0.5,0.75,1.0],dtype=np.float64)
RR=np.array([0.75,1.,1.5,2.,3.,4.],dtype=np.float64)
HOLDS=np.array([30,60,120],dtype=np.int32)
RULES=("always_long","always_short",
       "mom5_follow","mom5_fade",
       "mom15_follow","mom15_fade",
       "mom60_follow","mom60_fade",
       "mom240_follow","mom240_fade")
MODES=("standard","scalper_offer")
NTRAIN=int(np.count_nonzero(DAYS.year==2025))
IST_DAYS=np.asarray(DAYS.strftime("%Y-%m-%d"))
MONTH_LABELS=np.array([x[:7] for x in IST_DAYS])
MONTH_KEYS,MONTH_IDX=np.unique(MONTH_LABELS,return_inverse=True)
assert len(MONTH_KEYS)==22 and NTRAIN==260 and len(DAYS)-NTRAIN==217 and len(DAYS)==477

def load():
    parts=[]
    for mon in MONTHS:
        f=SOURCE/(mon+".csv.gz")
        if not f.exists():raise FileNotFoundError(f)
        v=pd.read_csv(f,compression="gzip",usecols=["time","open","high","low","close","volume"])
        v["time"]=pd.to_datetime(v.time.astype("int64"),unit="s",utc=True)
        parts.append(v)
    m=pd.concat(parts,ignore_index=True).set_index("time").sort_index()
    if m.index.has_duplicates or not m.index.is_monotonic_increasing or m.isna().any().any():
        raise ValueError("Null/duplicate 1m rows")
    if not m.index.to_series().diff().iloc[1:].eq(pd.Timedelta(minutes=1)).all():
        raise ValueError("Missing 1m candles")
    if ((m.low<=0)|(m.high<m[["low","open","close"]].max(axis=1))|
        (m.low>m[["high","open","close"]].min(axis=1))|
        (m.volume<0)).any():
        raise ValueError("Invalid OHLCV")
    if m.index[0]!=pd.Timestamp("2025-01-01T00:00:00Z") or m.index[-1]!=pd.Timestamp("2026-10-31T23:59:00Z"):
        raise AssertionError("Unexpected archive UTC start/end")
    return m

def prepare(m):
    o=m.open.to_numpy(float);c=m.close.to_numpy(float)
    starts=np.empty((len(DAYS),24),dtype=np.int32)
    directions=np.empty((len(RULES),len(DAYS),24),dtype=np.int8)
    ties=np.zeros((len(RULES),),dtype=int)
    for di,day in enumerate(DAYS):
        ds=day.strftime("%Y-%m-%d")
        start=int(m.index.get_indexer([day.tz_convert("UTC")])[0])
        last=int(m.index.get_indexer([(day+pd.Timedelta(minutes=1439)).tz_convert("UTC")])[0])
        if start<0 or last-start!=1439:
            raise AssertionError("Incomplete IST day "+ds)
        for hour in range(24):
            i=start+hour*60
            starts[di,hour]=i
            directions[0,di,hour]=1
            directions[1,di,hour]=-1
            for j,lookback in enumerate((5,15,60,240)):
                dx=c[i-1]-o[i-lookback]
                s=1 if dx>=0 else -1
                if dx==0:ties[2+2*j]+=1;ties[3+2*j]+=1
                directions[2+2*j,di,hour]=s
                directions[3+2*j,di,hour]=-s
    if np.any(directions==0):raise AssertionError("Daily entry skipped")
    if starts.shape!=(477,24):raise AssertionError("Wrong entry grid")
    return starts,directions,ties

@njit(cache=True)
def simulate(o,hi,lo,start,stop_pct,rr,hold,fee,slip):
    # dims: day, hour, side(long/short), stop, reward, maxhold, cost_model
    shape=(start.shape[0],start.shape[1],2,stop_pct.shape[0],rr.shape[0],hold.shape[0])
    returns=np.empty(shape+(2,),dtype=np.float64)
    fees=np.empty(shape+(2,),dtype=np.float64)
    gross=np.empty(shape,dtype=np.float64)
    slip_points=np.empty(shape,dtype=np.float64)
    reason=np.empty(shape,dtype=np.int8)
    durations=np.empty(shape,dtype=np.int16)
    for d in range(start.shape[0]):
        for hour in range(start.shape[1]):
            i=int(start[d,hour])
            mid=o[i]
            mins_left=1439-hour*60  # force out at 23:59 IST OPEN at latest.
            for si in range(2):
                side=1. if si==0 else -1.
                fillin=mid+side*slip
                fee_in=fee*fillin
                for s in range(stop_pct.shape[0]):
                    stop=mid*(1.-side*stop_pct[s]/100.)
                    for r in range(rr.shape[0]):
                        tp=mid*(1.+side*(stop_pct[s]/100.)*rr[r])
                        for h in range(hold.shape[0]):
                            maxhold=min(int(hold[h]),mins_left)
                            exit_j=i+maxhold
                            midout=o[exit_j]
                            why=3 # TIMEOUT
                            for j in range(i,i+maxhold):
                                stop_hit=lo[j]<=stop if side>0 else hi[j]>=stop
                                tp_hit=hi[j]>=tp if side>0 else lo[j]<=tp
                                if stop_hit:
                                    midout=min(o[j],stop) if side>0 else max(o[j],stop)
                                    exit_j=j;why=2;break
                                if tp_hit:
                                    midout=tp
                                    exit_j=j;why=1;break
                            fillout=midout-side*slip
                            elapsed=exit_j-i
                            fee_std=fee_in+fee*fillout
                            fee_offer=fee_in+(0. if elapsed<=30 else fee*fillout)
                            gross_pts=side*(midout-mid)
                            net_before_fee=side*(fillout-fillin)
                            returns[d,hour,si,s,r,h,0]=(net_before_fee-fee_std)/fillin
                            returns[d,hour,si,s,r,h,1]=(net_before_fee-fee_offer)/fillin
                            fees[d,hour,si,s,r,h,0]=fee_std
                            fees[d,hour,si,s,r,h,1]=fee_offer
                            gross[d,hour,si,s,r,h]=gross_pts
                            slip_points[d,hour,si,s,r,h]=2*slip
                            reason[d,hour,si,s,r,h]=why
                            durations[d,hour,si,s,r,h]=elapsed
    return returns,fees,gross,slip_points,reason,durations

def get_path(returns,fees,gross,slip_pts,reason,durations,signs,hour,stop_i,rr_i,hold_i,mode_i):
    d=np.arange(len(DAYS))
    side=np.where(signs>0,0,1)
    return (returns[d,hour,side,stop_i,rr_i,hold_i,mode_i],
            fees[d,hour,side,stop_i,rr_i,hold_i,mode_i],
            gross[d,hour,side,stop_i,rr_i,hold_i],
            slip_pts[d,hour,side,stop_i,rr_i,hold_i],
            reason[d,hour,side,stop_i,rr_i,hold_i],
            durations[d,hour,side,stop_i,rr_i,hold_i])

def score(path,feepts,grosspts,slippts,reason):
    if not np.isfinite(path).all() or np.min(path)<=-1.0:
        raise ValueError("Nonfinite or catastrophic 1x position")
    n=len(path)
    wealth=np.cumprod(1+path)
    peak=np.maximum.accumulate(np.r_[1.,wealth])[1:]
    log=np.log1p(path)
    monthly=np.expm1(np.bincount(MONTH_IDX,weights=log,minlength=len(MONTH_KEYS)))*100
    annual25=100*np.expm1(log[:NTRAIN].sum())
    annual26=100*np.expm1(log[NTRAIN:].sum())
    winning=path>0
    losing=path<0
    win_count=int(winning.sum())
    lose_count=int(losing.sum())
    grossgains=float(path[winning].sum())
    grosslosses=float(-path[losing].sum())
    return dict(
        trades=n,
        profitable_days=win_count,losing_days=lose_count,flat_days=n-win_count-lose_count,
        profitable_days_2025=int(winning[:NTRAIN].sum()),
        profitable_days_2026=int(winning[NTRAIN:].sum()),
        profitable_days_2025_pct=round(float(100*winning[:NTRAIN].mean()),4),
        profitable_days_2026_pct=round(float(100*winning[NTRAIN:].mean()),4),
        profitable_days_total_pct=round(float(100*winning.mean()),4),
        return_2025_pct=round(float(annual25),6),
        return_2026_pct=round(float(annual26),6),
        net_total_pct=round(float(100*np.expm1(log.sum())),6),
        win_months_2025=int((monthly[:12]>1e-9).sum()),
        win_months_2026=int((monthly[12:]>1e-9).sum()),
        win_months_all=int((monthly>1e-9).sum()),
        worst_month_pct=round(float(monthly.min()),6),
        worst_day_pct=round(float(100*path.min()),6),
        max_closed_dd_pct=round(float(100*np.max(1-wealth/peak)),6),
        profit_factor=round(grossgains/grosslosses,4) if grosslosses else None,
        tp_exits=int((reason==1).sum()),sl_exits=int((reason==2).sum()),
        time_exits=int((reason==3).sum()),
        gross_points=round(float(grosspts.sum()),2),
        total_fee_gst_points=round(float(feepts.sum()),2),
        adverse_slip_points=round(float(slippts.sum()),2))

def max_loss_run(values):
    best=run=0
    for bad in values:
        if bad:run+=1;best=max(best,run)
        else:run=0
    return best

def run():
    OUT.mkdir(parents=True,exist_ok=True)
    m=load()
    entries,directions,ties=prepare(m)
    cube,fees,gross,slippts,why,duration=simulate(
        m.open.to_numpy(float),m.high.to_numpy(float),m.low.to_numpy(float),
        entries,STOPS,RR,HOLDS,COST,SLIP)
    print("RESET1_SIMULATION_CUBE "+json.dumps({
         "dims":list(cube.shape),"weekday_dates":len(DAYS),
         "signal_rule_count":len(RULES),"historical_ties":ties.tolist(),
         "required_entries_per_model":477},sort_keys=True),flush=True)
    records=[]
    for si,rule in enumerate(RULES):
        for hour in range(24):
            signs=directions[si,:,hour]
            for stop_i,stop in enumerate(STOPS):
                for rr_i,rr in enumerate(RR):
                    for hold_i,hold in enumerate(HOLDS):
                        for mode_i,mode in enumerate(MODES):
                            path,fee,grossp,slipp,reason,dur=get_path(
                                cube,fees,gross,slippts,why,duration,
                                signs,hour,stop_i,rr_i,hold_i,mode_i)
                            stat=score(path,fee,grossp,slipp,reason)
                            records.append(dict(
                                rule=rule,hour_ist=hour,stop_pct=float(stop),
                                gross_rr=float(rr),gross_tp_pct=float(stop*rr),
                                hold_max_min=int(hold),cost_model=mode,
                                model=f"{rule}__{hour:02d}__stop{stop:g}__rr{rr:g}__hold{hold}__{mode}",
                                **stat))
    res=pd.DataFrame(records)
    expected=len(RULES)*24*len(STOPS)*len(RR)*len(HOLDS)*len(MODES)
    assert len(res)==expected,(len(res),expected)
    assert res.trades.eq(477).all(),"Not 1/weekday"
    assert (res.profitable_days+res.losing_days+res.flat_days).eq(477).all()
    res.to_csv(OUT/"all_51840_daily_variants.csv",index=False)
    summaries={}
    for mode_i,mode in enumerate(MODES):
        x=res[res.cost_model==mode].copy()
        positives=x[x.return_2025_pct>0]
        if len(positives)>0:
            sorted_2025=positives.sort_values([
                "profitable_days_2025","return_2025_pct","max_closed_dd_pct"],
                 ascending=[False,False,True])
        else:
            sorted_2025=x.sort_values(["return_2025_pct","profitable_days_2025"],
                ascending=[False,False])
        selected=sorted_2025.iloc[0].to_dict()
        si=RULES.index(selected["rule"]);hour=int(selected["hour_ist"])
        stop_i=int(np.where(np.isclose(STOPS,selected["stop_pct"]))[0][0])
        rr_i=int(np.where(np.isclose(RR,selected["gross_rr"]))[0][0])
        hold_i=int(np.where(HOLDS==selected["hold_max_min"])[0][0])
        path,fee,grossp,slipp,reason,durationm=get_path(
             cube,fees,gross,slippts,why,duration,directions[si,:,hour],
             hour,stop_i,rr_i,hold_i,mode_i)
        ledger=pd.DataFrame(dict(
            day_ist=IST_DAYS,year=DAYS.year,
            hour_ist=hour,direction=np.where(directions[si,:,hour]>0,"LONG","SHORT"),
            entry_btcusd=m.open.to_numpy(float)[entries[:,hour]],
            net_account_return_pct=100*path,
            gross_price_points=grossp,fee_gst_price_points=fee,
            adverse_slippage_points=slipp,
            exit_reason=np.where(reason==1,"TP",np.where(reason==2,"SL","TIMEOUT")),
            actual_hold_minutes=durationm,
            month_ist=MONTH_LABELS))
        ledgermonth=ledger.groupby("month_ist",sort=True).agg(
            trades=("day_ist","count"),
            positive_days=("net_account_return_pct",lambda s:int((s>0).sum())),
            negative_days=("net_account_return_pct",lambda s:int((s<0).sum())),
            net_compounded_pct=("net_account_return_pct",lambda s:float(
                100*(np.prod(1+s/100)-1))),
            fee_gst_points=("fee_gst_price_points","sum"),
            gross_points=("gross_price_points","sum")).reset_index()
        neighbor=x[(x.rule==selected["rule"])&(x.hour_ist==hour)&
            (abs(x.stop_pct-selected["stop_pct"])<=.3+1e-9)&
            (abs(x.gross_rr-selected["gross_rr"])<=1.0+1e-9)&
            (x.hold_max_min==selected["hold_max_min"])]
        top_in_sample=x.sort_values("return_2025_pct",ascending=False).head(10)
        dual_year=(x.return_2025_pct>0)&(x.return_2026_pct>0)
        daily_reliable={}
        for pct in (60,70,80):
            z=x[(x.profitable_days_2025_pct>=pct)&
                (x.profitable_days_2026_pct>=pct)&dual_year]
            daily_reliable[str(pct)+"_pct_both_years_and_profit_positive"]=int(len(z))
        summaries[mode]=dict(
            selected_from_2025=selected,
            positive_return_2025_model_count=int(len(positives)),
            positive_return_both_years_hindsight_count=int(dual_year.sum()),
            positive_day_rate_and_return_both_years_counts=daily_reliable,
            selection_paid_fee_gst_points=round(float(fee.sum()),2),
            selection_actual_max_consecutive_losing_days=max_loss_run(path<0),
            neighbor_count=int(len(neighbor)),
            neighbor_positive_2025=int((neighbor.return_2025_pct>0).sum()),
            neighbor_positive_2026=int((neighbor.return_2026_pct>0).sum()),
            neighbor_positive_both=int(((neighbor.return_2025_pct>0)&
                                        (neighbor.return_2026_pct>0)).sum()))
        oracle=x.sort_values("net_total_pct",ascending=False).iloc[0].to_dict()
        summaries[mode]["full_sample_hindsight_not_selected"]=oracle
        ledger.to_csv(OUT/(mode+"_2025_selected_477_daily.csv"),index=False)
        ledgermonth.to_csv(OUT/(mode+"_2025_selected_22_months.csv"),index=False)
        neighbor.to_csv(OUT/(mode+"_2025_selected_neighbors.csv"),index=False)
        top_in_sample.to_csv(OUT/(mode+"_top_2025_in_sample.csv"),index=False)
        print("RESET1_SELECTED_"+mode.upper()+" "+json.dumps(summaries[mode],sort_keys=True),flush=True)
        print("RESET1_MONTHLY_"+mode.upper()+"\n"+ledgermonth.to_string(index=False),flush=True)
    # Expose strongest full-period candidates as explicitly hindsight and for audit only.
    res[res.return_2025_pct.gt(0)&res.return_2026_pct.gt(0)].to_csv(
        OUT/"both_years_positive_hindsight_only.csv",index=False)
    res.sort_values("profitable_days_2025_pct",ascending=False).head(100).to_csv(
        OUT/"top_100_training_winning_day_rate.csv",index=False)
    (OUT/"summary.json").write_text(json.dumps(dict(
        experiment="RESET Step 1: one BTC position every completed IST weekday",
        data_utc_start=str(m.index[0]),data_utc_end=str(m.index[-1]),
        exact_weekdays=477,train_2025_weekdays=260,check_2026_weekdays=217,
        grids={"directions":list(RULES),"entry_hours_ist":list(range(24)),
             "stops_pct":STOPS.tolist(),"reward_multipliers":RR.tolist(),
             "maximum_holds_minutes":HOLDS.tolist(),"fee_modes":list(MODES)},
        comparisons=int(len(res)),capital_exposure="100% notional = 1x, zero leverage",
        assumptions="5 BTC price points slip each side; 0.05% taker each side +18% GST; offer hypothetical only <=30m exit waiver",
        future_data_cautions=[
          "2026 has been studied previously and is not a pristine forward holdout",
          "51,840 model comparisons are severely subject to multiple-testing bias",
          "No 1m OHLC sequence inside bar; stop wins double-touch; real bid/ask/orderbook excluded",
          "Scalper Offer historical activation is NOT verified, no funding or liquidation",
          "Last-hour entries have shorter maximum holds so day ends at 23:59 IST"],
        mode_summaries=summaries),indent=2)+"\n")
    report=["# BTCUSD — Step 1 reset: compulsory one trade EVERY IST weekday",
        "","No +0.2% fixed take-profit. Each of 51,840 combinations opens precisely ONE entry on each of 477 full Monday–Friday IST days. Trading clock and causal direction fixed ex-ante.",
        "","**Daily profit consistency takes priority**, then annual account return, costs, drawdown and 22 monthly results. User's previous objective was NOT rare low-frequency trades.",
        "","## 2025-selected regular Scalper Offer model","",json.dumps(summaries["scalper_offer"],indent=2),
        "","## 2025-selected standard-taker model","",json.dumps(summaries["standard"],indent=2),
        "","## Fixed 2025-selected candidate 22 monthly outcomes under offer","",
        pd.read_csv(OUT/"scalper_offer_2025_selected_22_months.csv").to_markdown(index=False),
        "","## 2025-selected candidate 22 monthly outcomes under standard","",
        pd.read_csv(OUT/"standard_2025_selected_22_months.csv").to_markdown(index=False),
        "","## Caveats","",
        "Historical top-of-51,840 is not a valid independent trading recommendation. 2026 is a research-exposed historical recheck, not truly unseen. Net-account results assume 1x full-notional exposure, fee schedules as modeled, 1m stop-first, 5-point adverse each side; exclude orderbook, funding, liquidation, actual historical Scalper activation."]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("RESET_STEP1_51840_COMPLETE",flush=True)

if __name__=="__main__":run()
