#!/usr/bin/env python3
"""BTC/ETH unhedged futures-only PORTFOLIO-MARGIN stress scenario.

Same EMA20/Supertrend strategy, $100 account and <=$10 initial margin per
trade as historical BTC/ETH Isolated/Cross comparisons. Reproduce Delta's
published risk margin formula on a single futures position (29 price/IV shock
scenarios, floor 0.5% of futures notional, maintenance 80% of risk margin).
Underlying futures have no sensitivity to IV, so the 27 conventional price/IV
scenarios collapse to price shocks; 2 extreme moves are weighted by 1/3.

For BTC <=100k notional, published BTC price shock is 1%. Delta's public
document doesn't establish ETH's specific small-portfolio span; run ETH at
1%, 2%, 3% risk shocks (sensitivity, NOT verified ETH exchange parameter).
The dynamic risk margin at each mark is priced from notional. Liquidation is
simplified to forced close when equity falls to maintenance requirement.

Portfolio mode has NO exchange-provided individual position liquidation price.
This branch TESTS A SYNTHETIC $0.20 ETH PRICE BUFFER AHEAD OF THE MODELLED
ACCOUNT MAINTENANCE CROSSING (not an exchange-recognized stop threshold).
This is a hypothetical PM exit scenario only. Original
ATR14 2x stop + trailing + opposite-ST flip remain. Entire account equity
at risk. No real Delta portfolio engine/mark, stop-fill latency, spread,
slippage, funding, other positions, options or historical fee-offer verification.
Fee penalty if forced liquidated: 0.25% of notional plus GST assumption.
No claim of exchange-equivalent or production-ready results.
"""
from pathlib import Path
import json, math, sys
import numpy as np
import pandas as pd

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path.insert(0,str(ROOT/"vps-btc-ema-st"))


from replay_btc_ema_st_screenshot import load as load_btc, indicators
from replay_eth_ema_st_fixed10_100x import load_eth
from replay_btc_ema_st_100x import fee_net

OUT=ROOT/"analysis"/"eth_portfolio_preliq_fixed_0p20_20261120"
OUT.mkdir(parents=True,exist_ok=True)
STARTING_WALLET=100.0
FIXED_MARGIN=10.0
LEVERAGE=100
FUTURES_MARGIN_FLOOR=0.005
PM_LIQ_FEE=0.0025
PM_MAINT_RATIO=0.8
BTC_REFERENCE=80000.0
FIXED_ETH_ACCOUNT_LIQ_BUFFER_USD=0.20
ENTRY_FEE_RATE=0.0005
GST=0.18

def portfolio_risk_margin(mark_price, qty, shock_span):
    """Reprice 29 documented risk scenarios for ONE futures position.

    Perps have no IV exposure; shock scenarios repeat for 3 volatility shocks.
    Largest standard loss is one full +/- span, and extreme 3x price shocks
    count at 1/3 weight, hence also one span. Floor is .5% notional.
    """
    if not(mark_price>0 and qty>0 and 0<shock_span<=.10):
        raise ValueError("Invalid portfolio risk scenario")
    notional=mark_price*qty
    price_shocks=(-1.0,-.67,-.50,-.33,0.0,.33,.50,.67,1.0)
    iv_states=("down","unchanged","up")
    # A long future has -PnL under negative price shocks; a short future
    # faces the reverse. Since price shocks are symmetric, the worst-case
    # loss is identical for both sides. IV has no effect on plain futures.
    standard=[max(0.,-notional*shock_span*shock)
              for shock in price_shocks for iv in iv_states]   # 27
    extreme=[max(0.,-notional*shock_span*(3*shock)/3)
             for shock in (-1.0,1.0)]                         # 2
    assert len(standard)+len(extreme)==29
    risk_margin=max(standard+extreme)
    floor_margin=FUTURES_MARGIN_FLOOR*notional
    return max(risk_margin,floor_margin)

