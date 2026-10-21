# DentalFlow — Progress board

Everyone updates this at the end of a work session (or asks Claude to). Keep it short.
Full task list: the weekly plan (DentalFlow_Weekly_Plan.docx). ✅ done · 🟡 in progress / partly · ⬜ not started

## Where we are
Plan week ~8 of 16 (Integration & Testing). Backend, frontend and auth are all on `main`; the app now has a real login.

| Area | Status |
|---|---|
| Backend & DB (Grant) | ✅ Phases 1–4 + Phase 6 analytics APIs, merged to `main` (PR #1) |
| Auth, DevOps & QA (Aung) | ✅ PR #2 + PR #7 merged (frontend login, Docker, Playwright e2e, security tests, staging setup). Staging waits on a server |
| Frontend (Aye Nyein Moe) | ✅ Calendar, booking, patients, dashboard, reports merged (PR #3). PR #10 (dentist screens) approved by Aung |

## Checklist by member

### Grant — Backend & DB
- ✅ Requirements, ERD, API list (`docs/`)
- ✅ FastAPI + SQLAlchemy + Alembic, seed data, patient/dentist CRUD
- ✅ Appointments, availability, slots, double-booking prevention, reschedule/cancel, audit log
- ✅ Booking hardening, indexes, patient CSV/Excel import tool
- ✅ SQL analytics + report APIs (Phase 6)
- ✅ Review PR #2
- ✅ PR #7 merged
- ⬜ Update PR #4 for the new `main`: migration `down_revision` → `7c1d2e3f4a5b`, resolve `patients.py` + `progress.md` conflicts
- ⬜ Repo settings (owner only): branch protection on `main` (require PR, 1 approval, CI checks "Backend lint + tests" and "Docker stack smoke test")

### Aye Nyein Moe — Frontend
- ✅ Push the Next.js project (PR #3)
- ✅ Login page + token + logout (done by Aung in PR #7, merged)
- ✅ Calendar, booking form, patient search, dentist dashboard, role-based page hiding
- 🟡 PR #10: dentist screens follow roles.md + calendar overlap fix (approved by Aung, CI green, ready to merge)
- ✅ `frontend/Dockerfile` (Aung, PR #7)

### Aung Sett Hpone — Auth, DevOps & QA
- ✅ README, `.gitignore`, PR template, CONTRIBUTING, roles & permissions doc
- ✅ Backend Dockerfile, docker-compose (PostgreSQL), `.env.example`, secrets out of Git
- ✅ pytest + coverage, GitHub Actions CI (lint, tests, Docker smoke test, frontend build)
- ✅ Login API, Argon2 hashing, JWT, protected routes, role-based permissions, `/users` admin API
- ✅ Auth/permission tests (52 backend tests, ~98% coverage)
- ✅ Login rate limiting, CORS
- ✅ Auth hardening (#6): password change/reset logs out old tokens; rate limiter memory can't grow (PR #7)
- ✅ Review PR #10 (frontend dentist screens vs roles.md)
- ✅ Security tests: auth bypass, role checks, SQL injection, input fuzzing (found + fixed NUL-byte / int-overflow 500s)
- ✅ Frontend Dockerfile + compose service
- ✅ Playwright end-to-end tests: login, logout, role hiding, create booking — run in CI
- 🟡 Staging deployment: VPS + Caddy HTTPS + daily backups + CI deploy all ready ([deploy.md](deploy.md)); needs a server bought + secrets set

## Handoffs / questions
Add a line: `YYYY-MM-DD From → To: message`. Delete it once answered.

- 2026-10-22 Aung → Grant: PR #7 is merged, so PR #4 now has to catch up. (1) In `bc23ba68177d_treatments.py` set
  `down_revision = '7c1d2e3f4a5b'` (still `21eff677ad3c`), else `alembic upgrade head` fails with two heads. (2) `patients.py` conflicts: keep the user-scoped
  `_get_or_404(db, id, user)` and pass `user` in `patient_treatments`, so dentists can't read the history of
  patients that aren't theirs. Then `pytest` + `ruff check .` and it's ready.
- 2026-10-18 Aung → team: **staging host decided: one small Linux VPS (~$5/month) running our docker compose
  stack + Caddy (HTTPS) + daily DB backups, auto-deployed from `main` by CI.** See [deploy.md](deploy.md).
  Need from the team: who pays for/creates the server and a (sub)domain, then I'll do the setup + GitHub secrets. (Still open, issue #8.)

## Log
- 2026-10-17 Grant: backend Phases 1–4 and 6 merged to `main` (PR #1).
- 2026-10-18 Aung: auth, roles, Docker, CI, docs pushed to `devops`; PR #2 opened; CI green.
- 2026-10-18 Aung: full Docker stack verified on Windows (Docker Desktop): migrate, seed, login, 52 tests pass in the container.
  Tip: if you already have PostgreSQL installed locally, set `DB_PORT=5433` in `.env` (port 5432 is taken).
- 2026-10-18 Aung: dentists see only their own patients; SQL injection + fuzzing tests (fixed two 500s);
  frontend login/logout; frontend Dockerfile (full stack in compose); Playwright e2e in CI;
  staging setup (VPS + Caddy + backups + deploy workflow) tested locally incl. backup restore. PR #7.
- 2026-10-18 Aung: fixed #6 (tokens survive password change; limiter memory growth). Commented on #4/#5, opened staging notice.
- 2026-10-22 Aung: PR #7 merged. Reviewed + approved PR #10 (matches roles.md, CI green). Checked PR #4: still conflicts with `main`, migration parent needs updating.
