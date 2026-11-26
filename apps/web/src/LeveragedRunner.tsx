import {useEffect,useRef,useState} from "react";
import type {BatchInput,LocalResult} from "./parallelReplay";
type RiskScenario=LocalResult["scenarios"][number]&{funding_paid:string;liquidation_count:number;preliq_count:number};
type RiskResult=Omit<LocalResult,"scenarios">&{scenarios:RiskScenario[];risk:unknown};
const defaults={leverage:"1",margin_mode:"isolated",initial_rate_floor:"",maintenance_rate:"",max_notional:"",liquidation_fee_bps:"",profile_start:"",profile_end:"",profile_source:"",preliq_points:"0",scalp_start:"",scalp_end:""};
export function LeveragedRunner({input,graph,disabled,onBusy}:{input:BatchInput;graph:string;disabled:boolean;onBusy:(v:boolean)=>void}){
 const [v,setV]=useState(defaults),[mark,setMark]=useState(""),[funding,setFunding]=useState(""),[fund,setFund]=useState(false),[scalp,setScalp]=useState(false),[ack,setAck]=useState(false),[interval,setInterval]=useState("28800"),[anchor,setAnchor]=useState("0");
 const [busy,setBusy]=useState(false),[loading,setLoading]=useState(false),[status,setStatus]=useState("Ready"),[error,setError]=useState(""),[result,setResult]=useState<RiskResult|null>(null);
 const worker=useRef<Worker|null>(null),timer=useRef<number|undefined>(undefined),seq=useRef(0);
 function close(){seq.current++;worker.current?.terminate();worker.current=null;window.clearTimeout(timer.current);setBusy(false);onBusy(false);}
 useEffect(()=>()=>{worker.current?.terminate();window.clearTimeout(timer.current);},[]);
 async function file(f:File|undefined,kind:"mark"|"funding"){setLoading(true);setError("");setResult(null);try{
  if(f&&f.size>16777216)throw new Error("Risk CSV exceeds 16 MiB.");
  const text=f?await f.text():"";if(kind==="mark")setMark(text);else setFunding(text);
 }catch(e){setError(String(e));if(kind==="mark")setMark("");else setFunding("");}finally{setLoading(false);}}
 function run(){
  if(disabled||busy||loading)return;setError("");setResult(null);setBusy(true);onBusy(true);setStatus("Initializing risk replay");
  const id=++seq.current;
  try{
   const w=new Worker(new URL("./browser-python-worker.js",document.baseURI));worker.current=w;
   w.onmessage=e=>{const m=e.data;if(m.id!==seq.current)return;
    if(m.status==="progress")setStatus("Running "+m.progress+"%");
    if(m.status==="done"){setResult(m.result);setStatus("Completed");close();}
    if(m.status==="error"){setError(m.message);setStatus("Failed");close();}
   };
   w.onerror=()=>{if(seq.current===id){setError("Risk worker failed.");setStatus("Failed");close();}};
   timer.current=window.setTimeout(()=>{if(seq.current===id){setError("Risk run exceeded 120 seconds.");setStatus("Timed out");close();}},120000);
   w.postMessage({id,...input,graph,risk:{...v,mark_csv:mark,funding_enabled:fund,funding_csv:fund?funding:"",funding_interval_seconds:Number(interval),funding_anchor_epoch:Number(anchor),scalp_enabled:scalp,acknowledge:ack}});
  }catch(e){setError(String(e));close();}
 }
 const ready=!!input.csv&&input.assume&&!!mark&&ack&&!!v.profile_start&&!!v.profile_end&&!!v.profile_source&&!!v.initial_rate_floor&&!!v.maintenance_rate&&!!v.max_notional&&!!v.liquidation_fee_bps&&(!fund||!!funding)&&(!scalp||!!v.scalp_start&&!!v.scalp_end);
 return <section className="scenario" style={{marginTop:16}}><h2>Leveraged reference replay</h2><p className="notice">Uses current strategy and trade CSV, separate mark data and explicit historical fixed-tier assumptions. Exposure % now represents equity allocated to initial margin; notional scales with leverage. No exchange-certified liquidation or historical eligibility inference. Mark-vertex protection can miss gaps. Single isolated/cross position only.</p>
 <fieldset disabled={disabled||busy||loading} style={{minWidth:0}}>
 <label>Risk mark CSV<input aria-label="Risk mark CSV" type="file" accept=".csv,text/csv" onChange={e=>void file(e.target.files?.[0],"mark")}/></label><small>time,open,high,low,close — one exact mark candle per trade candle.</small>
 <div className="visual-config">{Object.entries(v).filter(([k])=>k!=="margin_mode"&&!k.startsWith("scalp_")).map(([k,value])=><label key={k}>{k==="profile_start"||k==="profile_end"?k+" UTC epoch seconds":k}<input value={value} onChange={e=>{setV(old=>({...old,[k]:e.target.value}));setResult(null);}}/></label>)}
 <label>Margin mode<select value={v.margin_mode} onChange={e=>setV(old=>({...old,margin_mode:e.target.value}))}><option>isolated</option><option>cross</option></select></label></div>
 <label className="check"><input type="checkbox" checked={fund} onChange={e=>setFund(e.target.checked)}/> Include funding settlements</label>
 {fund&&<><label>Funding CSV<input aria-label="Funding CSV" type="file" accept=".csv,text/csv" onChange={e=>void file(e.target.files?.[0],"funding")}/></label><small>time,rate,reference_mark — signed decimal rate, every scheduled settlement.</small><label>Funding interval seconds<input value={interval} onChange={e=>setInterval(e.target.value)}/></label><label>Funding anchor UTC epoch<input value={anchor} onChange={e=>setAnchor(e.target.value)}/></label></>}
 <label className="check"><input type="checkbox" checked={scalp} onChange={e=>setScalp(e.target.checked)}/> Assume eligible 30-minute closing fee waiver (single entry, full close; no vouchers)</label>
 {scalp&&<>{(["scalp_start","scalp_end"] as const).map(k=><label key={k}>{k} UTC epoch seconds<input value={v[k]} onChange={e=>setV(old=>({...old,[k]:e.target.value}))}/></label>)}</>}
 <label className="check"><input type="checkbox" checked={ack} onChange={e=>setAck(e.target.checked)}/> I acknowledge supplied historical margin/fee assumptions, mark and funding provenance, and simulation limitations.</label>
 <button className="primary" disabled={!ready} onClick={run}>Run leveraged replay</button></fieldset>
 {busy&&<button onClick={()=>{close();setStatus("Cancelled");}}>Cancel leveraged replay</button>}<p role="status">{status}</p>{error&&<pre role="alert" className="error" style={{whiteSpace:"pre-wrap",overflowWrap:"anywhere"}}>{error}</pre>}
 {result&&<><h3>Leveraged reference result</h3><p className="hash">Result SHA-256: {result.result_sha256}</p><div className="table-wrap"><table><thead><tr><th>Path</th><th>Net P&amp;L</th><th>Drawdown %</th><th>Fees</th><th>GST</th><th>Funding paid</th><th>Liquidations</th><th>Pre-liq exits</th></tr></thead><tbody>{result.scenarios.map(s=><tr key={s.path}><td>{s.path}</td><td>{s.metrics.account_net}</td><td>{s.metrics.max_event_drawdown_pct}</td><td>{s.fees}</td><td>{s.taxes}</td><td>{s.funding_paid}</td><td>{s.liquidation_count}</td><td>{s.preliq_count}</td></tr>)}</tbody></table></div><details><summary>Risk assumptions and evidence</summary><pre style={{whiteSpace:"pre-wrap",overflowWrap:"anywhere"}}>{JSON.stringify(result.risk,null,2)}</pre><ul>{result.limitations.map(l=><li key={l}>{l}</li>)}</ul></details></>}
 </section>;
}
