"""Read-only local dashboard. NEVER serves orders, credentials, or config mutations."""
import csv,json,time
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from config import Config,ROOT
from store import Store

app=FastAPI(title="BTC Strategy VPS Monitor",docs_url=None,redoc_url=None,openapi_url=None)

@app.get("/api/status")
def status():
    cfg=Config.read()
    db=Store(cfg.state_dir)
    try:
        heart=db.get("heartbeat",{})
        age=round(time.time()-heart["now"],1) if heart.get("now") else None
        return dict(
            mode=cfg.mode,trading=cfg.trading,margin=cfg.margin,
            leverage=cfg.leverage,portfolio_budget=cfg.portfolio,
            heartbeat_age_seconds=age,connected=age is not None and age<max(20,cfg.poll*4),
            halted=db.get("halted"),position=db.get("active"),pending=db.get("pending"),
            exchange_product=db.get("product"),ticker=db.get("ticker"),
            signal=db.get("latest_signal"),last_candle=db.get("last_market_bar"),
            daily=db.get("daily_snapshot"),
            exchange_equity_usd=db.get("exchange_equity_usd"),
            fill_attribution=db.get("fill_attribution"),
            fills_synced_at=db.get("fills_synced_at"),
            alert_count=sum(1 for r in db.latest_events(100) if r["level"]=="ERROR"),
            events=db.latest_events(80))
    finally:db.close()

RESULT_DIR=ROOT/"analysis"/"btc_ema_st_fixed_10_margin_20261119"
VALID_WINDOWS={
    "history":"all_history",
    "recent":"recent_last_10000_15m"
}
VALID_FILLS={"threshold","bankruptcy"}

@app.get("/api/backtest")
def backtest(window:str="history",liquidation:str="threshold"):
    if window not in VALID_WINDOWS or liquidation not in VALID_FILLS:
        return {"error":"Invalid preset"}
    name=VALID_WINDOWS[window]+"_"+liquidation
    path=RESULT_DIR/(name+"_monthly.csv")
    summary=RESULT_DIR/"summary.json"
    if not path.is_file() or not summary.is_file():
        return {"error":"Run python app.py backtest first to generate historical results"}
    with path.open(newline="") as f:
        months=list(csv.DictReader(f))
    data=json.loads(summary.read_text())
    return dict(period=window,liquidation=liquidation,
                last_updated="Local historical model (not live P&L)",
                statistics=data.get(name,{}),months=months,settings=data.get("settings",{}))

