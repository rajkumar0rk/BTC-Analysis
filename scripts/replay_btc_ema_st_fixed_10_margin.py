#!/usr/bin/env python3
"""BTCUSD screenshot replay: $100 portfolio, fixed <=$10 isolated margin, 100x.

Reuse identical 15m historical signal and trailing replay functions from
the preceding BTC-Analysis research branch. Fixed *margin*, NOT fixed notional:
a $10 margin budget at 100x gives <= $1000 BTCUSD notional, quantized down
to 0.001 BTC lots. Fee charges are in addition to this margin budget.

No extra capital is automatically allocated to the isolated position. On a
liquidation the isolated loss is capped at the margin posted, except for the
entry taker fee/GST paid separately by the portfolio wallet.

The underlying data are traded OHLC, NOT mark prices. OHLC-based liquidation
is an illustrative scenario, not an accurate historical liquidation replay.
"""
from pathlib import Path
import math
import json
import numpy as np
import pandas as pd
from replay_btc_ema_st_screenshot import load,indicators
from replay_btc_ema_st_100x import path_exit,fee_net

OUT=Path("analysis/btc_ema_st_fixed_10_margin_20261119")
OUT.mkdir(parents=True, exist_ok=True)
STARTING_EQUITY_USD=100.0
PER_TRADE_MARGIN_BUDGET_USD=10.0
SELECTED_LEVERAGE=100
LOT_BTC=0.001
MAINTENANCE_FRACTION=0.0025
SCALPER_WINDOW_MINUTES=30
PARAMS={
  "portfolio_initial_equity_usd": STARTING_EQUITY_USD,
  "fixed_isolated_margin_budget_usd_per_trade": PER_TRADE_MARGIN_BUDGET_USD,
  "maximum_position_notional_usd": PER_TRADE_MARGIN_BUDGET_USD*SELECTED_LEVERAGE,
  "leverage":SELECTED_LEVERAGE,
  "lot_size_btc":LOT_BTC,
  "btc_usd_tick_size":0.5,
  "maintenance_margin_rate_assumed":MAINTENANCE_FRACTION,
  "scalper_fee_waiver_window_minutes_assumed":SCALPER_WINDOW_MINUTES,
  "taker_fee_pct_each_side":0.05,
  "gst_on_fees_pct":18,
  "liquidation_penalty_assumed_pct":0.05,
  "margin_mode":"isolated",
  "auto_add_margin":False,
  "auto_compound_margin":False,
  "wallet_pays_fee_outside_position_margin":True,
  "new_positions_when_wallet_cannot_cover_margin_and_entry_fee":"skip",
  "initial_stop":"ATR14 x 2",
  "trailing_activation_points":150,
  "trailing_distance_points":50,
  "signal_tf":"15m",
  "stop_monitoring_tf":"15m",
  "ohlc_path":"nearer extreme first, then farther extreme",
  "slippage_points":0,
  "funding_pct":0,
  "historical_offer_entitlement_verified":False,
  "historical_liquidation_mark_price_available":False,
}

