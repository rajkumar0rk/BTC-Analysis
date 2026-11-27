/* Dedicated local runner. Custom source is interpreted by a bounded SDK, never eval/exec. */
let runtime;
async function start(){
 const indexURL=new URL("./python-runtime/",self.location.href).href;
 importScripts(indexURL+"pyodide.js");
 const py=await self.loadPyodide({indexURL});
 await py.loadPackage(["pydantic","tzdata"]);
 const response=await fetch(indexURL+"studio-python.zip",{credentials:"omit"});
 if(!response.ok)throw new Error("Python SDK assets unavailable");
 py.FS.writeFile("/studio-python.zip",new Uint8Array(await response.arrayBuffer()));
 py.runPython("import sys; sys.path.insert(0, '/studio-python.zip')\nfrom btc_analysis.service.browser_replay import replay\nfrom btc_analysis.service.browser_cache import ReplayCache\nfrom btc_analysis.service.walkforward import browser_fold\nfrom btc_analysis.visual import Graph, compile_graph\ncache=ReplayCache()\nimport json");
 return py;
}
async function archiveBytes(url,max){
 const response=await fetch(url,{credentials:"omit",redirect:"error",referrerPolicy:"no-referrer"});
 if(!response.ok||!response.body)throw Error("Archive unavailable (HTTP "+response.status+")");
 const reader=response.body.getReader(),chunks=[];let length=0;
 try{for(;;){const {done,value}=await reader.read();if(done)break;length+=value.length;if(length>max){await reader.cancel();throw Error("Archive download exceeds limit");}chunks.push(value);}}finally{reader.releaseLock();}
 const bytes=new Uint8Array(length);let offset=0;for(const c of chunks){bytes.set(c,offset);offset+=c.length;}return bytes;
}
async function longReplay(m,t){
 const studyMode=m.action==="repository_study";
 if(typeof m.graph!=="string"||m.graph.length>65536||!["BTCUSD","ETHUSD"].includes(m.symbol)||m.assume!==true)throw Error("Invalid long replay request");
 self.postMessage({id:m.id,status:"initializing"});
 runtime??=start();const py=await runtime;
 py.runPython("from btc_analysis.service.browser_long_replay import plan_archive, replay_archive\nfrom btc_analysis.service.browser_archive_study import study_download_plan, repository_fold");
 const root=new URL("./history-archive/"+m.symbol+"/",self.location.href);
 const manifest=new TextDecoder("utf-8",{fatal:true}).decode(await archiveBytes(new URL("manifest.json",root),262144));
 const markRoot=new URL("mark_1m/",root);
 const markManifest=m.risk?new TextDecoder("utf-8",{fatal:true}).decode(await archiveBytes(new URL("manifest.json",markRoot),262144)):null;
 const common={manifest_text:manifest,symbol:m.symbol,from_date:m.from,to_date:m.to,graph_text:m.graph,settings:m.settings,assume_open:m.assume,folder:"/long-history"};
 const input=studyMode?{...common,study:m.study,fold:m.fold,...(m.risk?{risk:m.risk,mark_manifest:markManifest}:{})}:{...common,risk:m.risk??null,mark_manifest:markManifest};
 py.globals.set("long_json",JSON.stringify(input));
 const progress=p=>{self.postMessage({id:m.id,status:"progress",progress:Math.min(99,15+Math.floor(p*.85))});return true;};
 py.globals.set("report_progress",progress);
 let folder=false;
 try{
  const plan=JSON.parse(py.runPython(studyMode?"json.dumps(study_download_plan(**{k:v for k,v in json.loads(long_json).items() if k in ('manifest_text','symbol','from_date','to_date','graph_text','study','fold')}))":"json.dumps(plan_archive(**{k:v for k,v in json.loads(long_json).items() if k in ('manifest_text','symbol','from_date','to_date')}))"));
  const markPlan=markManifest?JSON.parse(py.runPython(studyMode?"json.dumps(study_download_plan(**{**{k:v for k,v in json.loads(long_json).items() if k in ('symbol','from_date','to_date','graph_text','study','fold')}, 'manifest_text':json.loads(long_json)['mark_manifest']}))":"json.dumps(plan_archive(json.loads(long_json)['mark_manifest'],json.loads(long_json)['symbol'],json.loads(long_json)['from_date'],json.loads(long_json)['to_date']))")):null;
  const parts=[...plan.parts.map(part=>({part,root})),...(markPlan?.parts??[]).map(part=>({part,root:markRoot}))];
  py.FS.mkdir("/long-history");folder=true;
  let total=0,done=0;
  for(const {part,root:archiveRoot} of parts){
   const bytes=await archiveBytes(new URL(part.sha256+".bin",archiveRoot),4*1024*1024);total+=bytes.length;
   if(total>64*1024*1024)throw Error("Compressed history exceeds 64 MiB");
   py.FS.writeFile("/long-history/"+part.sha256+".bin",bytes);
   self.postMessage({id:m.id,status:"progress",progress:Math.floor(++done*15/parts.length)});
  }
  self.postMessage({id:m.id,status:"running"});
  const started=performance.now();
  const result=py.runPython(studyMode?"json.dumps(repository_fold(**json.loads(long_json), progress=report_progress), allow_nan=False)":"json.dumps(replay_archive(**json.loads(long_json), progress=report_progress), allow_nan=False)");
  self.postMessage({id:m.id,status:"done",result:JSON.parse(result),elapsed_ms:performance.now()-started,total_ms:performance.now()-t});
 }finally{
  py.globals.delete("long_json");py.globals.delete("report_progress");
  if(folder){for(const name of py.FS.readdir("/long-history"))if(name!=="."&&name!=="..")py.FS.unlink("/long-history/"+name);py.FS.rmdir("/long-history");}
 }
}
let busy=false;
self.onmessage=async({data:m})=>{
 if(busy)return;
 busy=true;
 const t=performance.now();
 try{
  if(m.action==="long_repository"||m.action==="repository_study"){await longReplay(m,t);return;}
  if(m.action==="visual_catalog"){
   runtime??=start();const py=await runtime;
   const result=py.runPython("from btc_analysis.indicators import CATALOG\nfrom btc_analysis.serialization import to_wire\njson.dumps(to_wire(dict(sdk_version='1',execution_allowed=False,indicators=[dict(name=k,defaults=v[0],outputs=v[1]) for k,v in CATALOG.items()])))");
   self.postMessage({id:m.id,status:"done",result:JSON.parse(result)});return;
  }
  if(m.action==="compile_visual"){
   if(typeof m.graph!=="string"||m.graph.length>65536)throw Error("Invalid graph");
   runtime??=start();const py=await runtime;
   py.globals.set("graph_json",m.graph);
   try{const result=py.runPython("json.dumps(compile_graph(Graph.model_validate_json(graph_json)))");self.postMessage({id:m.id,status:"done",result:JSON.parse(result)});}
   finally{py.globals.delete("graph_json");}
   return;
  }
  if(typeof m.csv!=="string"||typeof m.graph!=="string"||m.csv.length>16777216||m.graph.length>65536)throw new Error("Invalid bounded input");
  self.postMessage({id:m.id,status:"initializing"});
  runtime??=start();const py=await runtime;
  self.postMessage({id:m.id,status:"running"});
  const args={csv_text:m.csv,graph_text:m.graph,symbol:m.symbol,settings:m.settings,assume_open:m.assume};
  py.globals.set("request_json",JSON.stringify(m.study?{...args,study:m.study,fold:m.fold,...(m.risk?{risk:m.risk}:{})}:{...args,risk:m.risk??null,details:m.details===true}));
  const progress=p=>{self.postMessage({id:m.id,status:"progress",progress:p});return true;};
  py.globals.set("report_progress",progress);
  const started=performance.now();
  try{
   const result=py.runPython(m.study?"json.dumps(browser_fold(**json.loads(request_json), progress=report_progress), allow_nan=False)":"json.dumps(replay(**json.loads(request_json), progress=report_progress, cache=cache), allow_nan=False)");
   const cacheStats=JSON.parse(py.runPython("json.dumps(cache.stats)"));
   self.postMessage({id:m.id,status:"done",result:JSON.parse(result),cacheStats,elapsed_ms:performance.now()-started,total_ms:performance.now()-t});
  }finally{py.globals.delete("request_json");py.globals.delete("report_progress");}
 }catch(e){self.postMessage({id:m.id,status:"error",message:String(e).slice(0,2000)});}
 finally{busy=false;}
};
