# DentalFlow — V2 / V3 backlog

After V1 ships. Rough priority order inside each list; pick with the clinic.

## Known V1 limits (fix first if the clinic hits them)
| Limit | Why it matters | Rough fix |
|---|---|---|
| Adding time off, changing working hours or deactivating a dentist leaves already-booked appointments in place | Staff must find and move them by hand | Return the affected appointments from those endpoints so the UI can list them for rescheduling |
| Patient search is `ILIKE '%text%'` | Fine to ~100k patients (measured < 5 ms at 20k); slower beyond | `pg_trgm` GIN index on name/phone |
| `import_patients.py` imports patients only | Old appointment history isn't carried over | Same script pattern for appointments (needs the clinic's export format) |
| Login rate limit is in-process memory | Only correct with one backend process | Move to the DB or Redis when we run more than one |
| Clinic timezone is one env setting (`CLINIC_TZ`) | One clinic per deployment | Store per clinic if we ever go multi-clinic |

## V2 — clinic workflow
1. **Appointment reminders** (SMS / email / Viber) the day before. Needs: a scheduled job, a provider account,
   patient consent field, `reminder_sent_at` on appointments. Expected to cut no-shows, so measure the
   no-show rate (`/reports/rates`) before and after.
2. **Treatment history**: per-appointment treatments (tooth number, procedure, notes) on the patient page.
   New table `treatments (appointment_id, tooth, procedure_code, notes)`.
3. **Billing and payments**: price list, invoice per appointment, paid / unpaid, daily cash report.
   Money in integer minor units (no floats); every change in the audit log.
4. Patient attachments (X-rays, consent forms) — needs file storage and backups that include it.

## V3 — only once there is enough real data (≈ 6–12 months)
1. **No-show prediction**: flag risky bookings (history of no-shows, lead time, time of day) so the desk
   can call ahead. Start with a simple rule or logistic regression; check it beats "past no-show rate".
2. **Demand forecasting**: expected bookings per day/dentist from history, to plan staff and hours.
3. **Clinic chatbot** for booking questions — reuse the free-slots API (`/dentists/{id}/slots`) and
   booking rules; never let it bypass `check_bookable`.
