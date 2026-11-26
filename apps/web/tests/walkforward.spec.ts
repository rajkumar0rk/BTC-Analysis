import {test,expect} from "@playwright/test";
import {readFileSync} from "node:fs";
test("local chronological study matches native fold hashes",async({page})=>{
 test.setTimeout(180000);
 const o=JSON.parse(readFileSync("tests/browser-oracle.json","utf8"));
 await page.addInitScript(()=>{Object.defineProperty(navigator,"hardwareConcurrency",{get:()=>8,configurable:true});Object.defineProperty(navigator,"deviceMemory",{get:()=>8,configurable:true});});
 await page.goto("/");await page.getByRole("button",{name:"Open local Python runner"}).click();
 await page.getByLabel("Historical CSV").setInputFiles({name:"fixture.csv",mimeType:"text/csv",buffer:Buffer.from(o.csv)});
 await page.getByLabel("Local visual source").fill(JSON.stringify(o.graph));
 await page.getByText("Assume CSV times are candle opens; provenance and contract specs are unverified.").click();
 await page.getByLabel("Training window minutes").fill("20");
 await page.getByLabel("Test window minutes").fill("10");
 await page.getByLabel("Study values 1").fill("2,5");
 await page.getByLabel("Study maximum drawdown %").fill("100");
 await page.getByText("Acknowledge research-only chronological testing, independent balances and non-attested holdout.").click();
 await page.getByRole("button",{name:"Run walk-forward study"}).click();
 await expect(page.getByLabel("Walk-forward progress")).toContainText("2/2 completed",{timeout:150000});
 for(const f of o.walkforward)await expect(page.getByText("Fold SHA-256: "+f.fold_sha256,{exact:true})).toBeVisible();
});
