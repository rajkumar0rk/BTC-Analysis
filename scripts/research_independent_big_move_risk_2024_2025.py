"""Predeclared risk/exit/warmup factorial on the six existing entries. No 2026."""
import csv,gzip,json,math,itertools
from pathlib import Path
import numpy as np
import research_independent_big_move_2024_2025 as base
import research_independent_big_move_mtf_2024_2025 as mtf
import research_independent_big_move_exits_2024_2025 as exits
import research_independent_big_move_audit_2024_2025 as audit
OUT=Path("scratch/independent_big_move_risk")
STOPS=("15m-atr","1h-atr","15m-swing")
EXIT_MODES=("fresh-cross","unfavorable")
WARMUPS=("original","ready")

def swing_levels(f):
    # Strict 2-left/2-right pivots known only after second right candle closes.
    h,l=f["h"],f["l"];hi=np.full(len(h),np.nan);lo=hi.copy();a=b=np.nan
    for i in range(len(h)):
        if i>=4:
            z=i-2;neighbors=[z-2,z-1,z+1,z+2]
            if all(h[z]>h[x] for x in neighbors):a=h[z]
            if all(l[z]<l[x] for x in neighbors):b=l[z]
        hi[i]=a;lo[i]=b
    return hi,lo

def risk_summary(trades,months):
    s=base.summarize(trades,months)
    r=[t["net_R_fee_inclusive"] for t in trades]
    gain=math.fsum(max(0,x) for x in r);loss=-math.fsum(min(0,x) for x in r)
    month={m:0. for m in months};eq=peak=dd=0.
    for t,x in zip(trades,r):
        month[t["entry_utc"][:7]]+=x;eq+=x;peak=max(peak,eq);dd=max(dd,peak-eq)
    s.update(fee_R=math.fsum(r),fee_pf=gain/loss if loss else None,fee_dd_R=dd,fee_months=sum(x>0 for x in month.values()),
        monthly_fee_R=month,fee_winners_5R=sum(x>=5 for x in r),fee_winners_10R=sum(x>=10 for x in r))
    for field,arr in (("points",[t["net_points"] for t in trades]),("R",[t["net_R"] for t in trades]),("fee_R",r)):
        ordered=sorted((x for x in arr if x>0),reverse=True)
        for n in (1,3,5):s[f"{field}_without_top{n}"]=math.fsum(arr)-math.fsum(ordered[:n])
    return s

def replay(bars,f,sig,stop_mode,exit_mode,warmup,start,end,h1,h4,swing,schedules):
    O,H,L,C=bars;trades=[];free=0;skips={"warmup":0,"stop":0,"unfavorable":0}
    for i in np.flatnonzero(sig):
        k=(int(i)+1)*15
        if k>=len(O) or k<free:continue
        d=int(sig[i]);ep=float(O[k]);z4=k//240-1;z1=k//60-1
        trend=int(h4[z4]) if z4>=0 else 0
        if warmup=="ready" and trend==0:skips["warmup"]+=1;continue
        # Under unfavorable-state policy, do not initiate an already adverse position.
        # Unknown state allowed only for the original-warmup variant.
        if exit_mode=="unfavorable" and trend==-d:skips["unfavorable"]+=1;continue
        if stop_mode=="15m-swing":
            pivot=swing[1 if d==1 else 0][i]
            if not np.isfinite(pivot):skips["stop"]+=1;continue
            stop=math.floor(pivot/base.TICK)*base.TICK-base.TICK if d==1 else math.ceil(pivot/base.TICK)*base.TICK+base.TICK
            risk=d*(ep-stop)
            if risk<=0:skips["stop"]+=1;continue
        else:
            atr=f["atr"][i] if stop_mode=="15m-atr" else h1["atr"][z1] if z1>=0 else np.nan
            if not np.isfinite(atr) or atr<=0:skips["stop"]+=1;continue
            risk=max(base.TICK,math.ceil(2*atr/base.TICK)*base.TICK);stop=ep-d*risk
        j,xp,reason=audit.independent_exit(bars,k,d,stop,schedules[exit_mode]);free=j+1
        gross=d*(xp-ep);fee=(ep+xp)*base.FEE;net=gross-fee
        trades.append(dict(entry_utc=base.dt(start+k*60).isoformat(),exit_utc=base.dt(end if reason=="End of yearly evaluation" else start+j*60).isoformat(),
            side=d,entry_price=ep,exit_price=xp,stop_price=stop,gross_points=gross,fee_points=fee,net_points=net,net_R=net/risk,
            net_R_fee_inclusive=net/(risk+2*ep*base.FEE),holding_minutes=j-k,exit_reason=reason,entry_h4_trend=trend,
            initial_risk_points=risk))
    months=[f"{base.dt(start).year}-{m:02d}" for m in range(base.dt(start).month,13)]
    s=risk_summary(trades,months);s["skips"]=skips
    return s,trades

