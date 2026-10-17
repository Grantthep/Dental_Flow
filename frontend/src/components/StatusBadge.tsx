import type { AppointmentStatus } from "@/lib/types";

export const STATUS_LABEL: Record<AppointmentStatus, string> = {
  booked: "Booked",
  confirmed: "Confirmed",
  completed: "Completed",
  cancelled: "Cancelled",
  no_show: "No-show",
};

/** Block colours for the calendar; badges use the same hues. */
export const STATUS_STYLE: Record<AppointmentStatus, string> = {
  booked: "bg-blue-50 text-blue-800 border-blue-300",
  confirmed: "bg-indigo-50 text-indigo-800 border-indigo-300",
  completed: "bg-green-50 text-green-800 border-green-300",
  cancelled: "bg-slate-100 text-slate-500 border-slate-300 line-through",
  no_show: "bg-amber-50 text-amber-800 border-amber-300",
};

export function StatusBadge({ status }: { status: AppointmentStatus }) {
  return (
    <span className={`inline-block rounded-full border px-2 py-0.5 text-xs font-medium ${STATUS_STYLE[status]}`}>
      {STATUS_LABEL[status]}
    </span>
  );
}
