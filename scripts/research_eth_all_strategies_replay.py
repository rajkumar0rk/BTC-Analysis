#!/usr/bin/env python3
"""Replay BTC-Analysis rule engines on ETHUSD in an isolated, price-normalized sandbox.

No original BTC research file, BTC automation, or live trading system is edited.
The ETH USD OHLCV source is verified against its committed SHA256 manifest.
ETH prices are multiplied by one FIXED BTC/ETH price ratio from 2025-01-01
00:00 UTC before entering unmodified BTC-coded price-point engines.
Thus a BTC legacy stop of 200 virtual points corresponds to 200 / ratio
USD of actual ETH, and adverse 5 virtual points equals 5 / ratio ETH USD.
The fixed ratio is set using only initial prices, never future prices.
Percent fees (0.05% taker per side + GST 18%) remain unchanged.

Caution: fixed-scale ETH reparameterization is NOT an exact recreation
of unscaled BTCUSD point levels or actual ETH fills/slippage.
Scripts using BTC-specific funding/OI/spot history need separate
instrument-specific adapters and are not silently run against BTC data.
Outputs of script failures are retained as failures, never converted to
successful backtests. Score 22 completed IST months Jan2025–Oct2026 only.
"""
import argparse, json, hashlib, subprocess, time, os, sys, shutil, tempfile
from pathlib import Path
from collections import defaultdict
import pandas as pd
import numpy as np

