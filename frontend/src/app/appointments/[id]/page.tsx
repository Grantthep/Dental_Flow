"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";
import { patientName } from "@/components/PatientPicker";
import { SlotPicker } from "@/components/SlotPicker";
import { StatusBadge } from "@/components/StatusBadge";
import { Button } from "@/components/ui/Button";
import { Input, Textarea } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { Card, ErrorBox, Loading, PageHeader } from "@/components/ui/States";
import { ApiError, api, errorText } from "@/lib/api";
import { can, useRole } from "@/lib/role";
import { clinicDay, fmtDateTime, fmtTime, minutesBetween, today } from "@/lib/time";
import type { Appointment, AppointmentStatus, Slot } from "@/lib/types";
import { useFetch } from "@/lib/useFetch";

const OPEN: AppointmentStatus[] = ["booked", "confirmed"];

export default function AppointmentPage() {
  const id = Number(useParams<{ id: string }>().id);
  const role = useRole();
  const appt = useFetch(() => api.appointments.get(id), [id]);
  const [error, setError] = useState<string>();
  const [busy, setBusy] = useState(false);
  const [rescheduleOpen, setRescheduleOpen] = useState(false);
  const [confirmCancel, setConfirmCancel] = useState(false);

  async function run(action: () => Promise<Appointment>) {
    setBusy(true);
    setError(undefined);
    try {
      await action();
      appt.reload();
    } catch (e) {
      setError(errorText(e));
    } finally {
      setBusy(false);
    }
  }

  if (appt.error !== undefined)
    return (
      <>
        <PageHeader title="Appointment" />
        <ErrorBox error={appt.error} onRetry={appt.reload} />
      </>
    );
  if (!appt.data) return <Loading />;

  const a = appt.data;
  const open = OPEN.includes(a.status);

  return (
    <>
      <PageHeader
        title={`Appointment #${a.id}`}
        actions={
          open &&
          can.book(role) && (
            <>
              <Button variant="secondary" disabled={busy} onClick={() => setRescheduleOpen(true)}>
                Reschedule
              </Button>
              <Button variant="danger" disabled={busy} onClick={() => setConfirmCancel(true)}>
                Cancel appointment
              </Button>
            </>
          )
        }
      />

      {error && (
        <p role="alert" className="mb-4 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          {error}
        </p>
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        <Card title="Details" className="lg:col-span-2">
          <dl className="grid gap-x-6 gap-y-3 text-sm sm:grid-cols-2">
            <Item label="Patient">
              <Link href={`/patients/${a.patient_id}`} className="font-medium text-teal-700 hover:underline">
                {patientName(a.patient)}
              </Link>{" "}
              <span className="text-slate-500">· {a.patient.phone}</span>
            </Item>
            <Item label="Dentist">{a.dentist.full_name}</Item>
            <Item label="When">
              <Link href={`/calendar?date=${clinicDay(a.start_at)}`} className="hover:underline">
                {fmtDateTime(a.start_at)}–{fmtTime(a.end_at)}
              </Link>{" "}
              ({minutesBetween(a.start_at, a.end_at)} min)
            </Item>
            <Item label="Status">
              <StatusBadge status={a.status} />
            </Item>
          </dl>
        </Card>

        <Card title="Status">
          {open ? (
            <div className="flex flex-wrap gap-2">
              {a.status === "booked" && can.confirm(role) && (
                <Button
                  variant="secondary"
                  disabled={busy}
                  onClick={() => run(() => api.appointments.update(a.id, { status: "confirmed" }))}
                >
                  Confirm
                </Button>
              )}
              <Button variant="secondary" disabled={busy} onClick={() => run(() => api.appointments.update(a.id, { status: "completed" }))}>
                Mark completed
              </Button>
              <Button variant="secondary" disabled={busy} onClick={() => run(() => api.appointments.update(a.id, { status: "no_show" }))}>
                Mark no-show
              </Button>
            </div>
          ) : (
            <p className="text-sm text-slate-500">This appointment is closed; its status can&apos;t change.</p>
          )}
        </Card>

        <NotesCard
          key={a.updated_at}
          appt={a}
          disabled={busy}
          canEditReason={can.editReason(role)}
          onSave={(body) => run(() => api.appointments.update(a.id, body))}
        />
      </div>

      <Modal open={rescheduleOpen} onClose={() => setRescheduleOpen(false)} title="Reschedule">
        <Reschedule
          appt={a}
          onDone={() => {
            setRescheduleOpen(false);
            appt.reload();
          }}
        />
      </Modal>

      <Modal open={confirmCancel} onClose={() => setConfirmCancel(false)} title="Cancel appointment?">
        <p className="text-sm text-slate-600">
          {patientName(a.patient)} on {fmtDateTime(a.start_at)} will be marked cancelled and the time freed up. This can&apos;t be undone.
        </p>
        <div className="mt-5 flex justify-end gap-2">
          <Button variant="secondary" onClick={() => setConfirmCancel(false)}>
            Keep it
          </Button>
          <Button
            variant="danger"
            onClick={() => {
              setConfirmCancel(false);
              run(() => api.appointments.cancel(a.id));
            }}
          >
            Cancel appointment
          </Button>
        </div>
      </Modal>
    </>
  );
}

function Item({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <dt className="text-slate-500">{label}</dt>
      <dd className="mt-0.5 text-slate-900">{children}</dd>
    </div>
  );
}

function NotesCard({
  appt,
  disabled,
  canEditReason,
  onSave,
}: {
  appt: Appointment;
  disabled: boolean;
  canEditReason: boolean;
  onSave: (b: { reason?: string | null; notes: string | null }) => void;
}) {
  const [reason, setReason] = useState(appt.reason ?? "");
  const [notes, setNotes] = useState(appt.notes ?? "");
  const dirty = reason !== (appt.reason ?? "") || notes !== (appt.notes ?? "");
  return (
    <Card title="Reason & notes" className="lg:col-span-3">
      <div className="space-y-4">
        <Input label="Reason" maxLength={255} value={reason} disabled={!canEditReason} onChange={(e) => setReason(e.target.value)} />
        <Textarea label="Notes" rows={4} value={notes} onChange={(e) => setNotes(e.target.value)} />
        <div className="flex justify-end">
          <Button
            disabled={!dirty || disabled}
            // Dentists may only send notes (the backend rejects any other field from them).
            onClick={() => onSave({ ...(canEditReason && { reason: reason.trim() || null }), notes: notes.trim() || null })}
          >
            Save notes
          </Button>
        </div>
      </div>
    </Card>
  );
}

function Reschedule({ appt, onDone }: { appt: Appointment; onDone: () => void }) {
  const day = clinicDay(appt.start_at);
  const [date, setDate] = useState(day < today() ? today() : day);
  const [slot, setSlot] = useState<Slot | null>(null);
  const [error, setError] = useState<string>();
  const [saving, setSaving] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);
  const duration = minutesBetween(appt.start_at, appt.end_at);

  async function save() {
    if (!slot) return;
    setSaving(true);
    setError(undefined);
    try {
      await api.appointments.reschedule(appt.id, slot);
      onDone();
    } catch (e) {
      setError(errorText(e));
      if (e instanceof ApiError && e.status === 409) {
        setSlot(null);
        setRefreshKey((k) => k + 1);
      }
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-600">
        Now: {fmtDateTime(appt.start_at)} with {appt.dentist.full_name}, {duration} min.
      </p>
      <Input
        label="New date"
        type="date"
        min={today()}
        value={date}
        onChange={(e) => {
          setDate(e.target.value);
          setSlot(null);
        }}
      />
      {/* Duration must fit the slot API's 15–240 min range. */}
      <SlotPicker
        dentistId={appt.dentist_id}
        date={date}
        duration={Math.min(Math.max(duration, 15), 240)}
        value={slot?.start_at ?? null}
        onChange={setSlot}
        refreshKey={refreshKey}
      />
      {error && (
        <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-800">
          {error}
        </p>
      )}
      <div className="flex justify-end">
        <Button disabled={!slot || saving} onClick={save}>
          {saving ? "Saving…" : slot ? `Move to ${fmtTime(slot.start_at)}` : "Pick a time"}
        </Button>
      </div>
    </div>
  );
}
