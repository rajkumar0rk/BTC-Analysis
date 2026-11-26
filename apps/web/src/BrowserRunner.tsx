import {useEffect,useRef,useState} from "react";
import type {Api,Strategy} from "./api";
import {saveHistory,loadHistory,deleteHistory} from "./historyCache";
import type {SymbolName} from "./historyCache";
import {ParallelRunner} from "./ParallelRunner";
import type {LocalResult as Result} from "./parallelReplay";
const rule=(op:string)=>({enabled:true,groups:[{conditions:[{left:{kind:"price",timeframe:300,field:"close"},op,right:{kind:"indicator",timeframe:300,name:"ema.value",parameters:{period:3}}}]}]});
const off={enabled:false,groups:[]};
const starter=JSON.stringify({signal_timeframe:300,execution_timeframe:60,exposure_pct:"20",stop_loss_pct:"1",take_profit_pct:"2",long_entry:rule("cross_up"),long_exit:rule("cross_down"),short_entry:off,short_exit:off},null,2);
export function BrowserRunner({api,strategies=[],initialGraph}:{api?:Api;strategies?:Strategy[];initialGraph?:string}){
 const [graph,setGraph]=useState(initialGraph??starter),[csv,setCsv]=useState(""),[file,setFile]=useState(""),[symbol,setSymbol]=useState<SymbolName>("BTCUSD"),[assume,setAssume]=useState(false),[sid,setSid]=useState("");
 const [settings,setSettings]=useState({initial_equity:"100",maker_bps:"2",taker_bps:"5",tax_rate:"0.18",slippage_bps:"0",tick_size:"0.1",lot_size:"0.001",multiplier:"1"});
 const [status,setStatus]=useState("Ready"),[busy,setBusy]=useState(false),[progress,setProgress]=useState(0),[error,setError]=useState(""),[result,setResult]=useState<Result|null>(null),[timing,setTiming]=useState("");
 const [batchBusy,setBatchBusy]=useState(false);
 const [cacheNote,setCacheNote]=useState(""),[historyBusy,setHistoryBusy]=useState(false),[cacheStats,setCacheStats]=useState<{candle_hit:boolean;indicator_hits:number;indicator_misses:number;indicator_updates_reused:number}|null>(null);
 const worker=useRef<Worker|null>(null),seq=useRef(0),timer=useRef<number|undefined>(undefined),readSeq=useRef(0);
 function stop(){seq.current++;worker.current?.terminate();worker.current=null;window.clearTimeout(timer.current);setBusy(false);}
 useEffect(()=>()=>{worker.current?.terminate();window.clearTimeout(timer.current);readSeq.current++;},[]);
 async function load(f:File|undefined){const n=++readSeq.current;setError("");setCsv("");setFile("");setAssume(false);setResult(null);setCacheStats(null);setCacheNote("");
  if(!f)return;if(f.size>16777216){setError("CSV exceeds 16 MiB.");return;}
  try{const text=await f.text();if(n===readSeq.current){setCsv(text);setFile(f.name);}}catch{if(n===readSeq.current)setError("CSV read failed.");}}
 async function openSaved(){if(!api)return;const s=strategies.find(x=>x.id===sid);if(!s)return;setBusy(true);setError("");try{const r=await api.revision(s.id,s.frozen_version??s.latest_version);setGraph(r.source);setResult(null);}catch(e){setError(String(e));}finally{setBusy(false);}}
 async function history(action:"save"|"load"|"remove"){
  setHistoryBusy(true);setCacheNote("");setError("");try{
   if(action==="save"){if(!result||!csv)throw new Error("Complete a validated run first.");await saveHistory({symbol,name:file,csv,sha256:result.data_sha256,storedAt:Date.now()});setCacheNote("Validated CSV saved on this device.");}
   else if(action==="load"){const stored=await loadHistory(symbol);if(!stored){setCacheNote("No saved CSV for "+symbol+".");return;}readSeq.current++;setCsv(stored.csv);setFile(stored.name);setAssume(false);setResult(null);setCacheStats(null);setCacheNote("Saved CSV restored and checksum verified.");}
   else{await deleteHistory(symbol);setCacheNote("Saved CSV removed. Current in-memory input unchanged.");}
  }catch(e){setError(String(e));}finally{setHistoryBusy(false);}
 }
 function run(){
  setError("");setResult(null);setTiming("");setCacheStats(null);setBusy(true);setProgress(0);setStatus("Initializing Python");
  const id=++seq.current;
  try{
   const w=worker.current??new Worker(new URL("./browser-python-worker.js",document.baseURI));worker.current=w;
   w.onmessage=e=>{const m=e.data;if(m.id!==seq.current)return;
    if(m.status==="progress"){setProgress(m.progress);return;}
    if(m.status==="running"){setStatus("Running both OHLC paths");return;}
    if(m.status==="done"){window.clearTimeout(timer.current);setBusy(false);setProgress(100);setStatus("Completed");setResult(m.result);setCacheStats(m.cacheStats);setTiming("Compute "+(m.elapsed_ms/1000).toFixed(3)+" s · total "+(m.total_ms/1000).toFixed(3)+" s");}
    if(m.status==="error"){stop();setStatus("Failed");setError(m.message);}
   };
   w.onerror=()=>{if(id===seq.current){stop();setStatus("Failed");setError("Browser Python worker failed. Verify runtime assets.");}};
   timer.current=window.setTimeout(()=>{if(id===seq.current){stop();setStatus("Timed out");setError("Local run exceeded 120 seconds.");}},120000);
   w.postMessage({id,csv,graph,symbol,settings,assume});
  }catch(e){stop();setStatus("Failed");setError(String(e));}
 }
 return <section className="panel"><h2>Local Python backtest</h2><p className="notice">Runs trusted visual rules in Python/WebAssembly on this device. No API call for execution. 1× only, two modeled OHLC paths, no funding or liquidation. Up to 31 days, no external warmup. Arbitrary handwritten Python is not executed.</p>
 <fieldset disabled={busy||historyBusy||batchBusy}><label>Historical CSV<input aria-label="Historical CSV" type="file" accept=".csv,text/csv" onChange={e=>void load(e.target.files?.[0])}/></label><small>time,open,high,low,close,volume — UTC epoch seconds, contiguous 1m rows. {file}</small>
 <label>Local instrument<select value={symbol} onChange={e=>{setSymbol(e.target.value as SymbolName);setResult(null);setCacheStats(null);setCacheNote("");}}><option>BTCUSD</option><option>ETHUSD</option></select></label>
 <div className="head"><button disabled={!result||!csv} onClick={()=>void history("save")}>Save CSV on this device</button><button onClick={()=>void history("load")}>Load saved CSV</button><button onClick={()=>void history("remove")}>Remove saved CSV</button></div><p className="muted">Optional local storage, one CSV per instrument. No upload or automatic persistence. {cacheNote}</p>
 {api&&<><label>Saved local-run strategy<select value={sid} onChange={e=>setSid(e.target.value)}><option value="">Choose strategy</option>{strategies.filter(s=>!s.archived).map(s=><option key={s.id} value={s.id}>{s.name}</option>)}</select></label><button disabled={!sid} onClick={()=>void openSaved()}>Load saved visual source</button></>}
 <label>Visual graph JSON or exact generated Python<textarea aria-label="Local visual source" rows={12} style={{width:"100%",fontFamily:"monospace"}} value={graph} onChange={e=>{setGraph(e.target.value);setResult(null);}}/></label>
 <div className="visual-config">{Object.entries(settings).map(([key,value])=><label key={key}>{key}<input value={value} onChange={e=>{setSettings(old=>({...old,[key]:e.target.value}));setResult(null);}}/></label>)}</div>
 <label className="check"><input type="checkbox" checked={assume} onChange={e=>{setAssume(e.target.checked);setResult(null);}}/> Assume CSV times are candle opens; provenance and contract specs are unverified.</label>
 <button className="primary" disabled={!csv||!assume||graph.length===0||graph.length>65536} onClick={run}>Run local Python</button></fieldset>
 {busy&&<button onClick={()=>{stop();setStatus("Cancelled");}}>Cancel local run</button>}
 <p role="status">{status} · {progress}% {timing}</p>{cacheStats&&<p className="muted" aria-label="Cache statistics">Candle cache: {cacheStats.candle_hit?"hit":"miss"} · Indicator series hits: {cacheStats.indicator_hits} · misses: {cacheStats.indicator_misses} · reused updates: {cacheStats.indicator_updates_reused}</p>}{error&&<pre role="alert" className="error" style={{whiteSpace:"pre-wrap",overflowWrap:"anywhere"}}>{error}</pre>}
 {result&&<><h3>Local reference result</h3><p>Worst modeled path: {result.worst_path}</p><p className="hash muted">CSV SHA-256: {result.data_sha256}<br/>Graph SHA-256: {result.graph_sha256}<br/>Result SHA-256: {result.result_sha256}</p><div className="scenarios">{result.scenarios.map(s=><article className="scenario" key={s.path}><h3>{s.path}</h3><dl>{[["Candles",s.bars],["Final equity",s.final_equity],["Net P&L",s.metrics.account_net],["Trades",s.metrics.trades],["Win rate %",s.metrics.win_rate_pct],["Profit factor",s.metrics.profit_factor],["Drawdown %",s.metrics.max_event_drawdown_pct],["Fees",s.fees],["Tax",s.taxes]].map(([k,v])=><div key={k}><dt>{k}</dt><dd>{v==null?"—":Number(v).toFixed(k==="Candles"||k==="Trades"?0:4)}</dd></div>)}</dl><table><thead><tr><th>Month</th><th>P&L</th></tr></thead><tbody>{s.monthly.map(m=><tr key={m.month}><td>{m.month}</td><td>{Number(m.pnl).toFixed(4)}</td></tr>)}</tbody></table></article>)}</div><details><summary>Limitations</summary><ul>{result.limitations.map(l=><li key={l}>{l}</li>)}</ul></details></>}
 <ParallelRunner input={{csv,symbol,settings,assume}} graph={graph} disabled={busy||historyBusy} onBusy={v=>{if(v){seq.current++;worker.current?.terminate();worker.current=null;window.clearTimeout(timer.current);}setBatchBusy(v);}}/>
 </section>;
}
