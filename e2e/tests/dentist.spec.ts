import { expect, test, type APIRequestContext } from "@playwright/test";
import { PASSWORD, USERS, login } from "./helpers";

async function apiLogin(request: APIRequestContext, email: string) {
  const res = await request.post("/api/v1/auth/login", { form: { username: email, password: PASSWORD } });
  expect(res.ok()).toBeTruthy();
  const { access_token, user } = await res.json();
  return { headers: { Authorization: `Bearer ${access_token}` }, user };
}

test("dentist sees only own schedule and can't do front-desk actions", async ({ page, request }) => {
  // Book an appointment for dentist1 as the receptionist, through the API.
  const rec = await apiLogin(request, USERS.receptionist);
  const den = await apiLogin(request, USERS.dentist);
  const dentists = await (await request.get("/api/v1/dentists", { headers: rec.headers })).json();
  const own = dentists.find((d: { user_id: number | null }) => d.user_id === den.user.id);
  const patient = await (
    await request.post("/api/v1/patients", {
      headers: rec.headers,
      data: { first_name: "Dent", last_name: `E2E${Date.now()}`, phone: "09 555 0101" },
    })
  ).json();
  let appt;
  for (let i = 2; i < 16 && !appt; i++) {
    const day = new Date(Date.now() + i * 86_400_000).toISOString().slice(0, 10);
    const slots = await (await request.get(`/api/v1/dentists/${own.id}/slots?date=${day}`, { headers: rec.headers })).json();
    if (slots.length)
      appt = await (
        await request.post("/api/v1/appointments", {
          headers: rec.headers,
          data: { ...slots[0], patient_id: patient.id, dentist_id: own.id, reason: "Check-up" },
        })
      ).json();
  }
  expect(appt?.id).toBeTruthy();

  await login(page, USERS.dentist);
  // No dentist picker: the backend only returns the dentist's own appointments (403 for others).
  await expect(page.getByLabel("Dentist")).toHaveCount(0);
  await page.goto("/calendar");
  await expect(page.getByRole("heading", { name: "Calendar" })).toBeVisible();
  await expect(page.getByLabel("Dentist")).toHaveCount(0);

  await page.goto(`/appointments/${appt.id}`);
  await expect(page.getByRole("button", { name: "Mark completed" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Confirm" })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Reschedule" })).toHaveCount(0);
  await expect(page.getByLabel("Reason")).toBeDisabled();

  // Dentists may edit notes.
  await page.getByLabel("Notes").fill("Sensitive on upper left molar");
  await page.getByRole("button", { name: "Save notes" }).click();
  await page.reload();
  await expect(page.getByLabel("Notes")).toHaveValue("Sensitive on upper left molar");
});
