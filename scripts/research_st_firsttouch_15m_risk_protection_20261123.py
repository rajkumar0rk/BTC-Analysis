#!/usr/bin/env python3
"""15M ST10x3 first EMA20 touch: risk-stop/profit protection and trend-filter ablation.
Causal 1m OHLC path replays; no historical ticks, funding, spread or liquidation.
"""
from pathlib import Path
import json
import pandas as pd
import numpy as np
from research_st_firsttouch_ema20_tp2r_stflip_1h15m import st_and_ema, ts_iso
from research_ema20_second_touch import read_source, MONTHS, FEE, SLIP

OUT = Path("analysis/st_firsttouch_15m_risk_protection_20261123")
INITIAL = 1000.0
TF = 15
PATHS = ("O-H-L-C", "O-L-H-C")
# Freeze candidate list before inspecting results: no post hoc grid search.
CONFIGS = {
 "original_2R_flip": (None, 2, None, None, "none"),
 "stop1R_tp2R": (1, 2, None, None, "none"),
 "stop1R_tp3R": (1, 3, None, None, "none"),
 "stop1R_tp4R": (1, 4, None, None, "none"),
 "stop1p5R_tp3R": (1.5, 3, None, None, "none"),
 "stop1R_tp2R_BE1R": (1, 2, 1, None, "none"),
 "stop1R_tp3R_BE1R": (1, 3, 1, None, "none"),
 "stop1R_tp3R_lock0p5R_at2R": (1, 3, 1, 2, "none"),
 "stop1R_tp2R_1hST": (1, 2, None, None, "1h"),
 "stop1R_tp3R_1hST": (1, 3, None, None, "1h"),
 "stop1R_tp3R_EMAslope": (1, 3, None, None, "slope"),
 "stop1R_tp3R_both": (1, 3, None, None, "both"),
}

