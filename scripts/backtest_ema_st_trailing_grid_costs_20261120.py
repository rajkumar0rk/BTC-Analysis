#!/usr/bin/env python3
"""BTC/ETH EMA20+ST 1H entries, 1M execution, controlled 100/50 ... 300/100 grid.

Reuses exact previous 2026-11-20 research entry indicators, verified 1m
archive, tick rounding, ATR(14) initial stop, preliquidation/isolated 100x
proxy, prior minute OHLC execution engine, and 0.05% taker + 18% GST.

Compares fixed BTC trailing point grid; ETH keeps previous BTC-equivalent
trailing scaling using price/80000, not arbitrary literal BTC dollar points.

Two capital interpretations:
 - constrained: actual model $100 cash, $10 margin/trade at 100x
 - continuity: $1,000,000 VIRTUAL research cash ONLY to avoid excluding signals
   after synthetic wallet depletion; fixed $10 margin, unchanged qty
   NOT a realistic percent return on a $100 wallet.
Three fee/cost scenarios:
 - normal: taker both sides & GST, ZERO slippage & funding
 - stress: same + adverse 0.5 BTC / 0.05 ETH points EACH FILL +
           0.01% notional per crossed 8h funding boundary (always a COST)
 - offer_stress: same stress but hypothesized exit fee waiver for <=27min,
           not historically verified or necessarily active.
Missing funding settlements and order-book spreads are NOT silently treated
as verified. Funding stress is an assumption, not historical exchange debits.
"""
from __future__ import annotations
import json,math
from pathlib import Path
import numpy as np
import pandas as pd
import backtest_tv_ema_st_1h_27min_20261120 as btc
import backtest_eth_ema_st_1h_27min_20261120 as eth
import backtest_ema_st_1h_trail_1_0p1_20261120 as prior

OUT=Path("analysis/ema_st_1h_trailing_grid_costs_20261120")
ORIGINAL=Path("analysis/ema_st_1h_trailing_1_0p1_20261120/summary.json")
TRAIL_GRID=[(100,50),(150,50),(200,50),(200,100),(300,100)]
COST_MODES=["normal","stress","offer_stress"]
CAPITAL_MODES=["constrained_100usd","continuity_fixed_size"]
MINUTE_SLIPPAGE_POINTS={"BTC":0.5,"ETH":0.05}
FUNDING_RATE_COST_PER_EIGHT_HOURS=.0001

def points(asset,entry,activation,distance):
    if asset=="BTC":return float(activation),float(distance)
    tick=prior.TICK["ETH"]
    return (prior.round_tick(entry*activation/80000,tick),
            prior.round_tick(entry*distance/80000,tick))

