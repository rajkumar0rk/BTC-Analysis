#!/usr/bin/env python3
"""Step 3: test causal direction predictors at fixed 19:00/20:00 IST BTCUSD opens.

All signals use data available strictly BEFORE entry. Every rule can skip a day.
Exact 1m stop-first TP/SL execution with fee-adjusted +0.2% NET account target,
under regular Scalper Offer and standard taker costs at 1x notional.
"""
import json
from pathlib import Path
from itertools import product

import numpy as np
import pandas as pd

import research_btc_daily_opportunity_step1 as s1
import research_btc_daily_target_first_step2 as s2

OUT = Path("analysis/btc_daily_direction_step3")
DAYS = pd.date_range(s1.START,s1.END,freq="B",tz=s1.TZ)
CLOCKS=(19,20)
CLOCK_RULES=("19","20","19_then_20")
STOPS=(0.2,0.3,0.5)
HOLDS=(30,120)
MODES=("offer","standard")
FEE=s1.FEE
SLIP=s1.SLIP
GOAL=s1.GOAL
RULES=(
    "always_long","always_short",
    "mom15","mom60","mom240",
    "mom15_60_agree","mom60_240_agree",
    "ema1h","ema15m","ema_15m_1h_align",
    "revert15","revert60","pullback15_60",
    "range_extreme240","mom15_volume",
    "hour_mom_volume","ema15m_volume",
)

def sign(x):
    return 1 if np.isfinite(x) and x>0 else (-1 if np.isfinite(x) and x<0 else 0)

def ema(s,n):
    return s.ewm(span=n,adjust=False,min_periods=n).mean()

def build_features(m):
    op=m.open.to_numpy(float)
    cl=m.close.to_numpy(float)
    hi=m.high.to_numpy(float)
    lo=m.low.to_numpy(float)
    b5=m[["close","volume"]].resample("5min",label="right",closed="left").agg(
        {"close":"last","volume":"sum"})
    b5n=m.close.resample("5min",label="right",closed="left").count()
    b5=b5.where(b5n.eq(5))
    b5["vol_ratio"]=(b5.volume/b5.volume.shift(1).rolling(20,min_periods=20).mean())
    b15=m.close.resample("15min",label="right",closed="left").last()
    b15n=m.close.resample("15min",label="right",closed="left").count()
    b15=b15.where(b15n.eq(15))
    q15=pd.DataFrame({"close":b15,"ema9":ema(b15,9),"ema21":ema(b15,21)})
    b1=m.close.resample("1h",label="right",closed="left").last()
    b1n=m.close.resample("1h",label="right",closed="left").count()
    b1=b1.where(b1n.eq(60))
    q1=pd.DataFrame({"close":b1,"ema20":ema(b1,20),"ema50":ema(b1,50)})
    result={}
    for day in DAYS:
        ds=day.strftime("%Y-%m-%d")
        daystart=int(m.index.get_indexer([day.tz_convert("UTC")])[0])
        if daystart<0:raise AssertionError("Missing first minute "+ds)
        if (int(m.index.get_indexer([(day+pd.Timedelta(minutes=1439)).tz_convert("UTC")])[0])-daystart)!=1439:
            raise AssertionError("Partial IST day "+ds)
        for hour in CLOCKS:
            i=daystart+60*hour
            clockts=m.index[i]
            closeprev=float(cl[i-1])
            r15=closeprev/float(op[i-15])-1
            r60=closeprev/float(op[i-60])-1
            r240=closeprev/float(op[i-240])-1
            h4=float(np.max(hi[i-240:i]))
            l4=float(np.min(lo[i-240:i]))
            pos=(closeprev-l4)/(h4-l4) if h4>l4 else .5
            # 19:00 IST = 13:30 UTC: 15m bar at 13:30 is closed;
            # 1h bar at 13:00 is closed; no current partial hour allowed.
            h15=q15.loc[:clockts].iloc[-1]
            h1=q1.loc[:clockts].iloc[-1]
            v5=b5.loc[:clockts].iloc[-1]
            t15=0
            t1=0
            if np.isfinite(h15["ema9"]) and np.isfinite(h15["ema21"]):
                t15=1 if h15["close"]>h15["ema9"]>h15["ema21"] else (-1 if h15["close"]<h15["ema9"]<h15["ema21"] else 0)
            if np.isfinite(h1["ema20"]) and np.isfinite(h1["ema50"]):
                t1=1 if h1["close"]>h1["ema20"]>h1["ema50"] else (-1 if h1["close"]<h1["ema20"]<h1["ema50"] else 0)
            result[(ds,hour)]=dict(i=i,day_ist=ds,year=int(day.year),hour=hour,
                r15=r15,r60=r60,r240=r240,range_pos240=pos,
                vol5=float(v5.vol_ratio),trend15=t15,trend1=t1)
    assert len(result)==len(DAYS)*len(CLOCKS)
    return result

