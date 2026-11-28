"""Fixed EMA pullback, H1 ATR2 stop, H4 exits with delayed activation/protection."""
import csv,gzip,json,math,itertools
from pathlib import Path
import numpy as np
from numba import njit
import research_independent_big_move_2024_2025 as base
import research_independent_big_move_mtf_2024_2025 as mtf
import research_independent_big_move_exits_2024_2025 as exits
import research_independent_big_move_risk_2024_2025 as risk
import research_ema_pullback_slow_exits_2024_2025 as slow
OUT=Path("scratch/ema_pullback_profit_protection")
# 2 reversals + 4 activation thresholds for each of two Chandelier policies.
EXITS=[("ema",0,0),("supertrend",1,0)]+[(name,mode,delay) for name,mode in (("chandelier",2),("chandelier-confirmed",3)) for delay in (0,2,3,5)]
PROTECTION=[(0,0)]+[(a,l) for a in (2,3,5) for l in (0,1)]
FEE=base.FEE;TICK=base.TICK
@njit
def execute(O,H,L,C,k,d,r,mode,delay,activation,lock,h4,st,lower,upper,hclose):
    ep=O[k];stop=ep-d*r;best=0.;chlevel=-np.inf if d==1 else np.inf;active=False;protected=False
    # Profit-lock level is fee-inclusive at the exact stop fill; gaps can exceed it.
    raw=ep+d*(2*ep*FEE+lock*r)/(1-d*FEE)
    lock_price=math.ceil(raw/TICK)*TICK if d==1 else math.floor(raw/TICK)*TICK
    for j in range(k,len(O)):
        # Best favorable excursion uses only fully processed prior 1m candles.
        if j>k and activation>0 and not protected and best>=activation*r:
            stop=max(stop,lock_price) if d==1 else min(stop,lock_price)
            protected=True
        if j>k and j%240==0:
            z=j//240-1
            if mode>=2 and best>=delay*r:
                active=True
                lev=lower[z] if d==1 else upper[z]
                if np.isfinite(lev):
                    chlevel=max(chlevel,lev) if d==1 else min(chlevel,lev)
                    if mode==2:stop=max(stop,chlevel) if d==1 else min(stop,chlevel)
        if d*(O[j]-stop)<=0:return j,O[j],stop,1,protected,active
        if j>k and j%240==0:
            z=j//240-1
            if z>=1 and mode==0 and h4[z-1]==d and h4[z]==-d:return j,O[j],stop,3,protected,active
            if z>=1 and mode==1 and st[z-1]==d and st[z]==-d:return j,O[j],stop,4,protected,active
            # Confirmation policy: both adverse ST state and completed H4 close beyond
            # ratcheted Chandelier level, then market exit at next minute open.
            if mode==3 and active and st[z]==-d and d*(hclose[z]-chlevel)<=0:
                return j,O[j],stop,5,protected,active
        if (d==1 and L[j]<=stop) or (d==-1 and H[j]>=stop):return j,stop,stop,1,protected,active
        best=max(best,H[j]-ep if d==1 else ep-L[j])
    return len(O)-1,C[-1],stop,2,protected,active

