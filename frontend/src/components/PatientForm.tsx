"use client";

import { useState, type FormEvent } from "react";
import { api } from "@/lib/api";
import type { Patient, PatientInput } from "@/lib/types";
import { Button } from "./ui/Button";
import { Input, Select, Textarea } from "./ui/Input";
import { ErrorBox } from "./ui/States";

const FIELDS = ["first_name", "last_name", "phone", "date_of_birth", "gender", "email", "address", "medical_notes"] as const;
type Form = Record<(typeof FIELDS)[number], string>;

// Same rule as the backend's Phone type.
const PHONE = /^\+?[0-9 ()-]{6,30}$/;

function validate(f: Form) {
  const e: Partial<Record<keyof Form, string>> = {};
  if (!f.first_name.trim()) e.first_name = "First name is required";
  if (!f.last_name.trim()) e.last_name = "Last name is required";
  if (!f.phone.trim()) e.phone = "Phone is required";
  else if (!PHONE.test(f.phone.trim())) e.phone = "Use digits, spaces, ( ) - and an optional leading +";
  if (f.email.trim() && !/^\S+@\S+\.\S+$/.test(f.email.trim())) e.email = "Enter a valid email";
  if (f.date_of_birth && f.date_of_birth > new Date().toISOString().slice(0, 10)) e.date_of_birth = "Date of birth can't be in the future";
  return e;
}

/** Create a patient, or edit one when `patient` is given. */
export function PatientForm({ patient, onSaved, onCancel }: { patient?: Patient; onSaved: (p: Patient) => void; onCancel: () => void }) {
  const [form, setForm] = useState<Form>(() => Object.fromEntries(FIELDS.map((k) => [k, patient?.[k] ?? ""])) as Form);
  const [errors, setErrors] = useState<Partial<Record<keyof Form, string>>>({});
  const [apiError, setApiError] = useState<unknown>();
  const [saving, setSaving] = useState(false);

  const bind = (k: keyof Form) => ({
    value: form[k],
    error: errors[k],
    onChange: (e: { target: { value: string } }) => setForm({ ...form, [k]: e.target.value }),
  });

  async function submit(e: FormEvent) {
    e.preventDefault();
    const errs = validate(form);
    setErrors(errs);
    if (Object.keys(errs).length) return;
    // Empty optional fields are sent as null.
    const body = Object.fromEntries(FIELDS.map((k) => [k, form[k].trim() || null])) as unknown as PatientInput;
    setSaving(true);
    setApiError(undefined);
    try {
      onSaved(patient ? await api.patients.update(patient.id, body) : await api.patients.create(body));
    } catch (err) {
      setApiError(err);
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={submit} noValidate className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <Input label="First name *" autoComplete="off" {...bind("first_name")} />
        <Input label="Last name *" autoComplete="off" {...bind("last_name")} />
        <Input label="Phone *" type="tel" {...bind("phone")} />
        <Input label="Email" type="email" {...bind("email")} />
        <Input label="Date of birth" type="date" {...bind("date_of_birth")} />
        <Select label="Gender" {...bind("gender")}>
          <option value="">—</option>
          <option value="female">Female</option>
          <option value="male">Male</option>
          <option value="other">Other</option>
        </Select>
      </div>
      <Input label="Address" {...bind("address")} />
      <Textarea label="Allergies / medical notes" {...bind("medical_notes")} />
      {apiError !== undefined && <ErrorBox error={apiError} />}
      <div className="flex justify-end gap-2">
        <Button variant="secondary" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" disabled={saving}>
          {saving ? "Saving…" : patient ? "Save changes" : "Create patient"}
        </Button>
      </div>
    </form>
  );
}
