#!/usr/bin/env python3
"""Count +0.118% BTC move before exit, two green-confirmation strategies.

Full 1m replay: 300-point hard SL, 1200-point fixed TP, 15m ST close stop.
Volume >= 1.0x and prior-completed-15m ATR% >= 0.20%. Pessimistic OHLC
collision: hard-stop-before-target in ambiguous stop minute.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import json
import research_supertrend_15m_line_touch as base
import research_supertrend_15m_filter_grid as filt
import research_supertrend_15m_profit_protection as protect
import research_supertrend_15m_second_green as green

OUT=Path("analysis/green_0118pct_before_exit_20261122")
PERCENT=.118

def count(entries, trades, high, opening, slippage, mode):
    assert len(entries)==len(trades)
    result=[]
    for orig, row in zip(entries,trades.itertuples()):
        cycle,bar,j,mid,line=orig
        assert cycle==row.cycle and j==row.entry_index
        k=int(row.exit_index)
        raw_target=mid*(1+PERCENT/100)
        fill=mid+slippage
        fill_target=fill*(1+PERCENT/100)
        # A market-at-open entry can see highs from the entry minute.
        # Exit-minute high is post-exit for stop/close-at-open; exclude it,
        # unless the EXIT opening itself was >= threshold.
        # For a fixed take-profit, the exit-minute high was before the exit
        # (provided stop-first replay did not choose a stop).
        limit= k+1 if row.reason=="take_profit" else k
        maxhi=float(np.max(high[j:limit])) if limit>j else -np.inf
        oexit=float(opening[k])
        # A standing prior protective stop would be checked here too but
        # selected protection mode is OFF for this user's matched settings.
        raw=(maxhi>=raw_target or
            (row.reason!="take_profit" and oexit>=raw_target))
        eff=(maxhi>=fill_target or
            (row.reason!="take_profit" and oexit>=fill_target))
        result.append(dict(entry_kind=mode,cycle=cycle,entry_index=j,
              exit_index=k,entry_mid=mid,entry_fill=fill,
              target_price_mid=round(raw_target,5),
              target_price_fill=round(fill_target,5),
              reached_0118pct_mid_before_exit=int(raw),
              reached_0118pct_fill_before_exit=int(eff),
              exit_reason=row.reason,
              month_ist=row.month_ist))
    return pd.DataFrame(result)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    minute,bar15,files=base.load()
    st,trend=base.supertrend(bar15)
    vol,atr_pct,atr_rel=filt.build_features(bar15)
    events,stops=filt.candidate_touch_events(
         minute,bar15,st,trend,vol,atr_pct,atr_rel)
    vn,an="vol_ge_1p0","atrpct_ge_0p20"
    vs=filt.VOLUME[vn]; ats=filt.VOLATILITY[an]
    first_touch=protect.select_events(events,vs,ats)
    after_touch=green.after_touch_green(first_touch,bar15,trend,stops,
                    minute.open.to_numpy(float))
    after_flip=green.after_flip_green(bar15,trend,vol,atr_pct,atr_rel,vs,ats,
                    stops,minute.open.to_numpy(float))
    h=minute.high.to_numpy(float)
    op=minute.open.to_numpy(float)
    arr=(h,minute.low.to_numpy(float),op,
        minute.close.to_numpy(float),minute.index)
    months=minute.index.tz_convert("Asia/Kolkata").strftime("%Y-%m").to_numpy()
    results=[]
    for name,entries,expected in [
       ("after_bullish_flip",after_flip,197),
       ("after_line_touch",after_touch,108)]:
        t=green.market_replay(entries,stops,arr,
                       300,1200,"off",months)
        t=t[t.month_ist.isin(base.MONTHS)].reset_index(drop=True)
        e=[x for x in entries if months[x[2]] in base.MONTHS]
        assert len(t)==expected==len(e),(name,len(t),len(e),expected)
        a=count(e,t,h,op,base.SLIP,name)
        results.append(a)
    allhits=pd.concat(results,ignore_index=True)
    stat=allhits.groupby("entry_kind").agg(
       trades=("cycle","count"),
       hit_mid=("reached_0118pct_mid_before_exit","sum"),
       hit_fill=("reached_0118pct_fill_before_exit","sum")).reset_index()
    stat["pct_mid"]=(100*stat.hit_mid/stat.trades).round(2)
    stat["pct_fill"]=(100*stat.hit_fill/stat.trades).round(2)
    stat["not_hit_fill"]=stat.trades-stat.hit_fill
    assert len(stat)==2
    stat.to_csv(OUT/"result_summary.csv",index=False)
    allhits.to_csv(OUT/"per_trade_0118pct.csv",index=False)
    details={
     "percent_gross_favorable_move":PERCENT,
     "source":"Delta India BTCUSD 1m Jan2025-Oct2026",
     "entries":"Green second 15m after bullish flip / after first ST support touch",
     "onward_fill":"Third 15m candle open, entry fill mid +5 BTC points",
     "filters":"vol >=1x, 15m ATR14 >=0.20pct (prior completed bar)",
     "exit":"300 point hard SL, 1200 point TP, 15m Supertrend closing stop",
     "profit_protection":"off",
     "collision_handling":"hard SL first if same 1m hit SL and percentage",
     "count_definition":"reached 0.118% over entry execution price before exit",
     "verification":"197 flip vs 108 touch, same setup used in prior verified report",
     "caveat":"Same-minute high/low unobservable; conservative stop-first; no funding",
     "summary":stat.to_dict(orient="records")
    }
    (OUT/"RESEARCH_REPORT.md").write_text(
       "# BTCUSD after flip vs after touch: 0.118% before exit\n\n"
       "## Counts\n"+stat.to_markdown(index=False)+
       "\n\nPercent counted from slippage-adjusted entry fill, with raw mid"
       " counts separately for cross-check. Exit conditions: 300pt hard SL,"
       " 1200pt TP, plus 15m close-stop. Same minute hard stop takes"
       " precedence when ordering ambiguous.\n")
    (OUT/"quality.json").write_text(json.dumps(details,indent=2)+"\n")
    print("VERIFIED_0_118_PERCENT_COUNTS\n"+stat.to_string(index=False),flush=True)

if __name__=="__main__":
    main()
