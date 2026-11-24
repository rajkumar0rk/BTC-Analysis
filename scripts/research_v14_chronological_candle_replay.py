#!/usr/bin/env python3
"""Causal V14 interpretation. Rebuild candidate signals from OHLC, no trade CSVs.
Single actual realized-PnL state (not retrospective shadow ledgers).
Priority = original layer order; no reservation of future entries.
Both OHLC paths tested independently. Cost stress charged at close.
"""
import json, hashlib
from pathlib import Path
from collections import defaultdict
import numpy as np
import pandas as pd
import research_supertrend_15m_line_touch as base
import research_supertrend_15m_filter_grid as filt
import research_st_three_best_combined_portfolio as port
import research_st_touch075_flip_lowvol_combination as original
import research_st_touch_flip_causal_regime_filters as htf
import research_second_green_percent_rr_scenarios as rr
import backtest_st_ema20_large_percent_locks as ema
import research_st_ema20_reclaim_loss_months_20261122 as rf
import backtest_st_ema20_reversal_only as flip
import research_btc_regime_attribution_20261121 as shock

OUT=Path("analysis/v14_chronological_candle_replay")
OUT.mkdir(parents=True,exist_ok=True)
FEE=.00059
SLIP=5.
COSTS=(0,10,25,50,60,75,100,125,150,175,200,225,250)
PATHS=("open_high_low_close","open_low_high_close")
MONTHS=pd.period_range("2025-01","2026-10",freq="M").astype(str).tolist()
def load():
    m,manifest=shock.load()
    # Retain complete UTC hours for feature construction, but stop execution
    # exactly at the end of October in IST.
    m=m.loc["2025-01-01":"2026-10-31 23:59:00"].copy()
    b=m.resample("15min").agg(open=("open","first"),high=("high","max"),low=("low","min"),close=("close","last"),volume=("volume","sum"))
    h=m.resample("1h").agg(open=("open","first"),high=("high","max"),low=("low","min"),close=("close","last"),volume=("volume","sum"))
    assert len(m)==len(b)*15==len(h)*60
    assert m.index[0]==pd.Timestamp("2025-01-01",tz="UTC")
    end=int(m.index.searchsorted(pd.Timestamp("2026-11-01",tz="Asia/Kolkata").tz_convert("UTC")))
    return m,b,h,end
