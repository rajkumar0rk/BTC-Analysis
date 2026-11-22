#!/usr/bin/env python3
"""Independent MR003 artifact reconciliation, runs AFTER authentic historical replay."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
p=Path("analysis/mean_reversion_research/MR003/results")
t=pd.read_csv(p/"trade_ledger.csv")
m=pd.read_csv(p/"monthly_ist_nav.csv")
n=pd.read_csv(p/"minute_nav.csv.gz")
s=json.loads((p/"summary.json").read_text())
assert len(t)==s["trades"] and len(m)==22
assert m.month_ist.tolist()==pd.period_range("2025-01","2026-10",freq="M").astype(str).tolist()
assert np.isfinite(n.nav).all() and (n.nav>0).all()
assert (t.entry_fee>=0).all() and (t.exit_fee>=0).all()
assert (t.quantity>0).all()
assert np.allclose(t.gross_pnl-t.entry_fee-t.exit_fee,t.net_pnl,rtol=0,atol=1e-10)
assert abs(1+t.net_pnl.sum()-t.nav_after.iloc[-1])<1e-8
assert abs(1+t.net_pnl.sum()-n.nav.iloc[-1])<1e-8
assert abs(n.nav.iloc[-1]-m.end_nav.iloc[-1])<1e-8
assert abs(np.prod(1+m.net_return_pct.to_numpy()/100)-n.nav.iloc[-1])<1e-8
assert abs(100*(n.nav.iloc[-1]-1)-s["net_return_pct"])<1e-8
assert abs(t.gross_pnl.sum()-s["gross_pnl"])<1e-8
assert abs(t.entry_fee.sum()+t.exit_fee.sum()-s["fees_gst"])<1e-8
assert int((m.net_return_pct>0).sum())==s["positive_months"]
assert int((m.net_return_pct<0).sum())==s["losing_months"]
assert not t.entry_utc.isna().any() and not t.exit_utc.isna().any()
assert (pd.to_datetime(t.exit_utc,utc=True)>=pd.to_datetime(t.entry_utc,utc=True)).all()
# NAV is marked every minute, and drawdown is measured from its running peak.
peak=np.maximum.accumulate(np.r_[1.,n.nav.to_numpy()])
drawdown=(1-n.nav.to_numpy()/peak[1:]).max()*100
assert abs(drawdown-s["max_minute_close_dd_pct"])<1e-7
out=dict(status="PASS",trades=len(t),months=len(m),net_return_pct=s["net_return_pct"],
    max_minute_close_dd_pct=s["max_minute_close_dd_pct"],
    positive_months=s["positive_months"],losing_months=s["losing_months"],
    fee_gst=t.entry_fee.sum()+t.exit_fee.sum(),
    nav_reconciled=True,monthly_compounding_reconciled=True)
(p/"independent_reconciliation.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