ROOT=Path(__file__).resolve().parent.parent
OUTROOT=ROOT/"analysis"/"ethusd_all_strategy_replay"
MONTHS=pd.period_range("2025-01","2026-10",freq="M").astype(str).tolist()
SUITES={
 "price_structures":[
  "research_structure_rr_stage11.py",
  "research_pretrend_market_state_stage12.py",
  "research_trend_pullback_breakout_stage13.py",
  "research_monthly_regime_stage14.py",
  "research_july_drawdown_stage15.py",
  "research_monthly_regime_switch_stage16.py",
  "research_swing_donchian_stage17.py",
  "research_new_1h_patterns_stage19.py",
  "research_monthly_portfolio_stage18.py",
  "research_three_sleeve_stage20.py",
  "research_monthly_fixed_weight_stage21.py",
 ],
 "high_frequency":[
  "research_every_candle_200.py",
  "research_time_day_volume_200.py",
  "research_anytime_volume_volatility_patterns.py",
  "research_adaptive_anytime_entries_stage9.py",
  "research_dynamic_exit_stage10.py",
 ],
 "time_day":[
  "research_one_trade_every_day_200.py",
  "research_time_day_strategies.py",
  "research_price_action_time_day.py",
  "research_selective_big_moves.py",
  "research_daily_200_500_points.py",
 ],
 "five_minute":[
  "research_monthly_10pct_stage19.py",
  "research_signal_inversion_stage20.py",
 ],
 "other_systems":[
  "research_retest_reclaim_stage4.py",
  "research_volatility_scaled_exits_stage5.py",
  "research_directional_acceptance.py",
  "research_behavioral_discovery.py",
  "research_failed_auction_stage24.py",
 ],

}
EXCLUDED_WITH_REASON={
 "research_market_neutral_carry.py":"Requires authentic ETH spot versus ETH perpetual hedge plus observed ETH funding cashflows; BTC spot must not substitute",
 "research_intraday_spread.py":"Requires valid ETH bid/ask/order-book spread; OHLCV is not order book",
 "analyze_first_forward_arbitrage.py":"Requires venue-specific current ETH arbitrage books and funding, not a historical OHLC-only strategy",
 "collect_delta_institutional_data.py":"Data collection, not a strategy backtest",
 "collect_market_microstructure.py":"Live data collection, not a strategy backtest",
 "sync_delta_btcusd_1m.py":"Download/repair utility, not a strategy",
 "research_trade_counts_stage22.py":"BTC original-artifact trade audit; ETH equivalent is derived from ETH-specific original trade ledgers",
 "research_wide_monthly_stage23.py":"Requires merged ETH-specific Stage19 5m, Stage20 inverse, Stage16, Stage17, Stage18 and Stage19 1H artifacts; run after the independent ETH suites complete",
 "analyze_delta_mtf_institutional.py":"Needs ETH OI/mark/funding and price harmonization before attribution",
 "analyze_institutional_regimes.py":"Needs instrument-specific ETH OI/mark/funding and price harmonization",
 "analyze_1m_exit_methods.py":"Study of old 1m stop/TP, needs ETH-specific normalized execution adapter",
 "research_stage12_monthly.py":"Supplementary monthly analysis using precomputed source results; hold until source backtests available",
 "research_stage24_failed_auction.py":"Alternate wrapper for Stage24, already replayed via research_failed_auction_stage24.py"
}
ARTIFACT_OUTPUTS={
 "research_swing_donchian_stage17.py":"institutional_discovery_stage17_swing_breakout",
 "research_new_1h_patterns_stage19.py":"institutional_discovery_stage19_new_1h_patterns",
 "research_failed_auction_stage24.py":"institutional_discovery_stage24_failed_auction",
 "research_structure_rr_stage11.py":"institutional_discovery_stage11_structure_rr",
 "research_monthly_regime_stage14.py":"institutional_discovery_stage14_monthly_regimes",
 "research_july_drawdown_stage15.py":"institutional_discovery_stage15_july_loss_controls",
 "research_monthly_regime_switch_stage16.py":"institutional_discovery_stage16_monthly_regime_switch",
 "research_monthly_portfolio_stage18.py":"institutional_discovery_stage18_monthly_dual_strategy",
 "research_three_sleeve_stage20.py":"institutional_discovery_stage20_three_sleeve",
 "research_monthly_fixed_weight_stage21.py":"institutional_discovery_stage21_monthly_perfect_search",
 "research_monthly_10pct_stage19.py":"institutional_discovery_stage19_monthly_10pct",
 "research_signal_inversion_stage20.py":"institutional_discovery_stage20_inverse_direction",
}
MONTHLY_CATALOG=[
 ("institutional_discovery_stage24_failed_auction","all_monthly.csv",["mult","rr","hold"],"net_account_return_pct","trades","winning_trades","losing_trades"),
 ("institutional_discovery_stage17_swing_breakout","monthly_mark_to_market.csv",["model"],"month_return_pct",None,None,None),
 ("institutional_discovery_stage19_new_1h_patterns","monthly_results.csv",["model"],"modeled_return_pct","trades",None,None),
 ("institutional_discovery_stage18_monthly_dual_strategy","monthly_blended_returns.csv",["name"],"portfolio_pct",None,None,None),
 ("institutional_discovery_stage20_three_sleeve","selected_month_by_month.csv",["variant"],"portfolio_month_pct",None,None,None),
 ("institutional_discovery_stage19_monthly_10pct","monthly_net_account_returns.csv",["pattern","trend_filter","stop_mode","reward_R","hold_min","target_trade_risk_pct","max_notional_leverage"],"net_account_return_pct","trades",None,None),
 ("institutional_discovery_stage20_inverse_direction","monthly_results.csv",["pattern","direction_mode","entry_filter","stop_mode","target_R","hold_min","risk_fraction_pct","max_leverage","cost_mode"],"account_return_pct","trades",None,None),
 ("institutional_discovery_stage16_monthly_regime_switch","monthly_results.csv",["profile","guard"],"modeled_equity_return_pct","trades",None,None),
]

