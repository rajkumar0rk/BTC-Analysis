#!/usr/bin/env python3
"""BTCUSD 15m ONLY: genuine EMA20 break/reclaim with 1m execution sensitivity.

All signal and risk indicators are 15m. No 1h signals, data or filters.
Predeclared variants inspect entry quality and independently ATR-scale risk/TP.
22 completed IST months Jan 2025-Oct 2026. Fee/slip same as BTC-Analysis baseline.
"""
from pathlib import Path
import bisect
import json
import numpy as np
import pandas as pd
from research_ema20_second_touch import read_source, MONTHS, FEE, SLIP
from research_st_firsttouch_ema20_tp2r_stflip_1h15m import st_and_ema, ts_iso
from research_btc_15m_touch_reclaim_20261123 import make_signals

OUT = Path("analysis/btc15m_small_net_tp_after_costs_20261123")
TF=15
INITIAL=1000.0
PATHS=("O-H-L-C","O-L-H-C")
# tuple = (reclaim wait in 15m bars, entry filter, R definition, scale, TP/R, profit-lock)
# Valid entries always: confirmed ST flip, first post-flip EMA20 interaction closes WRONG side,
# later 15m closes on trend side. The flip candle never enters.
CONFIGS={
 "touch_ST1R_3R":(4,"any","ST",1.,3.,"none"),
 "touch_stop0p30_tp0p20":(4,"any","PCT",0.00300,0.66666667,"none"),
 "touch_stop0p30_tp0p30":(4,"any","PCT",0.00300,1.00000000,"none"),
 "touch_stop0p30_tp0p40":(4,"any","PCT",0.00300,1.33333333,"none"),
 "touch_stop0p30_tp0p60":(4,"any","PCT",0.00300,2.00000000,"none"),
 "touch_stop0p30_tp0p80":(4,"any","PCT",0.00300,2.66666667,"none"),
 "touch_stop0p50_tp0p20":(4,"any","PCT",0.00500,0.40000000,"none"),
 "touch_stop0p50_tp0p30":(4,"any","PCT",0.00500,0.60000000,"none"),
 "touch_stop0p50_tp0p40":(4,"any","PCT",0.00500,0.80000000,"none"),
 "touch_stop0p50_tp0p60":(4,"any","PCT",0.00500,1.20000000,"none"),
 "touch_stop0p50_tp0p80":(4,"any","PCT",0.00500,1.60000000,"none"),
 "touch_stop0p75_tp0p20":(4,"any","PCT",0.00750,0.26666667,"none"),
 "touch_stop0p75_tp0p30":(4,"any","PCT",0.00750,0.40000000,"none"),
 "touch_stop0p75_tp0p40":(4,"any","PCT",0.00750,0.53333333,"none"),
 "touch_stop0p75_tp0p60":(4,"any","PCT",0.00750,0.80000000,"none"),
 "touch_stop0p75_tp0p80":(4,"any","PCT",0.00750,1.06666667,"none"),
 "reclaim_ST1R_3R":(4,"any","ST",1.,3.,"none"),
 "reclaim_stop0p30_tp0p20":(4,"any","PCT",0.00300,0.66666667,"none"),
 "reclaim_stop0p30_tp0p30":(4,"any","PCT",0.00300,1.00000000,"none"),
 "reclaim_stop0p30_tp0p40":(4,"any","PCT",0.00300,1.33333333,"none"),
 "reclaim_stop0p30_tp0p60":(4,"any","PCT",0.00300,2.00000000,"none"),
 "reclaim_stop0p30_tp0p80":(4,"any","PCT",0.00300,2.66666667,"none"),
 "reclaim_stop0p50_tp0p20":(4,"any","PCT",0.00500,0.40000000,"none"),
 "reclaim_stop0p50_tp0p30":(4,"any","PCT",0.00500,0.60000000,"none"),
 "reclaim_stop0p50_tp0p40":(4,"any","PCT",0.00500,0.80000000,"none"),
 "reclaim_stop0p50_tp0p60":(4,"any","PCT",0.00500,1.20000000,"none"),
 "reclaim_stop0p50_tp0p80":(4,"any","PCT",0.00500,1.60000000,"none"),
 "reclaim_stop0p75_tp0p20":(4,"any","PCT",0.00750,0.26666667,"none"),
 "reclaim_stop0p75_tp0p30":(4,"any","PCT",0.00750,0.40000000,"none"),
 "reclaim_stop0p75_tp0p40":(4,"any","PCT",0.00750,0.53333333,"none"),
 "reclaim_stop0p75_tp0p60":(4,"any","PCT",0.00750,0.80000000,"none"),
 "reclaim_stop0p75_tp0p80":(4,"any","PCT",0.00750,1.06666667,"none"),
 "combined_ST1R_3R":(4,"any","ST",1.,3.,"none"),
 "combined_stop0p30_tp0p20":(4,"any","PCT",0.00300,0.66666667,"none"),
 "combined_stop0p30_tp0p30":(4,"any","PCT",0.00300,1.00000000,"none"),
 "combined_stop0p30_tp0p40":(4,"any","PCT",0.00300,1.33333333,"none"),
 "combined_stop0p30_tp0p60":(4,"any","PCT",0.00300,2.00000000,"none"),
 "combined_stop0p30_tp0p80":(4,"any","PCT",0.00300,2.66666667,"none"),
 "combined_stop0p50_tp0p20":(4,"any","PCT",0.00500,0.40000000,"none"),
 "combined_stop0p50_tp0p30":(4,"any","PCT",0.00500,0.60000000,"none"),
 "combined_stop0p50_tp0p40":(4,"any","PCT",0.00500,0.80000000,"none"),
 "combined_stop0p50_tp0p60":(4,"any","PCT",0.00500,1.20000000,"none"),
 "combined_stop0p50_tp0p80":(4,"any","PCT",0.00500,1.60000000,"none"),
 "combined_stop0p75_tp0p20":(4,"any","PCT",0.00750,0.26666667,"none"),
 "combined_stop0p75_tp0p30":(4,"any","PCT",0.00750,0.40000000,"none"),
 "combined_stop0p75_tp0p40":(4,"any","PCT",0.00750,0.53333333,"none"),
 "combined_stop0p75_tp0p60":(4,"any","PCT",0.00750,0.80000000,"none"),
 "combined_stop0p75_tp0p80":(4,"any","PCT",0.00750,1.06666667,"none"),
}