def make_signals(m,b,h,end):
    events=defaultdict(list)
    op=m.open.to_numpy(float); hi=m.high.to_numpy(float); lo=m.low.to_numpy(float)
    st,tr=base.supertrend(b)
    vol,ap,ar=filt.build_features(b)
    rr.configure_grid(); port.SPECS=original.COHORTS
    touch,stops=filt.candidate_touch_events(m,b,st,tr,vol,ap,ar)
    raw=port.decode_signals(m,b,tr,vol,ap,ar,touch,stops)
    g=htf.features(b,tr)
    cycB=np.cumsum((tr==-1)&np.r_[True,tr[:-1]!=-1])
    cycS=np.cumsum((tr==1)&np.r_[True,tr[:-1]!=1])
    close=b.close.to_numpy(float); bo=b.open.to_numpy(float)
    bh=b.high.to_numpy(float); bl=b.low.to_numpy(float)
    def add(j,name,side,kind,priority,**kw):
        if 0<=j<end:
            events[j].append(dict(j=int(j),name=name,side=int(side),kind=kind,priority=priority,**kw))
    for name,rows in raw.items():
        for _,bar,j,mid,line in rows:
            bar=int(bar);j=int(j)
            ok=g["1h_above_ema20_and_rising"].iat[bar] if name=="line_touch" else g["1h_rsi50"].iat[bar]
            if ok:
                add(j,name,1,"fixed",0 if name=="line_touch" else 1,sl=.75 if name=="line_touch" else 3.,tp=1.5 if name=="line_touch" else .5,cycle=("15m",int(cycB[bar-1])),sttf=15,lock=name=="line_touch",gate="always")
    for i in range(15,len(b)-2):
        if tr[i-1]==-1 and tr[i]==1 and tr[i+1]==1 and close[i+1]<bo[i+1] and not close[i+1]>st[i] and np.isfinite(vol[i]) and vol[i]<=.8 and np.isfinite(ap[i]) and ap[i]>=.2:
            add((i+2)*15,"bearish_flip",-1,"fixed",2,sl=1.,tp=.3,cycle=("15m",-int(cycS[i])),sttf=15,gate="always")
    # Raw 15m setups, recomputed from all closed bars, not selected trade ledgers.
    e20=b.close.ewm(span=20,adjust=False).mean().to_numpy()
    d=b.close.diff(); u=d.clip(lower=0).ewm(alpha=.5,adjust=False,min_periods=2).mean()
    dn=(-d.clip(upper=0)).ewm(alpha=.5,adjust=False,min_periods=2).mean()
    rsi=(100*u/(u+dn).replace(0,np.nan)).to_numpy()
    z=((b.close-b.close.rolling(20).mean())/b.close.rolling(20).std(ddof=0).clip(lower=1e-10)).to_numpy()
    h1=b.resample("1h").close.last(); he=h1.ewm(span=20,adjust=False).mean()
    htrend=np.sign(h1-he).shift(1).reindex(b.index,method="ffill").fillna(0).to_numpy()
    h4=b.resample("4h").close.last(); h4trend=np.sign(h4-h4.ewm(span=20,adjust=False).mean()).shift(1).reindex(b.index,method="ffill").fillna(0).to_numpy()
    for i in range(25,len(b)-1):
        j=(i+1)*15
        if j>=end:break
        aligned=htrend[i+1]<0
        def s(name,sl,tp,cap,priority,gate,atr=0,align=False,ep=1):
            if (atr==0 or (np.isfinite(ap[i]) and ap[i]>=atr)) and (not align or aligned):
                add(j,name,-1,"fixed",priority,sl=sl,tp=tp,cap=cap,gate=gate,episode=ep)
        if z[i]>=2:
            s("BB_stretch",1,1,240,3,"bb",.3,True,2)
            s("BB_recovery",1,1,240,23,"v13bb",.3,True,2)
        if close[i]<np.min(bl[i-12:i]):s("Donchian12",1,1.5,480,4,"dc",.4,True)
        if rsi[i-1]>=80 and rsi[i]<80:s("RSI_cross20",1,1,480,5,"r20",0,True)
        if rsi[i-1]>=95 and rsi[i]<95:
            s("RSI_cross5",1,1,480,8,"r5",.4,False,2)
            s("RSI_cross5_late",1,1,480,26,"v14r5",.4,False,2)
        if rsi[i-1]>=90 and rsi[i]<90:
            s("RSI_reversal",.6,1.5,240,9,"rev",.3,True,2)
            s("RSI_reversal_late",.6,1.5,240,27,"v14rev",.3,True,2)
        if tr[i]==tr[i-1] and tr[i-1]!=tr[i-2]:
            side=1 if tr[i]==-1 else -1
            if side*(close[i]-bo[i])>0:
                if side==-1 and vol[i-1]<=1. and ap[i-1]>=.4:
                    add(j,"confirm_short",-1,"fixed",6,sl=1.,tp=1.5,cycle=("15m",-int(cycS[i])),sttf=15,gate="always")
                if side==1 and vol[i-1]<=.8 and ap[i-1]>=.2 and h4trend[i+1]>0:
                    add(j,"confirm_long",1,"fixed",7,sl=.5,tp=1.5,cycle=("15m",int(cycB[i])),sttf=15,gate="always")
    # Full raw H1 next-hour breakout triggers. Skip signals that never cross.
    eh=rf.indicator_features(ema.features(h))
    def trigger(ev,hour,with_risk=False):
        if hour>=len(h):return None
        side=ev["side"]; start=hour*60; stop=min(start+60,end)
        ids=np.flatnonzero((hi[start:stop]>=ev["trigger"]) if side==1 else (lo[start:stop]<=ev["trigger"]))
        if not len(ids):return None
        j=start+int(ids[0]); mid=max(op[j],ev["trigger"]) if side==1 else min(op[j],ev["trigger"])
        if with_risk and not 0<side*(mid+side*SLIP-ev["stop"])<=ev["max_risk"]:return None
        return j,mid
    for mode in ("touch","reclaim"):
        for hour,ev in ema.setups(eh,mode).items():
            zt=trigger(ev,hour)
            if zt is None:continue
            j,mid=zt; side=ev["side"]; f=eh.loc[pd.Timestamp(ev["signal"])]
            if not np.isfinite(f.volume_ratio) or f.volume_ratio<1.25 or (mode=="touch" and f.volume_ratio>2.5):continue
            common=dict(mid=mid,cycle=("1h_"+mode,ev["cycle"]),sttf=60)
            if mode=="touch":
                add(j,"EMA20_touch",side,"ladder",11,sl=3.,ladder=(.16,.18,.2,.21,.3,.5,1.,2.),gate="always",**common)
            else:
                if f.ema_gap_pct<=.75:
                    if side==-1:add(j,"EMA20_reclaim_short",side,"ladder",10,sl=2.,ladder=(2.,3.,5.),gate="rec7",**common)
                    add(j,"EMA20_reclaim_recovery",side,"ladder",16,sl=2.,ladder=(2.,3.,5.),gate="rec11",**common)
                if side==1:add(j,"EMA20_reclaim_long",side,"ladder",12,sl=2.,ladder=(2.,3.,5.),gate="rec8",**common)
                if f.adx14>=15 and f.ema_slope_pct<=.1:
                    add(j,"EMA20_ADX_reclaim",side,"ladder",20,sl=2.,ladder=(1.75,2.,3.,5.),gate="rec13",**common)
                add(j,"EMA20_reclaim_late",side,"ladder",25,sl=2.,ladder=(2.,3.,5.),gate="rec14",**common)
    fh=flip.features(h)
    for hour,ev in flip.setups(fh,"combined").items():
        zt=trigger(ev,hour,True)
        if zt is None or ev["side"]!=-1:continue
        j,mid=zt
        for p,gate in ((14,"flip9"),(22,"flip13")):
            add(j,"H1_ST_flip_exit",-1,"flip",p,mid=mid,cycle=("1h_flip",ev["cycle"]),sttf=60,gate=gate)
    sh=shock.features(m)
    ss=shock.prepare_signals(sh)["donchian_breakout"]
    for i in np.flatnonzero((ss!=0)&sh.regime.eq("shock").to_numpy()):
        j=(int(i)+1)*60; side=int(ss[i]); atr=float(sh.atr.iat[i])
        if not np.isfinite(atr) or atr<=0:continue
        for p,gate in ((13,"shock8"),(15,"shock9"),(17,"shock10"),(18,"shock11"),(19,"shock12a"),(19,"shock12b"),(21,"shock13a"),(21,"shock13b"),(21,"shock13c"),(21,"shock13d"),(24,"shock14a"),(28,"shock14b")):
            add(j,"Shock_Donchian",side,"shock",p,gate=gate,risk=1.8*atr,cap=2160)
    return events,st,tr,eh.side.to_numpy(),fh.side.to_numpy()