def replay(df,start,liq_fill):
    arr=df.reset_index()
    op=arr.open.to_numpy(dtype=float)
    hi=arr.high.to_numpy(dtype=float)
    lo=arr.low.to_numpy(dtype=float)
    cl=arr.close.to_numpy(dtype=float)
    ema=arr.ema.to_numpy(dtype=float)
    atr=arr.atr14.to_numpy(dtype=float)
    dr=arr.dir.to_numpy()
    ar=arr.atr_ratio.to_numpy(dtype=float)
    vr=arr.volume_ratio.to_numpy(dtype=float)
    times=arr.dt.to_numpy()
    wallet=STARTING_EQUITY_USD
    peak=STARTING_EQUITY_USD
    max_dd_pct=0.0
    skip_margin=0
    skip_lot=0
    max_notional=0.0
    min_notional=float("inf")
    liquidations=0
    position=None
    events=[]
    eligible_signals=0
    for i in range(max(start,36),len(arr)):
        if position is not None:
            s=position
            # Overnight opening gaps beyond estimated liquidation can bypass
            # stop-market orders; treat these as liquidations, not stop fills.
            if ((s["side"]==1 and op[i]<=s["liq_price"]) or
                (s["side"]==-1 and op[i]>=s["liq_price"])):
                xp=float(op[i])
                reason="liquidation"
            else:
                xp,s["sl"],s["best"],s["active"],reason=path_exit(
                    op[i],hi[i],lo[i],cl[i],s["side"],s["entry_price"],
                    s["sl"],s["best"],s["active"],s["liq_price"])
            if xp is None and (
                (s["side"]==1 and dr[i]==1 and dr[i-1]==-1) or
                (s["side"]==-1 and dr[i]==-1 and dr[i-1]==1)
            ):
                xp=float(cl[i])
                reason="supertrend_flip"

            if xp is not None:
                if reason=="liquidation" and liq_fill=="bankruptcy":
                    xp=s["bankruptcy_price"]
                duration_minutes=(i-s["entry_idx"])*15
                fee=fee_net(s["qty_btc"],s["entry_price"],xp,s["side"],
                            duration_minutes,reason,liq_fill)
                wallet_before=wallet
                if reason=="liquidation":
                    liquidations+=1
                    # Isolated position cannot absorb other wallet funds;
                    # margin at risk is initial posted IM (no auto top-up).
                    isolated_change=max(
                        -s["margin_usd"],
                        fee["gross_usd"]-fee["liquidation_fee_usd"]-fee["liquidation_gst_usd"])
                    net=isolated_change-fee["entry_fee_usd"]-fee["entry_gst_usd"]
                else:
                    isolated_change=fee["gross_usd"]-fee["exit_fee_usd"]-fee["exit_gst_usd"]
                    net=isolated_change-fee["entry_fee_usd"]-fee["entry_gst_usd"]
                wallet=max(0.,wallet+net)
                realized=wallet-wallet_before
                peak=max(peak,wallet)
                max_dd_pct=max(max_dd_pct,100*(1-wallet/peak))
                events.append(dict(
                    entry_utc=str(pd.Timestamp(times[s["entry_idx"]])+pd.Timedelta(minutes=15)),
                    exit_utc=str(pd.Timestamp(times[i])+pd.Timedelta(minutes=15)),
                    side="long" if s["side"]==1 else "short",
                    entry_price=s["entry_price"],exit_price=xp,
                    qty_btc=s["qty_btc"],contracts=s["contracts"],
                    entry_notional_usd=s["notional_usd"],
                    posted_margin_usd=s["margin_usd"],
                    liquidation_threshold_estimate=s["liq_price"],
                    stop_at_entry=s["initial_stop"],
                    exit_reason=reason,
                    hold_minutes=duration_minutes,
                    scalper_fee_waiver_applied=fee["eligible_scalper"],
                    portfolio_before_usd=wallet_before,
                    portfolio_after_usd=wallet,
                    change_usd=realized,
                    trade_pct_of_portfolio_before=100*realized/wallet_before if wallet_before else 0,
                    gross_price_pnl_usd=fee["gross_usd"],
                    isolated_position_change_usd=isolated_change,
                    entry_fee_usd=fee["entry_fee_usd"],
                    entry_gst_usd=fee["entry_gst_usd"],
                    exit_fee_usd=fee["exit_fee_usd"],
                    exit_gst_usd=fee["exit_gst_usd"],
                    liquidation_penalty_usd=fee["liquidation_fee_usd"],
                    liquidation_penalty_gst_usd=fee["liquidation_gst_usd"]))
                position=None

        if position is None and (np.isfinite(ema[i]) and np.isfinite(atr[i])
                               and np.isfinite(ar[i]) and np.isfinite(vr[i])):
            side=0
            if ar[i]>=1.0 and vr[i]>=1.5:
                if dr[i]==-1 and dr[i-1]==-1 and lo[i]<=ema[i] and cl[i]>ema[i]:
                    side=1
                elif dr[i]==1 and dr[i-1]==1 and hi[i]>=ema[i] and cl[i]<ema[i]:
                    side=-1
            if side:
                eligible_signals+=1
                ep=float(cl[i])
                # Place <= $10 in margin, regardless of wallet balance or profit.
                # Fixed margin target, never downsized simply because wallet shrank.
                contracts=math.floor((PER_TRADE_MARGIN_BUDGET_USD*SELECTED_LEVERAGE)
                                     / (ep*LOT_BTC)+1e-10)
                if contracts<1:
                    skip_lot+=1
                    continue
                qty=contracts*LOT_BTC
                notional=ep*qty
                margin=notional/SELECTED_LEVERAGE
                entry_fee=notional*0.0005*(1+0.18)
                if wallet+1e-9<margin+entry_fee:
                    skip_margin+=1
                    continue
                liq=(ep-margin/qty)/(1-MAINTENANCE_FRACTION) if side==1 else (
                     ep+margin/qty)/(1+MAINTENANCE_FRACTION)
                bankruptcy=ep-side*margin/qty
                slpts=max(0.5,round(2*atr[i]/0.5)*0.5)
                max_notional=max(max_notional,notional)
                min_notional=min(min_notional,notional)
                position=dict(
                    side=side,entry_idx=i,entry_price=ep,qty_btc=qty,
                    contracts=contracts,notional_usd=notional,margin_usd=margin,
                    initial_stop=ep-side*slpts,sl=ep-side*slpts,
                    best=ep,active=False,liq_price=liq,
                    bankruptcy_price=bankruptcy)
    z=pd.DataFrame(events)
    if len(z):
        z["exit_month_ist"]=pd.to_datetime(z.exit_utc,utc=True).dt.tz_convert(
            "Asia/Kolkata").dt.strftime("%Y-%m")
    net=z.change_usd if len(z) else pd.Series(dtype=float)
    wins=float(net[net>0].sum())
    losses=-float(net[net<0].sum())
    first=str(pd.Timestamp(times[start]))
    stats=dict(
        start_utc=first,last_bar_utc=str(pd.Timestamp(times[-1])),
        starting_portfolio_usd=STARTING_EQUITY_USD,
        ending_portfolio_usd=round(wallet,4),
        net_profit_usd=round(wallet-STARTING_EQUITY_USD,4),
        total_return_pct=round(100*(wallet/STARTING_EQUITY_USD-1),2),
        completed_trades=len(z),wins=int((net>0).sum()),
        losses=int((net<0).sum()),
        win_rate_pct=round(float((net>0).mean()*100),2) if len(z) else None,
        net_profit_factor=round(wins/losses,4) if losses>0 else None,
        assumed_liquidations=liquidations,
        scalper_eligible_trades=int(z.scalper_fee_waiver_applied.sum()) if len(z) else 0,
        max_closed_equity_drawdown_pct=round(max_dd_pct,2),
        eligible_entry_signals=eligible_signals,
        skipped_entries_insufficient_wallet=skip_margin,
        skipped_entries_less_than_one_contract=skip_lot,
        largest_position_notional_usd=round(max_notional,2),
        smallest_position_notional_usd=round(min_notional,2) if min_notional<float("inf") else None,
        open_position_at_end=position is not None,
        fees_entry_usd=round(float(z.entry_fee_usd.sum()),3) if len(z) else 0,
        fees_exit_usd=round(float(z.exit_fee_usd.sum()),3) if len(z) else 0,
        gst_usd=round(float((z.entry_gst_usd+z.exit_gst_usd+z.liquidation_penalty_gst_usd).sum()),3) if len(z) else 0,
        liq_penalties_usd=round(float(z.liquidation_penalty_usd.sum()),3) if len(z) else 0,
        liquidation_fill=liq_fill)
    if len(z):
        assert abs(float(net.sum())-(wallet-STARTING_EQUITY_USD))<0.00001
    return z,stats

