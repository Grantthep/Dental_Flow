"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState, type FormEvent } from "react";
import { DentistSelect, useDentists } from "@/components/DentistSelect";
import { PatientForm } from "@/components/PatientForm";
import { PatientPicker } from "@/components/PatientPicker";
import { RoleGate } from "@/components/Shell";
import { SlotPicker } from "@/components/SlotPicker";
import { Button } from "@/components/ui/Button";
import { Input, Select, Textarea } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { Card, Loading, PageHeader } from "@/components/ui/States";
import { ApiError, api, errorText } from "@/lib/api";
import { can } from "@/lib/role";
import { fmtDateTime, today } from "@/lib/time";
import type { Patient, Slot } from "@/lib/types";

export default function NewAppointmentPage() {
  return (
    <>
      <PageHeader title="New booking" />
      <RoleGate allow={can.book}>
        <Suspense fallback={<Loading />}>
          <BookingForm />
        </Suspense>
      </RoleGate>
    </>
  );
}

function BookingForm() {
  const params = useSearchParams();
  const router = useRouter();
  const dentists = useDentists();

  const [patient, setPatient] = useState<Patient | null>(null);
  const [dentistId, setDentistId] = useState<number | null>(params.get("dentist") ? Number(params.get("dentist")) : null);
  const [date, setDate] = useState(params.get("date") ?? today());
  const [duration, setDuration] = useState(30);
  const [slot, setSlot] = useState<Slot | null>(null);
  const [reason, setReason] = useState("");
  const [notes, setNotes] = useState("");
  const [errors, setErrors] = useState<{ patient?: string; dentist?: string; slot?: string }>({});
  const [submitError, setSubmitError] = useState<string>();
  const [saving, setSaving] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);
  const [newPatientOpen, setNewPatientOpen] = useState(false);

  // ?patient=ID pre-fills the patient (from the patient page's "Book appointment").
  useEffect(() => {
    const id = Number(params.get("patient"));
    if (id) api.patients.get(id).then(setPatient, () => {});
  }, [params]);

  // A different dentist/day/length means the chosen slot no longer applies.
  useEffect(() => setSlot(null), [dentistId, date, duration]);

  async function submit(e: FormEvent) {
    e.preventDefault();
    const errs = {
      patient: patient ? undefined : "Choose a patient",
      dentist: dentistId ? undefined : "Choose a dentist",
      slot: slot ? undefined : "Choose a free time",
    };
    setErrors(errs);
    if (!patient || !dentistId || !slot) return;

    setSaving(true);
    setSubmitError(undefined);
    try {
      const appt = await api.appointments.create({
        patient_id: patient.id,
        dentist_id: dentistId,
        start_at: slot.start_at,
        end_at: slot.end_at,
        reason: reason.trim() || null,
        notes: notes.trim() || null,
      });
      router.push(`/appointments/${appt.id}`);
    } catch (err) {
      setSubmitError(errorText(err));
      // Someone else may have just taken the slot: refresh the list.
      if (err instanceof ApiError && err.status === 409) {
        setSlot(null);
        setRefreshKey((k) => k + 1);
      }
      setSaving(false);
    }
  }

  return (
    <>
      <form onSubmit={submit} noValidate className="max-w-3xl space-y-6">
        <Card>
          <div className="space-y-2">
            <PatientPicker value={patient} onChange={setPatient} error={errors.patient} />
            {!patient && (
              <Button variant="ghost" className="!px-0 text-teal-700" onClick={() => setNewPatientOpen(true)}>
                + New patient
              </Button>
            )}
          </div>
        </Card>

        <Card>
          <div className="grid gap-4 sm:grid-cols-3">
            <DentistSelect dentists={dentists.data} value={dentistId} onChange={setDentistId} error={errors.dentist} />
            <Input label="Date" type="date" min={today()} value={date} onChange={(e) => setDate(e.target.value)} />
            <Select label="Length" value={duration} onChange={(e) => setDuration(Number(e.target.value))}>
              {[15, 30, 45, 60, 90, 120].map((m) => (
                <option key={m} value={m}>
                  {m} min
                </option>
              ))}
            </Select>
          </div>
          <div className="mt-4">
            <SlotPicker
              dentistId={dentistId}
              date={date}
              duration={duration}
              value={slot?.start_at ?? null}
              onChange={setSlot}
              refreshKey={refreshKey}
              preferTime={params.get("time")}
            />
            {errors.slot && <p className="mt-1 text-sm text-red-600">{errors.slot}</p>}
          </div>
        </Card>

        <Card>
          <div className="space-y-4">
            <Input
              label="Reason"
              placeholder="e.g. Check-up, filling, cleaning"
              maxLength={255}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
            />
            <Textarea label="Notes" value={notes} onChange={(e) => setNotes(e.target.value)} />
          </div>
        </Card>

        {submitError && (
          <p role="alert" className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
            {submitError}
          </p>
        )}

        <div className="flex flex-wrap items-center justify-end gap-3">
          {slot && dentistId && (
            <span className="mr-auto text-sm text-slate-600">
              {fmtDateTime(slot.start_at)} with {dentists.data?.find((d) => d.id === dentistId)?.full_name}
            </span>
          )}
          <Button variant="secondary" onClick={() => router.back()}>
            Cancel
          </Button>
          <Button type="submit" disabled={saving}>
            {saving ? "Booking…" : "Book appointment"}
          </Button>
        </div>
      </form>

      <Modal open={newPatientOpen} onClose={() => setNewPatientOpen(false)} title="New patient">
        <PatientForm
          onCancel={() => setNewPatientOpen(false)}
          onSaved={(p) => {
            setPatient(p);
            setNewPatientOpen(false);
          }}
        />
      </Modal>
    </>
  );
}
