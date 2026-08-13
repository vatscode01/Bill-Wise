import { test, expect } from "@playwright/test";

/**
 * E2E: Auth flow — register → login → dashboard
 * These tests hit the real running app (localhost:3000 + localhost:8000).
 * Run: npx playwright test
 */

const TEST_EMAIL = `e2e_${Date.now()}@billwise.test`;
const TEST_PASSWORD = "TestPass123!";

test.describe("Authentication Flow", () => {
  test("user can register a new account", async ({ page }) => {
    await page.goto("/register");
    await expect(page.getByRole("heading", { name: /register/i })).toBeVisible();

    await page.getByLabel(/email/i).fill(TEST_EMAIL);
    await page.getByLabel(/password/i).fill(TEST_PASSWORD);
    await page.getByRole("button", { name: /register/i }).click();

    // After register, user lands on /dashboard
    await expect(page).toHaveURL(/dashboard/);
  });

  test("user can log in with valid credentials", async ({ page }) => {
    // Register first
    await page.goto("/register");
    await page.getByLabel(/email/i).fill(TEST_EMAIL);
    await page.getByLabel(/password/i).fill(TEST_PASSWORD);
    await page.getByRole("button", { name: /register/i }).click();

    // Log out by going to /login directly
    await page.goto("/login");
    await page.getByLabel(/email/i).fill(TEST_EMAIL);
    await page.getByLabel(/password/i).fill(TEST_PASSWORD);
    await page.getByRole("button", { name: /log in/i }).click();

    await expect(page).toHaveURL(/dashboard/);
  });

  test("user cannot log in with wrong password", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel(/email/i).fill("nonexistent@test.com");
    await page.getByLabel(/password/i).fill("wrongpassword");
    await page.getByRole("button", { name: /log in/i }).click();

    // Should still be on /login
    await expect(page).toHaveURL(/login/);
    await expect(page.getByRole("alert")).toBeVisible();
  });

  test("protected routes redirect logged-out users to /login", async ({ page }) => {
    await page.goto("/dashboard");
    await expect(page).toHaveURL(/login/);

    await page.goto("/bills");
    await expect(page).toHaveURL(/login/);
  });
});
