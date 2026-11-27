import {test,expect} from "@playwright/test";
import {summarizeSpread,combinedBps} from "../src/spreadCalibration";
test("sparse quote cutoff and conservative spread scenarios",()=>{
 const samples=[1,2,3].map((v,i)=>({received_utc:"2026-11-"+String(17+i)+"T00:00:00.000Z",bid:"100",ask:"101",half_spread_bps:String(v)}));
 expect(summarizeSpread(samples,"2026-11-17")).toBeNull();
 const s=summarizeSpread(samples,"2026-11-19")!;
 expect(s.count).toBe(2);expect(s.median).toBe(1);expect(s.p90).toBe(2);
 expect(combinedBps("0.1",0.01234567)).toBe("0.11234567");
 expect(()=>combinedBps("100",1)).toThrow("100 bps");
});
test("actual calibration archive is available and does not auto-change execution assumptions",async({page})=>{
 await page.goto("/");await page.getByRole("button",{name:"Open local Python runner"}).click();
 await page.getByText("Observed bid-ask spread calibration (research assumptions)",{exact:true}).click();
 await expect(page.getByText(/Published samples:/)).toBeVisible({timeout:30000});
 await expect(page.getByText("No observations before this cutoff. No historical spread is inferred.")).toBeVisible();
 await expect(page.getByRole("button",{name:"Apply combined execution cost"})).toBeDisabled();
 await page.getByLabel("Calibration cutoff (exclusive UTC date)").fill("2026-11-28");
 await expect(page.getByText(/approximate 15m sampling coverage/)).toBeVisible();
 await page.getByText("Apply a fixed research assumption, not verified historical fills.",{exact:false}).click();
 await page.getByRole("button",{name:"Apply combined execution cost"}).click();
 await expect(page.getByText(/Applied .* bps to the shared slippage input/)).toBeVisible();
});
