import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";


async function expectNoA11yViolations(page) {
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
    .analyze();

  expect(
    results.violations,
    results.violations
      .map((violation) => `${violation.id}: ${violation.help}`)
      .join("\n"),
  ).toEqual([]);
}


test("golden household journey remains accessible and connected", async ({ page }, testInfo) => {
  await page.goto("/accounts/login/");
  await page.getByLabel("Username").fill("e2e");
  await page.getByLabel("Password").fill("e2e-password");
  await page.getByRole("button", { name: "Sign in" }).click();

  await page.goto("/search/?query=tomato&kind=recipes");
  await expect(page.getByRole("heading", { name: "Find what helps at home" })).toBeVisible();
  const recipeLink = page.getByRole("link", { name: /Tomato pasta/ }).first();
  await expect(recipeLink).toBeVisible();
  await recipeLink.click();

  await expect(page.getByRole("heading", { name: "Tomato pasta", level: 1 })).toBeVisible();
  await expect(page.getByText("Missing", { exact: true }).first()).toBeVisible();
  await expectNoA11yViolations(page);
  await page.screenshot({
    path: testInfo.outputPath("recipe-readiness.png"),
    fullPage: true,
  });

  await page.getByRole("button", { name: /Add 2 needed items to Shopping/ }).click();
  await expect(page.getByRole("heading", { name: "Tomato pasta", level: 1 })).toBeVisible();

  await page.getByRole("link", { name: "Plan this dinner" }).click();
  await expect(page.getByRole("heading", { name: "Dinner plan", level: 1 })).toBeVisible();
  const dateInput = page.getByLabel("Dinner date");
  const today = new Date().toISOString().slice(0, 10);
  await dateInput.fill(today);
  await page.getByRole("button", { name: "Save dinner" }).click();
  await expect(page.getByText("Tomato pasta", { exact: true }).first()).toBeVisible();

  await page.goto("/home/shopping/");
  await expect(page.getByText("Tomato", { exact: true })).toBeVisible();
  await expect(page.getByText("Pasta", { exact: true })).toBeVisible();
  await page.getByLabel("Item").fill("Oat milk");
  await page.getByRole("button", { name: "Add item" }).click();
  await expect(page.getByText("Oat milk", { exact: true })).toBeVisible();
  await expectNoA11yViolations(page);
  await page.screenshot({
    path: testInfo.outputPath("shopping.png"),
    fullPage: true,
  });

  await page.goto("/home/pantry/");
  await page.getByLabel("Item").fill("Rice");
  await page.getByRole("button", { name: "Add to pantry" }).click();
  await expect(page.getByText("Rice", { exact: true })).toBeVisible();
  await expectNoA11yViolations(page);

  await page.goto("/search/?query=Oat&kind=home");
  await expect(page.getByRole("heading", { name: "Your home" })).toBeVisible();
  await expect(page.getByText("Oat milk", { exact: true })).toBeVisible();

  await page.goto("/home/today/");
  await expect(page.getByRole("heading", { name: "Today", level: 1 })).toBeVisible();
  await expect(page.getByText("Tomato pasta", { exact: true }).first()).toBeVisible();
  await expectNoA11yViolations(page);
  await page.screenshot({
    path: testInfo.outputPath("today.png"),
    fullPage: true,
  });
});
