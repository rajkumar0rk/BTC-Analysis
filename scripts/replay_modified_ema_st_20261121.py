#!/usr/bin/env python3
"""Research-only modification of *existing* EMA20 + Supertrend(10,3) strategy.

Preserves original confirmed 15M/1H EMA-reclaim entry (plus optional stronger
filters). Tests parameterized initial stops (fixed, ATR, Supertrend line),
break-even-after-R, fixed targets and/or 1M trailing, and confirmed Supertrend
flip exits. Intrabar order is NOT fabricated: standing stop is checked before
new 1M trailing updates, which only become active the following minute.
When both standing stop and limit target touch in one 1M candle, the stop wins
conservatively; ambiguous same-minute count is surfaced.

Nominal, fee-aware P&L: 0.05% taker each side, 18% GST on fees, one
adverse native tick at each fill, 0.001 BTC / 0.01 ETH per trade.
No funding, spread, portfolio margin, slippage beyond one tick,
mark-price liquidation or maker-fill assumptions. Do not deploy from results.
Research splits report 2025 and Jan-Oct 2026, and rank on 2025 only.
"""
import json,sys
from pathlib import Path
import numpy as np
import pandas as pd
from numba import njit

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from replay_ema_st_15m_entries_1m_exits_20261121 import load
from ema_st_entry_quality_oos_20261121 import aggregate,adx14,all_signals

OUT=ROOT/"analysis"/"ema_st_modified_atr_trail_20261121"
OUT.mkdir(parents=True,exist_ok=True)
ENTRY_CUTOFF=int(pd.Timestamp("2026-11-01",tz="UTC").timestamp())
FEERATE=0.0005
GST=0.18
GATES=("baseline","higher_ST","ema_slope3_and_higher_ST",
       "candle_body40","atr_ratio_1p2","ADX25")
