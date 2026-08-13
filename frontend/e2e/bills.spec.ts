import { test, expect, Page } from "@playwright/test";

const EMAIL = `bills_e2e_${Date.now()}@billwise.test`;
const PASSWORD = "TestPass123!";

async function loginAs(page: Page, email: string, password: string) {
  await page.goto("/register");
  await page.getByLabel(/email/i).fill(email);
  await page.getByLabel(/password/i).fill(password);
  await page.getByRole("button", { name: /register/i }).click();
  await expect(page).toHaveURL(/dashboard/);
}

test.describe("Bills Management", () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, EMAIL, PASSWORD);
    await page.goto("/bills");
  });

  test("shows empty state for a new user", async ({ page }) => {
    await expect(page.getByText(/haven't added any bills/i)).toBeVisible();
  });

  test("can add a new bill", async ({ page }) => {
    await page.getByRole("button", { name: /add bill/i }).click();

    // Fill in the modal
    await page.getByLabel(/provider/i).fill("Electricity");
    await page.getByLabel(/amount/i).fill("2500");
    await page.getByLabel(/due date/i).fill("2026-09-30");

    await page.getByRole("button", { name: /save bill/i }).click();

    // Bill appears in the table
    await expect(page.getByText("Electricity")).toBeVisible();
  });

  test("can mark a bill as paid", async ({ page }) => {
    // Create a bill first
    await page.getByRole("button", { name: /add bill/i }).click();
    await page.getByLabel(/provider/i).fill("Internet");
    await page.getByLabel(/amount/i).fill("999");
    await page.getByLabel(/due date/i).fill("2026-09-25");
    await page.getByRole("button", { name: /save bill/i }).click();
    await expect(page.getByText("Internet")).toBeVisible();

    // Mark paid
    await page.getByRole("button", { name: /mark paid/i }).first().click();
    await expect(page.getByText("Paid")).toBeVisible();
  });

  test("can delete a bill", async ({ page }) => {
    // Create a bill
    await page.getByRole("button", { name: /add bill/i }).click();
    await page.getByLabel(/provider/i).fill("ToDelete");
    await page.getByLabel(/amount/i).fill("100");
    await page.getByLabel(/due date/i).fill("2026-09-20");
    await page.getByRole("button", { name: /save bill/i }).click();
    await expect(page.getByText("ToDelete")).toBeVisible();

    // Delete it
    await page.getByRole("button", { name: /delete/i }).first().click();
    // Confirm in the dialog
    await page.getByRole("button", { name: /confirm|yes|delete/i }).click();
    await expect(page.getByText("ToDelete")).not.toBeVisible();
  });
});
