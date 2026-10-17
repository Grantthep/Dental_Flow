# DentalFlow — API endpoints (draft)

Base path: `/api/v1`. JSON in and out. Full interactive docs at `/docs` once the backend runs.

Roles: **A** = admin, **R** = receptionist, **D** = dentist (own data only).

## Auth (owned by Member 3)
| Method | Path | Who | Purpose |
|---|---|---|---|
| POST | `/auth/login` | all | email + password → JWT |
| GET | `/auth/me` | all | current user |

## Users
| Method | Path | Who | Purpose |
|---|---|---|---|
| GET | `/users` | A | list staff accounts |
| POST | `/users` | A | create staff account |
| PATCH | `/users/{id}` | A | update role / deactivate |

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
| GET | `/appointments?date_from=&date_to=&dentist_id=&patient_id=&status=&page=&size=` | all | calendar / list / patient history; `status` can repeat; D sees own only (after auth) |
| POST | `/appointments` | A R | book — `409` if slot taken |
| GET | `/appointments/{id}` | all | detail |
| PATCH | `/appointments/{id}` | A R D | update notes / reason / status (`booked→confirmed→completed`; completed, cancelled, no_show are final → `409 bad_status`) |
| POST | `/appointments/{id}/reschedule` | A R | new start/end — `409` if slot taken |
| POST | `/appointments/{id}/cancel` | A R | set status `cancelled` |

## Audit
| Method | Path | Who | Purpose |
|---|---|---|---|
| GET | `/audit-logs?entity_type=&entity_id=` | A | change history |

## Reports (Phase 6)
| Method | Path | Who | Purpose |
|---|---|---|---|
| GET | `/reports/appointments?group_by=day\|week&date_from=&date_to=&dentist_id=` | A | counts over time |
| GET | `/reports/dentists?date_from=&date_to=` | A | per-dentist totals |
| GET | `/reports/rates?date_from=&date_to=` | A | no-show and cancellation rates |

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
| 401 | not logged in |
| 403 | wrong role |
| 404 | not found |
| 409 | conflict (double booking) |