def predict(rule,f):
    a,b,c=(sign(f["r15"]),sign(f["r60"]),sign(f["r240"]))
    t15=f["trend15"];t1=f["trend1"];vol=f["vol5"]
    if rule=="always_long":return 1
    if rule=="always_short":return -1
    if rule=="mom15":return a
    if rule=="mom60":return b
    if rule=="mom240":return c
    if rule=="mom15_60_agree":return a if a==b else 0
    if rule=="mom60_240_agree":return b if b==c else 0
    if rule=="ema1h":return t1
    if rule=="ema15m":return t15
    if rule=="ema_15m_1h_align":return t15 if t15==t1 else 0
    if rule=="revert15":return -a if abs(f["r15"])>=.0015 else 0
    if rule=="revert60":return -b if abs(f["r60"])>=.003 else 0
    if rule=="pullback15_60":
        return b if a==-b and abs(f["r15"])>=.0008 and abs(f["r60"])>=.002 else 0
    if rule=="range_extreme240":
        return 1 if f["range_pos240"]>=.8 else (-1 if f["range_pos240"]<=.2 else 0)
    if rule=="mom15_volume":return a if vol>=1.5 else 0
    if rule=="hour_mom_volume":return t1 if t1==a and vol>=1.25 else 0
    if rule=="ema15m_volume":return t15 if vol>=1.25 else 0
    raise KeyError(rule)

def standard_replay(op,hi,lo,daystart,hour,side,stop_pct,hold):
    i=daystart+60*hour
    mid=float(op[i]);entryfill=mid+side*SLIP
    stop=mid*(1-side*stop_pct/100)
    levels=s1.required_mid_exit(mid)
    target=levels["standard_long"] if side>0 else levels["standard_short"]
    reason="timeout"
    j=i
    for j in range(i,i+hold):
        if (lo[j]<=stop if side>0 else hi[j]>=stop):
            midout=min(float(op[j]),stop) if side>0 else max(float(op[j]),stop)
            reason="stop";break
        if (hi[j]>=target if side>0 else lo[j]<=target):
            midout=float(target);reason="target";break
    else:
        j=i+hold
        midout=float(op[j])
    exitfill=midout-side*SLIP
    net=side*(exitfill-entryfill)-FEE*(entryfill+exitfill)
    return dict(account_ret=float(net/entryfill),net_points=float(net),
        exit_reason=reason,hold_minutes=int(j-i),
        eligible_scalper=False,total_fees=float(FEE*(entryfill+exitfill)),
        gross_points=float(side*(midout-mid)))

def outcome_cache(m,features):
    op=m.open.to_numpy(float);hi=m.high.to_numpy(float);lo=m.low.to_numpy(float)
    out={}
    for (day,hour),f in features.items():
        i=f["i"];daystart=i-hour*60
        for stop,hold,side in product(STOPS,HOLDS,(1,-1)):
            # Reuse actual earlier Step 2 implementation for the offer fee case.
            a=s2.simulate_one(op,hi,lo,daystart,hour,side,stop,"net0p2",hold)
            # Use independent target price when standard double-sided fees apply.
            b=standard_replay(op,hi,lo,daystart,hour,side,stop,hold)
            out[(day,hour,stop,hold,side,"offer")]=a
            out[(day,hour,stop,hold,side,"standard")]=b
    return out

def construct_daily(rule,clock,stop,hold,mode,features,outcomes):
    rows=[]
    for day in DAYS:
        ds=day.strftime("%Y-%m-%d")
        opt=(19,) if clock=="19" else ((20,) if clock=="20" else CLOCKS)
        side=0;hour=0
        for h in opt:
            x=predict(rule,features[(ds,h)])
            if x:
                side=x;hour=h;break
        if side:
            entry=outcomes[(ds,hour,stop,hold,side,mode)]
            ret=float(entry["account_ret"])
            pts=float(entry["net_points"])
            reason=entry["exit_reason"]
            duration=int(entry["hold_minutes"])
        else:
            ret=0.;pts=0.;reason="no_trade";duration=0
        rows.append(dict(day_ist=ds,year=int(day.year),hour_ist=hour,
            side=side,exit_reason=reason,account_ret=ret,net_points=pts,
            hold_minutes=duration,goal=ret>=GOAL-1.e-9))
    return pd.DataFrame(rows)

