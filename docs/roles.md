# DentalFlow — Roles and permissions

Owned by Member 3 (Auth, DevOps & QA). Enforced in `backend/app/deps.py` (`require_roles`) and
checked by `backend/tests/test_permissions.py` — change both together.

| Area | Admin | Receptionist | Dentist |
|---|---|---|---|
| Log in, view own account, change own password | ✅ | ✅ | ✅ |
| Staff accounts (`/users`): create, change role, deactivate, reset password | ✅ | ❌ | ❌ |
| Patients: search, view | ✅ | ✅ | ✅ |
| Patients: create, edit, deactivate | ✅ | ✅ | ❌ |
| Dentists: view | ✅ | ✅ | ✅ |
| Dentists: create, edit | ✅ | ❌ | ❌ |
| Working hours, time off: view, free slots | ✅ | ✅ | ✅ |
| Working hours, time off: change | ✅ | ❌ | ❌ |
| Appointments: view | ✅ all | ✅ all | own only |
| Appointments: book, reschedule, cancel | ✅ | ✅ | ❌ |
| Appointments: edit reason / notes / status | ✅ | ✅ | own only: notes, and status → `completed` / `no_show` |
| Treatment history: view | ✅ | ✅ | ✅ (own appointments; all for a patient's history) |
| Treatment history: add (append-only) | ✅ | ❌ | own appointments |
| Audit log | ✅ | ❌ | ❌ |
| Reports / analytics | ✅ | ❌ | ❌ |

## Rules
- Every `/api/v1` endpoint except `POST /auth/login` needs `Authorization: Bearer <token>`. `/health` is public.
- `401` = not logged in / token expired / account deactivated. `403` = logged in but wrong role.
- A dentist account sees only appointments of the dentist profile linked to it (`dentists.user_id`).
  Another dentist's appointment returns `404`, not `403`, so IDs can't be probed.
  An unlinked dentist account gets `403 "Your account is not linked to a dentist profile"`.
- Deactivating a user takes effect immediately, even if their token hasn't expired.
- The last active admin can't be demoted or deactivated.

## Tokens and passwords
- Passwords: Argon2 (`pwdlib`), minimum 8 characters. Never stored or logged in plain text.
- Tokens: JWT (HS256), signed with `SECRET_KEY`, valid `ACCESS_TOKEN_MINUTES` (default 480 = one shift).
  No refresh token in V1 — when it expires the frontend sends the user back to the login page.
- Logout is client-side: the frontend deletes the token.
- Login is limited to 5 failed attempts per IP + email per 15 minutes (`429` with `Retry-After`).
- The backend refuses to start outside `APP_ENV=development` without a `SECRET_KEY` of 32+ characters.

## Frontend notes
- Log in with a form POST (`application/x-www-form-urlencoded`): `username=<email>&password=<password>`.
  The response has `access_token`, `expires_in` (seconds) and `user` (`id, email, full_name, role, ...`).
- Use `user.role` only to hide/show pages; the backend is what actually enforces access.
- On any `401`, clear the token and go to the login page.
