import {test,expect} from "@playwright/test";
test("portfolio-style stress mode shows its explicit inputs and preserves isolated/cross tier controls",async({page})=>{
 await page.goto("/");
 await page.getByRole("button",{name:"Open local Python runner"}).click();
 const mode=page.getByLabel("Margin mode",{exact:true});
 await expect(mode).toHaveValue("isolated");
 await expect(page.getByLabel("Use explicit notional margin tiers")).toBeVisible();
 await mode.selectOption("portfolio");
 await expect(page.getByLabel("initial_shock (decimal price move)")).toBeVisible();
 await expect(page.getByLabel("maintenance_shock (decimal price move)")).toBeVisible();
 await expect(page.getByLabel("Use explicit notional margin tiers")).toHaveCount(0);
 await expect(page.getByRole("button",{name:"Run leveraged replay",exact:true})).toBeDisabled();
 await mode.selectOption("cross");
 await expect(page.getByLabel("initial_shock (decimal price move)")).toHaveCount(0);
 await expect(page.getByLabel("Use explicit notional margin tiers")).toBeVisible();
});
