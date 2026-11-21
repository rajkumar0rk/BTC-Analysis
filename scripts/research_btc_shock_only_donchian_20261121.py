#!/usr/bin/env python3
"""Research: run BTCUSD 1H Donchian only when the PREVIOUS completed 1H regime is SHOCK.

Do not choose or tune parameters here. Reuse frozen classifier and backtest engine,
rerun all eligible trades (not a post-hoc subset of unfiltered trade fills).
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import research_btc_regime_attribution_20261121 as base

OUT = Path("analysis/btc_shock_only_donchian_20261121")
OUT.mkdir(parents=True, exist_ok=True)
MONTHS = [str(x) for x in pd.period_range("2025-01", "2026-10", freq="M")]
EXPECTED_BASELINE_TRADES = 573
EXPECTED_BASELINE_RETURN = -13.23

def performance(tr):
    if tr.empty:
        return {
            "trades":0, "wins":0, "losses":0, "win_rate_pct":0,
            "net_return_pct":0,"net_pnl_usd":0, "profit_factor":None,
            "max_trade_close_drawdown_pct":0
        }
    wins = tr.pnl_usd > 0
    losses = tr.pnl_usd < 0
    gain = float(tr.loc[wins, "pnl_usd"].sum())
    loss = -float(tr.loc[losses, "pnl_usd"].sum())
    final = float(tr.equity_usd.iloc[-1])
    eq = np.r_[base.INITIAL, tr.equity_usd.to_numpy(float)]
    dd = (1 - eq / np.maximum.accumulate(eq))*100
    return {
        "trades":len(tr),
        "wins":int(wins.sum()),
        "losses":int(losses.sum()),
        "win_rate_pct":round(float(100*wins.mean()),3),
        "profit_factor":round(float(gain/loss),4) if loss>0 else None,
        "net_pnl_usd":round(float(tr.pnl_usd.sum()),2),
        "net_return_pct":round(float(100*(final/base.INITIAL-1)),4),
        "ending_account_usd":round(final,2),
        "max_trade_close_drawdown_pct":round(float(dd.max()),3),
        "avg_net_R":round(float(tr.net_R.mean()),4),
        "total_fee_gst_usd":round(float(tr.fee_gst_usd.sum()),2),
        "total_slippage_usd":round(float(tr.slippage_usd.sum()),2),
        "gross_before_costs_usd":round(float(
            tr.pnl_usd.sum()+tr.fee_gst_usd.sum()+tr.slippage_usd.sum()),2),
    }

def monthly(tr):
    rows=[]
    for month in MONTHS:
        g=tr.loc[tr.month_ist==month]
        mo_return = float((np.prod(1 + g.return_pct.to_numpy(float)/100)-1)*100)
        rows.append({
            "month_ist":month,
            "trades":len(g),
            "wins":int((g.pnl_usd>0).sum()),
            "losses":int((g.pnl_usd<0).sum()),
            "net_return_pct":round(mo_return,5),
            "net_pnl_usd":round(float(g.pnl_usd.sum()),2),
            "gross_before_costs_usd":round(float(
                g.pnl_usd.sum()+g.fee_gst_usd.sum()+g.slippage_usd.sum()),2),
            "fees_gst_usd":round(float(g.fee_gst_usd.sum()),2),
            "slippage_usd":round(float(g.slippage_usd.sum()),2),
            "status":"Profit" if mo_return>1e-8 else "Loss" if mo_return < -1e-8 else "No trades",
        })
    return pd.DataFrame(rows)

def years(month):
    results=[]
    for year,g in month.groupby(month.month_ist.str[:4]):
        compounded=(np.prod(1+g.net_return_pct.to_numpy(float)/100)-1)*100
        results.append({
            "year":year,"months":len(g),"trades":int(g.trades.sum()),
            "profitable_months":int((g.net_return_pct>0).sum()),
            "losing_months":int((g.net_return_pct<0).sum()),
            "idle_months":int((g.net_return_pct==0).sum()),
            "year_net_return_pct":round(float(compounded),4),
        })
    return pd.DataFrame(results)

def make_report(quality, shock, baseline, month, year, filtered_signals, all_signals):
    text=[
        "# Shock-only 1H Donchian breakout — fully replayed BTCUSD account",
        "",
        "## What is actually tested",
        "Only enter on a **closed 1H** break of the previous 24 completed hourly bars when the fully closed signal hour is classified as **shock** by the frozen 2026-11-21 market-regime engine. Entry at the very next native 1M open. No intrabar order inference from the hourly candle.",
        "",
        "Shock rule: (1H true range > 2.2 x ATR14) OR (ATR14 / prior-72H median ATR14 >= 1.8). It uses information available at the completed signal hour.",
        "",
        "Stop = 1.8 x ATR14, target = 3R, maximum hold 36 hours; one position at a time; IST month-end flatten. Replays are newly generated for the filtered account; they do NOT sum the baseline's old shock-tagged trades.",
        "",
        "Hypothetical independent initial equity $10,000; risk 0.5% of changing equity per stop and 3x notional cap; fees 0.05% taker each side + GST 18%; 5 BTC price points assumed adverse slip each side. Stop/target same 1M candle => stop first, possible stop gap filled at worse price. Funding, real spread, impact, liquidation and margin requirements are not modeled.",
        "",
        "## Data and run quality", "~~~json",json.dumps(quality,indent=2),"~~~","",
        "## Unfiltered vs independently executed shock-only account",
        pd.DataFrame([dict(model="Unfiltered 1H Donchian",**baseline),
                      dict(model="Shock-only 1H Donchian",**shock)]).to_markdown(index=False),
        "",
        "## Calendar year returns (2026 through Oct only)",
        year.to_markdown(index=False),"",
        "## Every complete IST month's actual account net return, no-trade months included",
        month.to_markdown(index=False),"",
        "## Read before interpreting",
        "- This gate was chosen *after inspecting the same full history*, where the baseline's shock-tagged subset had PF > 1. Ex-post selection bias applies. 2026 has already been researched; this is not a pristine untouched holdout.",
        "- Unlike attribution on the old baseline ledger, the shock-only account has its own entries, position concurrency, fees, sizing, cash and equity progression.",
        "- No claim of real-trading profitability until forward test and realistic historical spreads, actual funding, liquidation and fills are incorporated.",
        "- Equity drawdown is sampled on trade closes; intratrade max drawdown may be much worse.",
        "- The returns are for a hypothetical equity account, NOT BTC price-point movement and NOT a margin/contract feasibility estimate.",
        "- Zero-trade months count as **not profitable**. November 2026 excluded because incomplete.",
        "- \`shock\` is a price volatility definition, not proof of liquidations.",
        "",
        "## Execution audit",
        f"- Original eligible all-regime Donchian signal hours: {all_signals}",
        f"- Eligible shock Donchian signal hours: {filtered_signals}",
        f"- Actual executed shock-only trades, with independent concurrency: {shock['trades']}",
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(text)+"\n")

def main():
    one,manifest=base.load()
    h=base.features(one)
    raw=base.prepare_signals(h)["donchian_breakout"]
    mask=h.regime.eq("shock").to_numpy()
    shock_sig=np.where(mask,raw,0).astype(int)
    filtered_signals=int(np.count_nonzero(shock_sig))
    raw_signals=int(np.count_nonzero(raw))
    if filtered_signals==0:
        raise RuntimeError("No shock breakouts — invalid results")
    if np.any(shock_sig[~mask]!=0):
        raise RuntimeError("Shock filter permitted a non-shock bar")

    # Replay FULL frozen strategy for identical-engine comparison.
    original=base.run(one,h,{"donchian_breakout":raw})
    if len(original)!=EXPECTED_BASELINE_TRADES:
        raise RuntimeError("Baseline trade count changed; investigate parity before reporting")
    baseline=performance(original)
    if abs(baseline["net_return_pct"]-EXPECTED_BASELINE_RETURN)>0.02:
        raise RuntimeError("Baseline net return unexpectedly changed; audit frozen parity")

    # Entirely fresh live-like entry sequence and PnL; do NOT subset the original ledger.
    filtered=base.run(one,h,{"donchian_breakout":shock_sig})
    if filtered.empty or not filtered.regime.eq("shock").all():
        raise RuntimeError("Filter replay failed or contains non-shock entries")
    summary=performance(filtered)
    monthly_results=monthly(filtered)
    yearly_results=years(monthly_results)
    if abs(np.prod(1+monthly_results.net_return_pct.to_numpy()/100) -
           filtered.equity_usd.iloc[-1]/base.INITIAL)>0.00001:
        raise RuntimeError("Monthly compounded returns do not reconcile with final equity")
    if abs(float(filtered.pnl_usd.sum())-
           (float(filtered.equity_usd.iloc[-1])-base.INITIAL))>0.01:
        raise RuntimeError("PnL and final account equity do not reconcile")

    filtered.to_csv(OUT/"shock_only_trade_ledger.csv",index=False)
    original.to_csv(OUT/"unfiltered_comparison_trade_ledger.csv",index=False)
    monthly_results.to_csv(OUT/"monthly_account_returns.csv",index=False)
    yearly_results.to_csv(OUT/"yearly_account_returns.csv",index=False)
    equity=filtered[["exit_utc","equity_usd","pnl_usd"]].copy()
    equity.to_csv(OUT/"trade_close_equity_curve.csv",index=False)
    (OUT/"overall_summary.json").write_text(json.dumps(
        {"shock_only":summary,"unfiltered":baseline},indent=2)+"\n")
    qual={
        "data": "Delta India BTCUSD native 1M, SHA verified, no missing minutes",
        "first_utc":str(one.index[0]),"last_utc":str(one.index[-1]),
        "minute_candles":len(one),"source_partitions":len(manifest["partitions"]),
        "complete_ist_months":MONTHS,
        "shock_candidate_signals":filtered_signals,
        "all_regime_candidate_signals":raw_signals,
        "shock_only_executed_trades":len(filtered),
        "unfiltered_baseline_executed_trades":len(original),
        "execution": "next 1M open after completely closed 1H signal; stop-first 1M; IST monthly flatten",
        "baseline_parity_verified":True,
        "selection_bias_warning": "shock gate selected after seeing original 2025-2026 subgroup result",
        "blind_out_of_sample":False,
    }
    (OUT/"quality.json").write_text(json.dumps(qual,indent=2)+"\n")
    make_report(qual,summary,baseline,monthly_results,yearly_results,
                filtered_signals,raw_signals)
    print("SHOCK_ONLY_SUMMARY",json.dumps(summary))
    print("UNFILTERED_SUMMARY",json.dumps(baseline))
    print("YEARLY")
    print(yearly_results.to_string(index=False))
    print("MONTHLY")
    print(monthly_results.to_string(index=False))
    print("COMPLETE")

if __name__=="__main__":
    main()
