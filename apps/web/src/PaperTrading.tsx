import {useEffect,useState,useRef} from "react";
import type {Api,Strategy,PaperSession,PaperRequest} from "./api";
const utc=(t:number)=>new Date(t*1000).toISOString();
const fmt=(v:string|number|null|undefined)=>v==null?"—":Number(v).toFixed(2);
export function PaperTrading({api,strategies}:{api:Api;strategies:Strategy[]}){
 const [sessions,setSessions]=useState<PaperSession[]>([]),[sid,setSid]=useState(""),[symbol,setSymbol]=useState<PaperRequest["symbol"]>("BTCUSD"),[duration,setDuration]=useState(60),[ack,setAck]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState("");
 const [values,setValues]=useState({initial_equity:"100",maker_bps:"2",taker_bps:"5",tax_rate:"0.18",slippage_bps:"0",tick_size:"0.1",lot_size:"0.001",multiplier:"1",max_drawdown_pct:"10"});
 const key=useRef<{body:string;key:string}|null>(null);
 const frozen=strategies.filter(s=>!s.archived&&s.frozen_version!==null),selected=frozen.find(s=>s.id===sid);
 async function reload(){setSessions(await api.paper());}
 useEffect(()=>{let live=true;let timer:number;async function poll(){try{const rows=await api.paper();if(live)setSessions(rows);}catch(e){if(live)setError(String(e));}if(live)timer=window.setTimeout(poll,5000);}void poll();return()=>{live=false;window.clearTimeout(timer);};},[api]);
 async function start(){if(!selected||selected.frozen_version===null||!ack)return;setBusy(true);setError("");
 const body:PaperRequest={strategy_id:sid,version:selected.frozen_version,symbol,duration_minutes:duration,...values,acknowledge_assumptions:true};
 const str=JSON.stringify(body);if(key.current?.body!==str)key.current={body:str,key:crypto.randomUUID()};
 try{await api.startPaper(body,key.current.key);key.current=null;await reload();}catch(e){setError(String(e));}finally{setBusy(false);}}
 async function stop(id:string){setBusy(true);try{await api.stopPaper(id);await reload();}catch(e){setError(String(e));}finally{setBusy(false);}}
 return <><section className="panel"><h2>Forward paper trading</h2><p className="notice">Paper only. Newly received public candles; 1× modeled fills, two independent OHLC paths. No exchange orders, funding, spread or liquidation. Start requires a separately running paper poller. No historical warmup.</p>
 <label>Frozen visual strategy<select value={sid} onChange={e=>setSid(e.target.value)}><option value="">Select frozen strategy</option>{frozen.map(s=><option key={s.id} value={s.id}>{s.name} · v{s.frozen_version}</option>)}</select></label>
 <label>Instrument<select value={symbol} onChange={e=>setSymbol(e.target.value as PaperRequest["symbol"])}><option>BTCUSD</option><option>ETHUSD</option></select></label>
 <label>Duration (minutes)<input type="number" min={1} max={120} value={duration} onChange={e=>setDuration(Number(e.target.value))}/></label>
 <div className="visual-config">{Object.entries(values).map(([k,v])=><label key={k}>{k.replace(/_/g," ")}<input value={v} onChange={e=>setValues(o=>({...o,[k]:e.target.value}))}/></label>)}</div>
 <label className="check"><input type="checkbox" checked={ack} onChange={e=>setAck(e.target.checked)}/> Accept assumed candle-open labels and contract/cost settings; modeled drawdown halt stops observation, not an actual position close.</label>
 <button className="primary" disabled={!selected||!ack||busy||!Number.isInteger(duration)||duration<1||duration>120} onClick={()=>void start()}>Start paper session</button>{error&&<p role="alert" className="error">{error}</p>}</section>
 {sessions.map(s=><section className="panel" key={s.id}><div className="head"><h2>{s.config.symbol} · {s.status}</h2>{["scheduled","running"].includes(s.status)&&<button disabled={busy} onClick={()=>void stop(s.id)}>Stop paper session</button>}</div>
 <p>Start {utc(s.start)} · End {utc(s.end)} · Captured {(s.cursor-s.start)/60}/{(s.end-s.start)/60} candles</p><p className="hash muted">{s.id} · Configuration {s.config_sha256}</p>{s.reason&&<p role="status">{s.reason}</p>}
 {s.checkpoint?<><p>Modeled checkpoint through {utc(s.checkpoint.through)}. Unclosed simulated positions remain visible; no forced closing at session end.</p><div className="scenarios">{s.checkpoint.scenarios.map(x=><article className="scenario" key={x.path}><h3>{x.path}</h3><dl>{[["Balance USD",fmt(x.balance)],["Equity USD",fmt(x.equity)],["Net P&L USD",fmt(x.metrics.account_net)],["Drawdown %",fmt(x.metrics.max_event_drawdown_pct)],["Signed position",x.open_quantity],["Unrealized USD",fmt(x.unrealized_pnl)],["Closed trades",x.closed_trades.length]].map(([k,v])=><div key={k}><dt>{k}</dt><dd>{v}</dd></div>)}</dl><details><summary>Modeled fill history ({x.fills.length})</summary><div className="table-wrap"><table><thead><tr><th>UTC</th><th>Side</th><th>Price</th><th>Quantity</th><th>Reason</th></tr></thead><tbody>{x.fills.map(f=><tr key={f.fill_id}><td>{f.event_utc}</td><td>{f.side}</td><td>{f.price}</td><td>{f.quantity}</td><td>{f.reason}</td></tr>)}</tbody></table></div></details></article>)}</div></>:<p className="muted">Waiting for first complete aligned checkpoint. If the poller is offline, no candles are captured.</p>}</section>)}</>;
}
