#!/usr/bin/env python3
"""Small predeclared grid, training 2024/25 only, one frozen validation candidate."""
import sys,inspect,itertools,json,hashlib,os
from pathlib import Path
import numpy as np
import pandas as pd
import research_btc15m_worst_month_loss_pause_20261123 as base
OUT=Path("analysis/btc15m_c05_trade_diagnostics_20261124")
DATA=Path("_repaired/data/delta_india/BTCUSD/2024_verified_archive")
ARCHIVE_COMMIT="edcf60fa0a229108d09772dc6cbe04eb15476291"
TZ="Asia/Kolkata"
# Predeclared equity risk caps, inclusive of entry/stop fees and slippage.
# All ordinary entries retained; no increase beyond existing notional cap.
def config(threshold,weak,fraction=.25,hard=0.,smooth=False,dmi_size=1.,adx_tf=15,rise=0,rise_size=1.,vol_anchor=1.,vol_power=0.,timeout_hours=0,swing_bars=0,swing_buffer=0.,rvol_threshold=0.,rvol_weak=1.,er_bars=0,er_threshold=0.,early_trigger=0.,early_lock=-1.,age_limit=0,weak_target=0.,h4_exit=0,pre_protection=False,equity_risk=0.):
    assert early_trigger>=0 and -1<=early_lock<=0
    assert equity_risk in (0.,.005,.01,.015,.02)
    return dict(atr=3.5,rr=3.5,wait=2,flip=False,filter="h4ema50_volmin_0.8",activation=2.5,lock=0.,stage2=0.,lock2=1.,partial_trigger=3. if fraction else 0.,partial_fraction=fraction,trail_atr=0.,adx_min=hard,adx_threshold=threshold,weak_size=weak,smooth=smooth,dmi_size=dmi_size,adx_tf=adx_tf,rise=rise,rise_size=rise_size,vol_anchor=vol_anchor,vol_power=vol_power,timeout_hours=timeout_hours,swing_bars=swing_bars,swing_buffer=swing_buffer,rvol_threshold=rvol_threshold,rvol_weak=rvol_weak,er_bars=er_bars,er_threshold=er_threshold,early_trigger=early_trigger,early_lock=early_lock,age_limit=age_limit,weak_target=weak_target,h4_exit=h4_exit,pre_protection=pre_protection,equity_risk=equity_risk)
# No new candidates: four exact historical controls only.
GRID=[config(0.,1.,0.),config(0.,1.),config(20.,.25),config(0.,1.,hard=20.)]
LABELS=["profitability","partial_tp","adx20_sizing","adx20_strict"]
SHARDS=4
def date(s):return pd.Timestamp(s,tz=TZ).tz_convert("UTC")
def source24():
    manifest=json.loads((DATA/"manifest.json").read_text())
    assert manifest["synthetic_rows"]==0
    parts={p["month"]:p for p in manifest["months"] if p["series"]=="trade_1m"}
    frames=[]
    for mon in pd.period_range("2024-02","2024-12",freq="M").astype(str):
        p=parts[mon];f=DATA/"trade_1m"/(mon+".csv.gz")
        assert p["missing"]==0 and p["observed"]==p["expected"] and hashlib.sha256(f.read_bytes()).hexdigest()==p["sha256"]
        d=pd.read_csv(f,usecols=["time","open","high","low","close","volume"])
        assert len(d)==p["expected"]
        frames.append(d)
    df=pd.concat(frames,ignore_index=True)
    assert np.array_equal(df.time.to_numpy(np.int64),np.arange(int(date("2024-02-01").timestamp()),int(date("2025-01-01").timestamp()),60))
    df.index=pd.to_datetime(df.time,unit="s",utc=True)
    return df
def source25_26(period):
    root=Path("data/delta_india/BTCUSD/1m")
    manifest=json.loads((root/"manifest.json").read_text())
    lo,hi=("2025-01","2025-12") if period=="2025" else ("2025-12","2026-10")
    parts=[p for p in manifest["partitions"] if lo+".csv.gz"<=p["file"]<=hi+".csv.gz"]
    assert len(parts)==(12 if period=="2025" else 11)
    frames=[]
    for p in parts:
        f=root/p["file"]
        assert hashlib.sha256(f.read_bytes()).hexdigest()==p["sha256_gzip"] and p["missing_minutes"]==0
        d=pd.read_csv(f);assert len(d)==p["observed_candles"];frames.append(d)
    df=pd.concat(frames,ignore_index=True)
    assert np.all(np.diff(df.time.to_numpy(np.int64))==60)
    df.index=pd.to_datetime(df.time,unit="s",utc=True)
    end=date("2026-01-01" if period=="2025" else "2026-11-01")
    return df.loc[df.index<end].copy()
