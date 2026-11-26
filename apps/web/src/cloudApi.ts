/** Explicit HTTPS cloud endpoint; token lives only in the returned client closure. */
export type CloudCapabilities={schema_version:1;owner:string;storage:boolean;source_execution:false;backtest_execution:false;paper_trading:false;live_orders:false;max_source_bytes:number;max_strategies:number;max_revisions:number};
export type CloudStrategy={id:string;name:string;latest_version:number};
export type CloudRevision={id:string;name?:string;version:number;source:string;code_sha256:string;created:number};
export function cloudClient(endpoint:string,token:string){
 const url=new URL(endpoint);
 if(url.protocol!=="https:"||url.username||url.password||url.search||url.hash||url.pathname!=="/")throw new Error("Cloud API must be an explicit HTTPS origin.");
 if(!/^[A-Za-z0-9_-]{43,128}$/.test(token))throw new Error("Invalid cloud token format.");
 const root=url.origin+"/v1/cloud";
 async function call<T>(path:string,method="GET",body?:unknown):Promise<T>{
  const response=await fetch(root+path,{method,headers:{Authorization:"Bearer "+token,...(body===undefined?{}:{"Content-Type":"application/json"})},body:body===undefined?undefined:JSON.stringify(body),credentials:"omit",redirect:"error",cache:"no-store",signal:AbortSignal.timeout(15000)});
  if(!response.ok)throw new Error("Cloud API request failed ("+response.status+").");
  return response.json() as Promise<T>;
 }
 const id=(value:string)=>{if(!/^[0-9a-f]{32}$/.test(value))throw new Error("Invalid strategy id");return value;};
 const version=(value:number)=>{if(!Number.isInteger(value)||value<1||value>100)throw new Error("Invalid revision");return value;};
 return {capabilities:()=>call<CloudCapabilities>("/capabilities"),strategies:()=>call<{strategies:CloudStrategy[]}>("/strategies"),
  create:(name:string,source:string)=>call<CloudRevision>("/strategies","POST",{name,source}),
  revision:(key:string,v:number)=>call<CloudRevision>("/strategies/"+id(key)+"/revisions/"+version(v)),
  revise:(key:string,v:number,source:string)=>call<CloudRevision>("/strategies/"+id(key),"PUT",{expected_version:version(v),source})};
}
