"""Booking rules shared by create, reschedule and the free-slots endpoint."""

import os
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ACTIVE_STATUSES, Appointment, Availability, Dentist, Patient, TimeOff

CLINIC_TZ = ZoneInfo(os.getenv("CLINIC_TZ", "Asia/Yangon"))
SLOT_STEP = timedelta(minutes=15)


class BookingError(HTTPException):
    """Rendered as {"detail": ..., "code": ...} by the handler in main.py."""

    def __init__(self, status: int, code: str, detail: str):
        super().__init__(status, detail)
        self.code = code


def _conflict(code: str, detail: str):
    return BookingError(409, code, detail)


def _overlap(model, start: datetime, end: datetime):
    return (model.start_at < end) & (model.end_at > start)


def _blocks(db: Session, dentist_id: int, day: int) -> list[Availability]:
    return db.scalars(
        select(Availability)
        .where(Availability.dentist_id == dentist_id, Availability.day_of_week == day)
        .order_by(Availability.start_time)
    ).all()


def check_bookable(
    db: Session, dentist_id: int, patient_id: int, start: datetime, end: datetime, exclude_id: int | None = None
) -> None:
    """Raise 4xx if this time can't be booked. The DB exclusion constraint is the final guard."""
    if start < datetime.now(UTC):
        raise BookingError(422, "in_past", "Cannot book in the past")

    dentist = db.get(Dentist, dentist_id)
    if not dentist or not dentist.is_active:
        raise HTTPException(404, "Dentist not found")
    patient = db.get(Patient, patient_id)
    if not patient or not patient.is_active:
        raise HTTPException(404, "Patient not found")

    local_start, local_end = start.astimezone(CLINIC_TZ), end.astimezone(CLINIC_TZ)
    fits = local_start.date() == local_end.date() and any(
        b.start_time <= local_start.time() and local_end.time() <= b.end_time
        for b in _blocks(db, dentist_id, local_start.weekday())
    )
    if not fits:
        raise _conflict("outside_hours", "Outside the dentist's working hours")

    if db.scalar(select(TimeOff.id).where(TimeOff.dentist_id == dentist_id, _overlap(TimeOff, start, end))):
        raise _conflict("time_off", "Dentist is off at this time")

    taken = select(Appointment.id).where(
        Appointment.status.in_(ACTIVE_STATUSES), _overlap(Appointment, start, end)
    )
    if exclude_id:
        taken = taken.where(Appointment.id != exclude_id)
    if db.scalar(taken.where(Appointment.dentist_id == dentist_id)):
        raise _conflict("slot_taken", "Dentist already has an appointment at this time")
    if db.scalar(taken.where(Appointment.patient_id == patient_id)):
        raise _conflict("patient_busy", "Patient already has an appointment at this time")


def free_slots(db: Session, dentist_id: int, day: date, duration: timedelta) -> list[tuple[datetime, datetime]]:
    """Start/end pairs (UTC) on 15-minute steps where the dentist is free for `duration`."""
    day_start = datetime.combine(day, datetime.min.time(), CLINIC_TZ)
    day_end = day_start + timedelta(days=1)
    busy = [
        (a.start_at, a.end_at)
        for a in db.scalars(
            select(Appointment).where(
                Appointment.dentist_id == dentist_id,
                Appointment.status.in_(ACTIVE_STATUSES),
                _overlap(Appointment, day_start, day_end),
            )
        )
    ] + [
        (t.start_at, t.end_at)
        for t in db.scalars(
            select(TimeOff).where(TimeOff.dentist_id == dentist_id, _overlap(TimeOff, day_start, day_end))
        )
    ]
    now = datetime.now(UTC)

    slots = []
    for block in _blocks(db, dentist_id, day.weekday()):
        t = datetime.combine(day, block.start_time, CLINIC_TZ)
        block_end = datetime.combine(day, block.end_time, CLINIC_TZ)
        while t + duration <= block_end:
            end = t + duration
            if t >= now and not any(s < end and e > t for s, e in busy):
                slots.append((t.astimezone(UTC), end.astimezone(UTC)))
            t += SLOT_STEP
    return slots
