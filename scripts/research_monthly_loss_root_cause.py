"""Descriptive diagnostic only. Reproduce frozen entries/exits; no parameter search."""
import csv,gzip,json,math
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
import research_rsi14_entry_exit_diagnostics as r
import research_momentum_continuation_frequency as m
from research_rsi14_depth_stability import y24,y25,q,candles25,checks,summarize,dt
OUT=Path("scratch/monthly_loss_root_cause")
REF={"RSI Chandelier":{2024:9644.735195,2025:12787.68496},"1H momentum + 4H trend":{2024:3185.70309,2025:12141.56828}}
def describe(ts,bars,start,year):
    tz=y24.IST if year==2024 else timezone.utc
    def month(t):return datetime.fromisoformat(t["entry_utc"]).astimezone(tz).strftime("%Y-%m")
    C=bars[3];O=bars[0]
    summary=summarize(ts,year);rows=[]
    for key,p in summary["monthly_entry_attribution"].items():
        yr,mo=map(int,key.split("-"))
        a=datetime(yr,mo,1,tzinfo=tz)
        z=datetime(yr+int(mo==12),mo%12+1,1,tzinfo=tz)
        lo=int((a.timestamp()-start)//60);hi=int((z.timestamp()-start)//60)
        assert 0<=lo<hi<=len(C)
        # Daily close-to-close path efficiency, including first daily open.
        prices=np.r_[O[lo],C[lo+1439:hi:1440]]
        assert len(prices)==(hi-lo)//1440+1
        dif=np.diff(np.log(prices));eff=abs(float(np.sum(dif)))/float(np.sum(np.abs(dif))) if np.sum(np.abs(dif)) else 0.
        t=[x for x in ts if month(x)==key];loss=[x for x in t if x["net_points"]<0];win=[x for x in t if x["net_points"]>0]
        gross=sum(x["gross_points"] for x in t);fees=sum(x["fee_points"] for x in t)
        full=[x for x in loss if x["gross_points"]<=-.999999*x["signal_context"]["risk_points"]]
        reached=[x for x in loss if x["signal_context"]["mfe"]>=x["signal_context"]["risk_points"]]
        covered=[x for x in loss if x["signal_context"]["mfe"]>=x["fee_points"]]
        fee_flips=[x for x in loss if x["gross_points"]>0]
        rows.append(dict(month=key,net=p,trades=len(t),wins=len(win),losses=len(loss),gross=gross,fees=fees,full_sl=len(full),losers_mfe_1r=len(reached),losers_mfe_fee=len(covered),fee_flips=len(fee_flips),month_fee_flip=gross>0 and p<=0,loss_points=sum(x["net_points"] for x in loss),loss_full_sl_points=sum(x["net_points"] for x in full),median_loser_mfe_r=float(np.median([x["signal_context"]["mfe"]/x["signal_context"]["risk_points"] for x in loss])) if loss else None,median_loser_mae_r=float(np.median([x["signal_context"]["mae"]/x["signal_context"]["risk_points"] for x in loss])) if loss else None,monthly_return_pct=100*(prices[-1]/prices[0]-1),efficiency=eff,daily_abs_log_move_pct=100*float(np.sum(np.abs(dif))),exits=dict(Counter(x["exit_reason"] for x in t)),status="profit" if p>0 else "loss" if p<0 else "flat"))
    return summary,rows
def totals(rows):
    out={}
    for status,subset in (("profit",[x for x in rows if x["net"]>0]),("loss",[x for x in rows if x["net"]<0]),("flat",[x for x in rows if x["net"]==0]),("nonprofit",[x for x in rows if x["net"]<=0])):
        out[status]=dict(months=len(subset),zero_trade_months=sum(x["trades"]==0 for x in subset),month_fee_flips=sum(x["month_fee_flip"] for x in subset),**{k:sum(x[k] for x in subset) for k in ("net","trades","wins","losses","gross","fees","full_sl","losers_mfe_1r","losers_mfe_fee","fee_flips","loss_points","loss_full_sl_points")},median_efficiency=float(np.median([x["efficiency"] for x in subset])) if subset else None,median_abs_return=float(np.median([abs(x["monthly_return_pct"]) for x in subset])) if subset else None,median_trades=float(np.median([x["trades"] for x in subset])) if subset else None)
    return out
def run():
    checks();m.unit_checks();OUT.mkdir(parents=True,exist_ok=True)
    results={n:{} for n in REF}
    for year in (2024,2025):
        if year==2024:
            q.candles=y24.candles;bars,signals,snapshots,extra,rec=y24.load();start,end,ev=y24.START,y24.END,y24.EVAL
        else:
            q.candles=candles25;bars,signals,snapshots,extra,rec=y25.load();start,end,ev=y25.START,y25.END,y25.START
        ind=q.indicators(bars,snapshots);atr=ind[-1];avg=np.full(len(atr),np.nan)
        for k in range(20,len(atr)):avg[k]=np.mean(atr[k-20:k])
        ST=np.full(len(atr),np.nan);LINE=ST.copy()
        for minute,v in extra.items():
            if minute%15==0:
                if v[1] is not None:ST[minute//15]=v[1]
                if v[2] is not None:LINE[minute//15]=v[2]
        v15=ind[0].reshape(-1,15).sum(axis=1);vavg=np.full(len(v15),np.nan)
        for k in range(20,len(v15)):vavg[k]=np.mean(v15[k-20:k])
        setups=q.setup_rows(bars,signals,snapshots,extra)
        ts=r.replay(bars,ind,setups,start,end,"80-chandelier","baseline",snapshots,extra,avg,ST,LINE,v15,vavg)
        candidates=m.signal_lists(bars,ind,snapshots,extra,start,ev)
        mt=m.replay(bars,candidates["4h-trend"],start,end,"4h-trend","baseline")
        for name,trades in (("RSI Chandelier",ts),("1H momentum + 4H trend",mt)):
            summary,rows=describe(trades,bars,start,year)
            assert math.isclose(summary["net"],REF[name][year],abs_tol=1e-5),(name,year,summary["net"])
            assert summary["trades"]==({"RSI Chandelier":{2024:44,2025:47},"1H momentum + 4H trend":{2024:29,2025:29}}[name][year])
            results[name][year]=dict(summary=summary,months=rows,trades=trades)
            for row in rows:print("MONTH",json.dumps(dict(strategy=name,**row),allow_nan=False))
            print("YEAR",json.dumps(dict(strategy=name,year=year,**totals(rows)),allow_nan=False))
        del bars,ind,snapshots,extra,rec
    for name,years in results.items():
        rows=[x for y in years.values() for x in y["months"]]
        print("TOTAL",json.dumps(dict(strategy=name,**totals(rows)),allow_nan=False))
    rows=[dict(strategy=name,**x) for name,years in results.items() for y in years.values() for x in y["months"]]
    with (OUT/"monthly_diagnostics.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    with gzip.open(OUT/"all_results.json.gz","wt") as f:json.dump(results,f,allow_nan=False,separators=(",",":"))
if __name__=="__main__":run()
