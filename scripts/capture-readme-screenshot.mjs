import { chromium } from "@playwright/test";
import fs from "node:fs/promises";

const baseURL = process.env.DOMONEST_BASE_URL ?? "http://127.0.0.1:8000";
const outputPath = "docs/images/domonest-today.png";

await fs.mkdir("docs/images", { recursive: true });

const browser = await chromium.launch();
const page = await browser.newPage({
  viewport: { width: 1280, height: 720 },
  deviceScaleFactor: 1,
});

try {
  await page.emulateMedia({ reducedMotion: "reduce" });

  await page.goto(`${baseURL}/accounts/login/`, { waitUntil: "networkidle" });
  await page.getByLabel("Username").fill("demo");
  await page.getByLabel("Password").fill("domonest-demo");
  await page.getByRole("button", { name: "Sign in" }).click();

  await page.goto(`${baseURL}/home/today/`, { waitUntil: "networkidle" });
  await page.getByRole("heading", { name: "Today", level: 1 }).waitFor();

  await page.screenshot({
    path: outputPath,
    fullPage: true,
  });

  console.log(`Captured ${outputPath}`);
} finally {
  await browser.close();
}