# name, stop_kind (fixed=0, ATR=1, Supertrend-line=2), stop_arg,
# profit_R (0=no hard TP), BE_activation_R (0=disabled),
# trail_activation_R (0=disabled), trail_distance_R,
# exit_on_confirmed_ST_flip (0/1).
MODES=(
 ("fixed_200_100",0,100.0,2.0,0.,0.,0.,0),
 ("fixed_900_300",0,300.0,3.0,0.,0.,0.,0),
 ("ATR1p0_TP3R",1,1.0,3.0,0.,0.,0.,0),
 ("ATR1p5_TP3R",1,1.5,3.0,0.,0.,0.,0),
 ("ATR2p0_TP3R",1,2.0,3.0,0.,0.,0.,0),
 ("ATR1p5_TP3R_flip",1,1.5,3.0,0.,0.,0.,1),
 ("ATR1p5_TP3R_BE1R",1,1.5,3.0,1.,0.,0.,0),
 ("ATR2_TP3R_BE1R",1,2.,3.0,1.,0.,0.,0),
 ("ATR2_TP4R_BE1R",1,2.,4.0,1.,0.,0.,0),
 ("ATR1p5_trail_1R_0p5R",1,1.5,0.,0.,1.,0.5,0),
 ("ATR1p5_trail_2R_1R",1,1.5,0.,0.,2.,1.,0),
 ("ATR1p5_trail_2R_1R_flip",1,1.5,0.,0.,2.,1.,1),
 ("ATR2_trail_2R_1R",1,2.,0.,0.,2.,1.,0),
 ("ATR2_trail_2R_1R_flip",1,2.,0.,0.,2.,1.,1),
 ("ATR2_trail_2R_1R_BE1R",1,2.,0.,1.,2.,1.,0),
 ("ATR2_trail_1R_0p7R_flip",1,2.,0.,0.,1.,0.7,1),
 ("ATR2_TP4R_trail_2R_1R",1,2.,4.,0.,2.,1.,0),
 ("ATR2_TP5R_trail_2R_1R",1,2.,5.,0.,2.,1.,0),
 ("STline50_TP3R",2,50.,3.,0.,0.,0.,0),
 ("STline50_trail_2R_1R",2,50.,0.,0.,2.,1.,0),
 ("STline50_trail_2R_1R_flip",2,50.,0.,0.,2.,1.,1),
)
@njit
def core(op,hi,lo,cl,clock,signal,atr_st,st_line,flipdir,
         asset_eth,stopkind,stoparg,profit_r,be_r,activation_r,distance_r,
         use_flip,tick,qty,fee_rate,gst,entry_cutoff,maxtrades):
    eidx=np.empty(maxtrades,np.int64)
    xidx=np.empty(maxtrades,np.int64)
    enter=np.empty(maxtrades,np.float64)
    leave=np.empty(maxtrades,np.float64)
    sideout=np.empty(maxtrades,np.int8)
    riskpts=np.empty(maxtrades,np.float64)
    resultcode=np.empty(maxtrades,np.int8) # 1 TP, 2 stop, 3 STflip, 4 trail stop
    costs=np.empty(maxtrades,np.float64)
    nets=np.empty(maxtrades,np.float64)
    ambiguity=0
    too_big_risk=0
    entries_skipped=0
    pos=0
    j0=0; ep=0.; stop=0.; target=0.; best=0.; risk=0.
    entered=0
    n=0
    for j in range(len(op)):
        # A new signal cannot enter during an existing position. The signal
        # itself is calculated from a COMPLETED 15M/1H candle.
        sg=signal[j]
        if sg!=0 and clock[j]<entry_cutoff:
            if pos!=0:
                entries_skipped+=1
            else:
                e=float(op[j])+sg*tick
                if stopkind==0:
                    d=stoparg*(1.0 if not asset_eth else e/80000.)
                elif stopkind==1:
                    d=stoparg*atr_st[j]
                else:
                    buffer=stoparg*(1.0 if not asset_eth else e/80000.)
                    d=sg*(e-(st_line[j]-sg*buffer))
                if d>tick and np.isfinite(d) and np.isfinite(e):
                    # nearest exchange tick for protective risk distance
                    d=max(tick,np.floor(d/tick+0.5)*tick)
                    pstop=e-sg*d
                    ptp=(e+sg*profit_r*d) if profit_r>0 else 0.
                    pos=int(sg)
                    ep=e
                    stop=pstop
                    target=ptp
                    best=e
                    risk=d
                    j0=j
                    entered+=1
                    if d/e>=0.0075:
                        too_big_risk+=1
        if pos==0:continue
        # Existing protection on each 1M minute first: gap-crossing at OPEN.
        o=op[j]
        outcome=0
        x=0.
        if (pos==1 and o<=stop) or (pos==-1 and o>=stop):
            outcome=2
            x=o-pos*tick
        elif profit_r>0 and ((pos==1 and o>=target) or (pos==-1 and o<=target)):
            outcome=1
            x=target-pos*tick # conservatively do not claim favorable gap improvement
        elif use_flip and j>j0 and flipdir[j]==pos:
            outcome=3
            x=o-pos*tick
        else:
            if pos==1:
                hits=lo[j]<=stop
                hitt=profit_r>0 and hi[j]>=target
            else:
                hits=hi[j]>=stop
                hitt=profit_r>0 and lo[j]<=target
            if hits and hitt:
                ambiguity+=1
                outcome=2
                x=stop-pos*tick # stop first conservatively
            elif hits:
                outcome=4 if activation_r>0 and stop!=ep-pos*risk else 2
                x=stop-pos*tick
            elif hitt:
                outcome=1
                x=target-pos*tick
        if outcome>0:
            if n>=maxtrades:
                raise ValueError("maxtrades overflow")
            eidx[n]=j0
            xidx[n]=j
            enter[n]=ep
            leave[n]=x
            sideout[n]=pos
            riskpts[n]=risk
            resultcode[n]=outcome
            # Full notional fee+GST; each side is taker. Includes 1 tick
            # adverse execution on top of that fee.
            cost=(ep+max(x,0.))*fee_rate*(1.+gst)*qty
            pnl=(x-ep)*pos*qty-cost
            nets[n]=pnl
            costs[n]=cost
            n+=1
            pos=0
        else:
            # No standing barrier touched; update stop AFTER minute completion,
            # effective only on the NEXT 1M bar.
            if pos==1:
                best=max(best,hi[j])
            else:
                best=min(best,lo[j])
            favorable=(best-ep)*pos
            if be_r>0 and favorable>=be_r*risk:
                # "Break even" includes approximate round-trip taker fees + GST.
                cstop=ep+pos*(2*ep*fee_rate*(1.+gst)+2*tick)
                if pos==1:stop=max(stop,cstop)
                else:stop=min(stop,cstop)
            if activation_r>0 and favorable>=activation_r*risk:
                tstop=best-pos*distance_r*risk
                if pos==1:stop=max(stop,tstop)
                else:stop=min(stop,tstop)
    return (eidx[:n],xidx[:n],enter[:n],leave[:n],sideout[:n],riskpts[:n],
            resultcode[:n],costs[:n],nets[:n],
            ambiguity,too_big_risk,entries_skipped,entered,int(pos!=0))

