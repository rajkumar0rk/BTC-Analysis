#!/usr/bin/env python3
"""BTCUSD-only ST(10,3) 15m: first EMA20 touch-close versus break-and-reclaim entry.

Touch-close: first later 15m candle TOUCHES prior completed EMA20 and closes
  above it (long) / below it (short). Entry at NEXT 15m open.
Reclaim: first later 15m candle TOUCHES prior completed EMA20 and CLOSES
  below it (long) / above it (short). A separate subsequent completed 15m
  candle must close back above it (long) / below it (short). Enter next 15m open.
Combined: choose touch-close if first touch finishes on trend side, or wait for reclaim\n  if first touch finishes on the opposite side; do not enter twice.\nThe first touch of a cycle is consumed even when invalid. No re-entries in cycle.
All price-dependent intraminute stops and targets replayed on two hypothesized
OHLC paths from 1m candles; paths are not historical ticks.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from research_ema20_second_touch import read_source, MONTHS, FEE, SLIP
from research_st_firsttouch_ema20_tp2r_stflip_1h15m import st_and_ema, ts_iso

OUT=Path("analysis/st_touch_reclaim_btc_only_15m_20261123")
INITIAL=1000.
TF=15
PATHS=("O-H-L-C","O-L-H-C")
# mode, reclaim maximum following 15m bars, 1H trend alignment, target multiple
# Frozen before the result, not a blind optimizer.
CONFIGS={
  "touch_close_2R":("touch",0,False,2),
  "touch_close_2R_1hST":("touch",0,True,2),
  "reclaim4_3R":("reclaim",4,False,3),
  "reclaim4_3R_1hST":("reclaim",4,True,3),
  "combined4_2R":("combined",4,False,2),
  "combined4_3R":("combined",4,False,3),
  "combined4_2R_1hST":("combined",4,True,2),
  "combined4_3R_1hST":("combined",4,True,3),
  "combined8_3R":("combined",8,False,3),
  "combined8_3R_1hST":("combined",8,True,3),
}

def make_signals(df,ema,trend,valid,mode,max_wait):
    """Only completed 15m bars. Signals are indexed at the NEXT bar's 1m open."""
    n=len(trend)
    h=df.high.to_numpy(float).reshape(-1,TF).max(axis=1)
    l=df.low.to_numpy(float).reshape(-1,TF).min(axis=1)
    c=df.close.to_numpy(float).reshape(-1,TF)[:,-1]
    assert len(h)==n
    result={}
    active=0
    epoch=0
    used=False
    pending_at=None
    count_touches=0
    count_reject=0
    count_reclaims=0
    count_expired=0
    for j in range(101,n-1):
        if not valid[j] or not valid[j-1] or not np.isfinite(ema[j-1]) or trend[j]==0:
            pending_at=None
            continue
        side=int(trend[j])
        if side!=active:
            active=side
            epoch+=1
            used=False
            pending_at=None
            continue  # Flip candle itself MUST be ignored.
        prev_ema=float(ema[j-1]) # Last closed value at START of this 15m candle.
        finished_ema=float(ema[j])
        # Close must satisfy both EMA at start and confirmed EMA at end.
        trend_side=side*(c[j]-prev_ema)>0 and side*(c[j]-finished_ema)>0
        other_side=side*(c[j]-prev_ema)<0 and side*(c[j]-finished_ema)<0
        if pending_at is not None:
            if j-pending_at>max_wait:
                count_expired+=1
                pending_at=None
            elif trend_side:
                result[(j+1)*TF]=dict(epoch=epoch,side=side,signal_close_bar=j)
                count_reclaims+=1
                pending_at=None
            continue
        if used:
            continue
        # Uses prev fixed EMA20, avoiding same-bar derived trigger level.
        if not (l[j]<=prev_ema<=h[j]):
            continue
        used=True
        count_touches+=1
        if mode=="touch" or (mode=="combined" and trend_side):
            if trend_side:
                result[(j+1)*TF]=dict(epoch=epoch,side=side,signal_close_bar=j)
            else:
                count_reject+=1
        else:
            if other_side:
                pending_at=j
            else:
                count_reject+=1
    return result, dict(first_touches=count_touches,invalid_first_touches=count_reject,
                        valid_reclaims=count_reclaims,expired_reclaim_windows=count_expired)