def make_indicators(df):
    n=len(df)//TF
    assert n*TF==len(df), "Incomplete 15m data"
    H=df.high.to_numpy(float).reshape(n,TF).max(axis=1)
    L=df.low.to_numpy(float).reshape(n,TF).min(axis=1)
    O=df.open.to_numpy(float).reshape(n,TF)[:,0]
    C=df.close.to_numpy(float).reshape(n,TF)[:,-1]
    V=df.volume.to_numpy(float).reshape(n,TF).sum(axis=1)
    prev=np.r_[C[0],C[:-1]]
    TR=np.maximum(H-L,np.maximum(abs(H-prev),abs(L-prev)))
    ATR=np.full(n,np.nan)
    ATR[9]=np.mean(TR[:10])
    for j in range(10,n):
        ATR[j]=(ATR[j-1]*9+TR[j])/10
    return dict(O=O,H=H,L=L,C=C,V=V,ATR=ATR)

def check_filter(filter_name,side,j,ema,ind):
    c=float(ind["C"][j]);o=float(ind["O"][j])
    h=float(ind["H"][j]);l=float(ind["L"][j])
    a=float(ind["ATR"][j])
    if filter_name=="any":return True
    if filter_name=="slope4":return j>=4 and side*(ema[j]-ema[j-4])>0
    if filter_name=="slope8":return j>=8 and side*(ema[j]-ema[j-8])>0
    if filter_name=="body35":return side*(c-o)>=.35*(h-l)
    if filter_name=="body55":return side*(c-o)>=.55*(h-l)
    if filter_name=="margin10":return side*(c-ema[j])>=.10*a
    if filter_name=="margin20":return side*(c-ema[j])>=.20*a
    if filter_name=="volume120":return j>=20 and ind["V"][j] >= 1.2*float(np.mean(ind["V"][j-20:j]))
    if filter_name=="volume150":return j>=20 and ind["V"][j] >= 1.5*float(np.mean(ind["V"][j-20:j]))
    raise ValueError("Unknown filter "+filter_name)

