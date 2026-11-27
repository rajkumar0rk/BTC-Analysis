"""Independent vectorized fill audit and outlier sensitivity for all 24 H4 reversal variants."""
import csv,gzip,json,math
from datetime import datetime
from pathlib import Path
import numpy as np
import research_independent_big_move_2024_2025 as base
import research_independent_big_move_mtf_2024_2025 as mtf
import research_independent_big_move_exits_2024_2025 as exits
OUT=Path("scratch/independent_big_move_audit")
def stamp(s):return int(datetime.fromisoformat(s).timestamp())
def independent_exit(bars,k,d,stop,flips):
    O,H,L,C=bars
    # Search the stop and the scheduled crossover independently.
    # A stop gap takes priority; market crossover at open precedes intraminute stop.
    candidates=flips[d];q=np.searchsorted(candidates,k,side="right")
    cross=int(candidates[q]) if q<len(candidates) else len(O)
    limit=min(cross+1,len(O))
    hit=np.flatnonzero((L[k:limit]<=stop) if d==1 else (H[k:limit]>=stop))
    j=k+int(hit[0]) if len(hit) else len(O)
    if j<=cross and j<len(O) and d*(O[j]-stop)<=0:return j,float(O[j]),"Initial/trailing stop"
    if cross<=j and cross<len(O):return cross,float(O[cross]),"H4 EMA reversal"
    if j<len(O):return j,stop,"Initial/trailing stop"
    return len(O)-1,float(C[-1]),"End of yearly evaluation"
def cross_schedule(h4):
    return {d:(np.flatnonzero((h4[:-1]==d)&(h4[1:]==-d))+2)*240 for d in (1,-1)}
def audit(bars,f,sig,h4,start,end,v,year):
    O,H,L,C=bars;flips=cross_schedule(h4);free=0;idx=0;rows=[]
    for i in np.flatnonzero(sig):
        k=(int(i)+1)*15
        if k>=len(O) or k<free:continue
        d=int(sig[i]);ep=float(O[k]);risk=max(base.TICK,math.ceil(2*f["atr"][i]/base.TICK)*base.TICK)
        stop=ep-d*risk
        j,xp,reason=independent_exit(bars,k,d,stop,flips)
        t=v["trades"][idx];idx+=1;free=j+1
        expected_exit=end if reason=="End of yearly evaluation" else start+j*60
        assert stamp(t["entry_utc"])==start+k*60 and stamp(t["exit_utc"])==expected_exit
        assert t["side"]==d and t["entry_price"]==ep and t["stop_price"]==stop
        assert math.isclose(t["exit_price"],xp,abs_tol=1e-8) and t["exit_reason"]==reason,(t,j,xp,reason)
        gross=d*(xp-ep);fees=(ep+xp)*base.FEE;net=gross-fees
        assert math.isclose(t["net_points"],net,abs_tol=1e-8)
        assert math.isclose(t["net_R"],net/risk,abs_tol=1e-9)
        z=k//240-1;trend=int(h4[z]) if z>=0 else 0
        rows.append(dict(year=year,strategy=v["key"],entry_utc=t["entry_utc"],exit_utc=t["exit_utc"],side=d,
            entry_price=ep,exit_price=xp,initial_risk_points=risk,risk_pct=100*risk/ep,holding_hours=(j-k)/60,
            entry_h4_trend=trend,entry_alignment="aligned" if trend==d else "opposite" if trend==-d else "unknown",
            reason=reason,net_points=net,net_R=net/risk,fee_points=fees,net_R_fee_inclusive=net/(risk+2*ep*base.FEE),
            adverse_gap_points=max(0,d*(stop-xp)) if reason=="Initial/trailing stop" else 0))
    assert idx==len(v["trades"])
    return rows
