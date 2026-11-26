import {WorkspaceNav} from "./WorkspaceNav";
import {useState,useEffect,useRef} from "react";
import {BrowserRunner} from "./BrowserRunner";
import {FrameSelect,RuleEdit} from "./VisualBuilder";
import {initialGraph,keys} from "./visualTypes";
import type {Graph,Compiled} from "./visualTypes";
import type {Catalog} from "./api";
const catalog:Catalog={sdk_version:"1",execution_allowed:false,indicators:[
 ...["sma","ema","atr","rsi","roc","volume_ratio","vwap","stddev"].map(name=>({name,defaults:{period:name==="atr"||name==="rsi"?14:name==="roc"?10:20},outputs:["value"]})),
 {name:"adx",defaults:{period:14},outputs:["value","plus_di","minus_di"]},
 {name:"supertrend",defaults:{period:10,multiplier:"3"},outputs:["line","direction"]},
 {name:"bollinger",defaults:{period:20,multiplier:"2"},outputs:["middle","upper","lower"]},
 {name:"donchian",defaults:{period:20},outputs:["upper","lower","middle"]},
 {name:"macd",defaults:{fast:12,slow:26,signal:9},outputs:["line","signal","histogram"]}
]};
const titles={long_entry:"Long entry",short_entry:"Short entry",long_exit:"Long exit",short_exit:"Short exit"};
export function PublicStudio(){
 const [page,setPage]=useState<"builder"|"research">("builder"),[graph,setGraph]=useState<Graph>(initialGraph),[compiled,setCompiled]=useState<Compiled|null>(null),[source,setSource]=useState<string|undefined>();
 const [busy,setBusy]=useState(false),[error,setError]=useState("");
 const worker=useRef<Worker|null>(null),timer=useRef<number|undefined>(undefined);
 function stop(){worker.current?.terminate();worker.current=null;window.clearTimeout(timer.current);setBusy(false);}
 useEffect(()=>()=>{worker.current?.terminate();window.clearTimeout(timer.current);},[]);
 function edit(g:Graph){setGraph(g);setCompiled(null);setError("");}
 function generate(){
  stop();setBusy(true);setError("");
  try{const w=new Worker(new URL("./browser-python-worker.js",document.baseURI));worker.current=w;
   w.onmessage=e=>{if(worker.current!==w)return;const m=e.data;if(m.status==="done"){setCompiled(m.result);setGraph(m.result.graph);stop();}else if(m.status==="error"){setError(String(m.message));stop();}};
   w.onerror=()=>{setError("Local compiler unavailable.");stop();};
   timer.current=window.setTimeout(()=>{setError("Local compiler timed out.");stop();},120000);
   w.postMessage({id:1,action:"compile_visual",graph:JSON.stringify(graph)});
  }catch(e){setError(String(e));stop();}
 }
 return <main className="public-studio"><header><div><div className="eyebrow">BTC ANALYSIS / RESEARCH</div><h1>Strategy Studio</h1></div></header><WorkspaceNav current="studio"/>
 <p className="notice">Public static workspace. No API token, cloud account or VPS required for local backtests. Imported CSV and optional local storage are device/browser-local, not private from other scripts on this shared origin. Do not enter secrets. Private cloud storage and paper controls use the separately hosted trusted workspace.</p>
 <div className="head"><button aria-current={page==="builder"?"page":undefined} onClick={()=>{stop();setPage("builder");}}>Visual strategy builder</button><button aria-current={page==="research"?"page":undefined} onClick={()=>{stop();setPage("research");}}>Local research runner</button></div>
 {page==="builder"?<><section className="panel"><h2>Visual Python strategy builder</h2><button disabled={busy} onClick={()=>edit(initialGraph())}>New visual strategy</button><div className="visual-config"><FrameSelect label="Signal timeframe" value={graph.signal_timeframe} disabled={busy} change={v=>edit({...graph,signal_timeframe:v})}/><FrameSelect label="Execution timeframe" value={graph.execution_timeframe} disabled={busy} change={v=>edit({...graph,execution_timeframe:v})}/>
 {(["exposure_pct","stop_loss_pct","take_profit_pct"] as const).map(k=><label key={k}>{k}<input disabled={busy} value={graph[k]} onChange={e=>edit({...graph,[k]:e.target.value})}/></label>)}</div></section>
 <div className="visual-rules">{keys.map(k=><RuleEdit key={k} title={titles[k]} rule={graph[k]} catalog={catalog} disabled={busy} change={r=>edit({...graph,[k]:r})}/>)}</div>
 <section className="panel"><h2>Generated Python</h2><button disabled={busy} onClick={generate}>Generate local Python</button>{busy&&<button onClick={stop}>Cancel generation</button>}{error&&<p role="alert" className="error">{error}</p>}{compiled&&<><p className="hash">Graph SHA-256: {compiled.graph_sha256}</p><textarea aria-label="Generated local Python" readOnly rows={12} value={compiled.source}/><button onClick={()=>{setSource(compiled.source);setPage("research");}}>Use generated strategy in backtest</button></>}</section></>:<BrowserRunner initialGraph={source}/>}
 </main>;
}