def prep(period):
    if period=="2024":
        df=source24()
        start=date("2024-02-03")
        months=pd.period_range("2024-02","2024-12",freq="M")
    elif period=="2025":
        df=source25_26(period);start=date("2025-01-01");months=pd.period_range("2025-01","2025-12",freq="M")
    else:
        df=source25_26(period);start=date("2026-01-01");months=pd.period_range("2026-01","2026-10",freq="M")
    assert len(df)%15==0
    ema,st,trend,valid=base.st_and_ema(df,base.TF)
    ind=base.make_indicators(df)
    # Running age only: no future flip information. Initial unconfirmed epoch stays old.
    age=np.full(len(trend),np.inf)
    for j in range(1,len(trend)):
        if valid[j] and valid[j-1] and trend[j]!=trend[j-1]:age[j]=1.
        elif valid[j] and valid[j-1]:age[j]=age[j-1]+1.
    ind["trend_age"]=age
    start_i=int(np.searchsorted(df.time.to_numpy(),int(start.timestamp())))
    # ATR14 of completed 15m candles, Wilder smoothing.
    h,l,c=ind["H"],ind["L"],ind["C"]
    prev=np.r_[c[0],c[:-1]]
    tr=np.maximum(h-l,np.maximum(abs(h-prev),abs(l-prev)))
    atr=np.full(len(tr),np.nan);atr[13]=np.mean(tr[:14])
    for j in range(14,len(tr)):atr[j]=(13*atr[j-1]+tr[j])/14
    ind["ATR"]=atr
    close=pd.Series(ind["C"],dtype=float)
    for n in (16,32):
        distance=close.diff(n).abs()
        travel=close.diff().abs().rolling(n,min_periods=n).sum()
        er=(distance/travel.where(travel>0)).where(travel!=0,0.)
        assert ((er.dropna()>=0)&(er.dropna()<=1+1e-10)).all()
        ind[f"er_{n}"]=er.clip(0,1).to_numpy()
    volume=pd.Series(ind["V"],dtype=float)
    assert np.isfinite(volume).all() and (volume>=0).all() and (volume>0).any(), "invalid or unavailable recorded volume"
    prior_mean=volume.shift(1).rolling(20,min_periods=20).mean()
    ind["relative_volume"]=(volume/prior_mean.where(prior_mean>0)).to_numpy()
    for n in (1,4,8):
        ind[f"swing_low_{n}"]=pd.Series(ind["L"]).rolling(n,min_periods=n).min().to_numpy()
        ind[f"swing_high_{n}"]=pd.Series(ind["H"]).rolling(n,min_periods=n).max().to_numpy()
    # Wilder directional movement: first 14 transitions, then Wilder smoothing.
    def wilder(x,start=1):
        out=np.full(len(x),np.nan)
        j=start+13
        out[j]=np.mean(x[start:j+1])
        for k in range(j+1,len(x)):out[k]=(13*out[k-1]+x[k])/14
        return out
    up=np.r_[0.,np.diff(h)];down=np.r_[0.,-np.diff(l)]
    plus=np.where((up>down)&(up>0),up,0.)
    minus=np.where((down>up)&(down>0),down,0.)
    ps=wilder(plus);ms=wilder(minus)
    den=ps+ms
    dx=np.divide(100*abs(ps-ms),den,out=np.zeros(len(den)),where=den>0)
    dx[:14]=np.nan
    ind["adx14"]=wilder(dx,14)
    for n in (1,3,5):
        a=ind["adx14"]
        slope=np.full(len(a),np.nan)
        slope[n:]=a[n:]-a[:-n]
        ind[f"adx_rise_{n}"]=slope
    # +DI > -DI iff smoothed +DM > smoothed -DM (common positive TR denominator).
    ind["dmi_direction"]=ps-ms
    natr=pd.Series(atr/c)
    # Prior 20 calendar days of 15m bars; 10 days minimum warm-up.
    ref=natr.shift(1).rolling(20*96,min_periods=10*96).median()
    ind["relative_vol"]=(natr/ref.where(ref>0)).to_numpy()
    # Confirmed higher timeframe closes only, aligned by UTC epoch.
    times=df.time.to_numpy(np.int64)
    signal_end=times[14::15]+60
    # UTC-aligned complete bars, never include the currently forming HTF bar.
    for minutes in (30,60,240):
        seconds=minutes*60
        tmp=pd.DataFrame({"t":times,"high":df.high.to_numpy(float),"low":df.low.to_numpy(float)})
        tmp["bucket"]=tmp.t//seconds
        g=tmp.groupby("bucket",sort=True).agg(high=("high","max"),low=("low","min"),count=("t","size"))
        g=g[g["count"]==minutes]
        gh=g.high.to_numpy();gl=g.low.to_numpy()
        u=np.r_[0.,np.diff(gh)];d=np.r_[0.,-np.diff(gl)]
        pp=wilder(np.where((u>d)&(u>0),u,0.))
        mm=wilder(np.where((d>u)&(d>0),d,0.))
        denom=pp+mm
        hdx=np.divide(100*abs(pp-mm),denom,out=np.zeros(len(denom)),where=denom>0)
        hdx[:14]=np.nan
        hadx=wilder(hdx,14)
        ends=(g.index.to_numpy(np.int64)+1)*seconds
        idx=np.searchsorted(ends,signal_end,side="right")-1
        mapped=np.full(len(signal_end),np.nan)
        ok=idx>=0
        assert np.all(ends[idx[ok]]<=signal_end[ok])
        mapped[ok]=hadx[idx[ok]]
        ind[f"adx{minutes}"]=mapped
    for hours in (1,4):
        seconds=hours*3600
        tmp=pd.DataFrame({"t":times,"close":df.close.to_numpy(float)})
        tmp["bucket"]=tmp.t//seconds
        grouped=tmp.groupby("bucket",sort=True).agg(close=("close","last"),count=("t","size"))
        grouped=grouped[grouped["count"]==hours*60]
        vals=grouped.close
        avg=vals.ewm(span=50,adjust=False,min_periods=50).mean()
        ends=(grouped.index.to_numpy(np.int64)+1)*seconds
        idx=np.searchsorted(ends,signal_end,side="right")-1
        mapped=np.full(len(signal_end),np.nan)
        ok=idx>=0
        mapped[ok]=(vals-avg).to_numpy()[idx[ok]]
        ind[f"h{hours}ema50"]=mapped
        if hours==4:
            # Distinct previous completed H4 candle, not repeated 15m samples.
            prev=np.full(len(signal_end),np.nan)
            old=idx>=1
            prev[old]=(vals-avg).to_numpy()[idx[old]-1]
            ind["h4ema50_previous"]=prev
            for n in (2,4,8):
                slope=np.full(len(signal_end),np.nan)
                slope[ok]=(avg-avg.shift(n)).to_numpy()[idx[ok]]
                ind[f"h4ema50_slope_{n}"]=slope
    sig={}
    for wait in (2,4,6,8,12):
        q=base.make_signals(df,ema,trend,valid,"reclaim",wait)[0]
        sig[wait]={i:v for i,v in q.items() if i>=start_i}
    return df,ema,st,trend,ind,sig,months.astype(str).tolist()