def portfolio_liquidation(entry, qty, side, cash_after_entry_fee, shock_span):
    """Approximate mark-price boundary under maintenance 80% of risk margin.

    Eligibility: cash + UPNL <= .8*max(risk margin, futures margin floor)
    for a single position only. The ACTUAL engine may reduce/hedge positions
    instead of a full liquidation and revalues dynamically.
    """
    if not(entry>0 and qty>0 and cash_after_entry_fee>0):
        raise ValueError("Invalid portfolio equity/size")
    maint_ratio=PM_MAINT_RATIO*max(shock_span,FUTURES_MARGIN_FLOOR)
    if side==1:
        threshold=(qty*entry-cash_after_entry_fee)/(qty*(1-maint_ratio))
        return max(0.,threshold)
    if side==-1:
        return (qty*entry+cash_after_entry_fee)/(qty*(1+maint_ratio))
    raise ValueError("Invalid side")

def synthetic_exit(o,h,l,c,p):
    """Preserve original nearer-extreme-first OHLC path, output trace to exit.

    Liquidation is only chosen ahead of a market stop when estimated barrier
    is hit first. Opening price crossing liq causes liquidation regardless of
    stop-market order. The stop itself is granted exact zero-latency fill
    whenever reached from the non-gapped side. This is an OPTIMISTIC model.
    """
    side=p["side"];entry=p["entry_price"];liq=p["liq_price"]
    stop=p["sl"];best=p["best"];active=p["active"]
    if (side==1 and liq>0 and o<=liq) or (side==-1 and o>=liq):
        return float(o),stop,best,active,"liquidation",[float(o)]
    seq=(float(o),float(h),float(l),float(c)) if h-o<o-l else (
        float(o),float(l),float(h),float(c))
    trace=[seq[0]]
    trail_activation=150.0 if p["asset"]=="BTC" else max(
        0.05,round((entry*150/BTC_REFERENCE)/.05)*.05)
    trail_distance=50.0 if p["asset"]=="BTC" else max(
        0.05,round((entry*50/BTC_REFERENCE)/.05)*.05)
    for a,b in zip(seq,seq[1:]):
        boundary=max(stop,liq) if side==1 else min(stop,liq)
        if (side==1 and a<=boundary) or (side==-1 and a>=boundary):
            isliq=(liq>=stop if side==1 else liq<=stop)
            trace.append(float(a))
            return float(a),stop,best,active,("liquidation" if isliq
                          else "stop_gap"),trace
        favorable=(b>a) if side==1 else (b<a)
        if favorable:
            target=entry+side*trail_activation
            if not active and (b>=target if side==1 else b<=target):
                active=True;best=target
            if active:
                best=max(best,b) if side==1 else min(best,b)
                candidate=best-side*trail_distance
                stop=max(stop,candidate) if side==1 else min(stop,candidate)
            trace.append(float(b))
        else:
            boundary=max(stop,liq) if side==1 else min(stop,liq)
            hit=(b<=boundary if side==1 else b>=boundary)
            if hit:
                isliq=(liq>=stop if side==1 else liq<=stop)
                trace.append(float(boundary))
                return float(boundary),stop,best,active,(
                    "liquidation" if isliq else
                    "trailing" if active else "initial_or_preliq_stop"),trace
            trace.append(float(b))
    return None,stop,best,active,None,trace

