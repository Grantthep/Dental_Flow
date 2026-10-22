# DentalFlow — Backend & Database (Member 1: Pyae Phyo Han)

*Draft for the final report and portfolio. Facts and numbers are from the repo; edit the wording to your own voice.*

## My role
Backend and database for a dental clinic management system: data model, booking engine,
REST API, data import and analytics. Stack: Python 3.12, FastAPI, SQLAlchemy 2, PostgreSQL 17, Alembic, Pydantic v2, pytest.

## What I built
| Area | Result |
|---|---|
| Requirements & design | Requirements doc, ERD (7 tables), API endpoint list ([requirements.md](../requirements.md), [erd.md](../erd.md), [api.md](../api.md)) |
| Data layer | SQLAlchemy models, Alembic migrations (tested upgrade → downgrade → upgrade), synthetic seed data |
| Patients & dentists | CRUD with validation, search by name/phone, pagination, soft delete (`is_active`) |
| Scheduling | Weekly working hours (breaks = gaps between blocks), time off, free-slot finder in 15-minute steps |
| Booking engine | Create / reschedule / cancel; rules: not in the past, inside working hours, not during time off, no overlap for the dentist **or** the patient; status workflow booked → confirmed → completed (cancelled / no-show final) |
| Audit log | Every appointment change stores who, when, and before/after values in the same transaction |
| Data import | CSV / Excel import of the clinic's existing patients: loose header matching, date parsing, duplicate detection, dry run by default, error report |
| Analytics | SQL reports: appointments per day / week / month (zero-filled), per-dentist totals and chair time, cancellation and no-show rates |

## Key technical decisions
- **Double booking is impossible at the database level.** A PostgreSQL exclusion constraint
  (`EXCLUDE USING gist (... WITH =, tstzrange(start_at, end_at) WITH &&) WHERE status is active`) rejects
  overlapping appointments even when two receptionists book the same slot at the same moment. The API checks
  first so users get a clear message (`409 slot_taken`); the constraint is the final guard.
  Using `int4range(id, id, '[]')` instead of a plain `=` on the id means it needs no `btree_gist` extension.
- **Time zones.** Everything is stored in UTC (`timestamptz`); working hours, slots and report days use the
  clinic's time zone (`CLINIC_TZ`). A test checks that an appointment at 00:15 clinic time lands on the right
  day although it is the previous day in UTC.
- **Machine-readable errors.** Booking errors return `{"detail", "code"}` so the frontend can show friendly text
  per code (`slot_taken`, `patient_busy`, `outside_hours`, `time_off`, `in_past`, `bad_status`, `too_early`).
- **Measure before optimising.** With 20,000 patients and 20,000 appointments, patient search, the calendar and
  the overlap check each ran in under 5 ms; a year of reports returned in 10–30 ms including HTTP. Only one
  extra index (`appointments.start_at`) was needed; trigram search and summary views were not.

## Quality
- Automated tests for every rule above (CRUD, validation, each booking rule, the race between two bookings,
  status transitions, slots, audit, import, reports); the team's suite has 53 tests at 98 % coverage, run in CI on every pull request.
- Found and fixed through a code audit: a race that returned a server error instead of `409`, and a seed
  script that could create a known-password admin outside development.

## Challenges and what I learned
- *(Write 2–3 of your own, e.g. modelling breaks and time off; keeping rules identical between the API check and the DB constraint;
  time zones; working with teammates' auth changes to my routers through pull requests.)*

## Team collaboration
- Worked on the `backend` branch, merged through pull requests; shared progress in `docs/progress.md`.
- Provided `docs/api.md` and live `/docs` so the frontend could build against the API early.
- Auth (Member 3) plugged into my routers through one dependency (`deps.current_user_id`), so audit logs record the real user.

## Next steps (from [backlog.md](../backlog.md))
Appointment reminders, treatment history, billing; later no-show prediction and demand forecasting once real data exists.

## Portfolio blurb (short version)
> Designed and built the backend for DentalFlow, a dental clinic management system (FastAPI, PostgreSQL).
> Booking engine with database-enforced double-booking prevention, clinic-timezone scheduling and free-slot search,
> audit logging, a CSV/Excel import tool, and SQL analytics for no-show and cancellation rates. 53 automated tests, 98 % coverage, CI on every PR.
