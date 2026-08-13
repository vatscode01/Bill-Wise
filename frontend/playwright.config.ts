import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright configuration for BillWise E2E tests.
 * Assumes the app is running locally on port 3000.
 * Start with: docker compose up  OR  npm run dev
 */
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,   // false to avoid conflicting test data
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  timeout: 30_000,
  reporter: [["html", { open: "never" }], ["list"]],

  use: {
    baseURL: "http://localhost:3000",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },

  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "firefox",
      use: { ...devices["Desktop Firefox"] },
    },
  ],
});
