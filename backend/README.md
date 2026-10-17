# DentalFlow backend

FastAPI + SQLAlchemy 2 + PostgreSQL + Alembic.

## Run locally
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

# point at your PostgreSQL (default: postgres:postgres@localhost:5432/dentalflow)
set DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/dentalflow

alembic upgrade head              # create tables
python seed.py                    # fake dentists + 50 patients
fastapi dev app/main.py           # http://localhost:8000/docs
```

## Tests
Needs an empty database `dentalflow_test` (tables are recreated for each test).
```bash
set TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/dentalflow_test
pytest
```

## Layout
| Path | What |
|---|---|
| `app/db.py` | engine, session, `Base` |
| `app/models.py` | tables (see `docs/erd.md`) |
| `app/schemas.py` | request/response models + validation |
| `app/routers/` | API endpoints (`/api/v1/...`) |
| `alembic/versions/` | migrations — after changing models run `alembic revision --autogenerate -m "..."` |
| `seed.py` | synthetic data |

Double booking is blocked by PostgreSQL exclusion constraints on `appointments`
(same dentist or same patient, overlapping time, status not cancelled/no-show).