def engine():
    src=inspect.getsource(base.simulate)
    assert src.count("qty=cash/entry")==1
    src=src.replace("qty=cash/entry",'qty=cash/entry*float(name.split("__P_")[1])/100*size_factor(ind["adx14"][j],side,ind["dmi_direction"][j],ind["adx_rise"][j],ind["relative_vol"][j],ind["relative_volume"][j],ind["efficiency"][j],ind["trend_age"][j])*swing_risk_cap(R,R_ATR)')
    anchor='                elif risk_mode=="ATR":R=R_ATR*riskmult'
    assert src.count(anchor)==1
    src=src.replace(anchor,"""                elif risk_mode=="ATR":
                    R=R_ATR*riskmult
                    if SWING_BARS>0:
                        boundary=ind[f"swing_low_{SWING_BARS}" if side>0 else f"swing_high_{SWING_BARS}"][j]
                        structural_stop=boundary-side*SWING_BUFFER*R_ATR
                        R=side*(entry-structural_stop)
                        if not side*(raw_open-structural_stop)>0:R=float("nan")""")
    # Partial fills use the same adverse slippage and fee model as the full exit.
    # Keep a single trade ledger row per original entry, aggregating all exit legs.
    def patch(a,b):
        nonlocal src
        assert src.count(a)==1,("partial engine anchor",a)
        src=src.replace(a,b)
    patch('                target=(float("inf") if side>0 else float("-inf")) if tp_off else entry+side*tpR*R',"""                weak_target_used=bool(WEAK_TARGET>0 and ind["adx14"][j]<20.)
                target_r=WEAK_TARGET if weak_target_used else tpR
                target=(float("inf") if side>0 else float("-inf")) if tp_off else entry+side*target_r*R""")
    patch('stop=stop,initial_stop=stop,target=target,entry_sec=sec,epoch=sig["epoch"],','stop=stop,initial_stop=stop,target=target,entry_sec=sec,epoch=sig["epoch"],weak_target_used=weak_target_used,target_r=target_r,planned_risk_pct=planned_risk_pct,entry_exposure_pct=entry_exposure_pct,')
    patch('                    fee_in=FEE*qty*entry',"""                    # Estimate loss at the original stop, inclusive of both fees
                    # and adverse stop slippage. Entry is already slip-adjusted.
                    stop_fill=stop*(1-side*SLIP)
                    loss_per_unit=side*(entry-stop_fill)+FEE*(entry+stop_fill)
                    assert np.isfinite(loss_per_unit) and loss_per_unit>0
                    if EQUITY_RISK>0:
                        qty=min(qty,cash*EQUITY_RISK/loss_per_unit)
                    planned_risk_pct=100*qty*loss_per_unit/cash
                    entry_exposure_pct=100*qty*entry/cash
                    assert 0<entry_exposure_pct<=100+1e-8
                    if EQUITY_RISK>0:assert planned_risk_pct<=100*EQUITY_RISK+1e-8
                    fee_in=FEE*qty*entry""")
    # Read-only diagnostic observations. They cannot influence execution.
    patch('            proxy=raw*(1-position["side"]*SLIP)\n            eq+=position["side"]*position["qty"]*(proxy-position["entry"])-FEE*position["qty"]*proxy\n        eq_high=max(eq_high,eq)',"""            observe(position,raw)
            proxy=raw*(1-position["side"]*SLIP)
            eq+=position["side"]*position["qty"]*(proxy-position["entry"])-FEE*position["qty"]*proxy
        eq_high=max(eq_high,eq)""")
    patch('active=False,activation_count=0,lock_increase_count=0,highest_locked_pct=-1.0)','active=False,activation_count=0,lock_increase_count=0,highest_locked_pct=-1.0,diagnostic_mfe=0.,diagnostic_mae=0.,diagnostic_slip=qty*abs(entry-raw_open),diagnostic_equity=cash+fee_in,diagnostic_adx=float(ind["adx14"][j]),diagnostic_vol=float(ind["relative_vol"][j]),diagnostic_dmi=float(side*ind["dmi_direction"][j]),diagnostic_h4=float(side*ind["h4ema50"][j]/R_ATR))')
    patch('        fill=raw*(1-p["side"]*SLIP)\n        gross=p["side"]*p["qty"]*(fill-p["entry"])',"""        observe(p,raw)
        fill=raw*(1-p["side"]*SLIP)
        p["diagnostic_slip"]+=p["qty"]*abs(fill-raw)
        gross=p["side"]*p["qty"]*(fill-p["entry"])""")
    patch('    def close_trade(raw,sec,reason):',"""    def partial_take(raw):
        nonlocal cash
        p=position
        if PARTIAL_FRACTION<=0 or p.get("partial_done",False) or PARTIAL_TRIGGER>=p["target_r"]:return
        side=p["side"]
        level=p["entry"]+side*PARTIAL_TRIGGER*p["R"]
        if side*(raw-level)<0:return
        assert side*(level-p["target"])<0
        qty=p["qty"]*PARTIAL_FRACTION
        assert 0<qty<p["qty"]
        mark(level)
        fill=level*(1-side*SLIP)
        gross=side*qty*(fill-p["entry"])
        p["diagnostic_slip"]+=qty*abs(fill-level)
        fee=FEE*qty*fill
        p["qty"]-=qty
        p["partial_done"]=True
        p["partial_realized"]=gross-fee
        p["partial_fee"]=fee
        cash+=gross-fee
        mark(level)
    def close_trade(raw,sec,reason):""")
    patch('        net=gross-fee_out-p["fee_in"]','        net=gross-fee_out-p["fee_in"]+p.get("partial_realized",0.)')
    patch('fee_gst_usd=p["fee_in"]+fee_out,','fee_gst_usd=p["fee_in"]+fee_out+p.get("partial_fee",0.),partial_exit=bool(p.get("partial_done",False)),early_risk_reduced=bool(p.get("early_risk_reduced",False)),weak_target_used=p["weak_target_used"],target_r=p["target_r"],planned_risk_pct=p["planned_risk_pct"],entry_exposure_pct=p["entry_exposure_pct"],mfe_r=p["diagnostic_mfe"],mae_r=p["diagnostic_mae"],slippage_usd=p["diagnostic_slip"],entry_equity=p["diagnostic_equity"],adx_at_entry=p["diagnostic_adx"],relative_vol_at_entry=p["diagnostic_vol"],dmi_aligned=p["diagnostic_dmi"]>0,h4_distance_atr=p["diagnostic_h4"],')
    # Existing stop/target gap handling has priority. Deadline exit is a market fill
    # at the current open, before any new signal and before reading the minute high/low.
    patch('        if i in signal_indices and position is not None:\n            skipped_entries_due_to_open_position+=1',"""        # Check only at the first minute of a newly completed UTC H4 bar.
        # At this open, old gap stops/targets have already been processed.
        if position is not None and H4_EXIT>0 and sec%14400==0:
            assert i%TF==0 and tm[i-1]+60==sec
            p=position
            wrong=p["side"]*ind["h4ema50"][done]<0
            prior_wrong=p["side"]*ind["h4ema50_previous"][done]<0
            if wrong and (H4_EXIT==1 or prior_wrong) and (not PRE_PROTECTION or not p["active"]):
                mark(raw_open)
                close_trade(raw_open,sec,"H4_INVALIDATION")
        if position is not None and TIMEOUT_SECONDS>0:
            p=position
            if p["side"]*(raw_open-p["entry"])>=p["R"]:
                p["reached_one_r"]=True
            if sec-p["entry_sec"]>=TIMEOUT_SECONDS and not p.get("reached_one_r",False):
                mark(raw_open)
                close_trade(raw_open,sec,"TIME_INVALIDATION")
        if i in signal_indices and position is not None:
            skipped_entries_due_to_open_position+=1""")
    # Process a reached partial target before the final target, even on a gap.
    patch('                close_trade(position["target"],sec,"TP")','                partial_take(raw_open)\n                close_trade(position["target"],sec,"TP")')
    patch('        path=(raw_open,h[i],l[i],c[i])','        if position is not None:\n            partial_take(raw_open)\n            advance_trail(position,raw_open)\n        path=(raw_open,h[i],l[i],c[i])')
    patch('            if side*(dest-p["target"])>=0:', '            partial_take(dest)\n            if side*(dest-p["target"])>=0:')
    # Evaluate reached protection levels only after observing the path endpoint.
    # Existing stop and target checks remain first; a stop never moves backward.
    anchor='        # An overnight/minute opening price may already cross a rung.'
    assert src.count(anchor)==1
    src=src.replace(anchor, """        if position is not None:
            advance_lock(position,raw_open)
        # An overnight/minute opening price may already cross a rung.""")
    anchor='                mark(dest)\n        if i in monthends:'
    assert src.count(anchor)==1
    src=src.replace(anchor, """                advance_lock(p,dest)
                advance_trail(p,dest)
                mark(dest)
        if i in monthends:""")
    ns=dict(base.__dict__)
    def observe(p,raw):
        move=p["side"]*(raw-p["entry"])/p["R"]
        p["diagnostic_mfe"]=max(p["diagnostic_mfe"],move)
        p["diagnostic_mae"]=max(p["diagnostic_mae"],-move)
    ns["observe"]=observe
    def filter_entry(fil,side,j,ema,ind):
        if fil in ("h1ema50","h4ema50"):return bool(side*ind[fil][j]>0)
        if fil.startswith("h4ema50_vol"):
            if not side*ind["h4ema50"][j]>0:return False
            if ns["ADX_MIN"]>0 and not (ind["adx14"][j]>=ns["ADX_MIN"]):return False
            if ns["RVOL_THRESHOLD"]>0 and ns["RVOL_WEAK"]==0 and not ind["relative_volume"][j]>=ns["RVOL_THRESHOLD"]:return False
            if ns["RISE"]>0 and ns["RISE_SIZE"]==0 and not ind["adx_rise"][j]>0:return False
            if ns["DMI_SIZE"]==0 and not side*ind["dmi_direction"][j]>0:return False
            _,mode,x=fil.split("_");x=float(x)
            v=ind["relative_vol"][j]
            if not np.isfinite(v):return False
            return bool(v>=x if mode=="volmin" else v<=x)
        return base.check_filter(fil,side,j,ema,ind)
    ns["check_filter"]=filter_entry
    def size_factor(adx,side,dmi,rise,vol,rvol,efficiency,age):
        if ns["AGE_LIMIT"]>0:return 1. if age<=ns["AGE_LIMIT"] else .25
        if ns["ER_THRESHOLD"]>0:
            return 1. if efficiency>=ns["ER_THRESHOLD"] else .25
        if ns["RVOL_THRESHOLD"]>0:
            if rvol>=ns["RVOL_THRESHOLD"]:return 1.
            assert ns["RVOL_WEAK"]>0., "strict volume filter must run before sizing"
            return ns["RVOL_WEAK"]
        if ns["VOL_POWER"]>0.:
            assert np.isfinite(vol) and vol>0., "relative-vol entry filter must be evaluated first"
            return max(.25,min(1.,(ns["VOL_ANCHOR"]/vol)**ns["VOL_POWER"]))

        if ns["RISE"]>0:
            if rise>0:return 1.
            assert ns["RISE_SIZE"]>0., "strict momentum must be filtered before sizing"
            return ns["RISE_SIZE"]
        if ns["DMI_SIZE"]<1.:
            assert ns["ADX_THRESHOLD"]==0.
            if side*dmi>0:return 1.
            assert ns["DMI_SIZE"]>0., "strict DMI must be filtered before sizing"
            return ns["DMI_SIZE"]
        if ns["ADX_THRESHOLD"]<=0:return 1.
        if not np.isfinite(adx):return ns["WEAK_SIZE"]
        if ns["SMOOTH"]:
            assert ns["ADX_THRESHOLD"]>10.
            w=max(0.,min(1.,(adx-10.)/(ns["ADX_THRESHOLD"]-10.)))
            return ns["WEAK_SIZE"]+(1.-ns["WEAK_SIZE"])*w
        return 1. if adx>=ns["ADX_THRESHOLD"] else ns["WEAK_SIZE"]
    ns["size_factor"]=size_factor
    def swing_risk_cap(r,atr):
        if ns["SWING_BARS"]==0:return 1.
        assert np.isfinite(r) and r>0 and atr>0
        return min(1.,3.5*atr/r)
    ns["swing_risk_cap"]=swing_risk_cap
    def advance_lock(p,price):
        side=p["side"]
        favorable=side*(price-p["entry"])
        if ns["TIMEOUT_SECONDS"]>0 and favorable>=p["R"]:p["reached_one_r"]=True
        # The early stop is still a loss stop, not a breakeven activation.
        # Keep the original active flag until the original protection fires.
        if ns["EARLY_TRIGGER"]>0 and favorable>=ns["EARLY_TRIGGER"]*p["R"]:
            candidate=p["entry"]+side*ns["EARLY_LOCK"]*p["R"]
            if side*(candidate-p["stop"])>0:
                assert not p["active"]
                p["stop"]=candidate
                p["early_risk_reduced"]=True
        for trigger,lock in ((ns["ACT"],ns["LOCK"]),(ns["ACT2"],ns["LOCK2"])):
            if trigger<=0 or trigger>=p["target_r"] or favorable<trigger*p["R"]:continue
            candidate=p["entry"]+side*lock*p["R"]
            if side*(candidate-p["stop"])<=0:continue
            if p["active"]:p["lock_increase_count"]+=1
            else:p["activation_count"]+=1
            p["stop"]=candidate;p["active"]=True
    def advance_trail(p,price):
        if ns["TRAIL_ATR"]<=0 or not p.get("partial_done",False):return
        side=p["side"]
        # Distance is based on the entry ATR, never on an incomplete candle.
        distance=ns["TRAIL_ATR"]*p["R"]/3.5
        candidate=price-side*distance
        if side*(candidate-p["stop"])>0:
            assert p["active"], "breakeven must already be armed"
            p["stop"]=candidate
            p["lock_increase_count"]+=1
    ns["advance_trail"]=advance_trail
    ns["advance_lock"]=advance_lock
    exec(compile(src,"<simple_core>","exec"),ns);return ns
