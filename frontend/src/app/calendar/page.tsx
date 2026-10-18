"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState, type MouseEvent } from "react";
import { DentistSelect, ownDentistId, useDentists } from "@/components/DentistSelect";
import { patientName } from "@/components/PatientPicker";
import { STATUS_LABEL, STATUS_STYLE } from "@/components/StatusBadge";
import { Button } from "@/components/ui/Button";
import { ErrorBox, Loading, PageHeader } from "@/components/ui/States";
import { api } from "@/lib/api";
import { can, useAuth, useRole } from "@/lib/role";
import { addDays, clinicDay, clinicTime, fmtDay, fmtDayShort, fmtTime, minuteOfDay, today, weekStart } from "@/lib/time";
import type { Appointment } from "@/lib/types";
import { useFetch } from "@/lib/useFetch";

const DAY_START = 8 * 60; // 08:00
const DAY_END = 19 * 60; // 19:00
const PX_PER_MIN = 1.2;
const HOURS = Array.from({ length: (DAY_END - DAY_START) / 60 }, (_, i) => DAY_START / 60 + i);

/** Put overlapping appointments side by side. Lanes are counted per group of overlapping
 *  appointments, so one that overlaps nothing keeps the full column width. */
function layout(items: Appointment[]) {
  const time = (s: string) => new Date(s).getTime();
  const placed: { a: Appointment; lane: number; lanes: number }[] = [];
  let group: typeof placed = [];
  let laneEnds: number[] = [];
  let groupEnd = 0;
  const closeGroup = () => group.forEach((p) => (p.lanes = laneEnds.length));
  for (const a of [...items].sort((x, y) => time(x.start_at) - time(y.start_at))) {
    const start = time(a.start_at);
    if (start >= groupEnd) {
      closeGroup();
      group = [];
      laneEnds = [];
    }
    let lane = laneEnds.findIndex((end) => end <= start);
    if (lane < 0) lane = laneEnds.push(0) - 1;
    laneEnds[lane] = time(a.end_at);
    groupEnd = Math.max(groupEnd, laneEnds[lane]);
    const p = { a, lane, lanes: 1 };
    group.push(p);
    placed.push(p);
  }
  closeGroup();
  return placed;
}

type Column = { key: string; label: string; date: string; dentistId: number | null; items: Appointment[] };

export default function CalendarPage() {
  return (
    <Suspense fallback={<Loading />}>
      <Calendar />
    </Suspense>
  );
}

