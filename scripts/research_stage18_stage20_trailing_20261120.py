#!/usr/bin/env python3
"""Stage18/Stage20 TRUE 1m Stage15 trailing-stop and asymmetric exit tests.
Only BTC 2025 may select an improvement; 2026 check is research-exposed.
Uses exactly the preserved Stage14 events and original Stage15 1m OHLC fills.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from numba import njit
import research_july_drawdown_stage15 as stage
import research_stage18_stage20_signal_exit_improvement_20261120 as prior
from research_every_candle_200 import read_archive, FEE, SLIPPAGE

OUT=Path("analysis/stage18_stage20_trailing_exits_20261120")
MONTHS=prior.MONTHS
# 0=never advance stop; 1=cost-adjusted break-even once price travels 2R;
# 2=break-even at 2R then +1R lock on completed 3R candle;
# 3=as mode2 plus +3R lock once completed 5R candle.
RULES=[
 ("original_3R",3.,240,0),
 ("untrailed_5R",5.,240,0),
 ("5R_breakeven_after2R",5.,240,1),
 ("5R_profit_lock_after3R",5.,240,2),
 ("8R_progressive_lock",8.,240,3),
 ("8R_progressive_lock_480m",8.,480,3),
 ("6R_profit_lock_after3R",6.,240,2),
 ("6R_progressive_lock",6.,240,3),
]
@njit(cache=True)
def replay(O,H,L,C,k,side,base_stop,R,hold,mode):
    ent=O[k];risk=side*(ent-base_stop);target=ent+side*risk*R
    stop=base_stop
    # conservative: stop/target checked with PREVIOUS 1m close's trailing state
    # inside same minute, stop always first if stop and target both touch.
    for j in range(k,k+hold):
        stop_hit=(L[j]<=stop) if side==1 else (H[j]>=stop)
        target_hit=(H[j]>=target) if side==1 else (L[j]<=target)
        if stop_hit:
            outmid=min(O[j],stop) if side==1 else max(O[j],stop)
            why=0
            break
        if target_hit:
            outmid=target
            why=1
            break
        if mode>0:
            favorable=(H[j]-ent)/risk if side==1 else (ent-L[j])/risk
            # No same-minute retroactive tightened stop: only next candle
            # sees this update. Break-even mid must cover fee+GST and slip.
            if favorable>=2:
                allcost=2*SLIPPAGE+2*FEE*ent
                newstop=ent+side*allcost
                stop=max(stop,newstop) if side==1 else min(stop,newstop)
            if mode>=2 and favorable>=3:
                newstop=ent+side*risk
                stop=max(stop,newstop) if side==1 else min(stop,newstop)
            if mode>=3 and favorable>=5:
                newstop=ent+side*3*risk
                stop=max(stop,newstop) if side==1 else min(stop,newstop)
    else:
        j=k+hold-1;outmid=C[j];why=2
    fin=ent+side*SLIPPAGE
    fout=outmid-side*SLIPPAGE
    gross=side*(outmid-ent)
    net=side*(fout-fin)-FEE*(fin+fout)
    offer=side*(fout-fin)-FEE*fin-(0. if j-k+1<=30 else FEE*fout)
    return j,why,gross,net,offer,net/risk,risk
def variant_events(e,f,name,R,hold,mode):
    stage.REWARD_R=R;stage.HOLD_MINUTES=hold
    if mode==0:
        from research_structure_rr_stage11 import replay_one
        stage.replay_one=replay_one
    else:
        stage.replay_one=lambda O,H,L,C,k,side,stop,rr,h: replay(O,H,L,C,k,side,stop,rr,h,mode)
    s,skip=stage.simulate_candidates(e,f,name,"weekly_minus_3R",prior.mask(e,"baseline"))
    if not s:raise AssertionError("Empty candidate "+name)
    g=pd.DataFrame(s).sort_values(["exit_unix","entry_unix"],kind="stable")
    g["exit_month_ist"]=pd.to_datetime(g.exit_unix,unit="s",utc=True).dt.tz_convert("Asia/Kolkata").dt.strftime("%Y-%m")
    g=g[g.exit_month_ist.isin(MONTHS)].copy()
    g["entry_mid"]=f.open.to_numpy(float)[g.k.to_numpy(int)]
    g["risk_fraction"]=np.minimum(prior.RISK_FRACTION,prior.MAX_LEVERAGE*g.initial_risk_pts/g.entry_mid)
    g["case"]=name
    return g
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    f,_,_,sourceq=read_archive()
    e=stage.selected_events(pd.read_csv(prior.EVENTS))
    sleeves=prior.saved_sleeves()
    results=[];monthly=[];trades=[]
    baseline=None
    for name,R,hold,mode in RULES:
        g=variant_events(e,f,name,R,hold,mode)
        trades.append(g)
        for bps in (0,2,5):
            calc=prior.replay_nav(g,bps)
            for family in ("Stage18","Stage20"):
                series=prior.portfolio(calc,sleeves["d55"],None) if family=="Stage18" else prior.portfolio(calc,sleeves["d20"],sleeves["hourly"])
                metrics=prior.returns(series)
                results.append(dict(family=family,variant=name,reward_R=R,hold_minutes=hold,
                    trail_mode=mode,extra_slip_bps_each_side=bps,
                    stage15_trades=calc["trades"],stage15_trades_2025=calc["trades_2025"],
                    stage15_pf_netR=calc["pf_net_R"],stage15_mean_netR=calc["mean_net_R_per_trade"],
                    stage15_2025_net_pct=calc["net_2025"],
                    stage15_2026_JanOct_pct=calc["net_2026JanOct"],**metrics))
                monthly.extend([dict(family=family,variant=name,extra_slip_bps_each_side=bps,
                                     month_ist=m,net_account_pct=float(r)) for m,r in zip(MONTHS,series)])
    rd=pd.DataFrame(results);mo=pd.DataFrame(monthly)
    for family in ("Stage18","Stage20"):
        baseline=rd[(rd.family==family)&(rd.variant=="original_3R")&(rd.extra_slip_bps_each_side==0)].iloc[0]
        orig=sleeves["ref18"] if family=="Stage18" else sleeves["ref20"]
        original_portfolio=mo[(mo.family==family)&(mo.variant=="original_3R")&
                              (mo.extra_slip_bps_each_side==0)].set_index("month_ist").reindex(MONTHS).net_account_pct.to_numpy()
        delta=float(np.max(np.abs(original_portfolio-orig)))
        if delta>.04:raise AssertionError(f"Original baseline mismatched: {family} {delta}")
        # 2025 ONLY stressed +2bps per side, enough trades, downside penalty
        ranked=rd[(rd.family==family)&(rd.extra_slip_bps_each_side==2)&
                  (rd.stage15_trades_2025>=25)&(rd.net_2025_pct>0)].copy()
        ranked["BTC2025_select_score"]=ranked.net_2025_pct-.75*ranked.max_month_end_dd_pct
        ranked=ranked.sort_values(["BTC2025_select_score","stage15_trades_2025"],ascending=False)
        print("BTC2025_TRAIN_RANK",family,ranked[["variant","BTC2025_select_score",
          "net_2025_pct","stage15_trades_2025","max_month_end_dd_pct"]].to_json(orient="records"))
        pick=ranked.iloc[0].variant if len(ranked) else "original_3R"
        print("FROZEN_BTC2025_SELECTION",family,pick)
        for name in dict.fromkeys(["original_3R","untrailed_5R",pick]):
            for bps in (0,2,5):
                row=rd[(rd.family==family)&(rd.variant==name)&
                       (rd.extra_slip_bps_each_side==bps)]
                print("AUDIT_RESULT",row.iloc[0].to_json())
    rd.to_csv(OUT/"all_completed_1m_exit_tests.csv",index=False)
    mo.to_csv(OUT/"all_monthly_portfolio_returns.csv",index=False)
    pd.concat(trades,ignore_index=True).to_csv(OUT/"all_trade_exits.csv.gz",index=False,compression="gzip")
    (OUT/"study_limitations.json").write_text(json.dumps(dict(
      original_stage14_source_run=44118024590,
      source_quality=sourceq,rules=RULES,
      note="Actual BTC 1m replay for Stage15 component; archived Stage17/19 for combined NAV (not integrated multi-sleeve execution)",
      selection="ONLY 2025 BTC (stress 2bp per side) using net return minus .75*monthly DD; 2026 historically seen, NOT untouched holdout",
      costs="Base 0.05% taker/side, GST18%, 5 BTC points slip/side; extra 2/5bps adverse slippage per fill; funding/L2/margin/contract granularity missing",
      warning="No independent ETH native execution, original October 2026 UTC last day missing, 2025 IST start missing 330 minutes, month boundaries closed-trade NAV not fully MTM",
      no_live_trading=True),indent=2,default=str)+"\n")
    print("STAGE18_20_NEW_TRAILING_1M_EXECUTION_COMPLETE",len(rd))
if __name__=="__main__":main()