def monthly(z,first,last):
    previous=STARTING_EQUITY_USD
    month_groups={m:g for m,g in z.groupby("exit_month_ist",sort=True)} if len(z) else {}
    rows=[]
    for period in pd.period_range(first,last,freq="M"):
        key=str(period)
        g=month_groups.get(key)
        if g is None:
            end=previous
            trades=0
        else:
            end=float(g.portfolio_after_usd.iloc[-1])
            trades=len(g)
        profit=end-previous
        rows.append({
            "month_ist":key,
            "opening_balance_usd":round(previous,4),
            "net_profit_usd":round(profit,4),
            "monthly_return_pct":round(profit/previous*100,2) if previous>0 else None,
            "closing_balance_usd":round(end,4),
            "trades":trades,
            "winning_trades":int((g.change_usd>0).sum()) if trades else 0,
            "losing_trades":int((g.change_usd<0).sum()) if trades else 0,
            "liquidations":int((g.exit_reason=="liquidation").sum()) if trades else 0,
            "fees_and_gst_usd":round(float((
                 g.entry_fee_usd+g.entry_gst_usd+g.exit_fee_usd+g.exit_gst_usd+
                 g.liquidation_penalty_usd+g.liquidation_penalty_gst_usd).sum()),4) if trades else 0,
            "complete_month":(key<="2026-10" and (first!="2026-08" or key>="2026-09"))
        })
        previous=end
    return pd.DataFrame(rows)

def main():
    bars,manifest,count=load()
    enriched=indicators(bars)
    output={"settings":PARAMS,"source":manifest["source"],
            "source_manifest_generated_utc":manifest["generated_at_utc"],
            "loaded_verified_one_minute_bars":count,"aggregated_15m_bars":len(bars),
            "disclaimer":"OHLC-based liquidation estimates only, not mark-price liquidation replay; synthetic assumed 30m Scalper offer throughout historical data; no slippage, funding, spread; exact contract/tick and fee tiers not independently audited."}
    for window,start in (("all_history",0),
                         ("recent_last_10000_15m",max(0,len(enriched)-10000))):
        for fill in ("threshold","bankruptcy"):
            key=f"{window}_{fill}"
            z,stats=replay(enriched,start,fill)
            z.to_csv(OUT/f"{key}_trades.csv.gz",index=False,compression="gzip")
            m=monthly(z,"2025-01" if start==0 else "2026-08","2026-11")
            m.to_csv(OUT/f"{key}_monthly.csv",index=False)
            output[key]=stats
            complete=m[m.complete_month]
            output[key]["completed_months"]=len(complete)
            output[key]["profitable_completed_months"]=int((complete.net_profit_usd>0).sum())
            output[key]["losing_completed_months"]=int((complete.net_profit_usd<0).sum())
            output[key]["flat_completed_months"]=int((complete.net_profit_usd==0).sum())
            print(f"\n---- {key} ----")
            print(json.dumps(stats,indent=2))
            print(m.to_string(index=False))
    (OUT/"summary.json").write_text(json.dumps(output,indent=2))
    print("SUCCESS: fixed $10-margin BTCUSD 100x portfolio replay",OUT)

if __name__=="__main__":
    main()