def allowed(rule,side,p,a,d):
    # p is actual portfolio realized month PnL after costs. a is days since
    # actual last closed loss. No frozen future trade reservations.
    if rule=="always":return True
    if rule=="bb":return p<0 and a<=3
    if rule=="dc" or rule=="r5":return p<0 and a<=7
    if rule=="r20":return p<-500 and a<=3
    if rule=="rev":return p<-200 and a<=.25
    if rule=="rec7":return p<100
    if rule=="rec8":return p<900 and 1<=a<=30 and d>=10
    if rule=="shock8":return side==-1 and p<900 and 3<=a<=5 and d>=15
    if rule=="shock9":return 100<=p<250 and d>=15
    if rule=="flip9":return 100<=p<1500 and a<=21 and d>=18
    if rule=="shock10":return 0<=p<100 and a<=5 and d>=5
    if rule=="rec11":return p<1500 and 3<=a<=8 and 5<=d<=10
    if rule=="shock11":return 900<=p<1750 and 5<=a<=14 and 18<=d<=20
    if rule=="shock12a":return p<100 and a<=45 and d==16
    if rule=="shock12b":return p<1000 and a<=14 and 22<=d<=24
    if rule=="shock13a":return side==-1 and 750<=p<1000 and 1<=a<=5 and 18<=d<=27
    if rule=="shock13b":return 750<=p<1000 and 3<=a<=10 and 5<=d<=14
    if rule=="rec13":return 0<=p<750 and 7<=a<=14 and 10<=d<=24
    if rule=="shock13c":return side==1 and 1500<=p<3000 and 3<=a<=10 and 18<=d<=24
    if rule=="shock13d":return p<-500 and a<=5 and 15<=d<=24
    if rule=="flip13":return p<1500 and 10<=a<=30 and 25<=d<=27
    if rule=="v13bb":return p<250 and a<=45 and d<=7
    if rule=="shock14a":return side==1 and p<1500 and 14<=a<=30 and 15<=d<=27
    if rule=="rec14":return 750<=p<1500 and 1<=a<=14 and 20<=d<=24
    if rule=="v14r5":return p<1500 and a<=45 and d<=7
    if rule=="v14rev":return p<250 and a<=21 and d<=7
    if rule=="shock14b":return side==-1 and 250<=p<1500 and 1<=a<=3 and d<=20
    raise ValueError(rule)