def replay(bars,sig,h1,h4,st,lo,hi,hclose,plan,protection,start,end):
    O,H,L,C=bars;trades=[];free=0;name,mode,delay=plan;activation,lock=protection
    for i in np.flatnonzero(sig):
        k=(int(i)+1)*15
        if k>=len(O) or k<free:continue
        d=int(sig[i]);ep=float(O[k]);z1=k//60-1;z4=k//240-1
        # Require every H4 indicator used in this experiment to be ready.
        if z4<0 or h4[z4]==0 or st[z4]==0 or not np.isfinite(lo[z4]):continue
        a=h1["atr"][z1] if z1>=0 else np.nan
        if not np.isfinite(a) or a<=0:continue
        r=max(TICK,math.ceil(2*a/TICK)*TICK)
        j,xp,stop,reason,protected,active=execute(O,H,L,C,k,d,r,mode,delay,activation,lock,h4,st,lo,hi,hclose)
        free=j+1;gross=d*(float(xp)-ep);fee=(ep+float(xp))*FEE;net=gross-fee
        trades.append(dict(entry_utc=base.dt(start+k*60).isoformat(),exit_utc=base.dt(end if reason==2 else start+j*60).isoformat(),
            side=d,entry_price=ep,exit_price=float(xp),stop_price=ep-d*r,final_stop=float(stop),initial_risk_points=r,
            gross_points=gross,fee_points=fee,net_points=net,net_R=net/r,net_R_fee_inclusive=net/(r+2*ep*FEE),
            holding_minutes=int(j-k),exit_reason={1:"Initial/protected/trailing stop",2:"Year-end",3:"EMA reversal",4:"Supertrend reversal",5:"Confirmed Chandelier"}[reason],
            protection_activated=bool(protected),chandelier_activated=bool(active)))
    months=[f"{base.dt(start).year}-{m:02d}" for m in range(base.dt(start).month,13)]
    return risk.risk_summary(trades,months),trades

def tests():
    slow.tests()
    # 2R reached and protection activated only next minute, not within same bar.
    O=np.array([100.,101.,101.,100.]);H=np.array([105.,101.,101.,101.]);L=np.array([99.,100.,99.,99.]);C=np.array([101.,101.,100.,100.])
    z=np.array([1],dtype=np.int8);a=np.array([95.]);b=np.array([105.]);c=np.array([100.])
    j,x,stop,reason,p,active=execute(O,H,L,C,0,1,2.,0,0,2,0,z,z,a,b,c)
    assert j==1 and reason==1 and p and stop==100.5,(j,x,stop,reason,p)
    # A candle touching initial stop and activation exits at initial stop; no retroactive lock.
    L[0]=97.
    j,x,stop,reason,p,active=execute(O,H,L,C,0,1,2.,0,0,2,0,z,z,a,b,c)
    assert j==0 and x==98. and not p
    # Symmetric short protection, rounding toward profit.
    O=np.array([100.,99.,100.]);H=np.array([101.,100.,101.]);L=np.array([95.,98.,99.]);C=np.array([99.,99.,100.])
    j,x,stop,reason,p,active=execute(O,H,L,C,0,-1,2.,0,0,2,0,z,z,a,b,c)
    assert j==1 and x==99.5 and p
    # Delayed chandelier can only start at a subsequent completed H4 boundary.
    O=np.full(481,100.);H=O+1;L=O-1;C=O.copy();H[100]=105.
    z=np.array([1,-1],dtype=np.int8);a=np.array([101.,101.]);b=np.array([110.,110.]);c=np.array([100.,100.])
    assert execute(O,H,L,C,0,1,2.,2,2,0,0,z,z,a,b,c)[0]==240
    assert execute(O,H,L,C,0,1,2.,3,2,0,0,z,z,a,b,c)[0]==480

