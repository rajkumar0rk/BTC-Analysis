import {loadRepositoryHistory} from "./repositoryHistory";
import {estimateFunding,type FundingRateUnit} from "./fundingEstimate";
import {ResultVisuals} from "./ResultVisuals";
import {useEffect,useRef,useState} from "react";
import type {BatchInput,LocalResult} from "./parallelReplay";
type RiskScenario=LocalResult["scenarios"][number]&{funding_paid:string;liquidation_count:number;preliq_count:number};
type RiskResult=Omit<LocalResult,"scenarios">&{scenarios:RiskScenario[];risk:unknown};
const defaults={leverage:"1",margin_mode:"isolated",initial_rate_floor:"",maintenance_rate:"",max_notional:"",liquidation_fee_bps:"",profile_start:"",profile_end:"",profile_source:"",preliq_points:"0",scalp_start:"",scalp_end:""};
export function LeveragedRunner({input,graph,disabled,onBusy,from,to}:{input:BatchInput;graph:string;disabled:boolean;onBusy:(v:boolean)=>void;from:string;to:string}){
 const [v,setV]=useState(defaults),[mark,setMark]=useState(""),[funding,setFunding]=useState(""),[fund,setFund]=useState(false),[scalp,setScalp]=useState(false),[ack,setAck]=useState(false),[interval,setInterval]=useState("28800"),[anchor,setAnchor]=useState("0");
 const [fundingMode,setFundingMode]=useState<"operator_supplied"|"estimated_previous_hour_mark_open">("operator_supplied"),[unit,setUnit]=useState<FundingRateUnit|"">(""),[fundingNote,setFundingNote]=useState("");
 const [markInput,setMarkInput]=useState<{csv:string;symbol:string}|null>(null),[markNote,setMarkNote]=useState("");
 useEffect(()=>{setMark("");setMarkInput(null);setMarkNote("");setFunding("");setFundingNote("");setResult(null);},[input.csv,input.symbol]);
 const [busy,setBusy]=useState(false),[loading,setLoading]=useState(false),[status,setStatus]=useState("Ready"),[error,setError]=useState(""),[result,setResult]=useState<RiskResult|null>(null);
 const worker=useRef<Worker|null>(null),timer=useRef<number|undefined>(undefined),seq=useRef(0);
 function close(){seq.current++;worker.current?.terminate();worker.current=null;window.clearTimeout(timer.current);setBusy(false);onBusy(false);}
 useEffect(()=>()=>{worker.current?.terminate();window.clearTimeout(timer.current);},[]);
 async function file(f:File|undefined,kind:"mark"|"funding"){setLoading(true);setError("");setResult(null);try{
  if(f&&f.size>16777216)throw new Error("Risk CSV exceeds 16 MiB.");
  const text=f?await f.text():"";if(kind==="mark"){clearEstimate();setMark(text);setMarkInput({csv:input.csv,symbol:input.symbol});setMarkNote("Custom mark CSV.");}else {setFunding(text);setFundingMode("operator_supplied");setFundingNote("Operator-supplied funding CSV; not independently attested.");}
 }catch(e){setError(String(e));if(kind==="mark")setMark("");else setFunding("");}finally{setLoading(false);}}
 async function loadMark(){
  setLoading(true);onBusy(true);setError("");clearEstimate();setResult(null);setMark("");setMarkInput(null);setMarkNote("");
  try{
   const lines=input.csv.trimEnd().split(/\r?\n/);if(lines.length<3)throw Error("Load trade candles first.");
   const first=Number(lines[1].split(",")[0]),last=Number(lines[lines.length-1].split(",")[0]);
   if(!Number.isSafeInteger(first)||!Number.isSafeInteger(last)||first%86400||(last+60)%86400)throw Error("Repository mark loading requires complete UTC days. Import a matching custom mark CSV for partial days.");
   const from=new Date(first*1000).toISOString().slice(0,10),to=new Date(last*1000).toISOString().slice(0,10);
   const r=await loadRepositoryHistory(input.symbol,from,to,true,undefined,"mark");
   if(r.bars!==lines.length-1)throw Error("Mark and trade counts differ.");
   setMark(r.csv);setMarkInput({csv:input.csv,symbol:input.symbol});setMarkNote("Verified "+r.bars.toLocaleString()+" repository mark candles. Exact trade alignment is checked by the risk engine.");
  }catch(e){setError(String(e));}finally{setLoading(false);onBusy(false);}
 }
 async function loadEstimate(){
  if(!unit||!mark||markInput?.csv!==input.csv||markInput?.symbol!==input.symbol)return;
  setLoading(true);onBusy(true);setError("");setFunding("");setFundingNote("");setResult(null);
  try{
   const lines=input.csv.trimEnd().split(/\r?\n/),start=Number(lines[1].split(",")[0]),end=Number(lines.at(-1)!.split(",")[0])+60;
   if(!Number.isSafeInteger(start)||!Number.isSafeInteger(end)||start%86400||end%86400||end<=start||end-start>31*86400)throw Error("Select matching complete UTC days, up to 31.");
   const first=new Date(start*1000).toISOString().slice(0,10),last=new Date((end-1)*1000).toISOString().slice(0,10),previous=new Date((start-86400)*1000).toISOString().slice(0,10);
   const [prior,current]=await Promise.all([loadRepositoryHistory(input.symbol,previous,previous,true,undefined,"funding"),loadRepositoryHistory(input.symbol,first,last,true,undefined,"funding")]);
   const result=estimateFunding(prior.csv,current.csv,mark,start,end,Number(interval),Number(anchor),unit);
   setFunding(result.csv);setFundingMode("estimated_previous_hour_mark_open");setFundingNote("RESEARCH ESTIMATE: "+result.count+" modeled boundaries; preceding hourly close, "+unit+" input, mark-open proxy. Not actual exchange settlements.");
  }catch(e){setError(String(e));}finally{setLoading(false);onBusy(false);}
 }
 function clearEstimate(){if(fundingMode==="estimated_previous_hour_mark_open"){setFunding("");setFundingNote("");}setResult(null);}
 function run(long=false){
  if(disabled||busy||loading)return;setError("");setResult(null);setBusy(true);onBusy(true);setStatus(long?"Initializing continuous leveraged replay":"Initializing risk replay");
  const id=++seq.current;
  try{
   const w=new Worker(new URL("./browser-python-worker.js",document.baseURI));worker.current=w;
   w.onmessage=e=>{const m=e.data;if(m.id!==seq.current)return;
    if(m.status==="progress")setStatus("Running "+m.progress+"%");
    if(m.status==="done"){setResult(m.result);setStatus("Completed");close();}
    if(m.status==="error"){setError(m.message);setStatus("Failed");close();}
   };
   w.onerror=()=>{if(seq.current===id){setError("Risk worker failed.");setStatus("Failed");close();}};
   timer.current=window.setTimeout(()=>{if(seq.current===id){setError(long?"Long risk run exceeded 30 minutes.":"Risk run exceeded 120 seconds.");setStatus("Timed out");close();}},long?1800000:120000);
   const risk={...v,funding_enabled:fund,funding_csv:fund?funding:"",...(fund?{funding_provenance:fundingMode}:{}),funding_interval_seconds:Number(interval),funding_anchor_epoch:Number(anchor),scalp_enabled:scalp,acknowledge:ack};
   w.postMessage(long?{id,action:"long_repository",from,to,symbol:input.symbol,settings:input.settings,assume:input.assume,graph,risk}:{id,...input,graph,details:true,risk:{...risk,mark_csv:mark}});
  }catch(e){setError(String(e));close();}
 }
 const riskReady=input.assume&&ack&&!!v.profile_start&&!!v.profile_end&&!!v.profile_source&&!!v.initial_rate_floor&&!!v.maintenance_rate&&!!v.max_notional&&!!v.liquidation_fee_bps&&(!fund||!!funding)&&(!scalp||!!v.scalp_start&&!!v.scalp_end);
 const ready=riskReady&&!!input.csv&&!!mark&&markInput?.csv===input.csv&&markInput?.symbol===input.symbol;
 return <section className="scenario" style={{marginTop:16}}><h2>Leveraged reference replay</h2><p className="notice">Uses current strategy and trade CSV, separate mark data and explicit historical fixed-tier assumptions. Exposure % now represents equity allocated to initial margin; notional scales with leverage. No exchange-certified liquidation or historical eligibility inference. Mark-vertex protection can miss gaps. Single isolated/cross position only.</p>
 <fieldset disabled={disabled||busy||loading} style={{minWidth:0}}>
 <button disabled={!input.csv} onClick={()=>void loadMark()}>Load matching repository mark prices</button><p className="muted">{markNote}</p>
 <label>Risk mark CSV<input aria-label="Risk mark CSV" type="file" accept=".csv,text/csv" onChange={e=>void file(e.target.files?.[0],"mark")}/></label><small>time,open,high,low,close — one exact mark candle per trade candle.</small>
 <div className="visual-config">{Object.entries(v).filter(([k])=>k!=="margin_mode"&&!k.startsWith("scalp_")).map(([k,value])=><label key={k}>{k==="profile_start"||k==="profile_end"?k+" UTC epoch seconds":k}<input value={value} onChange={e=>{setV(old=>({...old,[k]:e.target.value}));setResult(null);}}/></label>)}
 <label>Margin mode<select value={v.margin_mode} onChange={e=>setV(old=>({...old,margin_mode:e.target.value}))}><option>isolated</option><option>cross</option></select></label></div>
 <label className="check"><input type="checkbox" checked={fund} onChange={e=>setFund(e.target.checked)}/> Include funding cost model</label>
 {fund&&<><label>Funding CSV<input aria-label="Funding CSV" type="file" accept=".csv,text/csv" onChange={e=>void file(e.target.files?.[0],"funding")}/></label><small>time,rate,reference_mark — signed decimal rate at every scheduled boundary. Supply independently sourced settlement reference/index prices; CSV is not independently verified here.</small><label>Funding interval seconds<input value={interval} onChange={e=>{clearEstimate();setInterval(e.target.value);}}/></label><label>Funding anchor UTC epoch<input value={anchor} onChange={e=>{clearEstimate();setAnchor(e.target.value);}}/></label><label>Observation rate units (explicit assumption)<select value={unit} onChange={e=>{clearEstimate();setUnit(e.target.value as FundingRateUnit|"");}}><option value="">Choose documented units</option><option value="percent">Percentage points (0.01 = 0.01%)</option><option value="decimal">Decimal fraction (0.0001 = 0.01%)</option></select></label><button disabled={!unit||!mark||markInput?.csv!==input.csv||markInput?.symbol!==input.symbol} onClick={()=>void loadEstimate()}>Estimate funding from repository observations</button><p className="muted">Research only: uses the preceding completed hourly close and settlement-minute mark open as a proxy for the true index price. No actual settlement verification; no estimate for missing observations.</p><p>{fundingNote}</p></>}
 <label className="check"><input type="checkbox" checked={scalp} onChange={e=>setScalp(e.target.checked)}/> Assume eligible 30-minute closing fee waiver (single entry, full close; no vouchers)</label>
 {scalp&&<>{(["scalp_start","scalp_end"] as const).map(k=><label key={k}>{k} UTC epoch seconds<input value={v[k]} onChange={e=>setV(old=>({...old,[k]:e.target.value}))}/></label>)}</>}
 <label className="check"><input type="checkbox" checked={ack} onChange={e=>setAck(e.target.checked)}/> I acknowledge supplied historical margin/fee assumptions, mark and funding provenance, and simulation limitations.</label>
 <button className="primary" disabled={!ready} onClick={()=>run()}>Run leveraged replay</button>
 <button className="primary" disabled={!riskReady||!from||!to||(fund&&fundingMode==="estimated_previous_hour_mark_open")} onClick={()=>run(true)}>Run continuous leveraged backtest</button><p className="muted">Uses repository trade and mark prices for {from} to {to} UTC, up to 1098 days within common coverage, no CSV needed except explicit settlements if enabled. Summary only; funding excluded unless operator CSV supplied. Repository funding estimate is limited to short replay. Fixed-tier assumptions are not exchange-certified.</p></fieldset>
 {busy&&<button onClick={()=>{close();setStatus("Cancelled");}}>Cancel leveraged replay</button>}<p role="status">{status}</p>{error&&<pre role="alert" className="error" style={{whiteSpace:"pre-wrap",overflowWrap:"anywhere"}}>{error}</pre>}
 {result&&<><h3>Leveraged reference result</h3>{(result.risk as {funding_provenance?:string}|null)?.funding_provenance==="estimated_previous_hour_mark_open"&&<p className="notice">Funding is a research estimate, not realized exchange funding.</p>}<ResultVisuals key={result.result_sha256} result={result} csv={input.csv}/><p className="hash">Result SHA-256: {result.result_sha256}</p><div className="table-wrap"><table><thead><tr><th>Path</th><th>Net P&amp;L</th><th>Drawdown %</th><th>Fees</th><th>GST</th><th>Funding paid</th><th>Liquidations</th><th>Pre-liq exits</th></tr></thead><tbody>{result.scenarios.map(s=><tr key={s.path}><td>{s.path}</td><td>{s.metrics.account_net}</td><td>{s.metrics.max_event_drawdown_pct}</td><td>{s.fees}</td><td>{s.taxes}</td><td>{s.funding_paid}</td><td>{s.liquidation_count}</td><td>{s.preliq_count}</td></tr>)}</tbody></table></div>{result.scenarios.map(s=><details key={s.path}><summary>{s.path} monthly / yearly results</summary><div className="table-wrap"><table><thead><tr><th>Period (IST)</th><th>P&amp;L</th><th>Return %</th></tr></thead><tbody>{s.monthly.map(m=><tr key={m.month}><td>{m.month}</td><td>{m.pnl}</td><td>{m.return_pct??"—"}</td></tr>)}{s.yearly?.map(y=><tr key={y.year}><td><strong>{y.year}</strong></td><td>{y.pnl}</td><td>{y.return_pct??"—"}</td></tr>)}</tbody></table></div></details>)}<details><summary>Risk assumptions and evidence</summary><pre style={{whiteSpace:"pre-wrap",overflowWrap:"anywhere"}}>{JSON.stringify(result.risk,null,2)}</pre><ul>{result.limitations.map(l=><li key={l}>{l}</li>)}</ul></details></>}
 </section>;
}
