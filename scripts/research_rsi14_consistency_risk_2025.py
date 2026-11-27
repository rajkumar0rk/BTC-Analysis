"""Full coarse factorial on four retained candidates, with exposure overlays."""
import csv,gzip,hashlib,json,math,copy
from itertools import product
from pathlib import Path
import numpy as np
from numba import njit
from research_rsi14_entry_quality_2025 import load,indicators,setup_rows,eligible,checks
from research_rsi14_improvements_2025 import ROOT,START,END,FEE,dt,export_bundle
OUT=Path("scratch/rsi14_consistency_risk")
BASES={
 "original":((False,0.,False,False,False,False,False,False),38547.273445),
 "high-profit":((False,0.,True,False,True,True,False,True),42194.300585),
 "balanced":((False,.5,True,False,True,True,False,True),33167.765155),
 "adx-only":((False,0.,False,False,True,False,False,False),37329.133)}
BASE=(False,False,False,0,3.,False)
@njit
def run_trade(O,H,L,C,rsi,i,d,activation,stagnation,mid):
    ep=O[i];stop=ep-d*1000;act=ep+d*activation*1000;best=ep;armed=-1
    for j in range(i,len(O)):
        o,h,l,c=O[j],H[j],L[j],C[j]
        if d*(o-stop)<=0:return j,o,1 if armed<0 else 2,stop,armed
        if armed<0:
            if stagnation and j==i+stagnation*15 and d*(best-ep)<500:return j,o,3,stop,armed
            if mid and j>i and j%15==0 and d*(rsi[j//15]-50)<0 and d*(rsi[j//15-1]-50)>=0:return j,o,5,stop,armed
        if d*(o-best)>0:best=o
        if armed<0 and d*(o-act)>=0:armed=j
        if armed>=0 and d*(best-d*1000-stop)>0:stop=best-d*1000
        seq=(o,l,h,c) if c>o or (c==o and o-l<=h-o) else (o,h,l,c)
        for k in range(3):
            a,b=seq[k],seq[k+1]
            if d*(b-a)<0:
                if d*(a-stop)>=0 and d*(b-stop)<=0:return j,stop,1 if armed<0 else 2,stop,armed
            elif d*(b-a)>0:
                if d*(b-best)>0:best=b
                if armed<0 and d*(b-act)>=0:armed=j
                if armed>=0 and d*(best-d*1000-stop)>0:stop=best-d*1000
    return len(O)-1,C[-1],4,stop,armed

def retest(bars,first,d,level,until):
    O,H,L,C=bars
    # Breakout close already observed at first-1. Require later touch, then
    # completed close back beyond level. A same-bar touch/reclaim is valid.
    for k in range(first,until-1):
        if (L[k]<=level if d==1 else H[k]>=level) and d*(C[k]-level)>0:return k+1
    return -1

def summarize(trades):
    p=[t["net_points"] for t in trades];g=math.fsum(max(n,0) for n in p);l=-math.fsum(min(n,0) for n in p)
    months={f"2025-{m:02d}":0. for m in range(1,13)};stressed=months.copy();eq=peak=dd=0.
    for t,n in zip(trades,p):
        k=t["entry_utc"][:7];months[k]+=n;stressed[k]+=n-50*t["signal_context"]["size_multiplier"]
        eq+=n;peak=max(peak,eq);dd=max(dd,peak-eq)
    p50=[n-50*t["signal_context"]["size_multiplier"] for t,n in zip(trades,p)]
    g50=math.fsum(max(n,0) for n in p50);l50=-math.fsum(min(n,0) for n in p50)
    wins=sum(n>0 for n in p)
    return dict(accounting="realized",open_position=None,trades=len(p),net=math.fsum(p),wins=wins,win_rate=100*wins/len(p) if p else 0,profit_factor=g/l if l else None,
      realized_drawdown_points=dd,monthly_entry_attribution=months,profitable_months=sum(x>0 for x in months.values()),worst_month=min(months.values()),
      losing_months=sum(x<0 for x in months.values()),flat_months=sum(x==0 for x in months.values()),h1_net=sum(list(months.values())[:6]),h2_net=sum(list(months.values())[6:]),
      stress_extra_50_points_roundtrip=dict(net=math.fsum(p50),pf=g50/l50 if l50 else None,months=sum(x>0 for x in stressed.values())))

def entries(bars,ind,avg,setups,old,cfg):
    ret,vol,dist,stag,act,mid=cfg;O,H,L,C=bars;atr=ind[-1];out=[];free=0
    def allowed(i,d,depth,level):
        if not eligible(bars,ind,i,d,depth,old):return False
        if vol and not (.5*avg[i//15]<=atr[i//15]<=2*avg[i//15]):return False
        if dist and not (0<d*(C[i-1]-level)<=250):return False
        return True
    def transform(raw,d,depth,level,until):
        if not eligible(bars,ind,raw,d,depth,old):return -1
        i=retest(bars,raw,d,level,until) if ret else raw
        return i if i>=free and i<until and allowed(i,d,depth,level) else -1
    for first,d,r,trigger,level,pull,depth,until,retries in setups:
        if first<free:continue
        i=transform(first,d,depth,level,until)
        if i<0:continue
        for attempt in range(2 if old[-1] else 1):
            ep=float(O[i]);j,xp,reason,stop,armed=run_trade(O,H,L,C,ind[2],i,d,act,stag,mid)
            free=j+1;gross=d*(xp-ep);fee=(ep+xp)*FEE
            vals={"indicator_0":r}
            if np.isfinite(atr[i//15]):vals["indicator_1"]=float(atr[i//15])
            out.append(dict(entry_utc=dt(START+i*60).isoformat(),trigger_utc=dt(START+trigger*60).isoformat(),exit_utc=dt(END if reason==4 else START+j*60).isoformat(),side=d,entry_price=ep,exit_price=float(xp),stop_price=ep-d*1000,target_price=ep+d*act*1000,final_stop_price=float(stop),gross_points=float(gross),fee_points=float(fee),net_points=float(gross-fee),assumed_slippage_points=0,entry_reason="pullback-breakout retest" if ret else "pullback-breakout",exit_reason={1:"Initial stop loss",2:"Trailing stop",3:"Stagnation exit",4:"End of 2025",5:"RSI midpoint deterioration"}[reason],signal_context=dict(rsi14=r,depth=depth,retry=bool(attempt),breakout_level=level,entry_atr=float(atr[i//15]),activation_utc=dt(START+armed*60).isoformat() if armed>=0 else None,size_multiplier=1.),indicator_values=vals))
            if attempt or not old[-1] or reason!=1 or free>=until:break
            nxt=-1
            for k in retries:
                if k<free:continue
                nxt=transform(int(k),d,depth,level,until)
                if nxt>=0:break
            if nxt<0:break
            i=nxt
    return out

def sized(trades,adaptive,streak):
    out=[];losses=0
    for t in trades:
        v=t.copy();ctx=t["signal_context"].copy();q=1.
        if adaptive:q=min(1.,1000/(2*ctx["entry_atr"]))
        if streak and losses>=3:q*=.5
        ctx["size_multiplier"]=q;v["signal_context"]=ctx
        for k in ("net_points","gross_points","fee_points"):v[k]=t[k]*q
        if t["net_points"]<0:losses+=1
        elif t["net_points"]>0:losses=0
        out.append(v)
    return out

def run():
    checks()
    bars,signals,snapshots,extra,rec=load();ind=indicators(bars,snapshots);setups=setup_rows(bars,signals,snapshots,extra)
    atr=ind[-1];avg=np.full(len(atr),np.nan)
    for k in range(20,len(atr)):avg[k]=np.mean(atr[k-20:k])
    # Two policies, each using only completed candle data.
    a=np.array([10000.,10000.]);h=np.array([10200.,10100.]);l=np.array([9900.,9900.]);r=np.array([60.])
    assert run_trade(a,h,l,a,r,0,1,3.,0,False)[2]==4
    OUT.mkdir(parents=True,exist_ok=True)
    rows=[];tops={};single={};counts={};baseline_by={}
    with gzip.open(OUT/"all_ledgers.jsonl.gz","wt") as f:
      for name,(old,expected) in BASES.items():
        raw=entries(bars,ind,avg,setups,old,BASE);bs=summarize(raw)
        assert math.isclose(bs["net"],expected,abs_tol=1e-5),(name,bs["net"],expected)
        baseline_by[name]=bs
        counts[name]=dict(total=0,positive=0,months_up=0,dd_down=0,both=0,net_up_dd_down=0,best_months=0)
        for cfg in product((False,True),(False,True),(False,True),(0,8,16),(2.,2.5,3.),(False,True)):
          raw=entries(bars,ind,avg,setups,old,cfg);raws=summarize(raw)
          for adaptive,streak in product((False,True),repeat=2):
            trades=sized(raw,adaptive,streak);s=summarize(trades)
            ret,vol,dist,stag,act,mid=cfg
            s.update(raw_net=raws["net"],raw_dd=raws["realized_drawdown_points"],raw_months=raws["profitable_months"],
               net_change=s["net"]-bs["net"],dd_change=s["realized_drawdown_points"]-bs["realized_drawdown_points"],
               months_change=s["profitable_months"]-bs["profitable_months"],exposure_mean=float(np.mean([t["signal_context"]["size_multiplier"] for t in trades])) if trades else 0.)
            n=sum((ret,vol,dist,stag!=0,act!=3,mid,adaptive,streak))
            p=dict(base=name,retest=ret,volatility_band=vol,max_breakout_distance_250=dist,stagnation_bars=stag,activation_r=act,midpoint_exit=mid,adaptive_size=adaptive,loss_streak_half_size=streak,new_rules=n)
            key=f"{name}-ret{int(ret)}-vol{int(vol)}-dist{int(dist)}-stag{stag}-act{act:g}-mid{int(mid)}-size{int(adaptive)}-loss{int(streak)}"
            v=dict(key=key,name="RSI14 consistency "+key,parameters=p,summary=s,trades=trades)
            f.write(json.dumps(v,separators=(",",":"),allow_nan=False)+"\n")
            rows.append(dict(key=key,**p,**{k:x for k,x in s.items() if k not in ("monthly_entry_attribution","stress_extra_50_points_roundtrip","open_position")},**s["monthly_entry_attribution"],stress50_net=s["stress_extra_50_points_roundtrip"]["net"],stress50_months=s["stress_extra_50_points_roundtrip"]["months"]))
            c=counts[name];c["total"]+=1;c["positive"]+=s["net"]>0;c["months_up"]+=s["months_change"]>0;c["dd_down"]+=s["dd_change"]<-1e-7;c["both"]+=s["months_change"]>0 and s["dd_change"]<-1e-7 and s["net"]>0;c["net_up_dd_down"]+=s["net_change"]>1e-7 and s["dd_change"]<-1e-7;c["best_months"]=max(c["best_months"],s["profitable_months"])
            if n<=1:
                single[key]=v
                print("SINGLE",json.dumps(dict(key=key,**p,**s),separators=(",",":"),allow_nan=False))
            if s["net"]<=0 or s["trades"]<40:continue
            kind="sized" if adaptive or streak else "raw"
            for label,score in (("consistency",(s["profitable_months"],s["stress_extra_50_points_roundtrip"]["months"],-s["realized_drawdown_points"],s["net"])),("net",(s["net"],)),("dd",(-s["realized_drawdown_points"],s["net"])),("robust",(s["stress_extra_50_points_roundtrip"]["months"],s["profitable_months"],-s["realized_drawdown_points"]))):
                group=tops.setdefault((name,kind,label),[])
                group.append((score,key,v));group.sort(key=lambda a:(a[0],a[1]),reverse=True);del group[2:]
    assert len(rows)==2304,len(rows)
    with (OUT/"all_results.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    chosen={}
    for name in BASES:
        for k,v in single.items():
            if v["parameters"]["base"]==name and v["parameters"]["new_rules"]==0:chosen[k]=v
    for (name,kind,label),group in tops.items():
        for _,key,v in group:
            print("TOP",json.dumps(dict(rank=label,kind=kind,key=key,**v["parameters"],**v["summary"]),separators=(",",":"),allow_nan=False))
            # Publish raw fills only; scaled P&L has different accounting semantics.
            if kind=="raw":chosen[key]=v
    print("COUNTS",json.dumps(counts),"PUBLISHED",len(chosen))
    export_bundle(OUT/"backtest.json",family="rsi14-consistency-risk-2025",symbol="BTCUSD",unit="price points",start_utc=dt(START).isoformat(),end_utc=dt(END).isoformat(),execution_timeframe_minutes=1,signal_timeframe_minutes=15,costs="0.05% taker each side +18% GST; 1m Color; stop gaps at open; funding/liquidation excluded; extra 50 points per unit accounting stress.",variants=list(chosen.values()),recorder=rec,data_provenance=dict(manifest=str(ROOT/"manifest.json"),manifest_sha256=hashlib.sha256((ROOT/"manifest.json").read_bytes()).hexdigest(),input_minutes=len(bars[0]),timestamp_label="assumed open UTC",total_variants=len(rows),published_variants=len(chosen),full_archive="rsi14-consistency-risk-full",selection="four frozen 2025 candidates; full coarse factorial, not independent validation; ranking minimum 40 trades; scaled results only in archive",retest="later 1m touch and close beyond original breakout boundary; entry next open; original filters rechecked",volatility="ATR14 within 0.5 to 2 times mean previous 20 completed 15m ATR values",distance="breakout/retest close within 250 points of level; next-open gap not limited",stagnation="after 8 or 16 15m intervals from entry, exit at minute open if prior MFE below 500 before trail",midpoint="completed 15m RSI crosses adverse midpoint before trail",sizing="cap exposure at min(1,1000/(2ATR)); halve after 3 net losses until win; scaled per-unit P&L not account returns"))
if __name__=="__main__":run()
