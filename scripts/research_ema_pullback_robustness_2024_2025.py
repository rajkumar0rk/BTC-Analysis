"""Robustness grid, not parameter selection. Three frozen EMA pullback candidates."""
import csv,gzip,json,math,itertools
from pathlib import Path
import numpy as np
import research_independent_big_move_2024_2025 as base
import research_independent_big_move_mtf_2024_2025 as mtf
import research_independent_big_move_audit_2024_2025 as audit
import research_independent_big_move_risk_2024_2025 as risk
OUT=Path("scratch/ema_pullback_robustness")
CANDIDATES={"A":"1h","B":"none","C":"1h-4h"}
PAIRS=((15,40),(20,50),(25,60));MULTS=(1.5,2.,2.5);DAYS=("all","weekdays");SLIPS=(0,10,50,100,200);WARM=("reset","continuous")
EXPECTED={2024:{"A":31511.67895,"B":20392.73849,"C":16871.682875},2025:{"A":12681.484125,"B":16581.102135,"C":8274.811835}}
ROOT=Path("data/delta_india")
def historical_rows(year,series,start,end):
    # Only 2024/2025 archives; merge by absolute timestamps, not partition name.
    if year==2024:
        files=sorted((ROOT/"BTCUSD/2024_verified_archive"/series).glob("2024-*.csv.gz"))
        files+=sorted((ROOT/"2024_recovery_candidates/BTCUSD").glob("2024-*/"+series+".csv.gz"))
    else:files=sorted((ROOT/"BTCUSD/institutional/history"/series).glob("2025-*.csv.gz"))
    values={}
    for p in files:
        with gzip.open(p,"rt") as f:
            for row in csv.DictReader(f):
                t=int(row["time"])
                if start<=t<end:
                    values[t]=float(row["close" if series=="funding_1h" else "open"])
    return values
