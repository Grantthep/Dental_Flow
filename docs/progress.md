# DentalFlow — Progress board

Everyone updates this at the end of a work session (or asks Claude to). Keep it short.
Full task list: the weekly plan (DentalFlow_Weekly_Plan.docx). ✅ done · 🟡 in progress / partly · ⬜ not started

## Where we are
Plan week ~8 of 16 (Integration & Testing). Backend is ahead, frontend hasn't been pushed yet.

| Area | Status |
|---|---|
| Backend & DB (Grant) | ✅ Phases 1–4 + Phase 6 analytics APIs, merged to `main` (PR #1) |
| Auth, DevOps & QA (Aung) | ✅ Weeks 1–8 backend-side work on `devops`, CI green — **PR #2 waiting for review** |
| Frontend (Aye Nyein Moe) | ⬜ No `frontend` branch on GitHub yet |

## Checklist by member

### Grant — Backend & DB
- ✅ Requirements, ERD, API list (`docs/`)
- ✅ FastAPI + SQLAlchemy + Alembic, seed data, patient/dentist CRUD
- ✅ Appointments, availability, slots, double-booking prevention, reschedule/cancel, audit log
- ✅ Booking hardening, indexes, patient CSV/Excel import tool
- ✅ SQL analytics + report APIs (Phase 6)
- ⬜ Review PR #2 (auth touches your routers + `deps.py`)
- ⬜ Repo settings (owner only): branch protection on `main` (require PR, 1 approval, CI checks "Backend lint + tests" and "Docker stack smoke test")

### Aye Nyein Moe — Frontend
- ⬜ Push the Next.js project to a `frontend` branch (CI builds it automatically once `frontend/package.json` exists)
- ⬜ Login page: see "Frontend notes" in [roles.md](roles.md)
- ⬜ Calendar, booking form, patient search, dentist dashboard, role-based page hiding
- ⬜ Add `frontend/Dockerfile` (or ask Aung) so it joins `docker-compose.yml`

### Aung Sett Hpone — Auth, DevOps & QA
- ✅ README, `.gitignore`, PR template, CONTRIBUTING, roles & permissions doc
- ✅ Backend Dockerfile, docker-compose (PostgreSQL), `.env.example`, secrets out of Git
- ✅ pytest + coverage, GitHub Actions CI (lint, tests, Docker smoke test, frontend build)
- ✅ Login API, Argon2 hashing, JWT, protected routes, role-based permissions, `/users` admin API
- ✅ Auth/permission tests (52 backend tests, ~98% coverage)
- ✅ Login rate limiting, CORS
- 🟡 Security tests (auth bypass, role checks done; SQL injection / input fuzzing still to do)
- ⬜ Frontend Dockerfile + compose service (after frontend lands)
- ⬜ Playwright end-to-end tests: login, create booking (needs frontend)
- ⬜ Staging deployment: cloud host, HTTPS, backups, deploy step in CI (week 10) — team to pick a host

## Handoffs / questions
Add a line: `YYYY-MM-DD From → To: message`. Delete it once answered.

- 2026-10-18 Aung → Grant: please review PR #2. I added role checks to your routers and changed
  `deps.current_user_id` to return the logged-in user (audit logs now have real `user_id`).
  Time off is admin-only as in your api.md. Also please turn on branch protection for `main`.
- 2026-10-18 Aung → Aye Nyein Moe: login + token rules for the UI are in [roles.md](roles.md)
  ("Frontend notes"). Dev logins after `seed.py`: `admin@example.com`, `reception@example.com`,
  `dentist1@example.com`, password `dentalflow-dev`. CORS allows `http://localhost:3000`.
- 2026-10-18 Aung → team: open question: should dentists see **all** patients or only patients they
  have appointments with? Currently all (read-only).
- 2026-10-18 Aung → team: we need to pick a cloud host for staging (week 10).

## Log
- 2026-10-17 Grant: backend Phases 1–4 and 6 merged to `main` (PR #1).
- 2026-10-18 Aung: auth, roles, Docker, CI, docs pushed to `devops`; PR #2 opened; CI green.
- 2026-10-18 Aung: full Docker stack verified on Windows (Docker Desktop): migrate, seed, login, 52 tests pass in the container.
  Tip: if you already have PostgreSQL installed locally, set `DB_PORT=5433` in `.env` (port 5432 is taken).
