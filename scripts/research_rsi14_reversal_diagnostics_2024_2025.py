"""Read-only diagnostic replay of three existing reversal configurations, no retuning."""
import csv,json,math,statistics
from datetime import datetime
from pathlib import Path
import numpy as np
import research_rsi14_reversal_regimes_2025 as regimes
import research_rsi14_reversal_multiple_r_2024 as prior24
import research_rsi14_80_20_2025 as source25
import research_rsi14_reversal_risk_grid_2024_2025 as grid
import research_rsi14_reversal_confirmation_2024_2025 as conf
OUT=Path("scratch/rsi14_reversal_diagnostics")

def stamp(s):return int(datetime.fromisoformat(s).timestamp())

def excursion(bars,k,last,side,entry,stop,target,exit_price,reason):
    # Replay exactly the Color path and end the excursion at the actual fill.
    # Never count any high or low reached after the stop or target.
    O,H,L,C=bars;favorable=adverse=0.;end=None
    def mark(p):
        nonlocal favorable,adverse
        q=side*(p-entry);favorable=max(favorable,q);adverse=max(adverse,-q)
    for j in range(k,last+1):
        o,h,l,c=map(float,(O[j],H[j],L[j],C[j]))
        if side*(o-stop)<=0:
            mark(o);end=(j,o,"Initial stop");break
        if side*(o-target)>=0:
            mark(target);end=(j,target,"Fixed target");break
        mark(o)
        path=(o,l,h,c) if c>o or (c==o and o-l<=h-o) else (o,h,l,c)
        for a,b in zip(path,path[1:]):
            if side*(b-a)<0 and side*(a-stop)>=0 and side*(b-stop)<=0:
                mark(stop);end=(j,stop,"Initial stop");break
            if side*(b-a)>0 and side*(a-target)<=0 and side*(b-target)>=0:
                mark(target);end=(j,target,"Fixed target");break
            mark(b)
        if end:break
    if end is None:
        assert reason=="End of yearly evaluation" and last==len(O)-1
        end=(last,float(C[last]),reason)
    assert end[0]==last and end[2]==reason and math.isclose(end[1],exit_price,abs_tol=1e-7),end
    return favorable,adverse

def tests():
    # Identical minute extremes, different candle colors. No post-exit MFE.
    a=np.array([100.]);h=np.array([125.]);l=np.array([85.])
    f,m=excursion((a,h,l,np.array([110.])),0,0,1,100,90,120,90,"Initial stop")
    assert (f,m)==(0,10)
    f,m=excursion((a,h,l,np.array([95.])),0,0,1,100,90,120,120,"Fixed target")
    assert (f,m)==(20,0)
    f,m=excursion((a,h,l,np.array([110.])),0,0,-1,100,110,90,90,"Fixed target")
    assert (f,m)==(10,0)

