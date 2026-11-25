#!/usr/bin/env python3
"""User-requested 2026 diagnostic replay of V69-B; no parameter selection."""
import itertools,json,hashlib
from pathlib import Path
import numpy as np
import pandas as pd
import research_v48_progressive_trailing as v
from research_v75_higher_frequency import setup,CFG

OUT=Path("analysis/v69_frozen_2026");OUT.mkdir(parents=True,exist_ok=True)
cfg=dict(CFG,timeframe=240,hold_minutes=14400,early_hours=48)
def replay():
    frozen=dict(profile="V69_no_cap",config=cfg,entry_rule="4H prior 20 highs/lows breakout with TR >= 1.25 prior Wilder ATR14",capital=100,risk=v.RISK,exposure_cap=v.CAP,minimum_lot_btc=.001,margin_mode="cross",training_net_usd=49.277536827321114,training_stress_net_usd=42.020963450250946,training_positive_months=17,training_months_ge_1pct=13,training_trades=68,training_pass=False,user_requested_diagnostic=True,prior_2026_research_exists=True,no_parameter_tuning=True)
    path=OUT/"frozen_config.json";path.write_text(json.dumps(frozen,indent=2));sha=hashlib.sha256(path.read_bytes()).hexdigest()
    m,ctx=v.load("validate")
    ctx["atr"]={240:v.atr_series(m,240)}
    ctx["channels"]={n:v.channel_series(m,n) for n in (10,20)}
    ev,ctx["exit_context"]=setup(m,240)
    rows=[];monthly=[];trades=[]
    for label,end in (("full_months","2026-11-01"),("including_partial_november",v.VALID_END)):
        p=v.period(m,ctx,ev,"2026-01-01",end)
        for lev,(sc,mode) in itertools.product((20,50,200),((v.SC[0],0),(v.SC[1],1))):
            r=v.run(ctx,p,cfg,lev,sc,mode,audit=True)
            ledger=r.pop("ledger");ex=ledger[ledger[:,0]==3];pnl=ex[:,9]
            assert (ex[1:,1]>ex[:-1,2]).all()
            assert abs(float(pnl.sum())-r["net_usd"])<1e-6
            win=np.sort(pnl[pnl>0])[::-1];loss=float(-pnl[pnl<0].sum())
            us=r.pop("monthly_usd");re=r.pop("monthly_returns");pt=r.pop("monthly_points")
            r.update(profit_factor=float(win.sum())/loss if loss else None,gross_profit_usd=float(win.sum()),gross_loss_usd=loss,expectancy_usd=float(pnl.mean()) if len(pnl) else 0.,losing_trades=int((pnl<0).sum()),zero_pnl_trades=int((pnl==0).sum()),negative_months=int((re<0).sum()),zero_pnl_months=int((re==0).sum()),worst_month_pct=float(re.min()),net_ex_top5_usd=float(pnl.sum()-win[:5].sum()),busy_signals=int((ledger[:,0]==1).sum()))
            rows.append(dict(period=label,leverage=lev,scenario=sc[0],**r))
            monthly.extend(dict(period=label,leverage=lev,scenario=sc[0],month=str(pd.Period("2026-01",freq="M")+i),net_usd=u,return_pct=q,net_points=t) for i,(u,q,t) in enumerate(zip(us,re,pt)))
            if lev==50:
                for event,rec in zip(p[1],ledger):
                    if rec[0]==3:trades.append(dict(period=label,scenario=sc[0],entry=str(m.index[int(rec[1])]),exit=str(m.index[int(rec[2])]),side=int(event[1]),qty_btc=rec[6],net_usd=rec[9],exit_reason=int(rec[10])))
    assert hashlib.sha256(path.read_bytes()).hexdigest()==sha
    df=pd.DataFrame(rows)
    df.to_csv(OUT/"validation_summary.csv",index=False)
    pd.DataFrame(monthly).to_csv(OUT/"validation_monthly.csv",index=False)
    pd.DataFrame(trades).to_csv(OUT/"validation_trades.csv",index=False)
    (OUT/"quality.json").write_text(json.dumps(dict(frozen_sha256=sha,config_unchanged=True,training_gate_passed=False,diagnostic_only=True,validation_previously_examined=True,no_parameter_tuning=True,full_months="2026-01 through 2026-10 IST",partial_period_end_exclusive=str(v.VALID_END),historical_funding_proxy=True,liquidation_proxy=True,live_execution=False,overlap_asserted=True,complete_candle_data_asserted=True),indent=2))
    print(df[df.leverage==50].to_string(index=False),flush=True)

if __name__=="__main__":replay()