def run_asset(df, symbol, features, name, cfg, path_name):
    ema, line, trend, valid, hour_trend = features
    stopmult, tpmult, be_trigger, lock_trigger, filter_name = cfg
    t = df.time.to_numpy(dtype=np.int64)
    op, hi, lo, cl = (df[k].to_numpy(dtype=float) for k in ("open","high","low","close"))
    monthends = {}
    for month in MONTHS:
        end = (pd.Period(month, freq="M") + 1).start_time.tz_localize("Asia/Kolkata").tz_convert("UTC") - pd.Timedelta(minutes=1)
        sec = int(end.timestamp())
        j = int(np.searchsorted(t,sec,side="right")-1)
        assert j>=0 and t[j]==sec, ("month-end missing", symbol, month)
        monthends[j] = month

    cash = INITIAL
    pos = None
    current_direction = 0
    epoch = 0
    used_epoch = -1
    denied_filter = 0
    denied_R = 0
    trades = []
    monthly = []
    high_eq = INITIAL
    max_dd = 0.0
    min_eq = INITIAL

    def mark(raw):
        nonlocal high_eq, max_dd, min_eq
        eq = cash
        if pos is not None:
            close_proxy = raw * (1 - pos["side"] * SLIP)
            eq += pos["side"] * pos["qty"] * (close_proxy-pos["entry"]) - FEE * pos["qty"] * close_proxy
        high_eq = max(high_eq,eq)
        min_eq = min(min_eq,eq)
        if high_eq > 0:
            max_dd = max(max_dd,100*(high_eq-eq)/high_eq)
        return eq

    def exit_trade(raw, sec, reason):
        nonlocal cash, pos
        p = pos
        assert p is not None
        fill = raw * (1 - p["side"] * SLIP)
        gross = p["side"] * p["qty"] * (fill-p["entry"])
        fee_out = FEE * p["qty"] * fill
        cash += gross-fee_out
        net = gross - fee_out - p["fee_in"]
        trades.append(dict(symbol=symbol, path_assumption=path_name, config=name,
            entry_time_utc=ts_iso(p["start"]), exit_time_utc=ts_iso(sec),
            exit_month_ist=pd.Timestamp(sec,unit="s",tz="UTC").tz_convert("Asia/Kolkata").strftime("%Y-%m"),
            direction="LONG" if p["side"]==1 else "SHORT", entry=p["entry"],
            exit=fill, ST_reference=p["line"], R=p["R"], target=p["target"],
            stop_at_exit=p["stop"], exit_reason=reason, net_usd=net,
            net_R=net/(p["qty"]*p["R"]), fee_gst_usd=p["fee_in"]+fee_out,
            equity_after_usd=cash, epoch=p["epoch"]))
        pos = None

    for i in range(len(df)):
        done = i//TF - 1
        if done < 100 or done >= len(trend) or not valid[done] or trend[done] == 0 or not np.isfinite(line[done]):
            continue
        sec = int(t[i])
        direction = int(trend[done])
        if current_direction != direction:
            if pos is not None:
                assert pos["side"] != direction
                exit_trade(float(op[i]),sec,"SUPERTREND_FLIP")
            current_direction = direction
            epoch += 1

        path = (op[i],hi[i],lo[i],cl[i]) if path_name=="O-H-L-C" else (op[i],lo[i],hi[i],cl[i])
        o = float(path[0])
        # At minute opens, honor adverse stop gaps and conservative target fills.
        if pos is not None:
            if direction * (o - pos["target"]) >= 0:
                exit_trade(float(pos["target"]),sec,"TP")
            elif pos["stop"] is not None and direction*(o-pos["stop"]) <= 0:
                exit_trade(o,sec,"STOP_GAP")
        mark(o)
        for k in range(3):
            a,b = float(path[k]), float(path[k+1])
            if pos is not None:
                p = pos
                side = p["side"]
                if side*(b-p["target"]) >= 0:
                    mark(float(p["target"]))
                    exit_trade(float(p["target"]),sec,"TP")
                elif p["stop"] is not None and side*(b-p["stop"]) <= 0:
                    mark(float(p["stop"]))
                    exit_trade(float(p["stop"]),sec,"STOP")
                else:
                    # Update profit protection only after favorable price reaches activation.
                    if side*(b-a)>0 and p["stop"] is not None:
                        if be_trigger is not None and side*(b-p["entry"])>=be_trigger*p["R"]:
                            if side*(p["entry"]-p["stop"])>0:
                                p["stop"] = p["entry"]
                        if lock_trigger is not None and side*(b-p["entry"])>=lock_trigger*p["R"]:
                            candidate = p["entry"]+side*0.5*p["R"]
                            if side*(candidate-p["stop"])>0:
                                p["stop"]=candidate
                    mark(b)
                continue

            if used_epoch == epoch or cash <= 0:
                mark(b)
                continue
            level = float(ema[done])
            if not np.isfinite(level) or not (min(a,b)<=level<=max(a,b)):
                mark(b)
                continue
            # First intersection consumes eligibility whether rejected or executed.
            used_epoch=epoch
            allowed=True
            if filter_name in ("1h","both"):
                hdone=i//60-1
                allowed = hdone >= 0 and int(hour_trend[hdone])==direction
            if filter_name in ("slope","both"):
                allowed = allowed and done >= 4 and direction*(ema[done]-ema[done-4])>0
            if not allowed:
                denied_filter += 1
                mark(b)
                continue
            entry=level*(1+direction*SLIP)
            st=float(line[done])
            R=direction*(entry-st)
            if not (np.isfinite(R) and R>0):
                denied_R += 1
                mark(b)
                continue
            target=entry+direction*tpmult*R
            if target<=0:
                denied_R += 1
                mark(b)
                continue
            stop=None if stopmult is None else entry-direction*stopmult*R
            qty=cash/entry
            fee_in=FEE*qty*entry
            cash-=fee_in
            pos=dict(side=direction,entry=entry,line=st,R=R,target=target,
                     stop=stop,qty=qty,fee_in=fee_in,start=sec,epoch=epoch)
            mark(level)
            # Check ONLY the remainder of the segment after EMA was touched.
            if direction*(b-target)>=0:
                mark(target)
                exit_trade(target,sec,"TP")
            elif stop is not None and direction*(b-stop)<=0:
                mark(stop)
                exit_trade(stop,sec,"STOP")
            elif pos is not None:
                if direction*(b-level)>0 and be_trigger is not None and direction*(b-entry)>=be_trigger*R:
                    pos["stop"]=entry
                if direction*(b-level)>0 and lock_trigger is not None and direction*(b-entry)>=lock_trigger*R:
                    pos["stop"]=entry+direction*0.5*R
                mark(b)

        if i in monthends:
            monthly.append(dict(month_ist=monthends[i], equity_usd=mark(float(cl[i])),
                open_position=pos is not None))
    if pos is not None:
        exit_trade(float(cl[-1]),int(t[-1]),"SAMPLE_END_ACCOUNTING_ONLY")
        monthly[-1]["equity_usd"]=cash
    assert len(monthly)==22
    ledger=pd.DataFrame(trades)
    assert not ledger.empty
    assert not ledger.epoch.duplicated().any()
    assert abs(ledger.net_usd.sum()-(cash-INITIAL))<0.02, "ledger mismatch"
    months=pd.DataFrame(monthly)
    months["return_pct"]=100*(months.equity_usd/months.equity_usd.shift(1,fill_value=INITIAL)-1)
    wins=ledger.net_usd>0
    gp=ledger.loc[wins,"net_usd"].sum()
    gl=-ledger.loc[~wins,"net_usd"].sum()
    year_end=float(months.loc[months.month_ist=="2025-12","equity_usd"].iloc[0])
    result=dict(symbol=symbol,path_assumption=path_name,config=name,trades=len(ledger),
        wins=int(wins.sum()),losses=int((~wins).sum()),win_rate_pct=round(100*wins.mean(),3),
        profit_factor=round(gp/gl,4) if gl else 0,
        net_return_pct=round(100*(cash/INITIAL-1),4),
        net_profit_usd=round(cash-INITIAL,4),
        positive_months=int((months.return_pct>0).sum()),
        positive_2025_months=int((months.iloc[:12].return_pct>0).sum()),
        positive_2026_months=int((months.iloc[12:].return_pct>0).sum()),
        year_2025_return_pct=round(100*(year_end/INITIAL-1),3),
        year_2026_return_pct=round(100*(cash/year_end-1),3),
        max_floating_drawdown_pct=round(max_dd,3),
        min_floating_equity_usd=round(min_eq,3),
        tp_exits=int((ledger.exit_reason=="TP").sum()),
        stop_exits=int(ledger.exit_reason.isin(["STOP","STOP_GAP"]).sum()),
        flip_exits=int((ledger.exit_reason=="SUPERTREND_FLIP").sum()),
        fees_gst_usd=round(ledger.fee_gst_usd.sum(),4),
        filter_rejections=denied_filter, invalid_risk=denied_R)
    months.insert(0,"config",name)
    months.insert(0,"symbol",symbol)
    months.insert(0,"path_assumption",path_name)
    return ledger,months,result

