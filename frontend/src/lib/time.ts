// All times are shown in the clinic's timezone, whatever timezone the browser is in.
// "Day" strings are clinic-local dates in YYYY-MM-DD form.

export const CLINIC_TZ = process.env.NEXT_PUBLIC_CLINIC_TZ ?? "Asia/Yangon";

const partsFmt = new Intl.DateTimeFormat("en-US", {
  timeZone: CLINIC_TZ,
  hourCycle: "h23",
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
  second: "2-digit",
});

/** How far the clinic's wall clock is ahead of UTC at instant `t` (ms). */
function offsetMs(t: number): number {
  const p = Object.fromEntries(partsFmt.formatToParts(new Date(t)).map((x) => [x.type, Number(x.value)]));
  return Date.UTC(p.year, p.month - 1, p.day, p.hour, p.minute, p.second) - Math.floor(t / 1000) * 1000;
}

/** Clinic-local day + "HH:MM" → the real instant. */
export function clinicTime(day: string, hm = "00:00"): Date {
  const [y, m, d] = day.split("-").map(Number);
  const [h, mi] = hm.split(":").map(Number);
  const wall = Date.UTC(y, m - 1, d, h, mi);
  return new Date(wall - offsetMs(wall - offsetMs(wall)));
}

const dayFmt = new Intl.DateTimeFormat("en-CA", { timeZone: CLINIC_TZ, year: "numeric", month: "2-digit", day: "2-digit" });
const timeFmt = new Intl.DateTimeFormat("en-GB", { timeZone: CLINIC_TZ, hour: "2-digit", minute: "2-digit" });
const longDayFmt = new Intl.DateTimeFormat("en-GB", { timeZone: "UTC", weekday: "short", day: "numeric", month: "short", year: "numeric" });
const shortDayFmt = new Intl.DateTimeFormat("en-GB", { timeZone: "UTC", weekday: "short", day: "numeric", month: "short" });

/** Clinic-local day of an instant. */
export const clinicDay = (d: Date | string) => dayFmt.format(new Date(d));
export const today = () => clinicDay(new Date());

/** "14:30" in clinic time. */
export const fmtTime = (d: Date | string) => timeFmt.format(new Date(d));
/** "Mon 20 Oct 2026" for a day string. */
export const fmtDay = (day: string) => longDayFmt.format(new Date(`${day}T00:00:00Z`));
/** "Mon 20 Oct" for a day string. */
export const fmtDayShort = (day: string) => shortDayFmt.format(new Date(`${day}T00:00:00Z`));
/** "Mon 20 Oct 2026, 14:30" for an instant. */
export const fmtDateTime = (d: Date | string) => `${fmtDay(clinicDay(d))}, ${fmtTime(d)}`;

/** Minutes since clinic-local midnight. */
export function minuteOfDay(d: Date | string): number {
  const [h, m] = fmtTime(d).split(":").map(Number);
  return h * 60 + m;
}

export function addDays(day: string, n: number): string {
  const d = new Date(`${day}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + n);
  return d.toISOString().slice(0, 10);
}

/** Monday of the week containing `day`. */
export function weekStart(day: string): string {
  const dow = (new Date(`${day}T00:00:00Z`).getUTCDay() + 6) % 7;
  return addDays(day, -dow);
}

export const minutesBetween = (a: string, b: string) => Math.round((new Date(b).getTime() - new Date(a).getTime()) / 60000);
