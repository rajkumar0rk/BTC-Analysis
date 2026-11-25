#!/usr/bin/env python3
"""User-requested diagnostic replay of exact C16; no new parameter selection."""
import json, hashlib
from pathlib import Path
import pandas as pd
import numpy as np
import research_btc15m_c05_partial_quantity as parent
OUT=Path("analysis/btc15m_c05_fixed_2026_20261125")
CID=16
SOURCE="638a1a3c1febb0059f25109e2c36a5a79e4aa989"
def main():
    cfg=parent.GRID[CID]
    assert cfg==parent.config(0.,1.,quality_factor=.25,cost_be=True)
    assert cfg["activation"]==2.5 and cfg["partial_trigger"]==3. and cfg["partial_fraction"]==.25 and cfg["rr"]==3.5
    OUT.mkdir(parents=True,exist_ok=True)
    fixed=dict(source_commit=SOURCE,candidate=CID,config=cfg,training_gate_passed=False,prior_2026_exposure=True,selection="User requested exact previously reported C16; diagnostic only; no parameter changes or reranking.",profiles=[100,80],costs={"fee_per_side":parent.base.FEE,"slippage_per_side":parent.base.SLIP,"stress_slippage_per_side":3*parent.base.SLIP,"funding_included":False})
    (OUT/"FIXED.json").write_text(json.dumps(fixed,indent=2)+"\n")
    ns=parent.engine();rows=[];monthly=[];ledger=[]
    # One 2025 parity replay verifies the imported exact benchmark before 2026.
    data=parent.prep("2025",cfg["signal_tf"])
    x,m,l=parent.replay(ns,data,"2025",CID,cfg,100,"O-H-L-C",False)
    assert abs(x["net_return_pct"]-47.1135)<.015 and x["trades"]==58 and x["profitable_months"]==11
    (OUT/"parity.json").write_text(json.dumps({"return_pct":x["net_return_pct"],"trades":x["trades"],"profitable_months":x["profitable_months"]},indent=2)+"\n")
    data=parent.prep("2026",cfg["signal_tf"])
    df=data[0]
    start=parent.date("2026-01-01");end=parent.date("2026-11-01")
    mask=(df.index>=start)&(df.index<end)
    assert mask.sum()==int((end-start).total_seconds()/60)
    assert df.index[mask][0]==start and df.index[mask][-1]==end-pd.Timedelta(minutes=1)
    for prof in (100,80):
        for path in parent.base.PATHS:
            for stress in (False,True):
                x,m,l=parent.replay(ns,data,"2026",CID,cfg,prof,path,stress)
                assert len(m)==10 and set(m.month_ist)==set(str(i) for i in pd.period_range("2026-01","2026-10",freq="M"))
                entries=pd.to_datetime(l.entry_time_utc,utc=True)
                exits=pd.to_datetime(l.exit_time_utc,utc=True)
                assert (entries>=start).all() and (exits<end).all()
                assert (entries.iloc[1:].reset_index(drop=True)>=exits.iloc[:-1].reset_index(drop=True)).all()
                assert x["wins"]+x["losses"]+x["breakeven_trades"]==len(l)
                assert abs(np.prod(1+m.monthly_return_pct/100)-1-x["net_return_pct"]/100)<1e-5
                x["profit_factor"]=float(l.loc[l.net_usd>1e-8,"net_usd"].sum()/(-l.loc[l.net_usd< -1e-8,"net_usd"].sum()))
                rows.append(x);monthly.append(m);ledger.append(l)
                print("FIXED",prof,path,stress,x["net_return_pct"],x["profitable_months"],flush=True)
    s=pd.DataFrame(rows);m=pd.concat(monthly,ignore_index=True);l=pd.concat(ledger,ignore_index=True)
    assert len(s)==8 and len(m)==80
    s.to_csv(OUT/"summary.csv",index=False);m.to_csv(OUT/"monthly.csv",index=False);l.to_csv(OUT/"ledger.csv",index=False)
    checks={"one_minute_candles":int(mask.sum()),"warmup_candles":int((df.index<start).sum()),"period_start_ist":"2026-01-01 00:00","period_end_ist_exclusive":"2026-11-01 00:00","scenario_count":len(s),"source_sha256":hashlib.sha256(Path(parent.__file__).read_bytes()).hexdigest(),"no_overlap":True,"no_preperiod_entry":True,"monthly_compounding_reconciled":True,"training_parity":True}
    (OUT/"checks.json").write_text(json.dumps(checks,indent=2)+"\n")
    cols=["profile","path_assumption","stress","net_return_pct","profit_factor","max_floating_drawdown_pct","profitable_months","trades","wins","losses","breakeven_trades","fees_gst_usd"]
    lines=["# Exact C16 diagnostic: 2026 Jan-Oct","", "Not an approved candidate; prior 2026 exposure, no retuning. Funding excluded. 2025 benchmark parity passed. 100% and 80% maximum exposure, not leverage.","",s[cols].to_markdown(index=False),"","## Monthly net returns, worse path per month","",m.groupby(["month_ist","profile","stress"]).monthly_return_pct.min().unstack(["profile","stress"]).to_markdown(),""]
    (OUT/"REPORT.md").write_text("\n".join(lines)+"\n")
if __name__=="__main__":main()
