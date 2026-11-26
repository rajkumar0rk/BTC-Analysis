"""Import pinned historical Supertrend evidence without replaying any strategy.
Account USD trades remain separate from instrument price points; account MTM months
and floating DD are displayed separately from entry-month realized cash P&L.
"""
import json, os, re, subprocess, math
from pathlib import Path
import pandas as pd
from dashboard_archive import dump, stats, curve, stamp, side, number
REPO="rajkumar0rk/BTC-Analysis"
def main(root,out):
    data=out/"data"; index=json.loads((data/"index.json").read_text())
    specs=json.loads((root/"dashboard/supertrend-sources.json").read_text())
    sources={s["id"]:s for s in specs}
    work=Path(os.environ.get("DASHBOARD_RESEARCH_CACHE",str(root/".dashboard-research-cache")))
    for s in specs:
        assert re.fullmatch(r"[a-f0-9]{40}",s["sha"])
        for name in s["files"]:
            dest=work/s["sha"]/s["folder"]/name
            if not dest.exists():
                dest.parent.mkdir(parents=True,exist_ok=True)
                tmp=dest.with_suffix(dest.suffix+".tmp")
                subprocess.run(["curl","--fail","--silent","--show-error","--location","--retry","3","--max-time","120","https://raw.githubusercontent.com/"+REPO+"/"+s["sha"]+"/"+s["folder"]+"/"+name,"-o",str(tmp)],check=True)
                if not tmp.stat().st_size:raise ValueError("Empty source "+name)
                tmp.replace(dest)
    def p(key,name):
        s=sources[key];return work/s["sha"]/s["folder"]/name
    def csv(key,name):return pd.read_csv(p(key,name))
    def obj(key,name):return json.loads(p(key,name).read_text())
    def link(key,name):
        s=sources[key];return f"https://github.com/{REPO}/blob/{s['sha']}/{s['folder']}/{name}"
    summaries=[]
    def add(id,name,key,file,window,status,net,dd,positive,total,trades,monthly=None,replay=None,unit="account return %",dd_label="Floating DD %",notes=""):
        row=dict(id=id,name=name,source=link(key,file),window=window,status=status,net=net,unit=unit,drawdown=dd,drawdown_label=dd_label,positive_months=positive,months=total,trades=trades,monthly=monthly or [],replay_id=replay,notes=notes)
        summaries.append(row)
    shortlist=obj("locked15","BTCUSD_15M_ATR_STRATEGY_SHORTLIST_20261123.json")
    for c in shortlist["candidates"]:
        exp=c["max_exposure_percent"]
        add("locked15-"+str(exp),f"15M EMA20 + Supertrend ATR0.20 / {exp}% exposure","locked15","BTCUSD_15M_ATR_STRATEGY_SHORTLIST_20261123.json","2025-01–2026-10 IST",c["status"],c["net_compounded_backtest_return_percent"],c["max_floating_drawdown_percent"],c["profitable_months"],c["total_months"],c["trades"],notes="In-sample; fee/GST and modeled slippage included; funding and liquidation excluded. Exact selected ledger/monthly series not committed.")
    for profile,rule in [(80,"A035"),(100,"A019")]:
        file=f"profile_{profile}.csv"; rows=csv("latest",file)
        r=rows[rows.rule==rule].iloc[0]
        add(f"recovery-{profile}",f"15M Supertrend recovery {rule} / {profile}%","latest",file,"2025-01–2026-10 IST","Latest research; strict 20-month candidate" if profile==80 else "Latest research; 21 months, failed strict floor",float(r.net),float(r.dd),int(r.winning_months),22,int(r.trades),notes="Worst-path reported result; in-sample adaptive sizing. No exact selected trade ledger/monthly series in this branch.")
    c=csv("c05","monthly_comparison.csv")
    m=[dict(month=str(r.month_ist),value=float(r.C05_worst_path_cost)) for r in c.itertuples()]
    add("c05-training","C05 / 2024–2025 training","c05","monthly_comparison.csv","2024-02–2025-12 IST","Training only; no approved improved candidate",None,None,sum(x["value"]>0 for x in m),len(m),None,m,notes="Worst-path/cost monthly results; annual equity resets; do not compound mixed scenarios into an aggregate.")
    # Explicitly label a named comparison/validation model even when loss-making.
    def import_replay(key,summaryfile,monthlyfile,ledgerfile,profile,period,name,status):
        ss=csv(key,summaryfile); mm=csv(key,monthlyfile); ll=csv(key,ledgerfile)
        def choose(d):
            x=d[(d.profile==profile)&(d.path_assumption=="O-H-L-C")]
            if "stress" in x:x=x[x.stress.astype(str).str.lower()=="false"]
            if "period" in x:x=x[x.period.astype(str)==str(period)]
            return x
        sr=choose(ss)
        if len(sr)!=1:raise ValueError("Ambiguous selected summary "+key+str(period))
        s=sr.iloc[0]; mo=choose(mm); le=choose(ll).sort_values("entry_time_utc")
        if len(le)!=int(s.trades):raise ValueError("Recorded trade count mismatch "+key)
        rid=f"st-{key}-{profile}-{period}"
        records=[]
        for i,r in enumerate(le.to_dict("records")):
            en,ex=stamp(r["entry_time_utc"]),stamp(r["exit_time_utc"])
            direction=side(r["direction"]); net=number(r["net_usd"])
            if not en or not ex or ex<en or direction is None or net is None:raise ValueError("Bad archived trade "+rid)
            context={k:number(r[k]) for k in ("R","activation_count","lock_increase_count","max_locked_market_move_pct","entry_exposure_pct","planned_risk_pct","equity_after_usd","fee_gst_usd","partial_entries","partial_exits") if k in r and number(r[k]) is not None}
            # net_points is the legacy transport key. The explicit USD unit controls every display.
            records.append(dict(id=f"{rid}-{i}",entry_utc=en,exit_utc=ex,side=direction,entry_price=number(r["entry"]),exit_price=number(r["exit"]),entry_reason=None,exit_reason=str(r["exit_reason"]),result=str(r["exit_reason"]),net_points=net,stop_price=number(r["initial_stop"]),target_price=number(r["target"]),signal_context=context,signal_tf=15,split=str(period),audit="Recorded ledger; no per-trade entry reason"))
        by={}
        for rec in records:by.setdefault(rec["entry_utc"][:7],[]).append(rec)
        months=[]
        for month,rs in sorted(by.items()):
            dump(data/"runs"/rid/(month+".json"),rs)
            months.append(dict(month=month,net=round(sum(t["net_points"] for t in rs),6),trades=len(rs),wins=sum(t["net_points"]>0 for t in rs)))
        dump(data/"runs"/rid/"curve.json",curve(records))
        metrics=stats(records)
        index["runs"].append(dict(id=rid,strategy=name,symbol="BTCUSD",unit="account USD",source=link(key,ledgerfile),audit="Recorded fills; entry reason unavailable",research_reference=True,detail_available=True,target=None,stop=None,months=months,costs="Source baseline modeled costs; O-H-L-C path. Funding excluded. Account USD, not price points.",**metrics))
        monthly=[dict(month=str(r.month_ist),value=float(r.monthly_return_pct)) for r in mo.sort_values("month_ist").itertuples()]
        if not monthly:raise ValueError("Missing source MTM monthly results")
        if sum(x["value"]>0 for x in monthly)!=int(s.profitable_months):raise ValueError("Monthly sign mismatch "+rid)
        add(rid,name,key,summaryfile,f"{monthly[0]['month']}–{monthly[-1]['month']} IST",status,float(s.net_return_pct),float(s.max_floating_drawdown_pct),int(s.profitable_months),len(monthly),int(s.trades),monthly,rid,notes="One explicitly selected O-H-L-C baseline scenario; account MTM result can differ from sum of closed trades. Actual entry/exit fills and exit reasons; entry reasons not recorded.")
    for profile in (80,100):
        import_replay("c05validation","summary.csv","monthly.csv","ledger.csv",profile,2026,f"C05 family / exact C16 2026 diagnostic / {profile}%","Failed 2026 diagnostic; not approved")
        for period in (2025,2026):
            import_replay("c13","frozen_summary.csv","frozen_monthly.csv","frozen_ledger.csv",profile,period,f"C13 family / C12 neighbor / {profile}% / {period}","Diagnostic; training gate failed")
        import_replay("x180","summary.csv","monthly.csv","ledger.csv",profile,2024,f"X180 frozen 2024 / {profile}%","Frozen historical check; failed")
    original=obj("original","summary.json")["comparison"]["one_minute"]["assumed_30m_offer"]
    mo=[dict(month=r["month"],value=r["net_usd"]) for r in original["monthly"] if r["complete"]]
    add("original15","Original 15M EMA20 + Supertrend / 1M execution audit","original","summary.json","2025-01–2026-10 complete months","Failed realistic 1M OHLC replay",original["net_usd"],original["max_closed_drawdown_pct"],original["positive_complete_months"],original["completed_months"],original["trades"],mo,unit="account USD",dd_label="Closed DD %",notes="Old +$828.50 15M OHLC result is not the 1M result. Assumed 30-minute fee offer, 100x isolated, no funding; source summary only here.")
    index["full_configurations"]=sum(r.get("detail_available",True) for r in index["runs"])
    index["supertrend_replay_count"]=sum(r.get("research_reference",False) for r in index["runs"])
    dump(data/"index.json",index);dump(data/"supertrend.json",summaries)
    coverage=json.loads((data/"coverage.json").read_text())
    coverage.extend(dict(path=s["folder"],url=link(s["id"],s["files"][0]),status="Pinned Supertrend evidence imported; only explicit selected configurations; no strategy rerun") for s in specs)
    dump(data/"coverage.json",coverage)
    print(f"SUPER TREND: {len(summaries)} evidence summaries; {index['supertrend_replay_count']} recorded account-USD replays")
