/* Dedicated trusted-code runner. No credentials, arbitrary Python or user JS. */
let runtime;
async function start(){
 const indexURL=new URL("./python-runtime/",self.location.href).href;
 importScripts(indexURL+"pyodide.js");
 const py=await self.loadPyodide({indexURL});
 await py.loadPackage(["pydantic","tzdata"]);
 const response=await fetch(indexURL+"studio-python.zip",{credentials:"omit"});
 if(!response.ok)throw new Error("Python SDK assets unavailable");
 py.FS.writeFile("/studio-python.zip",new Uint8Array(await response.arrayBuffer()));
 py.runPython("import sys; sys.path.insert(0, '/studio-python.zip')\nfrom btc_analysis.service.browser_replay import replay\nfrom btc_analysis.service.browser_cache import ReplayCache\ncache=ReplayCache()\nimport json");
 return py;
}
let busy=false;
self.onmessage=async({data:m})=>{
 if(busy)return;
 busy=true;
 const t=performance.now();
 try{
  if(typeof m.csv!=="string"||typeof m.graph!=="string"||m.csv.length>16777216||m.graph.length>65536)throw new Error("Invalid bounded input");
  self.postMessage({id:m.id,status:"initializing"});
  runtime??=start();const py=await runtime;
  self.postMessage({id:m.id,status:"running"});
  py.globals.set("request_json",JSON.stringify({csv_text:m.csv,graph_text:m.graph,symbol:m.symbol,settings:m.settings,assume_open:m.assume,risk:m.risk??null}));
  const progress=p=>self.postMessage({id:m.id,status:"progress",progress:p});
  py.globals.set("report_progress",progress);
  const started=performance.now();
  try{
   const result=py.runPython("json.dumps(replay(**json.loads(request_json), progress=report_progress, cache=cache), allow_nan=False)");
   const cacheStats=JSON.parse(py.runPython("json.dumps(cache.stats)"));
   self.postMessage({id:m.id,status:"done",result:JSON.parse(result),cacheStats,elapsed_ms:performance.now()-started,total_ms:performance.now()-t});
  }finally{py.globals.delete("request_json");py.globals.delete("report_progress");}
 }catch(e){self.postMessage({id:m.id,status:"error",message:String(e).slice(0,2000)});}
 finally{busy=false;}
};
