"use client";

import { useState } from "react";
import { DentistSelect, useDentists } from "@/components/DentistSelect";
import { RoleGate } from "@/components/Shell";
import { Button } from "@/components/ui/Button";
import { Input, Select } from "@/components/ui/Input";
import { Card, ErrorBox, Loading, PageHeader } from "@/components/ui/States";
import { Table } from "@/components/ui/Table";
import { api } from "@/lib/api";
import { can } from "@/lib/role";
import { addDays, today } from "@/lib/time";
import type { DentistRow, PeriodRow } from "@/lib/types";
import { useFetch } from "@/lib/useFetch";

type GroupBy = "day" | "week" | "month";

// Categorical slots 1–4 of the validated chart palette, in fixed order (stacked bottom → top).
const SERIES = [
  { key: "completed", label: "Completed", color: "#2a78d6" },
  { key: "upcoming", label: "Upcoming", color: "#eb6834" },
  { key: "cancelled", label: "Cancelled", color: "#1baf7a" },
  { key: "no_show", label: "No-show", color: "#eda100" },
] as const;

const MAX_DAYS = 3 * 366;

const pct = (r: number | null) => (r == null ? "—" : `${(r * 100).toFixed(1)}%`);

function periodLabel(period: string, by: GroupBy) {
  const d = new Date(`${period}T00:00:00Z`);
  if (by === "month") return d.toLocaleDateString("en-GB", { timeZone: "UTC", month: "short", year: "numeric" });
  const s = d.toLocaleDateString("en-GB", { timeZone: "UTC", day: "numeric", month: "short" });
  return by === "week" ? `w/c ${s}` : s;
}

/** Gridline step for 4 gridlines; counts are whole numbers so the step is at least 1. */
function niceStep(max: number) {
  const raw = Math.max(max, 4) / 4;
  const p = 10 ** Math.floor(Math.log10(raw));
  return ([1, 2, 5, 10].find((m) => m * p >= raw) ?? 10) * p;
}

/** First and last day of the current month. */
function thisMonth() {
  const first = `${today().slice(0, 7)}-01`;
  return { first, last: addDays(`${addDays(first, 32).slice(0, 7)}-01`, -1) };
}

