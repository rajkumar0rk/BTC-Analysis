/** Research-only causal proxy, not realized exchange funding. */
export type FundingRateUnit="percent"|"decimal";
function rows(text:string,header:string,step:number){
 const lines=text.trimEnd().split(/\r?\n/);
 if(lines.shift()!==header)throw Error("Unexpected funding/mark archive header.");
 const result=new Map<number,string[]>();let previous=-1;
 for(const line of lines){
  const a=line.split(","),t=Number(a[0]);
  if(a.length!==header.split(",").length||!/^\d+$/.test(a[0])||!Number.isSafeInteger(t)||t%step||t<=previous)throw Error("Invalid or unordered archive timestamp.");
  previous=t;result.set(t,a);
 }
 return result;
}
function rate(value:string,unit:FundingRateUnit){
 const m=/^(-?)(\d{1,18})(?:\.(\d{1,18}))?$/.exec(value);
 if(!m)throw Error("Invalid funding observation precision.");
 const frac=m[3]??"",shift=unit==="percent"?2:0;
 const digits=(m[2]+frac).padStart(frac.length+shift+1,"0"),n=frac.length+shift;
 const integer=(n?digits.slice(0,-n):digits).replace(/^0+(?=\d)/,""),fraction=n?digits.slice(-n).replace(/0+$/,""):"";
 if(fraction.length>18)throw Error("Funding conversion exceeds supported precision.");
 const result=(m[1]&&/[1-9]/.test(digits)?"-":"")+integer+(fraction?"."+fraction:"");
 if(Math.abs(Number(result))>0.1)throw Error("Funding observation outside supported decimal rate range. Verify units.");
 return result;
}
export function estimateFunding(previousDay:string,observations:string,mark:string,start:number,end:number,interval:number,anchor:number,unit:FundingRateUnit){
 if(!["percent","decimal"].includes(unit)||!Number.isSafeInteger(start)||!Number.isSafeInteger(end)||start%3600||end%3600||end<=start||end-start>31*86400||!Number.isSafeInteger(interval)||interval<3600||interval>86400||interval%3600||!Number.isSafeInteger(anchor)||anchor%3600)throw Error("Estimate requires hourly aligned settlement schedule and complete UTC dates.");
 const header="time,open,high,low,close,volume",prior=rows(previousDay,header,3600),current=rows(observations,header,3600),marks=rows(mark,"time,open,high,low,close",60);
 if(marks.size!==(end-start)/60)throw Error("Mark range does not match trade range.");
 let expected=start;for(const t of marks.keys()){if(t!==expected)throw Error("Missing or unexpected minute mark.");expected+=60;}
 const first=start+((anchor-start)%interval+interval)%interval;
 const output=["time,rate,reference_mark"];
 for(let t=first;t<end;t+=interval){
  // Last completed hourly observation, never the settlement-hour close.
  const prev=current.get(t-3600)??prior.get(t-3600),m=marks.get(t);
  if(!prev||!m)throw Error("Missing preceding funding observation or settlement-minute mark at "+new Date(t*1000).toISOString());
  if(!/^\d{1,18}(?:\.\d{1,18})?$/.test(m[1])||Number(m[1])<=0)throw Error("Invalid settlement-minute mark open.");
  output.push(t+","+rate(prev[4],unit)+","+m[1]);
 }
 if(output.length===1)throw Error("No funding boundary in selected range.");
 return {csv:output.join("\n")+"\n",count:output.length-1};
}