def metrics(z):
    daily=z.account_ret.to_numpy(float)
    factors=1+daily
    wealth=np.cumprod(factors)
    peak=np.maximum.accumulate(np.r_[1.,wealth])[1:]
    trade=z.side.ne(0)
    return dict(eligible_days=len(z),trades=int(trade.sum()),
        trade_day_pct=round(100*float(trade.mean()),3),
        goal_0p2_days=int(z.goal.sum()),
        goal_0p2_pct=round(100*float(z.goal.mean()),3),
        net_win_days=int((daily>0).sum()),
        net_loss_days=int((daily<0).sum()),
        no_trade_days=int((~trade).sum()),
        tp_first=int(z.exit_reason.eq("target").sum()),
        sl_first=int(z.exit_reason.eq("stop").sum()),
        timeout=int(z.exit_reason.eq("timeout").sum()),
        total_net_points=round(float(z.net_points.sum()),2),
        account_return_pct=round(100*float(wealth[-1]-1),5),
        max_closed_dd_pct=round(float(100*np.max(1-wealth/peak)),5),
        worst_day_pct=round(100*float(daily.min()),5))

def evaluate(daily):
    a=metrics(daily[daily.year==2025])
    b=metrics(daily[daily.year==2026])
    total=metrics(daily)
    return a,b,total

