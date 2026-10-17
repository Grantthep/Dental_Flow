"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Patient } from "@/lib/types";
import { useFetch } from "@/lib/useFetch";
import { Button } from "./ui/Button";
import { Input } from "./ui/Input";
import { ErrorBox } from "./ui/States";

export function useDebounced<T>(value: T, ms = 300) {
  const [v, setV] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setV(value), ms);
    return () => clearTimeout(t);
  }, [value, ms]);
  return v;
}

export const patientName = (p: { first_name: string; last_name: string }) => `${p.first_name} ${p.last_name}`;

/** Search box that lets the user pick one patient. */
export function PatientPicker({
  value,
  onChange,
  error,
}: {
  value: Patient | null;
  onChange: (p: Patient | null) => void;
  error?: string;
}) {
  const [q, setQ] = useState("");
  const query = useDebounced(q.trim());
  const results = useFetch(() => (query ? api.patients.list({ q: query, size: 8 }) : Promise.resolve(null)), [query]);

  if (value)
    return (
      <div className="space-y-1">
        <span className="block text-sm font-medium text-slate-700">Patient *</span>
        <div className="flex items-center justify-between rounded-md border border-slate-300 bg-slate-50 px-3 py-2 text-sm">
          <span>
            <strong>{patientName(value)}</strong> <span className="text-slate-500">· {value.phone}</span>
          </span>
          <Button variant="ghost" className="!py-1" onClick={() => onChange(null)}>
            Change
          </Button>
        </div>
      </div>
    );

  return (
    <div className="space-y-2">
      <Input label="Patient *" placeholder="Search name or phone…" value={q} onChange={(e) => setQ(e.target.value)} error={error} />
      {results.error !== undefined && <ErrorBox error={results.error} onRetry={results.reload} />}
      {results.data && (
        <ul className="divide-y divide-slate-100 rounded-md border border-slate-200 bg-white">
          {results.data.items.length === 0 && <li className="px-3 py-2 text-sm text-slate-500">No patients match “{query}”.</li>}
          {results.data.items.map((p) => (
            <li key={p.id}>
              <button
                type="button"
                onClick={() => onChange(p)}
                className="flex w-full justify-between px-3 py-2 text-left text-sm hover:bg-teal-50"
              >
                <span className="font-medium">{patientName(p)}</span>
                <span className="text-slate-500">{p.phone}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