def funding_proxy(year,bars,start,end):
    # Explicit estimate, not actual settlements: assumed UTC 00/08/16,
    # preceding completed hourly rate candle in percent and settlement mark open.
    # Missing inputs never silently replaced by zero.
    rates=historical_rows(year,"funding_1h",start-3600,end)
    marks=historical_rows(year,"mark_1m",start,end)
    ts=np.arange(((start+28799)//28800)*28800,end,28800,dtype=np.int64)
    vals=[];missing=0
    for t in ts:
        a=rates.get(int(t)-3600);m=marks.get(int(t))
        if a is None or m is None or not math.isfinite(a) or not math.isfinite(m) or m<=0 or abs(a)>10:
            vals.append(0.);missing+=1
        else:vals.append(a/100*m)
    # First boundary exactly at start cannot affect a position opened later.
    valid=np.array([(int(t)-3600 in rates and int(t) in marks and math.isfinite(rates[int(t)-3600]) and abs(rates[int(t)-3600])<=10 and math.isfinite(marks[int(t)]) and marks[int(t)]>0) for t in ts],dtype=np.int64)
    print("FUNDING_COVERAGE",year,len(ts),missing,"assumed 8h UTC and percent units; not settlements",flush=True)
    return ts,np.r_[0.,np.cumsum(vals)],np.r_[0,np.cumsum(1-valid)]
def indicator_pack(bars,pair):
    p,q=pair;closes={tf:bars[3,tf-1::tf] for tf in (15,60,240)}
    es={tf:(base.ema(c,p),base.ema(c,q)) for tf,c in closes.items()}
    d={tf:np.where(a>b,1,np.where(a<b,-1,0)).astype(np.int8) for tf,(a,b) in es.items()}
    c=closes[15];e=es[15][0];sig=np.zeros(len(c),dtype=np.int8)
    sig[1:]=np.where((d[15][1:]==1)&(c[:-1]<=e[:-1])&(c[1:]>e[1:]),1,np.where((d[15][1:]==-1)&(c[:-1]>=e[:-1])&(c[1:]<e[1:]),-1,0))
    return sig,d[60],d[240],base.features(bars,60)["atr"]
def slice_pack(pack,offset,n):
    sig,h1,h4,atr=pack
    # Preserve previous completed higher-timeframe state at first yearly bar.
    # Arrays of state indexed by entry minute, with prior state in element zero.
    k=np.arange(0,n+1,15,dtype=np.int64)+offset
    ix1=k//60-1;ix4=k//240-1
    s1=np.where(ix1>=0,h1[np.maximum(ix1,0)],0)
    s4=np.where(ix4>=0,h4[np.maximum(ix4,0)],0)
    a=np.where(ix1>=0,atr[np.maximum(ix1,0)],np.nan)
    # Signals at yearly opening excluded (prior-year trade forced closed).
    s=sig[offset//15: (offset+n)//15]
    schedule={}
    for side in (1,-1):
        ix=(np.flatnonzero((h4[:-1]==side)&(h4[1:]==-side))+2)*240-offset
        schedule[side]=ix[(ix>=0)&(ix<n)]
    return s,s1,s4,a,schedule
def replay(bars,pack,candidate,mult,days,slip,start,end,funding):
    O,H,L,C=bars;sig,s1,s4,atr,sched=pack;trades=[];free=0
    ts,fp,missing=funding
    for i in np.flatnonzero(sig):
        k=(int(i)+1)*15;z=int(i)+1
        if k>=len(O) or k<free:continue
        d=int(sig[i])
        if s4[z]==0 or not np.isfinite(atr[z]) or atr[z]<=0:continue
        if candidate in ("A","C") and s1[z]!=d:continue
        if candidate=="C" and s4[z]!=d:continue
        t=start+k*60
        if days=="weekdays" and base.dt(t+19800).weekday()>=5:continue
        # Adverse entry execution and exit execution separately. Stop is based on actual entry.
        ep=float(O[k])+d*slip;r=max(base.TICK,math.ceil(mult*atr[z]/base.TICK)*base.TICK);stop=ep-d*r
        j,raw,reason=audit.independent_exit(bars,k,d,stop,sched)
        xp=float(raw)-d*slip;free=j+1
        et=end if reason=="End of yearly evaluation" else start+j*60
        gross=d*(xp-ep);fee=(ep+xp)*base.FEE;net=gross-fee
        # Strictly after entry and before exit: conservative stated boundary convention.
        a=np.searchsorted(ts,t,side="right");b=np.searchsorted(ts,et,side="left")
        b=max(a,b);ok=missing[b]==missing[a];fc=d*(fp[b]-fp[a]) if ok else None
        trades.append(dict(entry_utc=base.dt(t).isoformat(),exit_utc=base.dt(et).isoformat(),side=d,entry_price=ep,exit_price=xp,
            stop_price=stop,initial_risk_points=r,gross_points=gross,fee_points=fee,net_points=net,net_R=net/r,
            net_R_fee_inclusive=net/(r+2*ep*base.FEE),holding_minutes=j-k,exit_reason=reason,funding_proxy_cost=fc))
    months=[f"{base.dt(start).year}-{m:02d}" for m in range(base.dt(start).month,13)]
    return risk.risk_summary(trades,months),trades
def funded(ts,months):
    if any(t["funding_proxy_cost"] is None for t in ts):return None
    adjusted=[]
    for t in ts:
        u=t.copy();u["net_points"]-=t["funding_proxy_cost"];u["net_R"]=u["net_points"]/t["initial_risk_points"]
        u["net_R_fee_inclusive"]=u["net_points"]/(t["initial_risk_points"]+2*t["entry_price"]*base.FEE);adjusted.append(u)
    s=risk.risk_summary(adjusted,months)
    s["funding_proxy_cost"]=math.fsum(t["funding_proxy_cost"] for t in ts);return s
def tests():
    audit.tests()
    rng=np.random.default_rng(17);c=100+np.cumsum(rng.normal(0,.2,240*65));o=np.r_[c[0],c[:-1]];bars=np.array([o,np.maximum(o,c)+.2,np.minimum(o,c)-.2,c])
    p=indicator_pack(bars,(20,50));q=indicator_pack(bars[:,:240*60],(20,50))
    for a,b in zip(p,q):assert np.allclose(a[:len(b)],b,equal_nan=True)
    assert np.array_equal(p[0],base.signals(base.features(bars,15))["ema-pullback"])
    assert np.array_equal(slice_pack(p,0,bars.shape[1])[0],p[0])
def run():
    tests();OUT.mkdir(parents=True,exist_ok=True);by_year={}
    y24=(base.data24.START,base.data24.END,base.data24.candles_2024);y25=(base.data25.START,base.data25.END,base.data25.candles)
    assert y24[1]==y25[0]
    b24=base.read_bars(y24[2],y24[0],y24[1]);b25=base.read_bars(y25[2],y25[0],y25[1]);both=np.concatenate([b24,b25],axis=1);offset=b24.shape[1]
    with gzip.open(OUT/"all_ledgers.jsonl.gz","wt") as ledger:
        for year,bars,(start,end,_),off in ((2024,b24,y24,0),(2025,b25,y25,offset)):
            funding=funding_proxy(year,bars,start,end);by_year[year]={}
            for pair in PAIRS:
                reset=slice_pack(indicator_pack(bars,pair),0,bars.shape[1])
                continuous=reset if year==2024 else slice_pack(indicator_pack(both,pair),off,bars.shape[1])
                for candidate,mult,days,slip,w in itertools.product(CANDIDATES,MULTS,DAYS,SLIPS,WARM):
                    key=f"{candidate}|{pair[0]}/{pair[1]}|{mult:g}|{days}|{slip}|{w}"
                    s,ts=replay(bars,reset if w=="reset" else continuous,candidate,mult,days,slip,start,end,funding)
                    if pair==(20,50) and mult==2 and days=="all" and slip==0 and w=="reset":
                        assert math.isclose(s["net"],EXPECTED[year][candidate],abs_tol=1e-6),(year,key,s["net"])
                    fs=funded(ts,list(s["monthly_entry_attribution"]));by_year[year][key]=(s,ts,fs)
                    ledger.write(json.dumps(dict(year=year,key=key,summary=s,proxy_summary=fs,trades=ts),separators=(",",":"),allow_nan=False)+"\n")
            print("YEAR_COMPLETE",year,len(by_year[year]),flush=True)
    fields=("trades","net","profit_factor","profitable_months","realized_drawdown_points","fee_R","fee_pf","fee_months","fee_dd_R","points_without_top1","points_without_top3","points_without_top5","fee_R_without_top3")
    rows=[]
    for key,(a,ta,fa) in by_year[2024].items():
        b,tb,fb=by_year[2025][key];months=list(a["monthly_entry_attribution"])+list(b["monthly_entry_attribution"])
        s=risk.risk_summary(ta+tb,months);fs=funded(ta+tb,months)
        row=dict(key=key,**{k:s[k] for k in fields})
        for prefix,ys in (("2024_",a),("2025_",b),("proxy_",fs),("2024_proxy_",fa),("2025_proxy_",fb)):
            row.update({prefix+k:ys[k] if ys is not None else None for k in fields})
        row["proxy_funding_cost"]=fs["funding_proxy_cost"] if fs is not None else None
        rows.append(row);print("RESULT",json.dumps(row,separators=(",",":"),allow_nan=False))
    assert len(rows)==540
    with (OUT/"all_results.csv").open("w",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    (OUT/"provenance.json").write_text(json.dumps(dict(candidates=CANDIDATES,pairs=PAIRS,atr=MULTS,days=DAYS,slippage_per_side=SLIPS,warmup=WARM,
        rules="EMA pair varied jointly across all timeframes; same closed-bar pullback/reversal logic; weekday entry restriction IST only, exits always active; continuous indicators across year boundary, both methods flat at year boundary; 2024 begins Feb1 12 UTC, no prior gap fill",
        costs="0.05% taker per side plus 18% GST, adverse slippage at both fills, no liquidation; proxy separate, assumed UTC 8h, last completed hourly funding percent and settlement-minute mark open; not actual settlements; missing rate/mark yields unavailable proxy for affected trade",
        selection="540 full factorial scenarios; duplicates due to identical 2024 warmup; no 2026, no parameter selection"),indent=2))
    print("TOTAL",len(rows),"BOTH_POINTS",sum(r["2024_net"]>0 and r["2025_net"]>0 for r in rows),"PROXY_COMPLETE",sum(r["proxy_net"] is not None for r in rows))
if __name__=="__main__":run()