def replay(ns,data,period,cid,cfg,prof,path,stress=False):
    df,ema,st,trend,ind,sig,months=data
    ns["MONTHS"]=months
    # Select the already-confirmed aligned ADX series for this replay only.
    ind=dict(ind)
    ind["efficiency"]=ind[f"er_{cfg['er_bars']}"] if cfg["er_bars"] else np.zeros(len(ind["C"]))
    if cfg["adx_tf"]!=15:ind["adx14"]=ind[f"adx{cfg['adx_tf']}"]
    ind["adx_rise"]=ind[f"adx_rise_{cfg['rise']}"] if cfg["rise"] else np.zeros(len(ind["adx14"]))
    ns["FEE"]=base.FEE;ns["SLIP"]=base.SLIP*(3 if stress else 1);ns["ACT"]=cfg["activation"];ns["LOCK"]=cfg["lock"];ns["ACT2"]=cfg["stage2"];ns["LOCK2"]=cfg["lock2"];ns["PARTIAL_TRIGGER"]=cfg["partial_trigger"];ns["PARTIAL_FRACTION"]=cfg["partial_fraction"];ns["TRAIL_ATR"]=cfg["trail_atr"];ns["ADX_MIN"]=cfg["adx_min"];ns["ADX_THRESHOLD"]=cfg["adx_threshold"];ns["WEAK_SIZE"]=cfg["weak_size"];ns["SMOOTH"]=cfg["smooth"];ns["DMI_SIZE"]=cfg["dmi_size"];ns["RISE"]=cfg["rise"];ns["RISE_SIZE"]=cfg["rise_size"];ns["VOL_ANCHOR"]=cfg["vol_anchor"];ns["VOL_POWER"]=cfg["vol_power"];ns["TIMEOUT_SECONDS"]=cfg["timeout_hours"]*3600;ns["SWING_BARS"]=cfg["swing_bars"];ns["SWING_BUFFER"]=cfg["swing_buffer"];ns["RVOL_THRESHOLD"]=cfg["rvol_threshold"];ns["RVOL_WEAK"]=cfg["rvol_weak"];ns["ER_THRESHOLD"]=cfg["er_threshold"];ns["EARLY_TRIGGER"]=cfg["early_trigger"];ns["EARLY_LOCK"]=cfg["early_lock"];ns["AGE_LIMIT"]=cfg["age_limit"];ns["WEAK_TARGET"]=cfg["weak_target"];ns["H4_EXIT"]=cfg["h4_exit"];ns["PRE_PROTECTION"]=cfg["pre_protection"];ns["EQUITY_RISK"]=cfg["equity_risk"]
    name=f"C{cid:02d}"+("_FLIPON_" if cfg["flip"] else "_NOFLIP_")+f"__P_{prof}"
    x,m,l=ns["simulate"](df,ema,st,trend,ind,name,(cfg["wait"],cfg["filter"],"ATR",cfg["atr"],cfg["rr"],"none"),sig[cfg["wait"]],path)
    for k in ("profitable_2025_months","profitable_2026_months","return_2025_pct","return_2026_pct"):x.pop(k,None)
    x.update(candidate=cid,period=period,profile=prof,stress=stress,**cfg)
    x["mean_planned_risk_pct"]=float(l.planned_risk_pct.mean())
    x["max_planned_risk_pct"]=float(l.planned_risk_pct.max())
    x["mean_entry_exposure_pct"]=float(l.entry_exposure_pct.mean())
    if cfg["equity_risk"]:assert x["max_planned_risk_pct"]<=100*cfg["equity_risk"]+1e-8
    x["h4_invalidation_exits"]=int((l.exit_reason=="H4_INVALIDATION").sum())
    if not cfg["h4_exit"]:assert x["h4_invalidation_exits"]==0
    z=l[l.exit_reason=="H4_INVALIDATION"]
    assert all(t.hour%4==0 and t.minute==0 and t.second==0 for t in pd.to_datetime(z.exit_time_utc,utc=True))
    if cfg["pre_protection"]:assert (z.activation_count==0).all()
    x["time_invalidation_exits"]=int((l.exit_reason=="TIME_INVALIDATION").sum())
    if cfg["timeout_hours"]==0:assert x["time_invalidation_exits"]==0
    x["early_risk_reduced_trades"]=int(l.early_risk_reduced.sum())
    if cfg["early_trigger"]==0:assert x["early_risk_reduced_trades"]==0
    x["weak_target_trades"]=int(l.weak_target_used.sum())
    x["weak_target_tp_exits"]=int((l.weak_target_used & (l.exit_reason=="TP")).sum())
    assert not l.loc[l.weak_target_used,"partial_exit"].any()
    if cfg["weak_target"]==0:assert x["weak_target_trades"]==0
    else:assert (l.loc[l.weak_target_used,"target_r"]==cfg["weak_target"]).all()
    assert (l.loc[~l.weak_target_used,"target_r"]==3.5).all()
    x["geo_month_pct"]=100*((1+x["net_return_pct"]/100)**(1/len(months))-1)
    x["positive_fraction"]=x["profitable_months"]/len(months)
    x["worst_month"]=float(m.monthly_return_pct.min())
    half=m.month_ist.str[:4]+"H"+np.where(m.month_ist.str[5:].astype(int)<=6,"1","2")
    x["worst_half_pct"]=float(((1+m.monthly_return_pct/100).groupby(half).prod()-1).min()*100)
    m=m.assign(candidate=cid,period=period,profile=prof,stress=stress)
    l=l.assign(candidate=cid,period=period,profile=prof,stress=stress)
    return x,m,l