def run():
    tests();OUT.mkdir(parents=True,exist_ok=True);by_year={}
    with gzip.open(OUT/"all_ledgers.jsonl.gz","wt") as ledger:
        for year,start,end,reader in ((2024,base.data24.START,base.data24.END,base.data24.candles_2024),(2025,base.data25.START,base.data25.END,base.data25.candles)):
            bars=base.read_bars(reader,start,end);f=base.features(bars,15);sig0=base.signals(f)["ema-pullback"];align=mtf.filters(bars)
            h1=base.features(bars,60);f4=base.features(bars,240);h4=np.where(f4["e20"]>f4["e50"],1,np.where(f4["e20"]<f4["e50"],-1,0)).astype(np.int8)
            st=exits.supertrend(f4);lo,hi=slow.chandelier(f4);series={240:(st,lo,hi)}
            by_year[year]={}
            for flt in mtf.FILTERS:
                sig=sig0 if flt=="none" else np.where(sig0==align[flt],sig0,0).astype(np.int8)
                # Exact baseline comparisons against preceding ready variants.
                benchmarks={0:slow.replay(bars,f,sig,h1,h4,("ema",240,0),"ready",start,end,series)[0],
                    1:slow.replay(bars,f,sig,h1,h4,("st",240,1),"ready",start,end,series)[0],
                    2:slow.replay(bars,f,sig,h1,h4,("ch",240,2),"ready",start,end,series)[0]}
                for plan,protection in itertools.product(EXITS,PROTECTION):
                    name,mode,delay=plan;a,l=protection;key=f"{flt}|{name}|delay{delay}|protect{a}|lock{l}"
                    s,ts=replay(bars,sig,h1,h4,st,lo,hi,f4["c"],plan,protection,start,end)
                    if mode<=2 and delay==0 and a==0:
                        assert s["trades"]==benchmarks[mode]["trades"] and math.isclose(s["net"],benchmarks[mode]["net"],abs_tol=1e-6),(key,s["net"],benchmarks[mode]["net"])
                    by_year[year][key]=(s,ts)
                    ledger.write(json.dumps(dict(year=year,key=key,summary=s,trades=ts),separators=(",",":"),allow_nan=False)+"\n")
            print("YEAR_COMPLETE",year,len(by_year[year]),flush=True)
    fields=("trades","trades_per_month","net","net_R","fee_R","profit_factor","fee_pf","profitable_months","fee_months","realized_drawdown_points","fee_dd_R","winners_5R","winners_10R","best_trade_R","fee_winners_5R","fee_winners_10R","points_without_top3","fee_R_without_top1","fee_R_without_top3","fee_R_without_top5","mean_holding_minutes")
    rows=[];report=[]
    for key,(a,ta) in by_year[2024].items():
        b,tb=by_year[2025][key];s=risk.risk_summary(ta+tb,list(a["monthly_entry_attribution"])+list(b["monthly_entry_attribution"]))
        row=dict(key=key,**{k:s[k] for k in fields},protection_activations=sum(t["protection_activated"] for t in ta+tb))
        for y,ys in ((2024,a),(2025,b)):row.update({str(y)+"_"+k:ys[k] for k in fields})
        rows.append(row);report.append(dict(key=key,summary=s,years={"2024":a,"2025":b}))
        print("RESULT",json.dumps(row,separators=(",",":"),allow_nan=False))
    assert len(rows)==280
    with (OUT/"all_results.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    (OUT/"results.json").write_text(json.dumps(report,separators=(",",":"),allow_nan=False))
    (OUT/"provenance.json").write_text(json.dumps(dict(exits=EXITS,protection=PROTECTION,filters=mtf.FILTERS,
        entry="unchanged 15m EMA pullback; 1H ATR14 x2 initial SL; all H4 indicators ready; no fixed TP",
        protection_rule="gross excursion in initial R, observed on survived 1m bar; fee-inclusive breakeven or +1R lock effective next minute; gap risk remains",
        chandelier_rule="4H 22-bar extreme +/-3 Wilder ATR22; delay 0/2/3/5R, evaluated only at closed H4 boundaries; confirmed variant exits only when H4 ST adverse and closed price crosses/breaches ratcheted Chandelier; no hard Chandelier stop in confirmed variant, initial/protection stop always active",
        period="Feb 1 2024 12 UTC to end 2025; annual resets; no 2026",costs="0.05% taker per side +18% GST; no offer; funding/liquidation/extra slippage excluded",
        selection="280 configurations; 12 exact baselines; multiple testing not independent validation; diagnostic top-winner removal"),indent=2))
    print("TOTAL",len(rows),"BOTH_POINTS",sum(r["2024_net"]>0 and r["2025_net"]>0 for r in rows),"BOTH_FEE_R",sum(r["2024_fee_R"]>0 and r["2025_fee_R"]>0 for r in rows),"ROBUST_TOP3",sum(r["fee_R_without_top3"]>0 for r in rows))
if __name__=="__main__":run()
