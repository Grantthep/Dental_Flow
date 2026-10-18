# DentalFlow backend

FastAPI + SQLAlchemy 2 + PostgreSQL + Alembic.

Prefer Docker? See the [root README](../README.md). Auth and roles: [docs/roles.md](../docs/roles.md).

## Run locally
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

# point at your PostgreSQL (default: postgres:postgres@localhost:5432/dentalflow)
set DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/dentalflow

set CLINIC_TZ=Asia/Yangon           # clinic timezone for working hours (default Asia/Yangon)
alembic upgrade head              # create tables
python seed.py                    # fake dentists + 50 patients + dev logins
fastapi dev app/main.py           # http://localhost:8000/docs
```

## Logging in
Every endpoint except `POST /api/v1/auth/login` and `/health` needs a token.
- In `/docs`: click **Authorize**, enter an email as *username* and the password.
- Dev logins from `seed.py` (password `dentalflow-dev`, or `SEED_PASSWORD`):
  `admin@example.com`, `reception@example.com`, `dentist1@example.com` .. `dentist3@example.com`.
- Real clinic: don't seed. Create the first admin, then add staff from `/users`:
  ```bash
  python create_admin.py admin@clinic.com "Full Name"   # asks for the password
  ```
- Settings: `SECRET_KEY` (required outside `APP_ENV=development`), `ACCESS_TOKEN_MINUTES`, `CORS_ORIGINS`,
  `LOGIN_MAX_FAILURES`, `LOGIN_WINDOW_SECONDS` — see [`.env.example`](../.env.example).

## Tests
Needs an empty database `dentalflow_test` (tables are recreated for each test).
```bash
set TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/dentalflow_test
pytest                            # add --cov=app for a coverage report
ruff check .                      # lint (same as CI)
```
Test clients: `client` is logged in as admin; `client_for(Role.dentist, dentist=True)` and `anon` for permission tests.

## Layout
| Path | What |
|---|---|
| `app/db.py` | engine, session, `Base` |
| `app/models.py` | tables (see `docs/erd.md`) |
| `app/schemas.py` | request/response models + validation |
| `app/routers/` | API endpoints (`/api/v1/...`) |
| `alembic/versions/` | migrations — after changing models run `alembic revision --autogenerate -m "..."` |
| `seed.py` | synthetic data + dev logins |
| `app/security.py`, `app/deps.py` | password hashing, JWT, `require_roles` |
| `create_admin.py` | first real admin account |

Double booking is blocked by PostgreSQL exclusion constraints on `appointments`
(same dentist or same patient, overlapping time, status not cancelled/no-show).

## Importing the clinic's existing patients
CSV or Excel (.xlsx). Dry run first — it only reports, writes nothing:
```bash
python import_patients.py clinic_patients.xlsx --errors bad_rows.csv
python import_patients.py clinic_patients.xlsx --commit
```
Headers are matched loosely (`Name`, `Mobile`, `DOB`, `Sex`, `Allergies`, ...); see the top of `import_patients.py`.
Dates that aren't `YYYY-MM-DD` are read as `DD/MM/YYYY` (change with `--date-format`).
Duplicates (same name + phone) and invalid rows are skipped and listed.
**Only import real records after the clinic approves and backups are in place.**

## Note: local PostgreSQL via pgserver (Windows)
If you use the pip `pgserver` package instead of Docker, it ships without timezone files and
reports fail with `time zone "Asia/Yangon" not recognized`. Fix once:
```bash
python -c "import tzdata,os,shutil,pgserver; shutil.copytree(os.path.join(os.path.dirname(tzdata.__file__),'zoneinfo'), os.path.join(os.path.dirname(pgserver.__file__),'pginstall','share','postgresql','timezone'), dirs_exist_ok=True)"
```