function downloadCsv(name: string, header: string[], rows: (string | number)[][]) {
  const esc = (v: string | number) => (/[",\n]/.test(String(v)) ? `"${String(v).replace(/"/g, '""')}"` : String(v));
  const csv = [header, ...rows].map((r) => r.map(esc).join(",")).join("\n");
  const url = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
  const a = Object.assign(document.createElement("a"), { href: url, download: name });
  a.click();
  URL.revokeObjectURL(url);
}

export default function ReportsPage() {
  return (
    <>
      <PageHeader title="Reports" />
      <RoleGate allow={can.reports}>
        <Reports />
      </RoleGate>
    </>
  );
}

function Reports() {
  const dentists = useDentists();
  const [from, setFrom] = useState(() => thisMonth().first);
  const [to, setTo] = useState(() => thisMonth().last);
  const [groupBy, setGroupBy] = useState<GroupBy>("day");
  const [dentistId, setDentistId] = useState<number | null>(null);

  const days = (new Date(to).getTime() - new Date(from).getTime()) / 86_400_000;
  const rangeError =
    !from || !to ? "Pick both dates" : days < 0 ? "“From” must be before “To”" : days > MAX_DAYS ? "Pick at most 3 years" : undefined;

  const data = useFetch(async () => {
    if (rangeError) return null;
    const range = { date_from: from, date_to: to };
    const dentist_id = dentistId ?? undefined;
    const [rates, periods, perDentist] = await Promise.all([
      api.reports.rates({ ...range, dentist_id }),
      api.reports.appointments({ ...range, group_by: groupBy, dentist_id }),
      api.reports.dentists(range),
    ]);
    return { rates, periods, perDentist: dentistId ? perDentist.filter((d) => d.dentist_id === dentistId) : perDentist };
  }, [from, to, groupBy, dentistId, rangeError]);

  function exportCsv() {
    if (!data.data) return;
    const keys = ["total", "completed", "upcoming", "cancelled", "no_show"] as const;
    downloadCsv(
      `dentalflow-appointments-${from}-to-${to}.csv`,
      ["period", ...keys],
      data.data.periods.map((r) => [r.period, ...keys.map((k) => r[k])]),
    );
    downloadCsv(
      `dentalflow-dentists-${from}-to-${to}.csv`,
      ["dentist", ...keys, "chair_hours"],
      data.data.perDentist.map((r) => [r.full_name, ...keys.map((k) => r[k]), (r.booked_minutes / 60).toFixed(1)]),
    );
  }

  return (
    <div className="space-y-6">
      <div className="no-print flex flex-wrap items-end gap-3">
        <div className="w-40">
          <Input label="From" type="date" value={from} max={to} onChange={(e) => setFrom(e.target.value)} />
        </div>
        <div className="w-40">
          <Input label="To" type="date" value={to} min={from} onChange={(e) => setTo(e.target.value)} />
        </div>
        <div className="w-32">
          <Select label="Group by" value={groupBy} onChange={(e) => setGroupBy(e.target.value as GroupBy)}>
            <option value="day">Day</option>
            <option value="week">Week</option>
            <option value="month">Month</option>
          </Select>
        </div>
        <div className="w-56">
          <DentistSelect dentists={dentists.data} value={dentistId} onChange={setDentistId} allLabel="All dentists" />
        </div>
        <div className="ml-auto flex gap-2">
          <Button variant="secondary" disabled={!data.data} onClick={exportCsv}>
            Export CSV
          </Button>
          <Button variant="secondary" disabled={!data.data} onClick={() => window.print()}>
            Print / PDF
          </Button>
        </div>
      </div>

      {rangeError ? (
        <p className="text-sm text-red-600">{rangeError}</p>
      ) : data.error !== undefined ? (
        <ErrorBox error={data.error} onRetry={data.reload} />
      ) : !data.data ? (
        <Loading />
      ) : (
        <div className={`space-y-6 ${data.loading ? "opacity-60" : ""}`}>
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            <Tile label="Appointments" value={String(data.data.rates.total)} />
            <Tile label="Completed" value={String(data.data.rates.completed)} />
            <Tile label="Cancellation rate" value={pct(data.data.rates.cancellation_rate)} hint="cancelled ÷ all" />
            <Tile label="No-show rate" value={pct(data.data.rates.no_show_rate)} hint="no-shows ÷ (completed + no-shows)" />
          </div>

          <Card title="Appointments over time">
            <StackedBars rows={data.data.periods} groupBy={groupBy} />
          </Card>

          <Card title="Per dentist">
            <Table<DentistRow>
              rows={data.data.perDentist}
              rowKey={(r) => r.dentist_id}
              empty="No dentists."
              columns={[
                { header: "Dentist", cell: (r) => <span className="font-medium">{r.full_name}</span> },
                { header: "Total", cell: (r) => r.total, className: "text-right tabular-nums" },
                { header: "Completed", cell: (r) => r.completed, className: "text-right tabular-nums" },
                { header: "Upcoming", cell: (r) => r.upcoming, className: "text-right tabular-nums" },
                { header: "Cancelled", cell: (r) => r.cancelled, className: "text-right tabular-nums" },
                { header: "No-show", cell: (r) => r.no_show, className: "text-right tabular-nums" },
                { header: "Chair hours", cell: (r) => (r.booked_minutes / 60).toFixed(1), className: "text-right tabular-nums" },
              ]}
            />
          </Card>
        </div>
      )}
    </div>
  );
}

function Tile({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white px-4 py-3">
      <div className="text-sm text-slate-500">{label}</div>
      <div className="mt-1 text-2xl font-semibold tabular-nums">{value}</div>
      {hint && <div className="mt-0.5 text-xs text-slate-400">{hint}</div>}
    </div>
  );
}

function StackedBars({ rows, groupBy }: { rows: PeriodRow[]; groupBy: GroupBy }) {
  const [hover, setHover] = useState<number | null>(null);
  const [asTable, setAsTable] = useState(false);
  const HEIGHT = 240;
  const step = niceStep(Math.max(0, ...rows.map((r) => r.total)));
  const max = step * 4;
  const labelEvery = Math.ceil(rows.length / 12);
  const h = hover != null ? rows[hover] : null;

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <ul className="flex flex-wrap gap-4 text-sm text-slate-600" aria-label="Legend">
          {SERIES.map((s) => (
            <li key={s.key} className="flex items-center gap-1.5">
              <span className="h-3 w-3 rounded-sm" style={{ background: s.color }} aria-hidden />
              {s.label}
            </li>
          ))}
        </ul>
        <Button variant="ghost" className="no-print !py-1" aria-pressed={asTable} onClick={() => setAsTable(!asTable)}>
          {asTable ? "Show chart" : "Show as table"}
        </Button>
      </div>

      {asTable ? (
        <Table<PeriodRow>
          rows={rows}
          rowKey={(r) => r.period}
          columns={[
            { header: "Period", cell: (r) => periodLabel(r.period, groupBy) },
            { header: "Total", cell: (r) => r.total, className: "text-right tabular-nums" },
            ...SERIES.map((s) => ({ header: s.label, cell: (r: PeriodRow) => r[s.key], className: "text-right tabular-nums" })),
          ]}
        />
      ) : (
        <div className="flex gap-2">
          {/* y axis */}
          <div className="relative w-8 shrink-0 text-right text-xs text-slate-500 tabular-nums" style={{ height: HEIGHT }}>
            {[0, 1, 2, 3, 4].map((i) => (
              <span key={i} className="absolute right-0 translate-y-1/2" style={{ bottom: (i / 4) * HEIGHT }}>
                {i * step}
              </span>
            ))}
          </div>
          <div className="min-w-0 flex-1">
            <div className="relative" style={{ height: HEIGHT }} onMouseLeave={() => setHover(null)}>
              {[0, 1, 2, 3, 4].map((i) => (
                <div
                  key={i}
                  className={`absolute inset-x-0 border-t ${i === 0 ? "border-slate-300" : "border-slate-100"}`}
                  style={{ bottom: (i / 4) * HEIGHT }}
                />
              ))}
              <div className="absolute inset-0 flex items-end gap-[2px]">
                {rows.map((r, i) => (
                  <div
                    key={r.period}
                    className="flex h-full flex-1 items-end justify-center"
                    onMouseEnter={() => setHover(i)}
                    aria-label={`${periodLabel(r.period, groupBy)}: ${r.total} appointments`}
                  >
                    <div
                      className={`flex w-full max-w-10 flex-col-reverse gap-[2px] overflow-hidden rounded-t-[4px] ${hover != null && hover !== i ? "opacity-60" : ""}`}
                      style={{ height: (r.total / max) * HEIGHT }}
                    >
                      {SERIES.map((s) =>
                        r[s.key] ? (
                          <div key={s.key} style={{ background: s.color, flexGrow: r[s.key], flexBasis: 0, minHeight: 1 }} />
                        ) : null,
                      )}
                    </div>
                  </div>
                ))}
              </div>
              {h && hover != null && (
                <div
                  role="tooltip"
                  className="pointer-events-none absolute top-0 z-10 w-44 rounded-md border border-slate-200 bg-white p-2 text-xs shadow-lg"
                  style={{
                    left: `${((hover + 0.5) / rows.length) * 100}%`,
                    transform: hover > rows.length / 2 ? "translateX(calc(-100% - 8px))" : "translateX(8px)",
                  }}
                >
                  <div className="mb-1 font-semibold text-slate-900">{periodLabel(h.period, groupBy)}</div>
                  {[...SERIES].reverse().map((s) => (
                    <div key={s.key} className="flex items-center justify-between gap-2 text-slate-600">
                      <span className="flex items-center gap-1.5">
                        <span className="h-2 w-2 rounded-sm" style={{ background: s.color }} />
                        {s.label}
                      </span>
                      <span className="tabular-nums text-slate-900">{h[s.key]}</span>
                    </div>
                  ))}
                  <div className="mt-1 flex justify-between border-t border-slate-100 pt-1 font-medium text-slate-900">
                    <span>Total</span>
                    <span className="tabular-nums">{h.total}</span>
                  </div>
                </div>
              )}
            </div>
            <div className="mt-1 flex gap-[2px] text-xs text-slate-500">
              {rows.map((r, i) => (
                <div key={r.period} className="flex-1 overflow-visible text-center whitespace-nowrap">
                  {i % labelEvery === 0 ? periodLabel(r.period, groupBy) : ""}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
