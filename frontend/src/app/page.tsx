"use client";

import Link from "next/link";
import { useState } from "react";
import { DentistSelect, useDentists } from "@/components/DentistSelect";
import { patientName } from "@/components/PatientPicker";
import { StatusBadge } from "@/components/StatusBadge";
import { Button, ButtonLink } from "@/components/ui/Button";
import { Card, ErrorBox, Loading, PageHeader } from "@/components/ui/States";
import { Table } from "@/components/ui/Table";
import { api, errorText } from "@/lib/api";
import { can, useRole } from "@/lib/role";
import { addDays, clinicTime, fmtDay, fmtTime, today } from "@/lib/time";
import type { Appointment, AppointmentStatus } from "@/lib/types";
import { useFetch } from "@/lib/useFetch";

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white px-4 py-3">
      <div className="text-sm text-slate-500">{label}</div>
      <div className="mt-1 text-2xl font-semibold tabular-nums">{value}</div>
    </div>
  );
}

export default function Dashboard() {
  const role = useRole();
  const dentists = useDentists();
  const [dentistId, setDentistId] = useState<number | null>(null);
  const [actionError, setActionError] = useState<string>();
  const day = today();

  const appts = useFetch(
    () =>
      api.appointments.list({
        date_from: clinicTime(day).toISOString(),
        date_to: clinicTime(addDays(day, 1)).toISOString(),
        dentist_id: dentistId ?? undefined,
        size: 500,
      }),
    [day, dentistId],
  );

  async function setStatus(a: Appointment, status: AppointmentStatus) {
    setActionError(undefined);
    try {
      await api.appointments.update(a.id, { status });
      appts.reload();
    } catch (e) {
      setActionError(errorText(e));
    }
  }

  const items = appts.data?.items ?? [];
  const active = items.filter((a) => a.status !== "cancelled");
  const now = Date.now();
  const next = active.find((a) => (a.status === "booked" || a.status === "confirmed") && new Date(a.end_at).getTime() > now);

  return (
    <>
      <PageHeader
        title={`Today — ${fmtDay(day)}`}
        actions={can.book(role) && <ButtonLink href="/appointments/new">New booking</ButtonLink>}
      />

      <div className="mb-6 max-w-xs">
        <DentistSelect dentists={dentists.data} value={dentistId} onChange={setDentistId} allLabel="All dentists" />
      </div>

      {appts.error !== undefined ? (
        <ErrorBox error={appts.error} onRetry={appts.reload} />
      ) : appts.loading && !appts.data ? (
        <Loading />
      ) : (
        <div className="space-y-6">
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            <Stat label="Appointments today" value={active.length} />
            <Stat label="Still to come" value={active.filter((a) => a.status === "booked" || a.status === "confirmed").length} />
            <Stat label="Completed" value={active.filter((a) => a.status === "completed").length} />
            <Stat label="No-shows" value={active.filter((a) => a.status === "no_show").length} />
          </div>

          <Card title="Next patient">
            {next ? (
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <div className="text-lg font-semibold">
                    {fmtTime(next.start_at)} · {patientName(next.patient)}
                  </div>
                  <div className="text-sm text-slate-600">
                    {next.reason || "No reason given"} · {next.dentist.full_name} · {next.patient.phone}
                  </div>
                </div>
                <ButtonLink variant="secondary" href={`/appointments/${next.id}`}>
                  Open
                </ButtonLink>
              </div>
            ) : (
              <p className="text-sm text-slate-500">No more patients today.</p>
            )}
          </Card>

          <div>
            <h2 className="mb-3 text-base font-semibold">Today&apos;s appointments</h2>
            {actionError && (
              <p role="alert" className="mb-3 rounded-md bg-red-50 px-3 py-2 text-sm text-red-800">
                {actionError}
              </p>
            )}
            <Table
              rows={items}
              rowKey={(a) => a.id}
              empty="No appointments today."
              columns={[
                {
                  header: "Time",
                  cell: (a) => (
                    <span className="tabular-nums">
                      {fmtTime(a.start_at)}–{fmtTime(a.end_at)}
                    </span>
                  ),
                },
                {
                  header: "Patient",
                  cell: (a) => (
                    <Link className="font-medium text-teal-700 hover:underline" href={`/appointments/${a.id}`}>
                      {patientName(a.patient)}
                    </Link>
                  ),
                },
                { header: "Dentist", cell: (a) => a.dentist.full_name },
                { header: "Reason", cell: (a) => a.reason ?? "—" },
                { header: "Status", cell: (a) => <StatusBadge status={a.status} /> },
                {
                  header: "Actions",
                  cell: (a) =>
                    (a.status === "booked" || a.status === "confirmed") && (
                      <div className="flex gap-1">
                        {a.status === "booked" && (
                          <Button variant="ghost" className="!px-2 !py-1" onClick={() => setStatus(a, "confirmed")}>
                            Confirm
                          </Button>
                        )}
                        <Button variant="ghost" className="!px-2 !py-1" onClick={() => setStatus(a, "completed")}>
                          Done
                        </Button>
                        <Button variant="ghost" className="!px-2 !py-1" onClick={() => setStatus(a, "no_show")}>
                          No-show
                        </Button>
                      </div>
                    ),
                },
              ]}
            />
          </div>
        </div>
      )}
    </>
  );
}
