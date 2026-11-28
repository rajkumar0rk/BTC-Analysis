"""Frozen EMA pullback + 1H ATR2 initial risk; compare six exits and H4 baseline."""
import csv,gzip,json,math,itertools
from pathlib import Path
import numpy as np
from numba import njit
import research_independent_big_move_2024_2025 as base
import research_independent_big_move_mtf_2024_2025 as mtf
import research_independent_big_move_exits_2024_2025 as exits
import research_independent_big_move_audit_2024_2025 as audit
import research_independent_big_move_risk_2024_2025 as risk
OUT=Path("scratch/ema_pullback_slow_exits")
PLANS=(("4h-ema-reversal",240,0),("1h-supertrend",60,1),("2h-supertrend",120,1),("4h-supertrend",240,1),("1h-chandelier",60,2),("2h-chandelier",120,2),("4h-chandelier",240,2))
WARMUPS=("original","ready")
EXPECTED={2024:{("1h","original"):34986.80262,("1h","ready"):31511.67895,("none","original"):23191.083645,("none","ready"):20392.73849,("1h-4h","original"):16871.682875,("1h-4h","ready"):16871.682875},2025:{("1h","original"):13698.83091,("1h","ready"):12681.484125,("none","original"):18094.06149,("none","ready"):16581.102135,("1h-4h","original"):8274.811835,("1h-4h","ready"):8274.811835}}

def chandelier(f):
    # Classic 22-bar extremes +/- 3 times Wilder ATR22. Completed bars only.
    h,l,tr=f["h"],f["l"],f["tr"];n=len(h)
    a=np.full(n,np.nan);upper=a.copy();lower=a.copy()
    if n>=22:
        a[21]=np.mean(tr[:22])
        for i in range(21,n):
            if i>21:a[i]=(21*a[i-1]+tr[i])/22
            lower[i]=math.floor((max(h[i-21:i+1])-3*a[i])/base.TICK)*base.TICK
            upper[i]=math.ceil((min(l[i-21:i+1])+3*a[i])/base.TICK)*base.TICK
    return lower,upper

@njit
def execute(O,H,L,C,k,d,initial,tf,mode,st,lower,upper):
    stop=initial
    for j in range(k,len(O)):
        if j>k and j%tf==0:
            z=j//tf-1
            if mode==2 and z>=0:
                level=lower[z] if d==1 else upper[z]
                if np.isfinite(level):stop=max(stop,level) if d==1 else min(stop,level)
        if d*(O[j]-stop)<=0:return j,O[j],stop,1
        if mode==1 and j>k and j%tf==0:
            z=j//tf-1
            if z>=1 and st[z-1]==d and st[z]==-d:return j,O[j],stop,3
        if (d==1 and L[j]<=stop) or (d==-1 and H[j]>=stop):return j,stop,stop,1
    return len(O)-1,C[-1],stop,2

def replay(bars,f,sig,h1,h4,plan,w,start,end,series):
    name,tf,mode=plan
    O,H,L,C=bars;trades=[];free=0
    st,lower,upper=series[tf]
    schedule=audit.cross_schedule(h4) if mode==0 else None
    for i in np.flatnonzero(sig):
        k=(int(i)+1)*15
        if k>=len(O) or k<free:continue
        d=int(sig[i]);ep=float(O[k]);z1=k//60-1;z4=k//240-1;z=k//tf-1
        trend=int(h4[z4]) if z4>=0 else 0
        if w=="ready":
            if trend==0:continue
            if mode==1 and (z<0 or st[z]==0):continue
            if mode==2 and (z<0 or not np.isfinite(lower[z])):continue
        a=h1["atr"][z1] if z1>=0 else np.nan
        if not np.isfinite(a) or a<=0:continue
        initial_risk=max(base.TICK,math.ceil(2*a/base.TICK)*base.TICK);stop=ep-d*initial_risk
        if mode==0:
            j,xp,reason=audit.independent_exit(bars,k,d,stop,schedule);final_stop=stop
        else:
            j,xp,final_stop,code=execute(O,H,L,C,k,d,stop,tf,mode,st,lower,upper)
            reason={1:"Initial/trailing stop",2:"End of yearly evaluation",3:"Supertrend reversal"}[code]
        free=j+1;gross=d*(float(xp)-ep);fee=(ep+float(xp))*base.FEE;net=gross-fee
        trades.append(dict(entry_utc=base.dt(start+k*60).isoformat(),exit_utc=base.dt(end if reason=="End of yearly evaluation" else start+j*60).isoformat(),
            side=d,entry_price=ep,exit_price=float(xp),stop_price=stop,final_stop=float(final_stop),initial_risk_points=initial_risk,
            gross_points=gross,fee_points=fee,net_points=net,net_R=net/initial_risk,net_R_fee_inclusive=net/(initial_risk+2*ep*base.FEE),
            holding_minutes=int(j-k),exit_reason=reason,entry_h4_trend=trend))
    months=[f"{base.dt(start).year}-{m:02d}" for m in range(base.dt(start).month,13)]
    return risk.risk_summary(trades,months),trades

