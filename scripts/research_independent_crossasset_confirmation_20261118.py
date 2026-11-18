#!/usr/bin/env python3
"""Independent differential: last-completed other-asset 4H direction confirmation."""
import sys, json
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parent))
from eth_native_crossfamily_v2 import load,aggregate,signal_library,MONTHS,FEE,RISK,CAP
from research_btc_eth_profit_factor_pairs import replay_instrument,month_table,flatten,events_for,ledger_detail
OUT=Path("analysis/independent_crossasset_confirmation_20261118")
FAMILIES=["4h:engulfing_reversal","15min:trend_retest","1h:failed_auction"]
MODES=["direction_agree","direction_and_body_035atr"]
GRID=[(1.5,2.),(2.5,2.),(1.5,3.),(2.5,3.)]
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    markets={sym:load(sym) for sym in ("BTCUSD","ETHUSD")}
    assert markets["BTCUSD"].index.equals(markets["ETHUSD"].index)
    bars={sym:{s:aggregate(a,s) for s in ("5min","15min","1h","4h")} for sym,a in markets.items()}
    signals={sym:signal_library(bars[sym]) for sym in markets}
    all_rows=[];all_months=[];ledger_cache={}
    for sym,asset in markets.items():
        other="ETHUSD" if sym=="BTCUSD" else "BTCUSD"
        o4=bars[other]["4h"]
        o4_direction=np.sign(o4.close-o4.open)
        o4_body=(o4.close-o4.open).abs()/o4.atr.replace(0,np.nan)
        ist=asset.index.tz_convert("Asia/Kolkata")
        mc=np.asarray(ist.year*100+ist.month,dtype=np.int32)
        open_,high,low,close=[asset[k].to_numpy(float) for k in ("open","high","low","close")]
        for family in FAMILIES:
            b,long,short=signals[sym][family]
            direction=o4_direction.reindex(b.index,method="ffill").fillna(0).to_numpy()
            strength=o4_body.reindex(b.index,method="ffill").fillna(0).to_numpy()
            other_valid=o4.valid.reindex(b.index,method="ffill").fillna(False).to_numpy(bool)
            for mode in MODES:
                mask=other_valid & (strength>=.35 if mode=="direction_and_body_035atr" else np.ones(len(b),bool))
                long_f=long & pd.Series(mask & (direction>0),index=b.index)
                short_f=short & pd.Series(mask & (direction<0),index=b.index)
                _,k,sides,idx=events_for((b,long_f,short_f),asset)
                if len(k)==0:continue
                stop=b.atr.to_numpy(float)[idx]
                hold={"4h":4320,"1h":1440,"15min":720}[family.split(":")[0]]
                for sl,rr in GRID:
                    name=f"{family}__cross_{mode}__SL{sl:g}_RR{rr:g}"
                    ledger=replay_instrument(open_,high,low,close,mc,k,sides,stop,rr,hold,sl,RISK,CAP,5. if sym=="BTCUSD" else 0.,0. if sym=="BTCUSD" else .0002,FEE)
                    months=month_table(ledger,mc,sym,name)
                    row=flatten(sym,name,ledger,months)
                    row["family"]=family;row["cross_filter"]=mode;row["stop_atr"]=sl;row["target_R"]=rr
                    all_rows.append(row);all_months.extend(months)
                    ledger_cache[(sym,name)]=(ledger,asset)
        print("MARKET_DONE",sym,flush=True)
    summary=pd.DataFrame(all_rows);monthly=pd.DataFrame(all_months)
    summary.to_csv(OUT/"all_models.csv",index=False)
    monthly.to_csv(OUT/"all_monthly.csv",index=False)
    assert len(summary)==len(FAMILIES)*len(MODES)*len(GRID)*2
    # Review candidates selected using 2025 only, not 2026. Same parameter name on both assets.
    picks=set()
    for sym in markets:
        t=summary[(summary.market==sym)&(summary.trades_2025>=24)&(summary.net_return_2025_pct>0)].copy()
        t["train_score"]=t.strong_months_2025*4+t.positive_months_2025+np.minimum(t.net_return_2025_pct,100)/10+t.profit_factor_2025.map(lambda x:float(x) if isinstance(x,(int,float)) else 0)
        picks.update(t.sort_values("train_score",ascending=False).head(3).model.tolist())
    selected=summary[summary.model.isin(picks)].copy()
    selected.to_csv(OUT/"selected_pairs.csv",index=False)
    monthly[monthly.model.isin(picks)].to_csv(OUT/"selected_monthly.csv",index=False)
    ledgers=[ledger_detail(sym,name,*ledger_cache[(sym,name)]) for sym,name in ledger_cache if name in picks]
    if ledgers:pd.concat(ledgers,ignore_index=True).to_csv(OUT/"selected_trade_ledgers.csv",index=False)
    def annualize(df):
        result=[]
        for r in df.to_dict("records"):
            m=monthly[(monthly.market==r["market"])&(monthly.model==r["model"])]
            assert len(m)==22
            r["months_pf15_net5"]=int(sum((x=="infinite" or (isinstance(x,(float,int)) and x>=1.5)) and y>=5 for x,y in zip(m.profit_factor,m.net_return_pct)))
            r["months_pf15_net10"]=int(sum((x=="infinite" or (isinstance(x,(float,int)) and x>=1.5)) and y>=10 for x,y in zip(m.profit_factor,m.net_return_pct)))
            r["full_2025_net_pct"]=(float(np.prod(1+m.iloc[:12].net_return_pct.to_numpy()/100))-1)*100
            r["jan_oct_2026_ytd_pct"]=(float(np.prod(1+m.iloc[12:].net_return_pct.to_numpy()/100))-1)*100
            r["full_2025_gt500"]=r["full_2025_net_pct"]>500
            r["jan_oct_2026_gt500"]=r["jan_oct_2026_ytd_pct"]>500
            result.append(r)
        return pd.DataFrame(result)
    final=annualize(summary)
    final.to_csv(OUT/"all_models_annual_and_monthly_thresholds.csv",index=False)
    best=final.sort_values(["months_pf15_net5","months_pf15_net10","net_return_pct"],ascending=False).head(12)
    best.to_csv(OUT/"best_exploratory.csv",index=False)
    quality={"original_data_sha256_verified":True,"markets":list(markets),"families":FAMILIES,"cross_modes":MODES,"models_per_market":24,
             "2025_train_only_selection":True,"2026_not_pristine_oos":True,
             "fee_each_side":.0005,"GST_on_fee":.18,"BTC_slip_each_side_points":5,"ETH_slip_each_side_fraction":.0002,
             "risk_per_stop":RISK,"notional_leverage_cap":CAP,
             "first_IST_month_missing":"Jan2025 first 5.5h absent",
             "omitted":["funding","verified spread","market impact","lot sizes","liquidation/margin","actual fills"],
             "novelty":"Partial overlap: cross-asset confirmation only; prior family entries and exits reused",
             "monthly_equity":"exit-based, positions closed at month boundaries by replay"}
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2)+"\n")
    report=["# BTC ETH other-asset completed 4H confirmation differential","","**Partial-overlap exploratory research, not novel base strategy or forward validation.**",
            "Same entry/exit/ATR/stop/target parameters for BTC and ETH. 24 models each; 2025-selected candidates cross-checked in both markets.",
            "","## Top models by count of monthly PF >=1.5 AND monthly NET return >=5%","",best[["market","model","profit_factor","net_return_pct","months_pf15_net5","months_pf15_net10","positive_months","trades","max_closed_trade_drawdown_pct","full_2025_net_pct","jan_oct_2026_ytd_pct","full_2025_gt500"]].to_markdown(index=False),
            "","## Limitations","",json.dumps(quality,indent=2)]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("FINISHED",json.dumps({"rows":len(final),"strong5_max":int(final.months_pf15_net5.max()),"strong10_max":int(final.months_pf15_net10.max()),"2025_gt500":int(final.full_2025_gt500.sum()),"top":best[["market","model","profit_factor","net_return_pct","months_pf15_net5","months_pf15_net10","positive_months","trades"]].head(5).to_dict("records")}),flush=True)
if __name__=="__main__":main()