def run():
    OUT.mkdir(parents=True,exist_ok=True)
    m=s1.load()
    feats=build_features(m)
    outcomes=outcome_cache(m,feats)
    results=[];selected_records={}
    all_2025_plus=0
    for rule,clock,stop,hold,mode in product(RULES,CLOCK_RULES,STOPS,HOLDS,MODES):
        daily=construct_daily(rule,clock,stop,hold,mode,feats,outcomes)
        y25,y26,total=evaluate(daily)
        if y25["account_return_pct"]>0:all_2025_plus+=1
        key=f"{rule}__{clock}__sl{stop:g}__hold{hold}__{mode}"
        results.append(dict(variant=key,rule=rule,clock=clock,stop_pct=stop,
            hold_min=hold,cost_model=mode,
            trades_2025=y25["trades"],trades_2026=y26["trades"],
            goals_2025=y25["goal_0p2_days"],goals_2026=y26["goal_0p2_days"],
            goals_all=total["goal_0p2_days"],
            coverage_2025=y25["trade_day_pct"],
            return_2025_pct=y25["account_return_pct"],
            return_2026_pct=y26["account_return_pct"],
            return_all_pct=total["account_return_pct"],
            max_closed_dd_pct=total["max_closed_dd_pct"],
            max_2025_dd_pct=y25["max_closed_dd_pct"],
            max_2026_dd_pct=y26["max_closed_dd_pct"],
            losses_2025=y25["net_loss_days"],
            losses_2026=y26["net_loss_days"],
            no_trade_all=total["no_trade_days"],
            tp_first_all=total["tp_first"],
            sl_first_all=total["sl_first"],
            worst_day_pct=total["worst_day_pct"]))
    result=pd.DataFrame(results)
    assert len(result)==len(RULES)*len(CLOCK_RULES)*len(STOPS)*len(HOLDS)*len(MODES)
    result.to_csv(OUT/"all_fixed_predictors.csv",index=False)
    selections={}
    for mode in MODES:
        universe=result[result.cost_model==mode].copy()
        eligible=universe[universe.trades_2025>=45]
        positive=eligible[eligible.return_2025_pct>0]
        if len(positive):
            rank=positive.sort_values(["goals_2025","return_2025_pct","max_2025_dd_pct"],
                ascending=[False,False,True])
        else:
            rank=eligible.sort_values(["return_2025_pct","goals_2025","max_2025_dd_pct"],
                ascending=[False,False,True])
        if len(rank)==0:raise AssertionError("No >=45 trade strategies")
        winner=rank.iloc[0].to_dict()
        daily=construct_daily(winner["rule"],winner["clock"],float(winner["stop_pct"]),
            int(winner["hold_min"]),mode,feats,outcomes)
        daily["month_ist"]=daily.day_ist.str[:7]
        monthly=daily.groupby("month_ist",sort=True).agg(
            trades=("side",lambda x:int(x.ne(0).sum())),
            goal_days=("goal","sum"),
            losing_days=("account_ret",lambda x:int((x<0).sum())),
            net_factor=("account_ret",lambda x:float(np.prod(1+x))),
            ).reset_index()
        monthly["net_pct"]=np.round(100*(monthly.net_factor-1),5)
        monthly=monthly.drop(columns="net_factor")
        selections[mode]=dict(selected_using_2025=winner,
            positive_train_candidates=int(len(positive)),eligible_train_candidates=int(len(eligible)),
            performance_2025=metrics(daily[daily.year==2025]),
            performance_2026=metrics(daily[daily.year==2026]),
            performance_total=metrics(daily),
            winning_months=int((monthly.net_pct>0).sum()))
        daily.to_csv(OUT/f"{mode}_2025_selected_daily.csv",index=False)
        monthly.to_csv(OUT/f"{mode}_2025_selected_monthly.csv",index=False)
        selected_records[mode]=(daily,monthly)
        print("STEP3_SELECTED_"+mode.upper()+" "+json.dumps(selections[mode],sort_keys=True),flush=True)
        print("STEP3_MONTHLY_"+mode.upper()+"\n"+monthly.to_string(index=False),flush=True)
        # rank by total only for DIAGNOSTICS, not an independently selected strategy
        bestfull=universe.sort_values("return_all_pct",ascending=False).iloc[0].to_dict()
        selections[mode]["full_sample_oracle_not_selected"]=bestfull
        print("STEP3_HINDSIGHT_"+mode.upper()+" "+json.dumps(bestfull,sort_keys=True),flush=True)
        y26positive=int((universe.return_2026_pct>0).sum())
        selections[mode]["positive_2026_variants_with_hindsight"]=y26positive
    result.sort_values(["return_2025_pct"],ascending=False).head(50).to_csv(
        OUT/"top_2025_variants_all_fees.csv",index=False)
    base=result[result.rule.isin(["always_long","always_short"])].sort_values(
        ["cost_model","return_2025_pct"],ascending=[True,False])
    base.to_csv(OUT/"unconditional_baselines.csv",index=False)
    (OUT/"summary.json").write_text(json.dumps(dict(
        selections=selections,total_variants=int(len(result)),
        preregistered_direction_rules=list(RULES),
        fixed_clock_rules=list(CLOCK_RULES),stop_pct=list(STOPS),
        max_holds=list(HOLDS),eligible_weekdays=len(DAYS),
        test_coverage="2025-01-02 .. 2026-10-30, Monday-Friday Asia/Kolkata",
        economics="1x BTCUSD account notional; 0.05% taker/side + GST; 5 BTC points adverse slip/side; regular <=30m closing-fee-waiver hypothetical",
        historical_cautions=[
            "2025 is selection/in-sample, 2026 was used in previous BTC research and is not clean unseen forward data",
            "Threshold crossing and same-bar stop-first from 1m candles, no tick-level order sequencing",
            "Scalper Offer may not have been available or activated throughout 2025-2026",
            "No funding, real spread/order book impact, liquidation or skipped fills"],),indent=2)+"\n")
    report=["# Step 3 — Causal 19:00/20:00 IST BTCUSD direction signal screening",
            "","**No oracle direction.** Pre-entry features only, 1x account exposure, 477 Mon-Fri IST days, max 1 trade/day and no trade allowed. Fee-correct net +0.2% target; stop-first minute execution.",
            "","2025-only selection among configurations with >=45 trades and positive 2025 account return. 2026 historical recheck is NOT pristine after previous research; do not claim validation.",
            "","## Best 2025-selected Scalper Offer",json.dumps(selections["offer"],indent=2),
            "","## Offer selected monthly","",
            selected_records["offer"][1].to_markdown(index=False),
            "","## Best 2025-selected standard taker",json.dumps(selections["standard"],indent=2),
            "","## Standard selected monthly","",
            selected_records["standard"][1].to_markdown(index=False),
            "","## Fixed predictors ranked by 2025 (first 50)","",
            result.sort_values(["return_2025_pct"],ascending=False).head(50).to_markdown(index=False),
            "","## Warnings","",
            "No actual forward validation. Multiple rule screening can overfit even when 2025-only selection is enforced. The user goal is daily +0.2% NET, not an intrabar hindsight-label success rate.",
            ""]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report))
    print("STEP3_PREDICTOR_SEARCH_COMPLETED",flush=True)

if __name__=="__main__":
    run()
