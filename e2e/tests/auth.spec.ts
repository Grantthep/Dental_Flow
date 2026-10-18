import { expect, test } from "@playwright/test";
import { USERS, login } from "./helpers";

test("protected pages send you to the login page", async ({ page }) => {
  await page.goto("/patients");
  await expect(page).toHaveURL(/\/login\?next=%2Fpatients/);
});

test("wrong password shows an error and stays logged out", async ({ page }) => {
  await page.goto("/login");
  // unique email per run so the login rate limit (5 failures per email) is never hit
  await page.getByLabel("Email").fill(`nobody-${Date.now()}@example.com`);
  await page.getByLabel("Password").fill("wrong-password");
  await page.getByRole("button", { name: "Log in" }).click();
  await expect(page.getByRole("alert").filter({ hasText: /./ })).toHaveText("Incorrect email or password");
  await expect(page).toHaveURL(/\/login/);
});

test("admin logs in, sees reports, logs out", async ({ page }) => {
  await login(page, USERS.admin);
  await expect(page.getByText("Clinic Admin")).toBeVisible();
  await expect(page.getByRole("link", { name: "Reports" })).toBeVisible();
  await page.getByRole("button", { name: "Log out" }).click();
  await expect(page).toHaveURL(/\/login/);
  await page.goto("/");
  await expect(page).toHaveURL(/\/login/);
});

test("login returns you to the page you asked for", async ({ page }) => {
  await page.goto("/patients");
  await page.getByLabel("Email").fill(USERS.receptionist);
  await page.getByLabel("Password").fill(process.env.E2E_PASSWORD ?? "dentalflow-dev");
  await page.getByRole("button", { name: "Log in" }).click();
  await expect(page).toHaveURL(/\/patients$/);
});

test("dentist does not get booking or reports", async ({ page }) => {
  await login(page, USERS.dentist);
  await expect(page.getByRole("link", { name: "New booking" })).toHaveCount(0);
  await expect(page.getByRole("link", { name: "Reports" })).toHaveCount(0);
  await page.goto("/reports");
  await expect(page.getByText("You don't have access to this page")).toBeVisible();
});
