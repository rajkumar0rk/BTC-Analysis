#!/usr/bin/env python3
"""ETHUSD 1h EMA20/Supertrend replay, BTC-equivalent 100/50 trailing, 100x isolated.

Reuse exactly the 1h OHLC signals, ATR14 x2 initial stop and ETH-scaled
100/50 trailing settings from backtest_eth_ema_st_1h_27min_20261120.py.
New assumptions are solely portfolio/margin sizing and modeled liquidation.
No 1-minute execution, no added indicators or filters.
"""
from pathlib import Path
import json, math
import numpy as np
import pandas as pd
import backtest_eth_ema_st_1h_27min_20261120 as base

OUTPUT=Path("analysis/eth_ema_st_1h_100x_20261120")
START_WALLET=100.0
MARGIN_BUDGET=10.0
LEVERAGE=100
CONTRACT_ETH=0.01
ASSUMED_MAINTENANCE=0.0025
LIQUIDATION_CHARGE_RATE=0.0005
FEE_RATE=0.0005
GST_RATE=0.18
SCALP_WINDOW_MIN=27
TICK=0.05

def liquidation_price(entry,side):
    initial_fraction=1.0/LEVERAGE
    # Approximation using constant 0.25% maintenance rate; NOT exchange mark.
    if side==1:
        return entry*(1-initial_fraction)/(1-ASSUMED_MAINTENANCE)
    return entry*(1+initial_fraction)/(1+ASSUMED_MAINTENANCE)

def stop_or_liquidation(a,z,p):
    """Process monotonic OHLC path: first adverse barrier wins.
    Favorable move updates the original ETH-scaled trail after reaching
    100/80000*entry, at trailing distance 50/80000*entry.
    """
    side=p["side"]
    liq=p["liquidation_price"]
    stop=p["initial_stop"]
    if p["trail"] is not None:
        stop=max(stop,p["trail"]) if side==1 else min(stop,p["trail"])

    # Opening gaps can jump past the liquidation threshold before the bot
    # can execute its exit; cap subsequent loss at isolated margin below.
    if (side==1 and a<=liq) or (side==-1 and a>=liq):
        return float(a),"liquidation"
    if (side==1 and a<=stop) or (side==-1 and a>=stop):
        return float(a),"stop_gap"

    if (z-a)*side>0:  # Favorable leg
        p["best"]=max(p["best"],z) if side==1 else min(p["best"],z)
        if (p["best"]-p["entry"])*side>=p["activation"]:
            new=p["best"]-side*p["distance"]
            p["trail"]=(max(new,p["trail"]) if side==1 else min(new,p["trail"])
                        ) if p["trail"] is not None else new
        return None,None

    if (z-a)*side>=0:
        return None,None

    # Adverse leg: stop and liquidation are competing price barriers.
    if side==1:
        first=max(stop,liq)
        if z<=first:
            return float(first),("liquidation" if liq>=stop else "initial_or_trailing_stop")
    else:
        first=min(stop,liq)
        if z>=first:
            return float(first),("liquidation" if liq<=stop else "initial_or_trailing_stop")
    return None,None

