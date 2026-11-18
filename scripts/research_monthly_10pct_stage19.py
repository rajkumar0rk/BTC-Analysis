#!/usr/bin/env python3
"""Stage 19 — BTCUSD MULTI-TRADE / MONTHLY >=10% AFTER COSTS research.

New, causally observable intraday 5-minute patterns. Entry immediately after
fully CLOSED 5m bar at next 1m OPEN. 1m OHLC stop-first replay. Multiple trades
per day, one open at a time per strategy; LONG and SHORT. Sweeps, RSI2 reclaims,
breakouts, EMA pullback/engulf, volatility compression.

Inputs: authentic Delta India 1m BTCUSD candles as in other stages.
Standard taker model: 0.05% per side + 18% GST + 5 BTC quote points adverse
slippage per side. Funding / order book impact not known or modeled.

No targets can force 10% profits. Test a FIXED target: >=10% account NAV in
EVERY complete month (2025 all 12 and 2026 Jan-Oct 10), not aggregate return.
Report account equity / risk / leverage, positive months and worst drawdown.
2026 has been previously inspected: NOT a pristine untouched holdout.

Research only; risk 3%-5% per trade is included for stress-testing, not advice.
"""
from pathlib import Path
import json
import math
import numpy as np
import pandas as pd
from numba import njit
from research_every_candle_200 import read_archive, FEE, SLIPPAGE

OUT=Path("analysis/institutional_discovery_stage19_monthly_10pct")
RISK_LEVELS=(.005,.01,.02,.03,.05)
MAX_LEVERAGE=(5.,10.,20.)
REWARDS=(2.,3.)
HOLDS=(120,240)
STOPMODES=("atr1p5","structure3")
TREND_FILTERS=("any","hour_align")
PATS=("range_breakout","sweep_reversal","rsi2_reclaim",
      "ema20_pullback","compression_break","trend_engulf")
MIN_STOP=120.
MAX_STOP=1400.
MONTHS=pd.period_range("2025-01","2026-11",freq="M").astype(str)
START_CAPITAL=100.

