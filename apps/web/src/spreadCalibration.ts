export type SpreadSample={received_utc:string;bid:string;ask:string;half_spread_bps:string};
export type SpreadReport={schema:1;symbol:"BTCUSD";source:string;rejected:number;conflicting_receipts:number;files:{file:string;sha256:string}[];samples:SpreadSample[]};
export async function loadSpreadReport(signal?:AbortSignal):Promise<SpreadReport>{
 const r=await fetch(new URL("history-archive/BTCUSD/spread-calibration.json",document.baseURI),{credentials:"omit",redirect:"error",referrerPolicy:"no-referrer",signal});
 if(!r.ok||!r.body)throw Error("Spread calibration archive unavailable.");
 const reader=r.body.getReader(),decoder=new TextDecoder("utf-8",{fatal:true});let n=0,text="";
 try{while(true){const x=await reader.read();if(x.done)break;n+=x.value.byteLength;if(n>4*1024*1024){await reader.cancel();throw Error("Spread report exceeds size limit.");}text+=decoder.decode(x.value,{stream:true});}text+=decoder.decode();}finally{reader.releaseLock();}
 const d=JSON.parse(text) as SpreadReport;
 if(d.schema!==1||d.symbol!=="BTCUSD"||!Array.isArray(d.samples)||d.samples.length>20000||!Array.isArray(d.files)||d.files.some(x=>!/^\d{4}-\d{2}-\d{2}\.jsonl$/.test(x.file)||!/^[a-f0-9]{64}$/.test(x.sha256)))throw Error("Invalid spread report.");
 let prev=-Infinity;for(const s of d.samples){const t=Date.parse(s.received_utc),bid=Number(s.bid),ask=Number(s.ask),half=Number(s.half_spread_bps);
  if(!Number.isFinite(t)||t<=prev||!Number.isFinite(bid)||!Number.isFinite(ask)||bid<=0||ask<=bid||!/^\d{1,12}(?:\.\d{1,8})?$/.test(s.half_spread_bps)||!Number.isFinite(half)||Math.abs(half-(ask-bid)*10000/(ask+bid))>1.1e-8)throw Error("Invalid spread observation.");prev=t;
 }
 return d;
}
export function summarizeSpread(samples:SpreadSample[],cutoff:string){
 const t=Date.parse(cutoff+"T00:00:00Z");
 if(!/^\d{4}-\d{2}-\d{2}$/.test(cutoff)||!Number.isFinite(t)||new Date(t).toISOString().slice(0,10)!==cutoff)throw Error("Choose a valid exclusive UTC cutoff date.");
 const rows=samples.filter(s=>Date.parse(s.received_utc)<t);
 if(rows.length===0)return null;
 const values=rows.map(s=>Number(s.half_spread_bps)).sort((a,b)=>a-b);
 const first=Date.parse(rows[0].received_utc),last=Date.parse(rows.at(-1)!.received_utc);
 const expected=Math.max(1,Math.floor((last-first)/900000)+1);
 const quantile=(p:number)=>values[Math.max(0,Math.ceil(values.length*p)-1)];
 return {count:rows.length,first:rows[0].received_utc,last:rows.at(-1)!.received_utc,expected,coverage:100*rows.length/expected,median:quantile(.5),p90:quantile(.9),max:values.at(-1)!};
}
export function combinedBps(impact:string,spread:number){
 if(!/^\d{1,12}(?:\.\d{1,8})?$/.test(impact)||!Number.isFinite(spread)||spread<0)throw Error("Invalid impact/spread assumption.");
 const total=Math.ceil((Number(impact)+spread)*1e8-1e-6)/1e8;
 if(total>100)throw Error("Combined slippage exceeds 100 bps model limit.");
 return total.toFixed(8).replace(/\.?0+$/,"")||"0";
}
