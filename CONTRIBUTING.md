# Contributing to DentalFlow

## Branches
| Branch | Who | What |
|---|---|---|
| `main` | everyone, via PR only | always deployable |
| `backend` | Grant | API, database, analytics |
| `frontend` | Aye Nyein Moe | Next.js app |
| `devops` | Aung Sett Hpone | auth, Docker, CI, tests, deployment |

For bigger pieces of work, branch off your own branch (e.g. `devops-staging-deploy`) and merge back.
Before opening a PR, bring in the latest `main`: `git pull origin main`.

## Pull requests
1. Open a PR into `main`. Fill in the PR template.
2. CI must be green (lint + tests + Docker smoke test).
3. At least **one other member** reviews and approves. Grant (tech lead) reviews anything touching
   the database schema or booking rules; Aung reviews anything touching auth or permissions.
4. Squash or merge — don't force-push to `main`.
5. Update [docs/progress.md](docs/progress.md): tick your tasks, add a log line, leave handoff notes.

## Commits
- Prefix with the area: `backend:`, `frontend:`, `auth:`, `devops:`, `docs:`, `test:`.
- One logical change per commit; say *why* in the body when it's not obvious.

## Code rules
- New endpoint → add the role check (`require_roles`) and a row in [docs/roles.md](docs/roles.md) + a test.
- Changed a model → `alembic revision --autogenerate -m "..."` and commit the migration.
- Backend tests: `pytest` must pass; lint: `ruff check .` (in `backend/`).
- Never commit secrets (`.env`), real patient data, or database dumps.

## Bugs
Use GitHub Issues with labels `bug` + `critical` / `high` / `low`, and the area (`backend`, `frontend`, `devops`).
