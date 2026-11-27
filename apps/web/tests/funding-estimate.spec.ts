import {test,expect} from "@playwright/test";
import {estimateFunding} from "../src/fundingEstimate";
const start=1704067200,end=start+86400;
const h="time,open,high,low,close,volume\n";
const prior=h+(start-3600)+",0.01,0.01,0.01,0.01,\n";
const current=h+Array.from({length:24},(_,i)=>(start+i*3600)+",0.02,0.02,0.02,0.02,").join("\n")+"\n";
const mark="time,open,high,low,close\n"+Array.from({length:1440},(_,i)=>(start+i*60)+",100,101,99,101").join("\n")+"\n";
test("funding estimate uses prior completed hour, explicit units and boundary mark open",()=>{
 const r=estimateFunding(prior,current,mark,start,end,28800,0,"percent");
 expect(r.count).toBe(3);
 expect(r.csv.split("\n")[1]).toBe(start+",0.0001,100");
 expect(r.csv.split("\n")[2]).toBe((start+28800)+",0.0002,100");
 expect(estimateFunding(prior,current,mark,start,end,28800,0,"decimal").csv).toContain(start+",0.01,100");
});
test("funding estimate rejects missing observations, unaligned boundary and incomplete marks",()=>{
 expect(()=>estimateFunding(h,current,mark,start,end,28800,0,"percent")).toThrow("Missing preceding");
 expect(()=>estimateFunding(prior,current,mark,start,end,28800,60,"percent")).toThrow("hourly aligned");
 expect(()=>estimateFunding(prior,current,mark.split("\n").slice(0,-2).join("\n"),start,end,28800,0,"percent")).toThrow("Mark range");
});
