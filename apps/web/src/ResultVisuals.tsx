import {useMemo,useState} from "react";
import type {LocalResult,LocalDetails} from "./parallelReplay";
import type {Trade} from "./api";
const fmt=(x:unknown)=>x==null||!Number.isFinite(Number(x))?"—":Number(x).toLocaleString("en-US",{maximumFractionDigits:4});
const sign=(x:unknown)=>Number(x)>0?"gain":Number(x)<0?"loss":"";
type Point={label:string;value:number};
function Chart({points,bars=false,label}:{points:Point[];bars?:boolean;label:string}){
 const [cursor,setCursor]=useState(0);
 const [zoom,setZoom]=useState(0);
 const visible=points.slice(Math.min(zoom,Math.max(0,points.length-1)));
 if(!visible.length)return <p>No chart data.</p>;
 const idx=Math.min(cursor,visible.length-1),lo=Math.min(...visible.map(p=>p.value),...(bars?[0]:[])),hi=Math.max(...visible.map(p=>p.value),...(bars?[0]:[])),span=Math.max(hi-lo,Math.abs(hi)*.000001,.000001);
 const x=(i:number)=>52+(i+(bars?.5:0))*720/(bars?visible.length:Math.max(1,visible.length-1));
 const y=(n:number)=>190-(n-lo)*160/span,base=y(0);
 return <section className="result-chart"><h4>{label}</h4><p className="muted" aria-live="polite">{visible[idx].label} · {fmt(visible[idx].value)} USD</p>
 <svg viewBox="0 0 800 225" role="img" aria-label={label} onPointerMove={e=>{const r=e.currentTarget.getBoundingClientRect();const pos=(e.clientX-r.left)/Math.max(1,r.width)*800;setCursor(Math.max(0,Math.min(visible.length-1,Math.round((pos-52)/720*(bars?visible.length:Math.max(1,visible.length-1))-(bars?.5:0)))));}}>
 {[0,1,2,3,4].map(i=>{const v=lo+(hi-lo)*i/4;return <g key={i}><line x1="52" x2="772" y1={y(v)} y2={y(v)} stroke="#304058"/><text x="47" y={y(v)+4} textAnchor="end" fill="currentColor" fontSize="11">{Number(v.toPrecision(4))}</text></g>})}
 {bars?<>{visible.map((p,i)=><rect key={i} x={x(i)-Math.min(16,300/visible.length)} width={Math.min(32,600/visible.length)} y={Math.min(y(p.value),base)} height={Math.max(1,Math.abs(y(p.value)-base))} fill={p.value>=0?"#43cabb":"#e98d9e"}/>)}</>:<polyline points={visible.map((p,i)=>x(i)+","+y(p.value)).join(" ")} stroke="#43cabb" strokeWidth="2" fill="none"/>}
 <line x1={x(idx)} x2={x(idx)} y1="20" y2="195" stroke="#a8b7cb" strokeDasharray="4 4"/><circle cx={x(idx)} cy={y(visible[idx].value)} r="4" fill="#f5d58a"/>
 </svg><label>Chart point<input aria-label={label+" cursor"} type="range" min={0} max={visible.length-1} value={idx} onChange={e=>setCursor(Number(e.target.value))}/></label>
 {points.length>2&&<label>Chart start point<input aria-label={label+" zoom"} type="range" min={0} max={points.length-2} value={Math.min(zoom,points.length-2)} onChange={e=>{setZoom(Number(e.target.value));setCursor(0);}}/></label>}</section>;
}
function exportTrades(trades:Trade[]){
 const cells=(v:string)=>'"'+(/^[=+@-]/.test(v)&&!/^-\d+(\.\d+)?$/.test(v)?"'"+v:v).replace(/"/g,'""')+'"';
 const rows=[["trade","direction","entry_utc","exit_utc","entry_reason","exit_reason","gross","fees","tax","funding","net"],...trades.map(t=>[t.trade_id,t.entry_fills[0].side,t.entry_fills[0].event_utc,t.exit_fills.at(-1)!.event_utc,t.entry_reason,t.exit_reason,t.gross_pnl,t.fees,t.taxes,t.funding_paid,t.net_pnl])];
 const url=URL.createObjectURL(new Blob([rows.map(r=>r.map(cells).join(",")).join("\r\n")],{type:"text/csv;charset=utf-8"}));const a=document.createElement("a");a.href=url;a.download="local-trades.csv";a.click();window.setTimeout(()=>URL.revokeObjectURL(url),1000);
}
function TradeChart({details,trade,csv}:{details:LocalDetails;trade:Trade;csv:string}){
 const fills=[...trade.entry_fills,...trade.exit_fills],ids=new Set(fills.map(f=>f.fill_id));
 const evidence=details.evidence.filter(e=>ids.has(e.fill_id));
 const times=evidence.map(e=>Date.parse(e.bar_open_utc)/1000);
 const lo=times.length?Math.min(...times)-300:0,hi=times.length?Math.max(...times)+300:0;
 const [offset,setOffset]=useState(0);
 const count=times.length?Math.floor((hi-lo)/60)+1:0;
 const rows=useMemo(()=>csv.trim().split(/\r?\n/).slice(1).map(l=>l.split(",")).filter(r=>Number(r[0])>=lo+offset*60&&Number(r[0])<=hi&&Number(r[0])<lo+(offset+120)*60).map(r=>({t:Number(r[0]),o:Number(r[1]),h:Number(r[2]),l:Number(r[3]),c:Number(r[4])})),[csv,lo,hi,offset]);
 if(!rows.length)return <p>No matching candle window available.</p>;
 const low=Math.min(...rows.map(r=>r.l)),high=Math.max(...rows.map(r=>r.h)),span=Math.max(high-low,.000001);
 const x=(i:number)=>30+i*740/Math.max(1,rows.length-1),y=(v:number)=>195-(v-low)*175/span,width=Math.max(1,Math.min(10,500/rows.length));
 return <section className="result-chart"><h4>Trade candle window (1m UTC)</h4><p className="muted">Modeled fill intervals, not exact tick times. {new Date(rows[0].t*1000).toISOString()} – {new Date(rows[rows.length-1].t*1000).toISOString()}</p>
 <svg viewBox="0 0 800 220" role="img" aria-label="Local trade candlestick chart">{rows.map((r,i)=>{const c=r.c>=r.o?"#43cabb":"#e98d9e";return <g key={r.t}><line x1={x(i)} x2={x(i)} y1={y(r.h)} y2={y(r.l)} stroke={c}/><rect x={x(i)-width/2} y={Math.min(y(r.o),y(r.c))} width={width} height={Math.max(1,Math.abs(y(r.o)-y(r.c)))} fill={c}/></g>})}{evidence.map(e=>{const i=rows.findIndex(r=>r.t===Date.parse(e.bar_open_utc)/1000),fill=fills.find(f=>f.fill_id===e.fill_id);return i<0||!fill?null:<circle key={e.fill_id} cx={x(i)} cy={Math.max(8,Math.min(205,y(Number(fill.price))))} r="5" fill={trade.entry_fills.some(f=>f.fill_id===e.fill_id)?"#60a5fa":"#fbbf24"}><title>{fill.reason} · {fill.price} · {e.phase}</title></circle>})}</svg>
 <p>Blue = entry · Gold = exit</p><div className="rule-actions"><button disabled={offset===0} onClick={()=>setOffset(Math.max(0,offset-120))}>Previous candle window</button><button disabled={offset+120>=count} onClick={()=>setOffset(offset+120)}>Next candle window</button></div></section>;
}
function Ledger({details,csv}:{details:LocalDetails;csv:string}){
 const [filter,setFilter]=useState("all"),[query,setQuery]=useState(""),[page,setPage]=useState(0),[selected,setSelected]=useState<Trade|null>(null);
 const trades=details.trades.filter(t=>(filter==="all"||(filter==="win"&&Number(t.net_pnl)>0)||(filter==="loss"&&Number(t.net_pnl)<0)||(filter==="flat"&&Number(t.net_pnl)===0))&&[t.trade_id,t.entry_reason,t.exit_reason].join(" ").toLowerCase().includes(query.toLowerCase()));
 return <section><div className="head"><h4>Local closed trade ledger</h4><button disabled={!trades.length} onClick={()=>exportTrades(trades)}>Export local trades CSV</button></div><p className="muted">Showing latest {details.trades.length} of {details.closed_trade_total} closed trades (maximum 500). Export contains filtered retained trades only.</p>
 <div className="ledger-filters"><label>Local trade outcome<select value={filter} onChange={e=>{setFilter(e.target.value);setPage(0);setSelected(null);}}><option value="all">All trades</option><option value="win">Winners</option><option value="loss">Losers</option><option value="flat">Breakeven</option></select></label><label>Search local trades<input value={query} onChange={e=>{setQuery(e.target.value);setPage(0);setSelected(null);}}/></label></div>
 <div className="table-wrap"><table><thead><tr><th>Trade</th><th>Entry UTC</th><th>Exit UTC</th><th>Net USD</th><th>Details</th></tr></thead><tbody>{trades.slice(page*20,page*20+20).map(t=><tr key={t.trade_id}><td>{t.trade_id}<small>{t.entry_fills[0].side==="buy"?"Long":"Short"}</small></td><td>{t.entry_fills[0].event_utc}</td><td>{t.exit_fills.at(-1)!.event_utc}</td><td className={sign(t.net_pnl)}>{fmt(t.net_pnl)}</td><td><button onClick={()=>setSelected(t)}>Inspect local {t.trade_id}</button></td></tr>)}</tbody></table></div><div className="head"><small>{trades.length} matching</small><div className="rule-actions"><button disabled={!page} onClick={()=>setPage(page-1)}>Previous local trades</button><button disabled={(page+1)*20>=trades.length} onClick={()=>setPage(page+1)}>Next local trades</button></div></div>
 {selected&&<section className="trade-inspect"><div className="head"><h4>{selected.trade_id} fills</h4><button onClick={()=>setSelected(null)}>Close local trade</button></div><p>Gross {fmt(selected.gross_pnl)} · Fees {fmt(selected.fees)} · GST {fmt(selected.taxes)} · Funding {fmt(selected.funding_paid)} · Net {fmt(selected.net_pnl)} USD</p><div className="table-wrap"><table><thead><tr><th>Side</th><th>UTC</th><th>Price</th><th>Quantity</th><th>Reason</th></tr></thead><tbody>{[...selected.entry_fills,...selected.exit_fills].map(f=><tr key={f.fill_id}><td>{f.side}</td><td>{f.event_utc}</td><td>{f.price}</td><td>{f.quantity}</td><td>{f.reason}</td></tr>)}</tbody></table></div>{csv&&<TradeChart key={selected.trade_id} details={details} trade={selected} csv={csv}/>}</section>}</section>;
}
export function ResultVisuals({result,csv}:{result:LocalResult;csv:string}){
 const [path,setPath]=useState(result.worst_path);
 const s=result.scenarios.find(s=>s.path===path)??result.scenarios[0];if(!s)return null;
 const points=s.monthly.map(m=>({label:m.month,value:Number(m.pnl)})).filter(p=>Number.isFinite(p.value));
 const equity=s.details?s.details.equity.map(p=>({label:p.event_utc,value:Number(p.equity)})):s.monthly.filter(m=>m.closing_equity!==undefined).map(m=>({label:m.month,value:Number(m.closing_equity)}));
 return <section className="result-visuals" aria-label="Interactive backtest results"><div className="head"><h3>Interactive performance</h3><label>Chart scenario<select value={path} onChange={e=>setPath(e.target.value)}>{result.scenarios.map(s=><option key={s.path}>{s.path}</option>)}</select></label></div>
 <div className="analytics-metrics">{[["Net USD",s.metrics.account_net],["Return %",s.metrics.account_return_pct],["Max event DD %",s.metrics.max_event_drawdown_pct],["Profit factor",s.metrics.profit_factor],["Trades",s.metrics.trades],["Win rate %",s.metrics.win_rate_pct],["Positive months",s.metrics.positive_months],["Negative months",s.metrics.negative_months]].map(([k,v])=><div className="metric-tile" key={String(k)}><small>{k}</small><strong className={k==="Net USD"?sign(v):""}>{fmt(v)}</strong></div>)}</div>
 <div className="scenarios"><Chart key={path+"pnl"} points={points} bars label="Monthly net P&L (IST)"/><Chart key={path+"equity"} points={equity.filter(p=>Number.isFinite(p.value))} label={s.details?"Sampled account equity (UTC)":"Month-end equity (IST)"}/></div><p className="muted">{s.details?"Equity chart samples "+s.details.equity.length+" of "+s.details.equity_total+" recorded equity points.":"Long replay shows actual month-end equity only."} Max event drawdown is the engine metric, not derived from chart samples. Calendar-month segments may be partial.</p>
 <div className="month-tiles">{s.monthly.map(m=><div key={m.month} className={"month-tile "+(Number(m.pnl)>0?"positive":Number(m.pnl)<0?"negative":"")}><small>{m.month}</small><strong>{fmt(m.pnl)} USD</strong><span>{fmt(m.return_pct)}%</span></div>)}</div>
 {s.details?<Ledger key={path} details={s.details} csv={csv}/>:<p className="muted">Detailed trades are unavailable for summary-only long replay. Use a short CSV replay for trade inspection.</p>}</section>;
}
