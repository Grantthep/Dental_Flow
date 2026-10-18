# DentalFlow — Progress board

Everyone updates this at the end of a work session (or asks Claude to). Keep it short.
Full task list: the weekly plan (DentalFlow_Weekly_Plan.docx). ✅ done · 🟡 in progress / partly · ⬜ not started

## Where we are
Plan week ~8 of 16 (Integration & Testing). All three branches merged to `main`, CI green.
**Blocker:** the frontend has no login yet, so every API call on `main` gets 401 (see Handoffs).

| Area | Status |
|---|---|
| Backend & DB (Grant) | ✅ Phases 1–4 + Phase 6 analytics APIs, merged to `main` (PR #1) |
| Auth, DevOps & QA (Aung) | ✅ Weeks 1–8 backend-side work, merged (PR #2) |
| Frontend (Aye Nyein Moe) | 🟡 Phases 1–6 UI merged (PR #3); **login not wired up yet** |

## Checklist by member

### Grant — Backend & DB
- ✅ Requirements, ERD, API list (`docs/`)
- ✅ FastAPI + SQLAlchemy + Alembic, seed data, patient/dentist CRUD
- ✅ Appointments, availability, slots, double-booking prevention, reschedule/cancel, audit log
- ✅ Booking hardening, indexes, patient CSV/Excel import tool
- ✅ SQL analytics + report APIs (Phase 6)
- ✅ PR #2 merged; repo audit done (2026-10-18): fixed booking race → 500, seed.py dev-only guard, race test
- ⬜ Repo settings (owner only): branch protection on `main` (require PR, 1 approval, CI checks "Backend lint + tests" and "Docker stack smoke test")

### Aye Nyein Moe — Frontend
- ✅ Next.js project, calendar, booking form, patient search/detail, dentist dashboard, reports page (PR #3)
- ⬜ **Login page + send the token** (blocker, see Handoffs); replace the role switcher in `lib/role.tsx` with `/auth/me`
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

- 2026-10-18 Grant → Aye Nyein Moe (+ Aung): **blocker** — `frontend/src/lib/api.ts` sends no
  `Authorization` header and there's no login page, so on `main` every page gets 401. Needs: `/login` page
  (form post to `/api/v1/auth/login`), `Bearer` token on every request, redirect to `/login` on 401,
  role from `/auth/me` instead of the switcher. Details in roles.md "Frontend notes".
- 2026-10-18 Grant → Aung: from the audit, your area: (1) `ratelimit.py` never removes keys, so failed
  logins with random emails grow memory forever — `pop` empty keys in `_recent`; (2) password change/reset
  doesn't invalidate existing tokens (valid 8 h) — e.g. `password_changed_at` vs token `iat`.
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
- 2026-10-18 Grant: repo audit; backend fixes on `backend` (race → 409 not 500, seed.py dev-only, list date filters need a timezone). Handoffs added.
