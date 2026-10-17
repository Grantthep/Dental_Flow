"use client";

import { api } from "@/lib/api";
import type { Dentist } from "@/lib/types";
import { useFetch } from "@/lib/useFetch";
import { Select } from "./ui/Input";

export const useDentists = () => useFetch(api.dentists.list, []);

/** Dentist dropdown. `allLabel` adds an "all dentists" option with value null. */
export function DentistSelect({
  dentists,
  value,
  onChange,
  allLabel,
  label = "Dentist",
  error,
}: {
  dentists: Dentist[] | undefined;
  value: number | null;
  onChange: (id: number | null) => void;
  allLabel?: string;
  label?: string;
  error?: string;
}) {
  return (
    <Select label={label} value={value ?? ""} error={error} onChange={(e) => onChange(e.target.value ? Number(e.target.value) : null)}>
      {allLabel ? <option value="">{allLabel}</option> : <option value="">Choose…</option>}
      {dentists?.map((d) => (
        <option key={d.id} value={d.id}>
          {d.full_name}
          {d.specialty ? ` — ${d.specialty}` : ""}
        </option>
      ))}
    </Select>
  );
}
