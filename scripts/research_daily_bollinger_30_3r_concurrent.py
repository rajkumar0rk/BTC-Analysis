#!/usr/bin/env python3
"""Publisher-style overlapping-entry audit: daily BB30/ATR14/3R on Delta real 1m.
Multiple simultaneous signals permitted; shared gross leverage budget 2x.
Separate from strict one-position model, both reproducible without parameter fitting.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from research_daily_bollinger_30_3r import (
    load_1m, daily_signals, load_funding, OUT, INITIAL, RISK_PCT,
    LEVERAGE_CAP, FEE_RATE, SLIP_PTS
)

def simulate(d, signals, funding):
    unix=d.time.to_numpy(np.int64)
    o,h,l,c=[d[k].to_numpy(float) for k in ("open","high","low","close")]
    local=d.index.tz_convert("Asia/Kolkata")
    ym=local.year.to_numpy()*100+local.month.to_numpy()
    eom={i:int(ym[i]) for i in range(len(unix)) if i==len(unix)-1 or ym[i]!=ym[i+1]}
    positions=[]
    ledger=[]
    month_equity={}
    equity=INITIAL
    skipped_cap=0
    skipped_invalid=0
    accepted=0
    funding_due=0
    missing_funding=0
    peak_concurrent=0
    def mark_equity(px):
        est=equity
        for p in positions:
            exit_fill=px-p["side"]*SLIP_PTS
            est += p["side"]*p["qty"]*(exit_fill-p["entry_fill"]) - \
                FEE_RATE*p["qty"]*(p["entry_fill"]+exit_fill)+p["funding"]
        return est
    for i in range(len(unix)):
        sec=int(unix[i])
        if positions and sec%(8*3600)==0:
            for p in positions:
                funding_due+=1
                if sec in funding:
                    p["funding"] += -p["side"]*p["qty"]*o[i]*(funding[sec]/100)
                    p["funding_events"]+=1
                else:
                    missing_funding+=1
        if sec in signals:
            side,stop,signal_day,signal_close,atr=signals[sec]
            mid=float(o[i])
            entry_fill=mid+side*SLIP_PTS
            riskpts=side*(entry_fill-stop)
            eq=mark_equity(mid)
            used=sum(p["qty"]*mid for p in positions)
            available=max(0.,LEVERAGE_CAP*eq-used)
            if eq<=0 or riskpts<=0 or not np.isfinite(riskpts):
                skipped_invalid+=1
            else:
                qty=min(eq*RISK_PCT/riskpts, available/entry_fill)
                if qty<=1e-12:
                    skipped_cap+=1
                else:
                    positions.append(dict(side=side,entry_i=i,entry_utc=str(d.index[i]),
                        entry_mid=mid,entry_fill=entry_fill,qty=qty,stop=stop,
                        target=entry_fill+side*3*riskpts,risk_pts=riskpts,
                        signal_day_utc=signal_day, initial_marked_eq=eq, funding=0.,
                        funding_events=0,initial_portfolio_leverage=(used+qty*entry_fill)/eq))
                    accepted+=1
                    peak_concurrent=max(peak_concurrent,len(positions))
        remaining=[]
        for p in positions:
            side=p["side"]
            stop_hit=(l[i]<=p["stop"] if side==1 else h[i]>=p["stop"])
            target_hit=(h[i]>=p["target"] if side==1 else l[i]<=p["target"])
            if not (stop_hit or target_hit):
                remaining.append(p)
                continue
            if stop_hit:
                exitmid=min(o[i],p["stop"]) if side==1 else max(o[i],p["stop"])
                reason="stop"
            else:
                exitmid=p["target"]
                reason="target"
            fill=exitmid-side*SLIP_PTS
            qty=p["qty"]
            gross=side*qty*(exitmid-p["entry_mid"])
            slip=2*SLIP_PTS*qty
            fees=FEE_RATE*qty*(p["entry_fill"]+fill)
            pnl=gross-slip-fees+p["funding"]
            equity+=pnl
            ledger.append(dict(
                entry_utc=p["entry_utc"],exit_utc=str(d.index[i]),
                side="LONG" if side==1 else "SHORT",signal_day_utc=p["signal_day_utc"],
                entry_ist_month=str(int(ym[p["entry_i"]])),exit_ist_month=str(int(ym[i])),
                entry_fill=round(p["entry_fill"],4), exit_fill=round(float(fill),4),
                stop=round(p["stop"],4), target=round(p["target"],4),
                risk_points=round(p["risk_pts"],4), quantity_btc=round(qty,8),
                portfolio_leverage_at_entry=round(p["initial_portfolio_leverage"],4),
                held_minutes=i-p["entry_i"]+1,reason=reason,
                gross_usd=round(gross,5),slippage_usd=round(slip,5),
                fees_gst_usd=round(fees,5),funding_proxy_usd=round(p["funding"],5),
                funding_events=p["funding_events"],net_usd=round(pnl,5),
                net_R=round(pnl/(qty*p["risk_pts"]),5),closed_equity=round(equity,4)))
        positions=remaining
        if i in eom:
            month_equity[eom[i]]=dict(estimated=mark_equity(float(c[i])),
                open_positions=len(positions),end_utc=str(d.index[i]))
    df=pd.DataFrame(ledger)
    if df.empty:
        raise RuntimeError("No closed trades; refusing empty report")
    mo=[]
    old=INITIAL
    for code, val in sorted(month_equity.items()):
        month=f"{code//100:04}-{code%100:02}"
        sub=df[df.exit_ist_month==str(code)]
        eq=float(val["estimated"])
        mo.append(dict(month_ist=month,account_return_pct=round(100*(eq/old-1),3),
            end_marked_equity_usd=round(eq,2),trades_closed=len(sub),
            winners=int((sub.net_usd>0).sum()),losers=int((sub.net_usd<=0).sum()),
            closed_net_usd=round(float(sub.net_usd.sum()),2),
            open_positions_eom=val["open_positions"],complete=(month!="2026-11")))
        old=eq
    monthly=pd.DataFrame(mo)
    values=df.net_usd.to_numpy(float)
    poswin=values[values>0].sum()
    negloss=-values[values<0].sum()
    equities=np.r_[INITIAL,monthly.end_marked_equity_usd.to_numpy(float)]
    dd=float((equities/np.maximum.accumulate(equities)-1).min()*100)
    summary=dict(
        data="Delta India BTCUSD genuine 1m",period_start_utc=str(d.index[0]),
        period_end_utc=str(d.index[-1]),initial_equity_usd=INITIAL,
        final_marked_equity_usd=round(float(monthly.end_marked_equity_usd.iloc[-1]),2),
        parallel_signals=True,accepted_entries=accepted,skipped_leverage=skipped_cap,
        skipped_invalid=skipped_invalid,open_positions_end=len(positions),
        peak_concurrent_positions=peak_concurrent,trades_closed=len(df),
        winners=int((values>0).sum()),losers=int((values<=0).sum()),
        win_rate_pct=round(100*(values>0).mean(),2),
        net_profit_factor=round(float(poswin/negloss),3) if negloss else None,
        average_net_R=round(float(df.net_R.mean()),4),
        net_closed_usd=round(float(values.sum()),2),
        gross_usd=round(float(df.gross_usd.sum()),2),
        slippage_usd=round(float(df.slippage_usd.sum()),2),
        fees_gst_usd=round(float(df.fees_gst_usd.sum()),2),
        funding_proxy_usd=round(float(df.funding_proxy_usd.sum()),2),
        positive_full_months=int(((monthly.account_return_pct>0)&monthly.complete).sum()),
        full_months=int(monthly.complete.sum()),max_month_end_drawdown_pct=round(dd,2),
        funding_settlement_position_events=funding_due,
        missing_funding_proxy_events=missing_funding,
        limitations=["Multiple independent long and short exposures in one portfolio may require hedge mode/subaccounts.",
                     "Rates are funding proxies not settled cash transactions.",
                     "Gross notional cap is aggregate 2x marked equity, continuous sizing; liquidation not simulated.",
                     "In 1m ambiguous bars, STOP priority. Signal next 1m open. No spread/depth available.",
                     "2026 research-exposed, not independent out-of-sample."]
    )
    return df,monthly,summary

def main():
    d,files=load_1m()
    daily,signal_map,raw=daily_signals(d)
    fund,fundparts=load_funding()
    trades,month,summary=simulate(d,signal_map,fund)
    summary["source_files"]=len(files)
    summary["signal_count"]=raw
    summary["funding_files"]=fundparts
    trades.to_csv(OUT/"concurrent_trade_ledger.csv",index=False)
    month.to_csv(OUT/"concurrent_monthly_ist.csv",index=False)
    (OUT/"concurrent_summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    yearrows=[]
    for yr,z in month.groupby(month.month_ist.str[:4]):
        start=INITIAL if yr=="2025" else float(month.loc[month.month_ist==f"{int(yr)-1}-12","end_marked_equity_usd"].iloc[0])
        end=float(z.end_marked_equity_usd.iloc[-1])
        yearrows.append(dict(year=yr,return_pct=round(100*(end/start-1),3),
                             trades_closed=int(z.trades_closed.sum()),complete=bool(z.complete.all())))
    pd.DataFrame(yearrows).to_csv(OUT/"concurrent_yearly_ist.csv",index=False)
    print("CONCURRENT_DAILY_BB30_3R_COMPLETE")
    print(json.dumps(summary,indent=2))
    print(month.to_string(index=False))
if __name__=="__main__":
    main()
