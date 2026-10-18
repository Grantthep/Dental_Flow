import type {
  Appointment,
  AppointmentInput,
  AppointmentStatus,
  Dentist,
  DentistRow,
  Page,
  Patient,
  PatientInput,
  PeriodRow,
  Rates,
  Slot,
  User,
} from "./types";

const TOKEN_KEY = "df-token";

/** The login token lives in localStorage; logout = drop it (the backend has no logout call). */
export const token = {
  get: () => {
    try {
      return localStorage.getItem(TOKEN_KEY);
    } catch {
      return null;
    }
  },
  set: (t: string) => {
    try {
      localStorage.setItem(TOKEN_KEY, t);
    } catch {}
  },
  clear: () => {
    try {
      localStorage.removeItem(TOKEN_KEY);
    } catch {}
  },
};

/** An error from the API. `code` is set for booking errors (slot_taken, outside_hours, ...). */
export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public code?: string,
  ) {
    super(message);
  }
}

type Query = Record<string, string | number | boolean | null | undefined | (string | number)[]>;

function qs(query?: Query) {
  const p = new URLSearchParams();
  for (const [k, v] of Object.entries(query ?? {})) {
    if (v == null || v === "") continue;
    for (const x of Array.isArray(v) ? v : [v]) p.append(k, String(x));
  }
  const s = p.toString();
  return s ? `?${s}` : "";
}

function errorMessage(data: unknown, status: number): string {
  const detail = (data as { detail?: unknown } | null)?.detail;
  if (typeof detail === "string") return detail;
  // FastAPI 422: [{ loc: ["body", "phone"], msg: "..." }, ...]
  if (Array.isArray(detail)) return detail.map((e) => `${(e.loc ?? []).slice(1).join(".") || "input"}: ${e.msg}`).join("; ");
  return `Request failed (${status})`;
}

async function request<T>(method: string, path: string, opts: { query?: Query; body?: unknown } = {}): Promise<T> {
  const headers: Record<string, string> = {};
  if (opts.body !== undefined) headers["Content-Type"] = "application/json";
  const t = token.get();
  if (t) headers.Authorization = `Bearer ${t}`;
  const res = await fetch(`/api/v1${path}${qs(opts.query)}`, {
    method,
    headers,
    body: opts.body !== undefined ? JSON.stringify(opts.body) : undefined,
  });
  // Expired/invalid token or deactivated account: back to the login page (docs/roles.md, "Frontend notes").
  if (res.status === 401) {
    token.clear();
    if (location.pathname !== "/login") location.assign(`/login?next=${encodeURIComponent(location.pathname + location.search)}`);
  }
  if (res.status === 204) return undefined as T;
  const data = await res.json().catch(() => null);
  if (!res.ok) throw new ApiError(res.status, errorMessage(data, res.status), data?.code);
  return data as T;
}

export const api = {
  auth: {
    /** OAuth2 form post; username is the email. */
    login: async (email: string, password: string) => {
      const res = await fetch("/api/v1/auth/login", {
        method: "POST",
        body: new URLSearchParams({ username: email, password }),
      });
      const data = await res.json().catch(() => null);
      if (!res.ok) throw new ApiError(res.status, errorMessage(data, res.status));
      return data as { access_token: string; expires_in: number; user: User };
    },
    me: () => request<User>("GET", "/auth/me"),
  },
  patients: {
    list: (q: { q?: string; include_inactive?: boolean; page?: number; size?: number }) =>
      request<Page<Patient>>("GET", "/patients", { query: q }),
    get: (id: number) => request<Patient>("GET", `/patients/${id}`),
    create: (body: PatientInput) => request<Patient>("POST", "/patients", { body }),
    update: (id: number, body: Partial<PatientInput> & { is_active?: boolean }) => request<Patient>("PATCH", `/patients/${id}`, { body }),
  },
  dentists: {
    list: () => request<Dentist[]>("GET", "/dentists"),
    slots: (id: number, date: string, duration: number) => request<Slot[]>("GET", `/dentists/${id}/slots`, { query: { date, duration } }),
  },
  appointments: {
    list: (q: {
      date_from?: string;
      date_to?: string;
      dentist_id?: number;
      patient_id?: number;
      status?: AppointmentStatus[];
      page?: number;
      size?: number;
    }) => request<Page<Appointment>>("GET", "/appointments", { query: q }),
    get: (id: number) => request<Appointment>("GET", `/appointments/${id}`),
    create: (body: AppointmentInput) => request<Appointment>("POST", "/appointments", { body }),
    update: (id: number, body: { status?: AppointmentStatus; reason?: string | null; notes?: string | null }) =>
      request<Appointment>("PATCH", `/appointments/${id}`, { body }),
    reschedule: (id: number, body: { start_at: string; end_at: string }) =>
      request<Appointment>("POST", `/appointments/${id}/reschedule`, { body }),
    cancel: (id: number) => request<Appointment>("POST", `/appointments/${id}/cancel`),
  },
  reports: {
    appointments: (q: { date_from: string; date_to: string; group_by: string; dentist_id?: number }) =>
      request<PeriodRow[]>("GET", "/reports/appointments", { query: q }),
    dentists: (q: { date_from: string; date_to: string }) => request<DentistRow[]>("GET", "/reports/dentists", { query: q }),
    rates: (q: { date_from: string; date_to: string; dentist_id?: number }) => request<Rates>("GET", "/reports/rates", { query: q }),
  },
};

/** Friendlier wording for booking error codes from the backend. */
const BOOKING_MESSAGES: Record<string, string> = {
  slot_taken: "That time is already taken for this dentist. Pick another slot.",
  patient_busy: "This patient already has an appointment at that time.",
  outside_hours: "That time is outside the dentist's working hours.",
  time_off: "The dentist is off at that time.",
  in_past: "You can't book a time in the past.",
  bad_status: "This appointment can't be changed any more.",
  too_early: "You can't mark it completed or no-show before it starts.",
};

export function errorText(e: unknown): string {
  if (e instanceof ApiError) return (e.code && BOOKING_MESSAGES[e.code]) || e.message;
  if (e instanceof TypeError) return "Can't reach the server. Is the backend running?";
  return e instanceof Error ? e.message : String(e);
}