def run_replay(bars,direction,atr14,long,short):
    opens=bars.open.to_numpy(float)
    highs=bars.high.to_numpy(float)
    lows=bars.low.to_numpy(float)
    closes=bars.close.to_numpy(float)
    ts=np.array(bars.index.as_unit("ns").asi8,np.int64)
    assert len(ts)>5000 and np.all(np.diff(ts)==3600*1_000_000_000)
    wallet=START_WALLET
    peak=wallet
    max_dd=0.
    position=None
    events=[]
    all_signals=int(np.count_nonzero(long | short))
    signals_encountered=0
    skipped_margin=0
    skipped_lot=0
    liqs=0
    for i in range(1,len(bars)):
        closed_this_bar=False
        if position is not None:
            o=float(opens[i]);hi=float(highs[i]);lo=float(lows[i]);c=float(closes[i])
            path=(o,hi,lo,c) if abs(o-hi)<abs(o-lo) else (o,lo,hi,c)
            fill=None
            reason=None
            for a,z in zip(path[:-1],path[1:]):
                fill,reason=stop_or_liquidation(float(a),float(z),position)
                if fill is not None: break
            if fill is None:
                p=position
                flip=(p["side"]==1 and direction[i]==1 and direction[i-1]==-1
                      ) or (p["side"]==-1 and direction[i]==-1 and direction[i-1]==1)
                if flip:
                    fill=c
                    reason="supertrend_flip_close"
            if fill is not None:
                p=position
                qty=p["qty"]
                gross=(fill-p["entry"])*p["side"]*qty
                hold=(ts[i]-p["entry_ns"])/60_000_000_000
                eligible=(hold<=SCALP_WINDOW_MIN and reason!="liquidation")
                exit_fee=0.0 if eligible or reason=="liquidation" else fill*qty*FEE_RATE
                exit_gst=exit_fee*GST_RATE
                liquidation_fee=fill*qty*LIQUIDATION_CHARGE_RATE if reason=="liquidation" else 0.0
                liquidation_gst=liquidation_fee*GST_RATE
                if reason=="liquidation":
                    # Isolated margin caps loss after entry fees paid by wallet.
                    change_in_isolated=max(-p["margin"],gross-liquidation_fee-liquidation_gst)
                    liqs+=1
                else:
                    change_in_isolated=gross-exit_fee-exit_gst
                net=change_in_isolated-p["entry_fee"]-p["entry_gst"]
                before=wallet
                wallet=max(0.0,wallet+net)
                realized=wallet-before
                peak=max(peak,wallet)
                max_dd=max(max_dd,100*(1-wallet/peak)) if peak else 100
                events.append({
                    "entry_utc":pd.Timestamp(p["entry_ns"],unit="ns",tz="UTC").isoformat(),
                    "exit_utc":pd.Timestamp(ts[i],unit="ns",tz="UTC").isoformat(),
                    "side":"LONG" if p["side"]==1 else "SHORT",
                    "entry_price":p["entry"],"exit_price":fill,
                    "contracts":p["contracts"],"qty_eth":qty,
                    "notional_usd":p["notional"],"isolated_margin_usd":p["margin"],
                    "initial_stop":p["initial_stop"],
                    "liquidation_price_proxy":p["liquidation_price"],
                    "trailing_activation_eth_points":p["activation"],
                    "trailing_distance_eth_points":p["distance"],
                    "reason":reason,"held_minutes_conservative":hold,
                    "gross_usd":gross,"entry_fee_usd":p["entry_fee"],
                    "entry_gst_usd":p["entry_gst"],
                    "exit_fee_usd":exit_fee,"exit_gst_usd":exit_gst,
                    "liquidation_penalty_usd":liquidation_fee,
                    "liquidation_penalty_gst_usd":liquidation_gst,
                    "modeled_scalper_eligible":bool(eligible),
                    "wallet_before_usd":before,"wallet_after_usd":wallet,
                    "net_usd":realized})
                position=None
                closed_this_bar=True

        # Preserve screenshot's position-exclusive entry rule and lack of
        # same-hour re-entry. No daily loss or trade count cap imposed.
        if closed_this_bar or position is not None:
            continue
        if not (long[i] or short[i]):
            continue
        signals_encountered+=1
        side=1 if long[i] else -1
        entry=float(closes[i])
        if not np.isfinite(atr14[i]) or entry<=0: continue
        contracts=math.floor(MARGIN_BUDGET*LEVERAGE/(entry*CONTRACT_ETH)+1e-10)
        if contracts<=0:
            skipped_lot+=1
            continue
        qty=contracts*CONTRACT_ETH
        notional=entry*qty
        margin=notional/LEVERAGE
        entry_fee=notional*FEE_RATE
        entry_gst=entry_fee*GST_RATE
        if wallet+1e-9<margin+entry_fee+entry_gst:
            skipped_margin+=1
            continue
        dist=max(TICK,math.floor((2*atr14[i])/TICK+0.5)*TICK)
        # Preserve ETH percentage scaling from the user's existing test:
        # 100 BTC-equivalent points / 80000, and 50 / 80000.
        activation=max(TICK,base.round_ticks(entry*100/80000)*TICK)
        trail_distance=max(TICK,base.round_ticks(entry*50/80000)*TICK)
        position=dict(side=side,entry=entry,entry_ns=int(ts[i]),
                      contracts=contracts,qty=qty,notional=notional,margin=margin,
                      entry_fee=entry_fee,entry_gst=entry_gst,
                      initial_stop=entry-side*dist,
                      liquidation_price=liquidation_price(entry,side),
                      activation=activation,distance=trail_distance,
                      trail=None,best=entry)
    out=pd.DataFrame(events)
    if len(out):
        out["month_utc"]=pd.to_datetime(out.exit_utc,utc=True).dt.strftime("%Y-%m")
        assert np.isclose(out.net_usd.sum(),wallet-START_WALLET,atol=1e-7)
    stats=dict(
       starting_balance_usd=START_WALLET,ending_balance_usd=round(wallet,4),
       net_profit_usd=round(wallet-START_WALLET,4),
       total_return_on_initial_balance_pct=round((wallet/START_WALLET-1)*100,2),
       trades=len(out),
       win_rate_pct=round(float((out.net_usd>0).mean())*100,2) if len(out) else None,
       profit_factor=(round(float(out.loc[out.net_usd>0,"net_usd"].sum()/(-out.loc[out.net_usd<0,"net_usd"].sum())),4)
                      if len(out) and (out.net_usd<0).any() else None),
       modeled_liquidations=liqs,
       scalper_eligible_trades=int(out.modeled_scalper_eligible.sum()) if len(out) else 0,
       max_closed_equity_drawdown_pct=round(max_dd,2),
       signals_on_bars=all_signals,
       signals_reached_while_flat=signals_encountered,
       skipped_insufficient_wallet=skipped_margin,
       skipped_less_than_one_contract=skipped_lot,
       has_open_position_at_cutoff=position is not None,
       gross_realized_usd=round(float(out.gross_usd.sum()),4) if len(out) else 0,
       entry_fees_usd=round(float(out.entry_fee_usd.sum()),4) if len(out) else 0,
       exit_fees_usd=round(float(out.exit_fee_usd.sum()),4) if len(out) else 0,
       gst_usd=round(float((out.entry_gst_usd+out.exit_gst_usd+out.liquidation_penalty_gst_usd).sum()),4) if len(out) else 0,
       liquidation_penalties_usd=round(float(out.liquidation_penalty_usd.sum()),4) if len(out) else 0)
    return out,stats,position

