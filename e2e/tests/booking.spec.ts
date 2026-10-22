import { expect, test } from "@playwright/test";
import { USERS, login } from "./helpers";

test("receptionist books an appointment for a new patient", async ({ page }) => {
  const last = `E2E${Date.now()}`; // unique, so reruns don't collide
  await login(page, USERS.receptionist);
  await page.locator("#main-nav").getByRole("link", { name: "New booking" }).click();

  await page.getByRole("button", { name: "+ New patient" }).click();
  const dialog = page.getByRole("dialog");
  await dialog.getByLabel("First name *").fill("Test");
  await dialog.getByLabel("Last name *").fill(last);
  await dialog.getByLabel("Phone *").fill("09 555 0100");
  await dialog.getByRole("button", { name: "Create patient" }).click();
  await expect(dialog).toBeHidden();
  await expect(page.getByText(last)).toBeVisible();

  await page.getByLabel("Dentist").selectOption({ index: 1 });
  // Find a day within the next two weeks that still has a free slot (seed hours: Mon–Sat).
  const slots = page.getByRole("group", { name: "Free time *" }).getByRole("button");
  for (let i = 2; i < 16; i++) {
    const day = new Date(Date.now() + i * 86_400_000).toISOString().slice(0, 10);
    await page.getByLabel("Date").fill(day);
    await expect(page.getByText("Finding free times…")).toBeHidden();
    if ((await slots.count()) > 0) break;
  }
  await slots.first().click();
  await page.getByLabel("Reason").fill("E2E check-up");
  await page.getByRole("button", { name: "Book appointment" }).click();

  await expect(page).toHaveURL(/\/appointments\/\d+$/);
  await expect(page.getByText(last)).toBeVisible();
  await expect(page.getByLabel("Reason")).toHaveValue("E2E check-up");
});