def prepare_data(work,output):
    src=ROOT/"data/delta_india/ETHUSD/1m"
    manifest=json.loads((src/"manifest.json").read_text())
    partitions=[p for p in manifest["partitions"] if p["file"].endswith(".csv.gz")]
    if len(partitions)<23:raise AssertionError("ETH has fewer than 23 partitions")
    for p in partitions:
        if not (src/p["file"]).exists():
            raise AssertionError("ETH partition missing: "+p["file"])
        if hashlib.sha256((src/p["file"]).read_bytes()).hexdigest()!=p["sha256_gzip"]:
            raise AssertionError("ETH source SHA does not match manifest: "+p["file"])
        if p["missing_minutes"]!=0:
            raise AssertionError("ETH source missing candles: "+p["file"])
    def opening(directory):
        x=pd.read_csv(directory/"2025-01.csv.gz",compression="gzip",nrows=1,
                      usecols=["time","open"])
        return int(x.time.iat[0]),float(x.open.iat[0])
    eth_time,eth0=opening(src)
    btctime,btc0=opening(ROOT/"data/delta_india/BTCUSD/1m")
    if eth_time!=btctime or eth0<=0 or btc0<=0:
        raise AssertionError("2025-01-01 ETH/BTC opening times differ")
    ratio=btc0/eth0
    dst=work/"data/delta_india/BTCUSD/1m"
    dst.mkdir(parents=True,exist_ok=True)
    total=0
    start=None;end=None
    for p in partitions:
        x=pd.read_csv(src/p["file"],compression="gzip")
        if len(x)!=p["observed_candles"]:
            raise AssertionError("Mismatch observed candles in "+p["file"])
        for price_field in ["open","high","low","close"]:
            if price_field not in x:raise AssertionError("Missing "+price_field)
            x[price_field]=x[price_field].astype(float)*ratio
        if "time" not in x: raise AssertionError("time missing")
        unix=x.time.to_numpy("int64")
        if not np.all(np.diff(unix)==60):
            raise AssertionError("ETH minute timestamp gap within "+p["file"])
        if start is None:start=int(unix[0])
        end=int(unix[-1]);total+=len(x)
        x.to_csv(dst/p["file"],index=False,compression="gzip",
                 float_format="%.10f")
    # preserve provenance but never pass BTC institutional data; source
    # aliases to ETH normalized 1m prices ONLY.
    meta=dict(original_symbol="ETHUSD",source_branch="main",
        source_manifest="data/delta_india/ETHUSD/1m/manifest.json",
        normalized_virtual_symbol="BTCUSD sandbox alias (ETH prices scaled)",
        reference_utc="2025-01-01T00:00:00Z",
        reference_eth_open_usd=eth0,reference_btc_open_usd=btc0,
        fixed_multiplier=ratio,
        virtual_5_point_slippage_as_actual_eth_usd=5/ratio,
        virtual_200_point_stop_as_actual_eth_usd=200/ratio,
        total_eth_1m_rows=total,utc_first=start,utc_last=end,
        fee_model="0.05% taker each side, 18% GST on fees",
        monthly_target="2025-01 through 2026-10 IST, excluding partial November",
        limitations=[
            "Fixed ex-ante price normalization preserves BTC-coded absolute point thresholds in virtual units rather than forcing them on unscaled ETH prices",
            "Individual model labels may still print BTCUSD; data used is ETHUSD",
            "ETH order-book spreads, actual funding, maker fills, contract step sizes, liquidation and market impact not provided",
            "Fixed 5 virtual point adverse slippage is a proxy, not measured actual ETH execution",
            "Models may have hard-coded BTC-specific volume or OI assumptions; record these as limitations",
            "No on-chain or spot/perp cross-market hedging is inferred",
            "No guarantee of future profitability"])
    (output/"ETH_DATA_PROVENANCE.json").write_text(json.dumps(meta,indent=2))
    return meta

