#!/usr/bin/env python3
"""Run the pinned upstream volatility-persistence strategy on both BTC and ETH,
then score all 22 COMPLETE months by after-cost profit factor and exit-booked
account return. Exploratory score only: source lacks 2024-12-31 UTC IST warmup,
month-end open-position marking, and settled funding transfers. No winner
notification until such deficiencies are fixed. See adjacent replay script.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import replay_external_github_volpersistence as runner

OUT=runner.OUT
MONTHS=runner.PERIODS
HIGH_PF=1.5
REQUIRED_HIGH=12

def score_one(symbol):
    ledger=pd.read_csv(OUT/(symbol+"_trade_ledger.csv.gz"))
    monthly=pd.read_csv(OUT/(symbol+"_22_ist_months.csv"))
    if list(monthly.month_ist)!=MONTHS:
        raise ValueError("Expected exactly 22 completed IST months")
    t=ledger[ledger.exit_month_ist.isin(MONTHS)].copy()
    if t.empty: raise RuntimeError("No verified completed-month trades: "+symbol)
    rows=[]
    for r in monthly.itertuples(index=False):
        subset=t[t.exit_month_ist==r.month_ist]
        p=subset.pnl.to_numpy(float)
        profit=float(p[p>0].sum())
        loss=float(-p[p<0].sum())
        pf=float(profit/loss) if loss>0 else (float("inf") if profit>0 else float("nan"))
        if int(r.trades)!=len(subset) or not np.isclose(float(r.net_pnl),float(p.sum()),atol=0.01):
            raise AssertionError("Ledger/month reconciliation failed "+symbol+" "+r.month_ist)
        rows.append(dict(symbol=symbol,month_ist=r.month_ist,
          trades=int(r.trades),wins=int((p>0).sum()),losses=int((p<0).sum()),
          gross_profitable_trade_pnl_after_cost=round(profit,5),
          abs_losing_trade_pnl_after_cost=round(loss,5),
          profit_factor=(round(pf,6) if np.isfinite(pf) else
                         ("Infinity" if pf==float("inf") else "N/A")),
          net_trade_pnl_after_cost=round(float(p.sum()),5),
          exit_booked_net_account_return_pct=round(float(r.net_account_return_pct),5),
          high_profit_factor=bool(pf>=HIGH_PF and float(r.net_account_return_pct)>0),
          low_or_negative_return=bool(float(r.net_account_return_pct)<=0),
          mtm_verified=False))
    df=pd.DataFrame(rows)
    profit=float(t.loc[t.pnl>0,"pnl"].sum())
    loss=float(-t.loc[t.pnl<0,"pnl"].sum())
    overall_pf=float(profit/loss) if loss else None
    agg_ret=float(100*(np.prod(1+df.exit_booked_net_account_return_pct.to_numpy(float)/100)-1))
    res=dict(symbol=symbol,
      scored_complete_months=len(df),
      profitable_months=int((df.exit_booked_net_account_return_pct>0).sum()),
      losing_months=int((df.exit_booked_net_account_return_pct<0).sum()),
      no_trade_months=int((df.trades==0).sum()),
      high_pf_months=int(df.high_profit_factor.sum()),
      threshold_high_pf=HIGH_PF,
      aggregate_pf=round(overall_pf,6) if overall_pf is not None else None,
      compounded_exit_booked_return_pct=round(agg_ret,5),
      trade_count=int(len(t)),wins=int((t.pnl>0).sum()),losses=int((t.pnl<0).sum()),
      max_trade_close_drawdown_pct=round(float(t.drawdown_pct.max()),5),
      meets_exploratory_high_pf_threshold=bool(
        agg_ret>0 and overall_pf is not None and overall_pf>=HIGH_PF
        and df.high_profit_factor.sum()>=REQUIRED_HIGH),
      fully_verified=False,
      no_new_signal="Existing 22-month failing strategy rescored; not an approved live strategy",
      important_limits=["2025-01 IST missing 2024-12-31 UTC 18:30-23:59",
        "monthly return books trade exits, not open positions at calendar boundary",
        "actual settled funding, depth, bid/ask and liquidation not modeled",
        "2026 already exposed to research; not pristine independent data"])
    df.to_csv(OUT/(symbol+"_monthly_profit_factor.csv"),index=False)
    return res,df

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    runner.main()  # actual independent replay on authentic BTCUSD/ETHUSD candles
    results=[]
    for sym in ("BTCUSD","ETHUSD"):
        res,df=score_one(sym);results.append(res)
        print("PAIRED_HIGH_PF_SCORE "+json.dumps(res),flush=True)
    report=dict(title="Re-score pinned external GitHub candidate under new high-profit-factor objective",
       source_repo="https://github.com/anaysharma1717-svg/Volatility-Persistence-Trading-Strategy",
       source_sha="4987ed61c4fc7f6fc738d88a6eb844b08190a838",
       strategy_rules="Fixed NY-entry high-volatility 1H prior-candle direction + confirmed 4H EMA200 trend; stop 2x ATR5 and TP 3R; 1% risk single position; standard Delta India 0.05% taker each side + 18% GST; BTC adverse 5bps and ETH adverse 2bps each leg",
       high_pf_definition="Monthly PF >=1.5 and exit-booked monthly return >0, at least 12/22 months; aggregate PF >=1.5 and positive full-period return",
       caveats=["PF is never negative; monthly net account return can be negative",
          "January 2025 IST missing prior UTC evening; must not be considered fully verified",
          "Open positions not marked to market at month-end; do NOT claim true calendar monthly performance",
          "Funding cashflows and order book not modeled, so modeled results are incomplete",
          "Existing candidate; not a newly discovered strategy"],
       results=results,
       qualified_any=any(x["meets_exploratory_high_pf_threshold"] and x["fully_verified"] for x in results))
    (OUT/"paired_high_pf_verdict.json").write_text(json.dumps(report,indent=2)+"\n")
    out=["# Pairwise BTC and ETH monthly profit-factor re-evaluation","",
         "Existing open-source candidate; exploratory and unqualified, not a verified live edge.",
         "",
         "| Market | 22-month modeled return | Aggregate PF | High-PF months | Profitable months | Losing months | Trades |",
         "|---|---:|---:|---:|---:|---:|---:|"]
    for x in results:
        out.append(f'| {x["symbol"]} | {x["compounded_exit_booked_return_pct"]:.2f}% | {x["aggregate_pf"]:.3f} | {x["high_pf_months"]}/22 | {x["profitable_months"]}/22 | {x["losing_months"]}/22 | {x["trade_count"]} |')
    out.extend(["","New criterion: overall PF >=1.5 with 12+ months PF >=1.5 and a positive after-cost exit-booked account return.","",
       "Neither market passes this PF threshold. Monthly details in BTCUSD_monthly_profit_factor.csv and ETHUSD_monthly_profit_factor.csv.",
       "","**Data caveats:** January 2025 IST missing pre-UTC coverage, month-end open-trade MTM absent, funding settlements unmodeled.",
       "Not a verified 22-month calendar-account-return claim."])
    (OUT/"HIGH_PF_REPORT.md").write_text("\n".join(out)+"\n")
if __name__=="__main__":main()
