"""Read-only VPS dashboard for four independent asset/venue lanes.

Historical futures backtests are separate from LIVE FORWARD options paper quotes.
Never synthesizes nonexistent historical option premiums or bid/ask.
"""
import csv,json,time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from fastapi import FastAPI,HTTPException
from fastapi.responses import HTMLResponse
from config import Config,ROOT,lane_state
from store import Store

app=FastAPI(title="BTC & ETH Futures vs Options",
            docs_url=None,redoc_url=None,openapi_url=None)
ASSETS={"BTC","ETH"}
LANES=[("BTC","futures"),("BTC","options"),("ETH","futures"),("ETH","options")]
RESEARCH={
  "BTC":ROOT/"analysis"/"btc_ema_st_fixed_10_margin_20261119",
  "ETH":ROOT/"analysis"/"eth_ema_st_fixed10_100x_20261120",
}

def read_lane(cfg,asset,market):
    directory=(cfg.state_dir if asset==cfg.asset and market==cfg.market
               else lane_state(asset,market,cfg.mode))
    path=directory/"bot.sqlite3"
    if not path.is_file():
        return {"asset":asset,"market":market,"state":"not_started",
                "execution":"quote_paper_not_started"}
    db=Store(directory)
    try:
        hb=db.get("heartbeat",{})
        age=round(time.time()-float(hb["now"]),1) if hb.get("now") else None
        good=age is not None and age<20
        is_paper=market=="options" or bool(hb.get("paper")) or (
            db.get("paper_wallet") is not None and not hb.get("trading_enabled",False))
        base={"asset":asset,"market":market,"state":"connected" if good else "offline",
              "mode":cfg.mode,"heartbeat_age_seconds":age,
              "halted":db.get("halted"),
              "market_mark":(db.get("ticker") or {}).get("mark"),
              "latest_signal":db.get("latest_signal"),
              "last_candle":db.get("last_market_bar"),
              "open_position":db.get("paper_position") if is_paper else db.get("active"),
              "events":db.latest_events(12)}
        if is_paper:
            stats=db.get("paper_stats") or {"trades":0,"starting_balance_usd":cfg.portfolio,
                         "closed_equity_usd":cfg.portfolio,"net_profit_usd":0,
                         "profit_factor":None,"max_closed_equity_drawdown_pct":0}
            base.update(execution="quote_based_options_paper" if market=="options" else "quote_based_futures_paper",
                        margin_mode="option_premium_paid_not_leveraged" if market=="options" else "futures_100x_isolated_model",
                        portfolio_closed_equity=stats.get("closed_equity_usd"),
                        paper_cash=db.get("paper_wallet"),
                        paper_bid_equity=db.get("paper_equity_bid_estimate"),
                        fee_model=("0.01% of underlying notional capped at 3.5% premium per leg, plus assumed GST" if market=="options" else "0.05% taker entry and conditional 30min exit waiver; assumed GST and maintenance, zero modeled funding"),
                        statistics=stats,paper_exit_pending=db.get("paper_exit_pending"),
                        trades=db.paper_trades()[-10:])
        else:
            base.update(execution="exchange_demo_live_if_enabled",
                        account_equity_usd=db.get("exchange_equity_usd"),
                        trading_enabled=(hb or {}).get("trading_enabled",False),
                        statistics=db.get("fill_attribution"),
                        fee_model="Exchange reported commissions + modeled GST; funding excluded")
        return base
    finally:db.close()

def exchange_lane(cfg,asset):
    """Optional separate authenticated-futures directory, never reused paper state."""
    directory=lane_state(asset,"futures",cfg.mode).parent/(asset+"_futures_exchange")
    if not (directory/"bot.sqlite3").is_file():return None
    db=Store(directory)
    try:
        hb=db.get("heartbeat",{})
        age=time.time()-float(hb.get("now") or 0)
        return {"asset":asset,"execution":"real_exchange_orders_if_enabled",
                "mode":cfg.mode,"health":"connected" if age<20 else "offline",
                "trading_enabled":bool(hb.get("trading_enabled")),
                "active_position":db.get("active"),
                "pending":db.get("pending"),"halted":db.get("halted"),
                "account_equity_usd":db.get("exchange_equity_usd"),
                "estimated_fill_pnl":db.get("fill_attribution")}
    finally:db.close()

