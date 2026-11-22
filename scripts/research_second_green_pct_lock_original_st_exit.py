#!/usr/bin/env python3
"""Keep ST(10,3) 15m closing exit, vary ONLY percentage profit protection.

No fixed TP or SL. Third candle open after 2nd green 15m bar after bullish
flip or bullish ST line touch; evaluate 1m. Fees/slippage as prior research.
A 1m bar that first activates a lock cannot also retrospectively hit it.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import json
import research_supertrend_15m_line_touch as base
import research_supertrend_15m_filter_grid as f
import research_supertrend_15m_profit_protection as p
import research_supertrend_15m_second_green as g
OUT=Path("analysis/second_green_pct_profit_only_st_exit_20261122")
ARMS=(.12,.2,.3,.5,.75,1.,1.5,2.,3.,5.)
FRACTIONS=(0.,.5,.75,1.)
LADDERS={
    "ladder_012_02_03_05_1_2_5":((.12,.2,.3,.5,1.,2.,5.),(0.,.12,.2,.3,.5,1.,2.)),
    "ladder_02_03_05_1_2_5":((.2,.3,.5,1.,2.,5.),(0.,.2,.3,.5,1.,2.)),
    "ladder_05_1_2_5":((.5,1.,2.,5.),(0.,.5,1.,2.)),
    "ladder_1_2_5":((1.,2.,5.),(0.,1.,2.)),
}
MODES=[("off","off",None,None)]
MODES += [(f"arm_{a:g}_lock_{int(q*100)}","single",a,q)
          for a in ARMS for q in FRACTIONS]
MODES += [(k,"ladder",a,b) for k,(a,b) in LADDERS.items()]
assert len(MODES)==45 and len(set(x[0] for x in MODES))==45
MONTHS=base.MONTHS

def one_exit(j,fill,end,h,l,o,c,mode):
    name,kind,trigger,lock=mode
    length=end-j
    assert length>0
    hh=h[j:end]; ll=l[j:end]
    stop=None
    if kind=="single":
        peak=np.maximum.accumulate(hh)
        cross=np.searchsorted(peak,fill*(1+trigger/100),side="left")
        if cross<length-1:
            start=j+int(cross)+1
            stopprice=fill*(1+trigger*lock/100)
            crossings=np.flatnonzero(l[start:end]<=stopprice)
            if len(crossings):
                k=start+int(crossings[0])
                stop=(k,float(min(o[k],stopprice)))
    elif kind=="ladder":
        highpeak=np.maximum.accumulate(hh)
        peak_pct=100*(highpeak/fill-1)
        stops=np.full(length,-np.inf)
        for a,b in zip(trigger,lock):
            stops[peak_pct>=a]=fill*(1+b/100)
        # An observed 1m HIGH establishes new protective level for NEXT 1m.
        crossings=np.flatnonzero(ll[1:]<=stops[:-1])
        if len(crossings):
            ix=int(crossings[0]);k=j+ix+1
            stop=(k,float(min(o[k],stops[ix])))
    else: assert kind=="off"
    n=len(h)
    if stop:
        k,mid=stop;reason="profit_lock"
    elif end<n:
        k=end;mid=float(o[end]);reason="supertrend_close"
    else:
        k=n-1;mid=float(c[-1]);reason="archive_end"
    mae=100*(float(np.min(l[j:k+1]))/fill-1)
    return k,mid,reason,mae

def tests():
    o=np.array([100000.,100100.,100200.,100200.,100200.,100200.])
    h=np.array([100200.,100250.,100240.,100240.,100240.,100240.])
    l=np.array([99700.,99990.,100130.,100130.,100130.,100130.])
    mode=("arm_0.12_lock_100","single",.12,1.)
    k,mid,reason,mae=one_exit(0,100005.,5,h,l,o,o,mode)
    assert k==1 and reason=="profit_lock"
    untouched=("arm_5_lock_100","single",5.,1.)
    k,mid,reason,mae=one_exit(0,100005.,5,h,l,o,o,untouched)
    assert k==5 and reason=="supertrend_close"
    h[5]=200000.
    k,mid,reason,mae=one_exit(0,100005.,5,h,l,o,o,untouched)
    assert k==5 and reason=="supertrend_close"
    o[1]=99000.
    k,mid,reason,mae=one_exit(0,100005.,5,h,l,o,o,mode)
    assert mid==99000.
    print("MICROTESTS_PASS",flush=True)

def run(cohort,stops,minute,mode,montharr,name,vol,atr):
    h=minute.high.to_numpy(float);l=minute.low.to_numpy(float)
    o=minute.open.to_numpy(float);c=minute.close.to_numpy(float)
    n=len(h);rows=[]
    for cycle,bar,j,mid,line in cohort:
        mo=montharr[j]
        if mo not in MONTHS:continue
        sidx=np.searchsorted(stops,bar,side="left")
        lastbar=int(stops[sidx]) if sidx<len(stops) else -1
        end=min((lastbar+1)*15,n) if lastbar>=0 else n
        assert end>j,(bar,j,lastbar)
        entryfill=mid+base.SLIP
        k,x,reason,mae=one_exit(j,entryfill,end,h,l,o,c,mode)
        xf=x-base.SLIP;fees=base.FEE*(entryfill+xf)
        net=float(xf-entryfill-fees)
        rows.append(dict(entry_type=name,vol_filter=vol,atr_filter=atr,
            mode=mode[0],entry_month_ist=mo,
            exit_month_ist=minute.index[k].tz_convert("Asia/Kolkata").strftime("%Y-%m"),
            entry_idx=j,exit_idx=k,net_pts=net,win=int(net>0),
            exit_reason=reason,mae_pct=mae,holding_minutes=k-j))
    return rows

def summary(rows,name,v,a,mode):
    df=pd.DataFrame(rows)
    n=len(df)
    if n==0:
        return dict(entry_type=name,vol_filter=v,atr_filter=a,mode=mode[0],
            trades=0,wins=0,losses=0,win_rate_pct=None,net_pts=0,
            profit_lock_exits=0,st_close_exits=0,archive_open=0,
            profitable_entry_months=0,losing_entry_months=0,
            profitable_exit_months=0,losing_exit_months=0,
            max_closed_dd_pts=0,worst_floating_pct=None,longest_days=None)
    wc=int(df.win.sum());byentry=df.groupby("entry_month_ist").net_pts.sum()
    byexit=df.groupby("exit_month_ist").net_pts.sum()
    mentry=np.array([byentry.get(m,0.) for m in MONTHS])
    mexit=np.array([byexit.get(m,0.) for m in MONTHS])
    cum=df.sort_values("exit_idx").net_pts.cumsum().to_numpy()
    dd=float(np.max(np.maximum.accumulate(np.r_[0,cum])-np.r_[0,cum]))
    return dict(entry_type=name,vol_filter=v,atr_filter=a,mode=mode[0],
      trades=n,wins=wc,losses=n-wc,win_rate_pct=round(100*wc/n,2),
      net_pts=round(float(df.net_pts.sum()),2),
      profit_lock_exits=int((df.exit_reason=="profit_lock").sum()),
      st_close_exits=int((df.exit_reason=="supertrend_close").sum()),
      archive_open=int((df.exit_reason=="archive_end").sum()),
      profitable_entry_months=int((mentry>0).sum()),
      losing_entry_months=int((mentry<0).sum()),
      profitable_exit_months=int((mexit>0).sum()),
      losing_exit_months=int((mexit<0).sum()),
      max_closed_dd_pts=round(dd,2),
      worst_floating_pct=round(float(df.mae_pct.min()),2),
      longest_days=round(float(df.holding_minutes.max()/1440),2))

def main():
    tests();OUT.mkdir(parents=True,exist_ok=True)
    m,b,files=base.load()
    st,trend=base.supertrend(b)
    vol,ap,ar=f.build_features(b)
    events,stops=f.candidate_touch_events(m,b,st,trend,vol,ap,ar)
    op=m.open.to_numpy(float)
    montharr=m.index.tz_convert("Asia/Kolkata").strftime("%Y-%m").to_numpy()
    report=[]
    tradeledger=[]
    wanted={("vol_ge_1p0","atrpct_ge_0p20"),
            ("vol_off","atr_off"),
            ("vol_off","atrpct_ge_0p20"),
            ("vol_ge_1p5","atrpct_ge_0p30")}
    selected_modes={"off","arm_0.12_lock_100","arm_0.2_lock_100",
        "arm_0.3_lock_100","arm_0.5_lock_100","arm_1_lock_100",
        "arm_2_lock_100","arm_5_lock_100","arm_0.3_lock_50",
        "arm_0.5_lock_50","arm_1_lock_50",
        "ladder_012_02_03_05_1_2_5","ladder_1_2_5"}
    for vn,vs in f.VOLUME.items():
        for an,ats in f.VOLATILITY.items():
            touch=p.select_events(events,vs,ats)
            cohorts={
              "after_line_touch":g.after_touch_green(touch,b,trend,stops,op),
              "after_bullish_flip":g.after_flip_green(
                   b,trend,vol,ap,ar,vs,ats,stops,op)}
            for name,cohort in cohorts.items():
                cohort=[x for x in cohort if montharr[x[2]] in MONTHS]
                if (vn,an)==("vol_ge_1p0","atrpct_ge_0p20"):
                    assert len(cohort)==(108 if name=="after_line_touch" else 197)
                for mode in MODES:
                    rows=run(cohort,stops,m,mode,montharr,name,vn,an)
                    report.append(summary(rows,name,vn,an,mode))
                    if (vn,an) in wanted and mode[0] in selected_modes:
                        tradeledger+=rows
            print("FILTER",vn,an,"done",len(report),flush=True)
    s=pd.DataFrame(report)
    assert len(s)==45*42*2==3780
    assert (s.trades==s.wins+s.losses).all()
    assert (s.trades==s.profit_lock_exits+s.st_close_exits+s.archive_open).all()
    s.to_csv(OUT/"all_3780_combinations.csv",index=False)
    same=s[(s.vol_filter=="vol_ge_1p0")&
           (s.atr_filter=="atrpct_ge_0p20")]
    same.to_csv(OUT/"same_filters_2_entries.csv",index=False)
    t=pd.DataFrame(tradeledger)
    t.to_csv(OUT/"selected_trade_ledger.csv.gz",index=False,compression="gzip")
    m=t.groupby(["entry_type","vol_filter","atr_filter","mode",
       "exit_month_ist"]).agg(trades=("net_pts","count"),
       wins=("win","sum"),net_pts=("net_pts","sum")).reset_index()
    m.to_csv(OUT/"monthly_by_actual_exit_month.csv",index=False)
    pos=s[(s.trades>=60)&(s.archive_open==0)].sort_values(
            "net_pts",ascending=False)
    pos.to_csv(OUT/"min60_trades.csv",index=False)
    quality=dict(
      configurations=3780,entries=2,filters=42,modes=45,
      supertrend_period=10,supertrend_factor=3,
      original_st_closing_exit_kept=True,fixed_TP=False,fixed_SL=False,
      changed_only="profit lock activation and lock percentage",
      no_same_bar_lookahead=True,
      matched_previous_cohorts="108 touch, 197 bullish flip",
      costs="taker 0.05% each side + GST 18% + 5 pts slippage each side",
      liquidation_modeled=False,
      timeline="22 IST entry months Jan2025-Oct2026")
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2)+"\n")
    cols=["entry_type","mode","trades","wins","losses",
        "win_rate_pct","net_pts","profit_lock_exits","st_close_exits",
        "profitable_entry_months","losing_entry_months",
        "max_closed_dd_pts","worst_floating_pct"]
    write=[
      "# Corrected 15m BTCUSD: ORIGINAL Supertrend exit + percentage profit lock",
      "Only the profit-lock parameters vary. No fixed take profit or hard SL.",
      "15m Supertrend (ATR10 x 3) closing-stop remains ON and unchanged.",
      "1m protection activates only after the threshold candle completes;",
      "fees 0.05% each way plus GST18 and 5 adverse price pts slippage each way.",
      "Net units = BTC price points per 1 BTC equivalent, not account returns.",
      "",
      "## Previously matched filters: vol>=1, ATR>=0.20",
      same[same["mode"].isin(selected_modes)][cols].to_markdown(index=False),
      "",
      "## Top 20 configs >=60 trades",
      pos[["vol_filter","atr_filter"]+cols].head(20).to_markdown(index=False),
      "",
      "## Note",
      "Unlike previous version, ST closing exit DOES realize losing trades.",
      "Multiple researched combinations are in-sample; no independent OOS.",
      "Liquidation/funding/order-book spread not modeled. Entry-month positive",
      "month stats differ from actual exit-month realization, both in CSV."]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(write)+"\n")
    print("VERIFIED_CORRECTED_BACKTEST",len(s),flush=True)
    print("MATCHED_FILTERS\n"+same[same["mode"].isin(selected_modes)][cols].to_string(index=False),flush=True)
    print("BEST_OVER60\n"+pos[["vol_filter","atr_filter"]+cols].head(10).to_string(index=False),flush=True)

if __name__=="__main__":main()
