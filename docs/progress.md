# DentalFlow — Progress board

Everyone updates this at the end of a work session (or asks Claude to). Keep it short.
Full task list: the weekly plan (DentalFlow_Weekly_Plan.docx). ✅ done · 🟡 in progress / partly · ⬜ not started

## Where we are
Plan week ~8 of 16 (Integration & Testing). Backend, frontend and auth are all on `main`; the app now has a real login.

| Area | Status |
|---|---|
| Backend & DB (Grant) | ✅ Phases 1–4 + Phase 6 analytics APIs, merged to `main` (PR #1) |
| Auth, DevOps & QA (Aung) | ✅ PR #2 merged. PR #7: frontend login, Docker, Playwright e2e, security tests, staging setup |
| Frontend (Aye Nyein Moe) | ✅ Calendar, booking, patients, dashboard, reports merged (PR #3) |

## Checklist by member

### Grant — Backend & DB
- ✅ Requirements, ERD, API list (`docs/`)
- ✅ FastAPI + SQLAlchemy + Alembic, seed data, patient/dentist CRUD
- ✅ Appointments, availability, slots, double-booking prevention, reschedule/cancel, audit log
- ✅ Booking hardening, indexes, patient CSV/Excel import tool
- ✅ SQL analytics + report APIs (Phase 6)
- ✅ Review PR #2
- ✅ PR #7 merged (dentists see own patients; DB bad values → 422)
- ✅ Branch protection on `main`: 1 approval + Backend / Docker smoke / Frontend checks, admins included
- ✅ Audit fixes: booking race → 409 not 500, `seed.py` dev-only, timezone-aware list filters (PR #4)
- ✅ V2 treatment history API, append-only (PR #4); frontend screens not started
- ✅ Import rehearsed on a DB copy; `backend/import_template.csv` for the clinic (PR #4)
- ✅ Phase 7 docs: production migration steps, [backlog.md](backlog.md), report draft `docs/report/backend.md` (PR #4)
- ⬜ Manual: confirm **[confirm]** items with the clinic; real-data import + production migration when staging/production exist

### Aye Nyein Moe — Frontend
- ✅ Push the Next.js project (PR #3)
- ✅ Login page + token + logout (done by Aung in PR #7, please review)
- ✅ Calendar, booking form, patient search, dentist dashboard, role-based page hiding
- ✅ `frontend/Dockerfile` (Aung, PR #7)

### Aung Sett Hpone — Auth, DevOps & QA
- ✅ README, `.gitignore`, PR template, CONTRIBUTING, roles & permissions doc
- ✅ Backend Dockerfile, docker-compose (PostgreSQL), `.env.example`, secrets out of Git
- ✅ pytest + coverage, GitHub Actions CI (lint, tests, Docker smoke test, frontend build)
- ✅ Login API, Argon2 hashing, JWT, protected routes, role-based permissions, `/users` admin API
- ✅ Auth/permission tests (52 backend tests, ~98% coverage)
- ✅ Login rate limiting, CORS
- ✅ Auth hardening (#6): password change/reset logs out old tokens; rate limiter memory can't grow (PR #7)
- ✅ Security tests: auth bypass, role checks, SQL injection, input fuzzing (found + fixed NUL-byte / int-overflow 500s)
- ✅ Frontend Dockerfile + compose service
- ✅ Playwright end-to-end tests: login, logout, role hiding, create booking — run in CI
- 🟡 Staging deployment: VPS + Caddy HTTPS + daily backups + CI deploy all ready ([deploy.md](deploy.md)); needs a server bought + secrets set

## Handoffs / questions
Add a line: `YYYY-MM-DD From → To: message`. Delete it once answered.

- 2026-10-18 Aung → Grant: please review PR #7. Edits in your area: `routers/patients.py` (dentists see only
  their own patients, decided by the team) and `main.py` (DB "bad value" errors → 422 instead of 500).
  Branch protection: the deploy workflow needs nothing extra; the required check names didn't change.
- 2026-10-18 Aung → Grant: PR #4 vs PR #7 overlap. (1) Both add a migration on top of `21eff677ad3c`;
  whichever merges second must set its `down_revision` to the other's (`bc23ba68177d` / `7c1d2e3f4a5b`),
  else `alembic upgrade head` fails with two heads. (2) `patients.py` conflicts: keep the user-scoped
  `_get_or_404(db, id, user)` and pass `user` in `patient_treatments`, so dentists can't read the history of
  patients that aren't theirs. Details in my comment on PR #4.
- 2026-10-18 Aung → Aye Nyein Moe: I wired real login into the frontend (PR #7, please review): new `/login`
  page, token + `Authorization` header + 401 redirect in `lib/api.ts`, `lib/role.tsx` now reads the user from
  `/auth/me`, and the "Viewing as" switcher became name + Log out. Dentists now only see their own patients.
  Run everything with `docker compose up --build` → http://localhost:3000.
- 2026-10-22 Grant → Aye Nyein Moe: after PR #4 merges, treatment history API is ready for the patient and appointment pages
  (`GET/POST /appointments/{id}/treatments`, `GET /patients/{id}/treatments`), see docs/api.md.
- 2026-10-18 Aung → team: **staging host decided: one small Linux VPS (~$5/month) running our docker compose
  stack + Caddy (HTTPS) + daily DB backups, auto-deployed from `main` by CI.** See [deploy.md](deploy.md).
  Need from the team: who pays for/creates the server and a (sub)domain, then I'll do the setup + GitHub secrets.

## Log
- 2026-10-17 Grant: backend Phases 1–4 and 6 merged to `main` (PR #1).
- 2026-10-18 Aung: auth, roles, Docker, CI, docs pushed to `devops`; PR #2 opened; CI green.
- 2026-10-18 Aung: full Docker stack verified on Windows (Docker Desktop): migrate, seed, login, 52 tests pass in the container.
  Tip: if you already have PostgreSQL installed locally, set `DB_PORT=5433` in `.env` (port 5432 is taken).
- 2026-10-18 Aung: dentists see only their own patients; SQL injection + fuzzing tests (fixed two 500s);
  frontend login/logout; frontend Dockerfile (full stack in compose); Playwright e2e in CI;
  staging setup (VPS + Caddy + backups + deploy workflow) tested locally incl. backup restore. PR #7.
- 2026-10-18 Aung: fixed #6 (tokens survive password change; limiter memory growth). Commented on #4/#5, opened staging notice.
- 2026-10-22 Grant: PR #4 caught up with main — treatments migration now after `7c1d2e3f4a5b` (one head), patient treatment history uses the dentist-scoped `_get_or_404`. Branch protection on.
