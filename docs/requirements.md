# DentalFlow — Requirements (draft)

> Draft by Member 1 (Backend & DB). Items marked **[confirm]** are assumptions to check with the clinic.

## Users and roles
| Role | Can do |
|---|---|
| Admin | Everything: manage staff accounts, dentists, clinic settings, view reports and audit log |
| Receptionist | Manage patients, book / reschedule / cancel appointments for any dentist, view calendar |
| Dentist | View own schedule and patients, update status of own appointments (completed, no-show), add notes |

## Patients
- Store: first name, last name, date of birth, gender, phone, email, address, allergies / medical notes.
- Phone is required (main contact); email optional. **[confirm]**
- Search by name or phone.
- Patients are never hard-deleted (appointments keep history); they can be deactivated.

## Dentists
- Store: name, specialty, phone, email, active flag.
- A dentist can be linked to a user account to log in.

## Opening hours and availability
- Each dentist has weekly working hours per weekday. Breaks are gaps between time blocks
  (e.g. Mon 09:00–12:00 and 13:00–17:00 = lunch break 12–13).
- Days off / holidays / leave are separate time-off periods.
- Clinic opening hours: Mon–Sat 09:00–18:00, closed Sunday. **[confirm]**

## Appointment rules
- An appointment has: patient, dentist, start time, end time, reason, notes, status.
- Default length 30 minutes; slots on 15-minute boundaries. **[confirm]**
- Status flow: `booked → confirmed → completed`, or `booked/confirmed → cancelled / no_show`.
- No double booking: a dentist cannot have two overlapping active appointments
  (cancelled and no-show appointments don't block the slot).
- Cannot book in the past, outside the dentist's working hours, or during time off.
- Reschedule = change start/end time (same rules apply). Cancel keeps the record with status `cancelled`.
- A patient should not have two overlapping appointments either.

## Audit
- Every create / update / cancel of an appointment records who did it, when, and what changed.

## Data protection
- Synthetic data only until the clinic approves real data and backups exist.
- All times stored in UTC; displayed in clinic timezone. **[confirm timezone]**

## Out of scope for V1
Billing, reminders (SMS/email), treatment history, online self-booking by patients.
