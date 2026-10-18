# DentalFlow — API endpoints (draft)

Base path: `/api/v1`. JSON in and out. Full interactive docs at `/docs` once the backend runs.

Roles: **A** = admin, **R** = receptionist, **D** = dentist (own data only).

## Auth (owned by Member 3)
Every endpoint below except `/auth/login` needs `Authorization: Bearer <token>`. Full rules: [roles.md](roles.md).

| Method | Path | Who | Purpose |
|---|---|---|---|
| POST | `/auth/login` | public | form `username=<email>&password=` → `{access_token, token_type, expires_in, user}`; `429` after 5 failures |
| GET | `/auth/me` | all | current user |
| POST | `/auth/change-password` | all | `{current_password, new_password}` → `204` |

## Users
| Method | Path | Who | Purpose |
|---|---|---|---|
| GET | `/users` | A | list staff accounts |
| POST | `/users` | A | create staff account |
| GET | `/users/{id}` | A | detail |
| PATCH | `/users/{id}` | A | update name / role / deactivate / reset password (`409` for the last admin) |

## Patients
| Method | Path | Who | Purpose |
|---|---|---|---|
| GET | `/patients?q=&page=&size=` | A R D | search by name/phone, paginated |
| POST | `/patients` | A R | create |
| GET | `/patients/{id}` | A R D | detail |
| PATCH | `/patients/{id}` | A R | update / deactivate |

## Dentists
| Method | Path | Who | Purpose |
|---|---|---|---|
| GET | `/dentists` | all | list (active by default) |
| POST | `/dentists` | A | create |
| GET | `/dentists/{id}` | all | detail |
| PATCH | `/dentists/{id}` | A | update / deactivate |

## Availability
| Method | Path | Who | Purpose |
|---|---|---|---|
| GET | `/dentists/{id}/availability` | all | weekly working hours |
| PUT | `/dentists/{id}/availability` | A | replace the weekly schedule |
| GET | `/dentists/{id}/time-off` | all | days off / leave |
| POST | `/dentists/{id}/time-off` | A | add time off |
| DELETE | `/time-off/{id}` | A | remove time off |
| GET | `/dentists/{id}/slots?date=YYYY-MM-DD&duration=30` | all | free bookable slots for a day |

## Appointments
| Method | Path | Who | Purpose |
|---|---|---|---|
| GET | `/appointments?date_from=&date_to=&dentist_id=&patient_id=&status=&page=&size=` | all | calendar / list / patient history; `status` can repeat; D sees own only |
| POST | `/appointments` | A R | book — `409` if slot taken |
| GET | `/appointments/{id}` | A R D | detail (D: own only, others `404`) |
| PATCH | `/appointments/{id}` | A R D | D: own only, `notes` + status `completed`/`no_show`. Update notes / reason / status (`booked→confirmed→completed`; completed, cancelled, no_show are final → `409 bad_status`) |
| POST | `/appointments/{id}/reschedule` | A R | new start/end — `409` if slot taken |
| POST | `/appointments/{id}/cancel` | A R | set status `cancelled` |

## Audit
| Method | Path | Who | Purpose |
|---|---|---|---|
| GET | `/audit-logs?entity_type=&entity_id=` | A | change history |

## Reports
Dates are clinic-local days, `date_from` and `date_to` both inclusive, max 3 years.
Every row has `total, completed, cancelled, no_show, upcoming` (upcoming = booked + confirmed).

| Method | Path | Who | Purpose |
|---|---|---|---|
| GET | `/reports/appointments?date_from=&date_to=&group_by=day\|week\|month&dentist_id=` | A | counts per period (`period` = day / Monday / 1st of month); empty periods included as 0 |
| GET | `/reports/dentists?date_from=&date_to=` | A | per-dentist counts + `booked_minutes` (chair time, excl. cancelled/no-show) |
| GET | `/reports/rates?date_from=&date_to=&dentist_id=` | A | `cancellation_rate` = cancelled / total; `no_show_rate` = no_show / (completed + no_show); `null` if no data |

## Error format
Booking errors:
```json
{ "detail": "Dentist already has an appointment at this time", "code": "slot_taken" }
```
Codes: `slot_taken`, `patient_busy`, `outside_hours`, `time_off`, `in_past`, `bad_status`, `too_early` (completed / no-show before the start time).
Other errors use FastAPI's default `{ "detail": ... }` (422 validation errors have a list in `detail`).

| Status | When |
|---|---|
| 400 / 422 | invalid input |
| 401 | not logged in / token expired / account deactivated |
| 403 | wrong role |
| 404 | not found |
| 409 | conflict (double booking) |
| 429 | too many failed logins |