def train():
    OUT.mkdir(parents=True,exist_ok=True)
    cid=int(os.environ["SHARD_INDEX"]);ns=engine()
    rows=[];monthly=[];ledger=[]
    for period in ("2024","2025"):
        data=prep(period)
        for path in base.PATHS:
            for stress in (False,True):
                x,m,l=replay(ns,data,period,cid,GRID[cid],100,path,stress)
                l["label"]=LABELS[cid]
                l["duration_hours"]=(pd.to_datetime(l.exit_time_utc,utc=True)-pd.to_datetime(l.entry_time_utc,utc=True)).dt.total_seconds()/3600
                l["net_pct_entry_equity"]=100*l.net_usd/l.entry_equity
                l["gross_before_fees_usd"]=l.net_usd+l.fee_gst_usd
                l["gross_before_modeled_costs_usd"]=l.gross_before_fees_usd+l.slippage_usd
                l["gross_pct_entry_equity"]=100*l.gross_before_modeled_costs_usd/l.entry_equity
                l["cost_pct_entry_equity"]=100*(l.fee_gst_usd+l.slippage_usd)/l.entry_equity
                assert (l.duration_hours>=0).all()
                assert np.isfinite(l[["mfe_r","mae_r","entry_equity","slippage_usd"]]).all().all()
                assert (l[["mfe_r","mae_r","slippage_usd"]]>=0).all().all()
                assert (l.entry_equity>0).all()
                assert np.allclose(l.net_pct_entry_equity,l.gross_pct_entry_equity-l.cost_pct_entry_equity)
                rows.append(x);monthly.append(m);ledger.append(l)
    d=OUT/f"shard_{cid}";d.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(rows).to_csv(d/"training.csv",index=False)
    pd.concat(monthly,ignore_index=True).to_csv(d/"monthly.csv",index=False)
    pd.concat(ledger,ignore_index=True).to_csv(d/"ledger.csv",index=False)