def tests():
    risk.tests();exits.tests()
    rng=np.random.default_rng(19);c=100+np.cumsum(rng.normal(0,.2,240*60));o=np.r_[c[0],c[:-1]]
    bars=np.array([o,np.maximum(o,c)+.2,np.minimum(o,c)-.2,c])
    for tf in (60,120,240):
        a=base.features(bars,tf);b=base.features(bars[:,:240*53],tf)
        assert np.array_equal(exits.supertrend(a)[:len(b["c"])],exits.supertrend(b))
        for x,y in zip(chandelier(a),chandelier(b)):assert np.allclose(x[:len(y)],y,equal_nan=True)
    O=np.full(181,100.);H=O+1;L=O-1;C=O.copy()
    st=np.array([1,-1,1],dtype=np.int8);lo=np.array([95.,101.,90.]);hi=np.array([105.,105.,105.])
    assert execute(O,H,L,C,60,1,90.,60,1,st,lo,hi)==(120,100.,90.,3)
    # No pre-entry Chandelier update; first eligible update uses completed bars.
    assert execute(O,H,L,C,60,1,90.,60,2,st,lo,hi)==(120,100.,101.,1)
    # Stop on a gap must precede reversal.
    O[120]=85.;L[120]=84.
    assert execute(O,H,L,C,60,1,90.,60,1,st,lo,hi)==(120,85.,90.,1)

def run():
    tests();by_year={};OUT.mkdir(parents=True,exist_ok=True)
    with gzip.open(OUT/"all_ledgers.jsonl.gz","wt") as ledger:
        for year,start,end,reader in ((2024,base.data24.START,base.data24.END,base.data24.candles_2024),(2025,base.data25.START,base.data25.END,base.data25.candles)):
            bars=base.read_bars(reader,start,end);f=base.features(bars,15);sig0=base.signals(f)["ema-pullback"];align=mtf.filters(bars)
            features={tf:base.features(bars,tf) for tf in (60,120,240)}
            h1=features[60];h4f=features[240];h4=np.where(h4f["e20"]>h4f["e50"],1,np.where(h4f["e20"]<h4f["e50"],-1,0)).astype(np.int8)
            series={tf:(exits.supertrend(ft),*chandelier(ft)) for tf,ft in features.items()}
            swing=risk.swing_levels(f);sched={"fresh-cross":audit.cross_schedule(h4)}
            by_year[year]={}
            for flt,w in itertools.product(mtf.FILTERS,WARMUPS):
                sig=sig0 if flt=="none" else np.where(sig0==align[flt],sig0,0).astype(np.int8)
                baseline,bt=risk.replay(bars,f,sig,"1h-atr","fresh-cross",w,start,end,h1,h4,swing,sched)
                for plan in PLANS:
                    key=f"{flt}|{plan[0]}|{w}";s,ts=replay(bars,f,sig,h1,h4,plan,w,start,end,series)
                    if plan[2]==0:
                        assert s["trades"]==baseline["trades"] and math.isclose(s["net"],baseline["net"],abs_tol=1e-6)
                        assert all(a["entry_utc"]==b["entry_utc"] and a["exit_utc"]==b["exit_utc"] and a["exit_price"]==b["exit_price"] for a,b in zip(ts,bt))
                        if (flt,w) in EXPECTED[year]:assert math.isclose(s["net"],EXPECTED[year][flt,w],abs_tol=1e-6)
                    by_year[year][key]=(s,ts)
                    ledger.write(json.dumps(dict(year=year,key=key,summary=s,trades=ts),separators=(",",":"),allow_nan=False)+"\n")
            print("YEAR_COMPLETE",year,len(by_year[year]),flush=True)
    fields=("trades","trades_per_month","net","net_R","fee_R","profit_factor","fee_pf","profitable_months","fee_months","realized_drawdown_points","fee_dd_R","winners_5R","winners_10R","best_trade_R","fee_winners_5R","fee_winners_10R","points_without_top3","fee_R_without_top1","fee_R_without_top3","fee_R_without_top5","mean_holding_minutes")
    rows=[];report=[]
    for key,(a,ta) in by_year[2024].items():
        b,tb=by_year[2025][key];s=risk.risk_summary(ta+tb,list(a["monthly_entry_attribution"])+list(b["monthly_entry_attribution"]))
        row=dict(key=key,**{k:s[k] for k in fields})
        for y,ys in ((2024,a),(2025,b)):row.update({str(y)+"_"+k:ys[k] for k in fields})
        rows.append(row);report.append(dict(key=key,summary=s,years={"2024":a,"2025":b}))
        print("RESULT",json.dumps(row,separators=(",",":"),allow_nan=False))
    assert len(rows)==56
    with (OUT/"all_results.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    (OUT/"results.json").write_text(json.dumps(report,separators=(",",":"),allow_nan=False))
    (OUT/"provenance.json").write_text(json.dumps(dict(plans=PLANS,filters=mtf.FILTERS,warmup=WARMUPS,
        entry="unchanged EMA20 reclaim with 15m EMA20/50 alignment; 1H ATR14 x2 initial stop",
        rules="ST10 x3 fresh flip on closed bar, execute next 1m open; Chandelier22 x3 Wilder ATR22, 22 completed bars extremes, tick rounded, ratchets only on boundaries strictly after entry, never loosens; original warmup allows unknown exit state, ready requires known H4 and relevant exit indicator",
        execution="1m stop/gap, one position, all days, no TP; fees 0.05% each side +18% GST; no funding/liquidation/extra slippage",
        period="2024 Feb 1 12 UTC to end 2025, separate annual resets/forced yearly close; no 2026; 48 new and 8 baseline variants; retrospective stress not tradable"),indent=2))
    print("TOTAL",len(rows),"BOTH_POINTS",sum(r["2024_net"]>0 and r["2025_net"]>0 for r in rows),"BOTH_FEE_R",sum(r["2024_fee_R"]>0 and r["2025_fee_R"]>0 for r in rows),"ROBUST_TOP3",sum(r["fee_R_without_top3"]>0 for r in rows))
if __name__=="__main__":run()