@app.get("/api/exchange-lanes")
def exchange_lanes():
    cfg=Config.read()
    return {"mode":cfg.mode,
            "exchange_lanes":[r for r in (exchange_lane(cfg,a) for a in ("BTC","ETH")) if r],
            "note":"Exchange account figures are not directly comparable to paper fills; these lanes use separate state."}

@app.get("/api/compare")
def compare():
    cfg=Config.read()
    return {
      "mode":cfg.mode,"server_time_utc":datetime.utcnow().isoformat()+"Z",
      "lanes":[read_lane(cfg,a,m) for a,m in LANES],
      "historical_options_available":False,
      "historical_option_blocker":"Missing date/strike/expiry-specific historical Delta option bid/ask quote archive.",
      "comparison_rule":"Both venues act on same causal underlying EMA20/Supertrend signals, 2x ATR and flip/trail exits; ETH trail uses percent-scaled BTC 150/50 references. Futures $10 margin 100x, options $10 total premium+entry fee cap.",
      "warning":"Paper option quotes are not real fills. Historical futures replay uses OHLC, not true mark-price/intrabar execution."}

@app.get("/api/historical")
def historical(asset:str="BTC",window:str="history",offer:str="offer",liquidation:str="threshold"):
    asset=asset.upper()
    if asset not in ASSETS or window not in ("history","recent") or offer not in (
        "offer","nooffer") or liquidation not in ("threshold","bankruptcy"):
        raise HTTPException(400,"Invalid comparison filters")
    if asset=="BTC" and offer=="nooffer":
        return {"available":False,"reason":"BTC original historical run has no no-offer replay; use ETH no-offer sensitivity or rerun BTC fee model."}
    prefix="all_history" if window=="history" else "recent_last_10000_15m"
    key=(prefix+"_"+liquidation if asset=="BTC" else
         prefix+"_original_"+offer+"_"+liquidation)
    directory=RESEARCH[asset]
    summary=directory/"summary.json"
    monthly=directory/(key+"_monthly.csv")
    if not summary.exists() or not monthly.exists():
        return {"available":False,"reason":"Verified futures results missing; run app.py backtest --asset "+asset}
    data=json.loads(summary.read_text())
    with monthly.open(newline="") as f:months=list(csv.DictReader(f))
    stat=data.get(key)
    if not isinstance(stat,dict):
        raise HTTPException(500,"Saved research scenario has unexpected schema")
    return {"available":True,"asset":asset,"market":"futures_backtest",
            "window":window,"offer":offer,"liquidation":liquidation,
            "statistics":stat,"months":months,"settings":data.get("settings"),
            "dates_note":"BTC through 2026-11-18; ETH through 2026-11-17; November partial.",
            "cost_note":"Fees and GST modeled; actual historical Scalper Offer enrollment NOT proven; no funding, spread, slippage or real mark-price liquidation."}

@app.get("/api/paired-forward")
def paired_forward(asset:str="BTC"):
    """Matched underlying signal IDs only; missed options signals remain excluded."""
    asset=asset.upper()
    if asset not in ASSETS:raise HTTPException(400,"Invalid asset")
    cfg=Config.read()
    lanes={}
    for market in ("futures","options"):
        directory=(cfg.state_dir if asset==cfg.asset and market==cfg.market else
                   lane_state(asset,market,cfg.mode))
        if not (directory/"bot.sqlite3").is_file():
            lanes[market]=[];continue
        db=Store(directory)
        try:lanes[market]=db.paper_trades()
        finally:db.close()
    def mapping(market):
        return {str(x["signal_bar_ts"]):x for x in lanes[market]
                if x.get("signal_bar_ts") is not None}
    futures=mapping("futures");options=mapping("options")
    matched=sorted(set(futures)&set(options),key=int)
    pairs=[]
    for bar in matched:
        f=futures[bar];o=options[bar]
        if f.get("side")!=o.get("side"):continue
        pairs.append({"signal_bar_utc":datetime.fromtimestamp(int(bar),
                     tz=ZoneInfo("UTC")).isoformat(),"side":f.get("side"),
                     "option_symbol":o.get("symbol"),
                     "futures_pnl_usd":round(float(f["net_pnl_usd"]),4),
                     "option_pnl_usd":round(float(o["net_pnl_usd"]),4),
                     "difference_option_minus_futures_usd":round(
                         float(o["net_pnl_usd"])-float(f["net_pnl_usd"]),4)})
    return {"asset":asset,"mode":cfg.mode,"matched_trades":len(pairs),
            "futures_total_closed_paper_trades":len(lanes["futures"]),
            "options_total_closed_paper_trades":len(lanes["options"]),
            "futures_total_paper_net_usd":round(sum(float(x["net_pnl_usd"]) for x in lanes["futures"]),4),
            "options_total_paper_net_usd":round(sum(float(x["net_pnl_usd"]) for x in lanes["options"]),4),
            "matched_futures_net_usd":round(sum(x["futures_pnl_usd"] for x in pairs),4),
            "matched_options_net_usd":round(sum(x["option_pnl_usd"] for x in pairs),4),
            "pairs":pairs,
            "note":"Only positions opened on the SAME underlying 15-minute signal candle are paired. Unmatched/skipped entries excluded. Futures modeled 100x isolated liquidation, options modeled bid/ask premium; all results paper-only."}

