"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { PatientForm } from "@/components/PatientForm";
import { patientName, useDebounced } from "@/components/PatientPicker";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { ErrorBox, Loading, PageHeader } from "@/components/ui/States";
import { Table } from "@/components/ui/Table";
import { api } from "@/lib/api";
import { can, useRole } from "@/lib/role";
import { useFetch } from "@/lib/useFetch";

const SIZE = 20;

export default function PatientsPage() {
  const router = useRouter();
  const role = useRole();
  const [q, setQ] = useState("");
  const [includeInactive, setIncludeInactive] = useState(false);
  const [page, setPage] = useState(1);
  const [creating, setCreating] = useState(false);
  const query = useDebounced(q.trim());

  useEffect(() => setPage(1), [query, includeInactive]);

  const patients = useFetch(
    () => api.patients.list({ q: query, include_inactive: includeInactive, page, size: SIZE }),
    [query, includeInactive, page],
  );
  const pages = patients.data ? Math.max(1, Math.ceil(patients.data.total / SIZE)) : 1;

  return (
    <>
      <PageHeader title="Patients" actions={can.editPatients(role) && <Button onClick={() => setCreating(true)}>+ New patient</Button>} />

      <div className="mb-4 flex flex-wrap items-end gap-4">
        <div className="w-full max-w-sm">
          <Input label="Search" type="search" placeholder="Name or phone…" value={q} onChange={(e) => setQ(e.target.value)} />
        </div>
        <label className="flex items-center gap-2 pb-2 text-sm text-slate-600">
          <input type="checkbox" checked={includeInactive} onChange={(e) => setIncludeInactive(e.target.checked)} />
          Include inactive
        </label>
      </div>

      {patients.error !== undefined ? (
        <ErrorBox error={patients.error} onRetry={patients.reload} />
      ) : !patients.data ? (
        <Loading />
      ) : (
        <>
          <div className={patients.loading ? "opacity-60" : undefined}>
            <Table
              rows={patients.data.items}
              rowKey={(p) => p.id}
              onRowClick={(p) => router.push(`/patients/${p.id}`)}
              empty={query ? `No patients match “${query}”.` : "No patients yet."}
              columns={[
                {
                  header: "Name",
                  cell: (p) => (
                    <span className="font-medium text-slate-900">
                      {patientName(p)}
                      {!p.is_active && <span className="ml-2 rounded bg-slate-100 px-1.5 py-0.5 text-xs text-slate-500">inactive</span>}
                    </span>
                  ),
                },
                { header: "Phone", cell: (p) => p.phone },
                { header: "Date of birth", cell: (p) => p.date_of_birth ?? "—", className: "hidden sm:table-cell" },
                { header: "Email", cell: (p) => p.email ?? "—", className: "hidden md:table-cell" },
              ]}
            />
          </div>
          <div className="mt-4 flex items-center justify-between text-sm text-slate-600">
            <span>{patients.data.total} patients</span>
            <div className="flex items-center gap-2">
              <Button variant="secondary" disabled={page <= 1} onClick={() => setPage(page - 1)}>
                Previous
              </Button>
              <span>
                Page {page} of {pages}
              </span>
              <Button variant="secondary" disabled={page >= pages} onClick={() => setPage(page + 1)}>
                Next
              </Button>
            </div>
          </div>
        </>
      )}

      <Modal open={creating} onClose={() => setCreating(false)} title="New patient">
        <PatientForm onCancel={() => setCreating(false)} onSaved={(p) => router.push(`/patients/${p.id}`)} />
      </Modal>
    </>
  );
}