def features(f,seg_start,seg_end):
    b=f[["open","high","low","close","volume"]].resample(
        "5min",label="right",closed="left").agg({
        "open":"first","high":"max","low":"min","close":"last","volume":"sum"})
    n=f.close.resample("5min",label="right",closed="left").count()
    b["cnt"]=n
    b["complete"]=n.rolling(70,min_periods=70).min().eq(5)
    span=(b.high-b.low).replace(0,np.nan)
    b["range"]=span
    b["range_ref"]=span.shift(1).rolling(24,min_periods=24).median()
    b["vr"]=b.volume/b.volume.shift(1).rolling(24,min_periods=24).mean().replace(0,np.nan)
    b["rr"]=span/b.range_ref
    b["loc"]=(b.close-b.low)/span
    b["body"]=(b.close-b.open).abs()/span
    b["prev12H"]=b.high.shift(1).rolling(12,min_periods=12).max()
    b["prev12L"]=b.low.shift(1).rolling(12,min_periods=12).min()
    b["prev24H"]=b.high.shift(1).rolling(24,min_periods=24).max()
    b["prev24L"]=b.low.shift(1).rolling(24,min_periods=24).min()
    b["prev6H"]=b.high.shift(1).rolling(6,min_periods=6).max()
    b["prev6L"]=b.low.shift(1).rolling(6,min_periods=6).min()
    b["support3"]=b.low.rolling(3,min_periods=3).min()
    b["resist3"]=b.high.rolling(3,min_periods=3).max()
    cprev=b.close.shift(1)
    tr=pd.concat((b.high-b.low,(b.high-cprev).abs(),
                  (b.low-cprev).abs()),axis=1).max(axis=1)
    b["atr14"]=tr.rolling(14,min_periods=14).mean()
    b["ema20"]=b.close.ewm(span=20,adjust=False).mean()
    b["ema50"]=b.close.ewm(span=50,adjust=False).mean()
    diff=b.close.diff()
    avg_up=diff.clip(lower=0).ewm(alpha=.5,adjust=False,min_periods=2).mean()
    avg_dn=(-diff.clip(upper=0)).ewm(alpha=.5,adjust=False,min_periods=2).mean()
    b["rsi2"]=100*avg_up/(avg_up+avg_dn).replace(0,np.nan)
    b["std20"]=b.close.rolling(20,min_periods=20).std()
    b["sma20"]=b.close.rolling(20,min_periods=20).mean()
    prev3mean=(span.shift(1)+span.shift(2)+span.shift(3))/3
    b["quiet_prev3"]=prev3mean<=.75*b.range_ref

    # Current hour close is known at a 5m-close timestamp, otherwise the
    # previously completed 1h bar. No partial 1h candles.
    h=f[["open","high","low","close"]].resample(
        "1h",label="right",closed="left").agg({
        "open":"first","high":"max","low":"min","close":"last"})
    count=f.close.resample("1h",label="right",closed="left").count()
    h["valid"]=count.rolling(30,min_periods=30).min().eq(60)
    h["ema20"]=h.close.ewm(span=20,adjust=False).mean()
    h["ema50"]=h.close.ewm(span=50,adjust=False).mean()
    hour=h.reindex(b.index,method="ffill")
    b["hour_bull"]=(hour.valid & (hour.close>hour.ema20)&
                    (hour.ema20>hour.ema50)).fillna(False).to_numpy(bool)
    b["hour_bear"]=(hour.valid & (hour.close<hour.ema20)&
                    (hour.ema20<hour.ema50)).fillna(False).to_numpy(bool)

    bull=(b.close>b.open)&(b.loc>=.65)&(b.body>=.40)
    bear=(b.close<b.open)&(b.loc<=.35)&(b.body>=.40)
    signals={
       "range_breakout": (
           bull&(b.close>b.prev24H)&(b.vr>=1.15)&(b.rr>=1.2),
           bear&(b.close<b.prev24L)&(b.vr>=1.15)&(b.rr>=1.2)),
       "sweep_reversal": (
           bull&(b.low<b.prev24L)&(b.close>b.prev24L),
           bear&(b.high>b.prev24H)&(b.close<b.prev24H)),
       "rsi2_reclaim": (
           bull&(b.rsi2.shift(1)<5)&(b.rsi2>=25)&
           (b.low.shift(1)<(b.sma20.shift(1)-1.6*b.std20.shift(1))),
           bear&(b.rsi2.shift(1)>95)&(b.rsi2<=75)&
           (b.high.shift(1)>(b.sma20.shift(1)+1.6*b.std20.shift(1)))),
       "ema20_pullback": (
           bull&(b.ema20>b.ema50)&(b.low<=b.ema20)&(b.close>b.ema20),
           bear&(b.ema20<b.ema50)&(b.high>=b.ema20)&(b.close<b.ema20)),
       "compression_break": (
           bull&b.quiet_prev3&(b.close>b.prev6H)&(b.rr>=1.3),
           bear&b.quiet_prev3&(b.close<b.prev6L)&(b.rr>=1.3)),
       "trend_engulf": (
           bull&(b.ema20>b.ema50)&(b.close.shift(1)<b.open.shift(1))&
           (b.close>b.open.shift(1)),
           bear&(b.ema20<b.ema50)&(b.close.shift(1)>b.open.shift(1))&
           (b.close<b.open.shift(1)))
    }
    idx=f.index.get_indexer(b.index)
    events=[]
    unix=f.time.to_numpy(np.int64)
    O=f.open.to_numpy(float)
    for pat in PATS:
        longmask,shortmask=signals[pat]
        for side,mask in ((1,longmask),(-1,shortmask)):
            valid=(mask&b.complete&b.atr14.gt(0)).fillna(False)
            for j in np.flatnonzero(valid.to_numpy(bool)):
                k=int(idx[j])
                if k<0 or k<seg_start[k]+300 or k+max(HOLDS)>=seg_end[k]:
                    continue
                price=O[k]
                atr=float(b.atr14.iat[j])
                fixedrisk=max(120.,1.5*atr)
                structbuffer=max(10.,.1*atr)
                stopstruct=(float(b.support3.iat[j])-structbuffer if side==1 else
                            float(b.resist3.iat[j])+structbuffer)
                riskstruct=side*(price-stopstruct)
                for st,initialrisk in (("atr1p5",fixedrisk),
                                       ("structure3",riskstruct)):
                    if np.isfinite(initialrisk) and MIN_STOP<=initialrisk<=MAX_STOP:
                        events.append((pat,side,int(k),int(unix[k]),float(price),
                             float(initialrisk),float(atr),st,
                             bool(b.hour_bull.iat[j] if side==1 else b.hour_bear.iat[j])))
    e=pd.DataFrame(events,columns=["pattern","side","k","entry_unix",
             "entry_price","risk_pts","atr5","stop_mode","hour_agrees"])
    if e.empty:raise RuntimeError("No signals found")
    return e.sort_values(["pattern","stop_mode","k","side"]),b