def run_one(work, filename, timeout_s):
    script=ROOT/"scripts"/filename
    cmd=[sys.executable,str(script)]
    src=work/"analysis/institutional_discovery_stage14_monthly_regimes"
    if filename in ("research_july_drawdown_stage15.py",
                    "research_monthly_regime_switch_stage16.py"):
        cmd.extend(["--original-artifact",str(src)])
    if filename=="research_monthly_portfolio_stage18.py":
        stage15=work/"analysis/institutional_discovery_stage15_july_loss_controls/variant_trade_ledger.csv.gz"
        cmd.extend(["--stage15-ledger",str(stage15)])
    env=os.environ.copy()
    env["PYTHONUNBUFFERED"]="1"
    env["NUMBA_CACHE_DIR"]=str(work/"numba_cache")
    st=time.monotonic()
    try:
        p=subprocess.run(cmd,cwd=work,text=True,stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,timeout=timeout_s,env=env)
        status="completed" if p.returncode==0 else "failed"
        log=p.stdout
        reason="" if p.returncode==0 else f"exit_code={p.returncode}"
    except subprocess.TimeoutExpired as ex:
        status="timed_out"
        log=(ex.stdout or b"").decode(errors="replace") if isinstance(ex.stdout,bytes) else ex.stdout or ""
        reason=f"Exceeded {timeout_s} seconds"
    duration=round(time.monotonic()-st,2)
    return dict(script=filename,status=status,elapsed_seconds=duration,
        reason=reason,log_tail=log[-5000:])

def copy_result_summaries(work,output,script):
    before=work/"analysis"
    if not before.exists():return
    for folder in before.iterdir():
        if not folder.is_dir():continue
        target=output/"source_results"/folder.name
        target.mkdir(parents=True,exist_ok=True)
        # Don't commit gigabytes of trial ledgers; retain available
        # summary CSVs and full quality/research reports.
        preferred=[
            "quality.json","RESEARCH_REPORT.md","selected_22_months.csv",
            "all_monthly.csv","selected_monthly_results.csv",
            "selected_month_by_month.csv","selected_monthly.csv",
            "selected_monthly_returns.csv","monthly_mark_to_market.csv",
            "monthly_results.csv","month_by_month.csv",
            "yearly_trade_win_loss_summary.csv","2025_only_ranking.csv",
            "strategy_summary.csv","strategy_results.csv",
            "2025_selected_rank_with_2026_checks.csv",
            "selected_weight_allocations.csv","top_2025_ranked_models.csv",
            "ranked_by_2025_then_recheck_2026.csv","selected_portfolios.csv",
            "all_combinations.csv","top_2025_ranked.csv",
            "config_comparison.csv","2025_ranked_standard.csv",
        ]
        for name in preferred:
            fp=folder/name
            if fp.exists() and fp.stat().st_size<10_000_000:
                shutil.copy2(fp,target/name)

