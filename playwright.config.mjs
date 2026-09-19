import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 45_000,
  expect: {
    timeout: 7_500,
  },
  reporter: [
    ["list"],
    ["html", { outputFolder: "playwright-report", open: "never" }],
  ],
  use: {
    baseURL: "http://127.0.0.1:8000",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
      },
    },
  ],
  webServer: {
    command:
      "python manage.py migrate --noinput && " +
      "python manage.py seed_demo --reset --username e2e --password e2e-password && " +
      "python manage.py runserver 127.0.0.1:8000 --noreload",
    url: "http://127.0.0.1:8000/health/",
    reuseExistingServer: false,
    timeout: 120_000,
  },
});
