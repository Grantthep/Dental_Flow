import { expect, type Page } from "@playwright/test";

// Dev accounts created by backend/seed.py.
export const PASSWORD = process.env.E2E_PASSWORD ?? "dentalflow-dev";
export const USERS = {
  admin: "admin@example.com",
  receptionist: "reception@example.com",
  dentist: "dentist1@example.com",
};

export async function login(page: Page, email: string, password = PASSWORD) {
  await page.goto("/login");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Log in" }).click();
  await expect(page.getByRole("button", { name: "Log out" })).toBeVisible();
}
