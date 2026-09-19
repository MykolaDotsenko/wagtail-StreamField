import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";


async function login(page) {
  await page.goto("/accounts/login/");
  await page.getByLabel("Username").fill("e2e");
  await page.getByLabel("Password").fill("e2e-password");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).toHaveURL(/\/home\/today\/$/);
}


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


function projectSuffix(testInfo) {
  return testInfo.project.name.includes("mobile") ? "mobile" : "desktop";
}


function isoToday() {
  return new Date().toISOString().slice(0, 10);
}


test("anonymous users can discover public content without seeing private household state", async ({ page }) => {
  await page.goto("/search/?query=Take&kind=home");

  await expect(page.getByRole("heading", { name: "Find what helps at home" })).toBeVisible();
  await expect(page.getByText("Take out recycling", { exact: true })).toHaveCount(0);
  await expect(page.getByText("Sign in before searching private household state.")).toBeVisible();
  await expect(page.getByRole("link", { name: "Your home" })).toHaveCount(0);

  await page.goto("/search/?query=tomato&kind=recipes");
  const recipeLink = page.getByRole("link", { name: /Tomato pasta/ }).first();
  await expect(recipeLink).toBeVisible();
  await recipeLink.click();

  await expect(page.getByRole("heading", { name: "Tomato pasta", level: 1 })).toBeVisible();
  await expect(page.getByRole("link", { name: "Compare with Pantry" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Plan this dinner" })).toHaveCount(0);
  await expectNoA11yViolations(page);
});


test("shopping workflow handles duplicate capture, completion, undo and focused shopping mode", async ({ page }, testInfo) => {
  const suffix = projectSuffix(testInfo);
  const itemName = `Workflow milk ${suffix}`;

  await login(page);
  await page.goto("/home/shopping/");

  await page.getByLabel("Item").fill(itemName);
  await page.getByRole("button", { name: "Add item" }).click();
  await expect(page.getByText(itemName, { exact: true })).toBeVisible();

  await page.getByLabel("Item").fill(`  ${itemName.toUpperCase()}  `);
  await page.getByRole("button", { name: "Add item" }).click();

  const openRow = page.locator(".shopping-item-row").filter({ hasText: itemName }).first();
  await expect(openRow).toContainText("Quantity 2");
  await expect(page.getByText(itemName, { exact: true })).toHaveCount(1);

  await openRow.getByRole("button", { name: `Mark ${itemName} as bought` }).click();
  await expect(page.getByRole("heading", { name: "Bought" })).toBeVisible();
  await expect(page.getByRole("button", { name: `Move ${itemName} back to shopping` })).toBeVisible();

  await page.getByRole("button", { name: `Move ${itemName} back to shopping` }).click();
  await expect(page.getByRole("button", { name: `Mark ${itemName} as bought` })).toBeVisible();

  await page.getByRole("button", { name: `Remove ${itemName} from shopping` }).click();
  await expect(page.getByText(`${itemName} removed`, { exact: true })).toBeVisible();
  await expect(page.getByText(itemName, { exact: true })).toHaveCount(0);

  await page.getByRole("button", { name: "Undo" }).click();
  await expect(page.getByText(itemName, { exact: true })).toBeVisible();

  await page.getByRole("link", { name: "Shopping mode" }).click();
  await expect(page.getByRole("link", { name: "Exit shopping mode" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "What do you need?" })).toHaveCount(0);
  await expect(page.getByRole("button", { name: `Remove ${itemName} from shopping` })).toHaveCount(0);
  await expect(page.getByText(itemName, { exact: true })).toBeVisible();
  await expectNoA11yViolations(page);

  await page.getByRole("link", { name: "Exit shopping mode" }).click();
  await expect(page.getByRole("heading", { name: "What do you need?" })).toBeVisible();
});


test("pantry recovers from precise-validation errors and low stock adds to Shopping idempotently", async ({ page }, testInfo) => {
  const suffix = projectSuffix(testInfo);
  const preciseName = `Workflow flour ${suffix}`;
  const lowName = `Workflow oats ${suffix}`;

  await login(page);
  await page.goto("/home/pantry/");

  await page.getByLabel("Item").fill(preciseName);
  await page.getByText("Stock details", { exact: true }).click();
  await page.getByLabel("Tracking style").selectOption("precise");
  await page.getByRole("button", { name: "Add to pantry" }).click();

  await expect(page.getByText("Enter the current amount.")).toBeVisible();
  await expect(page.getByText("Choose a unit for precise tracking.")).toBeVisible();
  await expect(page.locator("details.pantry-disclosure")).toHaveAttribute("open", "");

  await page.getByLabel("Exact amount").fill("1.5");
  await page.getByLabel("Unit").selectOption("kg");
  await page.getByRole("button", { name: "Add to pantry" }).click();
  await expect(page.getByText(preciseName, { exact: true })).toBeVisible();

  await page.getByLabel("Item").fill(lowName);
  await page.getByText("Stock details", { exact: true }).click();
  await page.getByLabel("Approximate level").selectOption("low");
  await page.getByRole("button", { name: "Add to pantry" }).click();

  const pantryRow = page.locator(".pantry-item-row").filter({ hasText: lowName }).first();
  await expect(pantryRow).toContainText("Low stock");
  await pantryRow.getByRole("button", { name: "Add to Shopping" }).click();

  const samePantryRow = page.locator(".pantry-item-row").filter({ hasText: lowName }).first();
  await samePantryRow.getByRole("button", { name: "Add to Shopping" }).click();

  await page.goto("/home/shopping/");
  const shoppingRow = page.locator(".shopping-item-row").filter({ hasText: lowName }).first();
  await expect(shoppingRow).toContainText("Quantity 1");
  await expectNoA11yViolations(page);
});


test("daily routine completion advances to the next occurrence without creating backlog noise", async ({ page }, testInfo) => {
  const suffix = projectSuffix(testInfo);
  const title = `Workflow reset ${suffix}`;

  await login(page);
  await page.goto("/home/routines/");

  await page.getByLabel("Routine").fill(title);
  await page.getByLabel("Next due").fill(isoToday());
  await page.getByLabel("Repeat").selectOption("daily");
  await page.getByRole("button", { name: "Add routine" }).click();

  const dueCard = page.locator(".routine-card").filter({ hasText: title }).first();
  await expect(dueCard).toBeVisible();
  await expect(dueCard).toContainText("Today");

  await dueCard.getByRole("button", { name: "Done" }).click();
  await expect(page.getByText(new RegExp(`^${title} completed\\. Next due `))).toBeVisible();

  await expect(page.locator(".routine-card").filter({ hasText: title })).toHaveCount(0);
  const upcomingRow = page.locator(".item-row").filter({ hasText: title }).first();
  await expect(upcomingRow).toBeVisible();
  await expect(upcomingRow).toContainText("Daily");
  await expectNoA11yViolations(page);

  await upcomingRow.getByRole("link", { name: "Edit" }).click();
  await page.getByRole("button", { name: "Archive" }).click();
  await expect(page.getByText(title, { exact: true })).toHaveCount(0);
});
