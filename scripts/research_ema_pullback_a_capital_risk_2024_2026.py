"""Frozen A capital sizing and mark-price risk stress; no strategy changes."""
import csv,gzip,json,math,itertools
from pathlib import Path
from datetime import datetime
import numpy as np
import research_independent_big_move_2024_2025 as base
import research_ema_pullback_robustness_2024_2025 as rob
import research_ema_pullback_ab_validation_2026 as validation
OUT=Path("scratch/ema_pullback_a_capital_risk")
START_BALANCE=100.
LEVERAGES=(1,2,5,10,20)
RISKS=(.0025,.005,.01,.02)
SLIPS=(0,50)
MMRS=(.005,.01) # hypothetical fixed stress rates, not historical exchange tiers
FEE=base.FEE
def stamp(s):return int(datetime.fromisoformat(s).timestamp())
def mark_bars(year,start,end):
    root=rob.ROOT
    if year==2024:
        files=sorted((root/"BTCUSD/2024_verified_archive/mark_1m").glob("2024-*.csv.gz"))
        files+=sorted((root/"2024_recovery_candidates/BTCUSD").glob("2024-*/mark_1m.csv.gz"))
    else:files=sorted((root/"BTCUSD/institutional/history/mark_1m").glob(f"{year}-*.csv.gz"))
    out=np.full((4,(end-start)//60),np.nan)
    for p in files:
        with gzip.open(p,"rt") as f:
            for row in csv.DictReader(f):
                t=int(row["time"])
                if start<=t<end:
                    assert (t-start)%60==0
                    o,h,l,c=(float(row[k]) for k in ("open","high","low","close"))
                    assert 0<l<=min(o,c)<=max(o,c)<=h and all(math.isfinite(x) for x in (o,h,l,c))
                    out[:,(t-start)//60]=o,h,l,c
    missing=int(np.isnan(out[0]).sum())
    print("MARK_COVERAGE",year,out.shape[1],missing,flush=True)
    assert np.isfinite(out).all(),(year,missing)
    return out
def prepare(trades,bars,marks,start,end,funding,slip):
    ts,fp,missing=funding;out=[]
    for t in trades:
        k=(stamp(t["entry_utc"])-start)//60
        j=min((stamp(t["exit_utc"])-start)//60,len(bars[0])-1)
        d=t["side"];ep=t["entry_price"];xp=t["exit_price"];r=t["initial_risk_points"]
        assert j>=k and t["funding_proxy_cost"] is not None
        # Funding boundaries strictly after entry and before exit, same convention as prior run.
        a=np.searchsorted(ts,start+k*60,side="right")
        b=np.searchsorted(ts,stamp(t["exit_utc"]),side="left");b=max(a,b)
        assert missing[b]==missing[a]
        minute=np.arange(k,j+1,dtype=np.int64)*60+start
        idx=np.clip(np.searchsorted(ts,minute,side="right"),a,b)
        fc=d*(fp[idx]-fp[a])
        assert math.isclose(float(fc[-1]),t["funding_proxy_cost"],abs_tol=1e-6)
        hi=marks[1,k:j+1].copy();lo=marks[2,k:j+1].copy()
        # At known open exit (reversal or stop gap), exclude post-exit minute extremes.
        raw=xp+d*slip
        if t["exit_reason"]=="H4 EMA reversal" or (t["exit_reason"]=="Initial/trailing stop" and d*(bars[0,j]-t["stop_price"])<=0):
            hi[-1]=lo[-1]=marks[0,j]
        good=hi if d==1 else lo;bad=lo if d==1 else hi
        # Before closing, account equity conservatively reserves taker exit fee.
        good_pnl=d*(good-ep)-ep*FEE-good*FEE-fc
        bad_pnl=d*(bad-ep)-ep*FEE-bad*FEE-fc
        # Full entry and intraminute stop-exit bar envelope; touches on these bars
        # are potential, not confirmed liquidations, because event order is unknown.
        out.append(dict(t=t,year=base.dt(start).year,good=good_pnl,bad=bad_pnl,mark_bad=bad,fc=fc,
            net=t["net_points"]-t["funding_proxy_cost"],time=minute,ep=ep,r=r,d=d))
    return out
def size(balance,ep,r,side,lev,risk,slip):
    # Risk budget at modeled initial stop, including both fees and adverse exit slip.
    stop=ep-side*(r+slip)
    planned=r+slip+(ep+stop)*FEE
    desired=balance*risk/planned
    cap=balance/(ep*(1/lev+FEE))
    return min(desired,cap),desired>cap,planned
def mc(returns):
    if not returns:return None
    r=np.asarray(returns);n=len(r);rng=np.random.default_rng(20261128)
    # Circular block bootstrap of historical trade capital returns, 5-trade blocks.
    # No prediction of liquidation, price gaps or changing regimes.
    starts=rng.integers(0,n,size=(5000,math.ceil(n/5)))
    ix=((starts[:,:,None]+np.arange(5))%n).reshape(5000,-1)[:,:n]
    factors=np.maximum(0,1+r[ix])
    eq=np.concatenate([np.ones((5000,1)),np.cumprod(factors,axis=1)],axis=1)
    peak=np.maximum.accumulate(eq,axis=1)
    dd=np.max(1-eq/peak,axis=1)
    return dict(paths=5000,block=5,median_return_pct=float(100*(np.median(eq[:,-1])-1)),
        p05_return_pct=float(100*(np.quantile(eq[:,-1],.05)-1)),p95_closed_dd_pct=float(100*np.quantile(dd,.95)),
        probability_loss_pct=float(100*np.mean(eq[:,-1]<1)),probability_half_capital_pct=float(100*np.mean(eq.min(axis=1)<=.5)),
        probability_50pct_dd_pct=float(100*np.mean(dd>=.5)))
def simulate(items,lev,risk,slip,mmr):
    bal=peak=closed_peak=START_BALANCE;dd=closed_dd=0.;cap_count=0;loss_streak=max_streak=0
    returns=[];year_start={};year_end={};months={};rows=[];breach=None;min_buffer=math.inf
    for x in items:
        t=x["t"];ep=x["ep"];d=x["d"];r=x["r"];year=x["year"]
        year_start.setdefault(year,bal)
        q,capped,planned=size(bal,ep,r,d,lev,risk,slip);cap_count+=int(capped)
        # Isolated margin per BTC. Entry fee is paid from available wallet.
        # Funding paid from position collateral; exit fee reserved conservatively.
        # Breach if mark equity <= maintenance plus estimated exit fee.
        margin_per_btc=ep/lev
        mb=x["mark_bad"]
        buffer=margin_per_btc+d*(mb-ep)-x["fc"]-mb*(mmr+FEE)
        hits=np.flatnonzero(buffer<=0)
        n=int(hits[0])+1 if len(hits) else len(buffer)
        min_buffer=min(min_buffer,float(np.min(buffer[:n]/mb[:n])*100))
        # Worst-case intraminute order: favorable extreme then adverse extreme.
        # This is an upper-bound drawdown envelope, not tick-verified equity.
        highs=bal+q*x["good"][:n];lows=bal+q*x["bad"][:n]
        peaks=np.maximum.accumulate(np.maximum(highs,peak))
        dd=max(dd,float(np.max(1-lows/peaks)));peak=max(peak,float(peaks[-1]))
        if len(hits):
            idx=int(hits[0]);breach=dict(entry_utc=t["entry_utc"],potential_breach_utc=base.dt(int(x["time"][idx])).isoformat(),
                mark=float(mb[idx]),side=d,buffer_per_btc=float(buffer[idx]),entry_or_exit_minute=idx==0 or idx==len(buffer)-1)
            break # no invented liquidation settlement or subsequent trading
        before=bal;bal+=q*x["net"]
        returns.append(bal/before-1);year_end[year]=bal;month=t["entry_utc"][:7];months[month]=months.get(month,0.)+bal-before
        closed_peak=max(closed_peak,bal);closed_dd=max(closed_dd,1-bal/closed_peak);peak=max(peak,bal);dd=max(dd,1-bal/peak)
        loss_streak=loss_streak+1 if bal<before else 0;max_streak=max(max_streak,loss_streak)
        rows.append(dict(entry_utc=t["entry_utc"],exit_utc=t["exit_utc"],quantity_btc=q,balance_before=before,balance_after=bal,
            net_usd=bal-before,margin_usd=q*ep/lev,planned_risk_pct=100*q*planned/before,cap=capped))
        if bal<=0:break
    complete=breach is None and len(rows)==len(items)
    result=dict(leverage=lev,risk_pct=risk*100,slippage_per_side=slip,assumed_mmr_pct=mmr*100,status="complete_no_modeled_breach" if complete else "halted_potential_breach",
        starting_equity=START_BALANCE,ending_equity=bal if complete else None,last_closed_equity=bal,return_pct=100*(bal/START_BALANCE-1) if complete else None,
        completed_trades=len(rows),planned_trades=len(items),margin_capped_entries=cap_count,potential_liquidation=breach,minimum_buffer_pct_of_mark=min_buffer,
        mark_drawdown_upper_bound_pct=100*dd,closed_drawdown_pct=100*closed_dd,max_consecutive_losses=max_streak,
        profitable_entry_months=sum(v>0 for v in months.values()),year_returns_pct={str(y):100*(v/year_start[y]-1) for y,v in year_end.items()},
        monte_carlo=mc(returns) if complete else None)
    return result,rows
def tests():
    rob.tests()
    for lev in LEVERAGES:
        q,c,p=size(100,80000,500,1,lev,.01,50)
        assert q*80000*(1/lev+FEE)<=100+1e-9 and q*p<=1+1e-9
    # A 20x long with a 6% adverse move breaches a 0.5% fixed maintenance model.
    x=dict(t=dict(entry_utc="2026-01-01T00:00:00+00:00",exit_utc="2026-01-01T00:01:00+00:00"),
        year=2026,ep=100.,r=1.,d=1,good=np.array([0.,0.]),bad=np.array([0.,-6.]),mark_bad=np.array([100.,94.]),fc=np.zeros(2),net=-1.,time=np.array([validation.START,validation.START+60]))
    s,_=simulate([x],20,.01,0,.005)
    assert s["potential_liquidation"] is not None and s["ending_equity"] is None
    s,_=simulate([x],2,.01,0,.005)
    assert s["potential_liquidation"] is None and s["completed_trades"]==1
def run():
    tests();OUT.mkdir(parents=True,exist_ok=True)
    periods=((2024,base.data24.START,base.data24.END,base.data24.candles_2024),(2025,base.data25.START,base.data25.END,base.data25.candles),(2026,validation.START,validation.END,validation.candles))
    bars=[base.read_bars(reader,start,end) for year,start,end,reader in periods]
    pack=rob.indicator_pack(np.concatenate(bars,axis=1),(20,50));offset=0;items={s:[] for s in SLIPS}
    expected={2024:31511.67895,2025:12163.06097,2026:35359.04223}
    for (year,start,end,_),b in zip(periods,bars):
        p=rob.slice_pack(pack,offset,b.shape[1]);offset+=b.shape[1]
        f=rob.funding_proxy(year,b,start,end);marks=mark_bars(year,start,end)
        for slip in SLIPS:
            s,ts=rob.replay(b,p,"A",2.,"all",slip,start,end,f)
            if slip==0:assert math.isclose(s["net"],expected[year],abs_tol=1e-6),(year,s["net"])
            items[slip]+=prepare(ts,b,marks,start,end,f,slip)
            print("BASELINE",year,slip,s["trades"],s["net"],flush=True)
    assert len(items[0])==178
    results=[]
    with gzip.open(OUT/"capital_ledgers.jsonl.gz","wt") as f:
        for lev,risk,slip,mmr in itertools.product(LEVERAGES,RISKS,SLIPS,MMRS):
            s,rows=simulate(items[slip],lev,risk,slip,mmr);results.append(s)
            print("RESULT",json.dumps(s,separators=(",",":"),allow_nan=False,default=rob.json_scalar),flush=True)
            f.write(json.dumps(dict(summary=s,trades=rows),separators=(",",":"),allow_nan=False,default=rob.json_scalar)+"\n")
    assert len(results)==80
    (OUT/"results.json").write_text(json.dumps(results,indent=2,allow_nan=False,default=rob.json_scalar))
    (OUT/"provenance.json").write_text(json.dumps(dict(strategy="A exact EMA20/50 15M pullback, H1 trend, H1 ATR14 x2, H4 EMA reversal, continuous indicators, annual accounting close",
        period="2024 Feb1 12 UTC to 2026 Nov1 UTC",capital="hypothetical USD100, fractional BTC, compounding, no minimum lot/tick quantity restriction or exchange tier enforcement",
        risk="fraction of current equity at modeled initial stop including fees and exit slippage; cap by isolated initial margin and entry fee",
        liquidation="historical mark minute extremes; assumed fixed 0.5% and 1% MMR + exit fee reserve; funding proxy deducted from isolated collateral; halt at first potential breach, no fabricated settlement; not exchange-confirmed",
        drawdown="upper-bound mark equity favorable-before-adverse within each minute; entry and intraminute stop exit bar extremes may occur outside holding interval",
        funding="assumed 8h schedule and prior-hour rate, historical mark; actual settlements unverified",
        bootstrap="5000 circular five-trade block resamples of historical closed-trade fractional equity returns, conditional on no historical modeled breach; not probability of actual liquidation or future loss",
        limitations="no lot rounding, verified historical MMR tiers, spread/tick sequence, actual settlement or demo execution; no change to entry/exit parameters"),indent=2))
    print("TOTAL",len(results),"NO_MODELED_BREACH",sum(x["potential_liquidation"] is None for x in results),flush=True)
if __name__=="__main__":run()