def run(df,symbol,features,config_name,cfg,path_name,signals,diagnostics):
    mode,wait,align_hour,tpR=cfg
    ema,stline,trend,valid,hour_trend=features
    tm=df.time.to_numpy(np.int64)
    op,hi,lo,cl=(df[k].to_numpy(float) for k in ("open","high","low","close"))
    monthends={}
    for mon in MONTHS:
        end=(pd.Period(mon,freq="M")+1).start_time.tz_localize("Asia/Kolkata").tz_convert("UTC")-pd.Timedelta(minutes=1)
        sec=int(end.timestamp())
        ix=int(np.searchsorted(tm,sec,side="right")-1)
        assert ix>=0 and tm[ix]==sec
        monthends[ix]=mon
    cash=INITIAL
    pos=None
    trades=[]
    monthly=[]
    active=0
    high_eq=INITIAL
    low_eq=INITIAL
    max_dd=0.
    filter_rejected=0
    invalid_risk=0
    signals_used=0
    def mark(px):
        nonlocal high_eq,low_eq,max_dd
        eq=cash
        if pos is not None:
            proxy=px*(1-pos["side"]*SLIP)
            eq+=pos["side"]*pos["qty"]*(proxy-pos["entry"])-FEE*pos["qty"]*proxy
        high_eq=max(high_eq,eq)
        low_eq=min(low_eq,eq)
        if high_eq>0: max_dd=max(max_dd,100*(high_eq-eq)/high_eq)
        return eq
    def exit_trade(price,sec,why):
        nonlocal pos,cash
        p=pos
        assert p is not None
        fill=price*(1-p["side"]*SLIP)
        gross=p["side"]*p["qty"]*(fill-p["entry"])
        exit_fee=FEE*p["qty"]*fill
        net=gross-p["fee"]-exit_fee
        cash+=gross-exit_fee
        trades.append(dict(symbol=symbol,config=config_name,path_assumption=path_name,
            entry_time_utc=ts_iso(p["when"]),exit_time_utc=ts_iso(sec),
            exit_month_ist=pd.Timestamp(sec,unit="s",tz="UTC").tz_convert("Asia/Kolkata").strftime("%Y-%m"),
            direction="LONG" if p["side"]==1 else "SHORT",entry=p["entry"],
            exit=fill,entry_ST=p["ST"],R=p["R"],target=p["target"],stop=p["stop"],
            exit_reason=why,net_usd=net,fee_gst_usd=p["fee"]+exit_fee,
            equity_after_usd=cash,epoch=p["epoch"]))
        pos=None

    assert tm[0]%(TF*60)==0
    for i in range(len(df)):
        done=i//TF-1
        if done<100 or done>=len(trend) or not valid[done] or trend[done]==0:
            continue
        sec=int(tm[i])
        side=int(trend[done])
        if side!=active:
            if pos is not None:
                assert pos["side"]!=side
                exit_trade(float(op[i]),sec,"SUPERTREND_FLIP")
            active=side
        raw_open=float(op[i])
        # Active position may exit before any new order.
        if pos is not None:
            if pos["side"]*(raw_open-pos["target"])>=0:
                exit_trade(float(pos["target"]),sec,"TP")
            elif pos["side"]*(raw_open-pos["stop"])<=0:
                exit_trade(raw_open,sec,"STOP_GAP")
        if i in signals and pos is None and cash>0:
            sig=signals[i]
            assert sig["side"]==side, "Direction changed after confirmation"
            allowed=True
            if align_hour:
                hdone=i//60-1
                allowed=hdone>=0 and int(hour_trend[hdone])==side
            if not allowed:
                filter_rejected+=1
            else:
                entry=raw_open*(1+side*SLIP)
                line=float(stline[done])
                R=side*(entry-line)
                target=entry+side*tpR*R
                stop=entry-side*R
                if not (np.isfinite(R) and R>0 and stop>0 and target>0 and np.isfinite(target)):
                    invalid_risk+=1
                else:
                    qty=cash/entry
                    fee=FEE*qty*entry
                    cash-=fee
                    pos=dict(side=side,entry=entry,ST=line,R=R,
                        target=target,stop=stop,qty=qty,fee=fee,when=sec,epoch=sig["epoch"])
                    signals_used+=1
        path=(raw_open,float(hi[i]),float(lo[i]),float(cl[i])) if path_name=="O-H-L-C" else (raw_open,float(lo[i]),float(hi[i]),float(cl[i]))
        mark(path[0])
        for k in range(3):
            if pos is None:
                mark(path[k+1])
                continue
            dest=float(path[k+1]);p=pos
            if p["side"]*(dest-p["target"])>=0:
                mark(p["target"])
                exit_trade(float(p["target"]),sec,"TP")
            elif p["side"]*(dest-p["stop"])<=0:
                mark(p["stop"])
                exit_trade(float(p["stop"]),sec,"STOP")
            else:
                mark(dest)
        if i in monthends:
            monthly.append(dict(month_ist=monthends[i],equity_usd=mark(float(cl[i])),
                                position_open_at_month_end=pos is not None))
    if pos is not None:
        exit_trade(float(cl[-1]),int(tm[-1]),"SAMPLE_END_ACCOUNTING_ONLY")
        monthly[-1]["equity_usd"]=cash
    assert len(monthly)==22
    ledger=pd.DataFrame(trades)
    if ledger.empty: raise AssertionError("No trades: "+symbol+" "+config_name)
    if ledger.epoch.duplicated().any():
        raise AssertionError("More than one trade per ST cycle")
    if abs(float(ledger.net_usd.sum())-(cash-INITIAL))>0.02:
        raise AssertionError("Ledger/cash mismatch")
    mdf=pd.DataFrame(monthly)
    mdf["return_pct"]=100*(mdf.equity_usd/mdf.equity_usd.shift(1,fill_value=INITIAL)-1)
    y25=float(mdf.loc[mdf.month_ist=="2025-12","equity_usd"].iloc[0])
    wins=ledger.net_usd>0
    gain=float(ledger.loc[wins,"net_usd"].sum())
    loss=-float(ledger.loc[~wins,"net_usd"].sum())
    summary=dict(symbol=symbol,config=config_name,path_assumption=path_name,
         trades=len(ledger),wins=int(wins.sum()),losses=int((~wins).sum()),
         win_rate_pct=round(100*wins.mean(),3),profit_factor=round(gain/loss,4) if loss>0 else None,
         net_return_pct=round(100*(cash/INITIAL-1),4),net_profit_usd=round(cash-INITIAL,4),
         profitable_months=int((mdf.return_pct>0).sum()),
         profitable_2025_months=int((mdf.iloc[:12].return_pct>0).sum()),
         profitable_2026_months=int((mdf.iloc[12:].return_pct>0).sum()),
         return_2025_pct=round(100*(y25/INITIAL-1),3),
         return_2026_pct=round(100*(cash/y25-1),3),
         max_floating_dd_pct=round(max_dd,3),min_equity=round(low_eq,3),
         fees_gst_usd=round(ledger.fee_gst_usd.sum(),4),
         tp_exits=int((ledger.exit_reason=="TP").sum()),
         stop_exits=int(ledger.exit_reason.isin(["STOP","STOP_GAP"]).sum()),
         flip_exits=int((ledger.exit_reason=="SUPERTREND_FLIP").sum()),
         signals=len(signals),signals_used=signals_used,
         rejected_1h_filter=filter_rejected,invalid_R=invalid_risk,
         **diagnostics)
    mdf.insert(0,"config",config_name)
    mdf.insert(0,"symbol",symbol)
    mdf.insert(0,"path_assumption",path_name)
    return summary,mdf,ledger

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    assert len(MONTHS)==22
    summaries=[];months=[];trades=[];quality={}
    for symbol in ("BTCUSD",):
        df,q=read_source(symbol)
        quality[symbol]=q
        ema,line,trend,valid=st_and_ema(df,15)
        _,_,hrtrend,_=st_and_ema(df,60)
        features=(ema,line,trend,valid,hrtrend)
        signal_cache={}
        for name,cfg in CONFIGS.items():
            key=(cfg[0],cfg[1])
            if key not in signal_cache:
                signal_cache[key]=make_signals(df,ema,trend,valid,*key)
            sigs,diag=signal_cache[key]
            for path in PATHS:
                print("RUN",symbol,name,path,flush=True)
                summary,mm,tt=run(df,symbol,features,name,cfg,path,sigs,diag)
                summaries.append(summary); months.append(mm); trades.append(tt)
                print("RESULT",json.dumps(summary,sort_keys=True),flush=True)
    sdf=pd.DataFrame(summaries)
    # Historical baseline parity - reject modified code if these controls change.
    references={("BTCUSD","touch_close_2R"):(809,-66.4683),
                ("BTCUSD","reclaim4_3R_1hST"):(206,-32.108)}
    for (sym,cfg),(expected_n,expected_net) in references.items():
        rr=sdf[(sdf.symbol==sym)&(sdf.config==cfg)&(sdf.path_assumption=="O-H-L-C")].iloc[0]
        assert int(rr.trades)==expected_n and abs(float(rr.net_return_pct)-expected_net)<.001,            ("REGRESSION_BASELINE_MISMATCH",sym,cfg,rr.to_dict())
    print("BASELINE_PARITY_OK",flush=True)
    sdf.to_csv(OUT/"summary.csv",index=False)
    pd.concat(months,ignore_index=True).to_csv(OUT/"monthly_mark_to_market.csv",index=False)
    pd.concat(trades,ignore_index=True).to_csv(OUT/"trades.csv.gz",index=False,compression="gzip")
    quality["strategy_rules"]=dict(signal_tf="15m",execution_tf="1m",
        supertrend="Wilder ATR10 factor3",EMA=20,flip_bar_excluded=True,
        entry_at="next 15m candle open after confirmation",
        first_touch="15m high-low intersects frozen prior closed 15m EMA20",
        touch_confirmation="touch candle closes on trend side of both prior and finished EMA20",
        reclaim_confirmation="first touch candle closes on wrong side of both prior and finished EMA20; subsequent bar closes back on trend side",
        reclaim_window="4 or 8 subsequent completed 15m candles",
        combined_mode="the same first touch can form immediate touch-close OR initiate a later reclaim, never both",
        one_trade_per_ST_cycle=True,st_flip_exit="next 15m candle open",
        initial_stop="1x frozen entry-to-completed-ST reference R",fixed_profit_target="2R or 3R",
        optional_1h_alignment="last completed 1h Supertrend trend same direction",
        initial_capital_usd=INITIAL,leverage="1x evolving equity notional",
        paths=PATHS,slippage_each_side=SLIP,fee_including_GST_each_side=FEE,
        no_volume_or_volatility_filter=True,
        excludes="funding, liquidation, depth, spread, tick order, live latency",
        all_data_in_sample=True)
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2,default=str)+"\n")
    table=sdf[sdf.path_assumption=="O-H-L-C"][
        ["symbol","config","trades","win_rate_pct","profit_factor","net_return_pct","profitable_months","return_2025_pct","return_2026_pct","max_floating_dd_pct"]]
    report=[
        "# BTCUSD ONLY — Touch-close vs break-and-reclaim vs combined entry (15M Supertrend + EMA20)",
        "",
        "First touch only per ST cycle, flip candle excluded. Entry at next 15m open AFTER closed confirmation. "
        "Fixed 1R stop and 2R/3R targets; 1m stop/TP simulation. Includes both long and short; weekends on.",
        "",
        "Touch-close: after flip, first EMA20 interaction CLOSES on trend side; trade next open.",
        "Reclaim: after flip, first EMA20 interaction CLOSES on WRONG side; later separate 15m bar CLOSES back on trend side; trade next open.",
        "Combined: use Touch when first touched candle closes on trend side, else use Reclaim if it closes on wrong side and later returns. Only one entry per Supertrend cycle.",
        "Both refer to prior frozen EMA20 and completed candle EMA20 to prevent ambiguous closes. No repaint.",
        "",
        "Data Jan 2025–Oct 2026 IST, Delta India historical 1m; 1x notional, $1000 starting capital, "
        "0.05% taker fee each side + 18% GST and 0.02% slippage each side.",
        "No funding, liquidation, spread, depth, tick-order guarantee, or genuine 2026 out-of-sample.",
        "",
        "## O-H-L-C 1m path comparison","",table.to_markdown(index=False),"",
        "All path variants and monthly mark-to-market in summary.csv / monthly_mark_to_market.csv.",
        "This is retrospective in-sample research, not a validated live edge.",
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("BACKTEST_DONE",len(summaries),flush=True)
if __name__=="__main__":
    main()
