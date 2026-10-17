"use client";

import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import { PatientForm } from "@/components/PatientForm";
import { patientName } from "@/components/PatientPicker";
import { StatusBadge } from "@/components/StatusBadge";
import { Button, ButtonLink } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { Card, ErrorBox, Loading, PageHeader } from "@/components/ui/States";
import { Table } from "@/components/ui/Table";
import { api, errorText } from "@/lib/api";
import { can, useRole } from "@/lib/role";
import { fmtDateTime } from "@/lib/time";
import { useFetch } from "@/lib/useFetch";

export default function PatientPage() {
  const id = Number(useParams<{ id: string }>().id);
  const router = useRouter();
  const role = useRole();
  const patient = useFetch(() => api.patients.get(id), [id]);
  const history = useFetch(() => api.appointments.list({ patient_id: id, size: 500 }), [id]);
  const [editing, setEditing] = useState(false);
  const [error, setError] = useState<string>();

  async function setActive(is_active: boolean) {
    setError(undefined);
    try {
      await api.patients.update(id, { is_active });
      patient.reload();
    } catch (e) {
      setError(errorText(e));
    }
  }

  if (patient.error !== undefined)
    return (
      <>
        <PageHeader title="Patient" />
        <ErrorBox error={patient.error} onRetry={patient.reload} />
      </>
    );
  if (!patient.data) return <Loading />;

  const p = patient.data;
  const editable = can.editPatients(role);
  // Newest first.
  const appointments = [...(history.data?.items ?? [])].reverse();

  return (
    <>
      <PageHeader
        title={patientName(p)}
        actions={
          <>
            {can.book(role) && p.is_active && <ButtonLink href={`/appointments/new?patient=${p.id}`}>Book appointment</ButtonLink>}
            {editable && (
              <>
                <Button variant="secondary" onClick={() => setEditing(true)}>
                  Edit
                </Button>
                <Button variant="secondary" onClick={() => setActive(!p.is_active)}>
                  {p.is_active ? "Deactivate" : "Reactivate"}
                </Button>
              </>
            )}
          </>
        }
      />

      {error && (
        <p role="alert" className="mb-4 rounded-md bg-red-50 px-4 py-3 text-sm text-red-800">
          {error}
        </p>
      )}
      {!p.is_active && (
        <p className="mb-4 rounded-md bg-amber-50 px-4 py-3 text-sm text-amber-800">This patient is inactive and hidden from search.</p>
      )}

      <div className="space-y-6">
        <Card title="Details">
          <dl className="grid gap-x-6 gap-y-3 text-sm sm:grid-cols-2 lg:grid-cols-3">
            {(
              [
                ["Phone", p.phone],
                ["Email", p.email],
                ["Date of birth", p.date_of_birth],
                ["Gender", p.gender],
                ["Address", p.address],
              ] as const
            ).map(([label, value]) => (
              <div key={label}>
                <dt className="text-slate-500">{label}</dt>
                <dd className="mt-0.5 text-slate-900">{value || "—"}</dd>
              </div>
            ))}
            <div className="sm:col-span-2 lg:col-span-3">
              <dt className="text-slate-500">Allergies / medical notes</dt>
              <dd className="mt-0.5 whitespace-pre-wrap text-slate-900">{p.medical_notes || "—"}</dd>
            </div>
          </dl>
        </Card>

        <div>
          <h2 className="mb-3 text-base font-semibold">Appointment history</h2>
          {history.error !== undefined ? (
            <ErrorBox error={history.error} onRetry={history.reload} />
          ) : !history.data ? (
            <Loading />
          ) : (
            <Table
              rows={appointments}
              rowKey={(a) => a.id}
              onRowClick={(a) => router.push(`/appointments/${a.id}`)}
              empty="No appointments yet."
              columns={[
                { header: "When", cell: (a) => fmtDateTime(a.start_at) },
                { header: "Dentist", cell: (a) => a.dentist.full_name },
                { header: "Reason", cell: (a) => a.reason ?? "—" },
                { header: "Status", cell: (a) => <StatusBadge status={a.status} /> },
              ]}
            />
          )}
        </div>
      </div>

      <Modal open={editing} onClose={() => setEditing(false)} title="Edit patient">
        <PatientForm
          patient={p}
          onCancel={() => setEditing(false)}
          onSaved={() => {
            setEditing(false);
            patient.reload();
          }}
        />
      </Modal>
    </>
  );
}
