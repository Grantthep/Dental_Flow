# DentalFlow frontend

Next.js (App Router) + TypeScript + Tailwind CSS. Pages, wireframes and style: [`docs/frontend.md`](../docs/frontend.md).

## Run locally
Start the backend first (see [`backend/README.md`](../backend/README.md)) so the API runs on http://localhost:8000.

```bash
cd frontend
npm install
copy .env.example .env.local      # macOS/Linux: cp .env.example .env.local
npm run dev                       # http://localhost:3000
```

The browser calls `/api/...` on the frontend, and Next forwards it to `API_URL` (see `next.config.ts`),
so the backend needs no CORS settings in development.

| Variable | Default | What |
|---|---|---|
| `API_URL` | `http://localhost:8000` | where FastAPI runs |
| `NEXT_PUBLIC_CLINIC_TZ` | `Asia/Yangon` | clinic timezone; must match the backend's `CLINIC_TZ` |

## Checks
```bash
npm run typecheck
npm run build
```

## Layout
| Path | What |
|---|---|
| `src/app/` | pages (one folder per route) |
| `src/components/ui/` | base components: `Button`, `Input`/`Select`/`Textarea`, `Modal`, `Table`, loading/empty/error states |
| `src/components/` | shared pieces: `Shell` (sidebar + top bar), `PatientForm`, `PatientPicker`, `SlotPicker`, `DentistSelect`, `StatusBadge` |
| `src/lib/api.ts` | API client: every backend call, error handling, friendly booking-error messages |
| `src/lib/types.ts` | TypeScript types matching `backend/app/schemas.py` |
| `src/lib/time.ts` | clinic-timezone date/time helpers |
| `src/lib/role.tsx` | current role + what each role may do |

## Login and roles
`/login` posts the email + password to `/api/v1/auth/login` and keeps the token in localStorage (`df-token`).
`src/lib/api.ts` sends it as `Authorization: Bearer ...` on every call; any `401` clears it and goes back to `/login`.
`src/lib/role.tsx` loads the user from `/auth/me`; pages use `useRole()` / `can.*` only to hide things —
the backend enforces the real rules ([docs/roles.md](../docs/roles.md)).
Dev logins after `seed.py`: `admin@example.com`, `reception@example.com`, `dentist1@example.com`, password `dentalflow-dev`.
