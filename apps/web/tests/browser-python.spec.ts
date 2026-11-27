import {test,expect} from "@playwright/test";
import {readFileSync} from "node:fs";
test("standalone Python worker matches native Python and supports warm rerun",async({page})=>{
 test.setTimeout(180000);
 const oracle=JSON.parse(readFileSync("tests/browser-oracle.json","utf8"));
 const apiCalls:string[]=[];page.on("request",r=>{if(r.url().includes("/v1/"))apiCalls.push(r.url());});
 await page.goto("/");
 await page.getByRole("button",{name:"Open local Python runner"}).click();
 await page.getByLabel("Historical CSV").setInputFiles({name:"fixture.csv",mimeType:"text/csv",buffer:Buffer.from(oracle.csv)});
 await page.getByLabel("Local visual source").fill(JSON.stringify(oracle.graph));
 await page.getByText("Assume CSV times are candle opens; provenance and contract specs are unverified.").click();
 await page.getByRole("button",{name:"Run local Python"}).click();
 await expect(page.getByRole("heading",{name:"Local reference result"})).toBeVisible({timeout:125000});
 await expect(page.getByText("Result SHA-256: "+oracle.result.result_sha256,{exact:false})).toBeVisible();
 await expect(page.getByLabel("Interactive backtest results")).toBeVisible();
 await expect(page.getByRole("img",{name:"Monthly net P&L (IST)"})).toBeVisible();
 await expect(page.getByRole("img",{name:"Sampled account equity (UTC)"})).toBeVisible();
 await expect(page.getByRole("heading",{name:"Local closed trade ledger"})).toBeVisible();
 await page.getByLabel("Chart scenario").selectOption("O-L-H-C");
 const inspect=page.getByRole("button",{name:/Inspect local trade-/}).first();
 if(await inspect.count()){await inspect.click();await expect(page.getByRole("img",{name:"Local trade candlestick chart"})).toBeVisible();}
 await page.setViewportSize({width:390,height:844});
 expect(await page.getByLabel("Interactive backtest results").evaluate(e=>e.scrollWidth<=e.clientWidth+2)).toBe(true);
 await page.getByRole("button",{name:"Run local Python"}).click();
 await expect(page.getByRole("heading",{name:"Local reference result"})).toBeVisible({timeout:30000});
 await expect(page.getByText("Result SHA-256: "+oracle.result.result_sha256,{exact:false})).toBeVisible();
 await expect(page.getByLabel("Cache statistics")).toContainText("Candle cache: hit");
 await page.getByRole("button",{name:"Save CSV on this device"}).click();
 await expect(page.getByText("Validated CSV saved on this device.",{exact:false})).toBeVisible();
 await page.reload();await page.getByRole("button",{name:"Open local Python runner"}).click();
 await page.getByRole("button",{name:"Load saved CSV",exact:true}).click();
 await expect(page.getByText("Saved CSV restored and checksum verified.",{exact:false})).toBeVisible();
 await page.getByLabel("Local visual source").fill("import os");
 await page.getByText("Assume CSV times are candle opens; provenance and contract specs are unverified.").click();
 await page.getByRole("button",{name:"Run local Python"}).click();
 await expect(page.getByRole("alert")).toBeVisible({timeout:10000});
 expect(apiCalls).toEqual([]);
});

test("handwritten SDK strategy validation and editable parameters",async({page})=>{
 test.setTimeout(180000);
 await page.goto("/");
 await page.getByRole("button",{name:"Open local Python runner"}).click();
 const source=page.getByLabel("Local visual source");
 await source.fill("from decimal import Decimal as D\nfrom btc_analysis.strategy import PythonStrategy\nclass Strategy(PythonStrategy):\n    period = parameter(20, 2, 50)\n    def on_signal(self, ctx):\n        pass\n");
 await page.getByRole("button",{name:"Validate strategy source"}).click();
 await expect(page.getByText("Source validation passed",{exact:true})).toBeVisible({timeout:125000});
 await page.getByLabel("Parameter period").fill("30");
 await page.getByRole("button",{name:"Apply parameter values to source"}).click();
 await expect(source).toHaveValue(/parameter\(30, 2, 50\)/,{timeout:125000});
 await source.fill("import os");
 await page.getByRole("button",{name:"Validate strategy source"}).click();
 await expect(page.getByText("Source validation failed",{exact:true})).toBeVisible({timeout:125000});
});

test("custom indicator declaration is validated and visible",async({page})=>{
 test.setTimeout(180000);
 await page.goto("/");
 await page.getByRole("button",{name:"Open local Python runner"}).click();
 await page.getByLabel("Local visual source").fill("from btc_analysis.strategy import PythonStrategy\nfrom btc_analysis.contracts import Timeframe\nclass Strategy(PythonStrategy):\n    def custom_indicators(self):\n        return ((\"user_formula\", Timeframe(900), 3, \"formula\"),)\n    def formula(self, bars, previous):\n        return mean(series(bars, \"close\"))\n    def on_signal(self, ctx):\n        pass\n");
 await page.getByRole("button",{name:"Validate strategy source"}).click();
 await expect(page.getByText("Source validation passed",{exact:true})).toBeVisible({timeout:125000});
 await page.getByText("Custom indicators (1)",{exact:true}).click();
 await expect(page.getByText("user_formula · 15m · 3 completed candles · formula")).toBeVisible();
});