def stats(ts):
    n=len(ts);p=[t["net_points"] for t in ts];r=[t["net_R"] for t in ts]
    def metrics(a):
        gains=math.fsum(max(0,x) for x in a);loss=-math.fsum(min(0,x) for x in a)
        ordered=sorted((x for x in a if x>0),reverse=True)
        return dict(net=math.fsum(a),pf=gains/loss if loss else None,largest=ordered[0] if ordered else 0,
            top1_share_of_gross_wins=ordered[0]/gains if gains else None,
            remove_top1=math.fsum(a)-sum(ordered[:1]),remove_top3=math.fsum(a)-sum(ordered[:3]),remove_top5=math.fsum(a)-sum(ordered[:5]))
    return dict(trades=n,points=metrics(p),R=metrics(r),fee_inclusive_R=metrics([t["net_R_fee_inclusive"] for t in ts]),
        median_risk_pct=float(np.median([t["risk_pct"] for t in ts])) if n else None,
        median_hold_hours=float(np.median([t["holding_hours"] for t in ts])) if n else None,
        max_hold_hours=max((t["holding_hours"] for t in ts),default=0),
        opposite_entry_count=sum(t["entry_alignment"]=="opposite" for t in ts),
        unknown_entry_count=sum(t["entry_alignment"]=="unknown" for t in ts),
        stop_gap_count=sum(t["adverse_gap_points"]>0 for t in ts),
        biggest_R_trade=max(ts,key=lambda t:t["net_R"]) if n else None)
def tests():
    O=np.full(800,100.);H=O+1;L=O-1;C=O.copy()
    f={1:np.array([480]),-1:np.array([],dtype=int)}
    assert independent_exit((O,H,L,C),60,1,90,f)==(480,100.,"H4 EMA reversal")
    L[480]=85
    assert independent_exit((O,H,L,C),60,1,90,f)==(480,100.,"H4 EMA reversal")
    O[480]=88
    assert independent_exit((O,H,L,C),60,1,90,f)==(480,88.,"Initial/trailing stop")
    L[200]=85
    assert independent_exit((O,H,L,C),60,1,90,f)==(200,90.,"Initial/trailing stop")
    assert np.array_equal(cross_schedule(np.array([0,1,-1,-1,1]))[1],np.array([720]))
def run():
    tests();exits.tests();results={};ledger=[]
    for year,start,end,reader in ((2024,base.data24.START,base.data24.END,base.data24.candles_2024),(2025,base.data25.START,base.data25.END,base.data25.candles)):
        bars=base.read_bars(reader,start,end);f=base.features(bars,15);ss=base.signals(f);align=mtf.filters(bars)
        h1=base.features(bars,60);st=exits.supertrend(h1)
        close4=bars[3,239::240];e20=base.ema(close4,20);e50=base.ema(close4,50)
        h4=np.where(e20>e50,1,np.where(e20<e50,-1,0)).astype(np.int8)
        for name in base.FAMILIES:
            for flt in mtf.FILTERS:
                sig=ss[name] if flt=="none" else np.where(ss[name]==align[flt],ss[name],0).astype(np.int8)
                v=exits.replay(bars,f,sig,name,flt,4,start,end,h1,st,h4)
                ts=audit(bars,f,sig,h4,start,end,v,year)
                ledger.extend(ts);results.setdefault(v["key"],{})[str(year)]=ts
    reports={}
    for key,ys in results.items():
        ts=ys["2024"]+ys["2025"];s=stats(ts);s["years"]={y:stats(t) for y,t in ys.items()};reports[key]=s
        print("AUDIT",key,json.dumps(s,separators=(",",":"),allow_nan=False))
    assert len(reports)==24
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"audit.json").write_text(json.dumps(reports,indent=2,allow_nan=False))
    with gzip.open(OUT/"trade_audit.csv.gz","wt",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(ledger[0]));w.writeheader();w.writerows(ledger)
    print("TOTAL",len(reports),"VERIFIED_TRADE_OBSERVATIONS",len(ledger))
if __name__=="__main__":run()