def summary(asset,tf,gate,mode,output,minute):
    ei,xi,ep,xp,side,risk,reason,fee,net,amb,bigrisk,skipped,entered,unfinished=output
    months=pd.to_datetime(minute.time.iloc[xi].to_numpy(),unit="s",utc=True).tz_convert("Asia/Kolkata").strftime("%Y-%m")
    years=np.where(minute.time.iloc[ei].to_numpy()<int(pd.Timestamp("2026-01-01",tz="UTC").timestamp()),2025,2026)
    d={"asset":asset,"timeframe":tf,"filter":gate,"mode":mode,
       "trades":len(net),"attempted_entries":entered,"unresolved":unfinished,
       "ignored_signals_while_occupied":skipped,"ambiguous_stop_target":amb,
       "entries_with_stop_ge_0p75pct":bigrisk,
       "net_usd_per_one_contract":round(float(np.sum(net)),3),
       "average_net_usd_per_contract":round(float(np.mean(net)),5) if len(net) else None,
       "fees_gst_usd_per_contract":round(float(np.sum(fee)),3)}
    if len(net):
        w=float(np.sum(net[net>0]));l=float(-np.sum(net[net<0]))
        d["net_profit_factor"]=round(w/l,4) if l else None
        d["net_win_rate_pct"]=round(float(np.mean(net>0)*100),2)
        d["median_hold_min"]=round(float(np.median(xi-ei)),1)
        d["avg_hold_min"]=round(float(np.mean(xi-ei)),1)
        d["avg_stop_pct"]=round(float(np.mean(risk/ep)*100),3)
        d["target_exits"]=int(np.sum(reason==1))
        d["initial_stop_exits"]=int(np.sum(reason==2))
        d["flip_exits"]=int(np.sum(reason==3))
        d["trailed_stop_exits"]=int(np.sum(reason==4))
        # BTC-equivalent points at entry for fair BTC/ETH comparison.
        equiv=net/(0.001 if asset=="BTC" else 0.01)*(1.0 if asset=="BTC" else 80000./ep)
        d["avg_net_equivalent_points"]=round(float(np.mean(equiv)),2)
        curve=np.cumsum(net)
        peak=np.maximum.accumulate(np.r_[0.,curve])[1:]
        d["max_closed_drawdown_usd_per_contract"]=round(float(np.max(peak-curve)),3)
        mframe=pd.DataFrame({"month":months,"net":net})
        monthly=mframe.groupby("month").net.sum()
        d["profitable_months"]=int((monthly>0).sum())
        d["losing_months"]=int((monthly<0).sum())
    for yr in (2025,2026):
        vals=net[years==yr]
        d[f"{yr}_trades"]=len(vals)
        d[f"{yr}_net_usd_per_contract"]=round(float(np.sum(vals)),3)
        d[f"{yr}_avg_net_usd_per_contract"]=round(float(np.mean(vals)),5) if len(vals) else None
        d[f"{yr}_profitable_months"]=int((pd.DataFrame({"month":np.array(months)[years==yr],"net":vals}).groupby("month").net.sum()>0).sum()) if len(vals) else 0
        d[f"{yr}_win_rate_pct"]=round(float(np.mean(vals>0)*100),2) if len(vals) else None
    return d

