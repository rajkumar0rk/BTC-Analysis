import {test,expect} from "@playwright/test";
test("continuous repository replay crosses a month boundary without CSV import",async({page})=>{
 test.setTimeout(180000);
 await page.goto("/");
 await page.getByRole("button",{name:"Open local Python runner"}).click();
 await page.getByLabel("History from (UTC)").fill("2025-01-31");
 await page.getByLabel("History to (UTC)").fill("2025-02-01");
 await page.getByText("Assume CSV times are candle opens; provenance and contract specs are unverified.").click();
 await page.getByRole("button",{name:"Run continuous multi-year backtest"}).click();
 await expect(page.getByRole("heading",{name:"Local reference result"})).toBeVisible({timeout:150000});
 await expect(page.getByText("Archive manifest SHA-256:",{exact:false})).toBeVisible();
 await expect(page.getByText("Yearly performance (IST)",{exact:true})).toHaveCount(2);
 await expect(page.getByText("2880",{exact:true})).toHaveCount(2);
 await expect(page.getByRole("button",{name:"Save CSV on this device"})).toBeDisabled();
});
