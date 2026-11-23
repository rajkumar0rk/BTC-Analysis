#!/usr/bin/env python3
"""Exact 22-month BTCUSD 15m Reclaim, NO ST-flip exit, 3% SL, 9% TP.
Reuses the previous validated backtest engine unchanged, with targeted
monthly equity and per-exit-month ledger metrics for reproducibility."""
import sys,json
from pathlib import Path
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parent))
import research_btc15m_no_st_flip_exit_pct_sl_20261123 as lab
OUT=Path("analysis/btc15m_reclaim_sl3_tp9_monthly_20261123")
CFG="reclaim_NOFLIP_SL300_NONE_TP3R"
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    df,quality=lab.read_source("BTCUSD")
    ema,stline,trend,valid=lab.st_and_ema(df,lab.TF)
    ind=lab.make_indicators(df)
    signals=lab.make_signals(df,ema,trend,valid,"reclaim",4)[0]
    results=[]
    for path in lab.PATHS:
        print("BEGIN",path,flush=True)
        summary,monthly,trades=lab.simulate(df,ema,stline,trend,ind,
          CFG,lab.CONFIGS[CFG],signals,path)
        assert summary["trades"]==75,(path,summary["trades"])
        assert abs(summary["net_return_pct"]-97.5183)<0.001,(path,summary)
        assert summary["wins"]==27 and summary["losses"]==48
        assert summary["tp_exits"]==26 and summary["stop_exits"]==48
        assert summary["flip_exits"]==0 and summary["protected_exit_trades"]==0
        assert summary["profitable_months"]==16
        assert summary["profitable_2025_months"]==8
        assert summary["profitable_2026_months"]==8
        assert len(monthly)==22
        assert (monthly.month_ist.to_list()==[str(x) for x in lab.MONTHS])
        monthly=monthly.copy()
        x=trades.groupby("exit_month_ist").agg(
           exits=("net_usd","size"),
           winning_exits=("net_usd",lambda z:int((z>0).sum())),
           losing_exits=("net_usd",lambda z:int((z<=0).sum())),
           realized_net_usd=("net_usd","sum"),
           fee_gst_usd=("fee_gst_usd","sum")).reset_index().rename(
           columns={"exit_month_ist":"month_ist"})
        monthly=monthly.merge(x,on="month_ist",how="left")
        for field in ("exits","winning_exits","losing_exits"):
            monthly[field]=monthly[field].fillna(0).astype(int)
        for field in ("realized_net_usd","fee_gst_usd"):
            monthly[field]=monthly[field].fillna(0.0).round(4)
        assert abs(float(monthly.equity_usd.iloc[-1])-1000*(1+summary["net_return_pct"]/100))<.01
        assert abs(((monthly.monthly_return_pct/100+1).prod()-1)*100-summary["net_return_pct"])<.0002
        tag=path.replace("-","").lower()
        monthly.to_csv(OUT/f"monthly_{tag}.csv",index=False)
        trades.to_csv(OUT/f"trades_{tag}.csv.gz",index=False,compression="gzip")
        results.append(summary)
        print("MONTHLY_RESULT",path,flush=True)
        print(monthly.to_string(index=False),flush=True)
    assert all(a["net_return_pct"]==results[0]["net_return_pct"] for a in results)
    pd.DataFrame(results).to_csv(OUT/"summary.csv",index=False)
    p=pd.read_csv(OUT/"monthly_ohlc.csv")
    lines=[
        "# BTCUSD 15m Reclaim — 3% SL / 9% TP month-by-month",
        "",
        "Exact re-run of the prior NOFLIP model, using the unmodified backtest engine.",
        "15M Supertrend(10,3) + EMA20 for entry only; no Supertrend reversal exit;",
        "fixed 3% SL of filled entry price and 9% TP (3R); profit protection OFF.",
        "One trade open maximum; entry signals arriving while in position skipped.",
        "Jan 2025–Oct 2026, 22 IST monthly periods; $1,000 initial, 1x evolving notional.",
        "Fees 0.05% taker per side + 18% GST, slippage 0.02% adverse each side.",
        "Monthly return calculated from end-of-month marked-to-market equity,",
        "so monthly returns can include unrealized P&L on an open trade.",
        "Number of trades shown is number EXITED in each month, not signal count.",
        "Backtest does not model real spread, execution depth, funding or liquidation.",
        "This same historical sample has been repeatedly studied; no out-of-sample verification.",
        "",
        "## Exact 22 monthly returns",
        "",
        p[["month_ist","monthly_return_pct","equity_usd","exits",
           "winning_exits","losing_exits","position_open"]].to_markdown(index=False,floatfmt=".3f"),
        "",
        "## Annual / full-window summary",
        "",
        "2025 "+str(results[0]["return_2025_pct"])+"% with "+str(results[0]["profitable_2025_months"])+"/12 positive months.",
        "Jan–Oct 2026 "+str(results[0]["return_2026_pct"])+"% with "+str(results[0]["profitable_2026_months"])+"/10 positive months.",
        "Full Jan 2025–Oct 2026 "+str(results[0]["net_return_pct"])+"%, "+str(results[0]["profitable_months"])+"/22 profitable months.",
        "75 completed trades: 27 positive and 48 negative; 26 TP, 48 SL and 1 final sample close.",
        "Alternate simulated 1m OHLC path reproduced identical net and monthly returns.",
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(lines)+"\n")
    (OUT/"data_quality.json").write_text(json.dumps(quality,default=str,indent=2)+"\n")
    print("EXACT_MONTHLY_PARITY_OK",len(p),flush=True)
if __name__=="__main__": main()
