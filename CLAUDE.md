# DentalFlow — notes for Claude (and humans)

Shared by the 3-person team; everyone uses Claude Code in VS Code. Read this first, then
[docs/progress.md](docs/progress.md) for what's done, what's next, and messages between members.

## Project
Dental clinic management system: patients, dentists, working hours, appointment booking with
double-booking prevention, audit log, analytics, staff login with roles. 16-week plan, V1 MVP.

| Member | Role | Branch | Owns |
|---|---|---|---|
| Pyae Phyo Han (Grant) — GitHub `Grantthep` | Backend & DB, tech lead | `backend` | `backend/app/models.py`, `booking.py`, routers, migrations, analytics |
| Aye Nyein Moe | Frontend | `frontend` | `frontend/` (Next.js + TypeScript + Tailwind) |
| Aung Sett Hpone | Auth, DevOps & QA | `devops` | `backend/app/security.py`, `deps.py`, `ratelimit.py`, `routers/auth.py`, `routers/users.py`, Docker, `.github/`, tests, deployment |

Ask the user which member they are if it matters for the task, and work on **that member's branch**.

## Working rules
- Never commit to `main` directly. Work on your branch → PR into `main` → 1 approval + green CI.
- Before starting: `git pull origin main` into your branch so you have everyone's latest work.
- Commit prefixes: `backend:`, `frontend:`, `auth:`, `devops:`, `docs:`, `test:`.
- **At the end of a work session, update [docs/progress.md](docs/progress.md)**: tick what you finished,
  add a dated line to the log, and leave notes for others under "Handoffs / questions".
- Editing another member's area is fine when needed, but say so in the PR and tag them for review.
- Only synthetic patient data. Never commit `.env`, dumps, or CSV/Excel patient exports.

## Code facts
- API base `/api/v1`; spec in [docs/api.md](docs/api.md); roles in [docs/roles.md](docs/roles.md).
- Every endpoint except `POST /api/v1/auth/login` and `/health` needs `Authorization: Bearer <token>`.
  New endpoint → add `require_roles(...)` (see `app/deps.py`), a row in docs/roles.md, and a test.
- Login is an OAuth2 **form** post: `username=<email>&password=...` → `{access_token, expires_in, user}`.
- Double booking is blocked by PostgreSQL exclusion constraints; booking errors return
  `{"detail": ..., "code": "slot_taken" | "patient_busy" | ...}`.
- Times are stored UTC (`timestamptz`); clinic timezone `CLINIC_TZ` (default Asia/Yangon).
- Model change → `alembic revision --autogenerate -m "..."` and commit the migration.

## Run / test
```bash
cp .env.example .env
docker compose up --build                       # db + backend, http://localhost:8000/docs
docker compose exec backend python seed.py      # fake data; logins admin@example.com / dentalflow-dev
docker compose exec -e TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/dentalflow_test backend pytest
```
Without Docker: see backend/README.md. In `backend/`: `pytest` and `ruff check .` must pass (CI runs both,
coverage must stay ≥ 90%). Test fixtures: `client` = admin, `client_for(Role.x)`, `anon`.