HTML=r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>BTC Strategy · VPS</title>
<style>
:root{color-scheme:dark;--bg:#0b1120;--panel:#111c2c;--panel2:#16253a;--line:#26384e;--text:#f1f5fd;--muted:#94a5be;--accent:#5bdbcb;--ok:#47d7a1;--bad:#fa7989;--warn:#f3c978}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(ellipse 85% 40% at 5% -9%,#123449 0%,transparent 70%),var(--bg);color:var(--text);font:14px/1.55 Inter,system-ui,-apple-system,Segoe UI,sans-serif}
a{color:var(--accent)}.app{max-width:1250px;margin:auto;padding:26px clamp(16px,3vw,38px) 65px}.top{display:flex;justify-content:space-between;gap:15px;align-items:flex-start;flex-wrap:wrap;margin-bottom:28px}
.logo{font-size:20px;letter-spacing:-.5px;font-weight:780}.logo .symbol{color:var(--accent)}.sub{color:var(--muted);font-size:12px;margin-top:4px}
.status{display:flex;align-items:center;gap:9px;flex-wrap:wrap}.chip{border-radius:50px;border:1px solid var(--line);padding:5px 11px;background:#1b2d40;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.06em}
.chip.good{color:var(--ok);border-color:#285846}.chip.bad{color:var(--bad);border-color:#703b4a}.chip.warn{color:var(--warn);border-color:#715b35}
.nav{display:flex;gap:7px;margin-bottom:22px;border-bottom:1px solid var(--line);padding-bottom:12px}.nav button{border:0;color:var(--muted);background:transparent;border-radius:8px;padding:10px 15px;cursor:pointer;font:inherit}
.nav button.on{background:var(--panel2);color:var(--text);font-weight:700}
h1{font-size:23px;margin:0 0 3px;letter-spacing:-.5px}h2{font-size:17px;margin:0 0 12px;letter-spacing:-.3px}.muted{color:var(--muted)}.small{font-size:12px}
.grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin-bottom:22px}.card{background:linear-gradient(155deg,var(--panel),#101a29);border:1px solid var(--line);border-radius:14px;padding:20px}
.metric-label{color:var(--muted);font-size:12px}.metric{font-size:29px;letter-spacing:-1px;font-weight:780;line-height:1.3;margin-top:8px}.good-txt{color:var(--ok)}.bad-txt{color:var(--bad)}
.split{display:grid;grid-template-columns:1.05fr .95fr;gap:14px;margin-bottom:22px}.line{display:flex;justify-content:space-between;gap:10px;padding:8px 0;border-bottom:1px solid #243347}.line:last-child{border:0}
.line strong{text-align:right;overflow-wrap:anywhere}table{width:100%;border-collapse:collapse;min-width:600px;font-variant-numeric:tabular-nums}th,td{text-align:right;padding:10px;border-bottom:1px solid #27364b;white-space:nowrap}
th:first-child,td:first-child{text-align:left}th{font-size:11px;letter-spacing:.07em;color:var(--muted);text-transform:uppercase}td{font-size:13px}.tablewrap{overflow:auto}
select{background:#192a3e;color:var(--text);border:1px solid var(--line);padding:10px 12px;border-radius:8px}.filters{display:flex;gap:8px;flex-wrap:wrap}
.chart{display:flex;gap:4px;align-items:stretch;height:150px;padding-top:20px;margin:12px 0 20px;position:relative;border-bottom:1px solid var(--line)}
.barhold{flex:1;display:flex;align-items:end;justify-content:center;min-width:3px}.bar{width:70%;max-width:18px;border-radius:3px 3px 0 0;background:var(--ok);min-height:2px}.bar.negative{background:var(--bad);border-radius:0 0 3px 3px}
.activity{display:grid;gap:8px}.event{display:grid;grid-template-columns:175px 90px minmax(0,1fr);gap:8px;border-bottom:1px solid var(--line);padding:9px 0;align-items:start}
.event code{color:var(--muted);overflow-wrap:anywhere;font-size:11px}.event .tag{font-size:11px;text-transform:uppercase;font-weight:bold}.warning{background:#2a2317;border:1px solid #735b34;border-radius:12px;padding:15px 18px;color:#f5d99c;margin:15px 0}
.err{color:var(--bad)}.hidden{display:none!important}footer{color:var(--muted);padding-top:18px;font-size:11px;line-height:1.7}
@media(max-width:950px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}.split{grid-template-columns:1fr}}
@media(max-width:520px){.app{padding-top:17px}.grid{grid-template-columns:1fr 1fr;gap:9px}.card{padding:13px;border-radius:11px}.metric{font-size:22px}.event{grid-template-columns:1fr 55px;gap:3px}.event code{grid-column:span 2}h1{font-size:20px}}
</style>
</head><body><div class="app">
<header class="top"><div><div class="logo"><span class="symbol">◈</span> BTC Strategy <span class="muted">/ VPS Monitor</span></div>
<div class="sub">EMA20 + Supertrend · BTCUSD perpetual · 15-minute signals</div></div>
<div class="status"><span class="chip" id="mode">MODE ?</span><span class="chip" id="health">CONNECTING</span><span class="chip" id="orders">NO ORDERS</span></div></header>
<div class="nav"><button class="on" data-tab="overview">Overview</button><button data-tab="backtest">Backtest</button><button data-tab="activity">Activity log</button><button data-tab="safety">Safety</button></div>
<main>
<section id="overview">
<div class="grid">
<div class="card"><div class="metric-label">BTCUSD last traded</div><div class="metric" id="lastprice">—</div><div class="small muted">Exchange ticker</div></div>
<div class="card"><div class="metric-label">BTCUSD mark price</div><div class="metric" id="markprice">—</div><div class="small muted">Liquidation trigger reference</div></div>
<div class="card"><div class="metric-label">Margin per trade</div><div class="metric" id="margin">$10</div><div class="small muted">Fixed isolated budget</div></div>
<div class="card"><div class="metric-label">Selected leverage</div><div class="metric" id="leverage">100×</div><div class="small muted">Only if orders enabled</div></div>
</div>
<div class="grid">
<div class="card"><div class="metric-label">Exchange wallet equity</div><div class="metric" id="wallet-equity">—</div><div class="small muted">Authenticated Delta balance</div></div>
<div class="card"><div class="metric-label">Estimated realized net from fills</div><div class="metric" id="fill-net">—</div><div class="small muted">After reported fee + assumed GST, before funding</div></div>
<div class="card"><div class="metric-label">Verified exchange fills</div><div class="metric" id="fill-count">—</div><div class="small muted" id="fill-updated">Waiting for keys / sync</div></div>
<div class="card"><div class="metric-label">Exchange liquidation fills</div><div class="metric" id="fill-liquidations">—</div><div class="small muted">From authenticated fill types</div></div>
</div>
<div class="split"><div class="card"><h2>Bot status</h2>
<div class="line"><span class="muted">Trading status</span><strong id="trading-state">—</strong></div>
<div class="line"><span class="muted">Latest completed candle</span><strong id="candle">—</strong></div>
<div class="line"><span class="muted">Latest signal</span><strong id="signal">—</strong></div>
<div class="line"><span class="muted">Heartbeat age</span><strong id="heartbeat">—</strong></div>
<div class="line"><span class="muted">Daily entries</span><strong id="entries">—</strong></div>
</div><div class="card"><h2>Exchange position</h2>
<div class="line"><span class="muted">Side / contracts</span><strong id="position">FLAT / UNCONFIRMED</strong></div>
<div class="line"><span class="muted">Entry price</span><strong id="entry">—</strong></div>
<div class="line"><span class="muted">Protective stop</span><strong id="stop">—</strong></div>
<div class="line"><span class="muted">Stop order ID</span><strong id="stopid">—</strong></div>
<div class="line"><span class="muted">Bot warning</span><strong class="err" id="halt">—</strong></div>
</div></div>
<div class="warning">This monitor is read-only and does not show verified realized P&amp;L until fills and exchange funding are reconciled. Backtest results are simulations, not demo/live profits.</div>
</section>
<section id="backtest" class="hidden">
<div class="top"><div><h1>Historical backtest</h1><p class="muted small">Fixed $10 isolated margin, 100× leverage, hypothetical $100 starting portfolio. Fees and GST modeled.</p></div>
<div class="filters"><select id="window"><option value="history">All history · Jan 2025–Nov 2026</option><option value="recent">Recent · Aug–Nov 2026</option></select>
<select id="liq"><option value="threshold">Liquidation threshold fill</option><option value="bankruptcy">Bankruptcy-price stress fill</option></select></div></div>
<div class="grid">
<div class="card"><div class="metric-label">Ending portfolio</div><div class="metric" id="bt-end">—</div></div>
<div class="card"><div class="metric-label">Total net return</div><div class="metric" id="bt-return">—</div></div>
<div class="card"><div class="metric-label">Net profit factor</div><div class="metric" id="bt-pf">—</div></div>
<div class="card"><div class="metric-label">Modeled liquidations</div><div class="metric" id="bt-liq">—</div></div>
</div>
<div class="card"><h2>Monthly net returns</h2><div class="chart" id="chart"></div>
<div class="tablewrap"><table><thead><tr><th>Month</th><th>Trades</th><th>Liquidations</th><th>Net P&amp;L</th><th>Monthly return</th><th>Ending balance</th></tr></thead><tbody id="months"></tbody></table></div>
<p class="muted small">Recent August and November are partial periods. The fee offer is assumed historically; slippage, spread, and realized funding are not included. Liquidation uses OHLC price proxies rather than actual exchange mark prices.</p></div>
</section>
<section id="activity" class="hidden"><h1>Bot activity</h1><p class="muted small">Persisted SQLite journal. Newest events first. Alerts remain visible until inspected.</p><div class="card activity" id="eventlist">No events yet</div></section>
<section id="safety" class="hidden"><h1>Execution safety</h1>
<div class="split"><div class="card"><h2>Order controls</h2>
<div class="line"><span class="muted">Account budget</span><strong id="budget">$100</strong></div>
<div class="line"><span class="muted">Margin mode</span><strong>Isolated (manual confirmation)</strong></div>
<div class="line"><span class="muted">Max margin allocation</span><strong>$10</strong></div>
<div class="line"><span class="muted">Initial stop</span><strong>2 × ATR(14)</strong></div>
<div class="line"><span class="muted">Trailing activation</span><strong>150 BTC points</strong></div>
<div class="line"><span class="muted">Trailing distance</span><strong>50 BTC points</strong></div>
</div><div class="card"><h2>Guards and limitations</h2>
<p>Only closed 15m signals; one position; native reduce-only mark stop; no blind retries; persisted order intents; stop-before-liquidation buffer; stale feed checks; manual live confirmation; localhost-only dashboard.</p>
<p class="muted small">Cross margin is not supported. The 2×ATR risk guard changes forward-trading signals relative to the historical backtest. REST polling and mark-triggered stops are not guaranteed to reproduce OHLC intrabar exits.</p></div></div>
<div class="warning">100× leverage carries substantial liquidation risk. Never switch to real money before validating testnet orders, fill prices, protective stop behavior, restarts, fee deductions, and emergency exits. A systemd restart is not a substitute for reconciling uncertain orders.</div>
</section>
</main>
<footer>BTC Strategy VPS · research build · Local data only. Access via SSH tunnel (127.0.0.1:8765). Auto-refresh every 4 seconds. No trading buttons.</footer></div>
<script>
const $=id=>document.getElementById(id);
function money(x,n=2){return x==null||!Number.isFinite(Number(x))?"—":"$"+Number(x).toLocaleString(undefined,{minimumFractionDigits:n,maximumFractionDigits:n})}
function val(x){return x==null||x===""?"—":String(x)}
function setText(id,s){$(id).textContent=s}
function pct(x){return x==null||x===""?"—":(Number(x)>0?"+":"")+Number(x).toFixed(2)+"%"}
function cls(id,txt,badge){const e=$(id);e.textContent=txt;e.className="chip"+(badge?" "+badge:"")}
document.querySelectorAll("[data-tab]").forEach(b=>b.addEventListener("click",()=>{
document.querySelectorAll("[data-tab]").forEach(x=>x.classList.toggle("on",x===b));
["overview","backtest","activity","safety"].forEach(n=>$(n).classList.toggle("hidden",n!==b.dataset.tab));
}));
async function refresh(){
 try{const r=await fetch("/api/status",{cache:"no-store"});if(!r.ok)throw Error("HTTP "+r.status);const s=await r.json();
 cls("mode",s.mode==="demo"?"DEMO / TESTNET":"LIVE / REAL","warn");
 cls("health",s.connected&&!s.halted?"CONNECTED":s.halted?"HALTED":"OFFLINE",s.connected&&!s.halted?"good":"bad");
 cls("orders",s.trading?"ORDERS ENABLED":"READ-ONLY",s.trading?"warn":"good");
 setText("lastprice",money(s.ticker&&s.ticker.last,1));setText("markprice",money(s.ticker&&s.ticker.mark,1));
 setText("margin",money(s.margin));setText("leverage",val(s.leverage)+"×");setText("budget",money(s.portfolio_budget));
 const f=s.fill_attribution;setText("wallet-equity",money(s.exchange_equity_usd));
 setText("fill-net",f?money(f.estimated_net_before_funding_usd):"—");
 setText("fill-count",f?val(f.fills):"—");
 setText("fill-liquidations",f?val(f.liquidation_fills):"—");
 setText("fill-updated",s.fills_synced_at?"Synced "+s.fills_synced_at:"Waiting for keys / sync");
 setText("trading-state",s.halted?"HALTED":s.trading?"ENABLED":"SIGNAL ONLY");
 setText("candle",val(s.last_candle));setText("signal",s.signal?s.signal.side.toUpperCase():"—");
 setText("heartbeat",s.heartbeat_age_seconds==null?"—":s.heartbeat_age_seconds+" seconds");
 setText("entries",s.daily?val(s.daily.entries):"—");
 const p=s.position;setText("position",p?p.side.toUpperCase()+" / "+Math.abs(p.size):"FLAT / NONE");
 setText("entry",p?money(p.entry,1):"—");setText("stop",p?money(p.stop,1):"—");
 setText("stopid",p?val(p.stop_id):"—");setText("halt",s.halted?String(s.halted):"—");
 const list=$("eventlist");list.replaceChildren();
 if(!s.events.length)list.textContent="No events yet";
 s.events.forEach(v=>{
  const row=document.createElement("div");row.className="event";
  const a=document.createElement("span");a.className="muted small";a.textContent=v.time_utc;
  const b=document.createElement("span");b.className="tag"+(v.level==="ERROR"?" err":"");b.textContent=v.level;
  const c=document.createElement("code");c.textContent=v.kind+" "+JSON.stringify(v.data);
  row.append(a,b,c);list.appendChild(row);
 });
 }catch(ex){cls("health","DASHBOARD ERROR","bad");setText("halt",String(ex))}
}
async function loadBacktest(){
 const url="/api/backtest?window="+encodeURIComponent($("window").value)+"&liquidation="+encodeURIComponent($("liq").value);
 try{const r=await fetch(url,{cache:"no-store"});const data=await r.json();if(data.error)throw Error(data.error);
 const st=data.statistics;setText("bt-end",money(st.ending_portfolio_usd));
 setText("bt-return",pct(st.total_return_pct));setText("bt-pf",val(st.net_profit_factor));
 setText("bt-liq",val(st.assumed_liquidations));
 const tbody=$("months");tbody.replaceChildren();
 const chart=$("chart");chart.replaceChildren();
 const max=Math.max(1,...data.months.map(m=>Math.abs(Number(m.monthly_return_pct||0))));
 data.months.forEach(m=>{
   const tr=document.createElement("tr");
   [m.month_ist,m.trades,m.liquidations,money(m.net_profit_usd),pct(m.monthly_return_pct),money(m.closing_balance_usd)].forEach((str,index)=>{
    const td=document.createElement("td");td.textContent=val(str);
    if(index===3||index===4)td.className=Number(m.net_profit_usd)<0?"bad-txt":"good-txt";
    tr.append(td);
   });tbody.append(tr);
   const outer=document.createElement("div");outer.className="barhold";
   const bar=document.createElement("div");bar.className="bar"+(Number(m.monthly_return_pct)<0?" negative":"");
   bar.style.height=Math.max(3,Math.abs(Number(m.monthly_return_pct||0))/max*118)+"px";
   bar.title=m.month_ist+": "+pct(m.monthly_return_pct);outer.append(bar);chart.append(outer);
 });
 }catch(ex){setText("bt-end","Unavailable");setText("bt-return",String(ex))}
}
$("window").addEventListener("change",loadBacktest);$("liq").addEventListener("change",loadBacktest);
refresh();loadBacktest();setInterval(refresh,4000);
</script></body></html>"""

@app.get("/",response_class=HTMLResponse)
def homepage():
    return HTMLResponse(HTML,headers={"Cache-Control":"no-store",
        "Content-Security-Policy":"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'",
        "X-Content-Type-Options":"nosniff","Referrer-Policy":"no-referrer"})
