import enum
from datetime import date, datetime, time

from sqlalchemy import (
    CheckConstraint,
    Enum,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, ExcludeConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Role(str, enum.Enum):
    admin = "admin"
    receptionist = "receptionist"
    dentist = "dentist"


class AppointmentStatus(str, enum.Enum):
    booked = "booked"
    confirmed = "confirmed"
    completed = "completed"
    cancelled = "cancelled"
    no_show = "no_show"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(150))
    role: Mapped[Role] = mapped_column(Enum(Role, name="user_role"))
    is_active: Mapped[bool] = mapped_column(server_default=text("true"))
    # Tokens issued before this are rejected (app/deps.py), so changing a password logs out old sessions.
    password_changed_at: Mapped[datetime | None]


class Dentist(TimestampMixin, Base):
    __tablename__ = "dentists"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), unique=True)
    full_name: Mapped[str] = mapped_column(String(150))
    specialty: Mapped[str | None] = mapped_column(String(100))
    phone: Mapped[str | None] = mapped_column(String(30))
    email: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(server_default=text("true"))


class Patient(TimestampMixin, Base):
    __tablename__ = "patients"
    __table_args__ = (
        Index("ix_patients_name", "last_name", "first_name"),
        Index("ix_patients_phone", "phone"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    date_of_birth: Mapped[date | None]
    gender: Mapped[str | None] = mapped_column(String(20))
    phone: Mapped[str] = mapped_column(String(30))
    email: Mapped[str | None] = mapped_column(String(255))
    address: Mapped[str | None] = mapped_column(String(255))
    medical_notes: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(server_default=text("true"))
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())


class Availability(Base):
    __tablename__ = "availability"
    __table_args__ = (
        CheckConstraint("end_time > start_time", name="ck_availability_time_order"),
        CheckConstraint("day_of_week BETWEEN 0 AND 6", name="ck_availability_day"),
        Index("ix_availability_dentist_day", "dentist_id", "day_of_week"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    dentist_id: Mapped[int] = mapped_column(ForeignKey("dentists.id", ondelete="CASCADE"))
    day_of_week: Mapped[int] = mapped_column(SmallInteger)  # 0=Mon .. 6=Sun
    start_time: Mapped[time]
    end_time: Mapped[time]


class TimeOff(Base):
    __tablename__ = "time_off"
    __table_args__ = (CheckConstraint("end_at > start_at", name="ck_time_off_order"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    dentist_id: Mapped[int] = mapped_column(ForeignKey("dentists.id", ondelete="CASCADE"), index=True)
    start_at: Mapped[datetime]
    end_at: Mapped[datetime]
    reason: Mapped[str | None] = mapped_column(String(255))


# Only active appointments block a slot.
_ACTIVE = text("status NOT IN ('cancelled', 'no_show')")


class Appointment(TimestampMixin, Base):
    __tablename__ = "appointments"
    __table_args__ = (
        CheckConstraint("end_at > start_at", name="ck_appointments_time_order"),
        # Double-booking prevention. int4range(id,id,'[]') stands in for "id =" so plain GiST
        # works without the btree_gist extension.
        ExcludeConstraint(
            (text("int4range(dentist_id, dentist_id, '[]')"), "="),
            (text("tstzrange(start_at, end_at)"), "&&"),
            name="ex_appointments_dentist_overlap",
            using="gist",
            where=_ACTIVE,
        ),
        ExcludeConstraint(
            (text("int4range(patient_id, patient_id, '[]')"), "="),
            (text("tstzrange(start_at, end_at)"), "&&"),
            name="ex_appointments_patient_overlap",
            using="gist",
            where=_ACTIVE,
        ),
        Index("ix_appointments_start", "start_at"),  # all-dentists calendar
        Index("ix_appointments_dentist_start", "dentist_id", "start_at"),
        Index("ix_appointments_patient_start", "patient_id", "start_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"))
    dentist_id: Mapped[int] = mapped_column(ForeignKey("dentists.id"))
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    start_at: Mapped[datetime]
    end_at: Mapped[datetime]
    status: Mapped[AppointmentStatus] = mapped_column(
        Enum(AppointmentStatus, name="appointment_status"), server_default="booked"
    )
    reason: Mapped[str | None] = mapped_column(String(255))
    notes: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    patient: Mapped[Patient] = relationship(lazy="joined")
    dentist: Mapped[Dentist] = relationship(lazy="joined")


ACTIVE_STATUSES = (AppointmentStatus.booked, AppointmentStatus.confirmed, AppointmentStatus.completed)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (Index("ix_audit_logs_entity", "entity_type", "entity_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(50))
    entity_type: Mapped[str] = mapped_column(String(50))
    entity_id: Mapped[int]
    changes: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class Treatment(Base):
    """What was done at an appointment. Append-only: corrections are new entries (it's a medical record)."""

    __tablename__ = "treatments"

    id: Mapped[int] = mapped_column(primary_key=True)
    appointment_id: Mapped[int] = mapped_column(ForeignKey("appointments.id"), index=True)
    tooth: Mapped[str | None] = mapped_column(String(10))  # FDI number, e.g. "36"; empty = whole mouth
    procedure: Mapped[str] = mapped_column(String(150))
    notes: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    appointment: Mapped[Appointment] = relationship(lazy="joined")