def replay(df,asset,start_index,shock_span=0.01,offer=True,liqfill="threshold"):
    assert 0<shock_span<=.10
    f=df.reset_index()
    op=f.open.to_numpy(dtype=float);hi=f.high.to_numpy(dtype=float)
    lo=f.low.to_numpy(dtype=float);cl=f.close.to_numpy(dtype=float)
    ema=f.ema.to_numpy(dtype=float);atr=f.atr14.to_numpy(dtype=float)
    direction=f.dir.to_numpy();ar=f.atr_ratio.to_numpy(dtype=float)
    vr=f.volume_ratio.to_numpy(dtype=float);times=f.dt.to_numpy()
    lot=.001 if asset=="BTC" else .01
    tick=.5 if asset=="BTC" else .05
    wallet=STARTING_WALLET
    closed_peak=wallet
    closed_dd=0.
    mtm_peak=wallet
    mtm_dd=0.
    mtm_dd_usd=0.
    worst_trade_floating_dd=0.
    liquidations=0
    stop_exits=0
    skipped_insufficient=0
    skipped_one_lot=0
    eligible_entries=0
    effective_preliq_entries=0
    modeled_liq_boundary_available_entries=0
    trades=[]
    position=None
    max_initial_requirement=0.0

    def mark_equity(balance):
        nonlocal mtm_peak,mtm_dd,mtm_dd_usd,worst_trade_floating_dd
        # Equity uses current synthetic traded bar price before exit fee. No mark feed.
        mtm_peak=max(mtm_peak,balance)
        dd=max(0.,mtm_peak-balance)
        mtm_dd_usd=max(mtm_dd_usd,dd)
        mtm_dd=max(mtm_dd,100*dd/mtm_peak if mtm_peak else 100.)
        return balance

    for i in range(max(start_index,36),len(f)):
        if position is not None:
            p=position
            xp,p["sl"],p["best"],p["active"],reason,path=synthetic_exit(
                op[i],hi[i],lo[i],cl[i],p)
            # Before exit, sample the assumed intrabar sequence, stopping exactly
            # at the simulated market fill, not the extreme AFTER the exit.
            for price in path:
                floating=p["wallet_before"]-p["entry_fee_paid"]+(
                    price-p["entry_price"])*p["qty"]*p["side"]
                mark_equity(max(0.,floating))
                worst_trade_floating_dd=max(worst_trade_floating_dd,
                    100*max(0,p["wallet_before"]-floating)/p["wallet_before"])
            if xp is None and (
                (p["side"]==1 and direction[i]==1 and direction[i-1]==-1) or
                (p["side"]==-1 and direction[i]==-1 and direction[i-1]==1)
            ):
                xp=float(cl[i]);reason="supertrend_flip"
            if xp is not None:
                if reason=="liquidation" and liqfill=="bankruptcy":
                    xp=p["bankruptcy_price"]
                hold=(i-p["entry_index"])*15
                fee=fee_net(p["qty"],p["entry_price"],xp,p["side"],
                            hold if offer else 1_000_000,reason,liqfill)
                if reason=="liquidation":
                    # Portfolio margin forced liquidation costs 0.25% of
                    # current notional; original fee_net uses isolated fee.
                    fee["liquidation_fee_usd"]=p["qty"]*xp*PM_LIQ_FEE
                    fee["liquidation_gst_usd"]=fee["liquidation_fee_usd"]*GST
                prev=wallet
                if reason=="liquidation":
                    liquidations+=1
                    # PORTFOLIO: entire account balance can be consumed, not
                    # just the $10 order's initial risk margin.
                    cross_collateral=p["wallet_before"]-p["entry_fee_paid"]
                    gross_after_liq=fee["gross_usd"]-fee["liquidation_fee_usd"]-fee["liquidation_gst_usd"]
                    net=max(-cross_collateral,gross_after_liq)-p["entry_fee_paid"]
                else:
                    net=(fee["gross_usd"]-fee["entry_fee_usd"]-fee["entry_gst_usd"]
                         -fee["exit_fee_usd"]-fee["exit_gst_usd"])
                wallet=max(0.,wallet+net)
                change=wallet-prev
                closed_peak=max(closed_peak,wallet)
                closed_dd=max(closed_dd,100*(1-wallet/closed_peak))
                mark_equity(wallet)
                if "stop" in reason or reason=="trailing":stop_exits+=1
                trades.append(dict(
                    asset=asset,entry_utc=str(pd.Timestamp(times[p["entry_index"]])+pd.Timedelta(minutes=15)),
                    exit_utc=str(pd.Timestamp(times[i])+pd.Timedelta(minutes=15)),
                    side="long" if p["side"]==1 else "short",
                    entry_price=p["entry_price"],exit_price=float(xp),
                    contracts=p["contracts"],qty_underlying=p["qty"],
                    position_notional_usd=p["qty"]*p["entry_price"],
                    initial_margin_requirement_usd=p["initial_margin"],
                    cross_wallet_before_usd=prev,
                    cross_liquidation_estimated_price=p["liq_price"],
                    preliq_emergency_stop_price=p["preliq_price"],
                    stop_at_entry=p["initial_stop"],
                    reason=reason,hold_minutes=hold,
                    gross_pnl_usd=fee["gross_usd"],
                    entry_fee_usd=fee["entry_fee_usd"],entry_gst_usd=fee["entry_gst_usd"],
                    exit_fee_usd=fee["exit_fee_usd"],exit_gst_usd=fee["exit_gst_usd"],
                    liquidation_penalty_usd=fee["liquidation_fee_usd"],
                    liquidation_gst_usd=fee["liquidation_gst_usd"],
                    scalper_offer_assumed=fee["eligible_scalper"] if offer else False,
                    net_pnl_usd=change,wallet_after_usd=wallet))
                position=None
        if position is None and (np.isfinite(ema[i]) and np.isfinite(atr[i]) and
                                 np.isfinite(ar[i]) and np.isfinite(vr[i])):
            side=0
            if ar[i]>=1 and vr[i]>=1.5:
                if direction[i]==direction[i-1]==-1 and lo[i]<=ema[i] and cl[i]>ema[i]:
                    side=1
                elif direction[i]==direction[i-1]==1 and hi[i]>=ema[i] and cl[i]<ema[i]:
                    side=-1
            if side:
                eligible_entries+=1
                entry=float(cl[i])
                # Budget <=$10 of portfolio INITIAL risk margin, not
                # fixed 100x leverage. Wider price stress reduces lots.
                allowed_notional=min(FIXED_MARGIN*LEVERAGE,
                                     FIXED_MARGIN/max(shock_span,FUTURES_MARGIN_FLOOR))
                contracts=math.floor(allowed_notional/(entry*lot)+1e-10)
                if contracts<1:
                    skipped_one_lot+=1;continue
                qty=contracts*lot
                notional=entry*qty
                margin=portfolio_risk_margin(entry,qty,shock_span)
                max_initial_requirement=max(max_initial_requirement,margin)
                entry_fee=notional*ENTRY_FEE_RATE*(1+GST)
                if wallet+1e-9<margin+entry_fee:
                    skipped_insufficient+=1;continue
                cross_cash=wallet-entry_fee
                liq=portfolio_liquidation(entry,qty,side,cross_cash,shock_span)
                bankruptcy=entry-side*cross_cash/qty
                pts=max(tick,round(2*atr[i]/tick)*tick)
                # Experiment: place stop USD 0.20 inside estimated PM account
                # maintenance crossing; this is NOT an exchange-supplied
                # per-position liquidation price and is not executable PM parity.
                original_atr_stop=entry-side*pts
                liq_pre_stop=None
                active_stop=original_atr_stop
                if asset=="ETH" and liq>0:
                    modeled_liq_boundary_available_entries+=1
                    if side==1:
                        candidate=math.ceil(round((liq+FIXED_ETH_ACCOUNT_LIQ_BUFFER_USD)/tick,10))*tick
                        if candidate<entry:
                            liq_pre_stop=candidate
                            active_stop=max(active_stop,candidate)
                    else:
                        candidate=math.floor(round((liq-FIXED_ETH_ACCOUNT_LIQ_BUFFER_USD)/tick,10))*tick
                        if candidate>entry:
                            liq_pre_stop=candidate
                            active_stop=min(active_stop,candidate)
                if liq_pre_stop is not None and abs(active_stop-original_atr_stop)>tick*0.1:
                    effective_preliq_entries+=1
                position=dict(asset=asset,side=side,entry_index=i,
                    entry_price=entry,qty=qty,contracts=contracts,
                    initial_margin=margin,entry_fee_paid=entry_fee,
                    wallet_before=wallet,liq_price=liq,
                    bankruptcy_price=bankruptcy,
                    preliq_price=liq_pre_stop,
                    initial_stop=active_stop,sl=active_stop,
                    best=entry,active=False)
                mark_equity(wallet-entry_fee)
    z=pd.DataFrame(trades)
    if len(z):
        z["exit_month_ist"]=pd.to_datetime(z.exit_utc,utc=True).dt.tz_convert(
            "Asia/Kolkata").dt.strftime("%Y-%m")
    change=z.net_pnl_usd if len(z) else pd.Series(dtype=float)
    wins=float(change[change>0].sum())
    losses=-float(change[change<0].sum())
    stats=dict(
        asset=asset,margin_mode="PORTFOLIO_MARGIN_FUTURES_ONLY_STRESS_MODEL",
        price_shock_span_fraction=shock_span,
        margin_floor_fraction=FUTURES_MARGIN_FLOOR,
        maintenance_fraction_of_risk_margin=PM_MAINT_RATIO,
        largest_initial_margin_usd=round(max_initial_requirement,3),
        start_utc=str(pd.Timestamp(times[start_index])),
        last_bar_utc=str(pd.Timestamp(times[-1])),
        initial_wallet_usd=STARTING_WALLET,
        ending_wallet_usd=round(wallet,4),
        net_profit_usd=round(wallet-STARTING_WALLET,4),
        total_return_pct=round(100*(wallet/STARTING_WALLET-1),2),
        closed_trades=len(z),
        winners=int((change>0).sum()),
        losers=int((change<0).sum()),
        win_rate_pct=round(float((change>0).mean()*100),2) if len(z) else None,
        net_profit_factor=round(wins/losses,4) if losses>0 else None,
        simulated_liquidations=liquidations,
        stop_exits=stop_exits,
        max_closed_equity_drawdown_pct=round(closed_dd,3),
        max_intrabar_equity_drawdown_pct=round(mtm_dd,3),
        max_intrabar_drawdown_usd=round(mtm_dd_usd,3),
        max_single_trade_floating_loss_pct_starting_wallet=round(
            worst_trade_floating_dd,3),
        eligible_signals_when_flat=eligible_entries,
        skipped_insufficient_wallet=skipped_insufficient,
        skipped_one_lot=skipped_one_lot,
        open_trade_at_end=position is not None,
        entry_fees_usd=round(float(z.entry_fee_usd.sum()),4) if len(z) else 0,
        exit_fees_usd=round(float(z.exit_fee_usd.sum()),4) if len(z) else 0,
        gst_usd=round(float((z.entry_gst_usd+z.exit_gst_usd+
                            z.liquidation_gst_usd).sum()),4) if len(z) else 0,
        liquidation_penalties_usd=round(float(z.liquidation_penalty_usd.sum()),4) if len(z) else 0,
        per_position_preliq_unavailable=True,
        fixed_eth_buffer_usd=FIXED_ETH_ACCOUNT_LIQ_BUFFER_USD if asset=="ETH" else None,
        modeled_liq_boundary_available_entries=modeled_liq_boundary_available_entries,
        effective_preliq_entries=effective_preliq_entries,
        portfolio_forced_liquidation_fee_rate=PM_LIQ_FEE,
        historical_scalper_offer_assumed_full_period=offer,
        liquidation_fill_method=liqfill,
        historical_mark_price_available=False,
        slippage_and_spread_assumed_usd=0,
        funding_assumed_usd=0)
    if len(z):
        assert abs(float(change.sum())-(wallet-STARTING_WALLET))<1e-5
        assert float(z.initial_margin_requirement_usd.max())<=FIXED_MARGIN+1e-5
        assert float(z.position_notional_usd.max())<=FIXED_MARGIN*LEVERAGE+1e-5
    return z,stats

