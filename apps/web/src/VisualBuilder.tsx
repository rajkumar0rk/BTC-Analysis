import {useEffect,useState} from "react";
import type {Api,Catalog,Strategy,Revision} from "./api";
import {frames,ops,keys,initialGraph,newCondition,newGroup,advancedDefaults} from "./visualTypes";
import type {Graph,Frame,Operand,Condition,Rule,Group,Compiled,AdvancedControls} from "./visualTypes";
const captions={long_entry:"Long entry",short_entry:"Short entry",long_exit:"Long exit",short_exit:"Short exit"};
const opLabels={gt:">",gte:"≥",lt:"<",lte:"≤",eq:"=",cross_up:"Crosses above",cross_down:"Crosses below"};
const frameLabel=(n:number)=>n>=86400?"1 day":n>=3600?n/3600+"h":n/60+"m";
const message=(e:unknown)=>e instanceof Error?e.message:"Request failed";
export function FrameSelect({value,change,label,disabled}:{value:Frame;change:(v:Frame)=>void;label:string;disabled:boolean}){
 return <label>{label}<select aria-label={label} value={value} disabled={disabled} onChange={e=>change(Number(e.target.value) as Frame)}>{frames.map(f=><option key={f} value={f}>{frameLabel(f)}</option>)}</select></label>;
}
function OperandEdit({value,change,catalog,label,disabled}:{value:Operand;change:(o:Operand)=>void;catalog:Catalog;label:string;disabled:boolean}){
 const options=catalog.indicators.flatMap(i=>i.outputs.map(o=>({name:i.name+"."+o,defaults:i.defaults})));
 const selected=value.kind==="indicator"?options.find(x=>x.name===value.name):undefined;
 return <div className="operand"><label>{label}<select aria-label={label+" type"} disabled={disabled} value={value.kind} onChange={e=>{
 const k=e.target.value;if(k==="constant")change({kind:k,value:"0"});else if(k==="price")change({kind:k,timeframe:900,field:"close"});else{const o=options.find(x=>x.name==="ema.value")??options[0];change({kind:"indicator",timeframe:900,name:o.name,parameters:{...o.defaults}});}
 }}><option value="price">Candle field</option><option value="indicator">Indicator</option><option value="constant">Number</option></select></label>
 {value.kind==="constant"?<label>Value<input aria-label={label+" value"} disabled={disabled} value={value.value} onChange={e=>change({...value,value:e.target.value})}/></label>:<>
 <FrameSelect label={label+" timeframe"} value={value.timeframe} disabled={disabled} change={timeframe=>change({...value,timeframe})}/>
 {value.kind==="price"?<label>Field<select aria-label={label+" field"} disabled={disabled} value={value.field} onChange={e=>change({...value,field:e.target.value as Extract<Operand,{kind:"price"}>["field"]})}>{["open","high","low","close","volume"].map(f=><option key={f}>{f}</option>)}</select></label>:
 <><label>Indicator<select aria-label={label+" indicator"} disabled={disabled} value={value.name} onChange={e=>{const o=options.find(x=>x.name===e.target.value)!;change({...value,name:o.name,parameters:{...o.defaults}});}}>{options.map(o=><option key={o.name}>{o.name}</option>)}</select></label>
 {Object.entries(selected?.defaults??{}).map(([k,def])=><label key={k}>{k}<input aria-label={label+" "+k} disabled={disabled} value={value.parameters[k]??def} onChange={e=>change({...value,parameters:{...value.parameters,[k]:typeof def==="number"?Number(e.target.value):e.target.value}})}/></label>)}</>}
 </>}
 </div>;
}
export function RuleEdit({rule,title,change,catalog,disabled}:{rule:Rule;title:string;change:(r:Rule)=>void;catalog:Catalog;disabled:boolean}){
 function group(i:number,g:Group){change({...rule,groups:rule.groups.map((x,j)=>j===i?g:x)});}
 function move(i:number,j:number){if(j<0||j>=rule.groups.length||i===j)return;const g=[...rule.groups];g.splice(j,0,g.splice(i,1)[0]);change({...rule,groups:g});}
 return <fieldset className="visual-rule" disabled={disabled}><legend>{title}</legend><label className="check"><input type="checkbox" checked={rule.enabled} onChange={e=>change({...rule,enabled:e.target.checked,groups:e.target.checked&&!rule.groups.length?[newGroup()]:rule.groups})}/> Enable {title.toLowerCase()}</label>
 {rule.enabled&&<><label>Combine groups<select value={rule.mode} onChange={e=>change({...rule,mode:e.target.value as Rule["mode"]})}><option value="all">AND — all groups</option><option value="any">OR — any group</option></select></label>
 {rule.groups.map((g,i)=><section key={i} className="rule-group" draggable={!disabled} onDragStart={e=>{e.dataTransfer.setData("text/plain",title+":"+i);e.dataTransfer.effectAllowed="move";}} onDragOver={e=>e.preventDefault()} onDrop={e=>{e.preventDefault();const [t,k]=e.dataTransfer.getData("text/plain").split(":");if(t===title&&/^\d+$/.test(k))move(Number(k),i);}}>
 <div className="head"><strong>Group {i+1}</strong><div className="rule-actions"><button type="button" disabled={i===0} onClick={()=>move(i,i-1)} aria-label={title+" group "+(i+1)+" move up"}>↑</button><button type="button" disabled={i===rule.groups.length-1} onClick={()=>move(i,i+1)} aria-label={title+" group "+(i+1)+" move down"}>↓</button><button type="button" disabled={rule.groups.length===1} onClick={()=>change({...rule,groups:rule.groups.filter((_,j)=>i!==j)})}>Remove group</button></div></div>
 <label>Combine conditions<select value={g.mode} onChange={e=>group(i,{...g,mode:e.target.value as Group["mode"]})}><option value="all">AND — all conditions</option><option value="any">OR — any condition</option></select></label>
 {g.conditions.map((c,j)=>{const update=(v:Condition)=>group(i,{...g,conditions:g.conditions.map((x,k)=>k===j?v:x)});const label=title+" group "+(i+1)+" condition "+(j+1);return <div className="condition" key={j}><div className="condition-head"><small>{label}</small><button type="button" disabled={g.conditions.length===1} onClick={()=>group(i,{...g,conditions:g.conditions.filter((_,k)=>k!==j)})}>Remove condition</button></div><div className="condition-grid">
 <OperandEdit label={label+" left"} value={c.left} catalog={catalog} disabled={disabled} change={left=>update({...c,left})}/>
 <label>Comparison<select aria-label={label+" comparison"} value={c.op} onChange={e=>update({...c,op:e.target.value as Condition["op"]})}>{ops.map(o=><option key={o} value={o}>{opLabels[o]}</option>)}</select></label>
 <OperandEdit label={label+" right"} value={c.right} catalog={catalog} disabled={disabled} change={right=>update({...c,right})}/></div></div>;})}
 <button type="button" disabled={g.conditions.length>=8} onClick={()=>group(i,{...g,conditions:[...g.conditions,newCondition()]})}>Add condition</button></section>)}
 <button type="button" disabled={rule.groups.length>=4} onClick={()=>change({...rule,groups:[...rule.groups,newGroup()]})}>Add group</button></>}
 </fieldset>;
}
export function AdvancedVisualControls({graph,change,disabled}:{graph:Graph;change:(g:Graph)=>void;disabled:boolean}){
 const a=graph.advanced;
 function edit(patch:Partial<AdvancedControls>){if(a)change({...graph,advanced:{...a,...patch}});}
 return <fieldset className="visual-rule" disabled={disabled}><legend>Advanced entry and risk controls</legend>
 <label className="check"><input type="checkbox" checked={!!a} onChange={e=>{if(e.target.checked)change({...graph,advanced:advancedDefaults()});else{const next={...graph};delete next.advanced;change(next);}}}/> Enable advanced controls</label>
 {a&&<><div className="visual-config">
 <label>Entry frequency<select value={a.entry_mode} onChange={e=>edit({entry_mode:e.target.value as AdvancedControls["entry_mode"]})}><option value="continuous">While entry condition is true</option><option value="once_per_true_run">One filled entry per continuous true condition</option></select></label>
 <label>Consecutive signal confirmations<input aria-label="Consecutive signal confirmations" type="number" min={1} max={100} value={a.confirmation_bars} onChange={e=>edit({confirmation_bars:Number(e.target.value)})}/></label>
 <label>Cooldown signal candles after exit<input type="number" min={0} max={10000} value={a.cooldown_bars} onChange={e=>edit({cooldown_bars:Number(e.target.value)})}/></label>
 <label>Exit distance unit<select aria-label="Exit distance unit" value={a.exit_mode} onChange={e=>edit({exit_mode:e.target.value as AdvancedControls["exit_mode"]})}><option value="percent">Percentage</option><option value="points">Fixed price points</option></select></label>
 {a.exit_mode==="points"&&<><label>Stop loss points<input value={a.stop_points} onChange={e=>edit({stop_points:e.target.value})}/></label><label>Take profit points<input value={a.target_points} onChange={e=>edit({target_points:e.target.value})}/></label></>}
 </div><p>Entry weekdays (IST). Exits remain enabled every day.</p><div className="head">{["Mon","Tue","Wed","Thu","Fri","Sat","Sun"].map((day,i)=><label className="check" key={day}><input type="checkbox" checked={a.weekdays_ist.includes(i)} onChange={e=>edit({weekdays_ist:e.target.checked?[...a.weekdays_ist,i]:a.weekdays_ist.filter(x=>x!==i)})}/>{day}</label>)}</div>
 <small>Confirmation and re-entry use completed signal candles. Fixed points require exact instrument tick multiples and activate at the entry minute; percentage exits retain next-minute protection. Both paths remain modeled, not tick execution.</small></>}
 </fieldset>;
}
export function VisualBuilder({api,strategies,refresh,report,openPython}:{api:Api;strategies:Strategy[];refresh:()=>Promise<void>;report:(e:unknown)=>void;openPython:(r:Revision)=>void}){
 const [graph,setGraph]=useState<Graph>(initialGraph);const [catalog,setCatalog]=useState<Catalog|null>(null);
 const [compiled,setCompiled]=useState<Compiled|null>(null);const [revision,setRevision]=useState<Revision|null>(null);
 const [name,setName]=useState("");const [selected,setSelected]=useState("");const [busy,setBusy]=useState(false);const [error,setError]=useState("");const [note,setNote]=useState("");
 const stale=!!revision&&strategies.some(s=>s.id===revision.id&&(s.latest_version>revision.version||s.archived||s.frozen_version!==null));
 useEffect(()=>{let active=true;api.catalog().then(v=>{if(active)setCatalog(v);}).catch(e=>{if(active)report(e);});return()=>{active=false;};},[api]);
 function edit(g:Graph){setGraph(g);setCompiled(null);setError("");setNote("");}
 async function load(){const s=strategies.find(x=>x.id===selected);if(!s)return;setBusy(true);setError("");setNote("");try{const r=await api.revision(s.id,s.latest_version);const c=await api.recoverVisual(r.source);setRevision(r);setName(r.name);setGraph(c.graph);setCompiled(c);setNote("Recovered exact visual source.");}catch(e){setError(message(e));}finally{setBusy(false);}}
 async function generate(save=false){setBusy(true);setError("");setNote("");try{const c=await api.compileVisual(graph);setCompiled(c);setGraph(c.graph);if(save){const v=await api.validate(c.source);if(!v.syntax_valid)throw new Error("Generated source syntax check failed");const r=revision?await api.save(revision.id,revision.version,c.source):await api.create(name.trim(),c.source);setRevision(r);setName(r.name);setNote("Saved visual strategy version "+r.version+".");await refresh();}}catch(e){setError(message(e));}finally{setBusy(false);}}
 return <><section className="panel"><div className="head"><h2>Visual Python strategy builder</h2><button disabled={busy} onClick={()=>{setRevision(null);setName("");setSelected("");edit(initialGraph());}}>New visual strategy</button></div>
 <p className="muted">Build conditions, reorder groups by dragging or arrow buttons, then generate Python. No execution is enabled. Manual code changes cannot be converted back automatically.</p>
 <div className="visual-load"><label>Open saved visual strategy<select aria-label="Saved visual strategy" disabled={busy} value={selected} onChange={e=>setSelected(e.target.value)}><option value="">Select strategy</option>{strategies.filter(s=>!s.archived).map(s=><option key={s.id} value={s.id}>{s.name} · v{s.latest_version}</option>)}</select></label><button disabled={busy||!selected} onClick={()=>void load()}>Open visual version</button></div>
 <label>Strategy name<input value={name} disabled={busy||!!revision} maxLength={100} onChange={e=>setName(e.target.value)}/></label>
 <div className="visual-config"><FrameSelect label="Signal timeframe" value={graph.signal_timeframe} disabled={busy} change={v=>edit({...graph,signal_timeframe:v})}/><FrameSelect label="Execution timeframe" value={graph.execution_timeframe} disabled={busy} change={v=>edit({...graph,execution_timeframe:v})}/>
 {(["exposure_pct","stop_loss_pct","take_profit_pct"] as const).map((k,i)=><label key={k}>{["Equity exposure (%)","Stop loss (%)","Take profit (%)"][i]}<input disabled={busy} value={graph[k]} onChange={e=>edit({...graph,[k]:e.target.value})}/></label>)}</div>
 <AdvancedVisualControls graph={graph} change={edit} disabled={busy}/><small>{graph.advanced?.exit_mode==="points"?"Fixed-point protection activates on the entry minute. Percentage fields are inactive.":"Percentage protection activates on the candle after the entry fill callback."} Position size is notional exposure at 1×.</small></section>
 {catalog?<div className="visual-rules">{keys.map(k=><RuleEdit key={k} title={captions[k]} rule={graph[k]} change={r=>edit({...graph,[k]:r})} catalog={catalog} disabled={busy}/>)}</div>:<section className="panel">Loading SDK catalog…</section>}
 <section className="panel"><div className="head"><h2>Generated Python</h2><div className="rule-actions"><button disabled={busy||!catalog} onClick={()=>void generate()}>Generate Python</button><button className="primary" disabled={busy||!catalog||!name.trim()||stale} onClick={()=>void generate(true)}>Save visual strategy</button>{revision&&<button disabled={busy} onClick={()=>openPython(revision)}>Open saved Python</button>}</div></div>
 {stale&&<p role="alert">Newer, frozen or archived revision. Reopen or clone in the strategy library before saving.</p>}
 {error&&<p className="error" role="alert">{error}</p>}{note&&<p role="status">{note}</p>}
 {compiled?<><p className="muted hash">Graph SHA-256: {compiled.graph_sha256}</p><pre className="generated-code" aria-label="Generated Python source">{compiled.source.split("\n").slice(1).join("\n")}</pre><small>The stored source includes a generated metadata header for exact visual recovery.</small></>:<p className="muted">Generate a preview after editing the rules.</p>}</section></>;
}