def main():
    records=[]
    results={"strategy":"Modification of existing EMA20+Supertrend(10,3) on confirmed 15m or 1h candles; 1m stop and exit execution",
             "date":"2025-01-01 through 2026-10-31 UTC signals; archive 1m data into mid-Nov 2026 to close open trades",
             "fee":FEERATE,"gst":GST,"slippage":"1 native price tick per side: 0.5 BTC or 0.05 ETH",
             "funding":"excluded, not assumed zero in live trading",
             "spread":"excluded","liq_mark_price":"unavailable","same_minute_conflicts":"stop first",
             "one_contract":"BTC=0.001 BTC, ETH=0.01 ETH", "never_merge_main":True,
             "strategies":[]}
    # Compile function first on tiny self-test: a long with 1 unit stop
    # cannot manufacture same-bar TP profit if stop is also touched.
    o=np.array([100.,100.,100.]);h=np.array([100.,112.,100.]);l=np.array([100.,88.,100.])
    sig=np.array([1,0,0],dtype=np.int8)
    arr=np.zeros(3,dtype=np.float64)
    test=core(o,h,l,o,np.array([1,2,3]),sig,arr,arr,np.zeros(3,dtype=np.int8),
       False,0,10.,1.,0.,0.,0.,0,0.5,0.001,FEERATE,GST,4,1)
    assert len(test[0])==1 and test[6][0]==2 and test[9]==1, "stop-first tie regression failed"
    for asset in ("BTC","ETH"):
        m,b15,_=load(asset)
        b15["adx14"]=adx14(b15)
        b60=aggregate(m,60)
        b240=aggregate(m,240)
        op=m.open.to_numpy(float)
        hi=m.high.to_numpy(float)
        lo=m.low.to_numpy(float)
        cl=m.close.to_numpy(float)
        clock=m.time.to_numpy(np.int64)
        tick=(0.5 if asset=="BTC" else 0.05)
        qty=(0.001 if asset=="BTC" else 0.01)
        for tf,mins,bars,higher,hm in (("15m",15,b15,b60,60),("1h",60,b60,b240,240)):
            signals=all_signals(bars,higher,mins,hm,clock)
            print("SIGNALS_MODIFIED",asset,tf,len(signals),flush=True)
            atrraw=bars.atr14.to_numpy(float)
            straws=bars.st.to_numpy(float)
            dirraw=bars.dir.to_numpy(np.int8)
            atr_at=np.zeros(len(m))
            st_at=np.zeros(len(m))
            flipdir=np.zeros(len(m),dtype=np.int8)
            for i in range(36,len(bars)-1):
                j=(i+1)*mins
                atr_at[j]=atrraw[i]
                st_at[j]=straws[i]
                if dirraw[i]!=dirraw[i-1]:
                    flipdir[j]=dirraw[i]
            for gate in GATES:
                sig=np.zeros(len(m),dtype=np.int8)
                for j,side,fl in signals:
                    if fl[gate]:sig[j]=side
                maxtrades=int(np.count_nonzero(sig))+1
                for nm,sk,sa,tp,be,act,dist,flip in MODES:
                    output=core(op,hi,lo,cl,clock,sig,atr_at,st_at,flipdir,
                        asset=="ETH",sk,sa,tp,be,act,dist,flip,tick,qty,
                        FEERATE,GST,ENTRY_CUTOFF,maxtrades)
                    record=summary(asset,tf,gate,nm,output,m)
                    records.append(record)
                    print("MOD_RESULT",json.dumps(record),flush=True)
    df=pd.DataFrame(records)
    df.to_csv(OUT/"modified_full_grid.csv",index=False)
    ranked=[]
    for asset in ("BTC","ETH"):
        for tf in ("15m","1h"):
            cohort=df[(df.asset==asset)&(df.timeframe==tf)&(df["2025_trades"]>=40)]
            # ONLY 2025 ranks; 2026 is held out from candidate selection.
            top=cohort.sort_values("2025_net_usd_per_contract",ascending=False).head(5)
            ranked.extend(top.to_dict("records"))
            print("TRAIN_2025_TOP_5_WITH_2026_HOLDOUT",asset,tf,
                  top[["asset","timeframe","filter","mode","trades",
                       "2025_trades","2025_net_usd_per_contract",
                       "2026_trades","2026_net_usd_per_contract",
                       "net_usd_per_one_contract","avg_net_equivalent_points",
                       "net_profit_factor","profitable_months",
                       "entries_with_stop_ge_0p75pct"]].to_json(orient="records"),flush=True)
    both=df[(df["2025_trades"]>=40)&(df["2026_trades"]>=30)&
            (df["2025_net_usd_per_contract"]>0)&(df["2026_net_usd_per_contract"]>0)]
    both=both.sort_values(["2026_net_usd_per_contract","2025_net_usd_per_contract"],ascending=False)
    print("POSITIVE_BOTH_YEARS_CANDIDATES",
        both[["asset","timeframe","filter","mode","trades",
              "2025_net_usd_per_contract","2026_net_usd_per_contract",
              "net_usd_per_one_contract","net_profit_factor","profitable_months",
              "entries_with_stop_ge_0p75pct"]].to_json(orient="records"),flush=True)
    results["all_count"]=len(df)
    results["ranked_2025"]=ranked
    results["both_years_positive"]=both.to_dict("records")
    (OUT/"summary.json").write_text(json.dumps(results,indent=2)+"\n")
    print("MODIFIED_EMA_ST_REPLAY_COMPLETE",flush=True)

if __name__=="__main__":
    main()