def monthly(z,start_ym,end_ym):
    rows=[]
    previous=STARTING_WALLET
    grouped={k:g for k,g in z.groupby("exit_month_ist",sort=True)} if len(z) else {}
    for period in pd.period_range(start_ym,end_ym,freq="M"):
        key=str(period)
        g=grouped.get(key)
        month_peak=previous
        month_dd=0.0
        if g is None:current=previous
        else:
            current=previous
            for _,t in g.iterrows():
                current=float(t.wallet_after_usd)
                month_peak=max(month_peak,current)
                month_dd=max(month_dd,100*(1-current/month_peak))
        n=0 if g is None else len(g)
        rows.append(dict(
            month_ist=key,opening_wallet_usd=round(previous,4),
            net_pnl_usd=round(current-previous,4),
            monthly_return_pct=round(100*(current-previous)/previous,2) if previous>0 else None,
            ending_wallet_usd=round(current,4),
            monthly_max_closed_drawdown_pct=round(month_dd,2),
            closed_trades=n,
            winning_trades=0 if g is None else int((g.net_pnl_usd>0).sum()),
            losing_trades=0 if g is None else int((g.net_pnl_usd<0).sum()),
            liquidations=0 if g is None else int((g.reason=="liquidation").sum()),
            complete_month=key<="2026-10" and (start_ym=="2025-01" or key>"2026-08")
        ))
        previous=current
    return pd.DataFrame(rows)