/** Opens on ?date=YYYY-MM-DD&view=day|week when given (e.g. links from other pages). */
function Calendar() {
  const params = useSearchParams();
  const router = useRouter();
  const role = useRole();
  const { user } = useAuth();
  const dentists = useDentists();
  const [view, setView] = useState<"day" | "week">(params.get("view") === "week" ? "week" : "day");
  const [day, setDay] = useState(() => (/^\d{4}-\d{2}-\d{2}$/.test(params.get("date") ?? "") ? params.get("date")! : today()));
  const [picked, setPicked] = useState<number | null>(null);
  const dentistId = role === "dentist" ? ownDentistId(dentists.data, user?.id) : picked;
  const [showCancelled, setShowCancelled] = useState(false);

  const from = view === "day" ? day : weekStart(day);
  const days = view === "day" ? 1 : 7;
  const appts = useFetch(
    () =>
      api.appointments.list({
        date_from: clinicTime(from).toISOString(),
        date_to: clinicTime(addDays(from, days)).toISOString(),
        dentist_id: dentistId ?? undefined,
        size: 500,
      }),
    [from, days, dentistId],
  );

  const visible = (appts.data?.items ?? []).filter((a) => showCancelled || a.status !== "cancelled");
  const columns: Column[] =
    view === "day"
      ? (dentists.data ?? [])
          .filter((d) => dentistId == null || d.id === dentistId)
          .map((d) => ({
            key: `d${d.id}`,
            label: d.full_name,
            date: day,
            dentistId: d.id,
            items: visible.filter((a) => a.dentist_id === d.id),
          }))
      : Array.from({ length: 7 }, (_, i) => {
          const date = addDays(from, i);
          return { key: date, label: fmtDayShort(date), date, dentistId, items: visible.filter((a) => clinicDay(a.start_at) === date) };
        });

  function bookAt(e: MouseEvent<HTMLDivElement>, col: Column) {
    if (!can.book(role)) return;
    const y = e.clientY - e.currentTarget.getBoundingClientRect().top;
    const min = DAY_START + Math.floor(y / PX_PER_MIN / 15) * 15;
    const hm = `${String(Math.floor(min / 60)).padStart(2, "0")}:${String(min % 60).padStart(2, "0")}`;
    const q = new URLSearchParams({ date: col.date, time: hm });
    if (col.dentistId) q.set("dentist", String(col.dentistId));
    router.push(`/appointments/new?${q}`);
  }

  const step = view === "day" ? 1 : 7;
  const title = view === "day" ? fmtDay(day) : `${fmtDayShort(from)} – ${fmtDay(addDays(from, 6))}`;

  return (
    <>
      <PageHeader title="Calendar" />

      <div className="mb-4 flex flex-wrap items-end gap-3">
        <div className="flex items-center gap-1">
          <Button variant="secondary" aria-label="Previous" onClick={() => setDay(addDays(day, -step))}>
            ‹
          </Button>
          <Button variant="secondary" onClick={() => setDay(today())}>
            Today
          </Button>
          <Button variant="secondary" aria-label="Next" onClick={() => setDay(addDays(day, step))}>
            ›
          </Button>
          <span className="ml-2 font-medium">{title}</span>
        </div>
        <div className="ml-auto flex flex-wrap items-end gap-3">
          <div role="group" aria-label="View" className="inline-flex overflow-hidden rounded-md border border-slate-300">
            {(["day", "week"] as const).map((v) => (
              <button
                key={v}
                type="button"
                aria-pressed={view === v}
                onClick={() => setView(v)}
                className={`px-3 py-2 text-sm capitalize ${view === v ? "bg-teal-600 text-white" : "bg-white text-slate-700 hover:bg-slate-50"}`}
              >
                {v}
              </button>
            ))}
          </div>
          {role !== "dentist" && (
            <div className="w-56">
              <DentistSelect dentists={dentists.data} value={picked} onChange={setPicked} allLabel="All dentists" />
            </div>
          )}
          <label className="flex items-center gap-2 pb-2 text-sm text-slate-600">
            <input type="checkbox" checked={showCancelled} onChange={(e) => setShowCancelled(e.target.checked)} />
            Show cancelled
          </label>
        </div>
      </div>

      {appts.error !== undefined || dentists.error !== undefined ? (
        <ErrorBox error={appts.error ?? dentists.error} onRetry={() => (appts.reload(), dentists.reload())} />
      ) : !appts.data || !dentists.data ? (
        <Loading />
      ) : columns.length === 0 ? (
        <p className="text-sm text-slate-500">No dentists yet.</p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
          <div className="flex" style={{ minWidth: 56 + columns.length * 150 }}>
            {/* time gutter */}
            <div className="w-14 shrink-0 border-r border-slate-200">
              <div className="h-10 border-b border-slate-200" />
              <div className="relative" style={{ height: (DAY_END - DAY_START) * PX_PER_MIN }}>
                {HOURS.map((h) => (
                  <div
                    key={h}
                    className="absolute right-2 -translate-y-1/2 text-xs text-slate-400 tabular-nums"
                    style={{ top: (h * 60 - DAY_START) * PX_PER_MIN }}
                  >
                    {h > DAY_START / 60 && `${String(h).padStart(2, "0")}:00`}
                  </div>
                ))}
              </div>
            </div>

            {columns.map((col) => {
              const placed = layout(col.items);
              const isToday = col.date === today();
              return (
                <div key={col.key} className="min-w-0 flex-1 border-r border-slate-100 last:border-r-0">
                  <div
                    className={`flex h-10 items-center justify-center truncate border-b border-slate-200 px-2 text-sm font-medium ${isToday && view === "week" ? "text-teal-700" : "text-slate-700"}`}
                  >
                    {col.label}
                  </div>
                  <div
                    className={`relative ${can.book(role) ? "cursor-copy" : ""}`}
                    style={{ height: (DAY_END - DAY_START) * PX_PER_MIN }}
                    onClick={(e) => bookAt(e, col)}
                    title={can.book(role) ? "Click an empty time to book" : undefined}
                  >
                    {HOURS.map((h) => (
                      <div
                        key={h}
                        className="absolute inset-x-0 border-t border-slate-100"
                        style={{ top: (h * 60 - DAY_START) * PX_PER_MIN }}
                      />
                    ))}
                    {placed.map(({ a, lane, lanes }) => {
                      const start = Math.max(minuteOfDay(a.start_at), DAY_START);
                      const end = Math.min(minuteOfDay(a.end_at) || 24 * 60, DAY_END);
                      return (
                        <Link
                          key={a.id}
                          href={`/appointments/${a.id}`}
                          onClick={(e) => e.stopPropagation()}
                          title={`${fmtTime(a.start_at)}–${fmtTime(a.end_at)} ${patientName(a.patient)} · ${a.dentist.full_name} · ${STATUS_LABEL[a.status]}`}
                          className={`absolute overflow-hidden rounded border-l-4 px-1.5 py-0.5 text-xs leading-tight shadow-sm hover:z-10 hover:shadow ${STATUS_STYLE[a.status]}`}
                          style={{
                            top: (start - DAY_START) * PX_PER_MIN + 1,
                            height: Math.max((end - start) * PX_PER_MIN - 2, 16),
                            left: `calc(${(lane / lanes) * 100}% + 2px)`,
                            width: `calc(${100 / lanes}% - 4px)`,
                          }}
                        >
                          <span className="font-semibold tabular-nums">{fmtTime(a.start_at)}</span> {patientName(a.patient)}
                          {view === "week" && <span className="block truncate opacity-80">{a.dentist.full_name}</span>}
                          {a.reason && <span className="block truncate opacity-80">{a.reason}</span>}
                        </Link>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
      {appts.data && appts.data.total > appts.data.items.length && (
        <p className="mt-2 text-sm text-amber-700">
          Showing the first {appts.data.items.length} of {appts.data.total} appointments — pick a dentist to see all.
        </p>
      )}
    </>
  );
}
