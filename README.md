# DentalFlow

Dental clinic management system: patients, dentists, working hours, appointment booking with
double-booking prevention, audit log, clinic analytics, and staff logins with role-based access.

| Part | Stack | Folder | Owner |
|---|---|---|---|
| Backend & DB | Python, FastAPI, SQLAlchemy, PostgreSQL, Alembic | [`backend/`](backend/) | Pyae Phyo Han (Grant) |
| Frontend | Next.js, TypeScript, Tailwind CSS | `frontend/` (on the `frontend` branch) | Aye Nyein Moe |
| Auth, DevOps & QA | JWT auth, Docker, GitHub Actions, Pytest, Playwright | `backend/app/security.py`, `deps.py`, `docker-compose.yml`, `.github/` | Aung Sett Hpone |

## Quick start (Docker)
```bash
cp .env.example .env              # then edit SECRET_KEY etc.
docker compose up --build         # PostgreSQL + backend; migrations run automatically
docker compose exec backend python seed.py   # synthetic data + dev logins
```
- API docs: http://localhost:8000/docs (click **Authorize** and log in with a dev account)
- Dev logins (password `dentalflow-dev`): `admin@example.com`, `reception@example.com`, `dentist1@example.com`
- Run the tests:
  ```bash
  docker compose exec -e TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/dentalflow_test backend pytest
  ```

Without Docker, see [backend/README.md](backend/README.md).

## Docs
- [Requirements](docs/requirements.md) · [ERD](docs/erd.md) · [API endpoints](docs/api.md) · [Roles & permissions](docs/roles.md)
- [Contributing: branches, PRs, reviews](CONTRIBUTING.md)

## Patient data
Only **synthetic (fake) data** until the clinic approves real data **and** backups are in place.
Never commit `.env`, database dumps, or CSV/Excel exports of patients (they are git-ignored).