def main():
    scenarios={
      "shock1pct_offer":(0.01,True,"threshold"),
      "shock1pct_nooffer":(0.01,False,"threshold"),
      "shock2pct_offer":(0.02,True,"threshold"),
      "shock3pct_offer":(0.03,True,"threshold"),
      "shock1pct_bankruptcy":(0.01,True,"bankruptcy"),
    }
    report={"settings":{
        "starting_wallet_usd":STARTING_WALLET,
        "max_per_trade_portfolio_initial_margin_usd":FIXED_MARGIN,
        "max_trade_notional_usd":FIXED_MARGIN*LEVERAGE,
        "notional_is_sizing_target_not_exchange_100x_setting":True,
        "full_account_collateral_used":True,
        "one_open_position_only":True,
        "other_positions_or_options":False,
        "price_span_BTC_small_portfolio_docs":0.01,
        "ETH_price_span_not_verified_runs_1_2_3_percent_sensitivity":True,
        "portfolio_risk_margin":"29 scenario shock max vs 0.5% future notional floor",
        "portfolio_maintenance_requirement":"80% of scenario risk margin minus unrealized cashflow",
        "portfolio_position_liquidation_price":None,
        "uses_preliq_one_point_stop":False,
        "fixed_eth_buffer_usd":FIXED_ETH_ACCOUNT_LIQ_BUFFER_USD,
        "experiment":"synthetic portfolio account maintenance threshold plus fixed ETH $0.20 buffer, no verified exchange position liquidation price",
        "forced_liquidation_fee_fraction":PM_LIQ_FEE,
        "scalper_offer_historical_enrollment_proven":False,
        "historical_mark_price_available":False,
        "funding_spread_slippage_included":False,
        "caution":"This models single-directional futures-only PM. Actual Delta portfolio liquidation reprices full positions/orders and may hedge/reduce rather than fully close. Do not infer actual eligibility/margin from static guide."
    }}
    for asset,load in [("ETH",load_eth)]:
        bars,manifest,n1=load()
        rich=indicators(bars)
        report[asset]={"source":manifest.get("source"),"bars_1m":n1,
                       "bars_15m":len(rich),
                       "first_bar_utc":str(rich.index[0]),
                       "last_bar_utc":str(rich.index[-1])}
        for window,start in (("history",0),("recent10k",max(0,len(rich)-10000))):
            for label,(shock_span,offer,liqfill) in scenarios.items():
                tag=f"{asset.lower()}_{window}_{label}"
                trades,stat=replay(rich,asset,start,shock_span,offer,liqfill)
                trades.to_csv(OUT/f"{tag}_trades.csv.gz",index=False,compression="gzip")
                m=monthly(trades,"2025-01" if start==0 else "2026-08","2026-11")
                m.to_csv(OUT/f"{tag}_monthly.csv",index=False)
                complete=m[m.complete_month]
                stat.update(
                   profitable_completed_months=int((complete.net_pnl_usd>0).sum()),
                   losing_completed_months=int((complete.net_pnl_usd<0).sum()),
                   flat_completed_months=int((complete.net_pnl_usd==0).sum()),
                   completed_months=len(complete),
                   worst_monthly_return_pct=float(m.monthly_return_pct.dropna().min()) if m.monthly_return_pct.notna().any() else None,
                   worst_monthly_pnl_usd=float(m.net_pnl_usd.min()))
                report[asset][window+"_"+label]=stat
                print("RESULT",asset,window,label,json.dumps(stat,sort_keys=True),flush=True)
                if window=="history" and label=="shock1pct_offer":
                    print("MONTHS",asset,m.to_csv(index=False),flush=True)
    (OUT/"summary.json").write_text(json.dumps(report,indent=2))
    print("ETH_PORTFOLIO_FIXED_020_SYNTHETIC_REPLAY_SUCCESS",OUT,flush=True)

if __name__=="__main__":main()