def tests():
    audit.tests()
    h=np.array([1.,2.,6.,3.,2.,7.,4.,3.]);l=-h
    hi,lo=swing_levels({"h":h,"l":l})
    assert np.isnan(hi[3]) and hi[4]==6 and hi[6]==6 and hi[7]==7
    assert np.allclose(hi[:6],swing_levels({"h":h[:6],"l":l[:6]})[0],equal_nan=True)
    assert np.allclose(lo,-hi,equal_nan=True)

def run():
    tests();by_year={};OUT.mkdir(parents=True,exist_ok=True)
    # Stream ledgers to bound memory across 288 variants.
    with gzip.open(OUT/"all_ledgers.jsonl.gz","wt") as ledger:
        for year,start,end,reader in ((2024,base.data24.START,base.data24.END,base.data24.candles_2024),(2025,base.data25.START,base.data25.END,base.data25.candles)):
            bars=base.read_bars(reader,start,end);f=base.features(bars,15);ss=base.signals(f);align=mtf.filters(bars);h1=base.features(bars,60);st=exits.supertrend(h1)
            c4=bars[3,239::240];e20=base.ema(c4,20);e50=base.ema(c4,50);h4=np.where(e20>e50,1,np.where(e20<e50,-1,0)).astype(np.int8)
            swing=swing_levels(f);schedules={"fresh-cross":audit.cross_schedule(h4),"unfavorable":{d:(np.flatnonzero(h4==-d)+1)*240 for d in (1,-1)}}
            by_year[year]={}
            for name,flt in itertools.product(base.FAMILIES,mtf.FILTERS):
                sig=ss[name] if flt=="none" else np.where(ss[name]==align[flt],ss[name],0).astype(np.int8)
                baseline=exits.replay(bars,f,sig,name,flt,4,start,end,h1,st,h4)
                for sm,em,w in itertools.product(STOPS,EXIT_MODES,WARMUPS):
                    key=f"{name}|{flt}|{sm}|{em}|{w}"
                    s,ts=replay(bars,f,sig,sm,em,w,start,end,h1,h4,swing,schedules)
                    if (sm,em,w)==("15m-atr","fresh-cross","original"):
                        assert s["trades"]==baseline["summary"]["trades"] and math.isclose(s["net"],baseline["summary"]["net"],abs_tol=1e-6),key
                        for a,b in zip(ts,baseline["trades"]):
                            assert a["entry_utc"]==b["entry_utc"] and a["exit_utc"]==b["exit_utc"] and a["exit_price"]==b["exit_price"],key
                    by_year[year][key]=(s,ts)
                    ledger.write(json.dumps(dict(year=year,key=key,summary=s,trades=ts),separators=(",",":"),allow_nan=False)+"\n")
            print("YEAR_COMPLETE",year,len(by_year[year]),flush=True)
    fields=("trades","net","net_R","fee_R","profit_factor","pf_R","fee_pf","profitable_months","profitable_R_months","fee_months","realized_drawdown_points","fee_dd_R","winners_5R","winners_10R","best_trade_R","fee_winners_5R","fee_winners_10R","points_without_top1","points_without_top3","points_without_top5","R_without_top1","R_without_top3","R_without_top5","fee_R_without_top1","fee_R_without_top3","fee_R_without_top5")
    rows=[];report=[]
    for key,(a,ta) in by_year[2024].items():
        b,tb=by_year[2025][key];s=risk_summary(ta+tb,list(a["monthly_entry_attribution"])+list(b["monthly_entry_attribution"]))
        row=dict(key=key,**{k:s[k] for k in fields})
        for y,ys in ((2024,a),(2025,b)):row.update({str(y)+"_"+k:ys[k] for k in fields})
        rows.append(row);report.append(dict(key=key,summary=s,years={"2024":a,"2025":b}))
        print("RESULT",json.dumps(row,separators=(",",":"),allow_nan=False))
    assert len(rows)==288
    with (OUT/"all_results.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    (OUT/"results.json").write_text(json.dumps(report,separators=(",",":"),allow_nan=False))
    (OUT/"provenance.json").write_text(json.dumps(dict(stops=STOPS,exit_modes=EXIT_MODES,warmup=WARMUPS,
        rules="15m ATR2 vs H1 ATR2 vs last confirmed 15m 2-left/2-right adverse pivot plus one tick; unfavorable exit skips adverse entry and exits on first completed adverse H4 state; ready requires known H4 trend; no backfill of warmup",
        period="Feb 1 2024 12 UTC through Dec 31 2025; separate annual resets; no 2026",
        execution="15m signals, next 1m open, fixed stop monitored 1m, gap at open, one position; 4H EMA20/50; no fixed TP",
        fees="0.05% taker each side plus 18% GST; no offer; funding/liquidation/extra slippage excluded",
        selection="288 configurations, 24 exact baselines; outlier removal is retrospective diagnostic not tradable rule"),indent=2))
    print("TOTAL",len(rows),"BOTH_POINTS",sum(r["2024_net"]>0 and r["2025_net"]>0 for r in rows),"BOTH_FEE_R",sum(r["2024_fee_R"]>0 and r["2025_fee_R"]>0 for r in rows),"ROBUST_TOP3",sum(r["fee_R_without_top3"]>0 for r in rows))
if __name__=="__main__":run()