def simulate(df,ema,stline,trend,ind,name,cfg,signals,path_name):
    wait,fil,risk_mode,riskmult,tpR,lock=cfg
    tm=df.time.to_numpy(np.int64)
    op=df.open.to_numpy(float);h=df.high.to_numpy(float)
    l=df.low.to_numpy(float);c=df.close.to_numpy(float)
    monthends={}
    for month in MONTHS:
        end=(pd.Period(month,freq="M")+1).start_time.tz_localize("Asia/Kolkata").tz_convert("UTC")-pd.Timedelta(minutes=1)
        sec=int(end.timestamp())
        i=int(np.searchsorted(tm,sec,side="right")-1)
        assert i>=0 and tm[i]==sec,(month,sec)
        monthends[i]=month
    signal_indices=set(signals)
    event_indices=sorted(signal_indices|set(monthends))
    cash=INITIAL;position=None;trade_rows=[];month_rows=[]
    eq_high=INITIAL;max_dd=0.;eq_low=INITIAL;filtered=0;badR=0
    signal_used=0
    seen_epochs=set()
    def mark(raw):
        nonlocal eq_high,eq_low,max_dd
        eq=cash
        if position is not None:
            proxy=raw*(1-position["side"]*SLIP)
            eq+=position["side"]*position["qty"]*(proxy-position["entry"])-FEE*position["qty"]*proxy
        eq_high=max(eq_high,eq)
        eq_low=min(eq_low,eq)
        if eq_high>0:
            max_dd=max(max_dd,100*(eq_high-eq)/eq_high)
        return eq
    def close_trade(raw,sec,reason):
        nonlocal position,cash
        p=position
        assert p is not None
        fill=raw*(1-p["side"]*SLIP)
        gross=p["side"]*p["qty"]*(fill-p["entry"])
        fee_out=FEE*p["qty"]*fill
        net=gross-fee_out-p["fee_in"]
        cash+=gross-fee_out
        trade_rows.append(dict(config=name,path_assumption=path_name,
           entry_time_utc=ts_iso(p["entry_sec"]),exit_time_utc=ts_iso(sec),
           exit_month_ist=pd.Timestamp(sec,unit="s",tz="UTC").tz_convert("Asia/Kolkata").strftime("%Y-%m"),
           direction="LONG" if p["side"]==1 else "SHORT",entry=p["entry"],exit=fill,
           R=p["R"],initial_stop=p["initial_stop"],target=p["target"],
           exit_reason=reason,net_usd=net,fee_gst_usd=p["fee_in"]+fee_out,
           equity_after_usd=cash,epoch=p["epoch"]))
        position=None
    i=0
    while i<len(df):
        if position is None and i not in signal_indices and i not in monthends:
            next_event=bisect.bisect_left(event_indices,i)
            if next_event==len(event_indices):
                break
            i=event_indices[next_event]
        done=i//TF-1
        if done<100:
            i+=1
            continue
        sec=int(tm[i]);raw_open=float(op[i])
        if position is not None:
            # Only confirmed 15m ST reversal (never a line touch).
            if i%TF==0 and trend[done]!=position["side"]:
                close_trade(raw_open,sec,"SUPERTREND_FLIP")
            elif position["side"]*(raw_open-position["target"])>=0:
                close_trade(position["target"],sec,"TP")
            elif position["side"]*(raw_open-position["stop"])<=0:
                close_trade(raw_open,sec,"STOP_GAP")
        if i in signal_indices and position is None and cash>0:
            sig=signals[i]
            side=int(sig["side"]); j=int(sig["signal_close_bar"])
            if not check_filter(fil,side,j,ema,ind):
                filtered+=1
            else:
                assert side==int(trend[done]), ("Unexpected trend after reclaim",name,i)
                entry=raw_open*(1+side*SLIP)
                R_ST=side*(entry-float(stline[done]))
                R_ATR=float(ind["ATR"][j])
                if risk_mode=="ST":R=R_ST*riskmult
                elif risk_mode=="ATR":R=R_ATR*riskmult
                elif risk_mode=="CAP":R=min(R_ST,R_ATR*riskmult)
                elif risk_mode=="PCT":R=entry*riskmult
                else:raise ValueError(risk_mode)
                target=entry+side*tpR*R
                stop=entry-side*R
                if not (np.isfinite(R) and R>0 and stop>0 and np.isfinite(target) and target>0 and R_ST>0):
                    badR+=1
                else:
                    assert sig["epoch"] not in seen_epochs, "Cycle duplicate"
                    seen_epochs.add(sig["epoch"])
                    qty=cash/entry
                    fee_in=FEE*qty*entry
                    cash-=fee_in
                    position=dict(side=side,entry=entry,R=R,qty=qty,fee_in=fee_in,
                                  stop=stop,initial_stop=stop,target=target,entry_sec=sec,epoch=sig["epoch"])
                    signal_used+=1
        path=(raw_open,h[i],l[i],c[i]) if path_name=="O-H-L-C" else (raw_open,l[i],h[i],c[i])
        mark(path[0])
        for k in range(3):
            dest=float(path[k+1])
            if position is None:
                mark(dest)
                continue
            p=position;side=p["side"]
            if side*(dest-p["target"])>=0:
                mark(p["target"])
                close_trade(p["target"],sec,"TP")
            elif side*(dest-p["stop"])<=0:
                mark(p["stop"])
                close_trade(p["stop"],sec,"STOP")
            else:
                if side*(dest-float(path[k]))>0:
                    if lock in ("BE1","STEP2") and side*(dest-p["entry"])>=p["R"] and side*(p["entry"]-p["stop"])>0:
                        p["stop"]=p["entry"]
                    if lock=="STEP2" and side*(dest-p["entry"])>=2*p["R"]:
                        candidate=p["entry"]+side*.5*p["R"]
                        if side*(candidate-p["stop"])>0:p["stop"]=candidate
                mark(dest)
        if i in monthends:
            month_rows.append(dict(month_ist=monthends[i],equity_usd=mark(float(c[i])),
                        position_open=position is not None))
        i+=1
    if position is not None:
        close_trade(float(c[-1]),int(tm[-1]),"SAMPLE_END_ACCOUNTING_ONLY")
        month_rows[-1]["equity_usd"]=cash
    assert len(month_rows)==22,("wrong month count",len(month_rows),name)
    ledger=pd.DataFrame(trade_rows)
    assert not ledger.empty,(name,path_name)
    assert not ledger.epoch.duplicated().any()
    assert abs(ledger.net_usd.sum()-(cash-INITIAL))<0.02,"Ledger/cash mismatch"
    month_df=pd.DataFrame(month_rows)
    month_df["monthly_return_pct"]=100*(month_df.equity_usd/month_df.equity_usd.shift(1,fill_value=INITIAL)-1)
    y25=float(month_df.loc[month_df.month_ist=="2025-12","equity_usd"].iloc[0])
    positive=ledger.net_usd>0
    gain=float(ledger.loc[positive,"net_usd"].sum())
    loss=-float(ledger.loc[~positive,"net_usd"].sum())
    summary=dict(symbol="BTCUSD",timeframe="15m",config=name,path_assumption=path_name,
        trades=len(ledger),wins=int(positive.sum()),losses=int((~positive).sum()),
        win_rate_pct=round(100*float(positive.mean()),3),
        profit_factor=round(gain/loss,4) if loss>0 else None,
        net_return_pct=round(100*(cash/INITIAL-1),4),
        net_profit_usd=round(cash-INITIAL,4),
        profitable_months=int((month_df.monthly_return_pct>0).sum()),
        profitable_2025_months=int((month_df.iloc[:12].monthly_return_pct>0).sum()),
        profitable_2026_months=int((month_df.iloc[12:].monthly_return_pct>0).sum()),
        return_2025_pct=round(100*(y25/INITIAL-1),3),
        return_2026_pct=round(100*(cash/y25-1),3),
        max_floating_drawdown_pct=round(max_dd,3),
        fees_gst_usd=round(float(ledger.fee_gst_usd.sum()),4),
        tp_exits=int((ledger.exit_reason=="TP").sum()),
        stop_exits=int(ledger.exit_reason.isin(["STOP","STOP_GAP"]).sum()),
        flip_exits=int((ledger.exit_reason=="SUPERTREND_FLIP").sum()),
        signal_candidates=len(signals),signals_filtered=filtered,invalid_risk=badR)
    month_df.insert(0,"config",name)
    month_df.insert(0,"symbol","BTCUSD")
    month_df.insert(0,"path_assumption",path_name)
    return summary,month_df,ledger

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    df,quality=read_source("BTCUSD")
    ema,stline,trend,valid=st_and_ema(df,TF)
    ind=make_indicators(df)
    signal_cache={}
    results=[];monthly=[];trades=[]
    for name,cfg in CONFIGS.items():
        mode=name.split("_")[0]
        wait=cfg[0]
        key=(mode,wait)
        if key not in signal_cache:
            signal_cache[key]=make_signals(df,ema,trend,valid,mode,wait)[0]
        for path in PATHS:
            print("RUN",name,path,flush=True)
            row,mon,ledger=simulate(df,ema,stline,trend,ind,name,cfg,signal_cache[key],path)
            results.append(row);monthly.append(mon);trades.append(ledger)
            print("RESULT",json.dumps(row,sort_keys=True),flush=True)
    result_df=pd.DataFrame(results)
    # Must reproduce the complete established original 15m-only configuration.
    reference=[("touch_ST1R_3R",809,-69.4444),("reclaim_ST1R_3R",434,-44.5322),("combined_ST1R_3R",1243,-83.0515)]
    for name,trades_expected,net_expected in reference:
        for path in PATHS:
            row=result_df[(result_df.config==name)&(result_df.path_assumption==path)].iloc[0]
            assert int(row.trades)==trades_expected and abs(row.net_return_pct-net_expected)<0.001,("BASELINE_PARITY_FAILED",name,path,row.to_dict())
    print("BASELINE_PARITY_OK",flush=True)
    result_df.to_csv(OUT/"summary.csv",index=False)
    pd.concat(monthly,ignore_index=True).to_csv(OUT/"monthly_mark_to_market.csv",index=False)
    pd.concat(trades,ignore_index=True).to_csv(OUT/"trades.csv.gz",index=False,compression="gzip")
    (OUT/"quality.json").write_text(json.dumps(dict(BTCUSD=quality,configurations=CONFIGS,
        signal_timeframe="15m",higher_timeframe_features=False,execution_timeframe="1m",
        pct_targets_after_costs="gross target 0.20%–0.80% of entry, fees+GST+slippage deducted from every trade",
        supertrend_ATR10_multiplier3=True,ema20=True,stop_on_opposite_confirmed_ST_flip=True,
        one_trade_per_cycle=True,first_touch_must_close_wrong_side=True,
        then_later_15m_close_reclaims=True,flip_candle_excluded=True,
        entry_modes="touch/reclaim/combined, each requires first eligible 15m EMA20 interaction after ST flip",
        fee_incl_GST_per_side=FEE,slippage_per_side=SLIP,notional="1x evolving $1000 equity",
        no_volume_filter_baseline=True,
        limitations="2026 is already inspected, no genuine fresh out-of-sample; no tick execution, spread, liquidity, funding, leverage, or liquidation"),indent=2,default=str)+"\n")
    display=result_df[result_df.path_assumption=="O-H-L-C"]
    display=display.sort_values(["net_return_pct"],ascending=False)[["config","trades","win_rate_pct","profit_factor",
        "net_return_pct","profitable_months","profitable_2025_months","profitable_2026_months",
        "return_2025_pct","return_2026_pct","max_floating_drawdown_pct"]]
    body=["# BTCUSD 15M only — Reclaim entry quality and ATR risk scale","","No 1H data or indicators. BTCUSD 15m ST(10,3), EMA20. 1m exit replay only.",
        "Jan 2025-Oct 2026 inclusive (22 completed IST months); $1000 initial, 1x notional; taker fee .05% each side plus 18% GST, adverse slippage .02% each side.",
        "Touch/reclaim/combined entry modes, one trade per ST cycle; stop fixed at 0.30–0.75% price or original ST distance; gross fixed take profits 0.20–0.80% price. Opposite ST flip can exit early. All P&L after taker/GST/slippage.",
        "No volume or 1h filters in this test; both long and short, all entry candidates retained, including 1m path sensitivity.",
        "R for PCT = entry filled price times stop percentage; TP = entry filled price times chosen gross TP percentage; fees and GST plus adverse 0.02% slippage on each fill.",
        "1m intrabar OHLC paths O-H-L-C and O-L-H-C are hypothetical, not historical ticks.",
        "ALL 2025/2026 data has already been inspected: best in-sample does not establish a repeatable forward edge.",
        "","## BTC 15M small fixed gross TP after full costs (O-H-L-C)","",display.to_markdown(index=False),"",
        "Full monthly returns, trades ledger, alternate minute path and settings are in sidecar files."]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(body)+"\n")
    print("BACKTEST_DONE",len(result_df),flush=True)

if __name__=="__main__":
    main()