@app.get("/api/paper-trades")
def paper_trades(asset:str="BTC"):
    asset=asset.upper()
    if asset not in ASSETS:raise HTTPException(400,"Invalid asset")
    cfg=Config.read()
    s=read_lane(cfg,asset,"options")
    rows=s.get("trades",[])
    directory=(cfg.state_dir if asset==cfg.asset and cfg.market=="options"
               else lane_state(asset,"options",cfg.mode))
    if (directory/"bot.sqlite3").exists():
        db=Store(directory)
        try:rows=db.paper_trades()
        finally:db.close()
    months={}
    for item in rows:
        key=item["closed_at_utc"][:7]
        months[key]=months.get(key,0)+float(item["net_pnl_usd"])
    return {"asset":asset,"market":"options_paper","trades":rows,
            "monthly_net_usd":{k:round(v,4) for k,v in sorted(months.items())},
            "note":"Forward observed option ask-entry/bid-exit only, with modeled option fees and 18% GST. No exchange orders or historical options inference."}

HTML=r"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>EMA-ST | Futures vs Options</title>
<style>
:root{color-scheme:dark;--bg:#091320;--surface:#111f30;--surface2:#17283e;--line:#2a3a4e;--txt:#e8f1ff;--mut:#96abc4;--teal:#4cddc4;--good:#53d5a1;--bad:#f07e91;--gold:#f3ca75}
*{box-sizing:border-box}body{margin:0;color:var(--txt);background:radial-gradient(70% 300px at 0% 0%,#12394a,transparent),var(--bg);font:14px/1.55 system-ui,-apple-system,Segoe UI,sans-serif}
.shell{max-width:1280px;margin:auto;padding:25px clamp(14px,3vw,34px) 65px}
.head{display:flex;gap:12px;justify-content:space-between;align-items:center;flex-wrap:wrap;margin-bottom:20px}
.brand{font-size:19px;font-weight:800;letter-spacing:-.4px}.brand span{color:var(--teal)}.subtitle,.muted{color:var(--mut)}.subtitle{font-size:12px}
.pill{border:1px solid var(--line);border-radius:99px;background:var(--surface2);color:var(--mut);padding:5px 12px;font-size:11px;font-weight:bold}
.tabs{display:flex;gap:9px;overflow:auto;border-bottom:1px solid var(--line);padding-bottom:11px;margin-bottom:21px}
.tabs button{border:0;background:transparent;color:var(--mut);padding:10px 12px;border-radius:8px;white-space:nowrap;cursor:pointer}
.tabs .selected{background:var(--surface2);color:#fff;font-weight:700}
h1{font-size:22px;margin:0 0 5px}h2{font-size:17px;margin:0 0 10px}h3{font-size:14px;margin:0 0 4px}
.lead{color:var(--mut);font-size:13px;margin:0 0 18px}
.cards{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:13px}
.card{border:1px solid var(--line);border-radius:13px;background:linear-gradient(160deg,var(--surface),#0e1b2b);padding:17px;min-width:0}
.card .kicker{color:var(--mut);font-size:11px;text-transform:uppercase;letter-spacing:.055em}
.metric{font-size:25px;font-weight:800;letter-spacing:-.7px;margin:7px 0;line-height:1.35}
.kv{display:flex;justify-content:space-between;border-bottom:1px solid var(--line);gap:8px;padding:8px 0}
.kv:last-child{border:0}.kv>span{color:var(--mut)}.kv b{text-align:right;overflow-wrap:anywhere}
.good{color:var(--good)}.bad{color:var(--bad)}.gold{color:var(--gold)}.tag{font-size:10px;border-radius:6px;padding:4px 7px;border:1px solid var(--line);font-weight:bold;letter-spacing:.045em}
section[hidden]{display:none}.panel{margin-top:17px}.note{color:#f2d58f;background:#292416;border:1px solid #6e5834;border-radius:12px;padding:13px 16px;margin:18px 0}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:13px}.selects{display:flex;gap:10px;flex-wrap:wrap;margin:14px 0}
select{background:#17283d;color:#fff;border:1px solid var(--line);padding:9px 12px;border-radius:8px}
.tablewrap{overflow:auto}.tablewrap table{border-collapse:collapse;min-width:730px;width:100%}
td,th{text-align:right;padding:11px 9px;border-bottom:1px solid var(--line);white-space:nowrap;font-variant-numeric:tabular-nums}
td:first-child,th:first-child{text-align:left}th{font-size:11px;color:var(--mut);text-transform:uppercase}
.label{font-size:12px;color:var(--mut)}.plot{display:flex;align-items:end;gap:4px;height:135px;padding:6px 0;margin:14px 0;border-bottom:1px solid var(--line)}
.plot .v{flex:1;min-width:3px;max-width:19px;background:var(--good);border-radius:3px 3px 0 0;position:relative}
.plot .v.neg{background:var(--bad)}.log{font:11px/1.5 ui-monospace,monospace;color:var(--mut);word-break:break-word;border-bottom:1px solid var(--line);padding:8px 0}
footer{margin-top:20px;color:var(--mut);font-size:11px}
@media(max-width:920px){.cards{grid-template-columns:repeat(2,minmax(0,1fr))}.grid2{grid-template-columns:1fr}}
@media(max-width:550px){.shell{padding:15px 12px 50px}.cards{grid-template-columns:1fr 1fr;gap:8px}.card{padding:12px}.metric{font-size:21px}}
</style></head>
<body><div class="shell">
<header class="head"><div><div class="brand"><span>◈</span> EMA + Supertrend <span class="muted">/ Strategy Monitor</span></div>
<div class="subtitle">BTCUSD &amp; ETHUSD · futures versus options · one signal strategy, two execution models</div></div>
<div><span class="pill" id="mode">DEMO</span> <span class="pill">READ-ONLY DASHBOARD</span></div></header>
<nav class="tabs"><button class="selected" data-target="overview">Comparison</button>
<button data-target="history">Futures backtests</button>
<button data-target="paper">Options paper trades</button>
<button data-target="safety">Strategy &amp; safety</button></nav>
<section id="overview">
<h1>Four strategy lanes</h1><p class="lead">Each asset and market has its own state, trade records and hypothetical $100 comparison baseline.</p>
<div class="cards" id="lanes"></div>
<div class="note">Historical options profit is intentionally not displayed: the archive contains underlying futures candles, not dated option contract bid/ask, expiry and strike quotes. Options are evaluated from real-time forward quotes, not fabricated historical premiums.</div>
<div class="card panel"><h2>Matched forward trades — same underlying signal</h2>
<p class="label">Both markets open on the same 15-minute signal. Options may skip illiquid contracts, so also compare total independent trades.</p>
<div class="selects"><select id="paired-asset"><option value="BTC">BTC: futures vs CALL/PUT</option><option value="ETH">ETH: futures vs CALL/PUT</option></select></div>
<div class="cards">
<div class="card"><div class="kicker">Matched trades</div><div class="metric" id="paired-count">—</div></div>
<div class="card"><div class="kicker">Matched futures net</div><div class="metric" id="paired-futures">—</div></div>
<div class="card"><div class="kicker">Matched options net</div><div class="metric" id="paired-options">—</div></div>
<div class="card"><div class="kicker">Option minus futures</div><div class="metric" id="paired-difference">—</div></div>
</div>
<div class="tablewrap"><table><thead><tr><th>Signal UTC</th><th>Side</th><th>Option contract</th><th>Futures net</th><th>Option net</th><th>Difference</th></tr></thead><tbody id="paired-rows"></tbody></table></div>
<p class="label" id="paired-note"></p></div>
<div class="card panel"><h2>Optional Delta exchange demo/live futures</h2>
<p class="label">Actual exchange order lanes use separate dedicated SQLite state, for example state/demo/BTC_futures_exchange. These are NOT part of the four paper portfolios.</p>
<div class="grid2" id="exchange-cards"><div class="label">No exchange-order lanes started</div></div>
</div>
<div class="grid2">
<div class="card"><h2>Historical futures (model)</h2>
<div class="kv"><span>BTCUSD original · $100 →</span><b id="btc-hist">—</b></div>
<div class="kv"><span>ETHUSD original · $100 →</span><b id="eth-hist">—</b></div>
<p class="label">Historical 100× isolated futures, $10 margin, modeled fee offer, liquidation and synthetic 15m OHLC execution. These are not forward comparison profits.</p>
</div><div class="card"><h2>Options forward test</h2>
<div class="kv"><span>BTC CALL/PUT paper net</span><b id="btc-paper">—</b></div>
<div class="kv"><span>ETH CALL/PUT paper net</span><b id="eth-paper">—</b></div>
<p class="label">Fresh ATM option buy at ask; sell at bid. $10 premium budget including estimated entry fee and GST. No real exchange orders.</p>
</div></div>
</section>
<section id="history" hidden>
<h1>Historical futures backtest</h1><p class="lead">Existing research replays with the **liquidation guard removed**. No options price simulation.</p>
<div class="selects"><select id="hist-asset"><option value="BTC">BTCUSD futures</option><option value="ETH">ETHUSD futures</option></select>
<select id="hist-range"><option value="history">Full history</option><option value="recent">Latest 10,000 15m bars (fresh $100)</option></select>
<select id="hist-offer"><option value="offer">Assumed Scalper Offer</option><option value="nooffer">Without offer (ETH only)</option></select>
<select id="hist-liq"><option value="threshold">Estimated liquidation threshold</option><option value="bankruptcy">Bankruptcy-price stress fill</option></select></div>
<div class="cards">
<div class="card"><div class="kicker">Ending wallet</div><div class="metric" id="hist-end">—</div></div>
<div class="card"><div class="kicker">Net profit</div><div class="metric" id="hist-net">—</div></div>
<div class="card"><div class="kicker">Net profit factor</div><div class="metric" id="hist-pf">—</div></div>
<div class="card"><div class="kicker">Modeled liquidations</div><div class="metric" id="hist-liquidations">—</div></div></div>
<div class="card panel"><h2>Monthly results</h2><div class="plot" id="monthlyplot"></div>
<div class="tablewrap"><table><thead><tr><th>Month (IST)</th><th>Trades</th><th>Liquidations</th><th>Net P&amp;L</th><th>Return</th><th>Closing equity</th></tr></thead><tbody id="monthrows"></tbody></table></div>
<p class="label" id="history-note"></p></div>
</section>
<section id="paper" hidden>
<h1>Real-quote options paper results</h1><p class="lead">Both CALL and PUT use the futures underlying signal; option P&amp;L uses ask on entry, bid on exit.</p>
<div class="selects"><select id="paper-asset"><option value="BTC">BTC options</option><option value="ETH">ETH options</option></select></div>
<div class="cards">
<div class="card"><div class="kicker">Closed trades</div><div class="metric" id="paper-count">—</div></div>
<div class="card"><div class="kicker">Net realized paper profit</div><div class="metric" id="paper-net">—</div></div>
<div class="card"><div class="kicker">Profit factor</div><div class="metric" id="paper-pf">—</div></div>
<div class="card"><div class="kicker">Closed-equity drawdown</div><div class="metric" id="paper-dd">—</div></div></div>
<div class="card panel"><h2>Paper option transactions</h2>
<div class="tablewrap"><table><thead><tr><th>Close UTC</th><th>Contract</th><th>Lots</th><th>Entry ask</th><th>Exit bid</th><th>Net P&amp;L</th><th>Exit</th></tr></thead><tbody id="paperrows"></tbody></table></div>
<p class="label">Estimated fees: 0.01% underlying notional capped at 3.5% of premium, plus assumed 18% GST. Requires fresh quotes and sufficient bid/ask depth. Some opportunities may be skipped. Paper outcomes are not guaranteed fills.</p></div>
</section>
<section id="safety" hidden><h1>Same underlying trading logic</h1>
<div class="grid2"><div class="card">
<h2>Signals and exits</h2>
<div class="kv"><span>Underlying timeframe</span><b>15-minute completed candle</b></div>
<div class="kv"><span>Trend</span><b>Established Supertrend(10,3)</b></div>
<div class="kv"><span>Pullback</span><b>EMA20 wick touch, trend-side close</b></div>
<div class="kv"><span>Volume filter</span><b>&gt;= 1.5× prior 20 average</b></div>
<div class="kv"><span>ATR filter</span><b>ATR14 &gt;= prior 20 average</b></div>
<div class="kv"><span>Initial stop</span><b>2× underlying ATR14</b></div>
<div class="kv"><span>Trail BTC</span><b>150 activate, 50 distance</b></div>
<div class="kv"><span>Trail ETH</span><b>0.1875% activate, 0.0625% distance</b></div>
<div class="kv"><span>Other exit</span><b>Opposite Supertrend flip</b></div>
</div><div class="card"><h2>Money management and limitations</h2>
<div class="kv"><span>Futures</span><b>$10 isolated margin, 100×</b></div>
<div class="kv"><span>Options</span><b>Buy CALL/PUT, ≤$10 total debit</b></div>
<div class="kv"><span>Initial liquidation-entry guard</span><b class="gold">OFF (per request)</b></div>
<div class="kv"><span>Pre-liquidation emergency exit</span><b>ON; BTC $1 / ETH entry-relative tick</b></div>
<div class="kv"><span>Futures demo/live</span><b>Authenticated orders, locked by config</b></div>
<div class="kv"><span>Options demo/live</span><b>Paper only, no order writes</b></div>
<p class="label">Removing the liquidation guard allows positions whose 2×ATR stop lies beyond the estimated 100× liquidation barrier. The exchange may liquidate before your stop executes; no guarantee of $10 loss cap during exceptional execution.</p>
<p class="label">Options entries/exits triggered by underlying movement, not by premium stops. Spread, IV, theta and price impact create meaningful divergence. Historical option contract quotes are missing, so no credible historic options returns.</p>
</div></div></section>
<footer>Local-only dashboard · no order API · BTC vs ETH and futures vs options research. Avoid live trading until demo exchange behavior is independently checked.</footer></div>
<script>
const $=x=>document.getElementById(x);
const usd=(v,d=2)=>v==null||!Number.isFinite(Number(v))?"—":(Number(v)<0?"−$":"$")+Math.abs(Number(v)).toLocaleString(undefined,{minimumFractionDigits:d,maximumFractionDigits:d});
const txt=(x,v)=>$(x).textContent=v==null?"—":String(v);
const perc=v=>v==null?"—":Number(v).toFixed(2)+"%";
const num=v=>v==null?"—":Number(v).toFixed(2);
function el(tag,text,className){const x=document.createElement(tag);x.textContent=text;if(className)x.className=className;return x}
async function api(path){const r=await fetch(path,{cache:"no-store"});if(!r.ok)throw Error("HTTP "+r.status);return r.json()}
document.querySelectorAll("[data-target]").forEach(b=>b.addEventListener("click",()=>{
  document.querySelectorAll("[data-target]").forEach(n=>n.classList.toggle("selected",n===b));
  ["overview","history","paper","safety"].forEach(n=>$(n).hidden=n!==b.dataset.target)
}));
function line(label,value){const wrap=el("div","","kv");wrap.append(el("span",label),el("b",value));return wrap}
async function refresh(){
 try{
 const data=await api("/api/compare");txt("mode",data.mode.toUpperCase());
 const parent=$("lanes");parent.replaceChildren();
 for(const lane of data.lanes){
  const card=el("div","","card");
  card.append(el("div",lane.asset+" · "+(lane.market==="futures"?"Futures 100×":"Options CALL/PUT"),"kicker"));
  const status=lane.state==="connected"?"good":lane.state==="offline"?"bad":"muted";
  card.append(el("div",lane.state.replaceAll("_"," ").toUpperCase(),status+" metric"));
  card.append(line("Execution",lane.execution||"—"));
  card.append(line("Open position",lane.open_position?lane.open_position.symbol||lane.asset+"USD":"None / unconfirmed"));
  if(lane.market==="futures" && lane.open_position){
    const p=lane.open_position;
    card.append(line("Liquidation",p.exchange_liquidation_price!=null?
        usd(p.exchange_liquidation_price,2):
        p.liq_proxy!=null?usd(p.liq_proxy,2)+" model":"—"));
    card.append(line("Pre-liq stop",p.preliq_stop!=null?usd(p.preliq_stop,2):"—"));
    card.append(line("Active stop",p.stop!=null?usd(p.stop,2):"—"));
  }
  const paper=String(lane.execution||"").includes("paper");
  card.append(line("Forward net",paper
     ?usd((lane.statistics||{}).net_profit_usd)
     :lane.statistics?usd(lane.statistics.estimated_net_before_funding_usd)+" est.":"—"));
  card.append(line("Closed trades",paper
     ?String((lane.statistics||{}).trades||0)
     :lane.statistics?String(lane.statistics.fills)+" fills":"—"));
  if(lane.market==="options" && lane.open_position)card.append(el("p","Premium at risk; option may expire worthless.","label gold"));
  if(lane.halted)card.append(el("p",String(lane.halted),"bad"));
  parent.append(card);
  if(lane.asset==="BTC"&&lane.market==="options")txt("btc-paper",usd((lane.statistics||{}).net_profit_usd));
  if(lane.asset==="ETH"&&lane.market==="options")txt("eth-paper",usd((lane.statistics||{}).net_profit_usd));
 }
 }catch(err){txt("mode","DASHBOARD ERROR: "+err)}
}
async function loadPaired(){
 try{
 const d=await api("/api/paired-forward?asset="+encodeURIComponent($("paired-asset").value));
 txt("paired-count",d.matched_trades);
 txt("paired-futures",usd(d.matched_futures_net_usd));
 txt("paired-options",usd(d.matched_options_net_usd));
 txt("paired-difference",usd(d.matched_options_net_usd-d.matched_futures_net_usd));
 txt("paired-note","Total closed futures paper trades "+d.futures_total_closed_paper_trades+
     ", options paper trades "+d.options_total_closed_paper_trades+
     ". Total independent futures net "+usd(d.futures_total_paper_net_usd)+
     "; options net "+usd(d.options_total_paper_net_usd)+". "+d.note);
 const body=$("paired-rows");body.replaceChildren();
 d.pairs.slice(-65).reverse().forEach(x=>{
 const tr=el("tr","");
 [x.signal_bar_utc.slice(0,19),x.side,x.option_symbol,
 usd(x.futures_pnl_usd,3),usd(x.option_pnl_usd,3),
 usd(x.difference_option_minus_futures_usd,3)].forEach((v,i)=>
 tr.append(el("td",v,i===5?(x.difference_option_minus_futures_usd>=0?"good":"bad"):"")));
 body.append(tr);
 });
 }catch(e){txt("paired-count","Unavailable");txt("paired-note",String(e))}
}
async function loadExchange(){
 try{
 const data=await api("/api/exchange-lanes");
 const root=$("exchange-cards");root.replaceChildren();
 if(!data.exchange_lanes.length){
   root.append(el("span","No authenticated futures-order lanes are running yet.","label"));return;
 }
 data.exchange_lanes.forEach(s=>{
  const card=el("div","","card");
  card.append(el("h3",s.asset+"USD futures exchange · "+s.health));
  card.append(line("Order writes",s.trading_enabled?"Enabled":"Off"));
  card.append(line("Exchange equity",usd(s.account_equity_usd)));
  card.append(line("Net before funding (estimated)",s.estimated_fill_pnl?
    usd(s.estimated_fill_pnl.estimated_net_before_funding_usd):"—"));
  card.append(line("Position",s.active_position?JSON.stringify(s.active_position):"None"));
  if(s.halted)card.append(el("div",String(s.halted),"bad"));
  root.append(card);
 });
 }catch(e){$("exchange-cards").textContent="Exchange lane status unavailable: "+e}
}
async function loadHistory(){
 const q=new URLSearchParams({asset:$("hist-asset").value,window:$("hist-range").value,
 offer:$("hist-offer").value,liquidation:$("hist-liq").value});
 try{const d=await api("/api/historical?"+q);
 if(!d.available)throw Error(d.reason);
 const s=d.statistics;txt("hist-end",usd(s.ending_portfolio_usd));
 txt("hist-net",usd(s.net_profit_usd));txt("hist-pf",num(s.net_profit_factor));
 txt("hist-liquidations",s.assumed_liquidations);
 txt("history-note",d.dates_note+" "+d.cost_note);
 const table=$("monthrows");table.replaceChildren();const plot=$("monthlyplot");plot.replaceChildren();
 const max=Math.max(1,...d.months.map(x=>Math.abs(Number(x.monthly_return_pct||0))));
 for(const m of d.months){
 const tr=document.createElement("tr");const row=[
  m.month_ist,m.trades,m.liquidations,usd(m.net_profit_usd),
  perc(m.monthly_return_pct),usd(m.closing_balance_usd)];
 row.forEach((v,i)=>tr.append(el("td",v,(i===3||i===4)?(Number(m.net_profit_usd)<0?"bad":"good"):"")));
 table.append(tr);
 const bar=el("div","","v"+(Number(m.net_profit_usd)<0?" neg":""));
 bar.style.height=Math.max(2,100*Math.abs(Number(m.monthly_return_pct||0))/max)+"%";
 bar.title=m.month_ist+": "+perc(m.monthly_return_pct);plot.append(bar);
 }
 if(d.asset==="BTC")txt("btc-hist",usd(s.ending_portfolio_usd));
 else txt("eth-hist",usd(s.ending_portfolio_usd));
 }catch(e){txt("hist-end","Unavailable");txt("hist-net","—");txt("hist-pf","—");
 txt("hist-liquidations","—");txt("history-note",String(e));$("monthrows").replaceChildren();$("monthlyplot").replaceChildren()}
}
async function loadPaper(){
 const asset=$("paper-asset").value;
 try{const [d,c]=await Promise.all([api("/api/paper-trades?asset="+asset),api("/api/compare")]);
 const lane=c.lanes.find(x=>x.asset===asset&&x.market==="options");
 const s=(lane||{}).statistics||{};txt("paper-count",s.trades||0);
 txt("paper-net",usd(s.net_profit_usd||0));txt("paper-pf",num(s.profit_factor));
 txt("paper-dd",perc(s.max_closed_equity_drawdown_pct||0));
 const body=$("paperrows");body.replaceChildren();
 d.trades.slice(-70).reverse().forEach(t=>{const row=el("tr","");
  [t.closed_at_utc.slice(0,19),t.symbol,t.contracts,
   usd(t.option_buy_ask,2),usd(t.option_exit_bid,2),usd(t.net_pnl_usd,3),t.reason].forEach((v,i)=>
    row.append(el("td",v,i===5?(Number(t.net_pnl_usd)<0?"bad":"good"):"")));
  body.append(row);
 });
 }catch(e){txt("paper-net",String(e))}
}
["hist-asset","hist-range","hist-offer","hist-liq"].forEach(x=>$(x).addEventListener("change",loadHistory));
$("paper-asset").addEventListener("change",loadPaper);
$("paired-asset").addEventListener("change",loadPaired);
refresh();loadHistory();loadPaper();loadPaired();loadExchange();
setInterval(refresh,5000);setInterval(loadPaper,15000);setInterval(loadPaired,15000);setInterval(loadExchange,15000);
</script></body></html>"""

@app.get("/",response_class=HTMLResponse)
def homepage():
    return HTMLResponse(HTML,headers={"Cache-Control":"no-store",
        "Content-Security-Policy":"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; object-src 'none'; frame-ancestors 'none'",
        "X-Content-Type-Options":"nosniff","Referrer-Policy":"no-referrer"})