@njit(cache=True)
def replay(op,hi,lo,cl,entry_idx,side,risk,rr,hold):
    entry=op[entry_idx]
    stop=entry-side*risk
    target=entry+side*rr*risk
    for j in range(entry_idx,entry_idx+hold):
        stop_hit=(lo[j]<=stop if side==1 else hi[j]>=stop)
        target_hit=(hi[j]>=target if side==1 else lo[j]<=target)
        if stop_hit:
            exitmid=min(op[j],stop) if side==1 else max(op[j],stop)
            reason=0
            break
        if target_hit:
            exitmid=target
            reason=1
            break
    else:
        j=entry_idx+hold-1
        exitmid=cl[j]
        reason=2
    fin=entry+side*SLIPPAGE
    fout=exitmid-side*SLIPPAGE
    netpts=side*(fout-fin)-FEE*(fin+fout)
    return j,netpts/risk,netpts,reason

def simulate(f,e):
    op=f.open.to_numpy(float)
    hi=f.high.to_numpy(float)
    lo=f.low.to_numpy(float)
    cl=f.close.to_numpy(float)
    unix=f.time.to_numpy(np.int64)
    logs=[]
    for pat in PATS:
        for filt in TREND_FILTERS:
            for st in STOPMODES:
                subset=e[(e.pattern==pat)&(e.stop_mode==st)].copy()
                if filt=="hour_align":
                    subset=subset[subset.hour_agrees]
                subset=subset.sort_values(["k","side"],kind="stable")
                for rr in REWARDS:
                    for hold in HOLDS:
                        busy=-1
                        for z in subset.itertuples(index=False):
                            k=int(z.k)
                            if k<=busy:continue
                            j,netR,netpts,why=replay(op,hi,lo,cl,k,
                                int(z.side),float(z.risk_pts),float(rr),int(hold))
                            busy=j
                            logs.append(dict(pattern=pat,trend_filter=filt,
                                stop_mode=st,reward_R=rr,hold_min=hold,
                                k=k,entry_unix=int(z.entry_unix),
                                exit_unix=int(unix[j]),
                                entry_price=float(z.entry_price),
                                risk_pts=round(float(z.risk_pts),4),
                                net_pts=round(float(netpts),4),
                                net_R=round(float(netR),6),
                                direction="LONG" if z.side==1 else "SHORT",
                                reason=["stop","target","timeout"][why]))
    x=pd.DataFrame(logs)
    if x.empty:raise ValueError("No completed trades")
    x["exit_month_ist"]=pd.to_datetime(x.exit_unix,unit="s",utc=True).dt.tz_convert(
        "Asia/Kolkata").dt.strftime("%Y-%m")
    return x

