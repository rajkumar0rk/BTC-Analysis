import {test,expect} from "@playwright/test";
test("repository history loads real checked partitions, caches, and rejects out-of-range requests",async({page})=>{
 await page.goto("/");
 await page.getByRole("button",{name:"Open local Python runner"}).click();
 await page.getByLabel("History from (UTC)").fill("2025-01-31");
 await page.getByLabel("History to (UTC)").fill("2025-02-01");
 await page.getByRole("button",{name:"Load existing historical data"}).click();
 await expect(page.getByText(/Verified 2,880 contiguous 1m candles/)).toBeVisible({timeout:30000});
 await page.getByRole("button",{name:"Load existing historical data"}).click();
 await expect(page.getByText(/2\/2 cached partitions/)).toBeVisible({timeout:30000});
 await page.getByLabel("Local instrument").selectOption("ETHUSD");
 await expect(page.getByRole("button",{name:"Run local Python",exact:true})).toBeDisabled();
 await page.getByRole("button",{name:"Load existing historical data"}).click();
 await expect(page.getByText(/Verified 2,880 contiguous 1m candles/)).toBeVisible({timeout:30000});
 await page.getByLabel("History to (UTC)").fill("2025-04-01");
 await page.getByRole("button",{name:"Load existing historical data"}).click();
 await expect(page.getByRole("alert")).toContainText("1–31 calendar days");
 await page.getByLabel("History from (UTC)").fill("2024-01-01");
 await page.getByLabel("History to (UTC)").fill("2024-01-02");
 await page.getByRole("button",{name:"Load existing historical data"}).click();
 await expect(page.getByRole("alert")).toContainText("outside published archive coverage");
});
test("repository history refuses a corrupt compressed download",async({page})=>{
 await page.route("**/history-archive/BTCUSD/*.bin",r=>r.fulfill({body:"corrupt"}));
 await page.goto("/");await page.getByRole("button",{name:"Open local Python runner"}).click();
 await page.getByRole("button",{name:"Load existing historical data"}).click();
 await expect(page.getByRole("alert")).toContainText("checksum mismatch");
});

test("retained BTC 2024 and repository mark data are available",async({page})=>{
 await page.goto("/");await page.getByRole("button",{name:"Open local Python runner"}).click();
 await expect(page.getByRole("table",{name:"Published historical coverage"})).toContainText("2024-01-01");
 await page.getByLabel("History from (UTC)").fill("2024-04-01");await page.getByLabel("History to (UTC)").fill("2024-04-02");
 await page.getByRole("button",{name:"Load existing historical data"}).click();await expect(page.getByText(/Verified 2,880 contiguous 1m candles/)).toBeVisible({timeout:30000});
 await page.getByRole("button",{name:"Load matching repository mark prices"}).click();await expect(page.getByText(/Verified 2,880 repository mark candles/)).toBeVisible({timeout:30000});
 await expect(page.getByRole("table",{name:"Published historical coverage"}).getByRole("row").filter({hasText:"Funding 1h observations"})).toContainText("2024-01-01");
 await page.getByLabel("History from (UTC)").fill("2025-01-31");await page.getByLabel("History to (UTC)").fill("2025-02-01");
 await page.getByRole("button",{name:"Load existing historical data"}).click();await expect(page.getByText(/Verified 2,880 contiguous 1m candles/)).toBeVisible({timeout:30000});
 await page.getByRole("button",{name:"Load matching repository mark prices"}).click();await expect(page.getByText(/Verified 2,880 repository mark candles/)).toBeVisible({timeout:30000});
});