def execute_case(asset,raw,bars,direction,atr,long,short,activation,distance,capital,cost_mode):
    baseline_trail=prior.trail;baseline_close=prior.close
    baseline_wallet=prior.START_CASH
    no_wallet_guard=(capital=="continuity_fixed_size")
    stressed=cost_mode!="normal"
    offer=cost_mode=="offer_stress"
    slip=MINUTE_SLIPPAGE_POINTS[asset] if stressed else 0.
    def choose_trail(asset_name,entry,variant):
        assert asset_name==asset
        return points(asset,entry,activation,distance)
    def close_with_cost(pos,fill,t,reason,wallet,offer_arg):
        realized,trade=baseline_close(pos,fill,t,reason,wallet,offer_arg)
        if not stressed:
            trade["funding_stress_usd"]=0.
            trade["execution_slippage_usd"]=0.
            trade["extra_fee_gst_from_slip_usd"]=0.
            return realized,trade
        # Entry and exit each receive worse hypothetical fill by slip. Do NOT
        # claim minute candle can identify true execution or bid/ask spread.
        slip_usd=2*slip*pos["qty"]
        # Small extra fee due to worse fill prices (worst-side bound).
        extra_fee=slip*pos["qty"]*prior.FEE*(1+prior.GST)*(
            1 if trade["assumed_exit_fee_waiver"] else 2)
        # Apply adversarial funding *cost* at every crossed 8h interval.
        # Directionless by design: sensitivity, not signed historical funding.
        snap=max(0,((int(t)-1)//28800)-(int(pos["entry_time"])//28800))
        funding=snap*pos["entry"]*pos["qty"]*FUNDING_RATE_COST_PER_EIGHT_HOURS
        penalty=slip_usd+extra_fee+funding
        trade["gross_usd"]-=slip_usd
        trade["fees_gst_usd"]+=extra_fee
        trade["execution_slippage_usd"]=slip_usd
        trade["extra_fee_gst_from_slip_usd"]=extra_fee
        trade["funding_stress_usd"]=funding
        trade["funding_boundaries_crossed"]=snap
        trade["net_usd"]-=penalty
        return realized-penalty,trade
    try:
        prior.trail=choose_trail
        prior.close=close_with_cost
        prior.START_CASH=1_000_000. if no_wallet_guard else 100.
        result,trades=prior.replay(asset,raw,bars,direction,atr,long,short,"old",offer)
    finally:
        prior.trail=baseline_trail
        prior.close=baseline_close
        prior.START_CASH=baseline_wallet
    if len(trades):
        trades=trades.copy()
        trades["month_utc"]=pd.to_datetime(trades["exit_epoch"],unit="s",utc=True).dt.strftime("%Y-%m")
        assert all(trades["trailing_activation"]>0)
        assert all(trades["trailing_distance"]>0)
        assert trades["net_usd"].notna().all()
    monthrows=[]
    for month in prior.MONTHS:
        group=trades[trades.month_utc==month] if len(trades) else trades
        profit=float(group.loc[group.net_usd>0,"net_usd"].sum()) if len(group) else 0.
        loss=-float(group.loc[group.net_usd<0,"net_usd"].sum()) if len(group) else 0.
        monthrows.append(dict(month=month,net_usd=round(float(group.net_usd.sum()),5),
            profit_factor=round(profit/loss,5) if loss>0 else None,
            trades=int(len(group)),wins=int((group.net_usd>0).sum()) if len(group) else 0,
            losses=int((group.net_usd<0).sum()) if len(group) else 0))
    p=float(trades.loc[trades.net_usd>0,"net_usd"].sum()) if len(trades) else 0.
    l=-float(trades.loc[trades.net_usd<0,"net_usd"].sum()) if len(trades) else 0.
    mtotal=float(sum(x["net_usd"] for x in monthrows))
    net=float(result["realized_net_usd"])
    # Empty funding/entry fees for any position still OPEN at cutoff are
    # excluded from closed-trade monthly P&L, as in prior experiment.
    if not result["has_open_trade_at_end"]:
        assert abs(mtotal-net)<0.003,(asset,cost_mode,capital,net,mtotal)
    stats=dict(asset=asset,activation_btc_equivalent_points=activation,
        distance_btc_equivalent_points=distance,cost_case=cost_mode,capital_case=capital,
        initial_cash_usd=result["balance_initial_usd"],
        ending_cash_usd=result["balance_final_usd"],
        account_cash_change_usd=net,
        closed_trades_net_usd=round(float(trades.net_usd.sum()),4) if len(trades) else 0.,
        completed_trades=result["completed_trades"],win_rate_pct=result["win_rate_pct"],
        profit_factor=result["profit_factor"],
        positive_months=int(sum(x["net_usd"]>0 for x in monthrows)),
        negative_months=int(sum(x["net_usd"]<0 for x in monthrows)),
        flat_months=int(sum(abs(x["net_usd"])<.000005 for x in monthrows)),
        max_closed_equity_drawdown_pct=result["max_closed_drawdown_pct"],
        total_base_trading_fees_gst_usd=round(result["total_fees_gst"]-
            float(trades.extra_fee_gst_from_slip_usd.sum()),4) if len(trades) else 0.,
        simulated_execution_slippage_usd=round(float(trades.execution_slippage_usd.sum()),4) if len(trades) else 0.,
        simulated_funding_stress_usd=round(float(trades.funding_stress_usd.sum()),4) if len(trades) else 0.,
        simulated_extra_fee_gst_from_slippage_usd=round(float(trades.extra_fee_gst_from_slip_usd.sum()),4) if len(trades) else 0.,
        assumed_scalper_eligible=int(result["assumed_scalper_eligible"]),
        rejected_insufficient_cash=int(result["rejected_due_to_wallet"]),
        modeled_liquidations=int(result["liquidations"]),
        open_position_at_cutoff=bool(result["has_open_trade_at_end"]),
        monthly=monthrows if False else monthrows)
    return stats,trades

def main():
    assert ORIGINAL.exists(),"Prior experiment absent: comparative baseline required"
    previous=json.loads(ORIGINAL.read_text())
    assert len(previous["scored_completed_months"])==22
    OUT.mkdir(parents=True,exist_ok=True)
    output={}
    for asset,mod in (("BTC",btc),("ETH",eth)):
        print("VERIFY_ARCHIVE_AND_COMPUTE_1H_INDICATORS",asset,flush=True)
        bars,source_quality=mod.source()
        raw,raw_source=prior.read_minutes(mod)
        direction,atr,long,short=mod.features(bars)
        assert len(raw)==len(bars)*60 and len(bars)==16056
        results={}
        for act,dist in TRAIL_GRID:
            key=f"{act}_{dist}"
            cases={}
            for capital in CAPITAL_MODES:
                for cm in COST_MODES:
                    print("REPLAY",asset,key,capital,cm,flush=True)
                    row,trades=execute_case(asset,raw,bars,direction,atr,long,short,
                                            act,dist,capital,cm)
                    cases[f"{capital}__{cm}"]=row
                    prefix=f"{asset.lower()}_{key}_{capital}_{cm}"
                    trades.to_csv(OUT/f"{prefix}_trades.csv.gz",index=False,compression="gzip")
                    pd.DataFrame(row["monthly"]).to_csv(OUT/f"{prefix}_monthly.csv",index=False)
                    print("RESULT",asset,key,capital,cm,
                          "NET",row["account_cash_change_usd"],
                          "PF",row["profit_factor"],"TRADES",row["completed_trades"],
                          "POS_MONTHS",row["positive_months"],flush=True)
            results[key]=cases
        assert abs(results["100_50"]["constrained_100usd__normal"]["account_cash_change_usd"]
              - previous["assets"][asset]["results"]["old_no_offer"]["realized_net_usd"])<0.0001,(
                    "100/50 baseline parity failed",asset)
        output[asset]=dict(source=source_quality,archive=raw_source,
                           results=results)
        del bars,raw,direction,atr,long,short
    doc=dict(status="completed",period_utc="2025-01-01 to 2026-10-31",
             complete_months=prior.MONTHS,
             strategy=dict(entry_signal="1H EMA20 pullback aligned with confirmed Supertrend (10,3)",
                 reversal_exit="confirmed 1H Supertrend flip, exit at next 1m open",
                 stop_monitoring="1-minute OHLC approximated path",
                 stop_loss="2x ATR(14), with synthetic preliquidation risk guard",
                 notional_sizing="fixed $10 target margin, 100x isolated research proxy, lot-quantized",
                 wallet_constrained="$100 starting cash, no additional deposit",
                 continuity_mode="virtual $1,000,000 research cash to prevent dropped signals; margin budget per trade stays $10; not a usable $100 account PnL",
                 trailing_grid=[dict(activation=a,distance=b) for a,b in TRAIL_GRID],
                 BTC_points="literal",
                 ETH_points="scaled as entry*BTC_points/80000 rounded to 0.05 ETH tick",
                 fee_taker_each_side_pct=0.05,GST_on_fees_pct=18,
                 stress_slippage_per_fill_points=MINUTE_SLIPPAGE_POINTS,
                 stress_funding_per_8h_pct=0.01,
                 Scalper_offer="27m waiver hypothetical, independently not verified, not claimed historically",
                 excluded="real spread, tick fills, exact historical funding payments, exchange mark liquidation, true Portfolio Margin"),
             assets=output,
             warnings=[
                "Real liquidation and funding payments require exchange mark-price and settlement records; historical FUNDING candles are OBSERVATIONS, not actual realized account funding debits.",
                "Stress assumes 0.01% unfavorable funding at each crossed 8-hour boundary; realized signed funding may differ.",
                "1M historical candles still do not reveal exact tick movement or limit-order fills.",
                "Continuity mode is a research diagnostic to compare all 22 months, NOT the return obtainable with $100 starting cash.",
                "No backtest settings or bots were modified on the VPS.",
                "Scalper-offer simulation is hypothetical; not necessarily available over historical date range.",
                "Slippage stress includes 0.5 BTC and 0.05 ETH points per fill, not actual spread or modeled depth.",
                "Fees and GST follow assumed taker 0.05% each side, GST 18%." ])
    (OUT/"summary.json").write_text(json.dumps(doc,indent=2)+"\n")
    table=["# BTC and ETH EMA20+Supertrend trailing grid: costs included",
           "1H signal, 1M OHLC stop monitoring; 22 months historical (2025-01 to 2026-10).",
           "100/50 was regression-checked against the previous script.",
           "",
           "| Asset | Activation/Distance | $100 wallet normal USD | $100 stressed USD | 22-month fixed-size stress USD | PF (fixed-size stress) | Positive months /22 |",
           "|---|---|---:|---:|---:|---:|---:|"]
    for asset,z in output.items():
        for key,cases in z["results"].items():
            c=cases["constrained_100usd__normal"]
            s=cases["constrained_100usd__stress"]
            q=cases["continuity_fixed_size__stress"]
            table.append(f'| {asset} | {key.replace("_","/")} | {c["account_cash_change_usd"]:+,.2f} | {s["account_cash_change_usd"]:+,.2f} | {q["closed_trades_net_usd"]:+,.2f} | {q["profit_factor"]} | {q["positive_months"]}/22 |')
    table+=["","## Caveats"]+[f"- {x}" for x in doc["warnings"]]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(table)+"\n")
    print("FINAL_GRID",json.dumps({asset:{
        key:{label:{k:x for k,x in row.items() if k!="monthly"}
                 for label,row in cases.items()} for key,cases in r["results"].items()}
         for asset,r in output.items()},sort_keys=True),flush=True)
if __name__=="__main__":main()