def all_account_models(tr):
    annual=[]
    monthly=[]
    key=["pattern","trend_filter","stop_mode","reward_R","hold_min"]
    for setting,g in tr.groupby(key,sort=True):
        g=g.sort_values(["exit_unix","entry_unix"],kind="stable")
        month_sorted=g.exit_month_ist.to_numpy(str)
        riskpoints=g.risk_pts.to_numpy(float)
        entryprices=g.entry_price.to_numpy(float)
        normalized=g.net_R.to_numpy(float)
        for wanted_risk in RISK_LEVELS:
            for levercap in MAX_LEVERAGE:
                # Effective fraction of account risk at STOP is lower if
                # notional exposure capped at permitted gross leverage.
                # This handles BTC price regime drift and capital feasibility.
                riskused=np.minimum(wanted_risk,levercap*riskpoints/entryprices)
                returns=riskused*normalized
                if (returns<=-1).any():
                    continue
                pnl_by_month={}
                count_by_month={}
                for m in MONTHS:
                    idx=np.flatnonzero(month_sorted==m)
                    pnl_by_month[m]=float(np.prod(1.+returns[idx])-1) if len(idx) else 0.
                    count_by_month[m]=len(idx)
                cap=100.
                peak=cap
                worstdd=0.
                largest_gross_leverage=float((entryprices*riskused/riskpoints).max())
                for z in returns:
                    cap*=1.+z
                    peak=max(peak,cap)
                    worstdd=max(worstdd,100*(1-cap/peak))
                totalp=0
                highrisk=False
                for m in MONTHS:
                    v=pnl_by_month[m]
                    n=count_by_month[m]
                    if v>=.10-1e-9:stat=">=10%"
                    elif n==0:stat="No trades"
                    elif v>0:stat="Profit <10%"
                    else:stat="Loss" if v<0 else "Flat"
                    if stat==">=10%":totalp+=1
                    monthly.append(dict(zip(key,setting),
                        target_trade_risk_pct=int(wanted_risk*1000)/10,
                        max_notional_leverage=levercap,
                        month_ist=m,trades=n,
                        net_account_return_pct=round(100*v,4),
                        status=stat))
                m25=[pnl_by_month[m] for m in MONTHS[:12]]
                m26=[pnl_by_month[m] for m in MONTHS[12:22]]
                return25=float((np.prod(1+np.array(m25))-1)*100)
                return26=float((np.prod(1+np.array(m26))-1)*100)
                gate25=sum(v>=.1-1e-9 for v in m25)
                gate26=sum(v>=.1-1e-9 for v in m26)
                positive25=sum(v>1e-9 for v in m25)
                positive26=sum(v>1e-9 for v in m26)
                annual.append(dict(zip(key,setting),
                    target_trade_risk_pct=int(wanted_risk*1000)/10,
                    max_notional_leverage=levercap,
                    trades=len(g),trades_2025=sum(count_by_month[m] for m in MONTHS[:12]),
                    trades_2026=sum(count_by_month[m] for m in MONTHS[12:22]),
                    months_10pct_2025=int(gate25),
                    months_10pct_2026=int(gate26),
                    months_positive_2025=int(positive25),
                    months_positive_2026=int(positive26),
                    months_negative_2025=int(sum(v<0 for v in m25)),
                    months_negative_2026=int(sum(v<0 for v in m26)),
                    worst_month_2025_pct=round(100*min(m25),3),
                    worst_month_2026_pct=round(100*min(m26),3),
                    nav_return_2025_pct=round(return25,3),
                    nav_return_2026_pct=round(return26,3),
                    max_trade_equity_drawdown_pct=round(worstdd,3),
                    observed_max_gross_leverage=round(largest_gross_leverage,3),
                    months_all_10pct=bool(gate25==12 and gate26==10)))
    return pd.DataFrame(monthly),pd.DataFrame(annual)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    f,start,end,q=read_archive()
    events,b=features(f,start,end)
    ledger=simulate(f,events)
    monthly,all_models=all_account_models(ledger)
    events.to_csv(OUT/"entries.csv.gz",compression="gzip",index=False)
    ledger.to_csv(OUT/"trades.csv.gz",compression="gzip",index=False)
    monthly.to_csv(OUT/"monthly_net_account_returns.csv",index=False)
    all_models.to_csv(OUT/"config_comparison.csv",index=False)
    # Fixed primary ranking uses 2025 only, then reports all 2026 results
    # to avoid retroactive 2026 tuning; repeated prior exposures still apply.
    selected=all_models.sort_values(
        ["months_10pct_2025","months_positive_2025",
         "nav_return_2025_pct","max_trade_equity_drawdown_pct"],
        ascending=[False,False,False,True],kind="stable")
    safe=selected[selected.max_trade_equity_drawdown_pct<=30]
    if safe.empty:
        safe=selected
    choice=safe.iloc[0]
    idcols=["pattern","trend_filter","stop_mode","reward_R","hold_min",
        "target_trade_risk_pct","max_notional_leverage"]
    choice_m=monthly
    for col in idcols:
        choice_m=choice_m[choice_m[col]==choice[col]]
    choice_m.to_csv(OUT/"selected_monthly.csv",index=False)
    selected.head(30).to_csv(OUT/"top_2025_ranked.csv",index=False)
    meta=dict(source="Delta Exchange India BTCUSD 1m historic candles",
        observed_minute_candles=len(f),missing_minutes=q["missing_minutes"],
        event_rows=len(events),trade_rows=len(ledger),
        pattern_families=list(PATS),signal_models=6*2*2*2*2,
        risk_settings_percent=[100*i for i in RISK_LEVELS],
        leverage_caps=list(MAX_LEVERAGE),
        account_scenarios=len(all_models),
        exact_10pct_every_complete_month=int(all_models.months_all_10pct.sum()),
        selected_2025_only=choice.to_dict(),
        tested_months="2025 January-December, 2026 January-October; 2026 Nov partial only",
        risk_model="fractional BTC sizing; capital PNL netR*min(risk_pct, max_leverage*stopDistance/entryPrice)",
        costs=dict(taker_fee_each_side_pct=.05,fee_GST_pct=18,slip_BTCpoints_each_side=5),
        important_limitations=[
           "All historical months have been examined during prior research; NOT a blind OOS test",
           "No guarantee every future month will gain >=10%; target is extremely aggressive",
           "Real contracts have discrete lot sizes, minimum margin, exchange risk limits and liquidation",
           "No funding, actual bid-ask spread, market impact or forced liquidation modeled",
           "1m OHLC stop-first, adverse gap stops, trades enter only AFTER 5m completion",
           "One position open at a time per independent setting, no fixed trade/day limit",
           "Trade risk 3% or 5% can produce large drawdowns and is not recommended",
           "Maximum leverage cap is an assumption, not confirmation actual position can open",
           "2026-10-31 entire UTC day missing, November 2026 ends on 16th",
           "Realized PNL is counted in the actual IST EXIT month",
           "No-trade months count as misses of the 10% target",
           "Every scenario's monthly return is AFTER modeled taker/GST/slippage costs",
           "Equity drawdown sampled on each trade close; OPEN position drawdowns may be worse"])
    (OUT/"quality.json").write_text(json.dumps(meta,indent=2,default=str)+"\n")
    cols=["pattern","trend_filter","stop_mode","reward_R","hold_min",
        "target_trade_risk_pct","max_notional_leverage","trades",
        "months_10pct_2025","months_10pct_2026","months_positive_2025",
        "months_positive_2026","worst_month_2025_pct","worst_month_2026_pct",
        "nav_return_2025_pct","nav_return_2026_pct",
        "max_trade_equity_drawdown_pct"]
    report=[
        "# Stage19 — Find at least +10% net BTC account return EVERY calendar month",
        "",
        "## Hard target",
        "At least 10% account NAV return after taker fees/GST/slippage in",
        "every COMPLETE month of 2025 and Jan–Oct 2026. Zero-trade and",
        "negative months never pass. No requirement of limited trades/day.",
        "",
        "## Methods",
        "6 fully specified 5m intraday price action patterns, 1H confirm",
        "optional, structure or volatility stops, 2R/3R targets, 2h/4h max",
        "holds, every 1m candle checks exits, one open position at once.",
        "Account leverage cap: 5x/10x/20x; risk budget: 0.5/1/2/3/5 percent.",
        "",
        f"**Strategies achieving 10% in every complete month: {meta['exact_10pct_every_complete_month']} / {len(all_models)}**",
        "",
        "## Best ranked on 2025 only, then 2026 comparison",
        selected.head(20)[cols].to_markdown(index=False),"",
        "## Best drawdown-bounded 2025 candidate monthly account returns",
        choice_m.to_markdown(index=False),"",
        "## Limitations",
        *["- "+v for v in meta["important_limitations"]],"",
        "All result files committed. Raw trade and entry ledgers stored as GitHub Actions artifacts.",
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("STAGE19_COMPLETE "+json.dumps({
        "candles":len(f),"entries":len(events),"trade_rows":len(ledger),
        "models":len(all_models),"all_months_10pct":meta["exact_10pct_every_complete_month"]}))
    print("TOP_2025\n"+selected.head(18)[cols].to_string(index=False))
    print("SELECTED_MONTHLY\n"+choice_m.to_string(index=False))
if __name__=="__main__":
    main()