def score_months(work,output):
    found=[]
    for folder,file,keys,ret,trcol,wcol,lcol in MONTHLY_CATALOG:
        p=work/"analysis"/folder/file
        if not p.exists():continue
        try:
            d=pd.read_csv(p)
            required=["month_ist",ret,*keys]
            if any(c not in d.columns for c in required):continue
            d=d[d.month_ist.isin(MONTHS)].copy()
            # The scripts sometimes supply duplicate variants or multiple
            # extraneous months; only exact complete 22-month groups count.
            candidates=[]
            for param,g in d.groupby(keys,dropna=False,sort=False):
                g=g.sort_values("month_ist")
                if g.month_ist.tolist()!=MONTHS:continue
                v=g[ret].to_numpy(float)
                if not np.isfinite(v).all():continue
                p25=int((v[:12]>1.e-7).sum())
                p26=int((v[12:]>1.e-7).sum())
                rc25=float(100*(np.prod(1.+v[:12]/100)-1))
                rc26=float(100*(np.prod(1.+v[12:]/100)-1))
                tr=int(g[trcol].sum()) if trcol in d.columns else None
                wins=int(g[wcol].sum()) if wcol in d.columns else None
                losses=int(g[lcol].sum()) if lcol in d.columns else None
                candidates.append(dict(folder=folder,model=":".join(map(str,param if isinstance(param,tuple) else [param])),
                    positive_months_2025=p25,positive_months_2026=p26,
                    net_2025_pct=round(rc25,4),net_2026_pct=round(rc26,4),
                    total_closed_trades=tr,wins=wins,losses=losses,
                    monthly_ret=v))
            # Rank by 2025 only, then report 2026 out-of-selection;
            # no future-month hindsight is used for candidate choice.
            ranked=sorted(candidates,
                key=lambda a:(a["positive_months_2025"],a["net_2025_pct"]),
                reverse=True)
            if ranked:
                b=ranked[0]
                report={k:v for k,v in b.items() if k!="monthly_ret"}
                report["models_with_full_22_months"]=len(candidates)
                report["any_22_positive_historical"]=sum(
                    a["positive_months_2025"]==12 and a["positive_months_2026"]==10
                    for a in candidates)
                report["selected_by"]="2025 only: profitable months, then 2025 compounded return"
                found.append(report)
                rows=[]
                for i,m in enumerate(MONTHS):
                    rows.append(dict(model=b["model"],month_ist=m,
                        net_account_return_pct=round(float(b["monthly_ret"][i]),6)))
                pd.DataFrame(rows).to_csv(output/(folder+"_selected_22_months.csv"),index=False)
        except Exception as e:
            found.append(dict(folder=folder,scoring_error=str(e)[:500]))
    (output/"summaries.json").write_text(json.dumps(found,indent=2))
    return found

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--suite",choices=SUITES,required=True)
    a.add_argument("--per-script-timeout-seconds",type=int,default=1500)
    args=a.parse_args()
    out=OUTROOT/args.suite
    out.mkdir(parents=True,exist_ok=True)
    (out/"REQUESTED_STRATEGIES.json").write_text(json.dumps(
        dict(suites=SUITES,excluded=EXCLUDED_WITH_REASON),indent=2))
    work=Path(tempfile.mkdtemp(prefix="eth_replay_"))
    try:
        quality=prepare_data(work,out)
        runs=[]
        for filename in SUITES[args.suite]:
            print("START ETH NORMALIZED "+filename,flush=True)
            result=run_one(work,filename,args.per_script_timeout_seconds)
            runs.append(result)
            print("END "+result["status"]+" "+filename+" "+result["reason"],flush=True)
            (out/"engine_execution_results.json").write_text(json.dumps(runs,indent=2))
            copy_result_summaries(work,out,filename)
            score_months(work,out)
        found=score_months(work,out)
        catalog=dict(suite=args.suite,instrument="ETHUSD",
            provenance=quality,
            attempted=len(runs),
            completed=sum(x["status"]=="completed" for x in runs),
            failures=[dict(script=x["script"],status=x["status"],
                reason=x["reason"]) for x in runs if x["status"]!="completed"],
            engine_replays=runs,monthly_result_summaries=found)
        (out/"RUN_REPORT.json").write_text(json.dumps(catalog,indent=2))
        lines=[f"# ETHUSD — {args.suite} strategy family backtest",
            "","BTC-Analysis native rule engines replayed on ETHUSD",
            "via a fixed initial BTC/ETH price-normalization factor.",
            "Original BTC source and prior reports were NOT changed.",
            f"Fixed normalization factor: {quality['fixed_multiplier']:.8f}",
            f"5 virtual price points of slippage = {quality['virtual_5_point_slippage_as_actual_eth_usd']:.5f} actual ETH USD",
            "Fees: modeled 0.05% taker on each side plus 18% GST on fees",
            "Target: 22 complete IST months Jan2025–Oct2026; November excluded.",
            "",
            "## Engine status"]
        for q in runs:
            lines.append(f"- {q['script']}: **{q['status']}**, {q['elapsed_seconds']}s"+
                ((" — "+q["reason"]) if q["reason"] else ""))
        lines+=["","## Completed source backtest model summaries",""]
        for z in found:
            lines.append("- "+z["folder"]+": "+str(z))
        lines+=["","## Limitations"]+["- "+v for v in quality["limitations"]]
        (out/"RESEARCH_REPORT.md").write_text("\n".join(lines)+"\n")
        print("ETH_SUITE_COMPLETE "+json.dumps(dict(suite=args.suite,
           attempted=len(runs),completed=catalog["completed"],
           summaries=found))[:6500],flush=True)
    finally:
        shutil.rmtree(work,ignore_errors=True)

if __name__=="__main__":
    main()