def diagnose(v,bars,rows,start,end,year):
    result=[]
    for tr in v["trades"]:
        k=(stamp(tr["entry_utc"])-start)//60
        last=min(len(bars[0])-1,(stamp(tr["exit_utc"])-start)//60)
        d=tr["side"];ep=tr["entry_price"];sl=tr["stop_price"];tp=tr["target_price"];risk=d*(ep-sl)
        b=rows[k//15-1];assert b["k"]==k and risk>0
        mfe,mae=excursion(bars,k,last,d,ep,sl,tp,tr["exit_price"],tr["exit_reason"])
        result.append(dict(year=year,strategy=v["key"],entry_utc=tr["entry_utc"],exit_utc=tr["exit_utc"],side="long" if d==1 else "short",
            entry_price=ep,initial_risk_points=risk,exit_reason=tr["exit_reason"],gross_points=tr["gross_points"],fee_points=tr["fee_points"],net_points=tr["net_points"],
            net_R=tr["net_points"]/risk,mfe_points=mfe,mae_points=mae,mfe_R=mfe/risk,mae_R=mae/risk,
            fee_R=tr["fee_points"]/risk,atr14=b["atr"],adx14=b["adx"],h4_alignment="unknown" if b["ema"] is None else ("aligned" if d*(b["h4close"]-b["ema"])>0 else "countertrend"),
            atr_pct=100*b["atr"]/ep,setup_delay_minutes=(stamp(tr["entry_utc"])-stamp(tr["trigger_utc"]))//60,holding_minutes=last-k))
    return result

def metrics(ts):
    n=len(ts);wins=[t for t in ts if t["net_points"]>0];losses=[t for t in ts if t["net_points"]<=0];stops=[t for t in ts if t["exit_reason"]=="Initial stop"]
    avg=lambda key:statistics.mean(t[key] for t in ts) if n else None
    median=lambda key:statistics.median(t[key] for t in ts) if n else None
    def reach(group):return {str(r):sum(t["mfe_R"]>=r-1e-9 for t in group) for r in (.25,.5,1,1.5,2)}
    gross=math.fsum(t["gross_points"] for t in ts);fees=math.fsum(t["fee_points"] for t in ts);net=math.fsum(t["net_points"] for t in ts)
    return dict(trades=n,wins=len(wins),losses=len(losses),win_rate=100*len(wins)/n if n else None,stop_exits=len(stops),target_exits=sum(t["exit_reason"]=="Fixed target" for t in ts),
        gross_points=gross,fees=fees,net=net,avg_net=net/n if n else None,avg_net_R=avg("net_R"),median_mfe_R=median("mfe_R"),median_mae_R=median("mae_R"),
        median_stop_points=median("initial_risk_points"),median_fee_R=median("fee_R"),median_setup_delay_minutes=median("setup_delay_minutes"),
        median_atr_pct=median("atr_pct"),median_adx14=median("adx14") if n and all(t["adx14"] is not None for t in ts) else None,
        reach_all=reach(ts),reach_losers=reach(losses),reach_stops=reach(stops),
        gross_winners_net_losers=sum(t["gross_points"]>0 and t["net_points"]<=0 for t in ts))

def grouped(ts):
    groups={}
    for key,func in (("side",lambda t:t["side"]),("adx",lambda t:"unknown" if t["adx14"] is None else ("below25" if t["adx14"]<25 else "25plus")),("h4_alignment",lambda t:t["h4_alignment"])):
        groups[key]={}
        for t in ts:groups[key].setdefault(func(t),[]).append(t)
        groups[key]={k:metrics(v) for k,v in groups[key].items()}
    return groups

def run():
    regimes.tests();conf.confirmation_tests();tests()
    all_trades=[];report={}
    configs=((15,False,"15m-baseline"),(60,False,"1h-sweep"),(60,True,"1h-sweep-contraction"))
    expected={2024:(3651.574285,1797.47779,630.50891),2025:(10112.85959,7121.862695,8625.62726)}
    for year,start,end,reader in ((2024,prior24.START,prior24.END,prior24.candles_2024),(2025,source25.START,source25.END,source25.candles)):
        regimes.START,regimes.END,regimes.candles=start,end,reader;grid.START,grid.END=start,end
        bars,rows,signals,rec=regimes.load_data()
        vals15=[r["r"] for r in rows];vals60=conf.hourly_rsi(rows,start)
        es={15:conf.make_entries(rows,signals,vals15),60:conf.make_entries(rows,conf.threshold_signals(vals60),vals60)}
        for (tf,contraction,key),net in zip(configs,expected[year]):
            cfg=dict(key=key,entry="liquidity-sweep",sl=1.5,tp=2,management="fixed",activation=0,distance=0)
            v=grid.replay(bars,rows,es[tf][("none",contraction)],cfg,rec)
            assert math.isclose(v["summary"]["net"],net,abs_tol=1e-6),v["summary"]
            ts=diagnose(v,bars,rows,start,end,year);all_trades.extend(ts)
            s=metrics(ts);assert math.isclose(s["net"],net,abs_tol=1e-6)
            report[f"{key}-{year}"]=dict(overall=s,groups=grouped(ts))
            print("DIAG",key,year,json.dumps(s,separators=(",",":"),allow_nan=False))
            print("GROUPS",key,year,json.dumps(report[f"{key}-{year}"]["groups"],separators=(",",":"),allow_nan=False))
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"diagnostics.json").write_text(json.dumps(report,indent=2,allow_nan=False))
    with (OUT/"trade_diagnostics.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(all_trades[0]));w.writeheader();w.writerows(all_trades)
    print("TOTAL",len(all_trades),"trade observations across three configurations; overlapping trades not independent")
if __name__=="__main__":run()