def freeze():
    s=pd.concat([pd.read_csv(OUT/f"shard_{i}"/"training.csv") for i in range(SHARDS)],ignore_index=True)
    m=pd.concat([pd.read_csv(OUT/f"shard_{i}"/"monthly.csv") for i in range(SHARDS)],ignore_index=True)
    l=pd.concat([pd.read_csv(OUT/f"shard_{i}"/"ledger.csv") for i in range(SHARDS)],ignore_index=True)
    assert len(s)==32 and not s.duplicated(["candidate","period","path_assumption","stress"]).any()
    assert not l.duplicated(["candidate","period","path_assumption","stress","epoch"]).any()
    expected=[(65.205,55.5852),(66.7746,51.2151),(49.9938,66.3419),(37.9503,71.6078)]
    expected_worst=[52.0497,47.7759,39.7873,28.9068]
    expected_dd=[10.651,10.651,9.763,11.422]
    for cid,returns in enumerate(expected):
        for year,value in zip((2024,2025),returns):
            z=s[(s.candidate==cid)&(s.period==year)&(~s.stress)&(s.path_assumption=="O-H-L-C")]
            assert len(z)==1 and abs(z.net_return_pct.iloc[0]-value)<.015
        zz=s[s.candidate==cid]
        assert abs(zz.net_return_pct.min()-expected_worst[cid])<.015
        assert abs(zz.max_floating_drawdown_pct.max()-expected_dd[cid])<.015
    keys=["candidate","period","path_assumption","stress"]
    recon=l.groupby(keys).agg(net=("net_usd","sum"),trades=("net_usd","size")).reset_index().merge(s[keys+["net_profit_usd","trades"]],on=keys,suffixes=("_ledger","_summary"))
    assert len(recon)==32
    assert np.allclose(recon.net,recon.net_profit_usd,atol=.02)
    assert (recon.trades_ledger==recon.trades_summary).all()
    s.to_csv(OUT/"training.csv",index=False);m.to_csv(OUT/"monthly.csv",index=False);l.to_csv(OUT/"ledger.csv",index=False)
    # Fixed descriptive cohorts, not candidate rules. Outcome-conditioned MFE
    # and duration are post-entry observations, never eligible entry filters.
    l["outcome"]=np.where(l.net_usd>0,"win","nonpositive")
    l["adx_group"]=np.where(l.adx_at_entry>=20,"strong","weak")
    l["dmi_group"]=np.where(l.dmi_aligned,"aligned","unaligned")
    l["vol_group"]=np.where(l.relative_vol_at_entry>=1,"above_prior_median","below_prior_median")
    dims=["outcome","direction","adx_group","dmi_group","vol_group","exit_reason"]
    rows=[]
    for dim in dims:
        for group,z in l.groupby(keys+["label",dim],dropna=False):
            cid,year,path,stress,label,bucket=group
            rows.append(dict(candidate=cid,label=label,period=year,path_assumption=path,stress=stress,dimension=dim,bucket=bucket,n=len(z),wins=int((z.net_usd>0).sum()),net_usd=z.net_usd.sum(),mean_net_pct=z.net_pct_entry_equity.mean(),mean_gross_pct=z.gross_pct_entry_equity.mean(),mean_cost_pct=z.cost_pct_entry_equity.mean(),median_mfe_r=z.mfe_r.median(),median_mae_r=z.mae_r.median(),median_duration_hours=z.duration_hours.median(),mfe_ge_0_5r=int((z.mfe_r>=.5).sum()),mfe_ge_1r=int((z.mfe_r>=1).sum()),mfe_ge_2r=int((z.mfe_r>=2).sum()),gross_positive_net_nonpositive=int(((z.gross_before_modeled_costs_usd>0)&(z.net_usd<=0)).sum())))
    d=pd.DataFrame(rows);d.to_csv(OUT/"cohorts.csv",index=False)
    # Separate cohorts for loss months, using actual monthly marked-to-market
    # equity classification. Trade P&L grouped by exit month is diagnostic only.
    lm=m[keys+["month_ist","monthly_return_pct"]].rename(columns={"month_ist":"exit_month_ist"})
    z=l.merge(lm,on=keys+["exit_month_ist"],how="left",validate="many_to_one")
    assert z.monthly_return_pct.notna().all()
    z["month_outcome"]=np.where(z.monthly_return_pct>0,"profitable","nonpositive")
    z.groupby(keys+["label","month_outcome"]).agg(trades=("net_usd","size"),net_closed_usd=("net_usd","sum"),mean_mfe_r=("mfe_r","mean"),mean_mae_r=("mae_r","mean"),median_duration_hours=("duration_hours","median")).reset_index().to_csv(OUT/"loss_month_cohorts.csv",index=False)
    # Consistency across both years AND all path/cost variants; require at
    # least 10 trades in each cohort before reporting a recurring contrast.
    pairs={"direction":("LONG","SHORT"),"adx_group":("strong","weak"),"dmi_group":("aligned","unaligned"),"vol_group":("above_prior_median","below_prior_median")}
    contrasts=[]
    for cid in range(SHARDS):
        for dim,(a,b) in pairs.items():
            q=d[(d.candidate==cid)&(d.dimension==dim)]
            left=q[q.bucket==a];right=q[q.bucket==b]
            both=left.merge(right,on=keys,suffixes=("_a","_b"))
            if len(both)!=8:continue
            diff=both.mean_net_pct_a-both.mean_net_pct_b
            contrasts.append(dict(candidate=cid,label=LABELS[cid],dimension=dim,a=a,b=b,min_sample=int(min(both.n_a.min(),both.n_b.min())),min_difference_pct=float(diff.min()),max_difference_pct=float(diff.max()),consistent_direction=bool((diff>0).all() or (diff<0).all()),adequate_sample=bool(min(both.n_a.min(),both.n_b.min())>=10)))
    pd.DataFrame(contrasts).to_csv(OUT/"cross_year_contrasts.csv",index=False)
    (OUT/"REPORT.md").write_text("# C05 trade-level diagnostics\n\n32 unchanged benchmark replays; no new strategy or parameters selected. MFE/MAE observed only along modeled path while position open; gap exits use actual modeled raw exit, partial target crossings recorded. Gross-before-cost estimates add modeled slippage and fees, not an alternative frictionless simulation. Monthly cohorts classify marked-to-market month and group trades by exit month, not attribution of open positions. Small cohorts and repeated historical use limit inference. Funding excluded. 2026 not read or replayed.\n")
if __name__=="__main__":
    {"train":train,"freeze":freeze}[sys.argv[1]]()
