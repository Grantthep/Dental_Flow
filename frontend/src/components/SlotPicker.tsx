"use client";

import { useEffect } from "react";
import { api } from "@/lib/api";
import { fmtTime } from "@/lib/time";
import type { Slot } from "@/lib/types";
import { useFetch } from "@/lib/useFetch";
import { ErrorBox, Loading } from "./ui/States";

/** Free slots for one dentist on one day. Bump `refreshKey` to reload (e.g. after a 409).
 *  `preferTime` ("HH:MM") is selected automatically if that slot is free. */
export function SlotPicker({
  dentistId,
  date,
  duration,
  value,
  onChange,
  refreshKey = 0,
  preferTime,
}: {
  dentistId: number | null;
  date: string;
  duration: number;
  value: string | null;
  onChange: (s: Slot) => void;
  refreshKey?: number;
  preferTime?: string | null;
}) {
  const slots = useFetch(
    () => (dentistId && date ? api.dentists.slots(dentistId, date, duration) : Promise.resolve(null)),
    [dentistId, date, duration, refreshKey],
  );

  useEffect(() => {
    const match = preferTime && !value && slots.data?.find((s) => fmtTime(s.start_at) === preferTime);
    if (match) onChange(match);
    // only when new slots arrive
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [slots.data]);

  return (
    <fieldset className="space-y-2">
      <legend className="text-sm font-medium text-slate-700">Free time *</legend>
      {!dentistId || !date ? (
        <p className="text-sm text-slate-500">Choose a dentist and a date first.</p>
      ) : slots.loading ? (
        <Loading label="Finding free times…" />
      ) : slots.error !== undefined ? (
        <ErrorBox error={slots.error} onRetry={slots.reload} />
      ) : !slots.data?.length ? (
        <p className="rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-800">No free times that day. Try another date or dentist.</p>
      ) : (
        <div className="flex flex-wrap gap-2">
          {slots.data.map((s) => {
            const selected = s.start_at === value;
            return (
              <button
                key={s.start_at}
                type="button"
                aria-pressed={selected}
                onClick={() => onChange(s)}
                className={`rounded-md border px-3 py-1.5 text-sm tabular-nums ${
                  selected ? "border-teal-600 bg-teal-600 text-white" : "border-slate-300 bg-white hover:border-teal-600 hover:bg-teal-50"
                }`}
              >
                {fmtTime(s.start_at)}
              </button>
            );
          })}
        </div>
      )}
    </fieldset>
  );
}