def main():
    assert all(c[0] is None or c[0]>0 for c in CONFIGS.values())
    assert len(MONTHS)==22
    OUT.mkdir(parents=True,exist_ok=True)
    results=[]; all_months=[]; all_trades=[]; quality={}
    for symbol in ("BTCUSD","ETHUSD"):
        df,q=read_source(symbol)
        quality[symbol]=q
        ema,line,trend,valid=st_and_ema(df,TF)
        _,_,hour_trend,_=st_and_ema(df,60)
        features=(ema,line,trend,valid,hour_trend)
        for name,cfg in CONFIGS.items():
            for path in PATHS:
                print("RUN",symbol,name,path,flush=True)
                trade,monthly,summary=run_asset(df,symbol,features,name,cfg,path)
                all_trades.append(trade)
                all_months.append(monthly)
                results.append(summary)
                print("RESULT",json.dumps(summary,sort_keys=True),flush=True)
    result_df=pd.DataFrame(results)
    # Original code baseline parity: fail experiment if exact first-touch baseline cannot reproduce.
    expected={("BTCUSD","O-H-L-C"):(1554,-93.5378),
              ("BTCUSD","O-L-H-C"):(1554,-93.5441),
              ("ETHUSD","O-H-L-C"):(1422,-92.6031),
              ("ETHUSD","O-L-H-C"):(1422,-92.7268)}
    for (symbol,path),(trades,ret) in expected.items():
        got=result_df[(result_df.symbol==symbol)&(result_df.path_assumption==path)&(result_df.config=="original_2R_flip")].iloc[0]
        assert int(got.trades)==trades and abs(float(got.net_return_pct)-ret)<0.001,(symbol,path,got.to_dict())
    result_df.to_csv(OUT/"summary.csv",index=False)
    pd.concat(all_months,ignore_index=True).to_csv(OUT/"monthly_mark_to_market.csv",index=False)
    pd.concat(all_trades,ignore_index=True).to_csv(OUT/"trades.csv.gz",index=False,compression="gzip")
    quality["rules"]=dict(signal_tf=15,execution_tf=1,supertrend="Wilder ATR 10, multiplier 3",
        ema=20,first_touch_only=True,flip_candle_excluded=True,
        no_volume_or_volatility_filter=True,one_trade_per_st_epoch=True,
        stop_touched_using_1m_path=True,stop_gap_filled_at_open=True,
        flip_exit_at_next_15m_open=True, take_profit_fixed_R=True,
        risk_reference="entry_fill to completed ST line, frozen",
        slippage_each_side=SLIP,fee_plus_GST_each_side=FEE,one_x_notional=True,
        months="2025-01 through 2026-10 IST",
        both_1m_paths=list(PATHS),candidate_configs=CONFIGS,
        selection_warning="In-sample candidate comparison, not a fresh 2026 out-of-sample; no forward edge established")
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2)+"\n")
    (OUT/"RESEARCH_REPORT.md").write_text(
        "# ST10x3 first EMA20 touch 15m risk-protection ablation\n\n"
        "Both BTC and ETH. Jan 2025–Oct 2026 IST, 1m execution, weekends included. "
        "No tick path, depth, funding, liquidation, or spread. Cost: 0.05% taker each side, "
        "GST18%, adverse 0.02% slippage each side; 1x notional, $1000 each.\n\n"
        "No optimization against untouched holdout; all variants predeclared. "
        "Both hypothetical 1m OHLC paths tested. Original baseline parity is mandatory.\n\n"
        +result_df.to_markdown(index=False)+"\n\n"
        "See summary.csv, monthly_mark_to_market.csv, trades.csv.gz, quality.json.\n")
    print("BACKTEST_DONE",len(results),flush=True)

if __name__=="__main__":
    main()
