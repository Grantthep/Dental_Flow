"use client";

import { useId, type InputHTMLAttributes, type ReactNode, type SelectHTMLAttributes, type TextareaHTMLAttributes } from "react";

type FieldProps = { label: string; error?: string };

const control =
  "w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 " +
  "focus:border-teal-600 focus:outline-none focus:ring-2 focus:ring-teal-600/20 aria-[invalid=true]:border-red-500 disabled:bg-slate-100";

function Field({ id, label, error, children }: FieldProps & { id: string; children: ReactNode }) {
  return (
    <div className="space-y-1">
      <label htmlFor={id} className="block text-sm font-medium text-slate-700">
        {label}
      </label>
      {children}
      {error && (
        <p id={`${id}-error`} className="text-sm text-red-600">
          {error}
        </p>
      )}
    </div>
  );
}

export function Input({ label, error, id, className = "", ...props }: InputHTMLAttributes<HTMLInputElement> & FieldProps) {
  const auto = useId();
  const fid = id ?? auto;
  return (
    <Field id={fid} label={label} error={error}>
      <input
        id={fid}
        aria-invalid={!!error}
        aria-describedby={error ? `${fid}-error` : undefined}
        className={`${control} ${className}`}
        {...props}
      />
    </Field>
  );
}

export function Select({ label, error, id, className = "", children, ...props }: SelectHTMLAttributes<HTMLSelectElement> & FieldProps) {
  const auto = useId();
  const fid = id ?? auto;
  return (
    <Field id={fid} label={label} error={error}>
      <select id={fid} aria-invalid={!!error} className={`${control} ${className}`} {...props}>
        {children}
      </select>
    </Field>
  );
}

export function Textarea({ label, error, id, className = "", ...props }: TextareaHTMLAttributes<HTMLTextAreaElement> & FieldProps) {
  const auto = useId();
  const fid = id ?? auto;
  return (
    <Field id={fid} label={label} error={error}>
      <textarea id={fid} rows={3} aria-invalid={!!error} className={`${control} ${className}`} {...props} />
    </Field>
  );
}
