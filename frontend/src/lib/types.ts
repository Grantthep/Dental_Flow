// Mirrors backend/app/schemas.py — keep in sync when the API changes.

export type Role = "admin" | "receptionist" | "dentist";

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: Role;
  is_active: boolean;
  created_at: string;
}

export type AppointmentStatus = "booked" | "confirmed" | "completed" | "cancelled" | "no_show";

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

export interface PatientInput {
  first_name: string;
  last_name: string;
  phone: string;
  date_of_birth?: string | null; // YYYY-MM-DD
  gender?: string | null;
  email?: string | null;
  address?: string | null;
  medical_notes?: string | null;
}

export interface Patient extends PatientInput {
  id: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Dentist {
  id: number;
  full_name: string;
  specialty: string | null;
  phone: string | null;
  email: string | null;
  user_id: number | null;
  is_active: boolean;
  created_at: string;
}

export interface Slot {
  start_at: string;
  end_at: string;
}

export interface Appointment {
  id: number;
  patient_id: number;
  dentist_id: number;
  start_at: string;
  end_at: string;
  status: AppointmentStatus;
  reason: string | null;
  notes: string | null;
  created_by: number | null;
  created_at: string;
  updated_at: string;
  patient: { id: number; first_name: string; last_name: string; phone: string };
  dentist: { id: number; full_name: string };
}

export interface AppointmentInput {
  patient_id: number;
  dentist_id: number;
  start_at: string;
  end_at: string;
  reason?: string | null;
  notes?: string | null;
}

export interface Counts {
  total: number;
  completed: number;
  cancelled: number;
  no_show: number;
  upcoming: number;
}

export interface PeriodRow extends Counts {
  period: string;
}

export interface DentistRow extends Counts {
  dentist_id: number;
  full_name: string;
  booked_minutes: number;
}

export interface Rates extends Counts {
  cancellation_rate: number | null;
  no_show_rate: number | null;
}