def monthly_results(trades):
    first=START_WALLET
    months=[]
    grouped={m:g for m,g in trades.groupby("month_utc")} if len(trades) else {}
    for month in base.MONTHS:
        g=grouped.get(month)
        if g is None:
            ending=first
            monthly_net=0
            wins=losses=liq=trades_count=0
        else:
            ending=float(g.wallet_after_usd.iloc[-1])
            monthly_net=ending-first
            trades_count=len(g)
            wins=int((g.net_usd>0).sum())
            losses=int((g.net_usd<0).sum())
            liq=int((g.reason=="liquidation").sum())
        months.append(dict(month_utc=month,starting_balance_usd=round(first,4),
                           net_profit_usd=round(monthly_net,4),
                           monthly_return_pct=round(100*monthly_net/first,2) if first>0 else None,
                           ending_balance_usd=round(ending,4),
                           trades=trades_count,wins=wins,losses=losses,liquidations=liq))
        first=ending
    return pd.DataFrame(months)

def main():
    OUTPUT.mkdir(parents=True,exist_ok=True)
    bars,quality=base.source()
    direction,atr14,long,short=base.features(bars)
    trades,stats,open_position=run_replay(bars,direction,atr14,long,short)
    monthly=monthly_results(trades)
    assert len(monthly)==22
    assert abs(monthly.net_profit_usd.sum()-stats["net_profit_usd"])<0.003
    stats["profitable_months"]=int((monthly.net_profit_usd>0).sum())
    stats["losing_months"]=int((monthly.net_profit_usd<0).sum())
    stats["flat_months"]=int((monthly.net_profit_usd==0).sum())
    doc={
       "status":"completed_100x_isolated_ohlc_liquidation_proxy",
       "instrument":"ETHUSD",
       "data":quality,
       "settings":{
          "signal_timeframe":"1h","stop_monitoring_timeframe":"1h",
          "supertrend_atr_period":10,"supertrend_factor":3,
          "ema_length":20,"entry":"EMA20 pullback on confirmed Supertrend",
          "initial_stop":"2x ATR(14)",
          "trailing_activation_pct_of_entry":0.125,
          "trailing_distance_pct_of_entry":0.0625,
          "trailing_activation_scaled_from_BTC_points":100,
          "trailing_distance_scaled_from_BTC_points":50,
          "volume_volatility_master_filter":"Off",
          "starting_wallet_usd":START_WALLET,
          "fixed_isolated_margin_budget_usd":MARGIN_BUDGET,
          "leverage":LEVERAGE,
          "ETH_per_contract":CONTRACT_ETH,
          "estimated_maintenance_margin_rate":ASSUMED_MAINTENANCE,
          "liquidation_penalty_rate_assumed":LIQUIDATION_CHARGE_RATE,
          "entry_exit_taker_fee_rate":FEE_RATE,
          "gst_on_fees":GST_RATE,"scalper_offer_window_minutes":SCALP_WINDOW_MIN,
          "slippage_points":0.,"funding_pct":0.,
          "auto_add_margin":False,"auto_compound_margin":False,
          "assumed_27m_offer_active_entire_history":True},
       "results":stats,
       "open_position_at_cutoff":(dict(entry_price=open_position["entry"],
                                      side=open_position["side"],contracts=open_position["contracts"])
                                  if open_position else None),
       "warnings":[
          "1-hour historical OHLC broker-emulator approximation, not verified exchange execution or TradingView broker tester exactness.",
          "Liquidation based on trade-price OHLC and constant 0.25% assumed maintenance; actual Delta mark-price liquidation not reconstructed.",
          "Exchange margin details, lot increments, and historical scalper entitlement not independently verified.",
          "Conservative 1-hour close timing yields no 27-minute eligible trades; true minute-of-touch not available in 1-hour OHLC.",
          "Funding charges, actual spread, slippage, order latency excluded per screenshot assumptions.",
          "Unrealized P&L on a final unclosed position is not recognized in ending balance.",
          "100x leverage changes quantity and liquidation; unleveraged net is not multiplied by 100."]}
    trades.to_csv(OUTPUT/"trades.csv.gz",index=False,compression="gzip")
    monthly.to_csv(OUTPUT/"monthly.csv",index=False)
    (OUTPUT/"summary.json").write_text(json.dumps(doc,indent=2)+"\n")
    lines=["# ETHUSD EMA20/ST 1h, ETH-scaled 100/50, isolated 100x",
           "", "22 completed UTC months January 2025 through October 2026.",
           "Underlying reference: earlier 1h screenshot backtest, unchanged signals and trailing percentages.",
           "", "## Net portfolio results", "",json.dumps(stats,indent=2),
           "", "## Monthly results", "",monthly.to_markdown(index=False),
           "", "## Method caveats",""]
    lines.extend("- "+x for x in doc["warnings"])
    (OUTPUT/"RESEARCH_REPORT.md").write_text("\n".join(lines)+"\n")
    print("ETH_100X_RESULT "+json.dumps(stats,default=str),flush=True)
    print("ETH_100X_MONTHLY\n"+monthly.to_csv(index=False),flush=True)

if __name__=="__main__":
    main()