def replay(m,end,events,st,tr,eh,fh,cost,path):
    op=m.open.to_numpy(float);hi=m.high.to_numpy(float);lo=m.low.to_numpy(float);cl=m.close.to_numpy(float)
    ist=m.index.tz_convert("Asia/Kolkata"); months=ist.strftime("%Y-%m").to_numpy(); weekdays=ist.dayofweek.to_numpy(); days=ist.day.to_numpy(); dates=ist.strftime("%Y-%m-%d").to_numpy()
    monthly=defaultdict(float); used=set(); episode_count=defaultdict(int); daily=set()
    trades=[]; pos=None; last_loss=None; realized=0.; peak=0.; dd=0.; mtm_peak=0.; mtm_dd=0.; blocked=0
    def finish(j,mid,why):
        nonlocal pos,last_loss,realized,peak,dd
        p=pos;side=p["side"];entry=p["entry"]; xp=mid-side*SLIP; fee=FEE*(entry+xp); net=side*(xp-entry)-fee-cost
        realized+=net; monthly[months[j]]+=net; peak=max(peak,realized);dd=max(dd,peak-realized)
        if net<0:last_loss=j
        trades.append(dict(strategy=p["name"],gate=p["gate"],side=side,entry_utc=str(m.index[p["j"]]),exit_utc=str(m.index[j]),month=months[j],entry=entry,exit=xp,fee_gst=fee,extra_cost=cost,net=net,exit_reason=why))
        pos=None
    for j in range(end):
        # Process existing position and completed candle exits before new open orders.
        # No new entry in the same minute as an exit, including open exits.
        exited=False
        if pos:
            p=pos; side=p["side"]; tf=p.get("sttf")
            fail=False
            if tf==15 and j%15==0 and j>p["j"] and j>=30:
                i=j//15-1
                fail=tr[i]!=-side or (side*(cl[j-1]-st[i-1])<0)
            if tf==60 and j%60==0 and j>p["j"]:
                hs=fh if p["kind"]=="flip" else eh
                fail=hs[j//60-1]!=side
            if fail:finish(j,op[j],"completed_ST_close");exited=True
        if not pos and not exited and weekdays[j]<5 and months[j] in MONTHS:
            a=np.inf if last_loss is None else (j-last_loss)/1440
            for e in sorted(events.get(j,()),key=lambda q:q["priority"]):
                if e.get("cycle") in used:continue
                if e.get("episode"):
                    if (e["name"],dates[j]) in daily or episode_count[(e["name"],last_loss)]>=e["episode"]:continue
                if not allowed(e["gate"],e["side"],monthly[months[j]],a,days[j]):continue
                pos=e.copy();side=e["side"];mid=e.get("mid",op[j]);entry=mid+side*SLIP
                pos.update(entry=entry,mid=mid)
                if e["kind"]=="shock":
                    pos["stop"]=mid-side*e["risk"];pos["target"]=mid+side*3*e["risk"]
                elif e["kind"] in ("fixed","ladder"):
                    pos["stop"]=entry*(1-side*e["sl"]/100)
                    if e["kind"]=="fixed":pos["target"]=entry*(1+side*e["tp"]/100)
                if e.get("cycle") is not None:used.add(e["cycle"])
                if e.get("episode"):
                    daily.add((e["name"],dates[j]));episode_count[(e["name"],last_loss)]+=1
                break
        elif events.get(j):blocked+=len(events[j])
        if pos:
            p=pos; side=p["side"]; kind=p["kind"]; mid=None;why=None
            if kind=="ladder":
                # Source simulator clips entry candle path at actual trigger.
                part=ema.simulate_bar(ema.bar_path(op[j],hi[j],lo[j],cl[j],path),side,p["entry"],p["mid"],p["stop"],p["ladder"],j==p["j"])
                p["stop"]=part["stop"]
                if part["exit_mid"] is not None:mid=float(part["exit_mid"]);why="ladder_or_stop"
            elif kind in ("fixed","shock"):
                stop=p["stop"];target=p["target"]
                if (lo[j]<=stop if side==1 else hi[j]>=stop):
                    mid=min(op[j],stop) if side==1 else max(op[j],stop);why="stop_first"
                elif (hi[j]>=target if side==1 else lo[j]<=target):mid=target;why="target"
                elif p.get("lock") and hi[j]>=p["entry"]*1.01:
                    # Activation only applies to the NEXT candle.
                    p["stop"]=max(stop,p["entry"]*1.004)
            if mid is None:
                if (p.get("cap") and j-p["j"]+1>=p["cap"]) or (kind=="shock" and (j+1==end or months[j+1]!=months[j])):mid=cl[j];why="timeout_or_month_end"
                elif j==end-1:mid=cl[j];why="test_end_mark"
            if mid is not None:finish(j,mid,why)
        marked=realized
        if pos:
            xp=cl[j]-pos["side"]*SLIP
            marked+=pos["side"]*(xp-pos["entry"])-FEE*(xp+pos["entry"])-cost
        mtm_peak=max(mtm_peak,marked);mtm_dd=max(mtm_dd,mtm_peak-marked)
    assert pos is None
    vals=[float(monthly[x]) for x in MONTHS]
    n=np.array([t["net"] for t in trades],float)
    assert abs(sum(vals)-realized)<1e-6
    assert all(pd.Timestamp(t["entry_utc"]).tz_convert("Asia/Kolkata").dayofweek<5 for t in trades)
    assert all(pd.Timestamp(a["exit_utc"])<pd.Timestamp(b["entry_utc"]) for a,b in zip(trades,trades[1:]))
    return dict(cost=cost,path=path,trades=len(n),wins=int((n>0).sum()),net_points=realized,closed_dd_points=dd,mtm_close_dd_points=mtm_dd,profit_factor=float(n[n>0].sum()/max(1e-12,-n[n<0].sum())),positive_months=sum(x>0 for x in vals),months_ge_1pct=sum(x>=1000 for x in vals),min_month_points=min(vals),blocked_signal_count=blocked),vals,trades
def main():
    m,b,h,end=load()
    print("DATA",len(m),end,str(m.index[0]),str(m.index[end-1]),flush=True)
    events,st,tr,eh,fh=make_signals(m,b,h,end)
    print("SIGNALS",len(events),sum(map(len,events.values())),flush=True)
    rows=[];mons=[]
    for path in PATHS:
        for cost in COSTS:
            s,vals,t=replay(m,end,events,st,tr,eh,fh,cost,path)
            rows.append(s);mons.extend(dict(cost=cost,path=path,month=mo,net_points=v) for mo,v in zip(MONTHS,vals))
            pd.DataFrame(t).to_csv(OUT/f"trades_{path}_{cost}.csv",index=False)
            pd.DataFrame(rows).to_csv(OUT/"summary.csv",index=False)
            pd.DataFrame(mons).to_csv(OUT/"monthly.csv",index=False)
            print("RESULT",json.dumps(s),flush=True)
    (OUT/"quality.json").write_text(json.dumps(dict(candles=end,first=str(m.index[0]),last=str(m.index[end-1]),entry_days="Mon-Fri IST",single_position=True,raw_trade_ledgers_read=False,recovery_state="actual closed portfolio net; no shadow reservation",cost_model="uniform taker 0.05% + GST each side, 5 points per fill, extra points per close",funding="not modeled: settlement not verified",liquidation="not modeled; price points not leveraged returns",independent_ohlc_paths=True,unseen_holdout=False,interpretation="V14 causal adaptation, not exact hindsight-selected portfolio"),indent=2)+"\n")
if __name__=="__main__":main()
